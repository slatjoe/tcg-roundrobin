#!/usr/bin/env python3
"""Round-9 Stage 0 report-fix fixtures (claude-reply-2db6b77
sec.2/sec.3). Synthetic job/label sets with hand-computed
expectations, run against code/stage0_report.py as a subprocess.

Cases:
  FX-R1 refusal class: teacher worlds 0-9 are canary_hook_failed.
    Expect: teacher finished 40, unfinished 0, refusal 10, share
    0.0000; tally canary_hook_failed [REFUSAL]; sensitivity keeps
    only worlds 10-49 (40 worlds), mean diff 1.0000.
  FX-R2 timeout: teacher worlds 0-9 are {"error": "timeout"}.
    Expect: teacher share 10/50 = 0.2000; pooled 10/100 = 0.1000;
    tally timeout [unfinished]; sensitivity prices those worlds
    at 0.5 -> mean (10*0.5 + 40*1.0)/50 = 0.9000, which differs
    from the primary (finished-pairs only).
  FX-R3 unlisted class: same shape as FX-R2 with the error string
    "segfault_in_child" (run under --pass-name horizon, so the
    per-pass tallies are exercised for the horizon pass too --
    review sec.3.2). Expect identical numbers to FX-R2 and the
    class tallied as [unfinished] (the unlisted default).
  FX-R4 denominator rule: teacher 30 finished / 10 timeout /
    10 canary_hook_failed; prior all finished. Expect teacher
    share 10/(30+10) = 0.2500 (refusals leave the denominator).
  FX-R5 world-count guard (sec.3.1): teacher candidate has 49
    rows. Expect exit 2 and the guard line naming 49 rows.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "code", "stage0_report.py")

FAILURES = []


def build(tmp, teacher_errs, prior_errs=None, teacher_rows=50):
    job = {"snap": "fxsnap", "game": "fxgame",
           "teacher_pick": 0, "prior_pick": 1}
    jobs_p = os.path.join(tmp, "jobs.jsonl")
    labels_p = os.path.join(tmp, "labels.jsonl")
    with open(jobs_p, "w") as f:
        f.write(json.dumps(job) + "\n")
    with open(labels_p, "w") as f:
        for cand, errs, nrows, outcome in (
                (0, teacher_errs or {}, teacher_rows, 1.0),
                (1, prior_errs or {}, 50, -1.0)):
            for w in range(nrows):
                if w in errs:
                    res = {"error": errs[w]}
                else:
                    res = {"finished": 1, "outcome": outcome}
                f.write(json.dumps({"snap": "fxsnap", "cand": cand,
                                    "world": w, "result": res}) + "\n")
    return jobs_p, labels_p


def run(jobs_p, labels_p, pass_name="primary"):
    p = subprocess.run(
        [sys.executable, REPORT, "--jobs", jobs_p,
         "--labels", labels_p, "--pass-name", pass_name],
        capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def check(name, cond, detail=""):
    print("%s: %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        FAILURES.append(name)


def errs(cls, worlds=range(10)):
    return {w: cls for w in worlds}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        # FX-R1 refusal
        jp, lp = build(tmp, errs("canary_hook_failed"))
        rc, out = run(jp, lp)
        check("FX-R1 rc", rc == 0, "rc=%d" % rc)
        check("FX-R1 teacher counts",
              "finished 40, unfinished 0, refusal 10" in out)
        check("FX-R1 teacher share", "share 0.0000" in out)
        check("FX-R1 tally",
              "canary_hook_failed" in out and "[REFUSAL]" in out)
        check("FX-R1 sensitivity worlds", "over 40 worlds" in out)
        check("FX-R1 sensitivity mean",
              "mean paired diff 1.0000" in out)

        # FX-R2 timeout
        jp, lp = build(tmp, errs("timeout"))
        rc, out = run(jp, lp)
        check("FX-R2 rc", rc == 0, "rc=%d" % rc)
        check("FX-R2 teacher share", "share 0.2000" in out)
        check("FX-R2 pooled share",
              "unfinished 10, refusal 0; share 0.1000" in out)
        check("FX-R2 tally",
              "timeout" in out and "[unfinished]" in out)
        check("FX-R2 sensitivity mean",
              "mean paired diff 0.9000" in out)
        check("FX-R2 sensitivity worlds", "over 50 worlds" in out)

        # FX-R3 unlisted class, horizon pass name
        jp, lp = build(tmp, errs("segfault_in_child"))
        rc, out = run(jp, lp, pass_name="horizon")
        check("FX-R3 rc", rc == 0, "rc=%d" % rc)
        check("FX-R3 pass header", "pass: horizon" in out)
        check("FX-R3 teacher share", "share 0.2000" in out)
        check("FX-R3 tally",
              "segfault_in_child" in out and "[unfinished]" in out)
        check("FX-R3 sensitivity mean",
              "mean paired diff 0.9000" in out)

        # FX-R4 denominator rule
        mixed = dict(errs("timeout", range(30, 40)))
        mixed.update(errs("canary_hook_failed", range(40, 50)))
        jp, lp = build(tmp, mixed)
        rc, out = run(jp, lp)
        check("FX-R4 rc", rc == 0, "rc=%d" % rc)
        check("FX-R4 teacher counts",
              "finished 30, unfinished 10, refusal 10" in out)
        check("FX-R4 teacher share", "share 0.2500" in out)

        # FX-R5 world-count guard
        jp, lp = build(tmp, {}, teacher_rows=49)
        rc, out = run(jp, lp)
        check("FX-R5 rc", rc == 2, "rc=%d" % rc)
        check("FX-R5 guard line",
              "world-count guard" in out and "49 rows" in out)

    print("FX-REPORT-FIX: %s" % ("ALL PASS" if not FAILURES
                                 else "FAILURES: %s" % FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
