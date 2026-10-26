#!/usr/bin/env python3
"""Round-9 Stage 0 (D) reporting (claude-reply-8dddf38 sec.1;
error taxonomy per claude-reply-2db6b77 sec.2).

Companion to the registered L3 scorer (analyze_l3_deploy.py, the
O3 deployment copy: stock analyze_l3.py with DELTA = 0.0075). The
stock scorer's aggregation counts unfinished worlds in one global
integrity counter; the (D) condition requires more, computed here
from the same jobs + label rows:

ERROR TAXONOMY (review sec.2). A row's error class decides its
treatment everywhere in this report:
  * REFUSAL classes (REFUSAL_CLASSES below) are determinization
    refusals: the label machinery excluded the world itself. Such
    rows are tallied by class, excluded from every unfinished
    share, and drop their pair from the sensitivity read.
  * EVERY other error class -- abort, timeout, and any unlisted
    string; the unlisted default is NON-TERMINATION -- counts as
    UNFINISHED: it enters the unfinished shares (denominator =
    all rows minus refusals) and is priced as a draw (0.5) in the
    sensitivity read.
  * A non-error row with finished == 0 is unfinished (a world
    that ran and did not terminate); a row with no usable result
    at all is unfinished under the pseudo-class "null_result".

  (i)   unfinished-world share per candidate role (teacher pick /
        prior pick) and pooled, refusals excluded as above.
  (ii)  the paired-n distribution: per job, the number of worlds
        both candidates finished (the primary read's n_worlds) --
        min / p25 / median / mean / p75 / max, plus bucket counts.
  (iii) the SENSITIVITY read: worlds where NEITHER candidate's
        row is a refusal are scored with unfinished = draw
        (score 0.5, the instrument's own price for a game that
        does not end). Per-job sensitivity diff = mean over those
        worlds of (teacher score - prior score); the read is the
        mean over jobs with a game-clustered bootstrap CI (the
        scorer's own cluster_bootstrap, imported), plus per-game
        gain at TEACHER_GAMES = 400.
  (iv)  the registered condition, printed with its inputs: if the
        pooled unfinished share exceeds 20%, a null (CI includes
        0) or negative (mean <= 0) primary read is
        INSTRUMENT-LIMITED and cannot trigger CLOSE at Stage 0; a
        positive read (mean > 0 with CI lower > 0) stands either
        way.

WORLD-COUNT GUARD (review sec.3.1): neither label driver pins W
on its jobs, so this report asserts exactly EXPECT rows per
(job, candidate) over the pass's label files and aborts
otherwise -- a truncated label file must not silently shrink
the paired n. EXPECT defaults to 50, the registered Stage 0
width (the runner passes no override); the synthetic fixtures
pass their own small width explicitly.

The primary read itself is computed by IMPORTING the deployment
scorer's aggregate/summarize, and, when --scorer-json is given,
cross-checked against the scorer's standalone output (agreement
asserted to 1e-9; the bootstrap is seeded, so the two must agree
exactly). Any disagreement aborts the report.

Usage:
  stage0_report.py --jobs jobs.jsonl --labels l.jsonl [...] \
      --pass-name primary [--scorer-json scorer_stdout.txt] \
      [--json-out report.json]
"""
import argparse
import importlib.util
import json
import sys
from collections import defaultdict

HERE = __file__.rsplit("/", 1)[0]

# Determinization refusals (review sec.2): excluded from both the
# unfinished share and the sensitivity read, tallied separately.
# Every other error class -- and any unlisted one -- defaults to
# NON-TERMINATION and counts as unfinished.
REFUSAL_CLASSES = frozenset({
    "canary_hook_failed", "det_persist_failed",
    "det_verify_failed", "det_verify_hook_failed",
})


