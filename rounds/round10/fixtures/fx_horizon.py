#!/usr/bin/env python3
"""Fixture: the sec.14 horizon mechanism, demonstrated
on the REAL rollout code, and the sec.14 fix, proven
on the same harness.

Standing rule (sec.14 spec, claude-reply-28c2065
sec.2-3): fixtures may read only what's published in
the repo. This fixture reads two published files:
  AS-BUILT: rounds/round9/code/search_s2.php (the
    bytes the probe eval and the round-9 label fleets
    ran; the round-10 copy was byte-identical through
    fix pass 5).
  FIXED:    rounds/round10/code/search_s2.php (the
    sec.14-patched copy; round 9's file untouched).

From EACH file it extracts, verbatim, (A) the
SimLabel_RunRollout rollout loop (the while block)
and (B) the exit classification statements (winner /
outcome / horizonApplied), and executes them under
the local php8.3 with stub engine functions driven
by scripted step behavior from a late snapshot
(currentTurn starts at 58; the horizon is 62):

  stall1    every finish step advances 1 turn, the
            game never ends. As-built: the check
            runs only after a full 20-step inner
            block, so the world exits at turn 78 --
            16 finish steps BEGAN at or past the
            trigger. Fixed: the per-step check stops
            the world at exactly 62 and no step begins
            at >= 62.
  stalljump like stall1, except the step beginning
            at turn 61 advances 12 turns (a drive step
            spanning turns, the live driver's stated
            reason for its per-step cap check).
            As-built exits at 89. Fixed flags horizon
            at the first step boundary past the
            trigger (exit turn 73 -- the within-step
            overshoot the live instrument also
            records, capped games ending 62-71 --
            but flagged a draw, never decisive, and
            no further step runs).
  wincross  the step that brings currentTurn to 65
            also ends the game with the root player
            winning. As-built records a DECISIVE win
            at turn 65 -- an outcome the live game
            cannot produce (its cap scores the game a
            draw the moment currentTurn reaches 62).
            Fixed: the per-step check fires at 62,
            before the winning step ever runs; the
            world exits a horizon draw at 62.
  win61     the step bringing currentTurn to 61
            ends the game, root wins. Fixed: turn 61
            is the last decisive turn -- the win
            stands, horizon flag 0.

Confinement (H1/H2): with comment lines stripped,
the fixed loop equals the as-built loop plus exactly
the per-step check lines, and the fixed exit
classification is exactly the override form.

Limits, stated: the harness drives the extracted
loop with stubs, not a full engine game -- it proves
the check PLACEMENT and the exit classification,
which are the sec.14 mechanism; it does not measure
how often real snapshots stall (the published rows
carry that: horizon worlds' median exit ~95).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASBUILT = os.path.join(REPO, "rounds", "round9", "code",
                       "search_s2.php")
FIXED = os.path.join(REPO, "rounds", "round10", "code",
                     "search_s2.php")
FAILED = []


def check(name, cond, extra=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name,
                       (" -- " + extra) if extra else ""))
    if not cond:
        FAILED.append(name)


def find_php():
    cands = [os.environ.get("PHP"),
             os.path.expanduser(
                 "~/workspace/tcg-sim/.tools/php83/"
                 "usr/bin/php8.3"),
             shutil.which("php"), shutil.which("php8.3")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def extract_loop(text):
    """The verbatim while block of SimLabel_RunRollout."""
    fn = text.index("function SimLabel_RunRollout")
    start = text.index("while (!IsGameOver() && $guard < 400) {",
                       fn)
    depth = 0
    i = start
    while True:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    line_start = text.rindex("\n", 0, start) + 1
    return text[line_start:end]


def extract_exit(text):
    """The exit classification statements, verbatim,
    comment lines removed. The three assignments
    (winner / outcome / horizonApplied) sit within a
    few lines of each other in both files but in
    DIFFERENT orders (as-built: winner, outcome,
    horizonApplied; fixed: horizonApplied, winner,
    outcome) -- take from the first of them through
    the last of them."""
    lines = text.splitlines()
    first = None
    for j, ln in enumerate(lines):
        if ("$horizonApplied = $horizonHit" in ln
                or "$winner = IsGameOver()" in ln):
            first = j
            break
    assert first is not None
    last = first
    for j in range(first, min(len(lines), first + 12)):
        if re.search(r"\$(winner|outcome|horizonApplied)"
                     r"\s*=", lines[j]):
            last = j
    stmts = [ln for ln in lines[first:last + 1]
             if ln.strip() and not ln.strip().startswith("//")]
    return "\n".join(stmts)


HARNESS = """<?php
// fx_horizon harness: stubs + the verbatim extracted
// loop and exit classification (appended by the
// fixture between the markers).
$GLOBALS["currentTurn"] = intval($argv[2]);
$GLOBALS["winner"] = 0;
$GLOBALS["gameOver"] = false;
$GLOBALS["__mode"] = $argv[1];
$GLOBALS["__begunAt"] = array();
$GLOBALS["__stepIdx"] = 0;
function IsGameOver() { return $GLOBALS["gameOver"]; }
function PuzzleBeginStep($pl) {}
function PuzzleFinishStep() {
  $GLOBALS["__begunAt"][] = $GLOBALS["currentTurn"];
  $adv = 1;
  if ($GLOBALS["__mode"] === "stalljump"
      && $GLOBALS["currentTurn"] === 61) $adv = 12;
  $GLOBALS["currentTurn"] += $adv;
  $GLOBALS["__stepIdx"]++;
  if (($GLOBALS["__mode"] === "wincross"
       && $GLOBALS["currentTurn"] >= 65)
      || ($GLOBALS["__mode"] === "win61"
          && $GLOBALS["currentTurn"] >= 61)) {
    $GLOBALS["winner"] = 1;
    $GLOBALS["gameOver"] = true;
  }
}
function SimStateHash($a, $b) {
  return "k" . $GLOBALS["__stepIdx"] . "_"
    . $GLOBALS["currentTurn"];
}
$horizon = 62; $horizonHit = false; $root = 1;
$guard = 0; $lastKey = ""; $stuck = 0;
//__LOOP__
//__EXIT__
echo json_encode(array(
  "turns" => $GLOBALS["currentTurn"],
  "winner" => $winner, "outcome" => $outcome,
  "horizonApplied" => $horizonApplied,
  "horizonHit" => $horizonHit,
  "steps_run" => $GLOBALS["__stepIdx"],
  "begun_at" => $GLOBALS["__begunAt"])), "\n";
