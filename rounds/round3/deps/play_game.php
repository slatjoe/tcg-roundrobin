<?php
// play_game.php — headless bot-vs-bot game(s) on the Talishar engine (LOCAL ONLY).
//
// Usage:
//   php play_game.php <p1Deck.txt> <p2Deck.txt> [--games N] [--first-player 1|2] [--seed S]
//
// Both players run the built-in EncounterAI heuristic. No web server, no DB,
// no network. Game state lives in ./Games/<id>/ under the Talishar root and is
// deleted after each game.

error_reporting(E_ALL & ~E_DEPRECATED & ~E_WARNING);
ini_set('display_errors', '0');

// tcg-sim: disable EncounterAI's blind-pass tail (it skips whole turns when the
// 31-iteration budget is exhausted mid-combat). The harness drive loop + stuck
// guard below provides the stall safety instead, and turns are never skipped.
putenv('TCG_NO_BLIND_PASS=1');
// tcg-sim: keep the full per-game log (engine trims gamelog.txt to 500 lines
// at every turn end via ClearLog() — we parse the full log for analysis).
putenv('TCG_KEEP_FULL_LOG=1');

$TALISHAR = __DIR__ . '/vendor/talishar';

// Parse CLI args BEFORE chdir (engine uses relative ./Games/ paths).
// Usage: php play_game.php <p1Deck.txt> <p2Deck.txt> [--games N] [--first-player 1|2]
$rawArgs = array_slice($argv, 1);
$p1DeckPath = $p2DeckPath = null;
$games = 1;
$cliFirstPlayer = 0;
$policy = "v1";
$logDir = null;
for ($i = 0; $i < count($rawArgs); ++$i) {
  $a = $rawArgs[$i];
  if ($a === "--games" && isset($rawArgs[$i + 1])) { $games = max(1, intval($rawArgs[++$i])); }
  else if ($a === "--first-player" && isset($rawArgs[$i + 1])) { $cliFirstPlayer = intval($rawArgs[++$i]); }
  else if ($a === "--policy" && isset($rawArgs[$i + 1])) { $policy = $rawArgs[++$i]; }
  else if ($a === "--log-dir" && isset($rawArgs[$i + 1])) { $logDir = $rawArgs[++$i]; }
  else if ($a === "--mcts-player" && isset($rawArgs[$i + 1])) { $mctsPlayer = intval($rawArgs[++$i]); }
  else if ($a === "--seed" && isset($rawArgs[++$i])) { $fixedSeed = intval($rawArgs[$i]); }
  else if ($a === "--policy-server") { $policyServer = true; }
  else if ($a === "--policy-search") { $policySearch = true; }
  else if ($p1DeckPath === null) $p1DeckPath = $a;
  else if ($p2DeckPath === null) $p2DeckPath = $a;
}
if ($p1DeckPath === null || $p2DeckPath === null) {
  fwrite(STDERR, "usage: php play_game.php <p1Deck.txt> <p2Deck.txt> [--games N] [--first-player 1|2]\n");
  exit(1);
}
$p1DeckPath = realpath($p1DeckPath) ?: $p1DeckPath;
$p2DeckPath = realpath($p2DeckPath) ?: $p2DeckPath;

chdir($TALISHAR);

// ---------------------------------------------------------------- bootstrap
// Stubs for web/DB dependencies (mirrors tests/bootstrap.php approach).
if (!function_exists('LoadSavedSettings')) {
  function LoadSavedSettings($playerId) { return []; }
}
if (!function_exists('GetDBConnection')) {
  function GetDBConnection($logKey = 0) { return null; }
}
if (!function_exists('GetLocalMySQLConnection')) {
  function GetLocalMySQLConnection() { return null; }
}
// Rust-counter accrual bookkeeping (includes/functions.inc.php). No-ops without
// a state file, which never exists for headless sims. Stubbed to avoid pulling
// in the DB-adjacent include chain.
if (!function_exists('AddRustCountersAfterTurnZero')) {
  function AddRustCountersAfterTurnZero() { return false; }
}

