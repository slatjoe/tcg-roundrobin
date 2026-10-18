#!/usr/bin/env python3
"""Round-3 instrumentation patch (Claude round-2 design): per-decision
trace at the consumer boundary in every arm + shadow mode.

Applies to a sim tree's policy_server.php and search.php:
  policy_server.php (loaded in BOTH bridge and search modes, so the
  helpers live here):
    T1 trace helpers: SimTrace_On/Log/Hash/RngFingerprint/ZoneHash/
       CandHash. RNG fingerprint = fork, one mt_rand in the child, exit
       (reads the stream position without consuming it).
    T2 bridge pick row in SimPolicyServer_Choose (rule=bridge_pick),
       pass row (rule=pass_gate), DQ rows (rule=dq_pick), and the
       shared decision counter handed to RootDecide (ssTraceDec).
  search.php:
    T3 SimSearch_EvalState stashes its built state hash + priors for
       the tracer (ssTraceLastEval).
    T4 RootDecide: PRE capture before the checkpoint block (features
       built from untouched live globals + eval-endpoint priors on
       them, zone hash, RNG fingerprint); POST capture after
       SimTeacher_Decide (features/priors Decide actually used, zone
       hash, fingerprint). TEACHER_SHADOW=1: Decide runs in full,
       then the bridge's native pick (pick endpoint over the PRE
       state, i.e. the state Choose featurized) is played instead.

Production behavior is unchanged when TCG_TRACE_LOG is unset and
TEACHER_SHADOW is unset: every insert is env-gated except the
EvalState stash (gated by SimTrace_On()).
"""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tracetree")


def patch(fname, pairs):
    p = tree / fname
    s = p.read_text()
    for old, new in pairs:
        assert old in s, f"anchor missing in {fname}: {old[:70]!r}"
        assert s.count(old) == 1, f"anchor not unique in {fname}: {old[:70]!r}"
        s = s.replace(old, new)
    p.write_text(s)
    print(f"{fname}: {len(pairs)} edits OK")


HELPERS = r'''
// ---- round-3 trace instrumentation (Claude round-2 design) ----
// Written at the consumer boundary in every arm when TCG_TRACE_LOG is
// set. One row per decision, keyed by the bridge's own decision
// counter (simPolicyDecision) so arms align by seq.
function SimTrace_On() {
  $d = getenv("TCG_TRACE_LOG");
  return $d !== false && $d !== "";
}
function SimTrace_Log($row) {
  if (!SimTrace_On()) return;
  $dir = getenv("TCG_TRACE_LOG");
  if (!is_dir($dir)) @mkdir($dir, 0700, true);
  $row["game"] = strval($GLOBALS["gameName"] ?? "");
  @file_put_contents(rtrim($dir, "/") . "/trace_" . $row["game"] . ".jsonl",
    json_encode($row) . "\n", FILE_APPEND);
}
function SimTrace_Hash($x) {
  return substr(hash("sha256", json_encode($x)), 0, 16);
}
function SimTrace_RngFingerprint() {
  // Fork, draw one mt_rand in the child, exit: reads the live stream
  // position without consuming it (Claude's construction).
  if (!function_exists("pcntl_fork")) return null;
  $f = sys_get_temp_dir() . "/rngfp_" . getmypid() . ".txt";
  @unlink($f);
  $pid = pcntl_fork();
  if ($pid === -1) return null;
  if ($pid === 0) { @file_put_contents($f, strval(mt_rand())); exit(0); }
  pcntl_waitpid($pid, $st);
  $v = @file_get_contents($f);
  @unlink($f);
  return $v === false ? null : intval($v);
}
function SimTrace_ZoneHash() {
  $z = [];
  foreach (["p1Hand","p2Hand","p1Deck","p2Deck","p1Arsenal","p2Arsenal",
            "p1Character","p2Character","p1Items","p2Items","p1Allies",
            "p2Allies","p1Banish","p2Banish","p1Graveyard","p2Graveyard",
            "p1Pitch","p2Pitch","p1Life","p2Life","currentTurn",
            "currentPlayer","mainPlayerActionPoints",
            "defPlayerActionPoints","mainPlayerRemainingResources",
            "defPlayerRemainingResources"] as $k) {
    $z[$k] = $GLOBALS[$k] ?? null;
  }
  return SimTrace_Hash($z);
}
function SimTrace_CandHash($candRecs) {
  return SimTrace_Hash(array_map(function ($c) {
    return [strval($c["card_id"]), strval($c["zone"]),
            intval($c["zone_index"])];
  }, $candRecs));
}
'''

