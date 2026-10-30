#!/usr/bin/env python3
"""Step 2+3 fleet REAL-CONTRACT fixtures
(claude-reply-5ea3a72 sec.2.2, package sec.19).

The fleet games runner's as-approved server/driver
blocks carried seven contract defects (sec.19.1)
that 135 text-level checks missed, because every
fixture stubbed the counterparty: no fixture ever
composed a spawn against the real server's env
reads, or a driver call against the real argparse.
These fixtures read the REAL pinned files:

  SERVER  fixtures/ref_patched_search_server.py --
          a byte-identical copy of the tree's
          patched server ($GTREE/rl/search_server.py),
          sha256 asserted == ab85fa1b... before any
          parse (the file the forked blocks spawn;
          also byte-identical to the already
          published rounds/round3/code/search_server.py).
  DRIVER  code/step2/paired_driver_gravy.py (the
          runner's own pinned copy, 3389b1b9...).

Checks:
  (a) server env: every os.environ.get name is
      parsed out of the pinned server; each fleet
      spawn block (TS-SRV, RS-SRV) sets SEARCH_MODEL,
      TCG_POLICY_SOCK, TCG_LEARNER_SEAT and
      TCG_OPP_MIX; the socket embeds ${seat} (so the
      two seats' sockets differ) and TCG_LEARNER_SEAT
      is the same $seat; the runner pins the tree
      server at the spawned path; no spawn passes
      argv (--socket/--port) and the defect tokens
      (TCG_POLICY_SEARCH*, '"ready": true',
      --max-turns, --cap-trigger) occur nowhere in
      the runner.
  (b) socket wiring: every driver invocation's
      --sock equals the spawn blocks' TCG_POLICY_SOCK
      template for its seat.
  (c) readiness: the runner's readiness grep
      strings ('search model loaded', 'ckpt_v10')
      occur literally in the pinned server source;
      '"ready": true' occurs nowhere in it.
  (d) driver argv: every driver invocation
      (TS-DRIVERS, RS-DRIVERS, RAW-RERUN), extracted
      verbatim and variable-substituted, parses
      under the REAL driver's argparse (the parser
      is built by executing the add_argument
      statements out of the pinned driver file
      itself; no game is started). Negative cases:
      argv + --max-turns and argv + --cap-trigger
      must FAIL parsing (exit 2).
  (e) parity: the fleet's forked segments equal
      their run_stage3_games.sh sources (and the
      server/driver blocks equal run_pilot.sh's)
      as TOKEN STREAMS after applying ONLY the
      enumerated allowed differences (sec.19.2):
      seeds, block tags, paths (tree prefix, the
      installed build + its hash, the snap-dir path
      form), the --timeout form, --arm raw, the
      SMOKE skip-guard lines, the tree sections'
      expect_hash label/|| form, and (sec.20) the
      approved smoke repair's set -u-safe seeds read
      (seeds=${3:-} for the source's seeds=$3).
      Any other difference fails with its position.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(R10))
STEP2 = os.path.join(R10, "code", "step2")
STEP1 = os.path.join(R10, "code", "step1")
S3_PATH = os.path.join(REPO, "rounds", "round9", "code",
                       "run_stage3_games.sh")
PILOT_PATH = os.path.join(STEP1, "run_pilot.sh")
SERVER_REF = os.path.join(HERE,
                          "ref_patched_search_server.py")
PATCHED_SHA = ("ab85fa1bcf19b41c7d48db642a2fd93d211e826b"
               "9f684594cefa5a1100f3c52c")
DRIVER_SHA = ("3389b1b936180909b1f0c70f743ef2e6c414de"
              "933194405de344fc5abceaf359")

FLEET = open(os.path.join(STEP2,
                          "run_fleet_games.sh")).read()
S3 = open(S3_PATH).read()
PILOT = open(PILOT_PATH).read()
SETTINGS = json.load(open(os.path.join(
    STEP2, "settings_fleet.json")))

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def fleet_section(tag):
    i = FLEET.index("##### ===== %s" % tag)
    j = FLEET.index("##### =====", i + 10)
    return FLEET[i:j]


def marked(text, name, begin_tpl="# BLOCK:%s-BEGIN",
           end_tpl="# BLOCK:%s-END"):
    i = text.index(begin_tpl % name)
    i = text.index("\n", i) + 1
    j = text.index(end_tpl % name)
    return text[i:j]


def after_block_lines(text, name, n):
    """The n non-empty lines following a BLOCK end
    marker (Stage 3's sweeper stop touches live
    outside its DRIVERS markers)."""
    j = text.index("# BLOCK:%s-END" % name)
    lines = [l for l in text[j:].splitlines()[1:]
             if l.strip()]
    return "\n".join(lines[:n]) + "\n"


def blk_segment(text, blk, build):
    """The tree-prep segment for one block set: from
    its `for blk in ...` header through `done`."""
    i = text.index("for blk in %s; do" % blk)
    j = text.index("\ndone", i)
    return text[i:j + 5]


# ================= (a) server env =================
check("the published patched-server reference is "
      "byte-identical to the pinned server "
      "(ab85fa1b...)", sha(SERVER_REF) == PATCHED_SHA,
      sha(SERVER_REF))
SERVER = open(SERVER_REF).read()
env_names = sorted(set(re.findall(
    r'os\.environ\.get\("([A-Z_0-9]+)"', SERVER)))
check("env names parsed from the pinned server",
      env_names == ["EVAL_BATCH", "EVAL_WAIT_MS",
                    "SEARCH_MODEL", "TCG_LEARNER_SEAT",
                    "TCG_OPP_MIX", "TCG_POLICY_SOCK",
                    "TCG_TRAJ_LOG"],
      "parsed %s" % (env_names,))

REQUIRED_ENV = ('SEARCH_MODEL="$CKPT"',
                'TCG_POLICY_SOCK="$OUT/srv_s${seat}.sock"',
                "TCG_LEARNER_SEAT=$seat",
                'TCG_OPP_MIX="heuristic:1.0"')
for tag in ("TS-SRV", "RS-SRV"):
    seg = fleet_section(tag)
    for lit in REQUIRED_ENV:
        check("%s spawn sets %s" % (tag, lit),
              lit in seg)
    check("%s spawns the tree's patched server"
          % tag,
          '"$GTREE/rl/search_server.py"' in seg)
    check("%s spawn passes no argv to the server"
          % tag, "search_server.py\" --" not in seg
          and "--socket" not in seg
          and "--port" not in seg)
check("the runner pins the tree's patched server "
      "(PINFN, ab85fa1b...)",
      'expect_hash "$GTREE/rl/search_server.py"' in FLEET
      and PATCHED_SHA in FLEET)
for tok in ("TCG_POLICY_SEARCH", '"ready": true',
            "--max-turns", "--cap-trigger",
            "/tmp/pol_"):
    check("defect token %r occurs nowhere in the "
          "rebuilt runner" % tok, tok not in FLEET)

# ================= (b) socket wiring ==============
spawn_sock = re.search(r'TCG_POLICY_SOCK="([^"]+)"',
                       fleet_section("TS-SRV")).group(1)
for tag in ("TS-DRIVERS", "RS-DRIVERS", "RAW-RERUN"):
    seg = fleet_section(tag)
    socks = re.findall(r'--sock\s+"([^"]+)"', seg)
    check("%s: every driver's --sock == the spawn "
          "blocks' TCG_POLICY_SOCK (%s)"
          % (tag, spawn_sock),
          socks and all(s == spawn_sock for s in socks),
          "found %s" % (socks,))

# ================= (c) readiness ==================
# The readiness grep string proper must occur in the
# server source. The runner's second grep, 'ckpt_v10',
# matches the model path the server PRINTS (its
# SEARCH_MODEL env value), so its source-side anchor
# is the settings checkpoint basename, checked here.
check("readiness string 'search model loaded' "
      "occurs literally in the pinned server source",
      "search model loaded" in SERVER)
check("the runner greps server logs for 'search "
      "model loaded'",
      "grep -q 'search model loaded'" in FLEET)
_ckpt = re.search(r'^CKPT="([^"]+)"', FLEET, re.M)
check("the runner greps server logs for the model "
      "identity 'ckpt_v10' and its CKPT path's "
      "basename is ckpt_v10.pt (the string the "
      "server prints from SEARCH_MODEL)",
      "grep -q 'ckpt_v10'" in FLEET
      and _ckpt is not None
      and os.path.basename(_ckpt.group(1))
      == "ckpt_v10.pt",
      "CKPT %s" % (_ckpt.group(1) if _ckpt else None))
check("'\"ready\": true' occurs nowhere in the "
      "pinned server source (the as-approved "
      "readiness defect)", '"ready": true' not in SERVER)

# ================= (d) driver argv ================
DRIVER_PATH = os.path.join(STEP2,
                           "paired_driver_gravy.py")
check("the staged driver is the runner's pinned "
      "copy (3389b1b9...)", sha(DRIVER_PATH)
      == DRIVER_SHA, sha(DRIVER_PATH))
dsrc = open(DRIVER_PATH).read()
_i = dsrc.rindex(
    "\n", 0, dsrc.index("ap = argparse.ArgumentParser()")) + 1
_j = dsrc.rindex(
    "\n", 0, dsrc.index("a = ap.parse_args()")) + 1
import textwrap
seg = textwrap.dedent(dsrc[_i:_j])
ns = {"argparse": argparse}
exec(seg, ns)
REAL_PARSER = ns["ap"]


def invocation(section_text):
    """The paired_driver_gravy.py invocation inside
    a runner section, as a shlex token list
    (continuation lines joined)."""
    lines = section_text.splitlines()
    for i, l in enumerate(lines):
        if "paired_driver_gravy.py" in l:
            parts = [l]
            while parts[-1].rstrip().endswith("\\"):
                i += 1
                parts.append(lines[i])
            joined = " ".join(
                p.rstrip().rstrip("\\").strip()
                for p in parts)
            toks = shlex.split(joined)
            if ">" in toks:  # the shell redirect is
                toks = toks[:toks.index(">")]  # not argv
            return toks
    return None


SUBS = [
    ("$OUT", "/tmp/fleet_contract_out"),
    ("${seat}", "1"), ("$seat", "1"),
    ("${blk}", "t1a"), ("${rblk}", "r1a"),
    ("/tmp/r10fleet_gm_t1a", "/tmp/r10fleet_gm_t1a"),
    ("$tree", "/tmp/r10fleet_gm_t1a"),
    ("$DECK_REL", "decks/nats2026_eriksen_gravy_60.txt"),
    ("$GAME_TIMEOUT", "8031"),
    ("$seeds", SETTINGS["games"]["blocks"][0]["seeds"]),
    ("$seed", "27001"),
    ("$logdir", "/tmp/fleet_contract_out/games_t1a_log"),
]


def substitute(tokens):
    out = []
    for t in tokens:
        for a, b in SUBS:
            t = t.replace(a, b)
        out.append(t)
    return out


def try_parse(argv):
    import contextlib
    import io
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            return REAL_PARSER.parse_args(argv)
        except SystemExit:
            return None


def parses(argv):
    return try_parse(argv) is not None


invocations = {}
for tag in ("TS-DRIVERS", "RS-DRIVERS", "RAW-RERUN"):
    toks = invocation(fleet_section(tag))
    check("%s: a driver invocation is extractable"
          % tag, toks is not None)
    argv = substitute(toks[2:])  # drop $PY + script
    check("%s: substitution leaves no $ in argv"
          % tag, not any("$" in t for t in argv),
          "argv %s" % (argv,))
    invocations[tag] = argv
    check("%s: the extracted argv parses under the "
          "REAL driver's argparse" % tag, parses(argv),
          "argv %s" % (argv,))
ts_parsed = try_parse(invocations["TS-DRIVERS"])
check("TS-DRIVERS argv: --deck resolves to the tree "
      "deck (not the driver's hard-coded default)",
      ts_parsed is not None
      and ts_parsed.deck.endswith(
          "decks/" + SETTINGS["deck"])
      and ts_parsed.deck.startswith("/tmp/"),
      "deck %s" % (ts_parsed.deck if ts_parsed
                   else None))
for bad in ("--max-turns", "--cap-trigger"):
    argv = invocations["TS-DRIVERS"] + [bad, "1"]
    check("negative: argv + %s FAILS the real "
          "argparse (exit 2)" % bad, not parses(argv))

# ================= (e) parity =====================
SMOKE_GUARD = ('[ "${SMOKE:-0}" = 1 ] && '
               '[ -z "$seeds" ] && continue')


def normalize(seg, drop_sweep_clear=False):
    seg = seg.replace(SMOKE_GUARD, "")
    # sec.20 (reply baf16e7 sec.2.1): the approved
    # smoke repair reads the seeds field set -u-safely
    # in the fleet's driver loops; the sources read
    # seeds=$3. Map the repaired form to the source
    # form so parity measures the fork, not the fix.
    seg = seg.replace("seeds=${3:-}", "seeds=$3")
    lines = []
    for l in seg.splitlines():
        if l.startswith("##### ====="):
            continue
        if drop_sweep_clear and l.strip() == \
                'SWEEP_PIDS=""':
            continue
        lines.append(l)
    seg = "\n".join(lines)
    seg = seg.replace("/tmp/r9s3_gm_", "/tmp/TREE_gm_")
    seg = seg.replace("/tmp/r10fleet_gm_", "/tmp/TREE_gm_")
    seg = seg.replace("/tmp/r10pilot_gm_", "/tmp/TREE_gm_")
    seg = re.sub(r"\b\d{5}-\d{5}\b", "SEEDS", seg)
    seg = re.sub(r"\$BLOCK_[A-Z0-9]+_SEEDS", "SEEDS", seg)
    seg = seg.replace("search_s3_thr.php", "BUILD_PHP")
    seg = seg.replace("search_s2.php", "BUILD_PHP")
    seg = seg.replace(
        "4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49",
        "BUILD_SHA")
    seg = seg.replace(
        "85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa",
        "BUILD_SHA")
    seg = re.sub(r'"(installed|raw tree keeps)[^"]*"'
                 r" \|\| exit 1", "", seg)
    seg = seg.replace('--timeout "$GAME_TIMEOUT"',
                      "--timeout TIMEOUT")
    seg = seg.replace("--timeout $GAME_TIMEOUT",
                      "--timeout TIMEOUT")
    seg = seg.replace(
        'TEACHER_SNAP_DIR="$OUT/games_${blk}_log/snaps"',
        "TEACHER_SNAP_DIR=SNAPDIR")
    seg = seg.replace('TEACHER_SNAP_DIR="$logdir/snaps"',
                      "TEACHER_SNAP_DIR=SNAPDIR")
    # Stage 3's games-phase abort message carries the
    # word 'teacher' where the pilot's does not; the
    # fleet inherited Stage 3's wording verbatim.
    seg = seg.replace("a teacher games block failed",
                      "a games block failed")
    seg = re.sub(r"\b[tsr][12][ab]\b", "BLKTAG", seg)
    # Line-continuation backslashes are formatting,
    # not contract: the two sources break their
    # expect_hash calls at different points.
    return [t for t in seg.split() if t != "\\"]


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return "token %d: %r vs %r (context %s)" % (
                i, x, y, a[max(0, i - 4):i + 5])
    return "lengths %d vs %d" % (len(a), len(b))


def parity(name, fleet_seg, src_seg,
           drop_sweep_clear=False):
    fa = normalize(fleet_seg, drop_sweep_clear)
    fb = normalize(src_seg, drop_sweep_clear)
    check("parity: %s" % name, fa == fb,
          first_diff(fa, fb) if fa != fb else "")


fleet_ts = "\n".join(fleet_section(t) for t in (
    "TS-SRV", "TS-TREES", "TS-SWEEP", "TS-DRIVERS",
    "WAIT-T"))
s3_ts = "\n".join((
    marked(S3, "TS-SRV"),
    blk_segment(S3, "t1a t1b t2a t2b", None),
    marked(S3, "TS-SWEEP"),
    marked(S3, "TS-DRIVERS"),
    after_block_lines(S3, "TS-DRIVERS", 2)))
parity("fleet TS sections == Stage 3 TS blocks "
       "(+ tree segment + stop lines)", fleet_ts, s3_ts)

fleet_rs = "\n".join(fleet_section(t) for t in (
    "RS-SRV", "RS-TREES", "RS-SWEEP", "RS-DRIVERS",
    "WAIT-R"))
s3_rs = "\n".join((
    marked(S3, "RS-SRV"),
    blk_segment(S3, "r1a r1b r2a r2b", None),
    marked(S3, "RS-SWEEP"),
    marked(S3, "RS-DRIVERS"),
    after_block_lines(S3, "RS-DRIVERS", 1)))
parity("fleet RS sections == Stage 3 RS blocks "
       "(+ tree segment + stop line)", fleet_rs, s3_rs)

parity("fleet TS-SRV == the pilot's PILOT-SRV block",
       fleet_section("TS-SRV"), marked(PILOT, "PILOT-SRV"))
parity("fleet RS-SRV == the pilot-form server block "
       "(Stage 3 RS-SRV)", fleet_section("RS-SRV"),
       marked(S3, "RS-SRV"))
fleet_tg = fleet_section("TS-DRIVERS") \
    + fleet_section("WAIT-T")
parity("fleet TS-DRIVERS+WAIT-T == the pilot's "
       "PILOT-GAMES block (modulo the sweeper-stop "
       "lines, which the pilot runs post-block)",
       fleet_tg, marked(PILOT, "PILOT-GAMES")
       + "\n" + after_block_lines(PILOT, "PILOT-GAMES", 1),
       drop_sweep_clear=True)

# RAW-RERUN: the fleet's draft/selector/tail are its
# own approved form (the selector text is identical
# to Stage 3's); parity covers the rerun SUBSHELL:
# its env assignments + driver argv token stream.
def rerun_subshell_tokens(section_text):
    i = section_text.index('tree="/tmp/')
    j = section_text.index(") &", i)
    body = section_text[i:j]
    env = sorted(set(re.findall(
        r"(GATE_GAME_IDS_FILE|TCG_CLEAN_CHILDREN)=",
        body)))
    toks = invocation(body)
    return env, toks


f_env, f_toks = rerun_subshell_tokens(
    fleet_section("RAW-RERUN"))
s_env, s_toks = rerun_subshell_tokens(
    marked(S3, "RAW-RERUN"))
check("RAW-RERUN subshell env assignments match "
      "Stage 3's (GATE_GAME_IDS_FILE, "
      "TCG_CLEAN_CHILDREN)", f_env == s_env
      and f_env == ["GATE_GAME_IDS_FILE",
                    "TCG_CLEAN_CHILDREN"],
      "fleet %s s3 %s" % (f_env, s_env))
fa = normalize(" ".join(f_toks or []))
fb = normalize(" ".join(s_toks or []))
check("parity: RAW-RERUN driver argv == Stage 3's",
      fa == fb, first_diff(fa, fb) if fa != fb else "")

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL",
                            name,
                            (" -- " + detail)
                            if detail and not ok else ""))
        bad += 0 if ok else 1
    print("fx_fleet_contract: %d checks, %d failed"
          % (len(RESULTS), bad))
    raise SystemExit(1 if bad else 0)
