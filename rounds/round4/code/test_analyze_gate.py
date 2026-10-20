#!/usr/bin/env python3
"""Fixture test for analyze_gate.py (Claude G2: a fixture test that
runs in a review sandbox). Stdlib only. Builds a synthetic gate
dataset with hand-computed expected outputs, runs the analyzer as
a subprocess, and prints PASS/FAIL per check.

Fixture design (12 units, seeds 2001-2006 x seats 1-2):
  seat 1 deltas: +1, -1, 0, -0.5 (cap), -1 (teacher timeout), +0.5
  seat 2 deltas: 0, +1, 0, 0, -1, +1
  => seat 1 delta -1/6, seat 2 delta +1/6, pooled delta 0.
  Discordant: teacher>raw 4, teacher<raw 4, tied 4 -> sign p = 1.0.
  Teacher timeouts 1/12 = 8.33% -> INCONCLUSIVE flag must appear.
  Sensitivity (timeout pairs dropped): delta = +1/11 = +0.0909.
  Stats: 4 contested rows, 1 overturn -> overturn rate 25.00%.
  Calibration bins: bin1 pred 0.2500 / realized 0.5000 / n 2;
  bin2 0.5000/1.0000/1; bin3 1.0000/1.0000/1.
Fixture B (ruling-3 defect): one unit, raw wall-timeout, teacher
completed with zero overturns -> the DEFECT line must appear.
Also: a registry missing one gamename must make the analyzer
refuse (exit 2).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYZER = os.path.join(HERE, "analyze_gate.py")
FAILURES = []


def check(name, ok, detail=""):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILURES.append(name)


def row(seed, seat, arm, **kw):
    r = {"seed": seed, "seat": seat, "arm": arm,
         "gamename": "g%d%d%s" % (seed, seat, arm[0])}
    r.update(kw)
    return r


def build_fixture(d):
    rows = []
    # seat 1
    rows += [row(2001, 1, "teacher", winner=1), row(2001, 1, "raw", winner=2)]
    rows += [row(2002, 1, "teacher", winner=2), row(2002, 1, "raw", winner=1)]
    rows += [row(2003, 1, "teacher", winner=1), row(2003, 1, "raw", winner=1)]
    rows += [row(2004, 1, "teacher", winner=1, capped=True,
                 cap_reason="turn_cap"),
             row(2004, 1, "raw", winner=1)]
    t = row(2005, 1, "teacher", invalid="timeout")
    del t["gamename"]
    rows += [t, row(2005, 1, "raw", winner=1)]
    rows += [row(2006, 1, "teacher", winner=0, draw=True),
             row(2006, 1, "raw", winner=2)]
    # seat 2
    rows += [row(2001, 2, "teacher", winner=2), row(2001, 2, "raw", winner=2)]
    rows += [row(2002, 2, "teacher", winner=2), row(2002, 2, "raw", winner=1)]
    rows += [row(2003, 2, "teacher", winner=1), row(2003, 2, "raw", winner=1)]
    rows += [row(2004, 2, "teacher", winner=2), row(2004, 2, "raw", winner=2)]
    rows += [row(2005, 2, "teacher", winner=1), row(2005, 2, "raw", winner=2)]
    rows += [row(2006, 2, "teacher", winner=2), row(2006, 2, "raw", winner=1)]
    rows_path = os.path.join(d, "rows.jsonl")
    with open(rows_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    stats = []
    for m in (-1.0, 0.0, 1.0):
        stats.append({"teacher": 1, "contested": 1, "det_persisted": 1,
                      "branch": "M", "game": "g20011t", "prior_pick": 0,
                      "pick": 0, "overturn": 0,
                      "means": [m, -0.5, -0.5], "abort_reasons": [],
                      "abort_by_cand": [], "child_fallbacks": 0})
    stats.append({"teacher": 1, "contested": 1, "det_persisted": 1,
                  "branch": "B", "game": "g20021t", "prior_pick": 0,
                  "pick": 1, "overturn": 1, "means": [0.0, 0.4],
                  "abort_reasons": [], "abort_by_cand": [],
                  "child_fallbacks": 0})
    stats_path = os.path.join(d, "search_stats.jsonl")
    with open(stats_path, "w") as f:
        for s in stats:
            f.write(json.dumps(s) + "\n")
    games = {}
    for r in rows:
        if "gamename" in r:
            games[r["gamename"]] = "fixture"
    reg_path = os.path.join(d, "registry.json")
    with open(reg_path, "w") as f:
        json.dump({"created": "fixture", "n_games": len(games),
                   "rule": "fixture", "version": 1, "games": games}, f)
    return rows_path, stats_path, reg_path, games


def run_analyzer(rows, stats, reg, extra=()):
    cmd = [sys.executable, ANALYZER, "--rows", rows, "--stats", stats,
           "--registry", reg, "--boot", "200"] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    d = tempfile.mkdtemp(prefix="gate_fixture_")
    rows, stats, reg, games = build_fixture(d)
    rc, out = run_analyzer(rows, stats, reg)
    check("analyzer exits 0", rc == 0, "rc=%d" % rc)
    check("pooled delta +0.0000", "delta +0.0000" in out)
    check("seat 1 delta -0.1667", "delta -0.1667" in out)
    check("seat 2 delta +0.1667", "delta +0.1667" in out)
    check("discordant 4/4/4 + p=1.0",
          "teacher>raw 4 | teacher<raw 4 | tied 4" in out
          and "p = 1.0000" in out)
    check("teacher timeouts 1 of 12", "TEACHER TIMEOUTS: 1 of 12" in out)
    check("inconclusive flag", "INCONCLUSIVE" in out)
    check("sensitivity delta +0.0909", "delta +0.0909" in out)
    check("overturn rate 25.00%", "overturn_rate=25.00%" in out)
    # calibration bins: parse the CALIBRATION table lines
    cal = {}
    in_cal = False
    for ln in out.splitlines():
        if "G5 CALIBRATION" in ln:
            in_cal = True
        elif in_cal:
            parts = ln.split()
            if len(parts) == 4 and parts[0] in ("1", "2", "3"):
                cal[parts[0]] = (float(parts[1]), float(parts[2]),
                                 int(parts[3]))
    check("calibration bin 1", cal.get("1") == (0.25, 0.5, 2),
          str(cal.get("1")))
    check("calibration bin 2", cal.get("2") == (0.5, 1.0, 1),
          str(cal.get("2")))
    check("calibration bin 3", cal.get("3") == (1.0, 1.0, 1),
          str(cal.get("3")))

    # registry refusal
    bad_reg = os.path.join(d, "registry_bad.json")
    games2 = dict(games)
    del games2["g20011t"]
    with open(bad_reg, "w") as f:
        json.dump({"games": games2}, f)
    rc2, out2 = run_analyzer(rows, stats, bad_reg)
    check("registry refusal (exit 2)", rc2 == 2 and "REFUSING" in out2,
          "rc=%d" % rc2)

    # fixture B: ruling-3 defect
    d2 = tempfile.mkdtemp(prefix="gate_fixtureB_")
    rows_b = [row(3001, 1, "teacher", winner=1),
              row(3001, 1, "raw", invalid="timeout")]
    del rows_b[1]["gamename"]
    rows_b_path = os.path.join(d2, "rows.jsonl")
    with open(rows_b_path, "w") as f:
        for r in rows_b:
            f.write(json.dumps(r) + "\n")
    stats_b = [{"teacher": 1, "contested": 1, "det_persisted": 1,
                "branch": "M", "game": "g30011t", "prior_pick": 0,
                "pick": 0, "overturn": 0, "means": [0.0, -0.5],
                "abort_reasons": [], "abort_by_cand": [],
                "child_fallbacks": 0}]
    stats_b_path = os.path.join(d2, "search_stats.jsonl")
    with open(stats_b_path, "w") as f:
        for s in stats_b:
            f.write(json.dumps(s) + "\n")
    reg_b = os.path.join(d2, "registry.json")
    with open(reg_b, "w") as f:
        json.dump({"games": {"g30011t": "fixture"}}, f)
    rc3, out3 = run_analyzer(rows_b_path, stats_b_path, reg_b)
    check("ruling-3 defect line", "DEFECT (ruling 3)" in out3)
    check("raw timeout scored pair kept",
          "units total: 1 | scored: 1" in out3)

    print("")
    if FAILURES:
        print("FIXTURE TEST: FAIL (%d checks failed)" % len(FAILURES))
        return 1
    print("FIXTURE TEST: PASS (all checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