patch("policy_server.php", [
    # T1: helpers after SimPolicyServer_Stats
    ("""function SimPolicyServer_Stats() {
  return [
    "queries" => intval($GLOBALS["simPolicyQueries"] ?? 0),
    "fallbacks" => intval($GLOBALS["simPolicyFallbacks"] ?? 0),
  ];
}""",
     """function SimPolicyServer_Stats() {
  return [
    "queries" => intval($GLOBALS["simPolicyQueries"] ?? 0),
    "fallbacks" => intval($GLOBALS["simPolicyFallbacks"] ?? 0),
  ];
}
""" + HELPERS),
    # T2a: pass row
    ("""  if (!$gate || $cands === []) {
    // No real choice (gate failed or nothing playable): pass, log locally.
    SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, -1, $dec);""",
     """  if (!$gate || $cands === []) {
    // No real choice (gate failed or nothing playable): pass, log locally.
    if (SimTrace_On()) {
      SimTrace_Log(["seq" => $dec, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
        "branch" => $branch, "player" => $player,
        "state_hash" => SimTrace_Hash($state),
        "cand_hash" => SimTrace_CandHash($candRecs),
        "ncand" => count($candRecs), "chosen" => -1, "rule" => "pass_gate",
        "rng" => SimTrace_RngFingerprint()]);
    }
    SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, -1, $dec);"""),
    # T2b: hand the seq to RootDecide
    ("""    $sidx = SimSearch_RootDecide($branch, $cands, $candRecs, intval($player));""",
     """    $GLOBALS["ssTraceDec"] = $dec;
    $sidx = SimSearch_RootDecide($branch, $cands, $candRecs, intval($player));"""),
    # T2c: bridge pick row
    ("""  SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $idx, $dec);
  return [true, $cands[$idx]];""",
     """  if (SimTrace_On()) {
    SimTrace_Log(["seq" => $dec, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "branch" => $branch, "player" => $player,
      "state_hash" => SimTrace_Hash($state),
      "cand_hash" => SimTrace_CandHash($candRecs),
      "ncand" => count($candRecs), "chosen" => $idx, "rule" => "bridge_pick",
      "rng" => SimTrace_RngFingerprint()]);
  }
  SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $idx, $dec);
  return [true, $cands[$idx]];"""),
    # T2d: DQ pick row
    ("""  SimPolicyServer_LogTrajectory("DQ", $playerID, $state, $candRecs, $idx, $dec);
  return $options[$idx];""",
     """  if (SimTrace_On()) {
    SimTrace_Log(["seq" => $dec, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "branch" => "DQ", "player" => intval($playerID),
      "state_hash" => SimTrace_Hash($state),
      "cand_hash" => SimTrace_CandHash($candRecs),
      "ncand" => count($candRecs), "chosen" => $idx, "rule" => "dq_pick",
      "rng" => SimTrace_RngFingerprint()]);
  }
  SimPolicyServer_LogTrajectory("DQ", $playerID, $state, $candRecs, $idx, $dec);
  return $options[$idx];"""),
])

patch("search.php", [
    # T3: EvalState stash
    ("""  return SimSearch_Eval($state, $candRecs);
}""",
     """  $ev = SimSearch_Eval($state, $candRecs);
  if (SimTrace_On()) {
    $GLOBALS["ssTraceLastEval"] = [
      "state_hash" => SimTrace_Hash($state),
      "priors" => ($ev !== null && isset($ev[0])) ? $ev[0] : null];
  }
  return $ev;
}"""),
    # T4a: PRE capture before the checkpoint block
    ("""  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();""",
     """  // Round-3 trace: PRE capture on the untouched live globals (the
  // state the bridge would featurize), before the checkpoint block.
  $trc = null;
  if (SimTrace_On() && empty($GLOBALS["simSearchChild"])
      && empty($GLOBALS["simLabelChild"])) {
    $stPre = null;
    try { $stPre = SimFeat_BuildState($player, $branch, $candRecs); }
    catch (Throwable $e) { $stPre = null; }
    $evPre = ($stPre !== null) ? SimSearch_Eval($stPre, $candRecs) : null;
    $trc = ["seq" => intval($GLOBALS["ssTraceDec"] ?? -1),
      "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "branch" => $branch, "player" => $player,
      "feat_pre_hash" => ($stPre !== null) ? SimTrace_Hash($stPre) : null,
      "priors_pre" => ($evPre !== null && isset($evPre[0])) ? $evPre[0] : null,
      "zone_pre" => SimTrace_ZoneHash(),
      "rng_pre" => SimTrace_RngFingerprint(),
      "cand_hash" => SimTrace_CandHash($candRecs),
      "ncand" => count($candRecs), "state_pre" => $stPre];
  }
  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();"""),
    # T4b: traced teacher return + shadow mode
    ("""  if (getenv("TEACHER_MODE")) {
    return SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir);
  }""",
     """  if (getenv("TEACHER_MODE")) {
    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir);
    if ($trc !== null) {
      $post = $GLOBALS["ssTraceLastEval"] ?? [];
      $trc["feat_post_hash"] = $post["state_hash"] ?? null;
      $trc["priors_post"] = $post["priors"] ?? null;
      $trc["zone_post"] = SimTrace_ZoneHash();
      $trc["rng_post"] = SimTrace_RngFingerprint();
      $trc["decide_pick"] = $pick;
      $shadow = getenv("TEACHER_SHADOW");
      if ($shadow !== false && $shadow !== "" && $shadow !== "0"
          && ($trc["state_pre"] ?? null) !== null) {
        // Shadow mode (Claude round-2): the machinery does everything,
        // but the bridge's native choice is played - the pick
        // endpoint's answer over the PRE state and the shared
        // candidate list, exactly what a bridge game plays.
        $bIdx = SimPolicyServer_Query([
          "v" => 1, "game" => strval($GLOBALS["gameName"] ?? ""),
          "decision" => intval($GLOBALS["ssTraceDec"] ?? -1),
          "branch" => $branch, "player" => $player,
          "state" => $trc["state_pre"], "candidates" => $candRecs,
          "gate_pass" => true]);
        if ($bIdx !== null && $bIdx >= 0 && $bIdx < count($candRecs)) {
          $trc["chosen"] = $bIdx; $trc["rule"] = "shadow_bridge";
          $pick = $bIdx;
        } else {
          $trc["chosen"] = $pick; $trc["rule"] = "shadow_fallback_decide";
        }
      } else {
        $trc["chosen"] = $pick;
        $trc["rule"] = getenv("TEACHER_GHOST") ? "ghost_prior" : "teacher";
      }
      unset($trc["state_pre"]);
      SimTrace_Log($trc);
    }
    return $pick;
  }"""),
])
print("patch_trace_shadow: all edits applied")
