<?php
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
$jobs = [];
foreach (file($jobsFile) as $ln) {
  $ln = trim($ln); if ($ln === "") continue;
  $j = json_decode($ln, true); if (is_array($j)) $jobs[] = $j;
}
fwrite(STDERR, "meas jobs=" . count($jobs) . " W=$W\n");
foreach ($jobs as $ji => $j) {
  $meta = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]), "branch" => strval($j["branch"]),
           "cands" => $j["cands"]];
  $cfg = ["W" => $W, "cap" => count($j["cands"]),
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
    $r["prior_pick"] = intval($j["prior_pick"]);
    $r["game"] = strval($j["game"]);
    fwrite($fh, json_encode($r) . "\n");
  }
  fclose($fh);
  fwrite(STDERR, "done " . $j["snap"] . " rows=" . count($rows) . "\n");
}
fwrite(STDERR, "MEAS-LABEL-DONE\n");
