#!/usr/bin/env python3
"""Round-4 abort-reason logging (claude-reply-38dd581 sec.3
requirement): Decide catches its own exceptions and logs the abort
reason at the marker.

The finding this answers (gate fleet, builder-response-31ebec7
sec.4): 8 teacher decisions in 400 games produced the marker - a
rule=teacher trace row with decide_pick null, twinned at the same
seq by Choose's bridge_pick fall-through. The records could not say
why. Primary-record anatomy of one marker (game 397753742, seq 33):

  * RootDecide's own eval of the bridge state succeeded
    (priors_pre present, 5 candidates).
  * Decide's root eval of the SAME state returned null
    (priors_post null; feat_post_hash == feat_pre_hash, i.e. the
    trace stash WAS set from the bridge state before the eval).
  * Decide's eval-null exit DID write a stat row - but the row was
    {teacher:1, fallback:"eval", branch} only: no game, no turn,
    no player, no cause, so per-game accounting could not even
    attribute it. And an exception escaping Decide's body would
    have written nothing at all and propagated out of RootDecide.

This patch, applied to the gate build's search.php
(sha256 6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a):

  1. SimTeacher_Decide becomes a thin wrapper; the gate body is
     renamed SimTeacher_DecideInner, byte-identical. The wrapper
     resets $GLOBALS["ssTeacherAbortReason"], calls Inner, and on
     any Throwable: records the reason
     ("exception:<class>:<message, 120 chars>"), writes a stat row
     for the aborted decision carrying the reason, branch, player,
     turn and game, and returns null - the registered fall-through
     (Choose then plays the bridge pick).
  2. Inside Inner, the root-eval canary throw gets its own reason
     ("root_eval_canary:<class>:<message>"), distinct from an eval
     transport failure ("root_eval_failed", set at the null exit).
     A canary abort and a socket failure are different events and
     must not share a reason string.
  3. The eval-null stat row gains abort_reason, player, turn and
     game (it previously carried none of them).
  4. RootDecide stamps abort_reason on the marker trace row
     (rule=teacher, pick null) from the same global, defaulting to
     "decide_null" if no reason was recorded.

Deliberately NOT changed:
  * Any pick, margin (1.5 paired SE), selection (top-3 + prior
    >= 0.10 cap 4), validity (>= 20 shared finished worlds), or
    k=25 logic - Inner is the gate body verbatim.
  * The canary doctrine: Choose's own SimFeat_Canary on the same
    state runs UNCAUGHT before RootDecide is reached, and the R14
    root canary inside RootDecide runs before Decide; both still
    fail loud exactly as before. The wrapper only sees exceptions
    from code Decide itself runs.
  * Stat-row consumers: the new fields are additive keys on rows
    that already existed (fallback=eval) plus one new fallback
    class (exception); analyze_gate.py / L1 keys are unaffected.

Usage: patch_decide_abort_log.py <tree>   (tree contains search.php)
"""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/otreer1")


def patch(fname, pairs):
    p = tree / fname
    s = p.read_text()
    for old, new in pairs:
        assert old in s, f"anchor missing in {fname}: {old[:70]!r}"
        assert s.count(old) == 1, \
            f"anchor not unique in {fname}: {old[:70]!r}"
        s = s.replace(old, new)
    p.write_text(s)
    print(f"{fname}: {len(pairs)} edits OK")


patch("search.php", [
    # 1. Wrapper + rename. The gate body follows the Inner signature
    #    unchanged ($t0 line is part of the anchor).
    ("""function SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  $t0 = microtime(true);""",
     """function SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  // Abort-reason logging wrapper (round 4): the gate body lives in
  // SimTeacher_DecideInner below, byte-identical. This wrapper only
  // guarantees that a Decide which produces no pick SAYS WHY: the
  // reason lands in $GLOBALS["ssTeacherAbortReason"], a stat row
  // for the aborted decision is written here on the exception path
  // (the eval-null path writes its own, inside Inner), and
  // RootDecide stamps the reason on the marker trace row.
  $GLOBALS["ssTeacherAbortReason"] = null;
  try {
    return SimTeacher_DecideInner($branch, $cands, $candRecs, $player, $gameDir, $bridgeState);
  } catch (Throwable $e) {
    $GLOBALS["ssTeacherAbortReason"] = "exception:" . get_class($e)
      . ":" . substr(strval($e->getMessage()), 0, 120);
    SimSearch_LogStat(["teacher" => 1, "fallback" => "exception",
      "abort_reason" => $GLOBALS["ssTeacherAbortReason"],
      "branch" => $branch, "player" => $player,
      "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "game" => strval($GLOBALS["gameName"] ?? "")]);
    return null;
  }
}

function SimTeacher_DecideInner($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  $t0 = microtime(true);"""),
    # 2. The root-eval canary throw gets a distinct reason.
    ("""    try {
      SimFeat_Canary($player, $bridgeState);
      $evRoot = SimSearch_Eval($bridgeState, $candRecs);
    } catch (Throwable $e) { $evRoot = null; }""",
     """    try {
      SimFeat_Canary($player, $bridgeState);
      $evRoot = SimSearch_Eval($bridgeState, $candRecs);
    } catch (Throwable $e) {
      // Abort-reason logging: a canary throw is a different event
      // from an eval transport failure; give it its own reason.
      $evRoot = null;
      $GLOBALS["ssTeacherAbortReason"] = "root_eval_canary:"
        . get_class($e) . ":" . substr(strval($e->getMessage()), 0, 120);
    }"""),
    # 3. The eval-null stat row gains the reason and the decision's
    #    identity (game / turn / player).
    ("""  if (!$evRoot || !isset($evRoot[0])) {
    SimSearch_LogStat(["teacher" => 1, "fallback" => "eval",
                       "branch" => $branch]);
    return null;
  }""",
     """  if (!$evRoot || !isset($evRoot[0])) {
    // Abort-reason logging: name the cause and the decision. The
    // gate build's row carried only {teacher, fallback, branch},
    // so the fleet's aborted decisions could not be attributed
    // to a game, let alone a cause.
    if (empty($GLOBALS["ssTeacherAbortReason"])) {
      $GLOBALS["ssTeacherAbortReason"] = "root_eval_failed";
    }
    SimSearch_LogStat(["teacher" => 1, "fallback" => "eval",
                       "abort_reason" => $GLOBALS["ssTeacherAbortReason"],
                       "branch" => $branch, "player" => $player,
                       "turn" => intval($GLOBALS["currentTurn"] ?? 0),
                       "game" => strval($GLOBALS["gameName"] ?? "")]);
    return null;
  }"""),
    # 4. RootDecide stamps the reason on the marker trace row.
    ("""      $trc["decide_pick"] = $pick;
      $shadow = getenv("TEACHER_SHADOW");""",
     """      $trc["decide_pick"] = $pick;
      if ($pick === null) {
        // Abort-reason logging: this row is the marker (a teacher
        // row with no pick, twinned by Choose's bridge_pick at the
        // same seq). It now carries WHY Decide produced no pick.
        $trc["abort_reason"] = strval($GLOBALS["ssTeacherAbortReason"] ?? "decide_null");
      }
      $shadow = getenv("TEACHER_SHADOW");"""),
])

print("decide-abort-log patch applied to", tree)
