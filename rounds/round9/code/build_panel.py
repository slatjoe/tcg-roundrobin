#!/usr/bin/env python3
"""Round-9 Stage 1 panel builder (design sec.4.1; ruling
sec.4.1): the first 240 contested snapshots from the Stage-1
capture, at most 8 per game, in capture order.

Inputs are the capture streams' teacher_snap_index.jsonl
files (the paired driver's capture arm: every row is a
contested decision -- snapshot taken, prior pick played, no
rollout). Each stream is given as --stream PREFIX=PATH,
where PREFIX is that stream's TEACHER_SNAP_DIR (the paired
driver sets it to the capture logdir's snaps/ dir; the index
file itself lives in that same dir, and each snapshot at
PREFIX/<snap>); streams are read in argument order, which
is capture order (seat-1 stream, seat-2 stream, then any
extension blocks in run order).

A row without "selected"/"priors" is not a capture-arm
contested row and aborts the build (exit 2); a duplicated
snap aborts likewise. If the capture yields fewer than the
panel size, the builder still writes what it found, marks
the report incomplete, and exits 3 -- the registered
response is another 10-game capture block (design sec.4.1),
never a quiet shortfall.

Output jobs carry the label-job shape Stage 0 used:
{snap_dir, snap, game, player, branch, turn, cands,
selected, prior_pick}. snap_dir is PREFIX/<snap>, relative
to the run's OUT dir; the runner rewrites it to an absolute
path on its per-setting copies and asserts it exists.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", action="append", required=True,
                    help="PREFIX=INDEX_PATH, repeatable, in "
                         "capture order")
    ap.add_argument("--panel-size", type=int, default=240)
    ap.add_argument("--per-game-cap", type=int, default=8)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    rows_in = 0
    seen_snaps = set()
    per_game = Counter()
    branches = Counter()
    players = Counter()
    skipped_cap = 0
    panel = []
    for spec in a.stream:
        prefix, path = spec.split("=", 1)
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            rows_in += 1
            if "selected" not in r or "priors" not in r:
                print("ABORT: %s row %s is not a capture-arm "
                      "contested row (no selected/priors)"
                      % (path, r.get("snap")))
                return 2
            snap = str(r["snap"])
            if snap in seen_snaps:
                print("ABORT: duplicate snap %s across capture "
                      "streams" % snap)
                return 2
            seen_snaps.add(snap)
            if len(panel) >= a.panel_size:
                continue
            if per_game[str(r["game"])] >= a.per_game_cap:
                skipped_cap += 1
                continue
            per_game[str(r["game"])] += 1
            branches[str(r["branch"])] += 1
            players[int(r["player"])] += 1
            panel.append({
                "snap_dir": prefix + "/" + snap,
                "snap": snap, "game": str(r["game"]),
                "player": int(r["player"]),
                "branch": str(r["branch"]),
                "turn": int(r.get("turn") or 0),
                "cands": r["cands"],
                "selected": [int(x) for x in r["selected"]],
                "prior_pick": int(r["prior_pick"]),
            })

    with open(a.out, "w") as f:
        for j in panel:
            f.write(json.dumps(j) + "\n")
    report = {"states": len(panel),
              "complete": len(panel) >= a.panel_size,
              "panel_size": a.panel_size,
              "per_game_cap": a.per_game_cap,
              "games": len(per_game),
              "per_game": dict(sorted(per_game.items())),
              "branches": dict(sorted(branches.items())),
              "players": {str(k): v for k, v in
                          sorted(players.items())},
              "index_rows_total": rows_in,
              "skipped_by_cap": skipped_cap}
    with open(a.report, "w") as f:
        json.dump(report, f, indent=1)
    print("panel: %d states over %d games (branches %s; "
          "index rows %d, skipped by cap %d)"
          % (report["states"], report["games"], report["branches"],
             rows_in, skipped_cap))
    if not report["complete"]:
        print("SHORTFALL: panel has %d of %d states; extend the "
              "capture by a 10-game block and rebuild"
              % (len(panel), a.panel_size))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
