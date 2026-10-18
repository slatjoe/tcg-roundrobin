<?php
putenv("LABEL_DRIVER=1");
include __DIR__ . "/play_game.php";
// SWAP TEST: two parent states differing ONLY in the true opp hand/deck
// split (same unseen pool, same sizes). Same assignment + seed + candidate
// through SimLabel_RunRollout must give identical trajectories.
$job = null;
foreach (file("/tmp/relabel_jobs.jsonl") as $ln) { $job = json_decode(trim($ln), true); break; }
$root = intval($job["player"]); $opp = 3 - $root;
$GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
// Build snap B: swap opp hand[0] with opp deck[0] in a copy of the snap.
$snapB = "/tmp/swap_snapB/";
SimSearch_WipeDir($snapB);
SimSearch_CopyDir(rtrim($job["snap_dir"], "/") . "/", $snapB);
$lines = explode("\r\n", file_get_contents($snapB . "gamestate.txt"));
$hIdx = $opp === 1 ? 1 : 19; $dIdx = $opp === 1 ? 2 : 20;
$hand = explode(" ", $lines[$hIdx]); $deck = explode(" ", $lines[$dIdx]);
$tmp = $hand[0]; $hand[0] = $deck[0]; $deck[0] = $tmp;
$lines[$hIdx] = implode(" ", $hand); $lines[$dIdx] = implode(" ", $deck);
file_put_contents($snapB . "gamestate.txt", implode("\r\n", $lines));
echo "snapB opp hand[0] now: " . $hand[0] . " (deck top was swapped in)\n";
// Parent: parse snap A, compute ONE assignment from the shared pool.
$snapGameDir = $GLOBALS["ssGamesRoot"] . strval($job["game"]) . "/";
SimSearch_WipeDir($snapGameDir);
SimSearch_CopyDir(rtrim($job["snap_dir"], "/") . "/", $snapGameDir);
$GLOBALS["gameName"] = strval($job["game"]); $GLOBALS["filepath"] = $snapGameDir; $GLOBALS["filename"] = $snapGameDir . "gamestate.txt"; $GLOBALS["logWriteBuffer"] = [];
if (!function_exists("ParseGamestate")) { SimSearch_IncludeWithGlobals("ParseGamestate.php"); $GLOBALS["gameName"] = strval($job["game"]); $GLOBALS["filepath"] = $snapGameDir; $GLOBALS["filename"] = $snapGameDir . "gamestate.txt"; }
ParseGamestate();
$a = SimSearch_Determinize($root, 31337);
$rootKey = strval($job["branch"]) . "|" . $root . "|" . implode(",", array_map(function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $job["cands"]));
$cfg = ["rootPlayer" => $root, "rootKey" => $rootKey, "forceIdx" => intval($job["prior_pick"]), "snapGame" => strval($job["game"]), "pair" => "va", "seed" => 4242];
$results = [];
foreach ([["A", rtrim($job["snap_dir"], "/") . "/"], ["B", $snapB]] as $arm) {
  $pid = pcntl_fork();
  if ($pid === 0) { SimLabel_RunRollout($arm[1], "/tmp/swap_res_" . $arm[0] . ".json", $a, $cfg); exit(0); }
  pcntl_waitpid($pid, $st);
  $results[$arm[0]] = json_decode(file_get_contents("/tmp/swap_res_" . $arm[0] . ".json"), true);
}
$ra = $results["A"]; $rb = $results["B"];
$cmp = ["turns" => ($ra["turns"] ?? null) === ($rb["turns"] ?? null), "hooks" => ($ra["hooks"] ?? null) === ($rb["hooks"] ?? null), "outcome" => ($ra["outcome"] ?? null) === ($rb["outcome"] ?? null), "winner" => ($ra["winner"] ?? null) === ($rb["winner"] ?? null)];
echo "A: turns=" . ($ra["turns"] ?? "?") . " hooks=" . ($ra["hooks"] ?? "?") . " outcome=" . ($ra["outcome"] ?? "?") . "\n";
echo "B: turns=" . ($rb["turns"] ?? "?") . " hooks=" . ($rb["hooks"] ?? "?") . " outcome=" . ($rb["outcome"] ?? "?") . "\n";
echo "SWAP-TEST " . (!in_array(false, $cmp, true) ? "PASS (trajectories identical)" : "FAIL " . json_encode($cmp)) . "\n";
SimSearch_WipeDir($snapGameDir); SimSearch_WipeDir($snapB);
