#!/usr/bin/env python3
"""Round-9 Stage 0 fixtures (synthetic, hand-computed).

Runs code/stage0_report.py on planted job/label sets and checks the
primary read, the unfinished-share accounting, the paired-n
distribution, the draw-sensitivity read and the instrument-limited
verdict against expectations computed by hand in
fixtures/README.md. Also runs the deployment scorer's own
--self-test and the runner's pin-format guard negatives.

FX1  all finished, planted diffs +0.5 / -0.5 -> mean 0, shares 0
FX2  unfinished mix -> primary -0.25, sensitivity -0.375,
     shares teacher 0.25 / prior 0.125 / pooled 0.1875 (<= 20%,
     verdict NOT instrument-limited), paired-n {2, 4}
FX3  pooled unfinished 0.625 with null primary -> verdict
     INSTRUMENT-LIMITED
FX3b same zero diffs, pooled unfinished 0.125 -> verdict NOT
     instrument-limited
FX4  positive read (+1.0, degenerate CI) with pooled unfinished
     0.375 -> verdict POSITIVE, stands; NOT instrument-limited
FX5  runner pin guard: 62-char pin aborts on format; right-format
     wrong-value pin aborts on mismatch; correct pin passes
FX6  deployment scorer --self-test passes; DELTA reads +0.0075

Exit 0 iff every check passes. Prints one line per check.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
FAILURES = []


def check(name, cond, detail=""):
    print("%s: %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILURES.append(name)


def rows_for(snap, cand, spec):
    """spec: list per world of ('f', outcome) | ('u',) | ('e',)."""
    out = []
    for w, s in enumerate(spec):
        if s[0] == "f":
            res = {"outcome": s[1], "finished": 1, "fallbacks": 0}
        elif s[0] == "u":
            res = {"outcome": 0.0, "finished": 0, "fallbacks": 0}
        else:
            res = {"error": "abort"}
        out.append({"snap": snap, "cand": cand, "world": w,
                    "result": res})
    return out


def run_report(jobs, rows):
    d = tempfile.mkdtemp(prefix="fx")
    jp = os.path.join(d, "jobs.jsonl")
    lp = os.path.join(d, "labels.jsonl")
    op = os.path.join(d, "report.json")
    with open(jp, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(lp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    p = subprocess.run(
        [sys.executable, os.path.join(CODE, "stage0_report.py"),
         "--jobs", jp, "--labels", lp, "--pass-name", "fixture",
         "--json-out", op], capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise SystemExit("report script failed on a fixture")
    return json.load(open(op)), p.stdout


def job(snap, game):
    return {"snap": snap, "game": game, "prior_pick": 0,
            "teacher_pick": 1}


F = lambda o: ("f", o)
U = ("u",)
E = ("e",)

# ---------------- FX1
jobs, rows = [], []
plan = [("gA", [F(1.0)] * 4, [F(0.0)] * 4),
        ("gA", [F(1.0)] * 4, [F(0.0)] * 4),
        ("gB", [F(0.0)] * 4, [F(1.0)] * 4),
        ("gB", [F(0.0)] * 4, [F(1.0)] * 4)]
for i, (g, t, p) in enumerate(plan):
    s = "fx1_%d" % i
    jobs.append(job(s, g))
    rows += rows_for(s, 1, t) + rows_for(s, 0, p)
rep, _ = run_report(jobs, rows)
pr = rep["primary"]
check("FX1 mean_diff == 0", abs(pr["mean_diff"]) < 1e-12,
      "got %r" % pr["mean_diff"])
check("FX1 frac_pos == frac_neg == 0.5",
      pr["frac_pos"] == 0.5 and pr["frac_neg"] == 0.5)
check("FX1 shares all 0", rep["unfinished"]["share_pooled"] == 0.0
      and rep["unfinished"]["share_teacher"] == 0.0)
check("FX1 paired-n all 4", rep["paired_n"]["min"] == 4
      and rep["paired_n"]["max"] == 4)
check("FX1 sensitivity == 0", abs(rep["sensitivity"]["mean_diff"])
      < 1e-12)
check("FX1 verdict not instrument-limited",
      rep["instrument_limited"] is False)

# ---------------- FX2
jobs = [job("fx2_1", "gC"), job("fx2_2", "gC")]
rows = []
rows += rows_for("fx2_1", 1, [F(1.0), F(1.0), U, U])
rows += rows_for("fx2_1", 0, [F(0.0), F(0.0), F(0.0), U])
rows += rows_for("fx2_2", 1, [F(-1.0)] * 4)
rows += rows_for("fx2_2", 0, [F(1.0)] * 4)
rep, _ = run_report(jobs, rows)
check("FX2 primary mean == -0.25",
      abs(rep["primary"]["mean_diff"] - (-0.25)) < 1e-12,
      "got %r" % rep["primary"]["mean_diff"])
check("FX2 sensitivity mean == -0.375",
      abs(rep["sensitivity"]["mean_diff"] - (-0.375)) < 1e-12,
      "got %r" % rep["sensitivity"]["mean_diff"])
un = rep["unfinished"]
check("FX2 shares 0.25 / 0.125 / 0.1875",
      un["share_teacher"] == 0.25 and un["share_prior"] == 0.125
      and un["share_pooled"] == 0.1875,
      "got %r/%r/%r" % (un["share_teacher"], un["share_prior"],
                        un["share_pooled"]))
pn = rep["paired_n"]
check("FX2 paired-n min 2 max 4 median 3",
      pn["min"] == 2 and pn["max"] == 4 and pn["median"] == 3.0)
check("FX2 verdict not instrument-limited (0.1875 <= 0.20)",
      rep["instrument_limited"] is False)

# ---------------- FX3
jobs = [job("fx3_1", "gD"), job("fx3_2", "gD")]
rows = []
rows += rows_for("fx3_1", 1, [F(0.0), U, U, U])
rows += rows_for("fx3_1", 0, [F(0.0), U, U, U])
rows += rows_for("fx3_2", 1, [F(1.0), F(1.0), U, U])
rows += rows_for("fx3_2", 0, [F(1.0), F(1.0), U, U])
rep, txt = run_report(jobs, rows)
check("FX3 primary mean == 0",
      abs(rep["primary"]["mean_diff"]) < 1e-12)
check("FX3 pooled share == 0.625",
      rep["unfinished"]["share_pooled"] == 0.625,
      "got %r" % rep["unfinished"]["share_pooled"])
check("FX3 verdict INSTRUMENT-LIMITED",
      rep["instrument_limited"] is True
      and "INSTRUMENT-LIMITED" in txt)

# ---------------- FX3b
jobs = [job("fx3b_1", "gD"), job("fx3b_2", "gD")]
rows = []
rows += rows_for("fx3b_1", 1, [F(0.0), F(0.0), F(0.0), U])
rows += rows_for("fx3b_1", 0, [F(0.0)] * 4)
rows += rows_for("fx3b_2", 1, [F(0.0)] * 4)
rows += rows_for("fx3b_2", 0, [F(0.0), F(0.0), U, F(0.0)])
rep, txt = run_report(jobs, rows)
check("FX3b pooled share == 0.125",
      rep["unfinished"]["share_pooled"] == 0.125,
      "got %r" % rep["unfinished"]["share_pooled"])
check("FX3b verdict NOT instrument-limited",
      rep["instrument_limited"] is False
      and "INSTRUMENT-LIMITED" not in rep["verdict"])

# ---------------- FX4 (positive stands)
jobs = [job("fx4_1", "gE"), job("fx4_2", "gE")]
rows = []
rows += rows_for("fx4_1", 1, [F(1.0), F(1.0), U, U])
rows += rows_for("fx4_1", 0, [F(-1.0), F(-1.0), U, F(-1.0)])
rows += rows_for("fx4_2", 1, [F(1.0), U, F(1.0), U])
rows += rows_for("fx4_2", 0, [F(-1.0), F(-1.0), F(-1.0), U])
rep, txt = run_report(jobs, rows)
check("FX4 primary mean == +1.0, CI degenerate [1, 1]",
      abs(rep["primary"]["mean_diff"] - 1.0) < 1e-12
      and rep["primary"]["ci"] == [1.0, 1.0],
      "got %r %r" % (rep["primary"]["mean_diff"],
                     rep["primary"]["ci"]))
check("FX4 pooled share == 0.375",
      rep["unfinished"]["share_pooled"] == 0.375,
      "got %r" % rep["unfinished"]["share_pooled"])
check("FX4 verdict POSITIVE stands, not instrument-limited",
      rep["instrument_limited"] is False
      and rep["verdict"].startswith("POSITIVE"))

# ---------------- FX5 (pin guard, extracted verbatim from the runner)
runner = open(os.path.join(CODE, "run_stage0_l3.sh")).read()
begin = runner.index("# PINFN-BEGIN")
end = runner.index("# PINFN-END")
pinfn = runner[begin:end]
d = tempfile.mkdtemp(prefix="fxpin")
target = os.path.join(d, "f.bin")
with open(target, "wb") as f:
    f.write(b"stage0 fixture")
import hashlib
good = hashlib.sha256(b"stage0 fixture").hexdigest()
script = pinfn + '\nexpect_hash "%s" "%s" "%s"\n' % (
    target, "%s", "fixture pin")
p = subprocess.run(["bash", "-c", script % good[:62]],
                   capture_output=True, text=True)
check("FX5 62-char pin aborts on format",
      p.returncode == 1 and "is not a 64-char sha256" in p.stderr,
      "rc=%d" % p.returncode)
wrong = ("0" if good[0] != "0" else "1") + good[1:]
p = subprocess.run(["bash", "-c", script % wrong],
                   capture_output=True, text=True)
check("FX5 wrong-value pin aborts on mismatch",
      p.returncode == 1 and "!=" in p.stderr, "rc=%d" % p.returncode)
p = subprocess.run(["bash", "-c", script % good],
                   capture_output=True, text=True)
check("FX5 correct pin passes", p.returncode == 0,
      "rc=%d %s" % (p.returncode, p.stderr.strip()))

# ---------------- FX6 (scorer self-test + DELTA)
p = subprocess.run(
    [sys.executable, os.path.join(CODE, "analyze_l3_deploy.py"),
     "--self-test"], capture_output=True, text=True)
check("FX6 scorer self-test passes",
      p.returncode == 0 and "SELF-TEST PASS" in p.stdout,
      p.stdout.strip().split("\n")[-1] if p.stdout else p.stderr[:80])
src = open(os.path.join(CODE, "analyze_l3_deploy.py")).read()
check("FX6 deploy DELTA == 0.0075, TEACHER_GAMES == 400",
      "\nDELTA = 0.0075\n" in src and "\nTEACHER_GAMES = 400\n" in src)

print("FIXTURES: %s" % ("ALL PASS" if not FAILURES else
                        "FAILURES: %s" % ", ".join(FAILURES)))
return_code = 0 if not FAILURES else 1
sys.exit(return_code)
