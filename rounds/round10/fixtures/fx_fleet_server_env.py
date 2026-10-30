#!/usr/bin/env python3
"""Step 2+3 fleet server-spawn environment (the
2026-10-30 repair fixture).

Both 2026-10-30 fleet launches aborted before any
game: the second at teacher-server start, because
run_fleet_games.sh's two search_server.py spawn
blocks never set SEARCH_MODEL, which the pinned
PRODUCTION server (rl/search_server.py, sha256
81ef2cdb...) requires (its lines 68-69 exit when
SEARCH_MODEL is unset). The teacher block set only
the patched server's env names (TCG_POLICY_SEARCH*),
which the production server never reads; the raw
block set only TCG_POLICY_SEARCH_DEVICE=cuda. The
pilot's proven spawn form (code/step1/run_pilot.sh)
sets SEARCH_MODEL="$CKPT"; run_fleet_l3.sh already
did (its line 207).

This fixture extracts BOTH spawn blocks VERBATIM
from the staged run_fleet_games.sh -- from each
`for port in` loop header through the closing
`done` of its spawn loop, keeping only loops whose
body invokes search_server.py -- and asserts:
  (a) exactly 2 spawn sites exist;
  (b) each extracted block contains the literal
      line SEARCH_MODEL="$CKPT".
Negative cases: a copy with the SEARCH_MODEL lines
stripped fails both blocks; a copy with only the
raw block's line stripped fails exactly that block.

SCOPE: this is a text-level guard on the staged
runner. It does NOT start a server, load a model,
or exercise the composed runtime environment; the
first runtime proof is the relaunch's own
server-ready gate.

REBUILD AMENDMENT (2026-10-30, package sec.19;
claude-reply-5ea3a72 sec.2): the fork replaced the
port loops with the pilot/Stage 3 per-seat loops
(`for seat in 1 2; do`, sockets via
TCG_POLICY_SOCK, the tree's patched server). The
extractor now targets the seat-loop form and
identifies the blocks by their server-log names
(srv_s = teacher, srv_raw_s = raw); the assertions
are unchanged in substance. The deep contracts
(server env reads, socket wiring, readiness
strings, driver argparse, fork parity) live in
fx_fleet_contract.py.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
GAMES_PATH = os.path.join(R10, "code", "step2",
                          "run_fleet_games.sh")
LITERAL = 'SEARCH_MODEL="$CKPT"'

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def spawn_blocks(text):
    """Verbatim spawn blocks: from each
    `for seat in 1 2; do` header through the first
    following `done`, keeping blocks whose body
    invokes search_server.py (the readiness loops
    share the header but are filtered out by the
    body test)."""
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if re.match(r"for seat in 1 2; do$",
                    lines[i]):
            j = i
            while j < len(lines) and lines[j] != "done":
                j += 1
            block = "\n".join(lines[i:j + 1])
            if "search_server.py" in block:
                blocks.append((lines[i], block))
            i = j + 1
        else:
            i += 1
    return blocks


def has_literal(block):
    # In the forked (pilot/Stage 3) spawn lines,
    # SEARCH_MODEL="$CKPT" is one assignment token
    # among several on the env line (the as-approved
    # draft carried it as a line of its own); the
    # check is on the assignment token.
    return LITERAL in block.split()


def main():
    text = open(GAMES_PATH).read()
    blocks = spawn_blocks(text)
    check("exactly 2 search_server.py spawn sites "
          "extracted verbatim from run_fleet_games.sh",
          len(blocks) == 2,
          "found %d" % len(blocks))
    names = {0: "teacher (seats 1 2, srv_s logs)",
             1: "raw (seats 1 2, srv_raw_s logs)"}
    logmarks = {0: '"$OUT/srv_s${seat}.log"',
                1: '"$OUT/srv_raw_s${seat}.log"'}
    for idx in (0, 1):
        if idx < len(blocks):
            header, block = blocks[idx]
            check("%s spawn block is the seat loop "
                  "writing %s" % (names[idx],
                                  logmarks[idx]),
                  header.strip() == "for seat in 1 2; do"
                  and logmarks[idx] in block
                  and (idx == 1 or "srv_raw" not in block))
            check("%s spawn block contains the "
                  "assignment SEARCH_MODEL=\"$CKPT\""
                  % names[idx], has_literal(block))
    # Negative: strip every SEARCH_MODEL line.
    stripped = "\n".join(
        l for l in text.splitlines()
        if LITERAL not in l)
    sblocks = spawn_blocks(stripped)
    check("negative: with SEARCH_MODEL stripped, "
          "both blocks fail the literal check "
          "(detected)", len(sblocks) == 2
          and not any(has_literal(b)
                      for _, b in sblocks))
    # Negative: strip only the raw block's line
    # (the second occurrence in file order).
    lines = text.splitlines()
    seen = 0
    for i, l in enumerate(lines):
        if LITERAL in l:
            seen += 1
            if seen == 2:
                lines[i] = ""
                break
    oblocks = spawn_blocks("\n".join(lines))
    check("negative: with only the raw block's "
          "SEARCH_MODEL stripped, exactly the raw "
          "block fails", len(oblocks) == 2
          and has_literal(oblocks[0][1])
          and not has_literal(oblocks[1][1]))

    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL",
                            name,
                            (" -- " + detail)
                            if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