// Engine bootstrap — same file list as Libraries/PuzzleEngine.php.
include_once "WriteLog.php";
include_once "GameLogic.php";
include_once "GameTerms.php";
include_once "Libraries/SHMOPLibraries.php";
include_once "Libraries/StatFunctions.php";
include_once "Libraries/UILibraries.php";
include_once "Libraries/PlayerSettings.php";
include_once "Libraries/NetworkingLibraries.php";
include_once "Libraries/CacheLibraries.php";
include_once "AI/CombatDummy.php";
include_once "Libraries/HTTPLibraries.php";
include_once "Libraries/ReplayLibraries.php";
require_once "Libraries/CoreLibraries.php";
include_once "Libraries/PuzzleVerify.php";
include_once "MenuFiles/StartHelper.php";

// Heuristic policy v1 (deck-aware). Loaded unless --policy=stock.
// Takes over BotPriority() via the hook in AI/BotLogic.php.
// Phase A: PHP/Python policy bridge. Routes candidate-choice decisions
// (EncounterAI branches + decision queue) through a persistent Python
// inference server over a unix socket. v1 scores are still computed
// in-process by the real SimV1_Priority path; Python returns argmax, so
// decisions are bit-identical to --policy=v1. See policy_server.php.
if (!empty($policyServer)) {
  // The bridge needs v1's scoring (candidates arrive pre-scored by the real
  // SimV1_Priority path; Python returns argmax).
  include_once __DIR__ . "/policy_v1.php";
  include_once __DIR__ . "/featurize.php";
  include_once __DIR__ . "/policy_server.php";
  putenv("SIM_POLICY_SERVER=1");
  fwrite(STDERR, "policy: server (v1-equivalent via " . SimPolicyServer_SockPath() . ")\n");
} else if ($policy !== "stock") {
  include_once __DIR__ . "/policy_v1.php";
  fwrite(STDERR, "policy: v1 (deck-aware)\n");
} else {
  fwrite(STDERR, "policy: stock\n");
}
// ISMCTS decision layer: like --policy-server, but learner branch
// decisions with a real choice are searched (see search.php / DESIGN.md).
if (!empty($policySearch)) {
  include_once __DIR__ . "/policy_v1.php";
  include_once __DIR__ . "/featurize.php";
  include_once __DIR__ . "/policy_server.php";
  include_once __DIR__ . "/search.php";
  putenv("SIM_POLICY_SERVER=1");
  $GLOBALS["simSearchEnabled"] = true;
  $GLOBALS["simSearchSeat"] = intval(getenv("TCG_LEARNER_SEAT") ?: 1);
  fwrite(STDERR, "policy: search (seat " . $GLOBALS["simSearchSeat"] . " via " . SimPolicyServer_SockPath() . ")\n");
}
// MCTS decision layer (Phase 3B): sits above v1, searches M-phase candidate
// plays via forked rollouts. Enabled with --policy=mcts.
if ($policy === "mcts") {
  include_once __DIR__ . "/mcts.php";
  putenv("SIM_MCTS=1");
  // Which seat uses MCTS (0 = both). The other seat plays v1 heuristic.
  putenv("SIM_MCTS_PLAYER=" . (isset($mctsPlayer) ? $mctsPlayer : 0));
  fwrite(STDERR, "mcts: enabled (player " . (isset($mctsPlayer) ? $mctsPlayer : "both") . ")\n");
}

// Event logging (Phase 4): JSONL-grade per-game logs when --log-dir is set.
if ($logDir !== null) {
  if (!is_dir($logDir)) mkdir($logDir, 0700, true);
  $GLOBALS["simLogDir"] = $logDir;
  include_once __DIR__ . "/log_game.php";
  fwrite(STDERR, "logging to: $logDir\n");
}

// Engine scripts (ParseGamestate.php, WriteGamestate.php) execute at top level
// and expect globals in scope. When including from inside a function we must
// import $GLOBALS into that same scope first — mirrors PuzzleIncludeGlobal().
function IncludeWithGlobals($__file) {
  foreach (array_keys($GLOBALS) as $__name) {
    if ($__name !== "GLOBALS" && $__name !== "__file" && $__name !== "__name") global $$__name;
  }
  include $__file;
}

