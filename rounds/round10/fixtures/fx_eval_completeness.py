#!/usr/bin/env python3
"""Fixture: the eval-completeness assertion
(code/eval_completeness.py, fix pass 5,
claude-reply-9dae0e2 sec.2.2).

E1: a complete synthetic pair (every selected
    candidate at exactly k rows) passes with exit 0
    and missing = 0.
E2: the same pair with ONE candidate's rows deleted
    is caught: exit 2, the state named as missing
    with the deleted candidate listed.
E3: a candidate short by one row (k-1, not zero) is
    a count anomaly, named, exit 2 -- a partial drop
    cannot pass as complete either.
The script is driven through its real CLI on temp
files, never imported-and-reimplemented.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "code",
                      "eval_completeness.py")
FAILED = []


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL",
                        name, extra))
    if not cond:
        FAILED.append(name)


def job(snap, selected, k=3):
    return {"snap": snap, "game": "G%s" % snap[-1],
            "selected": selected,
            "setting": {"k": k, "name": "FX"}}


def rows(snap, cand, n, k=3):
    return [{"snap": snap, "cand": cand, "world": w,
             "result": {"finished": 1, "outcome": 1,
                        "horizon": 0, "fallbacks": 0}}
            for w in range(n)]


def run(jobs, evals):
    d = tempfile.mkdtemp(prefix="fx_evalcomp_")
    jp = os.path.join(d, "eval_jobs.jsonl")
    ep = os.path.join(d, "evals_all.jsonl")
    op = os.path.join(d, "out.json")
    with open(jp, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(ep, "w") as f:
        for r in evals:
            f.write(json.dumps(r) + "\n")
    p = subprocess.run(
        [sys.executable, SCRIPT, "--eval-jobs", jp,
         "--evals", ep, "--json-out", op],
        capture_output=True, text=True)
    out = json.load(open(op)) if os.path.exists(op) \
        else None
    return p, out


def main():
    jobs = [job("111_t1", [0, 1]), job("222_t2", [0, 2])]
    full = (rows("111_t1", 0, 3) + rows("111_t1", 1, 3)
            + rows("222_t2", 0, 3) + rows("222_t2", 2, 3))

    p, out = run(jobs, full)
    check("E1 complete pair exits 0", p.returncode == 0,
          "rc=%d" % p.returncode)
    check("E1 missing = 0, states complete = 2",
          out and out["missing_states"] == 0
          and out["states_complete"] == 2
          and out["eval_job_lines"] == 2
          and not out["count_anomalies"])

    cut = [r for r in full
           if not (r["snap"] == "222_t2"
                   and r["cand"] == 2)]
    p, out = run(jobs, cut)
    check("E2 deleted candidate exits 2",
          p.returncode == 2, "rc=%d" % p.returncode)
    check("E2 the state is named missing with cand 2",
          out and out["missing_states"] == 1
          and out["missing"][0]["snap"] == "222_t2"
          and out["missing"][0]["candidates"] == [2])
    check("E2 stdout names the missing state",
          "MISSING 222_t2" in p.stdout)

    short = (rows("111_t1", 0, 3) + rows("111_t1", 1, 3)
             + rows("222_t2", 0, 3) + rows("222_t2", 2, 2))
    p, out = run(jobs, short)
    check("E3 short candidate exits 2",
          p.returncode == 2, "rc=%d" % p.returncode)
    check("E3 the anomaly is named (cand 2, 2 of 3)",
          out and out["missing_states"] == 0
          and len(out["count_anomalies"]) == 1
          and out["count_anomalies"][0]["cand"] == 2
          and out["count_anomalies"][0]["rows"] == 2)

    print("fx_eval_completeness: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
