#!/usr/bin/env python3
"""Round-9 Stage 0 (D) reporting (claude-reply-8dddf38 sec.1).

Companion to the registered L3 scorer (analyze_l3_deploy.py, the
O3 deployment copy: stock analyze_l3.py with DELTA = 0.0075). The
stock scorer's aggregation counts unfinished worlds in one global
integrity counter; the (D) condition requires more, computed here
from the same jobs + label rows:

  (i)   unfinished-world share per candidate role (teacher pick /
        prior pick) and pooled. A candidate's share is
        unfinished / (finished + unfinished) over that candidate's
        rows; error rows (result carries "error", or a null result)
        are counted separately and never enter a share.
  (ii)  the paired-n distribution: per job, the number of worlds
        both candidates finished (the primary read's n_worlds) --
        min / p25 / median / mean / p75 / max, plus bucket counts.
  (iii) the SENSITIVITY read: worlds where BOTH candidates have a
        non-error row are scored with unfinished = draw (score
        0.5, the instrument's own price for a game that does not
        end). Per-job sensitivity diff = mean over those worlds of
        (teacher score - prior score); the read is the mean over
        jobs with a game-clustered bootstrap CI (the scorer's own
        cluster_bootstrap, imported), plus per-game gain at
        TEACHER_GAMES = 400.
  (iv)  the registered condition, printed with its inputs: if the
        pooled unfinished share exceeds 20%, a null (CI includes
        0) or negative (mean <= 0) primary read is
        INSTRUMENT-LIMITED and cannot trigger CLOSE at Stage 0; a
        positive read (mean > 0 with CI lower > 0) stands either
        way.

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--pass-name", required=True)
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
    #                          ("unfinished", None) | ("error", None)}
    worlds = defaultdict(dict)
    role_counts = {"teacher": defaultdict(int), "prior": defaultdict(int)}
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
        res = r.get("result")
        if not isinstance(res, dict) or "error" in res:
            kind = "error"
        elif int(res.get("finished") or 0) == 0:
            kind = "unfinished"
        else:
            kind = "finished"
        role_counts[role]["rows"] += 1
        role_counts[role][kind] += 1
        prev = worlds[(snap, cand)].get(int(r["world"]))
        if prev is None:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, float(res["outcome"]) if kind == "finished"
                else None)

    def share(role):
        c = role_counts[role]
        denom = c["finished"] + c["unfinished"]
        return (c["unfinished"] / denom) if denom else None

    sh_t, sh_p = share("teacher"), share("prior")
    fin = sum(role_counts[r]["finished"] for r in role_counts)
    unf = sum(role_counts[r]["unfinished"] for r in role_counts)
    sh_pool = (unf / (fin + unf)) if (fin + unf) else None

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

    # ---- sensitivity read: unfinished worlds scored as draws (0.5)
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
            if kt == "error" or kp == "error":
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
               "share_pooled": sh_pool},
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
    print("UNFINISHED WORLDS (error rows counted apart, never in a "
          "share):")
    for role in ("teacher", "prior"):
        c = role_counts[role]
        print("  %-7s rows %d: finished %d, unfinished %d, error %d; "
              "share %s" % (role, c["rows"], c["finished"],
                            c["unfinished"], c["error"],
                            pct(share(role)) if share(role) is not None
                            else "n/a"))
    print("  pooled : finished %d, unfinished %d; share %s"
          % (fin, unf, pct(sh_pool) if sh_pool is not None else "n/a"))
    print("PAIRED-N (finished worlds shared by both candidates, "
          "per scored job):")
    print("  min %s, p25 %s, median %s, mean %s, p75 %s, max %s; "
          "buckets %s; jobs missing %d"
          % (paired_n["min"], paired_n["p25"], paired_n["median"],
             ("%.2f" % paired_n["mean"]) if paired_n["mean"] is not None
             else "n/a", paired_n["p75"], paired_n["max"],
             paired_n["buckets"], paired_n["jobs_missing"]))
    print("SENSITIVITY (unfinished worlds scored as draws, 0.5):")
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
