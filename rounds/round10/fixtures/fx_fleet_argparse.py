#!/usr/bin/env python3
"""Step 2+3 fleet ARGPARSE-CONTRACT fixtures
(claude-reply-baf16e7 sec.4.1, package sec.20).

Defects 6, 8 and 9 were the same failure at three
call sites: a runner invoked a pinned Python tool
with argv the tool's own argparse rejects -- the
driver's --max-turns/--cap-trigger, the merge's
bare positional ids files, the sweeper's --once --
and two of the three were hidden by tolerance
lines or by never being reached. fx_fleet_contract
(d) covers the DRIVER sites; this fixture closes
the class over BOTH runners:

  * every `$PY "$CODE_DIR/<file>.py" ...`
    invocation in run_fleet_games.sh and
    run_fleet_l3.sh is enumerated BY GREP (the
    census below) and compared, token for token,
    against this fixture's contract table -- a
    call site added or changed without a contract
    entry FAILS;
  * for each site, the argv (shell variables
    substituted by type-valid placeholders) is
    parsed under THAT FILE's real argparse: the
    parser is rebuilt from the pinned file's own
    add_argument statements (AST replay; nothing
    of the tool executes), after the file's
    sha256 is asserted against its pin;
  * negative cases: the sweeper's argv + --once
    must FAIL, and the merge's old bare-files
    form (--tag X <ids files>, no --registry /
    --ids) must FAIL.

Out of the pattern's scope by construction:
`$PY -` heredocs (inline code, no file invoked),
`$PY "$GTREE/rl/search_server.py"` and
`$PY "$PROD"` (server spawns -- their env
contract is fx_fleet_contract (a)), and the L3
runner's php label mains (pinned by hash at
their tree-install sites).
"""
import argparse
import ast
import contextlib
import hashlib
import io
import os
import re
import shlex

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
STEP2 = os.path.join(R10, "code", "step2")

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


PINS = {
    "paired_driver_gravy.py":
        "3389b1b936180909b1f0c70f743ef2e6c414de"
        "933194405de344fc5abceaf359",
    "shm_sweep.py":
        "98027a8b6f58bb06651c5b1e5203872fa2939aea464"
        "da5f180907dde43d14f33",
    "fleet_games_report.py":
        "62ca60b5bc289944d1a6d7e66f0567e4ffac895f0f6"
        "e9b9a876207615f4fe578",
    "merge_registry.py":
        "13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146"
        "f20cc7ebbcf5b9faf6bbe",
    "fleet_read.py":
        "7370b989c36d1bac70673d4a3e16da35c6f39eb1da"
        "a425af3bb80df9d811cfdc",
    "build_fleet_jobs.py":
        "c7601341302fdf43f2e6708ff2d8bd5ef5417d1c2ed"
        "ee9dbe45dac1ca6e3695f",
}
REG = "/home/joe/tcg/registry-vault/" \
      "do_not_train_registry.json"
VAULT = "/home/joe/tcg/registry-vault"
DRV_T = ["--tree", "$tree", "--sock",
         "$OUT/srv_s${seat}.sock", "--seat", "$seat",
         "--arm", "teacher", "--seeds", "$seeds",
         "--deck", "$tree/$DECK_REL", "--timeout",
         "$GAME_TIMEOUT", "--out",
         "$OUT/games_${blk}.jsonl", "--logdir",
         "$logdir"]
DRV_R = ["--tree", "$tree",
         "--sock", "$OUT/srv_s${seat}.sock",
         "--seat", "$seat", "--arm", "raw",
         "--seeds", "$seeds", "--deck",
         "$tree/$DECK_REL", "--timeout",
         "$GAME_TIMEOUT", "--out",
         "$OUT/games_${blk}.jsonl", "--logdir",
         "$logdir"]
SWEEP = ["--log", "$OUT/shm_sweep_gm_${blk}.log",
         "--start-file",
         "$OUT/shm_start_gm_${blk}.txt",
         "--games-dir", "$tree/vendor/talishar/Games",
         "--interval", "60", "--stop-file",
         "$OUT/shm_sweep_gm_${blk}.stop"]

