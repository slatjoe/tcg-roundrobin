#!/usr/bin/env python3
"""Step 2+3 fleet SMOKE-LOOP fixtures
(claude-reply-baf16e7 sec.2.1, package sec.20).

The 2026-10-30 smoke (sec.19.4) aborted in
TS-DRIVERS at `seeds=$3` (unbound variable): the
SMOKE switch empties the b-block seed lists, an
emptied spec ("t1b 1 ") word-splits to two fields,
and under the runner's `set -u` the seeds read
crashed BEFORE the skip-guard line that sat after
it. The approved repair reads the field
set -u-safely -- seeds=${3:-} -- in every driver
loop the SMOKE switch can empty, so the guard
fires. This fixture is the test that would have
caught it (the ruling's fixture condition):

  * the TS-DRIVERS and RS-DRIVERS loops are
    extracted VERBATIM from the staged runner and
    RUN under `set -u` with SMOKE's emptied lists
    (a-blocks populated, b-blocks empty) and a
    stub driver: the emptied specs must be
    SKIPPED and the populated ones must RUN.
  * negative: the same extracted loops with the
    repair reverted (seeds=$3) must ABORT with
    the unbound-variable error.
  * RAW-RERUN determination: its loop is driven
    by `while read -r seed seat rblk` over the
    computed rerun list -- no positional $3 read,
    and the SMOKE switch does not empty its
    specs -- so it does NOT share the pattern and
    is not repaired (recorded in sec.20).
"""
import os
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
RUNNER = open(os.path.join(
    R10, "code", "step2", "run_fleet_games.sh")).read()

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def extract_loop(first_spec):
    """The `for spec in ...` loop whose first spec
    starts with first_spec, verbatim: from its
    `for` line through the first bare `done`."""
    lines = RUNNER.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.startswith('for spec in "%s' % first_spec):
            start = i
            break
    assert start is not None, first_spec
    out = []
    for l in lines[start:]:
        out.append(l)
        if l == "done":
            break
    return "\n".join(out) + "\n"


STUB = """#!/usr/bin/env bash
echo "$@" >> "$STUB_LOG"
exit 0
"""

HARNESS = """set -u
SMOKE=1
OUT="%(tmp)s/out"
mkdir -p "$OUT"
GAME_TIMEOUT=1
DECK_REL="decks/stub.txt"
PY="%(tmp)s/stub_driver.sh"
CODE_DIR="%(tmp)s"
STUB_LOG="%(tmp)s/stub.log"
export STUB_LOG
%(vars)s
PIDS=""
%(loop)s
for pid in $PIDS; do wait "$pid" || exit 3; done
"""


def run_loop(loop_text, seed_vars):
    tmp = tempfile.mkdtemp(prefix="fx_smoke_loop_")
    try:
        with open(os.path.join(tmp, "stub_driver.sh"),
                  "w") as f:
            f.write(STUB)
        os.chmod(os.path.join(tmp, "stub_driver.sh"),
                 0o755)
        script = HARNESS % {
            "tmp": tmp,
            "vars": "\n".join(
                "%s=%s" % kv for kv in seed_vars),
            "loop": loop_text}
        p = os.path.join(tmp, "harness.sh")
        with open(p, "w") as f:
            f.write(script)
        r = subprocess.run(["bash", p],
                           capture_output=True, text=True,
                           timeout=60)
        log = ""
        lp = os.path.join(tmp, "stub.log")
        if os.path.exists(lp):
            log = open(lp).read()
        return r.returncode, r.stderr, log
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def arm_run(tag, first_spec, arm, seed_vars):
    loop = extract_loop(first_spec)
    check("%s: the extracted loop reads the seeds "
          "field set -u-safely (seeds=${3:-})" % tag,
          "seeds=${3:-}" in loop)
    rc, err, log = run_loop(loop, seed_vars)
    lines = [l for l in log.splitlines() if l.strip()]
    check("%s: the loop runs to completion under "
          "set -u with SMOKE's emptied b-block lists"
          % tag, rc == 0,
          "rc=%d err=%s" % (rc, err.strip()[:200]))
    check("%s: exactly the two populated specs ran "
          "(stub driver invoked twice)" % tag,
          len(lines) == 2, "log lines: %s" % (lines,))
    seeds = [l.split("--seeds")[1].split()[0]
             for l in lines if "--seeds" in l]
    seats = sorted(l.split("--seat")[1].split()[0]
                   for l in lines if "--seat" in l)
    check("%s: both stub invocations carry the "
          "populated seed, the %s arm, seats 1+2, "
          "and no empty --seeds" % (tag, arm),
          seeds == ["27002", "27002"]
          and all(("--arm %s" % arm) in l for l in lines)
          and seats == ["1", "2"]
          and not any("--seeds --" in l for l in lines),
          "lines: %s" % (lines,))
    broken = loop.replace("seeds=${3:-}", "seeds=$3")
    check("%s: reverting the repair in the extracted "
          "loop is a one-token change" % tag,
          broken != loop
          and broken.count("seeds=$3") == 1)
    rc2, err2, _log2 = run_loop(broken, seed_vars)
    check("%s: negative -- with seeds=$3 the loop "
          "ABORTS on the unbound variable (the "
          "sec.19.4 crash)" % tag,
          rc2 != 0 and "unbound variable" in err2,
          "rc=%d err=%s" % (rc2, err2.strip()[:200]))


arm_run("TS-DRIVERS", "t1a 1", "teacher", [
    ("BLOCK_T1A_SEEDS", "27002"),
    ("BLOCK_T1B_SEEDS", ""),
    ("BLOCK_T2A_SEEDS", "27002"),
    ("BLOCK_T2B_SEEDS", ""),
])
arm_run("RS-DRIVERS", "r1a 1", "raw", [
    ("BLOCK_R1A_SEEDS", "27002"),
    ("BLOCK_R1B_SEEDS", ""),
    ("BLOCK_R2A_SEEDS", "27002"),
    ("BLOCK_R2B_SEEDS", ""),
])

# ---- RAW-RERUN determination ----
_i = RUNNER.index("##### ===== RAW-RERUN")
_j = RUNNER.index("##### =====", _i + 10)
rerun = RUNNER[_i:_j]
check("RAW-RERUN does not share the pattern: its "
      "loop is `while read -r seed seat rblk` over "
      "the computed rerun list (no positional "
      "seeds read for the SMOKE switch to empty)",
      "while read -r seed seat rblk" in rerun
      and "seeds=$3" not in rerun
      and "seeds=${3" not in rerun)

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL",
                            name,
                            (" -- " + detail)
                            if detail and not ok else ""))
        bad += 0 if ok else 1
    print("fx_fleet_smoke_loops: %d checks, %d failed"
          % (len(RESULTS), bad))
    raise SystemExit(1 if bad else 0)
