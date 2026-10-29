#!/usr/bin/env python3
"""Round-9 L3 primaries, CAP-ALIGNED co-report
(round-10 sec.14, 2026-10-29; claude-reply-28c2065
sec.2 / sec.3.3: "the same co-report for round 9 --
Stage 2 and Stage 3 L3 primaries recomputed
cap-aligned and printed beside the originals").

Recomputes both stages' L3 primaries from the
PUBLISHED label rows (data/stage2|stage3) under two
scorings of the same rows:

  AS-RUN     score = 1.0 if outcome > 0 else 0.0
             (stage3_attr_analyze.score_primary,
             the registered draw = 0 read);
  CAP-ALIGNED score = 1.0 if outcome > 0 AND the
             world ended by turn 61, else 0.0 -- a
             decisive world ending after turn 61 is
             a horizon draw under the live
             instrument (its cap trigger is
             currentTurn 62; play_game.php scores the
             game a draw the moment currentTurn
             reaches 62, so turn 61 is the last
             decisive turn), and a draw scores 0
             under the registered primary.

The read construction mirrors
stage3_attr_analyze.run_read exactly (worlds paired
by world index across each job's two candidates,
refusal worlds skipped, only worlds finished in
BOTH candidates counted, job diff = mean of the
per-world differences, primary = mean over jobs,
CI by analyze_l3.cluster_bootstrap at its defaults,
10,000 reps, seed 20261020). The guards are the
registered ones: the label-tuple audit (projection
on the settings' label_tuple keys) and the
world-count guard (exactly --expect-rows rows per
(snap, candidate)).

VERIFICATION before any cap-aligned number: the
as-run recomputation must reproduce the published
read's primary point estimate and job count exactly
(the read JSON is passed as --published-read); a
mismatch aborts. The CI is NOT expected to be
bit-identical to the published one across
recomputations -- the bootstrap is seeded but the
published Stage 2/3 reads and Claude's sec.2
recomputation already differ in the third decimal
for exactly this reason; the addendum doc states
the seed and reps so the reader can see which
differences are bootstrap draw and which are the
rule.

Also reported per stage: finished worlds, decisive
worlds (outcome > 0), decisive worlds ending after
turn 61 / after turn 63, and the end-turn median /
max of horizon-flagged worlds -- the sec.2
overshoot table, recomputed.

Usage: capalign_l3.py --jobs data/stageX/jobs_all.jsonl
  --labels data/stageX/labels_all.jsonl.gz
  --settings code/settings_stageX.json
  --published-read data/stageX/<read>.json
  --games-report data/stageX/games_report.json
  [--expect-rows 50] [--json-out out.json]
"""
import argparse
import gzip
import importlib.util
import json
import statistics
import sys
from collections import defaultdict

HERE = __file__.rsplit("/", 1)[0]
CAP_LAST_DECISIVE_TURN = 61


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, HERE + "/" + name + ".py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def score_primary(res):
    return 1.0 if float(res["outcome"]) > 0 else 0.0


def score_capaligned(res):
    if float(res["outcome"]) > 0 and int(
            res.get("turns") or 0) <= CAP_LAST_DECISIVE_TURN:
        return 1.0
    return 0.0


