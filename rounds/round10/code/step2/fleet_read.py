#!/usr/bin/env python3
"""Round-10 Step 2+3 COMBINED FLEET read (registered in
step2-fleet-package.md; design claude-reply-26cc773
sec.3). ONE script, TWO reads:

PRIMARY (paired fleet read, round-9 form): threshold
teacher vs raw v10, same seed + same seat per pair
(pairing.json + games_report.json from
fleet_games_report.py). Scores at draw = 0 (a game
scores 1 iff its arm's player won; a teacher-timeout
pair scores the teacher 0 -- a timeout is a LOSS in
the primary). PRIMARY = the pooled paired Delta over
scored pairs (statuses "scored" + "teacher_timeout");
CI = seed-clustered bootstrap (cluster = seed, both
seats; B = 10000; rng seed from settings, 20261030).
Co-reports: Delta at draw = 0.5 (a teacher timeout
still scores 0 at both prices), the game-level
life-differential (life_score IMPORTED from
fleet_games_report.py -- the ONE definition), per-seat
primary Deltas, the drop-teacher-timeout sensitivity.
BANDS (round 9, verbatim): INCONCLUSIVE iff teacher
timeout rate > 0.02 or (excluded + dropped) rate
> 0.02 (overrides); CONVERTS iff CI lower > 0; HARMS
iff CI upper < 0; else DOES NOT CONVERT. IMPEACHMENT:
primary mean > +0.25 -> the four checks print BEFORE
the verdict. RECONCILIATION before any read: pair
count == settings pairs; the games report's tuple
audit must be ok; teacher stat rows recounted ==
games report; gamename uniqueness over completed
rows; the R14 root-canary refusal class counted BY
NAME.

STEP 2 CO-READ (the pilot's registered construction,
extended): L3 (W=50 CRN) job diffs on ALL teacher-arm
overturns -- cap-aligned world scores (1.0 iff
outcome > 0 AND the world ended by turn 61, else 0),
CRN-paired over worlds finished in both candidates
(the pilot_read.job_diffs construction, re-implemented
here so the file carries no cross-package import);
per-game totals over ALL completed teacher games
(driver rows without "invalid"; zero-job games
contribute 0; NO sampling weights); gain = mean of
per-game totals; bounds from ONE set of game-cluster
bootstrap replicates (B = 10000, seed 20261020, the
pilot's registered bootstrap; the two-sided
percentiles cross-checked against
analyze_l3.cluster_bootstrap); lb = 5th percentile
(one-sided 95%), ub = 95th; SE = sd(per-game totals,
ddof=1) / sqrt(n). Per-class reads (contested /
newly_contested) and z-band edges in the pilot's
form; LOGO range + largest share.
STEP 2 GATE (registered decision rule, the pilot
package's two-sample bar): PASS iff
  z = (gain - 0.0649) / sqrt(SE^2 + 0.0090^2) >= 1.645
(one-sided alpha 0.05) against Stage 3's per-game
gain +0.0649 (SE 0.0090). The fleet's teacher arm
(122 games) satisfies the registered >= 72 minimum;
pilot games are never pooled.
ATTRIBUTION: ratio = co-read per-game gain / the
fleet's paired Delta, under the round-9 sec.4 guard
(stage3_attr_analyze form): the plain numeric ratio
prints ONLY when Delta > 0 AND its CI excludes 0;
Delta <= 0 -> "n/a (Delta <= 0)"; Delta > 0 with a CI
including 0 -> "unstable (Delta CI includes 0)" --
Delta's CI prints beside the label in both guarded
cases and the JSON carries ratio_to_delta: null +
ratio_note. The Fai gate references (87% / 101%)
print as history beside the line.

Modes: --primary-only prints the primary alone (the
games runner's invocation; the co-read section
prints as pending). The full mode (the L3 runner's
invocation) recomputes the primary identically and
adds the co-read; if the primary verdict is
INCONCLUSIVE the co-read prints flagged as under an
inconclusive fleet.

Usage:
  fleet_read.py --pairing pairing.json
      --games-report games_report.json
      --settings settings_fleet.json
      [--jobs jobs_all.jsonl --labels labels_all.jsonl
       --games-rows games_t1a.jsonl ... (teacher rows)]
      [--expect-pairs N] [--primary-only]
      --json-out fleet_read.json
"""
import argparse
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fleet_games_report import life_score  # noqa: E402
# ONE life-score definition: fleet_games_report.life_score
# (round-9 form; see that module).


