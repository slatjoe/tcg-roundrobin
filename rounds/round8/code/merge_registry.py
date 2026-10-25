#!/usr/bin/env python3
"""merge_registry.py - merge game ids into the do-not-train
registry (the round-7 fleet-registry-merge pattern, generalized;
build-package sec.5).

Registry shape (verified on the box): {"created", "games":
{gid_str: tag}, "n_games", "rule", "version"}. The merge:
  * refuses to retag an existing id to a DIFFERENT tag (a
    collision is reported, never silently overwritten);
  * writes atomically (tmp + replace), keeps a timestamped
    backup next to the registry, and optionally drops a copy in
    a vault dir;
  * prints the new registry's sha256 - the gate analysis asserts
    the sha it was handed, so the merged registry is the one the
    analysis read from.

Usage: merge_registry.py --registry <path> --tag <tag>
  --ids <file> [--ids <file> ...] [--vault <dir>]
Id files: one game id per line (GATE_GAME_IDS_FILE shape).
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--ids", action="append", required=True)
    ap.add_argument("--vault")
    a = ap.parse_args()

    reg = json.load(open(a.registry))
    games = reg["games"]
    new_ids = []
    for path in a.ids:
        for ln in open(path):
            gid = ln.strip()
            if gid:
                new_ids.append(gid)
    added, dup_same, conflicts = 0, 0, []
    for gid in new_ids:
        if gid in games:
            if games[gid] == a.tag:
                dup_same += 1
            else:
                conflicts.append((gid, games[gid]))
        else:
            games[gid] = a.tag
            added += 1
    if conflicts:
        print(f"ABORT: {len(conflicts)} ids already registered "
              f"under other tags, e.g. {conflicts[:5]}",
              file=sys.stderr)
        sys.exit(1)
    reg["n_games"] = len(games)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    bak = f"{a.registry}.bak-{stamp}"
    shutil.copy2(a.registry, bak)
    tmp = a.registry + ".tmp"
    with open(tmp, "w") as f:
        json.dump(reg, f)
    os.replace(tmp, a.registry)
    sha = hashlib.sha256(open(a.registry, "rb").read()).hexdigest()
    print(f"merged: +{added} new (tag {a.tag}), {dup_same} already "
          f"under this tag; n_games={reg['n_games']}")
    print(f"backup: {bak}")
    print(f"registry sha256: {sha}")
    if a.vault:
        os.makedirs(a.vault, exist_ok=True)
        dst = os.path.join(a.vault,
                           f"do_not_train_registry_{stamp}.json")
        shutil.copy2(a.registry, dst)
        print(f"vault copy: {dst}")


if __name__ == "__main__":
    main()
