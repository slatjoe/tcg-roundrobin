#!/usr/bin/env python3
"""Fixture: ARGUMENT-LIST PARITY between the
recovery's registered influence invocation and
the completion step's (fix pass 7, package doc
sec.15, on claude-reply-416872f sec.2).

Why this fixture exists: the fix-pass-6
completion script passed "--game 440261752" to
probe_influence.py. The registered game is
540261752 -- probe_influence.py's own --game
default, which the recovery's invocation
(run_probe_recovery.sh, the influence step)
used by passing no --game at all. 440261752 is
not a capture game (it appears in neither
published driver-rows file), so the completion
would have printed a state inspection of
nothing under a registered step while silently
differing from the invocation the recovery
registered. Nothing in the suite compared the
two scripts' argument lists.

This fixture extracts BOTH invocations
verbatim (the $PY ... probe_influence.py block
in each script), parses them into flag ->
values, normalizes PATH values (any value
containing '/' or '$') to a placeholder, and
asserts the two flag dicts are EQUAL: same
flag names, same non-path argument values,
same value counts per flag. It also executes
the completion script's inspected-game
assertion block (extracted verbatim between
its BEGIN/END markers) against driver-rows
fixtures with and without the inspected id.

Env overrides (used to demonstrate the pre-fix
failure): COMPLETION_SCRIPT, RECOVERY_SCRIPT.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
RECOVERY = os.environ.get(
    "RECOVERY_SCRIPT",
    os.path.join(CODE, "run_probe_recovery.sh"))
COMPLETION = os.environ.get(
    "COMPLETION_SCRIPT",
    os.path.join(CODE, "run_probe_completion.sh"))
FAILED = []

START = re.compile(r'\$PY"?\s+"\$CODE_DIR/probe_influence\.py"')


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL",
                        name, extra))
    if not cond:
        FAILED.append(name)


def extract_invocation(path):
    lines = open(path).read().split("\n")
    start = None
    for i, ln in enumerate(lines):
        if START.search(ln):
            start = i
            break
    if start is None:
        return None
    block = [lines[start]]
    i = start
    while lines[i].rstrip().endswith("\\"):
        i += 1
        block.append(lines[i])
    return block


def parse_flags(block):
    text = " ".join(block).replace("\\", " ")
    text = text.replace('"', " ")
    toks = text.split()
    cut = []
    for t in toks:
        if t in (">", "||"):
            break
        cut.append(t)
    # drop the interpreter + the script path
    while cut and "probe_influence.py" not in cut[0]:
        cut.pop(0)
    if cut:
        cut.pop(0)
    flags = {}
    cur = None
    for t in cut:
        if t.startswith("--"):
            cur = t
            flags.setdefault(cur, [])
        elif cur is not None:
            flags[cur].append(
                "<PATH>" if ("/" in t or "$" in t) else t)
    return flags


def extract_block(path, begin, end):
    lines = open(path).read().split("\n")
    try:
        a = next(i for i, ln in enumerate(lines)
                 if begin in ln)
        b = next(i for i, ln in enumerate(lines)
                 if end in ln and i > a)
    except StopIteration:
        return None
    return lines[a + 1:b]


def main():
    rec_block = extract_invocation(RECOVERY)
    check("P1 recovery influence invocation "
          "extracted", rec_block is not None
          and len(rec_block) >= 10,
          "(%s)" % RECOVERY)
    com_block = extract_invocation(COMPLETION)
    check("P2 completion influence invocation "
          "extracted", com_block is not None
          and len(com_block) >= 10,
          "(%s)" % COMPLETION)
    if rec_block is None or com_block is None:
        print("fx_invocation_parity: FAILURES %s"
              % FAILED)
        return 1
    rec = parse_flags(rec_block)
    com = parse_flags(com_block)
    diff = []
    for k in sorted(set(rec) | set(com)):
        if rec.get(k) != com.get(k):
            diff.append("%s: recovery=%r "
                        "completion=%r"
                        % (k, rec.get(k),
                           com.get(k)))
    check("P3 flag parity (names + non-path "
          "values, paths normalized)",
          not diff, "; ".join(diff))
    check("P4 completion passes no --game "
          "(the registered default is used)",
          "--game" not in com)

    blk = extract_block(
        COMPLETION,
        "BEGIN inspected-game assertion",
        "END inspected-game assertion")
    check("P5 inspected-game assertion block "
          "extracted from the completion script",
          blk is not None and any(
              "INSPECTED_GAME=540261752" in ln
              for ln in blk or []))
    if blk is not None:
        body = "\n".join(blk) + "\n"
        with tempfile.TemporaryDirectory() as td:
            script = os.path.join(td, "assert.sh")
            with open(script, "w") as f:
                f.write(body)
            for label, rows, want_fail in (
                    ("absent",
                     ['{"gamename": "232622694"}',
                      '{"gamename": "693440924"}'],
                     True),
                    ("present",
                     ['{"gamename": "232622694"}',
                      '{"gamename": "540261752"}'],
                     False)):
                d = os.path.join(td, label)
                os.makedirs(d)
                with open(os.path.join(
                        d, "cap_s1_b1.jsonl"),
                        "w") as f:
                    f.write(rows[0] + "\n")
                with open(os.path.join(
                        d, "cap_s2_b1.jsonl"),
                        "w") as f:
                    f.write(rows[1] + "\n")
                env = dict(os.environ)
                env["S0"] = d
                p = subprocess.run(
                    ["bash", script], env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                out = p.stdout.decode()
                if want_fail:
                    check("P6 assertion trips when "
                          "the inspected game is "
                          "absent from the driver "
                          "rows",
                          p.returncode != 0
                          and "ABORT" in out
                          and "540261752" in out)
                else:
                    check("P7 assertion passes "
                          "when the inspected "
                          "game is present",
                          p.returncode == 0
                          and "inspected game ok"
                          in out)
    print("fx_invocation_parity: %s"
          % ("ALL PASS" if not FAILED
             else "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
