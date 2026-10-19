#!/usr/bin/env python3
"""Round-3 pairing (Claude R6): for each seed, map gamename -> trace
file per arm from the driver rows, run the classifier on the arm
pairs, and emit one table with outcome fields (R3) beside verdicts.

Usage: r3_pair.py <arm>=<rows.jsonl>,<logdir> [<arm>=...]
Example: r3_pair.py raw=/tmp/r3_raw_s1.jsonl,/tmp/r3_raw_s1_log \
                    ghost=/tmp/r3_ghost_s1.jsonl,/tmp/r3_ghost_s1_log
Pairs are formed against the FIRST arm listed.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(HERE, "classify_divergence.py")
PAIRS_FIELDS = ("winner", "turns", "steps", "p1life", "p2life")


def load_arm(spec):
    name, rest = spec.split("=", 1)
    rows_path, logdir = rest.split(",", 1)
    games = {}
    for ln in open(rows_path):
        r = json.loads(ln)
        if r.get("gamename"):
            games[r["seed"]] = r
    return name, games, logdir


def main():
    arms = [load_arm(s) for s in sys.argv[1:]]
    base_name, base_games, base_log = arms[0]
    print("| seed | pair | verdict | class | seq | outcome equal |")
    print("|---|---|---|---|---|---|")
    for seed in sorted(base_games):
        brow = base_games[seed]
        btrace = os.path.join(base_log, "trace",
                              "trace_%s.jsonl" % brow["gamename"])
        for name, games, logdir in arms[1:]:
            orow = games.get(seed)
            if orow is None:
                print(f"| {seed} | {base_name} vs {name} | MISSING_GAME "
                      f"| - | - | - |")
                continue
            otrace = os.path.join(logdir, "trace",
                                  "trace_%s.jsonl" % orow["gamename"])
            out = subprocess.run([sys.executable, CLASSIFIER,
                                  btrace, otrace],
                                 capture_output=True, text=True)
            v = json.loads(out.stdout.strip())
            eq = all(brow.get(k) == orow.get(k) for k in PAIRS_FIELDS)
            print(f"| {seed} | {base_name} vs {name} | {v['class']} "
                  f"| {v['class']} | {v.get('first_diff_seq')} | {eq} |")


if __name__ == "__main__":
    main()