def load_mod(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


# =====================================================================
# PRIMARY -- paired scores (round-9 stage3_analyze form)
# =====================================================================

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


def primary_read(pairing, grep, settings, base, expect_pairs):
    """Returns (out_dict, lines) or raises AbortRead."""
    pairs = pairing["pairs"]
    B = int(settings["bands"]["bootstrap"]["B"])
    rng_seed = int(settings["bands"]["bootstrap"]["rng_seed"])

    def abort(msg):
        raise AbortRead(msg)

    # ---- RECONCILIATION (before any read) ------------------
    if len(pairs) != expect_pairs:
        abort("reconciliation: pair count %d != expected "
              "%d attempted" % (len(pairs), expect_pairs))
    if not (grep.get("tuple_audit") or {}).get("ok"):
        abort("reconciliation: games report tuple audit "
              "is not ok - no read")
    stat_teacher = 0
    canary = 0
    for rel in pairing.get("stat_files", []):
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            abort("reconciliation: stat file %s missing" % p)
        for l in open(p):
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("teacher") == 1:
                stat_teacher += 1
            elif r.get("fallback") == "canary":
                canary += 1
    if stat_teacher != int(grep.get("teacher_stat_rows", -1)):
        abort("reconciliation: teacher stat rows "
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
        abort("reconciliation: gamename uniqueness "
              "failed over completed rows (%d rows, %d "
              "distinct)" % (len(names), len(set(names))))

    lines = []
    lines.append("=== STEP 2+3 FLEET PAIRED READ (threshold "
                 "teacher vs raw v10, same seed + seat) ===")
    lines.append("RECONCILIATION: pairs attempted %d; teacher "
                 "stat rows %d == games report; tuple audit ok; "
                 "gamenames unique over %d completed rows"
                 % (len(pairs), stat_teacher, len(names)))
    lines.append("R14 root-canary refusal records "
                 "(fallback=canary, no teacher stamp): %d \u2014 "
                 "root decisions refused by the missing-card "
                 "conservation check and played down the plain "
                 "bridge; they write no teacher row" % canary)

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
    n_timeout_pairs = sum(1 for p in pairs
                          if p["status"] == "teacher_timeout")
    teacher_attempted = sum(1 for p in pairs if p.get("teacher"))
    timeout_rate = (n_timeout_pairs / teacher_attempted
                    if teacher_attempted else None)
    n_out_pairs = len(dropped) + len(excluded)
    out_rate = (n_out_pairs / len(pairs)) if pairs else None

    per_block = {}
    for p, d in prim:
        blk = ((p.get("teacher") or {}).get("file") or "?") \
            .replace("games_", "").replace(".jsonl", "")
        per_block.setdefault(blk, []).append(d)
    per_block = {b: {"pairs": len(v), "mean_diff": sum(v) / len(v)}
                 for b, v in sorted(per_block.items())}

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
    return out, lines


class AbortRead(Exception):
    pass


# =====================================================================
# CO-READ -- the pilot's registered construction (pilot_read form)
# =====================================================================

CAP_LAST_DECISIVE_TURN = 61
CLASSES = ("contested", "newly_contested")
BOOT_B = 10000
BOOT_SEED = 20261020


def world_score(res):
    if float(res["outcome"]) > 0 and \
            int(res.get("turns") or 0) <= CAP_LAST_DECISIVE_TURN:
        return 1.0
    return 0.0


def job_diffs(jobs, rows, s0):
    """(diff_by_snap, counts) -- cap-aligned paired diffs,
    the pilot construction."""
    job_by_snap = {str(j["snap"]): j for j in jobs}
    worlds = defaultdict(dict)
    fin = unf = ref = fb = 0
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand not in (int(j["teacher_pick"]),
                        int(j["prior_pick"])):
            continue
        kind, _ = s0.classify(r.get("result"))
        if kind == "finished":
            fin += 1
        elif kind == "refusal":
            ref += 1
        else:
            unf += 1
        if isinstance(r.get("result"), dict):
            fb += int(r["result"].get("fallbacks") or 0)
        if int(r["world"]) not in worlds[(snap, cand)]:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, r.get("result"))
    diff_by_snap = {}
    for snap, j in job_by_snap.items():
        tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
        wt = worlds.get((snap, tp), {})
        wp = worlds.get((snap, pp), {})
        diffs = []
        for w in sorted(set(wt) & set(wp)):
            kt, rt = wt[w]
            kp, rp = wp[w]
            if kt != "finished" or kp != "finished":
                continue
            diffs.append(world_score(rt) - world_score(rp))
        if diffs:
            diff_by_snap[snap] = {
                "diff": sum(diffs) / len(diffs),
                "game": str(j["game"]),
                "class": str(j["class"]),
                "z": float(j["z"]),
                "z_nonfinite": bool(j.get("z_nonfinite")),
                "n_worlds": len(diffs)}
    counts = {"finished": fin, "unfinished": unf,
              "refusals": ref, "fallbacks": fb,
              "jobs_no_shared_worlds":
                  len(jobs) - len(diff_by_snap)}
    return diff_by_snap, counts


def per_game_totals(recs, games, cls=None):
    per = {g: 0.0 for g in games}
    for r in recs:
        if cls is not None and r["class"] != cls:
            continue
        per[r["game"]] = per.get(r["game"], 0.0) + r["diff"]
    return per


def bootstrap_means(per):
    """The pilot's registered game-cluster bootstrap
    replicates (analyze_l3.cluster_bootstrap's algorithm,
    seed 20261020, B=10000). ONE set feeds every bound."""
    games = sorted(per)
    totals = [per[g] for g in games]
    rng = random.Random(BOOT_SEED)
    means = []
    for _ in range(BOOT_B):
        tot = 0.0
        for _ in range(len(games)):
            tot += totals[rng.choice(range(len(games)))]
        means.append(tot / len(games))
    means.sort()
    return means


def gain_read(per, stock):
    grecs = [{"game": g, "diff": per[g]} for g in sorted(per)]
    n = len(grecs)
    gain = sum(r["diff"] for r in grecs) / n if n else None
    lo, hi = stock.cluster_bootstrap(grecs)
    means = bootstrap_means(per)
    ci = [means[int(0.025 * BOOT_B)],
          means[int(0.975 * BOOT_B) - 1]]
    assert ci == [lo, hi], \
        "bootstrap replicates diverge from cluster_bootstrap"
    lb = means[int(0.05 * BOOT_B)]
    ub = means[int(0.95 * BOOT_B) - 1]
    if n > 1:
        var = sum((r["diff"] - gain) ** 2
                  for r in grecs) / (n - 1)
        se = math.sqrt(var) / math.sqrt(n)
    else:
        se = None
    return {"gain": gain, "ci": ci, "lb": lb, "ub": ub,
            "lb_one_sided": lb, "ub_one_sided": ub,
            "se_clustered": se, "games": n}


def logo_read(per):
    games = sorted(per)
    total = sum(per[g] for g in games)
    n = len(games)
    excl = {}
    for g in games:
        excl[g] = (total - per[g]) / (n - 1) if n > 1 else None
    weakest = min(excl, key=lambda g: excl[g]) if excl else None
    shares = {g: (per[g] / total if total != 0 else 0.0)
              for g in games}
    largest = max(shares, key=lambda g: abs(shares[g])) \
        if shares else None
    return {"range": [min(excl.values()), max(excl.values())]
            if excl else None,
            "weakest_exclusion_game": weakest,
            "weakest_exclusion_gain": excl.get(weakest),
            "largest_share_game": largest,
            "largest_share": shares.get(largest)}


def z_band(z, znf, bands):
    for lo, hi in bands:
        if znf:
            return ">3.5"
        if z > lo and (hi is None or z <= hi):
            return ("(%.1f, %.1f]" % (lo, hi)) if hi \
                else (">%.1f" % lo)
    return "<=1.5"


def coread(jobs, rows, games, grep, settings, fleet_primary):
    """The Step 2 co-read + gate decision + attribution.
    Returns (out_dict, lines)."""
    cr = settings["coread"]
    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")
    diff_by_snap, counts = job_diffs(jobs, rows, s0)
    recs = list(diff_by_snap.values())
    out = {"games_population": len(games), "jobs": len(jobs),
           "jobs_scored": len(recs), "label_counts": counts,
           "classes": {}, "bands": {}, "total": {}}

    bands = [(1.5, 2.0), (2.0, 2.5), (2.5, 3.5), (3.5, None)]
    band_recs = defaultdict(list)
    for r in recs:
        band_recs[z_band(r["z"], r["z_nonfinite"],
                         bands)].append(r)
    for b, brs in sorted(band_recs.items()):
        out["bands"][b] = {
            "jobs": len(brs),
            "edge": sum(r["diff"] for r in brs) / len(brs)}

    for cls in CLASSES + ("total",):
        sel = recs if cls == "total" else [
            r for r in recs if r["class"] == cls]
        per = per_game_totals(recs, games,
                              None if cls == "total" else cls)
        g = gain_read(per, stock)
        entry = {"jobs": len(sel),
                 "fires_per_game": len(sel) / len(games)
                 if games else None,
                 "edge": (sum(r["diff"] for r in sel)
                          / len(sel)) if sel else None,
                 "gain": g, "logo": logo_read(per)}
        if cls == "total":
            out["total"] = entry
        else:
            out["classes"][cls] = entry

    # ---- the Step 2 gate decision (registered rule) -----
    s3 = float(cr["stage3_gain"])
    s3se = float(cr["stage3_gain_se"])
    g = out["total"]["gain"]
    gain, se = g["gain"], g["se_clustered"]
    z2 = None
    if gain is not None and se is not None:
        z2 = (gain - s3) / math.sqrt(se * se + s3se * s3se)
    gate_pass = (z2 is not None and z2 >= 1.645)
    out["step2_gate"] = {
        "form": "PASS iff (gain - stage3_gain) / sqrt(SE^2 + "
                "stage3_gain_se^2) >= 1.645 (one-sided 0.05)",
        "gain": gain, "se": se, "stage3_gain": s3,
        "stage3_gain_se": s3se, "z": z2, "PASS": gate_pass,
        "teacher_games": len(games),
        "minimum_teacher_games": int(cr["minimum_teacher_games"]),
        "minimum_met": len(games) >= int(cr["minimum_teacher_games"]),
        "teacher_timeouts_excluded_from_population":
            grep.get("teacher_timeouts")}

    # ---- attribution ratio under the sec.4 guard --------
    fdelta = (fleet_primary.get("primary") or {}).get("mean_diff")
    fci = (fleet_primary.get("primary") or {}).get("ci")
    ratio = None
    ratio_note = None
    if gain is not None and fdelta is not None:
        if fdelta <= 0:
            ratio_note = "n/a (Δ ≤ 0)"
        elif fci is not None and fci[0] > 0:
            ratio = gain / fdelta
        else:
            ratio_note = "unstable (Δ CI includes 0)"
    out["attribution"] = {
        "per_game_gain": gain, "fleet_delta": fdelta,
        "fleet_delta_ci": fci, "ratio_to_delta": ratio,
        "ratio_note": ratio_note}

    lines = []
    lines.append("=== STEP 2 CO-READ (L3 on all teacher-arm "
                 "overturns; gate co-read, pilot games never "
                 "pooled) ===")
    if fleet_primary.get("verdict") == "INCONCLUSIVE":
        lines.append("NOTE: the fleet primary is INCONCLUSIVE; "
                     "this co-read is reported under an "
                     "inconclusive fleet.")
    lines.append("games %d (completed teacher games); jobs %d "
                 "(scored %d); label rows finished %d / "
                 "unfinished %d / refusals %d; fallbacks %d; "
                 "jobs_no_shared_worlds %d; teacher timeouts "
                 "excluded from population: %s"
                 % (len(games), len(jobs), len(recs),
                    counts["finished"], counts["unfinished"],
                    counts["refusals"], counts["fallbacks"],
                    counts["jobs_no_shared_worlds"],
                    grep.get("teacher_timeouts")))
    for cls in CLASSES:
        e = out["classes"][cls]
        gg = e["gain"]
        lines.append(
            "class %s: fires/game %.4f (%d jobs); edge %s; "
            "per-game gain %.4f, two-sided 95%% CI "
            "[%.4f, %.4f], one-sided 95%% lb %.4f / "
            "ub %.4f; LOGO range [%.4f, %.4f], largest "
            "share %.4f (game %s)"
            % (cls, e["fires_per_game"] or 0.0, e["jobs"],
               ("%.4f" % e["edge"]) if e["edge"] is not None
               else "n/a", gg["gain"], gg["ci"][0], gg["ci"][1],
               gg["lb"], gg["ub"], e["logo"]["range"][0],
               e["logo"]["range"][1],
               e["logo"]["largest_share"],
               e["logo"]["largest_share_game"]))
    for b, br in sorted(out["bands"].items()):
        lines.append("z-band %s: %d jobs, edge %.4f"
                     % (b, br["jobs"], br["edge"]))
    gg = out["total"]["gain"]
    lines.append(
        "TOTAL: per-game gain %.4f, two-sided 95%% CI "
        "[%.4f, %.4f], one-sided 95%% lb %.4f / ub %.4f; "
        "LOGO range [%.4f, %.4f], largest share %.4f "
        "(game %s)"
        % (gg["gain"], gg["ci"][0], gg["ci"][1], gg["lb"],
           gg["ub"],
           out["total"]["logo"]["range"][0],
           out["total"]["logo"]["range"][1],
           out["total"]["logo"]["largest_share"],
           out["total"]["logo"]["largest_share_game"]))
    lines.append(
        "STEP 2 GATE: z = (%.4f - %.4f) / sqrt(%.4f^2 + "
        "%.4f^2) = %s -> %s (PASS iff z >= 1.645, one-sided "
        "0.05; teacher games %d >= registered minimum %d: %s)"
        % (gain if gain is not None else float("nan"), s3,
           se if se is not None else float("nan"), s3se,
           ("%.4f" % z2) if z2 is not None else "n/a",
           "PASS" if gate_pass else "NOT PASSED",
           len(games), int(cr["minimum_teacher_games"]),
           "yes" if out["step2_gate"]["minimum_met"] else "NO"))
    ratio_str = pct(ratio)
    if ratio_note is not None:
        ratio_str = "%s, fleet Δ %s CI [%s, %s]" % (
            ratio_note, pct(fdelta),
            pct(fci[0]) if fci else "n/a",
            pct(fci[1]) if fci else "n/a")
    lines.append(
        "ATTRIBUTION: co-read per-game gain %s / fleet paired "
        "Delta %s = %s (Fai gate references: 87%% and 101%%, "
        "printed as history)"
        % (pct(gain), pct(fdelta), ratio_str))
    return out, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairing", required=True)
    ap.add_argument("--games-report", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--jobs")
    ap.add_argument("--labels", nargs="+")
    ap.add_argument("--games-rows", nargs="+")
    ap.add_argument("--base-dir")
    ap.add_argument("--expect-pairs", type=int)
    ap.add_argument("--primary-only", action="store_true")
    ap.add_argument("--json-out", required=True)
    a = ap.parse_args()
    settings = json.load(open(a.settings))
    pairing = json.load(open(a.pairing))
    grep = json.load(open(a.games_report))
    base = a.base_dir or os.path.dirname(os.path.abspath(a.pairing))
    expect_pairs = (a.expect_pairs if a.expect_pairs is not None
                    else int(settings["games"]["pairs"]))
    try:
        pout, plines = primary_read(pairing, grep, settings,
                                    base, expect_pairs)
    except AbortRead as e:
        print("ABORT: %s" % e)
        return 2
    out = dict(pout)
    lines = list(plines)
    if a.primary_only:
        out["coread"] = None
        lines.append("CO-READ: pending labels (fleet_read.py "
                     "full mode runs in run_fleet_l3.sh)")
    else:
        if not (a.jobs and a.labels and a.games_rows):
            print("ABORT: full mode needs --jobs, --labels "
                  "and --games-rows")
            return 2
        jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
        rows = []
        for p in a.labels:
            for l in open(p):
                if l.strip():
                    rows.append(json.loads(l))
        games = []
        for p in a.games_rows:
            for l in open(p):
                if l.strip():
                    r = json.loads(l)
                    if "invalid" not in r:
                        games.append(str(r["gamename"]))
        games = sorted(set(games))
        cout, clines = coread(jobs, rows, games, grep,
                              settings, pout)
        out["coread"] = cout
        lines += clines
    with open(a.json_out, "w") as f:
        json.dump(out, f, indent=1, allow_nan=False)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
