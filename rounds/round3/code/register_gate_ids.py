#!/usr/bin/env python3
"""G9 registry merge: add gate game ids (and overturn snapshot
ids) to the do-not-train registry as EVAL-ONLY, before any
analysis runs (Claude G9).

Registry format (existing): {"created", "n_games", "rule",
"version", "games": {game_id: source_tag}}. Existing entries are
never modified; an id that is already registered under another
tag is kept as-is and reported (a collision would matter).

Sources: the fleet's per-chunk gate_<chunk>_game_ids.txt files
(written by paired_driver.py under GATE_GAME_IDS_FILE) and the
teacher arms' teacher_snap_index.jsonl files (snapshot ids are
<snap> names, registered under a gate_snap tag). The chunk token
is read from each file's name/path (gate_c1_... -> c1).

Usage:
  register_gate_ids.py --registry REG.json [--out REG2.json] \
      --ids gate_c1_game_ids.txt [more files ...] \
      --snap-index PATH/teacher_snap_index.jsonl [more ...]
--out defaults to the registry path (in-place merge; pass a copy
path to demonstrate on a copy). Prints added counts, the new
total, and the sha256 of the written file.
"""
import argparse
import hashlib
import json
import os
import re
import sys


def chunk_token(path):
    m = re.search(r"(c\d+)", os.path.basename(path)) \
        or re.search(r"(c\d+)", path)
    return m.group(1) if m else "gate"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ids", nargs="+", default=[])
    ap.add_argument("--snap-index", nargs="+", default=[])
    a = ap.parse_args()
    out_path = a.out or a.registry
    with open(a.registry) as f:
        reg = json.load(f)
    games = reg.setdefault("games", {})
    added_games = 0
    added_snaps = 0
    collisions = []
    for path in a.ids:
        tag = "gate:%s" % chunk_token(path)
        with open(path) as f:
            for ln in f:
                gid = ln.strip()
                if not gid:
                    continue
                if gid in games:
                    if games[gid] != tag:
                        collisions.append((gid, games[gid], tag))
                    continue
                games[gid] = tag
                added_games += 1
    for path in a.snap_index:
        tag = "gate_snap:%s" % chunk_token(path)
        if not os.path.exists(path):
            print("WARNING: snap index not found: %s" % path)
            continue
        with open(path) as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                e = json.loads(ln)
                sid = str(e["snap"])
                if sid in games:
                    if games[sid] != tag:
                        collisions.append((sid, games[sid], tag))
                    continue
                games[sid] = tag
                added_snaps += 1
    reg["n_games"] = len(games)
    with open(out_path, "w") as f:
        json.dump(reg, f)
    h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    print("added game ids: %d | added snapshot ids: %d"
          % (added_games, added_snaps))
    print("registry total: %d games" % len(games))
    print("written: %s sha256 %s" % (out_path, h))
    for gid, old, new in collisions:
        print("COLLISION (kept existing): %s was %s, new source %s"
              % (gid, old, new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
