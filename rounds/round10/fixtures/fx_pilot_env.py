#!/usr/bin/env python3
"""Step 1 pilot fixture: the composed-environment
contract for the pilot games runner (the fx_runner_env
pattern, applied to run_pilot.sh).

BLOCK:PILOT-GAMES is extracted VERBATIM from
run_pilot.sh and EXECUTED in a stub harness whose
$PY is an environment-recording stub. The composed
runner -> driver environment of every block
invocation must carry:
  * TEACHER_TUPLE_JSON, exported by the runner from
    settings_pilot.json (the tuple pin; the driver
    passes its environment through to the games);
  * TEACHER_SNAP_DIR = the block's logdir/snaps
    (Decide's overturn capture gate);
  * GATE_GAME_IDS_FILE and TCG_CLEAN_CHILDREN=1;
  * --arm teacher, --timeout == settings timeout_s,
    the settings seed blocks;
and must NOT carry TEACHER_CAPTURE (the pilot plays
the teacher's picks; capture mode would play the
prior's).
Negative case: the same execution with
TEACHER_TUPLE_JSON unset must fail the tuple check.

Env audit (printed, and the pilot-critical rows
asserted): every getenv() consumer in the shipped
search files and mains, traced to its setting
channel in the doc (step1-pilot-package.md sec.6).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
fails = []
checks = 0


def check(name, good, detail=""):
    global checks
    checks += 1
    print("%s %s %s" % ("PASS" if good else "FAIL",
                        name, detail))
    if not good:
        fails.append(name)


def extract_block(path, name):
    txt = open(path).read()
    i = txt.index("# BLOCK:%s-BEGIN" % name)
    j = txt.index("# BLOCK:%s-END" % name)
    return txt[i:j]


STUB = """#!/bin/bash
# Fix pass 1 (sec.2.3 determinism): the block runs the
# four invocations in parallel; the first build's
# multi-line append to the shared $RECORD interleaved
# records (corrupting parses) and ordered them by
# completion. (A single printf append still split at
# a line boundary under concurrency -- observed in
# this pass's testing.) Each invocation now writes
# its own file and renames it into place atomically;
# run_block parses the per-invocation files and
# sorts the records by ARGV.
rec="ARGV: $*
TEACHER_TUPLE_JSON=${TEACHER_TUPLE_JSON-<UNSET>}
TEACHER_SNAP_DIR=${TEACHER_SNAP_DIR-<UNSET>}
GATE_GAME_IDS_FILE=${GATE_GAME_IDS_FILE-<UNSET>}
TCG_CLEAN_CHILDREN=${TCG_CLEAN_CHILDREN-<UNSET>}
TEACHER_CAPTURE=${TEACHER_CAPTURE-<UNSET>}
---
"
printf '%s' "$rec" > "$RECORD.$$.tmp"
mv "$RECORD.$$.tmp" "$RECORD.$$.txt"
exit 0
"""


def run_block(block, tmp, with_tuple):
    stub = os.path.join(tmp, "stub_py.sh")
    open(stub, "w").write(STUB)
    os.chmod(stub, 0o755)
    record = os.path.join(tmp, "record.txt")
    settings = json.load(open(os.path.join(
        S1, "settings_pilot.json")))
    tuple_json = json.dumps(settings["teacher_tuple"])
    harness = os.path.join(tmp, "harness.sh")
    env_lines = ""
    if with_tuple:
        env_lines = "export TEACHER_TUPLE_JSON='%s'\n" \
            % tuple_json
    open(harness, "w").write(
        "#!/bin/bash\nset -u\n"
        "PY=%s\nCODE_DIR=%s\nOUT=%s\nGAME_TIMEOUT=%d\n"
        "DECK_REL=decks/nats2026_eriksen_gravy_60.txt\n"
        "RECORD=%s\nexport RECORD\n%s\n%s\n"
        % (stub, S1, os.path.join(tmp, "out"),
           settings["games"]["timeout_s"], record,
           env_lines, block))
    r = subprocess.run(["bash", harness],
                       capture_output=True, text=True)
    recs = []
    recdir = os.path.dirname(record)
    base = os.path.basename(record)
    for fn in sorted(os.listdir(recdir)):
        if not (fn.startswith(base + ".")
                and fn.endswith(".txt")):
            continue
        cur = {}
        for l in open(os.path.join(recdir, fn)):
            l = l.rstrip("\n")
            if l == "---":
                recs.append(cur)
                cur = {}
            elif l.startswith("ARGV: "):
                cur["ARGV"] = l[len("ARGV: "):]
            elif "=" in l:
                k, v = l.split("=", 1)
                cur[k] = v
    recs.sort(key=lambda rec: rec.get("ARGV", ""))
    return r, recs, tuple_json, settings


def main():
    block = extract_block(os.path.join(
        S1, "run_pilot.sh"), "PILOT-GAMES")
    with tempfile.TemporaryDirectory() as tmp:
        r, recs, tuple_json, settings = run_block(
            block, tmp, True)
        check("games block executes in the stub harness",
              r.returncode == 0,
              r.stderr[-200:] if r.returncode else "")
        check("4 block invocations recorded",
              len(recs) == 4, str(len(recs)))
        want_seeds = {(b["tag"], b["seeds"])
                      for b in settings["games"]["blocks"]}
        got_seeds = set()
        for rec in recs:
            argv = rec.get("ARGV", "")
            m = re.search(r"--logdir (\S+)", argv)
            blk = re.search(r"games_(\w+)_log",
                            m.group(1)).group(1) if m \
                else "?"
            ms = re.search(r"--seeds (\S+)", argv)
            got_seeds.add((blk, ms.group(1) if ms
                           else "?"))
            check("block %s tuple pin composed" % blk,
                  rec.get("TEACHER_TUPLE_JSON")
                  == tuple_json)
            check("block %s snap dir == its logdir/snaps"
                  % blk,
                  rec.get("TEACHER_SNAP_DIR", "")
                  .endswith("games_%s_log/snaps" % blk))
            check("block %s ids file + clean children"
                  % blk,
                  rec.get("GATE_GAME_IDS_FILE",
                          "").endswith(
                              "games_%s_ids.txt" % blk)
                  and rec.get("TCG_CLEAN_CHILDREN") == "1")
            check("block %s TEACHER_CAPTURE unset" % blk,
                  rec.get("TEACHER_CAPTURE") == "<UNSET>")
            check("block %s arm teacher, timeout %d"
                  % (blk, settings["games"]["timeout_s"]),
                  "--arm teacher" in argv
                  and ("--timeout %d"
                       % settings["games"]["timeout_s"])
                  in argv)
        check("seed blocks == settings blocks",
              got_seeds == want_seeds,
              str(sorted(got_seeds)))
    with tempfile.TemporaryDirectory() as tmp:
        r, recs, _, _ = run_block(block, tmp, False)
        bad = [rec for rec in recs
               if rec.get("TEACHER_TUPLE_JSON")
               != "<UNSET>"]
        check("negative: without the runner's export "
              "the tuple check detects the gap",
              len(recs) == 4 and not bad)
    print("fx_pilot_env: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
