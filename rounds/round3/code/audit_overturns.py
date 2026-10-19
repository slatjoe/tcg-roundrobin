#!/usr/bin/env python3
"""G4 overturn audit - job emission half (the relabel RUN is
post-gate work; this script only collects and emits).

Reads teacher stat rows for overturn decisions (contested rows
with overturn == 1, equivalently pick != prior_pick) and the
TEACHER_SNAP_DIR snapshot indexes (teacher_snap_index.jsonl,
written by SimTeacher_Decide on every overturn when
TEACHER_SNAP_DIR is set). Samples up to N overturn snapshots
(seeded RNG) and emits labeler jobs in the format
meas_label_main.php consumes:

  {snap_dir, snap, game, player, branch, cands, selected,
   prior_pick, teacher_pick}

with selected = the two picks under audit (the overturn pick and
the prior pick). The post-gate relabel runs those jobs at k=50
worlds (LABEL_W=50) with fresh determinized rollouts under the
current labeler, and the fraction where the overturn pick beats
the prior pick - with its CI - is the realized conversion per
overturn (G4).

The snapshot index is the authoritative snapshot source (only
overturns snapshot); the stat-side overturn count is reported
alongside as a cross-check.

Usage:
  audit_overturns.py --snap-dir DIR [--snap-dir DIR ...] \
      --stats STATS.jsonl [STATS.jsonl ...] --out JOBS.jsonl \
      [--sample 100] [--seed 20261019]
"""
import argparse
import json
import os
import random
import sys


def load_jsonl(path):
    out = []
    if path and os.path.exists(path):
        with open(path) as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap-dir", action="append", required=True)
    ap.add_argument("--stats", nargs="+", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261019)
    a = ap.parse_args()

    stat_overturns = 0
    stat_contested = 0
    for path in a.stats:
        for r in load_jsonl(path):
            if r.get("teacher") == 1 and r.get("contested") == 1:
                stat_contested += 1
                if r.get("overturn") == 1 or (
                        r.get("pick") is not None
                        and r.get("prior_pick") is not None
                        and r.get("pick") != r.get("prior_pick")):
                    stat_overturns += 1

    entries = []
    for sd in a.snap_dir:
        idx = os.path.join(sd, "teacher_snap_index.jsonl")
        for e in load_jsonl(idx):
            e = dict(e)
            e["_snap_dir"] = sd
            entries.append(e)

    rng = random.Random(a.seed)
    chosen = entries
    sampled = False
    if len(entries) > a.sample:
        chosen = rng.sample(entries, a.sample)
        sampled = True

    jobs = []
    for e in chosen:
        snap = e["snap"]
        jobs.append({
            "snap_dir": os.path.join(e["_snap_dir"], snap),
            "snap": snap,
            "game": str(e["game"]),
            "player": e["player"],
            "branch": e["branch"],
            "cands": e["cands"],
            "selected": sorted({int(e["teacher_pick"]),
                                int(e["prior_pick"])}),
            "prior_pick": e["prior_pick"],
            "teacher_pick": e["teacher_pick"],
        })
    with open(a.out, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    print("stat overturns: %d of %d contested rows"
          % (stat_overturns, stat_contested))
    print("snapshot index entries: %d" % len(entries))
    print("jobs emitted: %d%s (sample seed %d, cap %d)"
          % (len(jobs), " (sampled)" if sampled else "",
             a.seed, a.sample))
    print("relabel (post-gate): MEAS_JOBS=%s LABEL_W=50 "
          "php meas_label_main.php <deck> <deck> --policy-search "
          "--games 1" % a.out)
    if stat_overturns and not entries:
        print("WARNING: stat rows show overturns but no snapshot "
              "index entries were found - TEACHER_SNAP_DIR was not "
              "set for those games.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
