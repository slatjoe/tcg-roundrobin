#!/usr/bin/env python3
"""pilot_prep.py - build the round-8 pilot's label jobs
(claude-reply-a076148 sec.3, the corrected V1/V2 design).

Two job sets:

v1 (--mode v1): the pilot capture's contested states. The pilot
first captures the first 20 corpus games (seeds 10001-10020,
heur seat-1 stream, run_capture_corpus.sh PILOT_CAPTURE=1);
their snap index rows carry the full job shape (cands, selected,
priors, prior_pick, native live state) directly - no join. Every
CONTESTED row becomes a V1 job (uncontested rows are skipped:
they are never labeled). Expected ~540 jobs. Run A's labels of
these are ordinary corpus labels (the pilot capture IS the
corpus's first 20 games); run B is the self-consistency draw.

v2 (--mode v2): 100 gate-fleet overturn snapshots, stratified
across the 8 teacher streams, drawn from the PRESERVED copy of
the gate fleet's snap dirs (default
/home/joe/tcg/gate_r4_v2_preserve - durable disk; the original
/tmp/gate_r4 sits on tmpfs and is never read). Layout of the
copy: {stream}_snaps/ snap dirs + teacher_snap_index.jsonl, and
{stream}_log_search_stats.jsonl. The index rows carry the LIVE
pick (teacher_pick) but not `selected`/`priors`; those join from
the stream's stat rows (within a stream, a game's overturn stat
rows in file order are its decisions in order; the index rows'
hcount is that same order - verified on game 725976967 at build
time). The join asserts pick, prior_pick and branch equality per
sampled row and aborts on any mismatch. The truth file carries,
per snap, the live pick AND the live per-candidate means /
n_worlds / selected list - the mechanism check's live side
(claude-reply-a076148 sec.3). Decide snapshots only overturns,
so V2's population is the overturn side by construction.

Draws are seeded (Random(20261025)); V2 quotas are 13,13,13,13,
12,12,12,12 across the 8 streams (any stream shortfall is topped
up from the remaining pool, still seeded).

Outputs (in --out dir): {v1,v2}_jobs.jsonl (labeler job shape);
v2 also pilot_v2_truth.jsonl.
"""
import argparse
import glob
import json
import random
from collections import defaultdict

STREAMS = [f"gate_c{c}_teacher_s{s}" for c in (1, 2, 3, 4)
           for s in (1, 2)]


def prep_v1(corpus, out):
    idx_path = (corpus.rstrip("/")
                + "/heur_s1_log/snaps/teacher_snap_index.jsonl")
    jobs = []
    n_unc = 0
    for ln in open(idx_path):
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("uncontested"):
            n_unc += 1
            continue
        jobs.append({
            "snap_dir": (corpus.rstrip("/") + "/heur_s1_log/snaps/"
                         + r["snap"]),
            "snap": r["snap"], "game": r["game"],
            "player": r["player"], "branch": r["branch"],
            "turn": r["turn"], "cands": r["cands"],
            "selected": r["selected"], "priors": r["priors"],
            "prior_pick": r["prior_pick"],
        })
    with open(out + "/v1_jobs.jsonl", "w") as fh:
        for j in jobs:
            fh.write(json.dumps(j) + "\n")
    print(f"v1 jobs (contested states of capture games "
          f"10001-10020): {len(jobs)}; uncontested skipped: {n_unc}")


def load_stream(preserve, stream):
    idx = [json.loads(ln) for ln in
           open(f"{preserve}/{stream}_snaps/teacher_snap_index.jsonl")
           if ln.strip()]
    stats = [json.loads(ln) for ln in
             open(f"{preserve}/{stream}_log_search_stats.jsonl")
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


def prep_v2(preserve, out, n_target=100):
    per = {}
    total = 0
    for st in STREAMS:
        per[st] = load_stream(preserve, st)
        total += len(per[st])
    print(f"preserved gate snap index rows (live overturn pairs): "
          f"{total}")

    rng = random.Random(20261025)
    quotas = [13, 13, 13, 13, 12, 12, 12, 12]
    chosen = []
    used = set()
    for st, q in zip(STREAMS, quotas):
        take = rng.sample(per[st], min(q, len(per[st])))
        for row, s in take:
            chosen.append((st, row, s))
            used.add(row["snap"])
    if len(chosen) < n_target:
        pool = [(st, row, s) for st in STREAMS
                for (row, s) in per[st] if row["snap"] not in used]
        for st, row, s in rng.sample(pool, n_target - len(chosen)):
            chosen.append((st, row, s))
    assert len(chosen) == n_target, len(chosen)

    jobs, truth = [], []
    for st, row, s in chosen:
        jobs.append({
            "snap_dir": f"{preserve}/{st}_snaps/{row['snap']}",
            "snap": row["snap"], "game": row["game"],
            "player": row["player"], "branch": row["branch"],
            "turn": row["turn"], "cands": row["cands"],
            "selected": s["selected"], "priors": s["priors"],
            "prior_pick": row["prior_pick"],
        })
        truth.append({
            "snap": row["snap"], "stream": st,
            "teacher_pick": row["teacher_pick"],
            "prior_pick": row["prior_pick"],
            "selected": s["selected"], "means": s["means"],
            "n_worlds": s["n_worlds"],
            "mean_diff": row["mean_diff"], "se_diff": row["se_diff"],
        })
    with open(out + "/v2_jobs.jsonl", "w") as fh:
        for j in jobs:
            fh.write(json.dumps(j) + "\n")
    with open(out + "/pilot_v2_truth.jsonl", "w") as fh:
        for t in truth:
            fh.write(json.dumps(t) + "\n")
    print(f"v2 jobs written: {len(jobs)} (join asserted on all; "
          f"stratified across the 8 streams)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["v1", "v2"], required=True)
    ap.add_argument("--corpus", default="/home/joe/tcg/distill_corpus")
    ap.add_argument("--preserve",
                    default="/home/joe/tcg/gate_r4_v2_preserve")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.mode == "v1":
        prep_v1(a.corpus, a.out)
    else:
        prep_v2(a.preserve, a.out)


if __name__ == "__main__":
    main()
