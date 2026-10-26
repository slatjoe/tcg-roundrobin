#!/usr/bin/env python3
"""fx_build_panel - known-answer fixture for
code/build_panel.py (first-240-in-capture-order, the
per-game cap, and its failure modes).

Planted streams: 10 games x 4 contested rows (40 rows),
split games 1-5 / 6-10 across two streams. Cases:
  1. panel-size 12, cap 2: exactly the first 12 rows in
     capture order qualify (games 1-6, 2 each - the cap
     binds before the size does only later); exit 0,
     report complete, games == 6, per_game max 2.
  2. panel-size 24, cap 2: 20 states over 10 games (the
     cap binds: 40 rows -> 20 kept, 20 skipped_by_cap);
     exit 0 (24 requested, 20 found -> SHORTFALL: exit 3).
     Asserted as the shortfall case: exit 3, complete
     False, states 20, skipped_by_cap 20.
  3. a row missing "selected" aborts: exit 2.
  4. a duplicated snap across streams aborts: exit 2.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(HERE, "..", "code", "build_panel.py")
FAILS = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILS.append(name)


def idx_row(snap, game, player, with_selected=True):
    r = {"snap": snap, "game": game, "player": player,
         "branch": "P", "turn": 3, "hcount": 1,
         "cands": [0, 1], "priors": [0.9, 0.1], "prior_pick": 0}
    if with_selected:
        r["selected"] = [0, 1]
    return r


def main():
    tmp = tempfile.mkdtemp(prefix="fx_panel_")
    s1, s2 = [], []
    for g in range(1, 11):
        for t in (1, 2, 3, 4):
            row = idx_row("g%d_t%d" % (g, t), "g%d" % g,
                          1 if g <= 5 else 2)
            (s1 if g <= 5 else s2).append(row)
    p1 = os.path.join(tmp, "idx1.jsonl")
    p2 = os.path.join(tmp, "idx2.jsonl")
    for path, rows in ((p1, s1), (p2, s2)):
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def run(streams, size, tag, extra_rows=None):
        paths = [p1, p2]
        if extra_rows is not None:
            paths = extra_rows
        out = os.path.join(tmp, "panel_%s.jsonl" % tag)
        rep = os.path.join(tmp, "report_%s.json" % tag)
        args = [sys.executable, BUILDER, "--out", out,
                "--report", rep, "--panel-size", str(size),
                "--per-game-cap", "2"]
        for i, pth in enumerate(paths):
            args += ["--stream",
                     "%s=%s" % ("capA" if i == 0 else "capB", pth)]
        p = subprocess.run(args, capture_output=True, text=True)
        rows = ([json.loads(l) for l in open(out) if l.strip()]
                if os.path.exists(out) else [])
        report = (json.load(open(rep))
                  if os.path.exists(rep) else None)
        return p, rows, report

    p, rows, rep = run(None, 12, "c1")
    check("case1 exit 0, 12 states over 6 games, cap respected",
          p.returncode == 0 and len(rows) == 12
          and rep["games"] == 6
          and max(rep["per_game"].values()) == 2
          and rep["complete"] is True,
          "rc=%d states=%d" % (p.returncode, len(rows)))
    check("case1 capture order preserved (g1_t1 first)",
          rows and rows[0]["snap"] == "g1_t1"
          and rows[0]["snap_dir"] == "capA/g1_t1",
          rows[0]["snap_dir"] if rows else "none")

    p, rows, rep = run(None, 24, "c2")
    check("case2 cap binds then shortfall: exit 3, 20 states, "
          "20 skipped by cap, complete False",
          p.returncode == 3 and len(rows) == 20
          and rep["skipped_by_cap"] == 20
          and rep["complete"] is False,
          "rc=%d states=%d skipped=%s"
          % (p.returncode, len(rows),
             rep and rep.get("skipped_by_cap")))

    bad = os.path.join(tmp, "idxbad.jsonl")
    with open(bad, "w") as f:
        f.write(json.dumps(idx_row("g1_t1", "g1", 1,
                                    with_selected=False)) + "\n")
    p, _, _ = run(None, 12, "c3", extra_rows=[bad, p2])
    check("case3 row without selected aborts (exit 2)",
          p.returncode == 2 and "ABORT" in p.stdout,
          "rc=%d" % p.returncode)

    dup = os.path.join(tmp, "idxdup.jsonl")
    with open(dup, "w") as f:
        f.write(json.dumps(idx_row("g1_t1", "g1", 1)) + "\n")
    p, _, _ = run(None, 12, "c4", extra_rows=[p1, dup])
    check("case4 duplicate snap aborts (exit 2)",
          p.returncode == 2 and "duplicate" in p.stdout,
          "rc=%d" % p.returncode)

    print("FX-BUILD-PANEL: %s"
          % ("ALL PASS" if not FAILS else "FAILURES: %s" % FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
