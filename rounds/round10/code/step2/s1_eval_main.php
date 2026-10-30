<?php
// Round-10 Step 1 pilot copy (2026-10-29): byte-identical
// to rounds/round10/code/s1_eval_main.php (73ed2482...)
// EXCEPT the jobs loader below, which is now the LOUD
// loader of s2_label_main.php's sec.12 form: every
// non-empty line must decode, a failing line aborts
// (exit 2) NAMING the line, and the decoded count is
// asserted against the line count. The round-9 form
// silently dropped undecodable lines (the pattern
// that lost attempt 3's ten Infinity jobs in the
// label path). Standing requirement:
// claude-reply-243b9d8 sec.3.5 (strict job files, loud
// loaders in every PHP job reader, this file named).
//
// Round-9 Stage 1 evaluator driver: derived from
// r9_label_main.php (sha256 2463fc29...) -- the sec.4(C)
// pinned-parameter pattern generalized from the single
// horizon pin to the full Stage-1 setting tuple
// (claude-reply-16f02e2 sec.4.4; clause 8 of the Stage 0
// package, discharged here).
//
// The run's setting is pinned by env: EVAL_SETTING_NAME,
// EVAL_HOOKS, EVAL_DEADLINE_S, LABEL_HORIZON ("off" or a
// non-negative integer turn, the r9 semantics verbatim),
// EVAL_HORIZON_VALUE (a decimal: "-1", "0"), EVAL_K (worlds
// per candidate). Every job must carry a "setting" object
// equal to the pins, field by field -- a missing field or a
// mismatch aborts (exit 2) before any evaluation. Every
// emitted world row and stat row is stamped with the full
// tuple; stage1_analyze.py audits the stamps against
// settings_stage1.json (the second placement of the rule).
//
// Per job the driver runs the label machinery
// (SimLabel_RunForSnapshot) at W = EVAL_K over the job's
// selected candidate set, pair "va", forwarding the
// setting's hook budget and per-candidate deadline through
// cfg into the evaluator build (code/search_s1.php). Per-job
// wall time is measured around the call and written with
// per-candidate finished counts and error tallies to the
// stats file (env EVAL_STATS) -- the analyzer's cost and
// completion inputs.
//
// HORIZON_VALUE is a pin of the run, stamped on every row;
// the valuation itself is applied by the analyzer from the
// raw world outcomes (the label child writes drawn worlds
// as outcome 0.0 / winner 0, exactly as in Stage 0), so
// both registered reads (draw = 0 primary, 0.5 co-report,
// ruling sec.3) come from one set of rows.
//
// Usage: php s1_eval_main.php <deck> <deck> --policy-search
//   --games 1   (argv mimics the labeler so play_game loads
//   the search bootstrap)
// Each job: {snap_dir, snap, game, player, branch, cands,
//   selected, prior_pick, setting{name, hooks, deadline_s,
//   horizon, horizon_value, k}}
// Env: MEAS_JOBS, MEAS_OUT, MEAS_SEED, TCG_POLICY_SOCK,
//   EVAL_STATS, and the pin set above.
$jobsFile = getenv("MEAS_JOBS"); $outFile = getenv("MEAS_OUT");
$statsFile = getenv("EVAL_STATS");
$seedBase = intval(getenv("MEAS_SEED") ?: 424242);
putenv("LABEL_DRIVER=1");
include "play_game.php"; // loads vendor + search.php, returns under LABEL_DRIVER

function s1_abort($msg) {
  fwrite(STDERR, "ABORT: $msg\n");
  exit(2);
}
function s1_pin_int($env, $min) {
  $v = getenv($env);
  if ($v === false || !preg_match('/^\d+$/', strval($v))) {
    s1_abort("$env '" . var_export($v, true) . "' is not a non-negative integer");
  }
  $n = intval($v);
  if ($n < $min) s1_abort("$env $n is below its minimum $min");
  return $n;
}

$ST_NAME = getenv("EVAL_SETTING_NAME");
if ($ST_NAME === false || strval($ST_NAME) === "") {
  s1_abort("EVAL_SETTING_NAME is missing");
}
$ST_NAME = strval($ST_NAME);
$HOOKS = s1_pin_int("EVAL_HOOKS", 1);
$DEADLINE = s1_pin_int("EVAL_DEADLINE_S", 1);
$hzRaw = getenv("LABEL_HORIZON");
if ($hzRaw === false || $hzRaw === "" || $hzRaw === "off") {
  $HORIZON = 0;
} elseif (preg_match('/^\d+$/', strval($hzRaw))) {
  $HORIZON = intval($hzRaw);
} else {
  s1_abort("LABEL_HORIZON '$hzRaw' is not 'off' or a non-negative integer");
}
$hvRaw = getenv("EVAL_HORIZON_VALUE");
if ($hvRaw === false || !preg_match('/^-?\d+(\.\d+)?$/', strval($hvRaw))) {
  s1_abort("EVAL_HORIZON_VALUE '" . var_export($hvRaw, true) .
           "' is not a decimal number");
}
$HVAL = floatval($hvRaw);
$K = s1_pin_int("EVAL_K", 1);
if ($statsFile === false || strval($statsFile) === "") {
  s1_abort("EVAL_STATS is missing");
}
$SETTING = ["name" => $ST_NAME, "hooks" => $HOOKS,
            "deadline_s" => $DEADLINE, "horizon" => $HORIZON,
            "horizon_value" => $HVAL, "k" => $K];

