<?php
// Round-9 horizon labeler: byte-derived from meas_label_main.php
// (sha256 3109176b...) with ONLY the D7 horizon pin added (see
// fixtures/r9_label_main_diff.txt). Used for the Stage-0 horizon
// co-report pass in the horizon tree (code/search_horizon.php).
// The pin: env LABEL_HORIZON is "off" (pin 0; the default) or a
// non-negative integer turn. Every job must carry "horizon" equal
// to the pin — a mismatch or a missing value aborts (exit 2)
// before any labeling. Every emitted row is stamped "horizon".
//
// Measurement labeler (Claude's pre-registered design, 2026-10-18):
// label the teacher's SELECTED candidate set at every contested
// decision captured from plain v15 games, pair "va" (the deployed
// teacher's continuation), k worlds per candidate.
// Usage: php meas_label_main.php <deck> <deck> --policy-search --games 1
//   (argv mimics label_main so play_game loads the search bootstrap)
// Each job: {snap_dir, snap, game, player, branch, cands, selected,
//   prior_pick}
// Env: MEAS_JOBS, MEAS_OUT, MEAS_SEED, TCG_POLICY_SOCK, LABEL_W (25).
$jobsFile = getenv("MEAS_JOBS"); $outFile = getenv("MEAS_OUT");
$seedBase = intval(getenv("MEAS_SEED") ?: 424242);
putenv("LABEL_DRIVER=1");
include "play_game.php"; // loads vendor + search.php, returns under LABEL_DRIVER
$W = intval(getenv("LABEL_W") ?: 25);
$hzRaw = getenv("LABEL_HORIZON");
if ($hzRaw === false || $hzRaw === "" || $hzRaw === "off") {
  $HORIZON = 0;
} elseif (preg_match('/^\d+$/', strval($hzRaw))) {
  $HORIZON = intval($hzRaw);
} else {
  fwrite(STDERR, "ABORT: LABEL_HORIZON '$hzRaw' is not 'off' or a non-negative integer\n");
  exit(2);
}
$jobs = [];
foreach (file($jobsFile) as $ln) {
  $ln = trim($ln); if ($ln === "") continue;
  $j = json_decode($ln, true); if (is_array($j)) $jobs[] = $j;
}
foreach ($jobs as $j) {
  if (!array_key_exists("horizon", $j) || intval($j["horizon"]) !== $HORIZON) {
    fwrite(STDERR, "ABORT: job for snap " . strval($j["snap"] ?? "?") .
      " carries horizon " . var_export($j["horizon"] ?? null, true) .
      " != LABEL_HORIZON pin $HORIZON\n");
    exit(2);
  }
}
fwrite(STDERR, "meas jobs=" . count($jobs) . " W=$W horizon=$HORIZON\n");
foreach ($jobs as $ji => $j) {
  $meta = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]), "branch" => strval($j["branch"]),
           "cands" => $j["cands"]];
  $cfg = ["W" => $W, "horizon" => $HORIZON, "cap" => count($j["cands"]),
          "seedBase" => $seedBase + $ji * 100003,
          "pair" => "va", "candIdx" => $j["selected"]];
  try {
    $rows = SimLabel_RunForSnapshot(rtrim($j["snap_dir"], "/") . "/", $meta, $cfg);
  } catch (Throwable $e) {
    fwrite(STDERR, "snap " . $j["snap"] . " failed: " . $e->getMessage() . "\n");
    continue;
  }
  $fh = fopen($outFile, "a");
  foreach ($rows as $r) {
    $r["horizon"] = $HORIZON;
    $r["prior_pick"] = intval($j["prior_pick"]);
    $r["game"] = strval($j["game"]);
    fwrite($fh, json_encode($r) . "\n");
  }
  fclose($fh);
  fwrite(STDERR, "done " . $j["snap"] . " rows=" . count($rows) . "\n");
}
fwrite(STDERR, "MEAS-LABEL-DONE\n");
