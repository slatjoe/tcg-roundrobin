#!/usr/bin/env python3
"""Round-9 Stage 2 ghost pre-gate checker (ruling sec.3.3;
clause 9 of claude-reply-16f02e2; the round-7 pre-gate
instruments, pregate-report.md).

Reads the pre-gate run's own records -- paired-driver rows,
arm manifests, and teacher stat files -- and renders the
pre-gate verdict. The new teacher build (TEACHER_GHOST=1,
tuple pinned as in the games) must be ACTION-IDENTICAL to
raw v10:

  1. determinism: the seat-1 raw arm, run twice on seeds
     8501-8510, agrees on (winner, draw, capped, turns,
     gamelog_sha) for every seed.
  2. R16 seat-crossed control: the seat-2 raw arm's
     gamestate_norm_sha differs from seat-1's for every
     seed (the harness can tell seats apart).
  3. ghost vs raw, per seat: same winner/draw/capped and
     the same gamelog_sha for every seed -- the applied
     action sequence is identical.
  4. the ghost arm manifests' checks are all true except
     possibly ghost_flag_on_all_rollouts, which is read
     under K6 instead:
  5. K6 (registered in claude-reply-1ab9903 sec.2): the
     ghost_flag_on_all_rollouts assert is satisfied iff
     every other ghost check is true AND every rollout row
     without ghost == 1 carries fallback == "thin_prior"
     AND pick == prior_pick. The mechanical line per seat:
     (rollout rows, unstamped, unstamped-not-thin-prior,
     unstamped-with-pick-not-prior); K6 holds iff the last
     two counts are 0. At the calibrated setting thin-prior
     should be ~0, so the unstamped count should be ~0 too
     -- K6 is implemented regardless.

Verdict IDENTICAL iff all five hold for both seats.
Exit 0 iff IDENTICAL, else 2.

Usage:
  pregate_check.py --rows raw_s1=F [--rows raw2_s1=F]
      --rows raw_s2=F --rows ghost_s1=F --rows ghost_s2=F
      --manifest ghost_s1=F --manifest ghost_s2=F
      --stats ghost_s1=F --stats ghost_s2=F
"""
import argparse
import json
import sys


def load_rows(path):
    out = {}
    for l in open(path):
        if l.strip():
            r = json.loads(l)
            if "seed" in r:
                out[int(r["seed"])] = r
    return out


def load_stats(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def k6_line(stats):
    ro = [r for r in stats if r.get("teacher") == 1
          and ("means" in r or "n_worlds" in r)]
    un = [r for r in ro if r.get("ghost") != 1]
    not_thin = sum(1 for r in un
                   if r.get("fallback") != "thin_prior")
    pick_off = sum(1 for r in un
                   if r.get("pick") != r.get("prior_pick"))
    return len(ro), len(un), not_thin, pick_off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", action="append", required=True)
    ap.add_argument("--manifest", action="append", required=True)
    ap.add_argument("--stats", action="append", required=True)
    a = ap.parse_args()
    rows = {}
    for spec in a.rows:
        tag, path = spec.split("=", 1)
        rows[tag] = load_rows(path)
    mans = {}
    for spec in a.manifest:
        tag, path = spec.split("=", 1)
        mans[tag] = json.load(open(path))
    stats = {}
    for spec in a.stats:
        tag, path = spec.split("=", 1)
        stats[tag] = load_stats(path)

    ok = True

    def verdict(name, good, detail=""):
        nonlocal ok
        print("%s %s %s" % ("PASS" if good else "FAIL", name,
                            detail))
        ok = ok and good

    # 1. determinism (seat-1 raw vs its rerun)
    r1, r2 = rows.get("raw_s1", {}), rows.get("raw2_s1", {})
    seeds = sorted(set(r1) & set(r2))
    same = sum(1 for s in seeds
               if all(r1[s].get(k) == r2[s].get(k) for k in
                      ("winner", "draw", "capped", "turns",
                       "gamelog_sha")))
    verdict("determinism: raw seat-1 rerun identical",
            len(seeds) == 10 and same == len(seeds),
            "%d/%d seeds agree" % (same, len(seeds)))

    # 2. R16 seat-crossed control
    rs2 = rows.get("raw_s2", {})
    seeds = sorted(set(r1) & set(rs2))
    diff = sum(1 for s in seeds
               if r1[s].get("gamestate_norm_sha")
               != rs2[s].get("gamestate_norm_sha"))
    verdict("R16: seat-crossed raw control differs",
            len(seeds) == 10 and diff == len(seeds),
            "%d/%d seeds differ" % (diff, len(seeds)))

    # 3-5. per-seat ghost identity + manifest + K6
    for seat, gtag, rtag in ((1, "ghost_s1", "raw_s1"),
                             (2, "ghost_s2", "raw_s2")):
        g, r = rows.get(gtag, {}), rows.get(rtag, {})
        seeds = sorted(set(g) & set(r))
        eq = sum(1 for s in seeds
                 if all(g[s].get(k) == r[s].get(k) for k in
                        ("winner", "draw", "capped"))
                 and g[s].get("gamelog_sha")
                 == r[s].get("gamelog_sha"))
        verdict("ghost seat %d action-identical to raw" % seat,
                len(seeds) == 10 and eq == len(seeds),
                "%d/%d seeds identical" % (eq, len(seeds)))
        man = mans.get(gtag, {})
        checks = man.get("checks", {})
        others = {k: v for k, v in checks.items()
                  if k != "ghost_flag_on_all_rollouts"}
        verdict("ghost seat %d manifest checks (other than "
                "the K6-read one)" % seat,
                bool(others) and all(others.values()),
                json.dumps(others))
        line = k6_line(stats.get(gtag, []))
        verdict("ghost seat %d K6 line %d %d %d %d" % ((seat,)
                + line),
                line[2] == 0 and line[3] == 0,
                "(rollout, unstamped, not-thin, pick-off)")
    print("PREGATE: %s" % ("IDENTICAL" if ok else "NOT IDENTICAL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
