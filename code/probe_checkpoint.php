<?php
putenv("LABEL_DRIVER=1");
include __DIR__ . "/play_game.php";
// CHECKPOINT ROUND-TRIP PROBE (ghost-failure mechanism hunt,
// 2026-10-18): RootDecide checkpoints the live state at every root
// decision with DoGamestateUpdate() + WriteGamestate.php, in the
// parent, so children can re-parse it. The engine re-derives its
// working state from that same serialization at the next step. If
// parse -> update -> write is NOT idempotent on a real decision
// state, every checkpoint drifts the live game. Fixtures: teacher
// snaps (already checkpoint-written decision states). For each:
// parse, snapshot the file bytes, run the checkpoint calls exactly
// as RootDecide does, snapshot again, diff.
$GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
$snaps = [];
foreach (glob("/tmp/meas_c0a/teacher_snaps/*_t*", GLOB_ONLYDIR) as $d) {
  $snaps[] = $d;
  if (count($snaps) >= 8) break;
}
foreach ($snaps as $snapDir) {
  $meta = json_decode(file_get_contents($snapDir . "/meta.json"), true);
  $game = strval($meta["game"] ?? basename($snapDir));
  $scratch = $GLOBALS["ssGamesRoot"] . "999000111/";
  SimSearch_WipeDir($scratch);
  SimSearch_CopyDir(rtrim($snapDir, "/") . "/", $scratch);
  $GLOBALS["gameName"] = "999000111";
  $GLOBALS["filepath"] = $scratch;
  $GLOBALS["filename"] = $scratch . "gamestate.txt";
  $GLOBALS["logWriteBuffer"] = [];
  if (function_exists("DeleteCache")) DeleteCache("999000111");
  if (!function_exists("ParseGamestate")) {
    SimSearch_IncludeWithGlobals("ParseGamestate.php");
    $GLOBALS["gameName"] = "999000111";
    $GLOBALS["filepath"] = $scratch;
    $GLOBALS["filename"] = $scratch . "gamestate.txt";
  }
  ParseGamestate();
  $before = file_get_contents($scratch . "gamestate.txt");
  // The exact RootDecide checkpoint calls:
  DoGamestateUpdate();
  $GLOBALS["skipWriteGamestate"] = false;
  SimSearch_IncludeWithGlobals("WriteGamestate.php");
  $after = file_get_contents($scratch . "gamestate.txt");
  if ($before === $after) {
    echo basename($snapDir) . ": IDENTICAL\n";
  } else {
    $bl = explode("\r\n", $before); $al = explode("\r\n", $after);
    $diffs = [];
    $n = max(count($bl), count($al));
    for ($i = 0; $i < $n; $i++) {
      $x = $bl[$i] ?? "<missing>"; $y = $al[$i] ?? "<missing>";
      if ($x !== $y) $diffs[] = $i;
    }
    echo basename($snapDir) . ": DIFFERS at lines " . implode(",", array_slice($diffs, 0, 8))
      . " (" . count($diffs) . " lines)\n";
    foreach (array_slice($diffs, 0, 3) as $i) {
      echo "  line $i BEFORE: " . substr($bl[$i] ?? "", 0, 150) . "\n";
      echo "  line $i AFTER:  " . substr($al[$i] ?? "", 0, 150) . "\n";
    }
  }
  SimSearch_WipeDir($scratch);
}
echo "CHECKPOINT-PROBE-DONE\n";