"""


def run_case(php, tmp, tag, loop, exit_stmts, mode,
             start=58):
    src = HARNESS.replace("//__LOOP__", loop)
    src = src.replace("//__EXIT__", exit_stmts)
    path = os.path.join(tmp, "harness_%s.php" % tag)
    with open(path, "w") as fh:
        fh.write(src)
    out = subprocess.run([php, path, mode, str(start)],
                         capture_output=True, text=True,
                         timeout=60)
    if out.returncode != 0:
        return {"error": out.stderr.strip()[:300]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def strip_comments(block):
    return [ln for ln in block.splitlines()
            if ln.strip() and not ln.strip().startswith("//")]


def main():
    php = find_php()
    check("H0: a php binary is available for the "
          "horizon harness", php is not None, str(php))
    if php is None:
        return 1
    for tag, path in (("as-built", ASBUILT), ("fixed", FIXED)):
        out = subprocess.run([php, "-l", path],
                             capture_output=True, text=True)
        check("H0 %s file lints under php" % tag,
              out.returncode == 0)
    ab = open(ASBUILT).read()
    fx = open(FIXED).read()
    ab_loop, fx_loop = extract_loop(ab), extract_loop(fx)
    ab_exit, fx_exit = extract_exit(ab), extract_exit(fx)

    # ---- confinement ---------------------------------------------
    added = ('if ($horizon > 0 && intval($GLOBALS["currentTurn"]'
             ' ?? 0) >= $horizon) { $horizonHit = true; break; }')
    ab_core = strip_comments(ab_loop)
    fx_core = strip_comments(fx_loop)
    check("H1: the as-built loop carries the horizon "
          "check only AFTER the inner finish-step loop",
          sum("horizonHit = true" in ln for ln in ab_core) == 1
          and ab_core.index(
              [ln for ln in ab_core
               if "horizonHit = true" in ln][0])
          > ab_core.index(
              [ln for ln in ab_core
               if "PuzzleFinishStep();" in ln][0]))
    # remove exactly ONE occurrence of the check line
    # (the inner one -- the outer per-iteration check
    # is textually identical and must stay)
    fx_reduced = []
    dropped = False
    for ln in fx_core:
        if not dropped and ln.strip() == added:
            dropped = True
            continue
        fx_reduced.append(ln)
    # the fixed for-header gained braces (its body is
    # now two statements); collapse the three lines
    # back to the as-built single-statement form for
    # the comparison
    collapsed = []
    j = 0
    while j < len(fx_reduced):
        ln = fx_reduced[j]
        if (ln.strip().endswith("++$k) {")
                and j + 2 < len(fx_reduced)
                and fx_reduced[j + 1].strip()
                == "PuzzleFinishStep();"
                and fx_reduced[j + 2].strip() == "}"):
            collapsed.append(
                ln.replace("++$k) {", "++$k)")
                + " PuzzleFinishStep();")
            j += 3
        else:
            collapsed.append(ln)
            j += 1
    check("H1: fixed loop = as-built loop + the "
          "per-step check inside the finish-step loop, "
          "nothing else",
          collapsed == ab_core,
          "as-built %d core lines, fixed %d"
          % (len(ab_core), len(fx_core)))
    inner = fx_loop[fx_loop.index("for ($k = 0;"):
                    fx_loop.index("$key = SimStateHash")]
    check("H1: the added check sits INSIDE the "
          "PuzzleFinishStep loop body",
          inner.count("PuzzleFinishStep();") == 1
          and "horizonHit = true" in inner
          and inner.index("PuzzleFinishStep();")
          < inner.index("horizonHit = true"))
    check("H2: exit classification -- as-built gates "
          "the flag on !IsGameOver(); fixed overrides",
          "$horizonApplied = ($horizonHit && !IsGameOver())"
          " ? 1 : 0;" in ab_exit
          and "$horizonApplied = $horizonHit ? 1 : 0;"
          in fx_exit
          and "$winner = ($horizonApplied === 1) ? 0"
          in fx_exit)

    tmp = tempfile.mkdtemp(prefix="fx_horizon_")
    cases = {}
    for tag, loop, ex in (("ab", ab_loop, ab_exit),
                          ("fx", fx_loop, fx_exit)):
        for mode in ("stall1", "stalljump", "wincross",
                     "win61"):
            cases[(tag, mode)] = run_case(
                php, tmp, "%s_%s" % (tag, mode), loop, ex,
                mode)
    for k, v in sorted(cases.items()):
        check("H3: harness ran %s/%s" % k, "error" not in v,
              v.get("error", ""))

    r = cases[("ab", "stall1")]
    check("H4 AS-BUILT stall: world passes the "
          "trigger -- exits at turn 78 after a full "
          "20-step block; 16 steps began at >= 62",
          r["turns"] == 78 and r["steps_run"] == 20
          and sum(1 for t in r["begun_at"] if t >= 62) == 16
          and r["horizonApplied"] == 1,
          "turns %s steps %s" % (r["turns"], r["steps_run"]))
    r = cases[("ab", "stalljump")]
    check("H5 AS-BUILT jump: exits at turn 89",
          r["turns"] == 89 and r["horizonApplied"] == 1,
          "turns %s" % r["turns"])
    r = cases[("ab", "wincross")]
    check("H6 AS-BUILT win-crossing: a DECISIVE win "
          "is recorded at turn 65 (winner root, "
          "outcome +1, horizon flag 0) -- an outcome "
          "the live game cannot produce",
          r["turns"] == 65 and r["winner"] == 1
          and r["outcome"] == 1.0
          and r["horizonApplied"] == 0,
          "turns %s winner %s horizon %s"
          % (r["turns"], r["winner"], r["horizonApplied"]))

    r = cases[("fx", "stall1")]
    check("H7 FIXED stall: stops at exactly 62, "
          "horizon draw, no step began at >= 62",
          r["turns"] == 62 and r["winner"] == 0
          and r["horizonApplied"] == 1
          and max(r["begun_at"]) == 61,
          "turns %s begun max %s"
          % (r["turns"], max(r["begun_at"])))
    r = cases[("fx", "stalljump")]
    check("H8 FIXED jump: horizon flag at the first "
          "step boundary past the trigger (exit 73, "
          "the within-step overshoot), draw, no step "
          "began at >= 62, never decisive",
          r["turns"] == 73 and r["winner"] == 0
          and r["horizonApplied"] == 1
          and max(r["begun_at"]) == 61,
          "turns %s" % r["turns"])
    r = cases[("fx", "wincross")]
    check("H9 FIXED win-crossing: the check fires at "
          "62 before the winning step runs -- horizon "
          "draw at 62 in 4 steps",
          r["turns"] == 62 and r["winner"] == 0
          and r["horizonApplied"] == 1
          and r["steps_run"] == 4,
          "turns %s steps %s" % (r["turns"], r["steps_run"]))
    r = cases[("fx", "win61")]
    check("H10 FIXED win at 61: turn 61 is the last "
          "decisive turn -- the win stands, flag 0",
          r["turns"] == 61 and r["winner"] == 1
          and r["outcome"] == 1.0
          and r["horizonApplied"] == 0,
          "turns %s" % r["turns"])
    r = cases[("ab", "win61")]
    check("H10 as-built agrees on a turn-61 win "
          "(pre-trigger behavior unchanged)",
          r["turns"] == 61 and r["winner"] == 1
          and r["horizonApplied"] == 0)

    print("fx_horizon: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
