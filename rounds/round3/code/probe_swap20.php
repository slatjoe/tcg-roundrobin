<?php
// L2 swap-invariance runner (Claude's L2, reply to 94b9449): the
// determinization-era probe_swap.php, parameterized. Core test is
// byte-faithful to the original: two parent states differing ONLY in
// the true opp hand/deck split (same unseen pool, same sizes); the
// SAME assignment (seed 31337) + seed (4242) + candidate through
// SimLabel_RunRollout must give identical trajectories.
// Changes vs the original: jobs file + job index from argv, per-job
// temp dirs, runs BOTH picks (prior_pick and teacher_pick), verdict
// appended as one JSON line per (job, pick) to the out file.
// Usage: SWAP_JOBS=<jobs.jsonl> SWAP_IDX=<n> SWAP_OUT=<out.jsonl> php probe_swap20.php
$jobsFile = getenv("SWAP_JOBS"); $idx = intval(getenv("SWAP_IDX")); $outFile = getenv("SWAP_OUT");
putenv("LABEL_DRIVER=1");
// play_game.php loads the search bootstrap only when argv mimics the
// label driver (deck deck --policy-search); give it that argv shape
// and take this runner's own parameters from the environment.
$deck = __DIR__ . "/decks/nats2026_ashlyn_fai_60.txt";
$argv = ["probe_swap20.php", $deck, $deck, "--policy-search", "--games", "1"];
$argc = count($argv);
$GLOBALS["argv"] = $argv; $GLOBALS["argc"] = $argc;
include __DIR__ . "/play_game.php";
$job = null; $i = 0;
foreach (file($jobsFile) as $ln) { if ($i === $idx) { $job = json_decode(trim($ln), true); break; } $i++; }
if ($job === null) { fwrite(STDERR, "no job at idx $idx\n"); exit(2); }
$root = intval($job["player"]); $opp = 3 - $root;
$GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
$tag = "j" . $idx . "_" . strval($job["snap"]);
foreach ([["prior", intval($job["prior_pick"])], ["teacher", intval($job["teacher_pick"])]] as $pickSpec) {
  $pickRole = $pickSpec[0]; $forceIdx = $pickSpec[1];
  $work = "/tmp/swap20/" . $tag . "_" . $pickRole . "/";
  // Build snap B: swap opp hand[0] with opp deck[0] in a copy of the snap.
  $snapB = $work . "snapB/";
  SimSearch_WipeDir($snapB);
  SimSearch_CopyDir(rtrim($job["snap_dir"], "/") . "/", $snapB);
  $lines = explode("\r\n", file_get_contents($snapB . "gamestate.txt"));
  $hIdx = $opp === 1 ? 1 : 19; $dIdx = $opp === 1 ? 2 : 20;
  $hand = explode(" ", $lines[$hIdx]); $deck = explode(" ", $lines[$dIdx]);
  $tmp = $hand[0]; $hand[0] = $deck[0]; $deck[0] = $tmp;
  $lines[$hIdx] = implode(" ", $hand); $lines[$dIdx] = implode(" ", $deck);
  file_put_contents($snapB . "gamestate.txt", implode("\r\n", $lines));
  // Parent: parse snap A, compute ONE assignment from the shared pool.
  $snapGameDir = $GLOBALS["ssGamesRoot"] . strval($job["game"]) . "/";
  SimSearch_WipeDir($snapGameDir);
  SimSearch_CopyDir(rtrim($job["snap_dir"], "/") . "/", $snapGameDir);
  $GLOBALS["gameName"] = strval($job["game"]); $GLOBALS["filepath"] = $snapGameDir; $GLOBALS["filename"] = $snapGameDir . "gamestate.txt"; $GLOBALS["logWriteBuffer"] = [];
  // ParseGamestate reads the SHMOP cache BEFORE the file; the fleet's
  // KEEP_GAME segments would silently replace the snapshot state (the
  // exact hazard SimLabel_RunForSnapshot guards against). Clear first.
  if (function_exists("DeleteCache")) DeleteCache(strval($job["game"]));
  if (!function_exists("ParseGamestate")) { SimSearch_IncludeWithGlobals("ParseGamestate.php"); $GLOBALS["gameName"] = strval($job["game"]); $GLOBALS["filepath"] = $snapGameDir; $GLOBALS["filename"] = $snapGameDir . "gamestate.txt"; }
  ParseGamestate();
  $a = SimSearch_Determinize($root, 31337);
  $rootKey = strval($job["branch"]) . "|" . $root . "|" . implode(",", array_map(function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $job["cands"]));
  $cfg = ["rootPlayer" => $root, "rootKey" => $rootKey, "forceIdx" => $forceIdx, "snapGame" => strval($job["game"]), "pair" => "va", "seed" => 4242];
  $results = [];
  foreach ([["A", rtrim($job["snap_dir"], "/") . "/"], ["B", $snapB]] as $arm) {
    $resFile = $work . "res_" . $arm[0] . ".json";
    $pid = pcntl_fork();
    if ($pid === 0) { SimLabel_RunRollout($arm[1], $resFile, $a, $cfg); exit(0); }
    pcntl_waitpid($pid, $st);
    $results[$arm[0]] = json_decode(file_get_contents($resFile), true);
  }
  $ra = $results["A"]; $rb = $results["B"];
  $cmp = ["turns" => ($ra["turns"] ?? null) === ($rb["turns"] ?? null), "hooks" => ($ra["hooks"] ?? null) === ($rb["hooks"] ?? null), "outcome" => ($ra["outcome"] ?? null) === ($rb["outcome"] ?? null), "winner" => ($ra["winner"] ?? null) === ($rb["winner"] ?? null)];
  // An errored or empty arm is a FAIL, never a vacuous pass: both arms
  // must carry a real rollout result (the smoke caught null==null).
  $real = !isset($ra["error"]) && !isset($rb["error"]) && ($ra["outcome"] ?? null) !== null && ($rb["outcome"] ?? null) !== null && ($ra["turns"] ?? null) !== null;
  $pass = $real && !in_array(false, $cmp, true);
  $verdict = ["snap" => strval($job["snap"]), "game" => strval($job["game"]), "player" => $root, "branch" => strval($job["branch"]), "pick_role" => $pickRole, "forceIdx" => $forceIdx, "pass" => $pass, "cmp" => $cmp, "A" => ["turns" => $ra["turns"] ?? null, "outcome" => $ra["outcome"] ?? null, "winner" => $ra["winner"] ?? null, "error" => $ra["error"] ?? null], "B" => ["turns" => $rb["turns"] ?? null, "outcome" => $rb["outcome"] ?? null, "winner" => $rb["winner"] ?? null, "error" => $rb["error"] ?? null], "swapped" => [$hand[0], $deck[0]]];
  file_put_contents($outFile, json_encode($verdict) . "\n", FILE_APPEND);
  echo $tag . " " . $pickRole . ": " . ($pass ? "PASS" : "FAIL " . json_encode($cmp)) . "\n";
  SimSearch_WipeDir($snapGameDir); SimSearch_WipeDir($work);
}