def load_scorer():
    spec = importlib.util.spec_from_file_location(
        "analyze_l3_deploy", HERE + "/analyze_l3_deploy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    i = q * (len(sorted_vals) - 1)
    lo = int(i)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def classify(res):
    """Classify one label row's result.

    Returns (kind, err_class): kind is "finished", "unfinished"
    or "refusal"; err_class is the row's error string for error
    rows ("null_result" for a row with no usable result), else
    None.
    """
    if not isinstance(res, dict):
        return "unfinished", "null_result"
    if "error" in res:
        ec = str(res["error"])
        if ec in REFUSAL_CLASSES:
            return "refusal", ec
        return "unfinished", ec
    if int(res.get("finished") or 0) == 0:
        return "unfinished", None
    return "finished", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--pass-name", required=True)
    ap.add_argument("--expect-rows", type=int, default=50)
    ap.add_argument("--scorer-json")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = []
    for path in a.labels:
        with open(path) as f:
            for l in f:
                if l.strip():
                    rows.append(json.loads(l))
    job_by_snap = {str(j["snap"]): j for j in jobs}

    # ---- world-count guard (review sec.3.1): exactly
    # EXPECT rows per (job, candidate) in this pass (default
    # 50, the registered width), or the report aborts --
    # neither driver pins W on its jobs, so a short label file
    # must fail here rather than shrink the paired n silently.
    pair_counts = defaultdict(int)
    for r in rows:
        snap = str(r.get("snap"))
        if snap in job_by_snap:
            pair_counts[(snap, int(r["cand"]))] += 1
    for snap, j in sorted(job_by_snap.items()):
        for cand in sorted({int(j["teacher_pick"]),
                            int(j["prior_pick"])}):
            n = pair_counts.get((snap, cand), 0)
            if n != a.expect_rows:
                print("ABORT: world-count guard: pass %s job %s "
                      "candidate %d has %d rows, expected exactly "
                      "%d" % (a.pass_name, snap, cand, n,
                              a.expect_rows))
                return 2

    # ---- primary read via the deployment scorer's own code
    scorer = load_scorer()
    records, integ = scorer.aggregate(jobs, rows)
    primary = scorer.summarize(records, integ)

    if a.scorer_json:
        raw = open(a.scorer_json).read()
        standalone, _ = json.JSONDecoder().raw_decode(raw)
        for key in ("jobs_scored", "mean_diff", "per_game_gain"):
            if abs(float(standalone[key]) - float(primary[key])) > 1e-9:
                print("ABORT: report primary %s=%r disagrees with the "
                      "scorer's standalone %r" % (key, primary[key],
                                                 standalone[key]))
                return 2
        for i in (0, 1):
            if abs(float(standalone["ci"][i]) -
                   float(primary["ci"][i])) > 1e-9:
                print("ABORT: report primary CI disagrees with the "
                      "scorer's standalone CI")
                return 2
        cross = "AGREE (1e-9) with the deployment scorer's standalone run"
    else:
        cross = "no standalone scorer output given"

    # ---- extended per-world aggregation
    # worlds[(snap, cand)] = {world: ("finished", outcome) |
    #                          ("unfinished", None) |
    #                          ("refusal", None)}
    worlds = defaultdict(dict)
    role_counts = {"teacher": defaultdict(int), "prior": defaultdict(int)}
    class_tallies = {"teacher": defaultdict(int),
                     "prior": defaultdict(int)}
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand == int(j["teacher_pick"]):
            role = "teacher"
        elif cand == int(j["prior_pick"]):
            role = "prior"
        else:
            continue
        kind, err_class = classify(r.get("result"))
        role_counts[role]["rows"] += 1
        role_counts[role][kind] += 1
        if err_class is not None:
            class_tallies[role][err_class] += 1
        prev = worlds[(snap, cand)].get(int(r["world"]))
        if prev is None:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, float(r["result"]["outcome"])
                if kind == "finished" else None)

    def share(role):
        c = role_counts[role]
        denom = c["finished"] + c["unfinished"]
        return (c["unfinished"] / denom) if denom else None

    sh_t, sh_p = share("teacher"), share("prior")
    fin = sum(role_counts[r]["finished"] for r in role_counts)
    unf = sum(role_counts[r]["unfinished"] for r in role_counts)
    ref = sum(role_counts[r]["refusal"] for r in role_counts)
    sh_pool = (unf / (fin + unf)) if (fin + unf) else None
    pooled_tally = defaultdict(int)
    for role in ("teacher", "prior"):
        for ec, n in class_tallies[role].items():
            pooled_tally[ec] += n

    # ---- paired-n distribution (the primary's per-job n_worlds)
    ns = sorted(r["n_worlds"] for r in records)
    buckets = {"n=50": 0, "40-49": 0, "20-39": 0, "1-19": 0}
    for n in ns:
        if n == 50:
            buckets["n=50"] += 1
        elif n >= 40:
            buckets["40-49"] += 1
        elif n >= 20:
            buckets["20-39"] += 1
        else:
            buckets["1-19"] += 1
    paired_n = {"jobs_scored": len(ns),
                "jobs_missing": integ["jobs_missing"],
                "min": ns[0] if ns else None,
                "p25": quantile(ns, 0.25),
                "median": quantile(ns, 0.5),
                "mean": (sum(ns) / len(ns)) if ns else None,
                "p75": quantile(ns, 0.75),
                "max": ns[-1] if ns else None,
                "buckets": buckets}

    # ---- sensitivity read: unfinished worlds scored as draws
    # (0.5); a world is dropped only when either side's row is a
    # refusal (review sec.2).
    sens_records = []
    sens_worlds = 0
    for snap, j in sorted(job_by_snap.items()):
        tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
        wt = worlds.get((snap, tp), {})
        wp = worlds.get((snap, pp), {})
        diffs = []
        for w in sorted(set(wt) & set(wp)):
            kt, ot = wt[w]
            kp, op = wp[w]
            if kt == "refusal" or kp == "refusal":
                continue
            st = (ot + 1.0) / 2.0 if kt == "finished" else 0.5
            sp = (op + 1.0) / 2.0 if kp == "finished" else 0.5
            diffs.append(st - sp)
        if diffs:
            sens_records.append({"snap": snap, "game": str(j["game"]),
                                 "diff": sum(diffs) / len(diffs),
                                 "n_worlds": len(diffs)})
            sens_worlds += len(diffs)
    if sens_records:
        s_mean = sum(r["diff"] for r in sens_records) / len(sens_records)
        s_lo, s_hi = scorer.cluster_bootstrap(sens_records)
        sens = {"jobs": len(sens_records), "worlds": sens_worlds,
                "mean_diff": s_mean, "ci": [s_lo, s_hi],
                "per_game_gain": s_mean *
                (len(sens_records) / scorer.TEACHER_GAMES)}
    else:
        sens = {"jobs": 0, "worlds": 0, "mean_diff": None, "ci": None,
                "per_game_gain": None}

    # ---- the registered (D) condition
    mean = primary["mean_diff"]
    lo = primary["ci"][0]
    positive = mean > 0 and lo > 0
    if positive:
        verdict = ("POSITIVE — the read stands regardless of the "
                   "unfinished share (registered condition, "
                   "claude-reply-8dddf38 sec.1)")
        instrument_limited = False
    elif sh_pool is not None and sh_pool > 0.20:
        verdict = ("INSTRUMENT-LIMITED — the primary read is null "
                   "or negative under a pooled unfinished share "
                   "above 20%; it cannot trigger CLOSE at Stage 0 "
                   "(registered condition, claude-reply-8dddf38 "
                   "sec.1)")
        instrument_limited = True
    else:
        verdict = ("read as registered — pooled unfinished share "
                   "at or below 20%, so the null/negative read is "
                   "not instrument-limited")
        instrument_limited = False

    out = {"pass": a.pass_name, "primary": primary, "cross_check": cross,
           "unfinished": {
               "teacher": dict(role_counts["teacher"]),
               "prior": dict(role_counts["prior"]),
               "share_teacher": sh_t, "share_prior": sh_p,
               "share_pooled": sh_pool,
               "error_classes": {
                   "teacher": dict(class_tallies["teacher"]),
                   "prior": dict(class_tallies["prior"]),
                   "pooled": dict(pooled_tally)}},
           "paired_n": paired_n, "sensitivity": sens,
           "instrument_limited": instrument_limited,
           "verdict": verdict}
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)

    print("=== STAGE 0 (D) REPORT — pass: %s ===" % a.pass_name)
    print("PRIMARY (deployment scorer %s; cross-check: %s):"
          % ("analyze_l3_deploy.py", cross))
    print("  jobs scored %d of %d (missing %d); mean paired diff %s; "
          "CI [%s, %s]" % (primary["jobs_scored"], integ["jobs_total"],
                           integ["jobs_missing"], pct(mean),
                           pct(primary["ci"][0]), pct(primary["ci"][1])))
    print("  frac better / tied / worse: %s / %s / %s; per-game gain "
          "%s (TEACHER_GAMES=400)" % (pct(primary["frac_pos"]),
                                      pct(primary["frac_zero"]),
                                      pct(primary["frac_neg"]),
                                      pct(primary["per_game_gain"])))
    print("UNFINISHED WORLDS (refusals excluded from every share "
          "and from the sensitivity read; every other error counts "
          "as unfinished):")
    for role in ("teacher", "prior"):
        c = role_counts[role]
        print("  %-7s rows %d: finished %d, unfinished %d, refusal %d; "
              "share %s" % (role, c["rows"], c["finished"],
                            c["unfinished"], c["refusal"],
                            pct(share(role)) if share(role) is not None
                            else "n/a"))
    print("  pooled : finished %d, unfinished %d, refusal %d; share %s"
          % (fin, unf, ref, pct(sh_pool) if sh_pool is not None
             else "n/a"))
    print("ERROR TALLIES BY CLASS (REFUSAL = determinization "
          "refusal, excluded; unfinished = priced as a draw in the "
          "sensitivity read):")
    if pooled_tally:
        for ec, n in sorted(pooled_tally.items(),
                            key=lambda kv: (-kv[1], kv[0])):
            tag = "REFUSAL" if ec in REFUSAL_CLASSES else "unfinished"
            print("  %-24s %4d  [%s]" % (ec, n, tag))
    else:
        print("  (no error rows)")
    print("PAIRED-N (finished worlds shared by both candidates, "
          "per scored job):")
    print("  min %s, p25 %s, median %s, mean %s, p75 %s, max %s; "
          "buckets %s; jobs missing %d"
          % (paired_n["min"], paired_n["p25"], paired_n["median"],
             ("%.2f" % paired_n["mean"]) if paired_n["mean"] is not None
             else "n/a", paired_n["p75"], paired_n["max"],
             paired_n["buckets"], paired_n["jobs_missing"]))
    print("SENSITIVITY (unfinished worlds scored as draws, 0.5; "
          "pairs dropped only on a refusal):")
    if sens["mean_diff"] is not None:
        print("  jobs %d over %d worlds; mean paired diff %s; CI "
              "[%s, %s]; per-game gain %s"
              % (sens["jobs"], sens["worlds"], pct(sens["mean_diff"]),
                 pct(sens["ci"][0]), pct(sens["ci"][1]),
                 pct(sens["per_game_gain"])))
    else:
        print("  no job has a world scored by both candidates")
    print("REGISTERED CONDITION (pooled unfinished share %s; "
          "threshold 0.2000):" % (pct(sh_pool) if sh_pool is not None
                                  else "n/a"))
    print("  " + verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