# The contract table: (runner, target, argv tokens
# after the script token), in file order. This IS
# the census the grep enumeration must reproduce.
EXPECTED = [
    # ---- run_fleet_games.sh ----
    ("games", "shm_sweep.py", SWEEP),                # TS-SWEEP
    ("games", "paired_driver_gravy.py", DRV_T),      # TS-DRIVERS
    ("games", "shm_sweep.py", SWEEP),                # RS-SWEEP
    ("games", "paired_driver_gravy.py", DRV_R),      # RS-DRIVERS
    ("games", "fleet_games_report.py",
     ["--out-dir", "$OUT", "--settings",
      "$CODE_DIR/settings_fleet.json", "--json-out",
      "$OUT/games_report_draft.json",
      "--pairing-only"]),                            # RAW-RERUN draft
    ("games", "paired_driver_gravy.py",
     ["--tree", "$tree", "--sock",
      "$OUT/srv_s${seat}.sock", "--seat", "$seat",
      "--arm", "raw", "--seeds", "$seed", "--deck",
      "$tree/$DECK_REL", "--timeout", "$GAME_TIMEOUT",
      "--out", "$OUT/games_${rblk}_rerun.jsonl",
      "--logdir", "$logdir"]),                       # RAW-RERUN driver
    ("games", "fleet_games_report.py",
     ["--out-dir", "$OUT", "--settings",
      "$CODE_DIR/settings_fleet.json", "--json-out",
      "$OUT/games_report.json",
      "--pairing-only"]),                            # SMOKE report
    ("games", "merge_registry.py",
     ["--registry", REG, "--tag",
      "r10_step2_fleet_smoke", "${SMOKE_IDS[@]}",
      "--vault", VAULT]),                            # SMOKE merge
    ("games", "fleet_games_report.py",
     ["--out-dir", "$OUT", "--settings",
      "$CODE_DIR/settings_fleet.json", "--json-out",
      "$OUT/games_report.json"]),                    # GRES report
    ("games", "merge_registry.py",
     ["--registry", REG, "--tag", "$REGISTRY_TAG",
      "${GRES_IDS[@]}", "--vault", VAULT]),          # GRES merge
    ("games", "fleet_read.py",
     ["--pairing", "$OUT/pairing.json",
      "--games-report", "$OUT/games_report.json",
      "--settings", "$CODE_DIR/settings_fleet.json",
      "--primary-only", "--json-out",
      "$OUT/fleet_read.json"]),                      # READ.G
    # ---- run_fleet_l3.sh ----
    ("l3", "build_fleet_jobs.py",
     ["$STREAM_ARGS", "$STAT_ARGS", "--settings",
      "$CODE_DIR/settings_fleet.json", "--out",
      "$OUT/jobs_all.jsonl", "--shard-prefix",
      "$OUT/jobs_shard", "--report",
      "$OUT/jobs_report.json", "--nshard",
      "$NSHARD"]),                                   # JOBS
    ("l3", "shm_sweep.py",
     ["--log", "$OUT/shm_sweep_$2.log",
      "--start-file", "$OUT/shm_start_$2.txt",
      "--games-dir", "$1/vendor/talishar/Games",
      "--interval", "60", "--stop-file",
      "$OUT/shm_sweep_$2.stop"]),                    # start_sweeper
    ("l3", "fleet_read.py",
     ["--pairing", "$GAMES_OUT/pairing.json",
      "--games-report", "$GAMES_OUT/games_report.json",
      "--settings", "$CODE_DIR/settings_fleet.json",
      "--jobs", "$OUT/jobs_all.jsonl", "--labels",
      "$OUT/labels_all.jsonl", "--games-rows",
      "$GAMES_OUT/games_t1a.jsonl",
      "$GAMES_OUT/games_t1b.jsonl",
      "$GAMES_OUT/games_t2a.jsonl",
      "$GAMES_OUT/games_t2b.jsonl", "--json-out",
      "$GAMES_OUT/fleet_read.json"]),                # READ.F
]

RUNNERS = {
    "games": os.path.join(STEP2, "run_fleet_games.sh"),
    "l3": os.path.join(STEP2, "run_fleet_l3.sh"),
}
SITE_RE = re.compile(
    r'\$PY\s+"\$CODE_DIR/([a-z0-9_]+\.py)"')


def logical_lines(text):
    out, buf = [], ""
    for raw in text.splitlines():
        buf = buf + raw if buf else raw
        if buf.rstrip().endswith("\\"):
            buf = buf.rstrip()[:-1] + " "
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return out


def enumerate_sites():
    sites = []
    for tag, path in RUNNERS.items():
        for line in logical_lines(open(path).read()):
            m = SITE_RE.search(line)
            if not m:
                continue
            rest = line[m.start():]
            toks = shlex.split(rest)
            argv = []
            for t in toks[2:]:
                if t in (">", "||", "|", "&", "2>&1") \
                        or t.startswith(">"):
                    break
                argv.append(t)
            sites.append((tag, m.group(1), argv))
    return sites


def eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return {"int": int, "str": str,
                "float": float}[node.id]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [eval_node(e) for e in node.elts]
    raise ValueError("unsupported node %r" % (node,))


