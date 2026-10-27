#!/usr/bin/env python3
"""Round-9 Stage 3 L3 jobs builder: every overturn the live
calibrated teacher captured in the Stage 3 games becomes one
label job (ruling sec.4.6). Streams are the 4 TEACHER blocks'
snap indexes only (t1a/t1b/t2a/t2b -- the raw arm captures no
overturns). Fork of build_s2_jobs.py: selected pair, abort
conditions, tuple stamp and sha256(game) mod 4 sharding are
identical in semantics; only the settings file (Stage 3's
label_tuple, the same L3-W50+H values) and naming change.

Inputs are the games streams' teacher_snap_index.jsonl files
(the paired driver's per-seat snap dirs, via the games
runner). Each index row is one overturn (the live Decide wrote
it only when overturn == 1): it carries snap, game, branch,
player, turn, the candidate RECORDS (cands), teacher_pick and
prior_pick. The job shape is the Stage 1 label shape plus the
registered L3 tuple stamp:

  {snap_dir, snap, game, player, branch, turn, cands,
   selected, prior_pick, teacher_pick, setting}

selected = the sorted unique {prior_pick, teacher_pick} --
exactly the pair the L3 labels (pair "va"). snap_dir is
PREFIX/<snap> from the --stream argument (the paired driver
set TEACHER_SNAP_DIR to that stream's snaps dir); the L3
runner rewrites it absolute on its shard copies and the
driver asserts the directory exists per job via the label
parent. A row missing cands/picks, or a duplicated snap,
aborts (exit 2). Jobs are also written sharded by
sha256(game) mod NSHARD (the Stage 0 pattern: a game's jobs
share a shard, so the game-clustered CI and the label seed
bases stay well-defined).

Usage:
  build_s3_jobs.py --stream PREFIX=INDEX_PATH [--stream ...]
      --settings settings_stage3.json --out jobs_all.jsonl
      --shard-prefix jobs_shard --report jobs_report.json
"""
import argparse
import hashlib
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", action="append", required=True,
                    help="PREFIX=INDEX_PATH, repeatable, in "
                         "games-runner stream order")
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard-prefix", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--nshard", type=int, default=4)
    a = ap.parse_args()

    settings = json.load(open(a.settings))
    label_tuple = settings["label_tuple"]

    jobs = []
    seen = set()
    rows_in = 0
    for spec in a.stream:
        prefix, path = spec.split("=", 1)
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            rows_in += 1
            for key in ("snap", "game", "cands", "teacher_pick",
                        "prior_pick"):
                if key not in r:
                    print("ABORT: %s row %s is not a live "
                          "overturn row (missing %s)"
                          % (path, r.get("snap"), key))
                    return 2
            snap = str(r["snap"])
            if snap in seen:
                print("ABORT: duplicate snap %s across games "
                      "streams" % snap)
                return 2
            seen.add(snap)
            tp, pp = int(r["teacher_pick"]), int(r["prior_pick"])
            if tp == pp:
                print("ABORT: snap %s has teacher_pick == "
                      "prior_pick (%d): not an overturn"
                      % (snap, tp))
                return 2
            jobs.append({
                "snap_dir": prefix + "/" + snap,
                "snap": snap, "game": str(r["game"]),
                "player": int(r["player"]),
                "branch": str(r["branch"]),
                "turn": int(r.get("turn") or 0),
                "cands": r["cands"],
                "selected": sorted({pp, tp}),
                "prior_pick": pp, "teacher_pick": tp,
                "setting": label_tuple,
            })

    with open(a.out, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    shards = {s: [] for s in range(a.nshard)}
    for j in jobs:
        s = int(hashlib.sha256(
            str(j["game"]).encode()).hexdigest(), 16) % a.nshard
        shards[s].append(j)
    counts = {}
    for s, rows in shards.items():
        with open("%s%d.jsonl" % (a.shard_prefix, s), "w") as f:
            for j in rows:
                f.write(json.dumps(j) + "\n")
        counts[str(s)] = len(rows)
    games = sorted({j["game"] for j in jobs})
    report = {"jobs": len(jobs), "games": len(games),
              "index_rows_total": rows_in,
              "shards": counts, "nshard": a.nshard,
              "label_tuple": label_tuple}
    with open(a.report, "w") as f:
        json.dump(report, f, indent=1)
    print("s3 jobs: %d overturns over %d games (index rows %d; "
          "shards %s)" % (len(jobs), len(games), rows_in, counts))
    if not jobs:
        print("ABORT: zero overturns captured - nothing to label")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
