#!/usr/bin/env python3
"""Round-10 Step 1 pilot GHOST PRE-GATE checker
(step1-pilot-package.md sec.5; the pre-gate plan is
registered there before any run).

Two ghost arms (TEACHER_GHOST: the full search machinery
runs, the played pick is forced to the prior's) on the
same seeds at both seats: one under the sec.14 build
(search_s3.php), one under the threshold-lifted build
(search_s3_thr.php). Because the played pick is the
prior's in BOTH builds, the played games must be
action-identical; the search rows show where the builds
differ. The check, exactly:

  1. DETERMINISM + SEAT CONTROL (the round-9
     instruments): raw seat 1 twice agrees per seed on
     (winner, draw, capped, turns, gamelog_sha); raw
     seat 2's gamestate_norm_sha differs from seat 1's
     per seed.
  2. PLAYED-ACTION IDENTITY: per seat, ghost-sec14 vs
     ghost-thr driver rows agree per seed on (winner,
     draw, capped, turns, gamelog_sha) -- ALL seeds.
  3. CONTESTED-CLASS IDENTITY: stat rows paired
     ORDER-AWARE by key (game, branch, player, turn,
     prior_pick) between the two ghost arms of a seat.
     For paired rows whose top prior (max of the
     sec.14 row's priors) is < 0.97: the priors arrays
     must be EXACTLY equal and the selected candidate
     sets must be equal. (The priors and the selection
     are the deterministic parts of a decision: the
     server eval is a function of the state, and the
     selection is a function of the priors. The
     rollout outcomes are NOT compared -- Decide's
     seed base is drawn per call, so two processes
     cannot reproduce each other's worlds; what the
     threshold change must not touch is what the
     contested machinery SEES and SELECTS.)
  4. NEWLY-CONTESTED DIVERGENCE, counted not failed:
     paired keys where the sec.14 arm logged an
     uncontested early-return row (contested == 0;
     that row carries no priors array, so boundary
     membership is read from the thr arm's paired
     row: its top prior >= 0.97) and the thr arm
     logged a full search row (contested == 1) --
     the expected and ONLY expected decision-level
     divergence. Any
     OTHER shape of divergence (a key present in one
     arm only; a contested row paired to an
     uncontested row below the boundary) fails.
  5. K6 per ghost arm (round-9 form): rollout rows
     without ghost == 1 must all carry
     fallback == "thin_prior" AND pick == prior_pick;
     the line (rollout, unstamped, not-thin, pick-off)
     passes iff the last two counts are 0.
  6. Each ghost arm's driver manifest checks are all
     true except possibly ghost_flag_on_all_rollouts
     (read under K6, as in round 9).

Verdict IDENTICAL iff 1, 2, 3, 5, 6 hold and 4's
divergences are all of the expected shape. Exit 0 iff
IDENTICAL, else 2.

Usage:
  pregate_check_pilot.py
      --rows raw_s1=F --rows raw2_s1=F --rows raw_s2=F
      --rows ghost14_s1=F --rows ghost14_s2=F
      --rows ghostthr_s1=F --rows ghostthr_s2=F
      --manifest ghost14_s1=F --manifest ghost14_s2=F
      --manifest ghostthr_s1=F --manifest ghostthr_s2=F
      --stats ghost14_s1=F --stats ghost14_s2=F
      --stats ghostthr_s1=F --stats ghostthr_s2=F
"""
import argparse
import json
import sys
from collections import defaultdict

BOUNDARY = 0.97


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


def top_prior(r):
    pv = r.get("priors")
    if isinstance(pv, dict):
        vals = [float(x) for x in pv.values()]
    elif isinstance(pv, list):
        vals = [float(x) for x in pv]
    else:
        return None
    return max(vals) if vals else None


def k6_line(stats):
    ro = [r for r in stats if r.get("teacher") == 1
          and ("means" in r or "n_worlds" in r)]
    un = [r for r in ro if r.get("ghost") != 1]
    not_thin = sum(1 for r in un
                   if r.get("fallback") != "thin_prior")
    pick_off = sum(1 for r in un
                   if r.get("pick") != r.get("prior_pick"))
    return len(ro), len(un), not_thin, pick_off


def decision_rows(stats):
    """Teacher rows that carry a decision: searched
    rows (priors present) and uncontested early-return
    rows (contested == 0 with ncand present)."""
    out = []
    for r in stats:
        if r.get("teacher") != 1:
            continue
        if "priors" in r or r.get("contested") == 0:
            out.append(r)
    return out


