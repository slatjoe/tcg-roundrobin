#!/usr/bin/env python3
"""Round-9 Stage 3 games analyzer (ruling sec.4): the PAIRED
fleet read -- calibrated teacher vs raw v10, same seed + same
seat per pair.

Reads pairing.json + games_report.json (both from
stage3_games_report.py) and the driver row / stat files the
pairing references (resolved under --base-dir, default the
pairing file's directory).

SCORES per pair: primary s = 1 iff the arm row's winner ==
the arm's seat (a teacher-timeout row scores s_teacher = 0
by the timeout rule), else 0. pair_diff = s_teacher - s_raw
in {-1, 0, +1}. Scored-pair set for the primary: pairing
statuses "scored" + "teacher_timeout". "dropped_raw_timeout"
and "excluded" pairs are OUT of the primary, listed with
reasons/counts.

PRIMARY: mean pair_diff over scored pairs; CI = seed-
clustered bootstrap (cluster = seed, both seats; resample
the seeds with replacement; statistic = sum of diffs /
count of scored pairs in the resample, pooled), B = 10000,
rng seed from settings (bands.bootstrap.rng_seed,
20261027), percentile [2.5, 97.5] with the analyze_l3.py
indexing convention (means[int(0.025*B)],
means[int(0.975*B)-1]).

CO-REPORTS: delta05 (draws score 0.5 for both arms; a
teacher timeout still scores 0 -- a timeout is a loss at
both prices); delta_lifediff from LIFE SCORES -- life score
per game (arm's seat frame), computed from p1life/p2life
by life_score(), IMPORTED from stage3_games_report.py so
the definition exists exactly once (fix pass on
claude-reply-c924b19 sec.2.1); per-seat primary deltas
(plain means + seed-cluster CIs on each seat's pairs);
sensitivity_primary = the primary over scored-minus-
teacher_timeout pairs (the drop-the-pair table);
teacher timeout rate = teacher timeouts / teacher games
attempted, with the > 2% -> INCONCLUSIVE rule; pairs out
of the primary (dropped_raw_timeout + excluded) likewise:
(excluded + dropped) / pairs attempted > 0.02 ->
INCONCLUSIVE (sec.2.2 of the same review).

BANDS: INCONCLUSIVE if teacher timeout rate > 0.02 OR
(excluded + dropped) rate > 0.02 (this verdict overrides);
else CONVERTS iff CI lower > 0; HARMS
iff CI upper < 0; else DOES NOT CONVERT. IMPEACHMENT: if
primary mean > +0.25, print BEFORE the verdict, in order:
(i) leave-one-seed-out range of the primary mean, (ii) the
drop-teacher-timeout sensitivity table, (iii) the per-seat
table, (iv) the per-block (teacher block) pair table. A
"VERDICT:" line comes last, always.

RECONCILIATION (before any read): recompute from the
driver rows -- pair count == expected pairs (settings
games.pairs, 400; --expect-pairs overrides for fixtures);
teacher stat rows recounted from the pairing's stat files
== the games report's teacher_stat_rows; the games report's
tuple-audit ok flag must be true (else ABORT exit 2); the
R14 CANARY class is counted and printed BY NAME (stat lines
with fallback == "canary" and no teacher stamp -- never an
unexplained difference); gamename uniqueness across
completed rows is asserted (the not-condition (b) assert).

Usage:
  stage3_analyze.py --pairing pairing.json
      --games-report games_report.json
      --settings settings_stage3.json
      [--base-dir DIR] [--expect-pairs N] [--json-out out]
"""
import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage3_games_report import life_score  # noqa: E402
# ONE life-score definition: stage3_games_report.life_score.
# (Fix pass, claude-reply-c924b19 sec.2.1: the two identical
# copies are replaced by this import so they cannot drift.)


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def score_primary(row, is_teacher_timeout=False):
    if is_teacher_timeout or not isinstance(row, dict) \
            or "invalid" in row:
        return 0.0
    return 1.0 if int(row.get("winner") or 0) == int(row["seat"]) \
        else 0.0


def score_draw05(row, is_teacher_timeout=False):
    if is_teacher_timeout or not isinstance(row, dict) \
            or "invalid" in row:
        return 0.0
    winner = int(row.get("winner") or 0)
    if winner == int(row["seat"]):
        return 1.0
    if winner == 0 or int(row.get("draw") or 0) == 1:
        return 0.5
    return 0.0