// ---------------------------------------------------------------- game setup
// Replicates the gamestate construction in Start.php (minus HTTP/session/DB).
function SetupGame($p1DeckFile, $p2DeckFile, $firstPlayer) {
  global $gameName, $filepath, $filename, $p1IsAI, $p2IsAI;
  global $p1id, $p2id, $p1IsPatron, $p2IsPatron;

  $gameName = (string)random_int(100000000, 999999999);
  $gameDir = "./Games/$gameName/";
  if (!mkdir($gameDir, 0700, true)) return null;
  copy($p1DeckFile, $gameDir . "p1Deck.txt");
  copy($p2DeckFile, $gameDir . "p2Deck.txt");
  file_put_contents($gameDir . "gamelog.txt", "");
  // Minimal GameFile.txt (ParseGamefile not used by our flow, but harmless).
  file_put_contents($gameDir . "GameFile.txt",
    "1\r\n2\r\n5\r\n" . FormatName(0) . "\r\nprivate\r\n\r\n$firstPlayer\r\n");

  $p1id = $p2id = "";
  $p1IsPatron = $p2IsPatron = "0";
  $p1Inventory = [];
  $p2Inventory = [];

  $memHandle = fopen("php://memory", "w+");
  fwrite($memHandle, "20 20\r\n"); // player life totals (overwritten by StartEffects)
  $h1 = fopen($gameDir . "p1Deck.txt", "r");
  initializePlayerState($memHandle, $h1, 1);
  fclose($h1);
  $h2 = fopen($gameDir . "p2Deck.txt", "r");
  initializePlayerState($memHandle, $h2, 2);
  fclose($h2);
  $p1Key = bin2hex(random_bytes(8));
  $p2Key = bin2hex(random_bytes(8));
  $p1IsAI = "1";
  $p2IsAI = "1";
  fwrite($memHandle,
    "\r\n" . // Landmarks
    "0\r\n" . // Game winner (0 = none)
    "$firstPlayer\r\n" . // First Player
    "1\r\n" . // Current Player
    "0\r\n" . // Current Turn
    "M 1\r\n" . // Phase
    "1\r\n" . // Action points
    "\r\n" . // Combat Chain
    "0 0 0 0 0 0 0 GY NA 0 0 0 0 0 0 0 NA 0 0 -1 -1 NA 0 0 0 -1 0 0 0 0 - 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -1 0 0 0 0 0 0\r\n" .
    "\r\n" . // Current Turn Effects
    "\r\n" . // Current Turn Effects From Combat
    "\r\n" . // Next Turn Effects
    "\r\n" . // Decision Queue
    "0\r\n" . // Decision Queue Variables
    "0 - - -\r\n" . // Decision Queue State
    "\r\n" . // Layers
    "\r\n" . // Layer Priority
    "1\r\n" . // What player's turn it is
    "\r\n" . // Last Played Card
    "0\r\n" . // Number of prior chain links this turn
    "\r\n" . // Chain Link Summaries
    "$p1Key\r\n" . // Player 1 auth key
    "$p2Key\r\n" . // Player 2 auth key
    "0\r\n" . // Permanent unique ID counter
    "0\r\n" . // Game status: 0 = START
    "\r\n" . // Animations
    "0\r\n" . // Current Player activity status
    "0\r\n" . // Player1 Rating
    "0\r\n" . // Player2 Rating
    "0\r\n" . // Player 1 total time
    "0\r\n" . // Player 2 total time
    time() . "\r\n" . // Last update time
    "\r\n" . // Reserved
    "\r\n" . // Events
    "-\r\n" . // Effect Context
    implode(" ", $p1Inventory) . "\r\n" .
    implode(" ", $p2Inventory) . "\r\n" .
    "$p1IsAI\r\n" .
    "$p2IsAI\r\n"
  );
  rewind($memHandle);
  $gamestate = stream_get_contents($memHandle);
  fclose($memHandle);
  file_put_contents($gameDir . "gamestate.txt", $gamestate);

  $GLOBALS["gameName"] = $gameName;
  $GLOBALS["filepath"] = $gameDir;
  $GLOBALS["filename"] = $gameDir . "gamestate.txt";
  $GLOBALS["lastWrittenGamestate"] = $gamestate;

  // Parse into globals, then run start-of-game effects (health, first player,
  // opening draws). Replicates the safe parts of StartEffects.php.
  // ParseGamestate.php defines functions at top level, so it can only be
  // included once per process; on later games call the parser directly.
  if (!function_exists("ParseGamestate")) {
    IncludeWithGlobals("ParseGamestate.php");
  } else {
    $GLOBALS["filename"] = $gameDir . "gamestate.txt";
    $GLOBALS["filepath"] = $gameDir;
    ParseGamestate();
  }
  StartGameEffects($firstPlayer);
  // Persist the post-setup state so the drive loop's first ParseGamestate is valid.
  $GLOBALS["skipWriteGamestate"] = false;
  DoGamestateUpdate();
  IncludeWithGlobals("WriteGamestate.php");
  return $gameName;
}