def key_of(r):
    return (str(r.get("game")), str(r.get("branch")),
            int(r.get("player") or 0),
            int(r.get("turn") or 0),
            int(r.get("prior_pick") or 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", action="append", required=True)
    ap.add_argument("--manifest", action="append",
                    required=True)
    ap.add_argument("--stats", action="append", required=True)
    a = ap.parse_args()
    rows, mans, stats = {}, {}, {}
    for spec in a.rows:
        t, p = spec.split("=", 1)
        rows[t] = load_rows(p)
    for spec in a.manifest:
        t, p = spec.split("=", 1)
        mans[t] = json.load(open(p))
    for spec in a.stats:
        t, p = spec.split("=", 1)
        stats[t] = load_stats(p)

    ok = True

    def verdict(name, good, detail=""):
        nonlocal ok
        print("%s %s %s" % ("PASS" if good else "FAIL",
                            name, detail))
        ok = ok and good

    r1, r2, rs2 = (rows.get("raw_s1", {}),
                   rows.get("raw2_s1", {}),
                   rows.get("raw_s2", {}))
    seeds = sorted(set(r1) & set(r2))
    same = sum(1 for s in seeds if all(
        r1[s].get(k) == r2[s].get(k) for k in
        ("winner", "draw", "capped", "turns",
         "gamelog_sha")))
    verdict("determinism: raw seat-1 rerun identical",
            len(seeds) == 10 and same == len(seeds),
            "%d/%d seeds agree" % (same, len(seeds)))
    seeds = sorted(set(r1) & set(rs2))
    diff = sum(1 for s in seeds
               if r1[s].get("gamestate_norm_sha")
               != rs2[s].get("gamestate_norm_sha"))
    verdict("R16: seat-crossed raw control differs",
            len(seeds) == 10 and diff == len(seeds),
            "%d/%d seeds differ" % (diff, len(seeds)))

    for seat in (1, 2):
        g14 = rows.get("ghost14_s%d" % seat, {})
        gth = rows.get("ghostthr_s%d" % seat, {})
        seeds = sorted(set(g14) & set(gth))
        eq = sum(1 for s in seeds if all(
            g14[s].get(k) == gth[s].get(k) for k in
            ("winner", "draw", "capped", "turns",
             "gamelog_sha")))
        verdict("seat %d played-action identity "
                "(ghost sec.14 vs ghost thr)" % seat,
                len(seeds) == 10 and eq == len(seeds),
                "%d/%d seeds identical" % (eq, len(seeds)))

        # decision-level pairing, order-aware
        A = decision_rows(stats.get("ghost14_s%d" % seat, []))
        B = decision_rows(stats.get("ghostthr_s%d" % seat, []))
        byA, byB = defaultdict(list), defaultdict(list)
        for r in A:
            byA[key_of(r)].append(r)
        for r in B:
            byB[key_of(r)].append(r)
        contested_pairs = contested_bad = 0
        newly = other_div = 0
        for k in sorted(set(byA) | set(byB)):
            la, lb = byA.get(k, []), byB.get(k, [])
            if len(la) != len(lb):
                other_div += abs(len(la) - len(lb))
                continue
            for ra, rb in zip(la, lb):
                a_unc = ra.get("contested") == 0
                b_unc = rb.get("contested") == 0
                # The sec.14 uncontested early-return row
                # carries NO priors array; the boundary
                # membership of an uncontested pair is
                # read from the THR arm's row, which
                # searched the decision and logged its
                # priors.
                if a_unc and b_unc:
                    # both builds returned early: only
                    # possible at ncand <= 1 (the lifted
                    # build searches everything else)
                    continue
                if a_unc and not b_unc:
                    tp_b = top_prior(rb)
                    if tp_b is not None and tp_b >= BOUNDARY:
                        newly += 1
                    else:
                        # the sec.14 build skipped a
                        # decision below the boundary:
                        # not the registered divergence
                        other_div += 1
                    continue
                if b_unc and not a_unc:
                    other_div += 1
                    continue
                tp = top_prior(ra)
                if tp is not None and tp < BOUNDARY:
                    contested_pairs += 1
                    if ra.get("priors") != rb.get("priors") \
                            or ra.get("selected") \
                            != rb.get("selected"):
                        contested_bad += 1
                else:
                    # both searched a >= boundary
                    # decision: impossible for the
                    # sec.14 build
                    other_div += 1
        verdict("seat %d contested-class identity "
                "(priors + selected, order-aware pairs)"
                % seat,
                contested_bad == 0 and other_div == 0,
                "%d contested pairs, %d bad, %d other "
                "divergences" % (contested_pairs,
                                 contested_bad, other_div))
        print("INFO seat %d newly-contested divergences "
              "(expected shape): %d" % (seat, newly))

        for tag in ("ghost14_s%d" % seat,
                    "ghostthr_s%d" % seat):
            man = mans.get(tag, {})
            checks = man.get("checks", {})
            others = {k: v for k, v in checks.items()
                      if k != "ghost_flag_on_all_rollouts"}
            verdict("%s manifest checks (other than the "
                    "K6-read one)" % tag,
                    bool(others) and all(others.values()),
                    json.dumps(others))
            line = k6_line(stats.get(tag, []))
            verdict("%s K6 line %d %d %d %d" % ((tag,)
                    + line),
                    line[2] == 0 and line[3] == 0,
                    "(rollout, unstamped, not-thin, "
                    "pick-off)")
    print("PREGATE: %s" % ("IDENTICAL" if ok
                           else "NOT IDENTICAL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
