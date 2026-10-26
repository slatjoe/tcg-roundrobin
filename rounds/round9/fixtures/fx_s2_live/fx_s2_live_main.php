<?php
// fx_s2_live harness main: runs ONE fixture case per process
// against the REAL code/search_s2.php (stubs from stubs.php
// stand in for the vendor/featurize boundary only) and writes
// a JSON summary to $FX_OUT for check_fx_s2_live.py.
//
//   php fx_s2_live_main.php <case> <workdir>
// Cases: flip0, flip1, unpinned, pin_bad, pin_bad_k,
//        hooks_live, hooks_low, label_default, label_horizon
//
// Planted root decision (all Decide cases): root player 1,
// branch "M", two candidates -- cand 0 wins the prior
// (0.55 / 0.45); cand 0's worlds are planted "lose" (outcome
// -1) and cand 1's are planted "draw" (every world runs to
// the horizon at raw outcome 0, root BEHIND on life 8 vs 14),
// except: unpinned -> cand 1 "win"; hooks_* -> cand 1 "hooks".
$case = strval($argv[1]);
$work = rtrim(strval($argv[2]), "/");
require __DIR__ . "/stubs.php";
require getenv("FX_SEARCH") ?: (__DIR__ . "/../../code/search_s2.php");

@mkdir($work . "/Games", 0777, true);
@mkdir($work . "/log", 0777, true);
@mkdir($work . "/snaps", 0777, true);
putenv("TCG_SEARCH_LOG=" . $work . "/log");
putenv("TEACHER_SNAP_DIR=" . $work . "/snaps");

// ---- the planted snapshot / game dir -------------------------
$p1deck = []; for ($i = 1; $i <= 40; ++$i) $p1deck[] = sprintf("fx_a%02d", $i);
$p2deck = []; for ($i = 1; $i <= 40; ++$i) $p2deck[] = sprintf("fx_b%02d", $i);
$p1hand = ["fx_a41", "fx_a42", "fx_a43", "fx_a44"];
$p2hand = ["fx_b41", "fx_b42", "fx_b43", "fx_b44"];
$lines = array_fill(0, 60, "");
$lines[1] = implode(" ", $p1hand);
$lines[2] = implode(" ", $p1deck);
$lines[5] = "";
$lines[19] = implode(" ", $p2hand);
$lines[20] = implode(" ", $p2deck);
$lines[23] = "";
$gameDir = $work . "/gamedir";
@mkdir($gameDir, 0777, true);
file_put_contents($gameDir . "/gamestate.txt", implode("\r\n", $lines));
file_put_contents($gameDir . "/p1Deck.txt",
  implode(" ", array_merge($p1deck, $p1hand)));
file_put_contents($gameDir . "/p2Deck.txt",
  implode(" ", array_merge($p2deck, $p2hand)));

// ---- parent-process state (the parsed root state) ------------
$GLOBALS["p1Hand"] = $p1hand; $GLOBALS["p1Deck"] = $p1deck;
$GLOBALS["p1Arsenal"] = [];
$GLOBALS["p2Hand"] = $p2hand; $GLOBALS["p2Deck"] = $p2deck;
$GLOBALS["p2Arsenal"] = [];
$GLOBALS["currentTurn"] = 40; $GLOBALS["currentPlayer"] = 1;
$GLOBALS["playerHealths"] = [20, 20]; $GLOBALS["winner"] = 0;
$GLOBALS["gameName"] = "fxgame";
$GLOBALS["filepath"] = $gameDir . "/";
$GLOBALS["filename"] = $gameDir . "/gamestate.txt";
$GLOBALS["ssGamesRoot"] = $work . "/Games/";
$GLOBALS["fxStartTurn"] = 40;
$GLOBALS["fxHealth"] = [8, 14]; // root (p1) BEHIND on life
$GLOBALS["fxRootBranch"] = "M";
$GLOBALS["fxRootCands"] = [0, 1];
$candRecs = [["card_id" => "fxA", "zone" => "hand"],
             ["card_id" => "fxB", "zone" => "hand"]];
$GLOBALS["fxRootCandRecs"] = $candRecs;
$GLOBALS["fxBehavior"] = [0 => "lose", 1 => "draw"];

// ---- fake policy server --------------------------------------
$sock = $work . "/fx.sock";
$GLOBALS["fxSockPath"] = $sock;
$priors = ($case === "label_default" || $case === "label_horizon")
  ? [0.55, 0.45, 0.30] : [0.55, 0.45];
$srv = proc_open(
  [PHP_BINARY, __DIR__ . "/fx_server.php", $sock, json_encode($priors)],
  [["pipe", "r"], ["file", $work . "/server.log", "a"],
   ["file", $work . "/server.log", "a"]], $pipes);