def build_parser(path):
    tree = ast.parse(open(path).read())
    pvars = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) \
                and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func,
                               ast.Attribute) \
                and node.value.func.attr \
                == "ArgumentParser":
            for t in node.targets:
                if isinstance(t, ast.Name):
                    pvars.add(t.id)
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute)
             and n.func.attr == "add_argument"
             and isinstance(n.func.value, ast.Name)
             and n.func.value.id in pvars]
    calls.sort(key=lambda n: n.lineno)
    ap = argparse.ArgumentParser()
    for c in calls:
        ap.add_argument(
            *[eval_node(a) for a in c.args],
            **{kw.arg: eval_node(kw.value)
               for kw in c.keywords})
    return ap


EXPAND = {
    "${SMOKE_IDS[@]}": ["--ids", "X"],
    "${GRES_IDS[@]}": ["--ids", "X"],
    "$STREAM_ARGS": ["--stream", "X"],
    "$STAT_ARGS": ["--stats", "X"],
}


def val(tok, act):
    if "$" not in tok:
        return tok
    if act is not None and act.type is int:
        return "1"
    if act is not None and act.type is float:
        return "1.0"
    return "X"


def substitute(tokens, parser):
    optmap = {}
    for act in parser._actions:
        for opt in act.option_strings:
            optmap[opt] = act
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in EXPAND:
            out += EXPAND[t]
            i += 1
            continue
        if t in optmap:
            act = optmap[t]
            out.append(t)
            if act.nargs == 0:
                i += 1
                continue
            if act.nargs in ("+", "*"):
                j = i + 1
                while j < len(tokens) \
                        and tokens[j] not in optmap \
                        and not tokens[j].startswith("--"):
                    out.append(val(tokens[j], act))
                    j += 1
                i = j
                continue
            out.append(val(tokens[i + 1], act))
            i += 2
            continue
        if t.startswith("--") and "=" in t:
            opt, v = t.split("=", 1)
            if opt in optmap:
                out.append(opt + "=" + val(v, optmap[opt]))
            else:
                out.append(t)
            i += 1
            continue
        if t.startswith("-") and t != "-":
            out.append(t)  # unknown: argparse rejects
            i += 1
            continue
        out.append(val(t, None))  # positional
        i += 1
    return out


def parses(parser, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            parser.parse_args(argv)
            return True
        except SystemExit:
            return False


# ---- pins ----
for fname, pin in sorted(PINS.items()):
    p = os.path.join(STEP2, fname)
    check("the staged %s is its pinned copy "
          "(%s...)" % (fname, pin[:8]),
          sha(p) == pin, sha(p))
PARSERS = {f: build_parser(os.path.join(STEP2, f))
           for f in PINS}

# ---- census + templates ----
sites = enumerate_sites()
check("census: the grep enumeration of both runners "
      "reproduces the contract table exactly "
      "(%d sites)" % len(EXPECTED),
      [(r, t) for r, t, _a in sites]
      == [(r, t) for r, t, _a in EXPECTED],
      "got %s" % ([(r, t) for r, t, _a in sites],))
for idx, (site, exp) in enumerate(zip(sites, EXPECTED)):
    check("site %d (%s %s): argv == the contract "
          "template" % (idx + 1, site[0], site[1]),
          site[2] == exp[2],
          "got %s want %s" % (site[2], exp[2]))

# ---- every site parses under its real argparse ----
for idx, (runner, target, argv) in enumerate(sites):
    sub = substitute(argv, PARSERS[target])
    check("site %d (%s %s): the substituted argv "
          "parses under the real argparse"
          % (idx + 1, runner, target),
          parses(PARSERS[target], sub),
          "argv %s" % (sub,))

# ---- negative cases ----
sweep_argv = substitute(EXPECTED[0][2],
                        PARSERS["shm_sweep.py"])
check("negative: the sweeper's argv + --once FAILS "
      "its real argparse (defect 9's form)",
      not parses(PARSERS["shm_sweep.py"],
                 sweep_argv + ["--once"]))
check("negative: the merge's old bare-files form "
      "(--tag X <ids files>, no --registry/--ids) "
      "FAILS its real argparse (defect 8's form)",
      not parses(PARSERS["merge_registry.py"],
                 ["--tag", "X", "a_ids.txt",
                  "b_ids.txt"]))

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL",
                            name,
                            (" -- " + detail)
                            if detail and not ok else ""))
        bad += 0 if ok else 1
    print("fx_fleet_argparse: %d checks, %d failed"
          % (len(RESULTS), bad))
    raise SystemExit(1 if bad else 0)