// Minimal start-of-game: character health, turn pointers, opening draws.
// (Character-specific start abilities like Fai's Phoenix Flame tutor are
// engine-defined; we invoke the same helper StartEffects.php uses.)
function StartGameEffects($firstPlayer) {
  global $mainPlayer, $currentPlayer, $otherPlayer;
  $p1Char = &GetPlayerCharacter(1);
  $p2Char = &GetPlayerCharacter(2);
  $p1H = &GetHealth(1);
  $p2H = &GetHealth(2);
  $p1H = CharacterHealth($p1Char[0]);
  $p2H = CharacterHealth($p2Char[0]);
  $mainPlayer = $firstPlayer;
  $currentPlayer = $firstPlayer;
  $otherPlayer = 3 - $firstPlayer;
  // Fai start ability (mirrors handleCharacterStartAbilities in StartEffects.php).
  foreach ([1, 2] as $p) {
    $ch = &GetPlayerCharacter($p);
    if ($ch[0] === "fai_rising_rebellion" || $ch[0] === "fai") {
      $cards = SearchDeckForCard($p, "phoenix_flame_red");
      if ($cards != "") {
        AddDecisionQueue("MAYCHOOSEDECK", $p, $cards);
        AddDecisionQueue("ADDDISCARD", $p, "DECK", 1);
      }
      unset($ch);
    }
  }
  GameSetup();
  ProcessDecisionQueue();
  // Opening hands / first turn begin here; drive loop takes it from here.
}

function GameSetup() {
  global $mainPlayer;
  AddDecisionQueue("SHUFFLEDECK", 1, "SKIPSEED");
  AddDecisionQueue("SHUFFLEDECK", 2, "SKIPSEED");
  AddDecisionQueue("DRAWTOINTELLECT", 1, "-");
  AddDecisionQueue("DRAWTOINTELLECT", 2, "-");
  AddDecisionQueue("STARTGAME", $mainPlayer, "-");
  AddDecisionQueue("STARTTURNABILITIES", $mainPlayer, "-");
}

// ---------------------------------------------------------------- drive loop
// Monotonic-field-stripped hash of the serialized gamestate, for the
// no-progress guard. WriteGamestate.php serializes fields that change every
// write even when nothing happens in-game (per-turn stat blocks, turn
// counter, per-turn life history, turn counts, accumulated clocks, last
// update time), so a raw md5 never repeats and the guard can't trip. We
// blank those lines before hashing; everything else (health, zones, combat
// chain, effects, decision queue, card/card-turn logs) still distinguishes
// genuinely different positions.
function SimStateHash($gamestate, $p1Key) {
  $lines = explode("\r\n", (string)$gamestate);
  // Head indices (fixed order in WriteGamestate.php, before chain links):
  // 15/33 = per-player per-turn stat blocks (LogEndTurnStats appends each
  // turn end), 41 = turn counter.
  foreach ([15, 33, 41] as $i) { if (isset($lines[$i])) $lines[$i] = ""; }
  // Tail indices, relative to the p1Key line (fixed order after the variable
  // chain-link lines): +8/+9 = player total times, +10 = last update time,
  // +22/+23 = per-turn life history, +27/+28 = per-player turn counts.
  $k = array_search((string)$p1Key, $lines, true);
  if ($k !== false) {
    foreach ([$k + 8, $k + 9, $k + 10, $k + 22, $k + 23, $k + 27, $k + 28] as $i) {
      if (isset($lines[$i])) $lines[$i] = "";
    }
  }
  return md5(implode("\r\n", $lines));
}

