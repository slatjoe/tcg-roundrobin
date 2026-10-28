#!/usr/bin/env python3
"""Round-10 Step 0 fixture: the capture environment
contract (third fix pass -- the attempt-2 defect).

THE DEFECT THIS GUARDS: search_s3.php's uncontested
capture hook gates on getenv("TEACHER_CAPTURE") &&
getenv("TEACHER_CAPTURE_UNCONTESTED"). The first is
set by paired_driver_gravy.py itself (its capture
arm); the second had to arrive through the runner --
and run_probe.sh never delivered it, so the hook's
uncontested branch could never fire under the
runner. The rest of the suite could not see it: the
hook fixtures set the env by hand, and the block
fixtures stubbed the driver without inspecting its
environment. Attempt 2 was killed as void at
first-minutes verification for exactly this.

THE CONTRACT, checked at every boundary with
verbatim sources (never a hand-copied env list):
  runner -> driver: the BLOCK:CAPTURE text is
    extracted verbatim from run_probe.sh and
    EXECUTED in the fx_probe_blocks stub harness
    (stub driver records the environment it is
    invoked with). TEACHER_CAPTURE_UNCONTESTED=1
    must be in that environment, on the same
    invocation-prefix channel as GATE_GAME_IDS_FILE
    / TCG_CLEAN_CHILDREN.
  driver -> game: paired_driver_gravy.py's own
    lines are lifted verbatim -- env seeded from
    dict(os.environ), the capture arm's
    env["TEACHER_CAPTURE"] = "1" (+ TEACHER_SNAP_DIR),
    and the game spawned with env=env -- and the
    composed environment is asserted to carry BOTH
    variables the hook gates on.
  consumer: the hook's gate line is lifted verbatim
    from search_s3.php, so a rename on either side
    of the contract fails here.
A NEGATIVE case runs the same checks against a
temporary runner copy with the
TEACHER_CAPTURE_UNCONTESTED assignment removed:
the guard must fail there, on exactly the
uncontested checks.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", "code"))
RUNNER_PATH = os.path.join(CODE, "run_probe.sh")
DRIVER_PATH = os.path.join(CODE, "paired_driver_gravy.py")
HOOK_PATH = os.path.join(CODE, "search_s3.php")

PYSTUB = '''#!/usr/bin/env python3
import json, os, sys
if len(sys.argv) > 1 and sys.argv[1] == "-":
    os.execvp("python3", ["python3", "-"] + sys.argv[2:])
if len(sys.argv) > 1 and sys.argv[1].endswith("paired_driver_gravy.py"):
    dump = os.environ.get("FX_ENV_DUMP")
    if dump:
        with open(dump, "a") as f:
            f.write(json.dumps(dict(os.environ)) + "\\n")
    args = sys.argv[2:]
    out = args[args.index("--out") + 1]
    with open(out, "w") as f:
        f.write('{"game": "2400100001"}\\n')
    with open(out + ".manifest.json", "w") as f:
        json.dump({"assert_ok": True, "arm": "capture",
                   "seat": 1, "assertions": ["stub"]}, f)
    ids = os.environ.get("GATE_GAME_IDS_FILE")
    if ids:
        with open(ids, "a") as f:
            f.write("2400100001\\n")
    sys.exit(0)
sys.exit(0)
'''


def extract_block(text, name):
    """The verbatim-extraction pattern (fx_probe_blocks'
    awk range, in Python): the lines between the
    BLOCK markers, inclusive."""
    lines = text.splitlines(keepends=True)
    out, inside = [], False
    for ln in lines:
        if ("# BLOCK:%s-BEGIN" % name) in ln:
            inside = True
        if inside:
            out.append(ln)
        if ("# BLOCK:%s-END" % name) in ln:
            inside = False
    return "".join(out)


def extract_expect_hash(text):
    m = re.search(r"^expect_hash\(\) \{.*?^\}", text, re.S | re.M)
    return m.group(0) if m else ""


def run_capture_block(runner_text, sb):
    """Execute the runner's verbatim BLOCK:CAPTURE in
    the stub harness (fx_probe_blocks.sh's CAPTURE
    case, rebuilt per run so the negative case can
    point it at a mutilated runner). Returns
    (rc, output, [env dict per driver invocation])."""
    os.makedirs(os.path.join(sb, "out"), exist_ok=True)
    os.makedirs(os.path.join(sb, "code"), exist_ok=True)
    gt = os.path.join(sb, "gtree")
    os.makedirs(os.path.join(gt, "decks"), exist_ok=True)
    os.makedirs(os.path.join(gt, "vendor", "talishar", "Games"),
                exist_ok=True)
    with open(os.path.join(
            gt, "decks", "nats2026_eriksen_gravy_60.txt"),
            "w") as f:
        f.write("deck\n")
    for fn in ("search_s3.php", "search_s2.php"):
        shutil.copy(os.path.join(CODE, fn),
                    os.path.join(sb, "code", fn))
    pystub = os.path.join(sb, "pystub")
    with open(pystub, "w") as f:
        f.write(PYSTUB)
    os.chmod(pystub, 0o755)
    dump = os.path.join(sb, "env_dump.jsonl")
    harness = "\n".join([
        "set -u",
        'OUT="%s/out"' % sb,
        'CODE_DIR="%s/code"' % sb,
        'GTREE="%s"' % gt,
        'PY="%s"' % pystub,
        'PHP="/bin/true"',
        'PROD="/stub/search_server.py"',
        'CKPT="/stub/ckpt_v10.pt"',
        'DECK_REL="decks/nats2026_eriksen_gravy_60.txt"',
        "SRV_WAIT_TRIES=5",
        'SRV_PIDS=""; SWEEP_PIDS=""',
        'export FX_ENV_DUMP="%s"' % dump,
        'start_sweeper() { :; }',
        "cleanup() { :; }",
        extract_expect_hash(runner_text),
        "BLOCK=1",
        'S1SEEDS="24001-24045"',
        'S2SEEDS="24046-24090"',
        extract_block(runner_text, "CAPTURE"),
        "echo CAPTURE_OK",
        ""])
    script = os.path.join(sb, "run_cap.sh")
    with open(script, "w") as f:
        f.write(harness)
    p = subprocess.run(["bash", script], capture_output=True,
                       text=True, timeout=300)
    envs = []
    if os.path.exists(dump):
        for ln in open(dump):
            ln = ln.strip()
            if ln:
                envs.append(json.loads(ln))
    return p.returncode, p.stdout + p.stderr, envs


def collect(runner_text, prefix=""):
    """Run every contract check against runner TEXT
    (pure in its input, so the negative case can run
    it against a mutilated copy). Returns the list of
    failed check names; prints each check line with
    PREFIX so the negative run is distinguishable."""
    fails = []

    def check(name, cond, extra=""):
        print("%s%s %s %s" % (prefix,
                              "PASS" if cond else "FAIL",
                              name, extra))
        if not cond:
            fails.append(name)

    block = extract_block(runner_text, "CAPTURE")
    check("capture block extracted verbatim from the runner",
          "paired_driver_gravy.py" in block
          and "BLOCK:CAPTURE-END" in block)
    check("capture block passes --arm capture to the driver",
          "--arm capture" in block)

    sb = tempfile.mkdtemp(prefix="fx_env_")
    try:
        rc, out, envs = run_capture_block(runner_text, sb)
    finally:
        shutil.rmtree(sb, ignore_errors=True)
    check("capture block executes clean in the stub harness",
          rc == 0 and "CAPTURE_OK" in out
          and "capture assertions OK" in out,
          "rc=%d" % rc)
    check("two capture driver invocations recorded",
          len(envs) == 2, "found %d" % len(envs))
    check("runner delivers the capture channel vars "
          "(GATE_GAME_IDS_FILE, TCG_CLEAN_CHILDREN=1)",
          len(envs) == 2 and all(
              e.get("GATE_GAME_IDS_FILE", "").endswith(
                  "cap_game_ids.txt")
              and e.get("TCG_CLEAN_CHILDREN") == "1"
              for e in envs))
    check("runner delivers TEACHER_CAPTURE_UNCONTESTED=1 "
          "to the capture driver",
          len(envs) == 2 and all(
              e.get("TEACHER_CAPTURE_UNCONTESTED") == "1"
              for e in envs))

    drv = open(DRIVER_PATH).read()
    check("driver seeds the game env from its own "
          "environment (env = dict(os.environ))",
          "env = dict(os.environ)" in drv)
    arm = re.search(r'if a\.arm == "capture":\n'
                    r'\s+env\["TEACHER_CAPTURE"\] = "1"\n'
                    r'\s+env\["TEACHER_SNAP_DIR"\] = ', drv)
    check("driver capture arm sets TEACHER_CAPTURE=1 "
          "and TEACHER_SNAP_DIR", arm is not None)
    check("driver spawns the game with the composed "
          "env (env=env)", "env=env" in drv)

    composed = dict(envs[0]) if envs else {}
    if arm is not None:
        composed["TEACHER_CAPTURE"] = "1"
    check("composed capture env carries TEACHER_CAPTURE=1 "
          "(set by the driver's capture arm)",
          composed.get("TEACHER_CAPTURE") == "1")
    check("composed capture env carries "
          "TEACHER_CAPTURE_UNCONTESTED=1 (runner channel)",
          composed.get("TEACHER_CAPTURE_UNCONTESTED") == "1")

    hook = open(HOOK_PATH).read()
    check("hook gate consumes exactly TEACHER_CAPTURE + "
          "TEACHER_CAPTURE_UNCONTESTED",
          'getenv("TEACHER_CAPTURE") && '
          'getenv("TEACHER_CAPTURE_UNCONTESTED")' in hook)
    return fails


def main():
    text = open(RUNNER_PATH).read()
    fails = collect(text)

    # negative case: a temporary copy of the runner
    # with the TEACHER_CAPTURE_UNCONTESTED assignment
    # removed from the capture invocation must FAIL
    # the guard, on exactly the two uncontested
    # checks (the attempt-2 defect, replanted).
    pat = re.compile(r"\n\s*TEACHER_CAPTURE_UNCONTESTED=1 \\")
    mut, n = pat.subn("", text)
    neg_fails = (collect(mut, prefix="[negative copy] ")
                 if n == 1 else ["<pattern matched %d "
                                 "assignments>" % n])
    want = {"runner delivers TEACHER_CAPTURE_UNCONTESTED=1 "
            "to the capture driver",
            "composed capture env carries "
            "TEACHER_CAPTURE_UNCONTESTED=1 (runner channel)"}
    ok = n == 1 and set(neg_fails) == want
    print("%s negative: guard fails on an env-stripped "
          "runner copy" % ("PASS" if ok else "FAIL"),
          "removed %d assignment(s); failures on the "
          "copy: %s" % (n, neg_fails))
    if not ok:
        fails.append("negative case")

    print("fx_runner_env: %s"
          % ("ALL PASS" if not fails
             else "FAILURES: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
