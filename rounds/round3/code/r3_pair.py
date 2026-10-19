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
PAIRS_FIELDS = ("winner", "turns", "decisions", "p1life", "p2life",
                "gamestate_norm_sha")
MODE_PREFIX = {"raw": "policy: server", "teacher": "policy: search",
               "ghost": "policy: search", "shadow": "policy: search",
               "capture": "policy: search"}


def mode_ok(arm_name, row):
    """R11: the misbuild class we've hit twice, checked per seed -
    each arm's own mode line must match its arm, and no connect
    failures are tolerable."""
    want = MODE_PREFIX.get(arm_name)
    ml = row.get("mode_line") or ""
    return (want is not None and ml.startswith(want)
            and row.get("connect_failed", 0) == 0)


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
    print("| seed | pair | verdict | within-row hits | seq | outcome "
          "equal | modes ok |")
    print("|---|---|---|---|---|---|---|")
    for seed in sorted(base_games):
        brow = base_games[seed]
        btrace = os.path.join(base_log, "trace",
                              "trace_%s.jsonl" % brow["gamename"])
        for name, games, logdir in arms[1:]:
            orow = games.get(seed)
            if orow is None:
                print(f"| {seed} | {base_name} vs {name} | MISSING_GAME "
                      f"| - | - | - | - |")
                continue
            otrace = os.path.join(logdir, "trace",
                                  "trace_%s.jsonl" % orow["gamename"])
            out = subprocess.run([sys.executable, CLASSIFIER,
                                  btrace, otrace],
                                 capture_output=True, text=True)
            v = json.loads(out.stdout.strip())
            eq = all(brow.get(k) == orow.get(k) for k in PAIRS_FIELDS)
            mok = mode_ok(base_name, brow) and mode_ok(name, orow)
            verdict = v["class"] if mok else "INVALID_MODE"
            print(f"| {seed} | {base_name} vs {name} | {verdict} "
                  f"| {len(v.get('within_row_hits', []))} "
                  f"| {v.get('first_diff_seq')} | {eq} | {mok} |")


if __name__ == "__main__":
    main()