for ($i = 0; $i < 100 && !file_exists($sock . ".ready"); ++$i) usleep(50000);
if (!file_exists($sock . ".ready")) {
  fwrite(STDERR, "fx server did not start\n"); exit(1);
}

$TUPLE = ["name" => "FX", "hooks" => 8000, "deadline_s" => 180,
          "horizon" => 62, "horizon_value" => -1.0, "k" => 25,
          "margin" => 1.5];
$out = ["case" => $case];

if (strpos($case, "label_") === 0) {
  // -------- label-path cases (SimLabel_RunForSnapshot) --------
  // The stub engine's rooted hook call must present the SAME
  // candidate records the label parent builds its root key
  // from (meta["cands"] below).
  $labelCands = [["card_id" => "fxA", "zone" => "hand"],
                 ["card_id" => "fxB", "zone" => "hand"],
                 ["card_id" => "fxC", "zone" => "hand"]];
  $GLOBALS["fxRootCands"] = [0, 1, 2];
  $GLOBALS["fxRootCandRecs"] = $labelCands;
  if ($case === "label_default") {
    $GLOBALS["fxBehavior"] = [0 => "lose", 1 => "draw", 2 => "hooks"];
    $cfg = ["W" => 3, "cap" => 3, "seedBase" => 777001,
            "pair" => "va", "candIdx" => [0, 1, 2]];
    // NO horizon / hookBudget / deadlineS keys: the registered
    // label instrument defaults must govern (horizon off,
    // 4,000 hooks, 300 s), by the build's own cfg fallbacks.
  } else {
    $GLOBALS["fxBehavior"] = [0 => "lose", 1 => "draw"];
    $cfg = ["W" => 3, "cap" => 2, "seedBase" => 777001,
            "pair" => "va", "candIdx" => [0, 1],
            "horizon" => 62, "hookBudget" => 8000,
            "deadlineS" => 180];
  }
  $meta = ["snap" => "fxsnap", "game" => "fxgame", "player" => 1,
           "branch" => "M",
           "cands" => $labelCands];
  $rows = SimLabel_RunForSnapshot($gameDir . "/", $meta, $cfg);
  $out["label_rows"] = $rows;
} else {
  // -------- live Decide cases ---------------------------------
  switch ($case) {
    case "flip0":
      $t = $TUPLE; $t["horizon_value"] = 0.0; $t["name"] = "FX-HV0";
      putenv("TEACHER_TUPLE_JSON=" . json_encode($t)); break;
    case "flip1":
      $t = $TUPLE; $t["name"] = "FX-HVm1";
      putenv("TEACHER_TUPLE_JSON=" . json_encode($t)); break;
    case "unpinned":
      $GLOBALS["fxBehavior"] = [0 => "lose", 1 => "win"];
      putenv("TEACHER_TUPLE_JSON"); break;
    case "pin_bad":
      putenv("TEACHER_TUPLE_JSON=" . json_encode(
        ["name" => "FX", "hooks" => 8000])); break;
    case "pin_bad_k":
      $t = $TUPLE; $t["k"] = 10;
      putenv("TEACHER_TUPLE_JSON=" . json_encode($t)); break;
    case "hooks_live":
      $GLOBALS["fxBehavior"] = [0 => "lose", 1 => "hooks"];
      putenv("TEACHER_TUPLE_JSON=" . json_encode($TUPLE)); break;
    case "hooks_low":
      $GLOBALS["fxBehavior"] = [0 => "lose", 1 => "hooks"];
      $t = $TUPLE; $t["hooks"] = 4000; $t["name"] = "FX-H4K";
      putenv("TEACHER_TUPLE_JSON=" . json_encode($t)); break;
    default:
      fwrite(STDERR, "unknown case $case\n"); exit(1);
  }
  $pick = SimTeacher_Decide("M", [0, 1], $candRecs, 1, $gameDir,
                            ["fx" => "root"]);
  $out["pick"] = $pick;
  $out["abort_reason"] = $GLOBALS["ssTeacherAbortReason"] ?? null;
  $statFile = $work . "/log/search_stats.jsonl";
  $rows = [];
  if (file_exists($statFile)) {
    foreach (file($statFile) as $ln) {
      $r = json_decode(trim($ln), true);
      if (is_array($r)) $rows[] = $r;
    }
  }
  $out["stat_rows"] = $rows;
  $idx = $work . "/snaps/teacher_snap_index.jsonl";
  $out["snap_index"] = file_exists($idx)
    ? array_values(array_filter(array_map(
        function ($l) { return json_decode(trim($l), true); },
        file($idx)))) : [];
}
file_put_contents(getenv("FX_OUT") ?: ($work . "/out.json"),
                  json_encode($out, JSON_PRETTY_PRINT));
proc_terminate($srv);
echo "FXCASE $case done\n";
