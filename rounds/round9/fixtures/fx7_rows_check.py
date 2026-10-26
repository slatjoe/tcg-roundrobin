#!/usr/bin/env python3
"""FX7-rows fixture (claude-reply-2db6b77 sec.2): run the fixed
stage0_report.py on FX7's OWN OFF rows (the box build test's
primary construction, 3 jobs / 300 candidate-rows: 272 finished,
28 abort errors, all past turn 62 -- the same 28 tuples the
horizon-ON pass converted to draws).

Expectations, hand-stated from the FX7 record:
  * pooled unfinished share = 28/300 = 0.0933 (abort is NOT a
    refusal class; refusals = 0)
  * error tally: abort 28 [unfinished]; no REFUSAL lines
  * world-count guard passes (50 rows per job x candidate)
  * sensitivity worlds > primary paired worlds wherever an
    aborted world's partner finished, and the sensitivity mean
    differs from the primary mean (the 28 are priced 0.5 there,
    excluded from the primary)

Usage: fx7_rows_check.py --jobs FX7_JOBS --labels FX7_OFF_LABELS
(the artifacts of fixtures/fx7_box_test.sh; if they are not
durable on the box, regenerate the OFF pass with that script
first and record that in the fix note).
"""
import argparse
import re
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "code", "stage0_report.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", required=True)
    a = ap.parse_args()
    p = subprocess.run(
        [sys.executable, REPORT, "--jobs", a.jobs,
         "--labels", a.labels, "--pass-name", "fx7-off"],
        capture_output=True, text=True)
    out = p.stdout + p.stderr
    print(out)
    fails = []

    def need(name, cond, detail=""):
        print("FX7-ROWS %s: %s %s" % (name, "PASS" if cond else
                                      "FAIL", detail))
        if not cond:
            fails.append(name)

    need("rc", p.returncode == 0, "rc=%d" % p.returncode)
    need("pooled share 28/300",
         "unfinished 28, refusal 0; share 0.0933" in out)
    need("abort tally", "abort" in out and "[REFUSAL]" not in out)
    m = re.search(r"SENSITIVITY.*?mean paired diff ([0-9.\-]+)",
                  out, re.S)
    prim = re.search(r"PRIMARY.*?mean paired diff ([0-9.\-]+)",
                     out, re.S)
    need("sensitivity present", m is not None)
    need("primary present", prim is not None)
    if m and prim:
        need("sensitivity != primary",
             abs(float(m.group(1)) - float(prim.group(1))) > 1e-9,
             "primary %s vs sensitivity %s"
             % (prim.group(1), m.group(1)))
    print("FX7-ROWS: %s" % ("ALL PASS" if not fails
                            else "FAILURES: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
