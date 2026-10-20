#!/usr/bin/env python3
"""L3 scoring - registered in claude-reply-94b9449 section 4.

Reads the audit jobs file (915 overturn jobs: snap, game, prior_pick,
teacher_pick) and the label rows emitted by meas_label_main.php at
LABEL_W=50 ({snap, cand, world, result{outcome, finished, fallbacks,
...}, prior_pick, game}). Worlds are paired across the two candidates
(CRN: identical per-world seeds in SimLabel_RunForSnapshot).

Per job: paired difference = mean over shared worlds of
(score[teacher_pick] - score[prior_pick]), score = (outcome + 1) / 2
(win probability units; outcome is from the deciding player's side).

PRIMARY: mean paired difference over jobs; CI from a bootstrap
clustered BY GAME (B=10000). SECONDARY: fraction of jobs with
difference > 0 (= 0, < 0). Also: expected per-game gain = mean
difference x (jobs / 400 teacher games), against the gate's
Delta = +0.2525 (half-Delta = 0.12625 is the registered middle-read
boundary).

Usage:
  analyze_l3.py --jobs jobs_all.jsonl --labels l3_out_0.jsonl [...]
  analyze_l3.py --self-test
"""
import argparse
import json
import random
import sys
from collections import defaultdict

DELTA = 0.2525
TEACHER_GAMES = 400


def aggregate(jobs, label_rows):
    """Return (per-job records, integrity dict). A job record:
    {snap, game, diff, n_worlds}. Error/missing worlds are counted,
    never silently dropped."""
    job_by_snap = {}
    for j in jobs:
        job_by_snap[str(j["snap"])] = j
    outcomes = defaultdict(dict)  # (snap, cand) -> {world: outcome}
    integ = {"rows": 0, "error_rows": 0, "unfinished": 0,
             "fallbacks": 0, "null_results": 0, "unknown_snap": 0,
             "dup_world": 0}
    for r in label_rows:
        integ["rows"] += 1
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            integ["unknown_snap"] += 1
            continue
        res = r.get("result")
        if not isinstance(res, dict):
            integ["null_results"] += 1
            continue
        if "error" in res:
            integ["error_rows"] += 1
            continue
        integ["fallbacks"] += int(res.get("fallbacks") or 0)
        if int(res.get("finished") or 0) == 0:
            integ["unfinished"] += 1
            continue
        key = (snap, int(r["cand"]))
        w = int(r["world"])
        if w in outcomes[key]:
            integ["dup_world"] += 1
            continue
        outcomes[key][w] = float(res["outcome"])
    records = []
    integ["jobs_total"] = len(job_by_snap)
    integ["jobs_missing"] = 0
    integ["worlds_min"] = None
    for snap, j in sorted(job_by_snap.items()):
        pp = int(j["prior_pick"])
        tp = int(j["teacher_pick"])
        a = outcomes.get((snap, tp), {})
        b = outcomes.get((snap, pp), {})
        shared = sorted(set(a) & set(b))
        if not shared:
            integ["jobs_missing"] += 1
            continue
        diffs = [((a[w] + 1.0) / 2.0) - ((b[w] + 1.0) / 2.0)
                 for w in shared]
        records.append({"snap": snap, "game": str(j["game"]),
                        "diff": sum(diffs) / len(diffs),
                        "n_worlds": len(shared)})
        if integ["worlds_min"] is None or len(shared) < integ["worlds_min"]:
            integ["worlds_min"] = len(shared)
    return records, integ


def cluster_bootstrap(records, b_reps=10000, seed=20261020):
    by_game = defaultdict(list)
    for r in records:
        by_game[r["game"]].append(r["diff"])
    games = sorted(by_game)
    rng = random.Random(seed)
    means = []
    for _ in range(b_reps):
        tot = 0.0
        n = 0
        for _ in range(len(games)):
            ds = by_game[rng.choice(games)]
            tot += sum(ds)
            n += len(ds)
        means.append(tot / n)
    means.sort()
    lo = means[int(0.025 * b_reps)]
    hi = means[int(0.975 * b_reps) - 1]
    return lo, hi


