#!/usr/bin/env python3
"""Step 1 pilot fixture: invocation parity wherever
one script re-invokes or re-reads another's step
(the fx_invocation_parity pattern).

  1. TUPLE BUILDER parity: run_pilot_pregate.sh and
     run_pilot.sh both build TEACHER_TUPLE_JSON from
     the settings file; the two TUPLE-BUILD blocks
     are extracted verbatim and must be IDENTICAL
     (a tuple that differs between the pre-gate and
     the games is a different measurement).
  2. MANIFEST writer/reader parity: the pregate
     runner's MANIFEST-WRITE block writes
     pregate_manifest.json; run_pilot.sh's
     PREGATE-GATE block reads it. Every key the gate
     reads via man.get(...) must be a key the writer
     writes.
  3. DRIVER flag parity: the pregate's ghost driver
     invocation (BLOCK:PG-GHOST) and the pilot's
     teacher driver invocation (BLOCK:PILOT-GAMES)
     are extracted verbatim; their flag NAME sets
     must be EQUAL, and the pregate's --timeout
     literal must equal the pilot's GAME_TIMEOUT
     (fix pass 2: the pre-gate ghost arms take the
     pilot's registered 7,845 s -- attempt 1's
     1,200 s driver default, an absent flag, killed
     5 + 3 thr games; everything else -- tree, sock,
     seat, arm value aside, seeds, deck, out,
     logdir -- is the same invocation shape).
"""
import os
import re
import sys

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


def extract(text, begin, end):
    i = text.index(begin)
    j = text.index(end, i)
    return text[i:j + len(end)]


def main():
    rp = open(os.path.join(S1, "run_pilot.sh")).read()
    rg = open(os.path.join(S1,
                           "run_pilot_pregate.sh")).read()
    tb_p = extract(rp, "# TUPLE-BUILD-BEGIN",
                   "# TUPLE-BUILD-END")
    tb_g = extract(rg, "# TUPLE-BUILD-BEGIN",
                   "# TUPLE-BUILD-END")
    check("tuple-builder blocks identical in both "
          "runners", tb_p == tb_g)

    mw = extract(rg, "# MANIFEST-WRITE-BEGIN",
                 "# MANIFEST-WRITE-END")
    written = set(re.findall(r'"([a-z_0-9]+)":', mw))
    gate = extract(rp, "# BLOCK:PREGATE-GATE-BEGIN",
                   "# BLOCK:PREGATE-GATE-END")
    read = set(re.findall(r'man\.get\("([a-z_0-9]+)"\)',
                          gate))
    check("gate reads only keys the pregate manifest "
          "writes", read <= written,
          "read %s vs written %s"
          % (sorted(read), sorted(written)))
    check("gate reads the three registered fields",
          read == {"verdict", "search_s3_thr_sha256",
                   "teacher_tuple_json"}, str(sorted(read)))

    def flags(block):
        names = set(re.findall(r"--[a-z][a-z\-]+", block))
        return names
    ghost = extract(rg, "# BLOCK:PG-GHOST-BEGIN",
                    "# BLOCK:PG-GHOST-END")
    games = extract(rp, "# BLOCK:PILOT-GAMES-BEGIN",
                    "# BLOCK:PILOT-GAMES-END")
    fg, fp = flags(ghost), flags(games)
    check("driver flag sets equal (both carry "
          "--timeout since fix pass 2)",
          fp == fg,
          "ghost %s pilot %s"
          % (sorted(fg), sorted(fp)))
    mt = re.search(r"--timeout\s+(\d+)", ghost)
    mg = re.search(r"GAME_TIMEOUT=(\d+)", rp)
    check("pregate ghost --timeout literal == pilot "
          "GAME_TIMEOUT",
          mt is not None and mg is not None
          and mt.group(1) == mg.group(1),
          "pregate %s vs pilot %s"
          % (mt.group(1) if mt else None,
             mg.group(1) if mg else None))
    print("fx_pilot_parity: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