def cluster_ci(pairs_diffs, B, rng_seed):
    """pairs_diffs: list of (seed, diff). Seed-clustered
    bootstrap, pooled statistic, analyze_l3.py indexing."""
    by_seed = defaultdict(list)
    for seed, d in pairs_diffs:
        by_seed[seed].append(d)
    seeds = sorted(by_seed)
    if not seeds:
        return None
    rng = random.Random(rng_seed)
    means = []
    for _ in range(B):
        tot = 0.0
        n = 0
        for _ in range(len(seeds)):
            ds = by_seed[rng.choice(seeds)]
            tot += sum(ds)
            n += len(ds)
        means.append(tot / n)
    means.sort()
    return [means[int(0.025 * B)], means[int(0.975 * B) - 1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairing", required=True)
    ap.add_argument("--games-report", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--base-dir")
    ap.add_argument("--expect-pairs", type=int)
    ap.add_argument("--json-out")
    a = ap.parse_args()
    settings = json.load(open(a.settings))
    pairing = json.load(open(a.pairing))
    grep = json.load(open(a.games_report))
    base = a.base_dir or os.path.dirname(os.path.abspath(a.pairing))
    pairs = pairing["pairs"]
    B = int(settings["bands"]["bootstrap"]["B"])
    rng_seed = int(settings["bands"]["bootstrap"]["rng_seed"])
    expect_pairs = (a.expect_pairs if a.expect_pairs is not None
                    else int(settings["games"]["pairs"]))

    def abort(msg):
        print("ABORT: %s" % msg)
        return 2

    # ---- RECONCILIATION (before any read) ------------------
    if len(pairs) != expect_pairs:
        return abort("reconciliation: pair count %d != expected "
                     "%d attempted" % (len(pairs), expect_pairs))
    if not (grep.get("tuple_audit") or {}).get("ok"):
        return abort("reconciliation: games report tuple audit "
                     "is not ok - no read")
    stat_teacher = 0
    canary = 0
    for rel in pairing.get("stat_files", []):
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            return abort("reconciliation: stat file %s missing" % p)
        for l in open(p):
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("teacher") == 1:
                stat_teacher += 1
            elif r.get("fallback") == "canary":
                canary += 1
    if stat_teacher != int(grep.get("teacher_stat_rows", -1)):
        return abort("reconciliation: teacher stat rows "
                     "recounted %d != games report %d"
                     % (stat_teacher,
                        int(grep.get("teacher_stat_rows", -1))))
    names = []
    for pr in pairs:
        for side in ("teacher", "raw"):
            ref = pr.get(side) or {}
            row = ref.get("row") or {}
            if "invalid" not in row and row.get("gamename") is not None:
                names.append(str(row["gamename"]))
    if len(names) != len(set(names)):
        return abort("reconciliation: gamename uniqueness "
                     "failed over completed rows (%d rows, %d "
                     "distinct)" % (len(names), len(set(names))))

    lines = []
    lines.append("=== STAGE 3 PAIRED READ (teacher vs raw v10, "
                 "same seed + seat) ===")
    lines.append("RECONCILIATION: pairs attempted %d; teacher "
                 "stat rows %d == games report; tuple audit ok; "
                 "gamenames unique over %d completed rows"
                 % (len(pairs), stat_teacher, len(names)))
    lines.append("R14 root-canary refusal records "
                 "(fallback=canary, no teacher stamp): %d \u2014 "
                 "root decisions refused by the missing-card "
                 "conservation check and played down the plain "
                 "bridge; they write no teacher row" % canary)

    # ---- scores ---------------------------------------------
    scored, dropped, excluded = [], [], []
    for pr in pairs:
        st = pr["status"]
        if st in ("scored", "teacher_timeout"):
            scored.append(pr)
        elif st == "dropped_raw_timeout":
            dropped.append(pr)
        else:
            excluded.append(pr)
    def diffs(scorefn, pool):
        out = []
        for pr in pool:
            tt = pr["status"] == "teacher_timeout"
            trow = (pr.get("teacher") or {}).get("row")
            rrow = (pr.get("raw") or {}).get("row")
            if scorefn is score_primary or scorefn is score_draw05:
                d = scorefn(trow, tt) - scorefn(rrow, False)
            else:
                d = scorefn(trow) - scorefn(rrow)
            out.append((pr, d))
        return out

    prim = diffs(score_primary, scored)
    mean = (sum(d for _p, d in prim) / len(prim)) if prim else None
    ci = cluster_ci([(p["seed"], d) for p, d in prim], B, rng_seed) \
        if prim else None
    d05 = diffs(score_draw05, scored)
    mean05 = (sum(d for _p, d in d05) / len(d05)) if d05 else None
    ci05 = cluster_ci([(p["seed"], d) for p, d in d05], B, rng_seed) \
        if d05 else None
    lfd = diffs(life_score, scored)
    meanlf = (sum(d for _p, d in lfd) / len(lfd)) if lfd else None
    cilf = cluster_ci([(p["seed"], d) for p, d in lfd], B, rng_seed) \
        if lfd else None

    per_seat = {}
    for seat in (1, 2):
        sp = [(p, d) for p, d in prim if p["seat"] == seat]
        per_seat[seat] = {
            "pairs": len(sp),
            "mean_diff": (sum(d for _p, d in sp) / len(sp)) if sp else None,
            "ci": cluster_ci([(p["seed"], d) for p, d in sp],
                             B, rng_seed) if sp else None}
    sens_pool = [p for p in scored if p["status"] != "teacher_timeout"]
    sens = diffs(score_primary, sens_pool)
    sens_mean = (sum(d for _p, d in sens) / len(sens)) if sens else None
    n_timeout_pairs = sum(1 for p in pairs if p["status"] == "teacher_timeout")
    teacher_attempted = sum(1 for p in pairs if p.get("teacher"))
    timeout_rate = (n_timeout_pairs / teacher_attempted
                    if teacher_attempted else None)
    n_out_pairs = len(dropped) + len(excluded)
    out_rate = (n_out_pairs / len(pairs)) if pairs else None

    # per-block (teacher block) pair table
    per_block = {}
    for p, d in prim:
        blk = ((p.get("teacher") or {}).get("file") or "?") \
            .replace("games_", "").replace(".jsonl", "")
        per_block.setdefault(blk, []).append(d)
    per_block = {b: {"pairs": len(v), "mean_diff": sum(v) / len(v)}
                 for b, v in sorted(per_block.items())}

    # LOGO (leave-one-seed-out) range of the primary mean
    logo = None
    if prim:
        by_seed = defaultdict(list)
        for p, d in prim:
            by_seed[p["seed"]].append(d)
        vals = []
        for s in sorted(by_seed):
            rest = [d for p, d in prim if p["seed"] != s]
            if rest:
                vals.append(sum(rest) / len(rest))
        if vals:
            logo = [min(vals), max(vals)]

    # ---- verdict ---------------------------------------------
    verdict = None
    if (timeout_rate is not None and timeout_rate > 0.02) \
            or (out_rate is not None and out_rate > 0.02):
        verdict = "INCONCLUSIVE"
    elif mean is not None and ci is not None:
        if ci[0] > 0:
            verdict = "CONVERTS"
        elif ci[1] < 0:
            verdict = "HARMS"
        else:
            verdict = "DOES NOT CONVERT"

    out = {
        "pairs_attempted": len(pairs),
        "primary": {"pairs_scored": len(scored),
                    "mean_diff": mean, "ci": ci},
        "delta05": {"pairs_scored": len(scored),
                    "mean_diff": mean05, "ci": ci05},
        "delta_lifediff": {"pairs_scored": len(scored),
                           "mean_diff": meanlf, "ci": cilf},
        "per_seat": {str(k): v for k, v in per_seat.items()},
        "per_block": per_block,
        "sensitivity_primary": {
            "pairs": len(sens), "mean_diff": sens_mean,
            "teacher_timeout_pairs_dropped": n_timeout_pairs},
        "teacher_timeouts": n_timeout_pairs,
        "teacher_games_attempted": teacher_attempted,
        "teacher_timeout_rate": timeout_rate,
        "pairs_out_of_primary": n_out_pairs,
        "pairs_out_rate": out_rate,
        "dropped": [{"seed": p["seed"], "seat": p["seat"],
                     "reason": p.get("reason")} for p in dropped],
        "excluded": [{"seed": p["seed"], "seat": p["seat"],
                      "reason": p.get("reason")} for p in excluded],
        "reconciliation": {"teacher_stat_rows": stat_teacher,
                           "canary_refusal_rows": canary,
                           "gamenames_checked": len(names)},
        "verdict": verdict,
        "impeachment": ({"logo_range": logo} if (mean is not None
                        and mean > 0.25) else None),
    }

    lines.append("PRIMARY: pairs scored %d of %d attempted; mean "
                 "paired diff %s; seed-clustered CI [%s, %s] "
                 "(B=%d, rng %d)"
                 % (len(scored), len(pairs), pct(mean),
                    pct(ci[0]) if ci else "n/a",
                    pct(ci[1]) if ci else "n/a", B, rng_seed))
    lines.append("CO-REPORT delta05 (draws 0.5; teacher timeout "
                 "still 0): mean %s; CI [%s, %s]"
                 % (pct(mean05), pct(ci05[0]) if ci05 else "n/a",
                    pct(ci05[1]) if ci05 else "n/a"))
    lines.append("CO-REPORT delta_lifediff (life scores from "
                 "p1life/p2life): mean %s; CI [%s, %s]"
                 % (pct(meanlf), pct(cilf[0]) if cilf else "n/a",
                    pct(cilf[1]) if cilf else "n/a"))
    lines.append("CO-REPORT per-seat primary: seat 1 mean %s CI "
                 "[%s, %s] over %d pairs; seat 2 mean %s CI "
                 "[%s, %s] over %d pairs"
                 % (pct(per_seat[1]["mean_diff"]),
                    pct(per_seat[1]["ci"][0]) if per_seat[1]["ci"]
                    else "n/a",
                    pct(per_seat[1]["ci"][1]) if per_seat[1]["ci"]
                    else "n/a", per_seat[1]["pairs"],
                    pct(per_seat[2]["mean_diff"]),
                    pct(per_seat[2]["ci"][0]) if per_seat[2]["ci"]
                    else "n/a",
                    pct(per_seat[2]["ci"][1]) if per_seat[2]["ci"]
                    else "n/a", per_seat[2]["pairs"]))
    lines.append("SENSITIVITY (drop teacher-timeout pairs): %d "
                 "pairs dropped; primary over %d pairs = %s"
                 % (n_timeout_pairs, len(sens), pct(sens_mean)))
    lines.append("TEACHER TIMEOUTS: %d of %d teacher games "
                 "(rate %s; > 0.02 -> INCONCLUSIVE)"
                 % (n_timeout_pairs, teacher_attempted,
                    pct(timeout_rate)))
    lines.append("PAIRS OUT of the primary: dropped_raw_timeout "
                 "%d, excluded %d (total %d of %d attempted, "
                 "rate %s; > 0.02 -> INCONCLUSIVE)"
                 % (len(dropped), len(excluded), n_out_pairs,
                    len(pairs), pct(out_rate)))
    for p in dropped + excluded:
        lines.append("  out: seed %s seat %s status %s (%s)"
                     % (p["seed"], p["seat"], p["status"],
                        p.get("reason")))

    if mean is not None and mean > 0.25:
        lines.append("IMPEACHMENT (primary mean %s > +0.25) - "
                     "checks BEFORE the verdict:" % pct(mean))
        lines.append("  (i) leave-one-seed-out range of the "
                     "primary mean: [%s, %s]"
                     % (pct(logo[0]) if logo else "n/a",
                        pct(logo[1]) if logo else "n/a"))
        lines.append("  (ii) drop-teacher-timeout sensitivity: "
                     "%d pairs dropped, primary recomputed = %s "
                     "over %d pairs"
                     % (n_timeout_pairs, pct(sens_mean), len(sens)))
        lines.append("  (iii) per-seat table:")
        for seat in (1, 2):
            lines.append("    seat %d: %d pairs, mean %s, CI "
                         "[%s, %s]"
                         % (seat, per_seat[seat]["pairs"],
                            pct(per_seat[seat]["mean_diff"]),
                            pct(per_seat[seat]["ci"][0])
                            if per_seat[seat]["ci"] else "n/a",
                            pct(per_seat[seat]["ci"][1])
                            if per_seat[seat]["ci"] else "n/a"))
        lines.append("  (iv) per-block (teacher block) pair table:")
        for b, v in per_block.items():
            lines.append("    block %s: %d pairs, mean diff %s"
                         % (b, v["pairs"], pct(v["mean_diff"])))
    lines.append("BANDS: INCONCLUSIVE iff teacher timeout rate "
                 "> 0.02 or (excluded + dropped) rate > 0.02; "
                 "CONVERTS iff CI lower > 0; HARMS iff CI "
                 "upper < 0; else DOES NOT CONVERT.")
    lines.append("VERDICT: %s" % verdict)
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