$jobs = [];
$linesRead = 0; $lineNo = 0;
foreach (file($jobsFile) as $ln) {
  $lineNo++;
  $ln = trim($ln); if ($ln === "") continue;
  $linesRead++;
  $j = json_decode($ln, true);
  if (!is_array($j)) {
    s1_abort("jobs line $lineNo of $jobsFile is not " .
             "valid JSON (" . json_last_error_msg() .
             "); a silently dropped job shifts every " .
             "later job's seed base -- the eval run " .
             "refuses to proceed");
  }
  $jobs[] = $j;
}
if (count($jobs) !== $linesRead) {
  s1_abort("jobs load mismatch in $jobsFile: " .
           "$linesRead non-empty lines read, " .
           count($jobs) . " jobs decoded");
}
foreach ($jobs as $j) {
  $snap = strval($j["snap"] ?? "?");
  $s = $j["setting"] ?? null;
  if (!is_array($s)) {
    s1_abort("job for snap $snap carries no setting tuple != run pin " .
             json_encode($SETTING));
  }
  $bad = null;
  if (strval($s["name"] ?? "") !== $ST_NAME) $bad = "name";
  elseif (intval($s["hooks"] ?? -1) !== $HOOKS) $bad = "hooks";
  elseif (intval($s["deadline_s"] ?? -1) !== $DEADLINE) $bad = "deadline_s";
  elseif (intval($s["horizon"] ?? -1) !== $HORIZON) $bad = "horizon";
  elseif (!isset($s["horizon_value"]) ||
          floatval($s["horizon_value"]) !== $HVAL) $bad = "horizon_value";
  elseif (intval($s["k"] ?? -1) !== $K) $bad = "k";
  if ($bad !== null) {
    s1_abort("job for snap $snap setting field $bad = " .
             var_export($s[$bad] ?? null, true) .
             " != run pin " . json_encode($SETTING));
  }
}
fwrite(STDERR, "s1 eval jobs=" . count($jobs) . " setting=" .
       json_encode($SETTING) . "\n");
foreach ($jobs as $ji => $j) {
  $meta = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]), "branch" => strval($j["branch"]),
           "cands" => $j["cands"]];
  $cfg = ["W" => $K, "horizon" => $HORIZON, "hookBudget" => $HOOKS,
          "deadlineS" => $DEADLINE, "cap" => count($j["cands"]),
          "seedBase" => $seedBase + $ji * 100003,
          "pair" => "va", "candIdx" => $j["selected"]];
  $t0 = microtime(true);
  try {
    $rows = SimLabel_RunForSnapshot(rtrim($j["snap_dir"], "/") . "/", $meta, $cfg);
  } catch (Throwable $e) {
    fwrite(STDERR, "snap " . $j["snap"] . " failed: " . $e->getMessage() . "\n");
    continue;
  }
  $wallMs = intval(round((microtime(true) - $t0) * 1000));
  $fh = fopen($outFile, "a");
  foreach ($rows as $r) {
    $r["setting"] = $SETTING;
    $r["prior_pick"] = intval($j["prior_pick"]);
    $r["game"] = strval($j["game"]);
    fwrite($fh, json_encode($r) . "\n");
  }
  fclose($fh);
  $fin = []; $cnt = []; $errs = []; $fb = 0;
  foreach (array_map("intval", $j["selected"]) as $ci) {
    $fin[$ci] = 0; $cnt[$ci] = 0;
  }
  foreach ($rows as $r) {
    $ci = intval($r["cand"]);
    if (!isset($cnt[$ci])) { $cnt[$ci] = 0; $fin[$ci] = 0; }
    $cnt[$ci] += 1;
    $res = $r["result"] ?? null;
    if (is_array($res) && isset($res["error"])) {
      $ec = strval($res["error"]);
      $errs[$ec] = ($errs[$ec] ?? 0) + 1;
    } elseif (is_array($res)) {
      $fb += intval($res["fallbacks"] ?? 0);
      if (intval($res["finished"] ?? 0) === 1) $fin[$ci] += 1;
    }
  }
  $stat = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]),
           "branch" => strval($j["branch"]), "setting" => $SETTING,
           "wall_ms" => $wallMs, "cand_finished" => (object)$fin,
           "cand_rows" => (object)$cnt, "errors" => (object)$errs,
           "fallbacks" => $fb, "prior_pick" => intval($j["prior_pick"]),
           "selected" => array_map("intval", $j["selected"])];
  $sf = fopen($statsFile, "a");
  fwrite($sf, json_encode($stat) . "\n");
  fclose($sf);
  fwrite(STDERR, "done " . $j["snap"] . " rows=" . count($rows) .
         " wall_ms=" . $wallMs . "\n");
}
fwrite(STDERR, "S1-EVAL-DONE setting=" . $ST_NAME . "\n");