// Mirrors PuzzleDriveBots(): step via PuzzleBeginStep/PuzzleFinishStep (which
// runs EncounterAI for the current AI player) until the game ends.
function PlayOneGame($p1DeckFile, $p2DeckFile, $firstPlayer) {
  $gameName = SetupGame($p1DeckFile, $p2DeckFile, $firstPlayer);
  if ($gameName === null) return ["error" => "setup failed"];
  $gameDir = "./Games/$gameName/";
  if ($GLOBALS["simLogDir"] ?? null) {
    $GLOBALS["simFirstPlayer"] = $firstPlayer;
    SimLog_Begin($gameName);
  }
  $maxSteps = intval(getenv("TCG_MAX_STEPS") ?: 30000);
  $maxTurns = intval(getenv("TCG_MAX_TURNS") ?: 750); // pass-forever games (e.g. gravy:gravy mirrors) never end
  $steps = 0;      // otherwise; cap turns and call it a draw.
  // The turn counter can jump several turns inside one PuzzleFinishStep, so
  // trigger the cap a margin early to keep the final turn count <= $maxTurns.
  $capTrigger = $maxTurns - 25;
  $lastKey = "";
  $stuck = 0;
  $turns = 0;
  $lastTurn = 0;
  $draw = false;
  $capReason = null;
  $stuckLimit = intval(getenv("TCG_STUCK_LIMIT") ?: 200);
  $decisionLimit = intval(getenv("TCG_MAX_DECISIONS") ?: 3000);
  $GLOBALS["simPolicyQueries"] = 0;
  try {
    while (!IsGameOver() && $steps < $maxSteps && !$draw) {
      $player = $GLOBALS["currentPlayer"] ?? 1;
      PuzzleBeginStep($player);
      // Give the AI enough iteration budget: each PuzzleFinishStep runs
      // EncounterAI (30 iters max), and a drive step can span ~7 rounds.
      // Without this, the logic limit force-passes whole turns.
      $finishSteps = intval(getenv("TCG_FINISH_STEPS") ?: 20);
      for ($k = 0; $k < $finishSteps && !IsGameOver() && !$draw; ++$k) {
        PuzzleFinishStep();
        if ($GLOBALS["simLogDir"] ?? null) SimLog_Track();
        // Check the turn cap per finish step: a drive step can span dozens
        // of turns, so checking only per drive step overshoots the cap.
        $t = $GLOBALS["currentTurn"] ?? 0;
        if ($t > $lastTurn) { $lastTurn = $t; $turns = $t; }
        if ($turns >= $capTrigger) { $draw = true; $capReason = "turns"; break; }
      }
      ++$steps;
      $t = $GLOBALS["currentTurn"] ?? 0;
      if ($t > $lastTurn) { $lastTurn = $t; $turns = $t; }
      if ($turns >= $capTrigger) { $draw = true; $capReason = "turns"; break; }
      if (($GLOBALS["simPolicyQueries"] ?? 0) > $decisionLimit) { $draw = true; $capReason = "decisions"; break; }
      $key = SimStateHash($GLOBALS["lastWrittenGamestate"] ?? "", $GLOBALS["p1Key"] ?? "");
      if ($key === $lastKey) {
        if (++$stuck > $stuckLimit) { $capReason = "stuck"; break; } // no-progress guard
      } else { $stuck = 0; $lastKey = $key; }
    }
  } catch (Throwable $e) {
    return ["error" => "engine exception: " . $e->getMessage(), "steps" => $steps];
  }
  if ($capReason === null && $draw) $capReason = "turns";
  if ($capReason === null && !IsGameOver()) $capReason = ($steps >= $maxSteps) ? "steps" : "guard";
  $winner = $draw ? 0 : ($GLOBALS["winner"] ?? 0);
  $p1Life = &GetHealth(1);
  $p2Life = &GetHealth(2);
  $result = [
    "winner" => $winner,
    "draw" => $draw,
    "steps" => $steps,
    "turns" => $turns,
    "p1life" => $p1Life,
    "p2life" => $p2Life,
    "stuck" => $stuck > $stuckLimit,
    "capped" => $capReason !== null,
    "cap_reason" => $capReason,
    "gamename" => $gameName,
  ];
  if ($GLOBALS["simLogDir"] ?? null) SimLog_End($result);
  // cleanup (unless KEEP_GAME=1 in env, for debugging)
  $keep = getenv("KEEP_GAME");
  if ($keep === false || $keep === "" || $keep === "0") {
    foreach (glob($gameDir . "*") ?: [] as $f) @unlink($f);
    @rmdir($gameDir);
    DeleteCache($gameName);
  } else {
    fwrite(STDERR, "kept game dir: $gameDir\n");
  }
  return $result;
}

