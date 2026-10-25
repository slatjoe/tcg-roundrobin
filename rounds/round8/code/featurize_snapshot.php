<?php
// featurize_snapshot.php - featurize registered snapshots through
// THIS tree's featurize.php (round 8). Deployed at a tree root; the
// tree it sits in decides which featurizer build answers - the
// native tree (f81193e0...) or the corrected tree (3dcf32c9...).
// Used by: the package's featurization smoke, the pilot's
// teacher-root census (in a census-probe tree), the T1 data builder
// (dual featurization of every corpus state), and the swap test.
//
// Batch shape, modeled on snap_relabel_main.php: argv mimics the
// label driver so play_game.php loads the search bootstrap and
// returns under LABEL_DRIVER. Jobs come from env FEAT_JOBS (jsonl),
// one output row per job to env FEAT_OUT (jsonl):
//   job: {snap_dir, snap, game, player, branch, cands}
//   out: {snap, game, player, branch, state, canary: true}
//        or {snap, ..., error: "..."} (canary throw included)
//
// The snapshot load mirrors SimLabel_RunForSnapshot's own sequence
// (search.php): copy into Games/<game>/, DeleteCache BEFORE
// ParseGamestate (ParseGamestate reads the SHMOP cache before the
// file; a stale segment would silently replace the snapshot), parse,
// then SimFeat_BuildState + SimFeat_Canary on the parsed state.
$jobsFile = getenv("FEAT_JOBS"); $outFile = getenv("FEAT_OUT");
putenv("LABEL_DRIVER=1");
include "play_game.php"; // loads vendor + search.php, returns under LABEL_DRIVER
$jobs = [];
foreach (file($jobsFile) as $ln) {
  $ln = trim($ln); if ($ln === "") continue;
  $j = json_decode($ln, true); if (is_array($j)) $jobs[] = $j;
}
fwrite(STDERR, "featurize jobs=" . count($jobs) . "\n");
$fh = fopen($outFile, "w");
foreach ($jobs as $j) {
  $snap = strval($j["snap"]); $game = strval($j["game"]);
  $player = intval($j["player"]); $branch = strval($j["branch"]);
  $row = ["snap" => $snap, "game" => $game,
          "player" => $player, "branch" => $branch];
  try {
    $GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
    $snapGameDir = $GLOBALS["ssGamesRoot"] . $game . "/";
    SimSearch_WipeDir($snapGameDir);
    SimSearch_CopyDir(rtrim($j["snap_dir"], "/") . "/", $snapGameDir);
    $GLOBALS["gameName"] = $game;
    $GLOBALS["filepath"] = $snapGameDir;
    $GLOBALS["filename"] = $snapGameDir . "gamestate.txt";
    $GLOBALS["logWriteBuffer"] = [];
    if (function_exists("DeleteCache")) DeleteCache($game);
    if (!function_exists("ParseGamestate")) {
      SimSearch_IncludeWithGlobals("ParseGamestate.php");
      $GLOBALS["gameName"] = $game;
      $GLOBALS["filepath"] = $snapGameDir;
      $GLOBALS["filename"] = $snapGameDir . "gamestate.txt";
    }
    ParseGamestate();
    $st = SimFeat_BuildState($player, $branch, $j["cands"]);
    SimFeat_Canary($player, $st);
    $row["state"] = $st;
    $row["canary"] = true;
  } catch (Throwable $e) {
    $row["error"] = $e->getMessage();
  }
  fwrite($fh, json_encode($row) . "\n");
}
fclose($fh);
fwrite(STDERR, "FEATURIZE-DONE\n");
