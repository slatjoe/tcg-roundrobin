#!/usr/bin/env python3
"""pilot_prep.py - draw the pilot's 20 label jobs from the Fai
gate fleet's surviving overturn snapshots (round 8 pilot,
build-package sec.3).

Source (verified on the box at build time): /tmp/gate_r4 holds the
gate fleet's per-stream snap dirs (gate_c{1..4}_teacher_s{1,2}_
snaps/), each with a teacher_snap_index.jsonl - 915 rows in total,
matching the fleet's 915 overturn stat rows. Each index row
carries the snapshot and the LIVE pick (teacher_pick), but not
the evaluated candidate set: Decide's snapshot block records the
full candidate list, while "selected" (top-3 + prior >= 0.10,
cap 4) and "priors" live on the decision's stat row. This prep
JOINS them: within a stream, a game's overturn stat rows in file
order are its decisions in order, and the index rows' hcount is
that same order (verified at build time on game 725976967: 3
overturn rows <-> 3 index rows, picks / priors / branches equal).
The join asserts pick, prior_pick and branch equality for every
sampled row and aborts on any mismatch - a bad join must never
reach the labeler.

Decide snapshots only overturns, so this population is the
overturn side; that is V2's registered limit (confirmations are
covered by V1's self-consistency split, pilot_report.py).

Draw: seeded (Random(20261025)), stratified across the 8 streams
(3,3,3,3,2,2,2,2 = 20), so both seats and all chunks appear.

Outputs (in --out dir): pilot_jobs.jsonl (labeler job shape, with
selected + priors joined), pilot_v2_truth.jsonl (live picks).
"""
import argparse
import glob
import json
import random
from collections import defaultdict


def load_stream(gate_out, stream):
    idx = [json.loads(ln) for ln in
           open(f"{gate_out}/{stream}_snaps/teacher_snap_index.jsonl")
           if ln.strip()]
    stats = [json.loads(ln) for ln in
             open(f"{gate_out}/{stream}_log/search_stats.jsonl")
             if ln.strip()]
    ov_by_game = defaultdict(list)
    for r in stats:
        if r.get("overturn") == 1:
            ov_by_game[str(r["game"])].append(r)
    joined = []
    for row in idx:
        ovs = ov_by_game[str(row["game"])]
        h = int(row["hcount"])
        assert 1 <= h <= len(ovs), \
            f"{row['snap']}: hcount {h} beyond {len(ovs)} overturn rows"
        s = ovs[h - 1]
        assert int(s["pick"]) == int(row["teacher_pick"]), \
            f"{row['snap']}: join pick mismatch"
        assert int(s["prior_pick"]) == int(row["prior_pick"]), \
            f"{row['snap']}: join prior mismatch"
        assert str(s["branch"]) == str(row["branch"]), \
            f"{row['snap']}: join branch mismatch"
        joined.append((row, s))
    return joined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-out", default="/tmp/gate_r4")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    streams = [f"gate_c{c}_teacher_s{s}" for c in (1, 2, 3, 4)
               for s in (1, 2)]
    per = {}
    total = 0
    for st in streams:
        per[st] = load_stream(a.gate_out, st)
        total += len(per[st])
    print(f"gate snap index rows (live overturn pairs): {total}")

    rng = random.Random(20261025)
    quotas = [3, 3, 3, 3, 2, 2, 2, 2]
    jobs, truth = [], []
    for st, q in zip(streams, quotas):
        for row, s in rng.sample(per[st], q):
            jobs.append({
                "snap_dir": f"{a.gate_out}/{st}_snaps/{row['snap']}",
                "snap": row["snap"], "game": row["game"],
                "player": row["player"], "branch": row["branch"],
                "turn": row["turn"], "cands": row["cands"],
                "selected": s["selected"], "priors": s["priors"],
                "prior_pick": row["prior_pick"],
            })
            truth.append({
                "snap": row["snap"], "teacher_pick": row["teacher_pick"],
                "prior_pick": row["prior_pick"],
                "mean_diff": row["mean_diff"], "se_diff": row["se_diff"],
            })
    with open(a.out + "/pilot_jobs.jsonl", "w") as fh:
        for j in jobs:
            fh.write(json.dumps(j) + "\n")
    with open(a.out + "/pilot_v2_truth.jsonl", "w") as fh:
        for t in truth:
            fh.write(json.dumps(t) + "\n")
    print(f"pilot jobs written: {len(jobs)} (join asserted on all)")


if __name__ == "__main__":
    main()