$results = [];
$deckLabel = function($p) { return preg_replace('/\.txt$/', '', basename($p)); };
for ($g = 0; $g < $games; ++$g) {
  $fp = $cliFirstPlayer > 0 ? $cliFirstPlayer : (($g % 2) + 1); // alternate when unset
  // reseed engine RNG per game (survey §4: deterministic seed otherwise replays draws)
  $seed = isset($fixedSeed) && $games == 1 ? $fixedSeed : random_int(1, PHP_INT_MAX);
  mt_srand($seed);
  $GLOBALS["simSeed"] = $seed;
  // Phase 2b LABEL_MODE (throwaway tree): label harvested snapshots and exit.
  if (getenv("LABEL_DRIVER")) { return; }
  if (getenv("LABEL_MODE")) {
    $idxPath = getenv("LABEL_INDEX");
    $snapRoot = rtrim(strval(getenv("LABEL_SNAPS")), "/");
    $outPath = getenv("LABEL_OUT");
    $only = getenv("LABEL_ONLY") ?: "";
    $lcfg = ["W" => intval(getenv("LABEL_W") ?: 10),
             "cap" => intval(getenv("LABEL_CAP") ?: 6),
             "pair" => strval(getenv("LABEL_PAIR") ?: "vh"),
             "seedBase" => intval(getenv("LABEL_SEED") ?: 555001)];
    foreach (file($idxPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
      $meta = json_decode($line, true);
      if (!$meta) continue;
      if ($only !== "" && $meta["snap"] !== $only) continue;
      $rows = SimLabel_RunForSnapshot($snapRoot . "/" . $meta["snap"], $meta, $lcfg);
      foreach ($rows as $r) {
        $r["pair"] = $lcfg["pair"];
        file_put_contents($outPath, json_encode($r) . "\n", FILE_APPEND);
      }
      fwrite(STDERR, "labeled " . $meta["snap"] . " (" . count($rows) . " rollouts)\n");
    }
    exit(0);
  }
  $GLOBALS["simDeckA"] = ["label" => "P1:" . $deckLabel($p1DeckPath), "file" => basename($p1DeckPath)];
  $GLOBALS["simDeckB"] = ["label" => "P2:" . $deckLabel($p2DeckPath), "file" => basename($p2DeckPath)];
  $r = PlayOneGame($p1DeckPath, $p2DeckPath, $fp);
  $r["game"] = $g + 1;
  $r["firstPlayer"] = $fp;
  $results[] = $r;
  echo json_encode($r) . "\n";
  if (isset($r["error"])) break;
}