def open_text(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--published-read", required=True)
    ap.add_argument("--games-report", required=True)
    ap.add_argument("--expect-rows", type=int, default=50)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")
    settings = json.load(open(a.settings))
    published = json.load(open(a.published_read))
    grep = json.load(open(a.games_report))
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = []
    for path in a.labels:
        with open_text(path) as f:
            for l in f:
                if l.strip():
                    rows.append(json.loads(l))
    job_by_snap = {str(j["snap"]): j for j in jobs}

    LT = settings["label_tuple"]
    bad_stamp = 0
    for r in rows:
        s = r.get("setting")
        if not isinstance(s, dict) or {
                k: s.get(k) for k in LT} != LT:
            bad_stamp += 1
    if bad_stamp:
        print("ABORT: %d label rows carry a setting stamp "
              "!= the registered label tuple" % bad_stamp)
        return 2

    pair_counts = defaultdict(int)
    for r in rows:
        if str(r.get("snap")) in job_by_snap:
            pair_counts[(str(r["snap"]), int(r["cand"]))] += 1
    for snap, j in sorted(job_by_snap.items()):
        for cand in sorted({int(j["teacher_pick"]),
                            int(j["prior_pick"])}):
            n = pair_counts.get((snap, cand), 0)
            if n != a.expect_rows:
                print("ABORT: world-count guard: job %s "
                      "candidate %d has %d rows, expected "
                      "exactly %d" % (snap, cand, n,
                                      a.expect_rows))
                return 2

    worlds = defaultdict(dict)
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand not in (int(j["teacher_pick"]),
                        int(j["prior_pick"])):
            continue
        kind, _e = s0.classify(r.get("result"))
        if int(r["world"]) not in worlds[(snap, cand)]:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, r.get("result"))

    def run_read(scorefn):
        recs = []
        for snap, j in sorted(job_by_snap.items()):
            tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
            wt = worlds.get((snap, tp), {})
            wp = worlds.get((snap, pp), {})
            diffs = []
            for w in sorted(set(wt) & set(wp)):
                kt, rt = wt[w]
                kp, rp = wp[w]
                if kt == "refusal" or kp == "refusal":
                    continue
                if kt != "finished" or kp != "finished":
                    continue
                diffs.append(scorefn(rt) - scorefn(rp))
            if diffs:
                recs.append({"snap": snap,
                             "game": str(j["game"]),
                             "diff": sum(diffs) / len(diffs),
                             "n_worlds": len(diffs)})
        if not recs:
            return {"jobs": 0, "mean_diff": None, "ci": None}
        mean = sum(r["diff"] for r in recs) / len(recs)
        lo, hi = stock.cluster_bootstrap(recs)
        return {"jobs": len(recs), "mean_diff": mean,
                "ci": [lo, hi]}

    # ---- overshoot tallies over the paired worlds --------
    fin_worlds = 0
    decisive = 0
    dec_after61 = 0
    dec_after63 = 0
    horizon_turns = []
    for snap, j in job_by_snap.items():
        for cand in (int(j["teacher_pick"]),
                     int(j["prior_pick"])):
            for _w, (kind, res) in worlds.get(
                    (snap, cand), {}).items():
                if kind != "finished":
                    continue
                fin_worlds += 1
                if int(res.get("horizon") or 0) == 1:
                    horizon_turns.append(
                        int(res.get("turns") or 0))
                elif float(res["outcome"]) > 0:
                    decisive += 1
                    t = int(res.get("turns") or 0)
                    if t > CAP_LAST_DECISIVE_TURN:
                        dec_after61 += 1
                    if t > 63:
                        dec_after63 += 1
    overshoot = {
        "finished_worlds": fin_worlds,
        "decisive_worlds": decisive,
        "decisive_after_turn61": dec_after61,
        "decisive_after_turn63": dec_after63,
        "horizon_worlds": len(horizon_turns),
        "horizon_turns_median": (
            statistics.median(horizon_turns)
            if horizon_turns else None),
        "horizon_turns_max": (
            max(horizon_turns) if horizon_turns else None)}

    asrun = run_read(score_primary)
    pub = published["primary"]
    if asrun["jobs"] != pub["jobs"] or \
            abs(asrun["mean_diff"] - pub["mean_diff"]) > 1e-12:
        print("ABORT: as-run recomputation does not "
              "reproduce the published primary: got "
              "jobs %s mean %s; published jobs %s mean %s"
              % (asrun["jobs"], asrun["mean_diff"],
                 pub["jobs"], pub["mean_diff"]))
        return 2
    cap = run_read(score_capaligned)
    opg = grep.get("overturns_per_game")
    out = {
        "jobs": len(jobs), "label_rows": len(rows),
        "as_run": {"jobs": asrun["jobs"],
                   "mean_diff": asrun["mean_diff"],
                   "ci": asrun["ci"],
                   "per_game_gain": (
                       asrun["mean_diff"] * opg
                       if opg is not None else None),
                   "published_ci": pub["ci"],
                   "verification": "point estimate and "
                                   "job count reproduce "
                                   "the published read "
                                   "exactly"},
        "cap_aligned": {"jobs": cap["jobs"],
                        "mean_diff": cap["mean_diff"],
                        "ci": cap["ci"],
                        "per_game_gain": (
                            cap["mean_diff"] * opg
                            if opg is not None else None)},
        "live_overturns_per_game": opg,
        "bootstrap": {"reps": 10000, "seed": 20261020,
                      "note": "analyze_l3.cluster_"
                              "bootstrap defaults; CIs "
                              "differ across "
                              "recomputations in the "
                              "third decimal by "
                              "bootstrap draw"},
        "overshoot": overshoot}
    print("L3 primary AS-RUN (verified): jobs %d, mean "
          "diff %s CI [%s, %s], per-game gain %s"
          % (asrun["jobs"], pct(asrun["mean_diff"]),
             pct(asrun["ci"][0]), pct(asrun["ci"][1]),
             pct(out["as_run"]["per_game_gain"])))
    print("L3 primary CAP-ALIGNED: jobs %d, mean diff "
          "%s CI [%s, %s], per-game gain %s"
          % (cap["jobs"], pct(cap["mean_diff"]),
             pct(cap["ci"][0]), pct(cap["ci"][1]),
             pct(out["cap_aligned"]["per_game_gain"])))
    print("overshoot: %d finished worlds; %d decisive, "
          "of which %d ended after turn 61 (%d after "
          "turn 63); %d horizon worlds, end turns "
          "median %s max %s"
          % (fin_worlds, decisive, dec_after61,
             dec_after63, len(horizon_turns),
             overshoot["horizon_turns_median"],
             overshoot["horizon_turns_max"]))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