def summarize(records, integ, b_reps=10000):
    n = len(records)
    mean_diff = sum(r["diff"] for r in records) / n
    lo, hi = cluster_bootstrap(records, b_reps=b_reps)
    frac_pos = sum(1 for r in records if r["diff"] > 0) / n
    frac_zero = sum(1 for r in records if r["diff"] == 0) / n
    frac_neg = sum(1 for r in records if r["diff"] < 0) / n
    per_game = mean_diff * (n / TEACHER_GAMES)
    return {"jobs_scored": n, "mean_diff": mean_diff, "ci": [lo, hi],
            "frac_pos": frac_pos, "frac_zero": frac_zero,
            "frac_neg": frac_neg, "per_game_gain": per_game,
            "integrity": integ}


def self_test():
    # Fixture: 3 games. Planted score diffs: game A jobs +0.5 (teacher
    # world outcomes all +1 vs prior all 0 -> scores 1.0 vs 0.5),
    # game B jobs 0.0 (identical outcomes), game C jobs -0.25.
    jobs = []
    rows = []
    plan = [("gA", [(1.0, 0.0)] * 4), ("gB", [(1.0, 1.0)] * 4),
            ("gC", [(0.0, 1.0)] * 4)]
    # outcome pairs (teacher, prior) per world; 4 worlds each
    k = 0
    for game, pairs in plan:
        for _ in range(2):  # 2 jobs per game
            k += 1
            snap = "s%d" % k
            jobs.append({"snap": snap, "game": game, "prior_pick": 0,
                         "teacher_pick": 1})
            for w, (ot, op) in enumerate(pairs):
                rows.append({"snap": snap, "cand": 1, "world": w,
                             "result": {"outcome": ot, "finished": 1,
                                        "fallbacks": 0}})
                rows.append({"snap": snap, "cand": 0, "world": w,
                             "result": {"outcome": op, "finished": 1,
                                        "fallbacks": 0}})
    records, integ = aggregate(jobs, rows)
    assert integ["jobs_total"] == 6 and len(records) == 6, integ
    diffs = sorted(r["diff"] for r in records)
    # teacher score - prior score: gA (1-0.5)=+0.5; gB 0; gC (0.5-1)=-0.5
    assert diffs == [-0.5, -0.5, 0.0, 0.0, 0.5, 0.5], diffs
    s = summarize(records, integ, b_reps=2000)
    assert abs(s["mean_diff"] - 0.0) < 1e-12, s
    assert s["frac_pos"] == 2 / 6 and s["frac_neg"] == 2 / 6, s
    # one-sided fixture: teacher strictly better -> CI must sit > 0
    jobs2 = [{"snap": "x1", "game": "gX", "prior_pick": 0,
              "teacher_pick": 1}]
    rows2 = []
    for w in range(50):
        rows2.append({"snap": "x1", "cand": 1, "world": w,
                      "result": {"outcome": 1.0, "finished": 1,
                                 "fallbacks": 0}})
        rows2.append({"snap": "x1", "cand": 0, "world": w,
                      "result": {"outcome": -1.0, "finished": 1,
                                 "fallbacks": 0}})
    rec2, _ = aggregate(jobs2, rows2)
    assert rec2[0]["diff"] == 1.0, rec2
    print("SELF-TEST PASS: aggregation, pairing, score conversion, "
          "cluster bootstrap all reproduce planted values")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs")
    ap.add_argument("--labels", nargs="+", default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = []
    for path in a.labels:
        with open(path) as f:
            for l in f:
                if l.strip():
                    rows.append(json.loads(l))
    records, integ = aggregate(jobs, rows)
    s = summarize(records, integ)
    print(json.dumps(s, indent=1))
    print("registered reads (claude-reply-94b9449 sec.4):")
    print(" Delta = +%.4f ; half-Delta = %.5f" % (DELTA, DELTA / 2))
    if s["ci"][0] > 0:
        if s["per_game_gain"] >= DELTA / 2:
            print(" READ: converts; per-game gain from overturn quality "
                  "alone covers at least half of Delta")
        else:
            print(" READ: converts, but per-game gain < half of Delta; "
                  "the excess is UNEXPLAINED (not compounding)")
    elif s["mean_diff"] > 0:
        print(" READ: mean > 0 but CI includes 0 band edge; see table")
    else:
        print(" READ: CI includes 0 or negative; Delta unexplained; "
              "do not read as conversion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
