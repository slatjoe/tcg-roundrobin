#!/usr/bin/env python3
"""Raw-arm timeout single re-run (timeout ruling 3).

A wall-clock timeout in the RAW arm is an engine hang, not a
score: the game is re-run ONCE. This helper finds the timeout
rows in a raw arm's driver row file, removes those rows, and
re-invokes paired_driver.py for exactly those seeds (the driver
resumes from the row file, so removed seeds are the only ones
replayed). If a re-run also times out, its fresh timeout row
stands and analyze_gate.py scores the raw arm 0.5 with the pair
kept, per the ruling.

Usage: gate_raw_retry.py --tree T --sock S --seat N --rows F \
    --logdir D [--timeout 700] [--deck PATH]
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--sock", required=True)
    ap.add_argument("--seat", type=int, required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--logdir", required=True)
    ap.add_argument("--timeout", type=int, default=700)
    ap.add_argument("--deck", default=None)
    a = ap.parse_args()
    if not os.path.exists(a.rows):
        print("no row file; nothing to retry")
        return 0
    rows = []
    timeout_seeds = []
    with open(a.rows) as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("invalid") == "timeout":
                timeout_seeds.append(r["seed"])
            else:
                rows.append(ln)
    if not timeout_seeds:
        print("no raw timeouts; nothing to retry")
        return 0
    with open(a.rows, "w") as f:
        for ln in rows:
            f.write(ln + "\n")
    for seed in timeout_seeds:
        cmd = [sys.executable, os.path.join(HERE, "paired_driver.py"),
               "--tree", a.tree, "--sock", a.sock,
               "--seat", str(a.seat), "--arm", "raw",
               "--seeds", str(seed), "--timeout", str(a.timeout),
               "--out", a.rows, "--logdir", a.logdir]
        if a.deck:
            cmd += ["--deck", a.deck]
        env = dict(os.environ)
        p = subprocess.run(cmd, env=env, capture_output=True,
                           text=True)
        status = "?"
        for ln in reversed(open(a.rows).read().splitlines()):
            r = json.loads(ln)
            if r["seed"] == seed:
                status = ("timeout again (scores 0.5, pair kept)"
                          if r.get("invalid") == "timeout"
                          else "completed winner=%s" % r.get("winner"))
                break
        print("raw retry seed %d: %s" % (seed, status))
        if p.returncode != 0:
            print("  driver stderr tail: %s"
                  % (p.stderr or "")[-300:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
