<?php
// Round-9 Stage 2 LIVE TEACHER build: byte-derived from
// code/search_s1.php (the Stage 1 evaluator build) with ONLY the
// Stage 2 changes listed in fixtures/search_s2_diff.txt:
//   (1) the live teacher tuple (SimTeacher_Tuple): the run-pinned
//       parameter set {name, hooks, deadline_s, horizon,
//       horizon_value, k, margin} read from env TEACHER_TUPLE_JSON,
//       validated before any decision (malformed = throw, caught
//       by the Decide wrapper and logged as an abort), stamped on
//       every teacher stat row. UNPINNED (env absent) the tuple is
//       the legacy live constants (hooks 4000 via the label-path
//       default, deadline 180, horizon 0/off, k 25, margin 1.5),
//       so an unparameterized call reproduces the pre-Stage-2
//       live teacher and the registered label instrument exactly.
//   (2) SimTeacher_DecideInner passes the tuple's horizon and
//       hook budget through cfg into its rollout children (the
//       children's hook guards in SimLabel_ChildChoose /
//       SimLabel_ChildDQ read $GLOBALS["ssLabelHookBudget"],
//       which SimLabel_RunRollout sets from cfg -- the live tuple
//       now reaches it; previously the live path passed neither
//       key and the children ran at the 4000 label default), the
//       parent deadline and k and the paired margin come from the
//       tuple, and a drawn world (winner 0, horizon-ended or
//       natural) is priced at the tuple's horizon_value INSIDE
//       the candidate means, where it changes picks (ruling
//       sec.3.1: the -1 that replaces the 0.5).
//   (3) SimLabel_RunRollout records both players' life totals
//       (life_root / life_opp, via GetHealth as in play_game's
//       result JSON) on every world that ends at the horizon, so
//       the life-differential price is computable from the row
//       (ruling sec.3.2). Non-horizon worlds carry no life
//       fields; the offline label rows' outcome/winner/horizon
//       semantics are unchanged, so the Stage 0/1 analyzers read
//       this build's label rows exactly as before.
// The (b) featurizer correction stays OUT (not in this lineage).
// Nothing else changes.
//
// Round-10 sec.14 addendum (THIS round-10 copy only; the
// round-9 file of the same name is untouched and stays
// 85490e8e...): SimLabel_RunRollout's horizon handling
// is aligned to the live instrument. As built through
// round 9, the horizon check ran once per outer rollout
// iteration -- after up to 20 PuzzleFinishStep() calls --
// so horizon worlds exited at a median ~30 turns past
// the turn-62 trigger and decisive worlds could be
// recorded after it. The fix: the check runs after EACH
// PuzzleFinishStep() (the live play_game.php checks its
// cap per finish step, for exactly this reason), and a
// step that carries currentTurn to the trigger scores
// the world a horizon draw even when the same step also
// ended the game (the live cap overrides the winner the
// same way). No other behavior changes; the sec.14
// package doc carries the mechanism evidence and the
// fixture (fixtures/fx_horizon.py).
//
// Round-9 Stage 1 evaluator build: byte-derived from
// code/search_horizon.php (sha256 6d63f5c3...) with ONLY the
// clause-8 parameterization of the LABEL path (see
// fixtures/search_s1_diff.txt): the rollout hook budget and the
// per-candidate parent deadline become cfg parameters
// (hookBudget / deadlineS, defaults 4000 / 300 = the registered
// label instrument, so an unparameterized call is byte-equivalent
// in behavior). The D7 horizon block is inherited unchanged. The
// teacher Decide path and every non-label function are
// byte-identical to the horizon build.
// search.php — ISMCTS decision layer for tcg-sim (see DESIGN.md).
//
// Loaded by play_game.php with --policy-search (after policy_v1.php,
// featurize.php, policy_server.php). At learner branch decisions with a
// real choice, SimSearch_RootDecide() runs root-parallel ISMCTS:
// fork D children, each determinizes the hidden zones in its private
// copy of the game, runs S PUCT sims against the v15 net (priors +
// value leaves via search_server.py "eval" requests), and reports root
// visit counts; the parent aggregates and plays the most-visited action.
//
// FAIR PLAY: determinization works by CONSERVATION on zone contents —
// the opponent's unseen pool is the multiset of cards physically in
// their deck+hand+arsenal zones. The true split among those zones is
// never read as information; the pool is shuffled and re-dealt at the
// observed sizes. A conservation canary (pool + public == decklist)
// fails closed to plain net play if any card sits in an unaccounted
// zone.

// ------------------------------------------------------------------ utils

function SimSearch_CountInto(&$counts, $ids) {
  foreach ((array)$ids as $id) {
    if ($id === "" || $id === null) continue;
    $id = strval($id);
    $counts[$id] = ($counts[$id] ?? 0) + 1;
  }
}

function SimSearch_FlatIDs($arr) {
  $ids = [];
  foreach ((array)$arr as $cid) {
    if ($cid !== "" && $cid !== null) $ids[] = strval($cid);
  }
  return $ids;
}

// Deterministic Fisher-Yates driven ONLY by a private xorshift32 stream
// held in a global. This must never consume the process's mt_rand stream:
// Determinize runs in the live parent process, and perturbing the engine's
// RNG would change the real game's subsequent draws (and would make
// paired-seed action-equivalence tests impossible).
function SimSearch_XorNext() {
  $x = intval($GLOBALS["ssXorState"] ?? 0);
  if ($x === 0) $x = 0x9E3779B9;
  $x ^= ($x << 13) & 0xFFFFFFFF;
  $x ^= $x >> 17;
  $x ^= ($x << 5) & 0xFFFFFFFF;
  $GLOBALS["ssXorState"] = $x & 0xFFFFFFFF;
  return $GLOBALS["ssXorState"];
}

function SimSearch_SeedShuffle($seed) {
  $s = intval($seed) & 0xFFFFFFFF;
  $GLOBALS["ssXorState"] = $s !== 0 ? $s : 0x9E3779B9;
  // Warm up the stream (xorshift needs a few steps to decorrelate seeds).
  for ($i = 0; $i < 4; ++$i) SimSearch_XorNext();
}

function SimSearch_Shuffle($ids) {
  $ids = array_values($ids);
  for ($i = count($ids) - 1; $i > 0; --$i) {
    $j = SimSearch_XorNext() % ($i + 1);
    $t = $ids[$i]; $ids[$i] = $ids[$j]; $ids[$j] = $t;
  }
  return $ids;
}

// ------------------------------------------------------- zone access
// Canonical per-player arrays are $p1Deck/$p2Deck etc. (ParseGamestate).
// The getters return references to per-perspective views; we write BOTH
// so whichever the engine reads mid-step sees the determinized world.

function &SimSearch_GetZoneRef($player, $zone) {
  switch ($zone) {
    case "deck": $r = &GetDeck($player); break;
    case "hand": $r = &GetHand($player); break;
    case "arsenal": $r = &GetArsenal($player); break;
    default: $r = null; break;
  }
  return $r;
}

function SimSearch_CanonVar($player, $zone) {
  // "p1Deck", "p2Hand", ...
  return "p" . intval($player) . ucfirst($zone);
}

function SimSearch_ReadZone($player, $zone) {
  $v = SimSearch_CanonVar($player, $zone);
  if (isset($GLOBALS[$v]) && is_array($GLOBALS[$v])) return $GLOBALS[$v];
  $r = &SimSearch_GetZoneRef($player, $zone);
  return is_array($r) ? $r : [];
}

function SimSearch_WriteZone($player, $zone, $arr) {
  $v = SimSearch_CanonVar($player, $zone);
  $GLOBALS[$v] = $arr;
  $r = &SimSearch_GetZoneRef($player, $zone);
  if (is_array($r)) $r = $arr;
}

// ------------------------------------------------------- public / pool

// Card IDs in a player's public zones (featurizer-readable), as counts.
// Includes soul (empty for Fai, covered for safety) and the player's
// combat-chain link cards.
function SimSearch_PublicCounts($p) {
  $c = [];
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetDiscard($p), DiscardPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetBanish($p), BanishPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetPitch($p), PitchPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetAllies($p), AllyPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetAuras($p), AuraPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetItems($p), ItemPieces()));
  SimSearch_CountInto($c, SimFeat_ZoneIDs(GetPlayerCharacter($p), CharacterPieces()));
  if (function_exists("GetSoul")) {
    try { SimSearch_CountInto($c, SimFeat_ZoneIDs(GetSoul($p), SoulPieces())); }
    catch (Throwable $e) { /* no soul zone in this build */ }
  }
  return $c;
}

// All combat-chain card IDs (both players; links are public).
function SimSearch_ChainIDs() {
  $ids = [];
  try {
    $cc = $GLOBALS["combatChain"] ?? [];
    if (is_array($cc)) {
      $pieces = function_exists("CombatChainPieces") ? CombatChainPieces() : 12;
      $n = count($cc);
      for ($i = 0; $i + $pieces - 1 < $n; $i += $pieces) {
        $cid = $cc[$i] ?? "";
        if ($cid !== "" && $cid !== null) $ids[] = strval($cid);
      }
    }
  } catch (Throwable $e) { /* no chain */ }
  return $ids;
}

// The unseen pool for player $p: IDs physically in deck+hand+arsenal.
// Arsenal contributes only its card-ID fields (offset 0 of each entry).
function SimSearch_PoolIDs($p) {
  $ids = [];
  foreach (SimSearch_FlatIDs(SimSearch_ReadZone($p, "deck")) as $id) $ids[] = $id;
  foreach (SimSearch_FlatIDs(SimSearch_ReadZone($p, "hand")) as $id) $ids[] = $id;
  $ars = SimSearch_ReadZone($p, "arsenal");
  $pieces = ArsenalPieces();
  $n = is_array($ars) ? count($ars) : 0;
  for ($i = 0; $i + $pieces - 1 < $n; $i += $pieces) {
    $cid = $ars[$i] ?? "";
    if ($cid !== "" && $cid !== null) $ids[] = strval($cid);
  }
  return $ids;
}

function SimSearch_DecklistCounts($deckFile) {
  // Deck files: whitespace-separated tokens (line 1 = hero + equipment,
  // line 2 = deck cards). The full token multiset is the conservation
  // universe: character zone + every other zone partitions it.
  $c = [];
  $raw = file_get_contents($deckFile) ?: "";
  foreach (preg_split('/\s+/', trim($raw)) as $id) {
    if ($id !== "") $c[$id] = ($c[$id] ?? 0) + 1;
  }
  return $c;
}

// Card IDs referenced by closed chain links ($chainLinks) and the stack
// ($layers). Physical chain cards appear at link offset 0 (the played
// card) and sometimes at later offsets (reactions/blocks); the same card
// can be referenced twice in one link, and a played card can still be
// listed in its home zone (double-homing — e.g. Phoenix Flame played
// from the graveyard). We therefore credit chain/layer cards as an ID
// SET (once per ID), never as counts.
function SimSearch_ChainLayerCredits() {
  // id => max copies that could be resident on the chain / stack: one per
  // distinct chain link referencing the id, +1 for the live combat chain,
  // +1 if the id appears anywhere in the layers array.
  $credit = [];
  foreach (SimSearch_ChainIDs() as $id) $credit[$id] = ($credit[$id] ?? 0) + 1;
  $links = $GLOBALS["chainLinks"] ?? [];
  if (is_array($links)) {
    foreach ($links as $link) {
      if (!is_array($link)) continue;
      $seenInLink = [];
      foreach ($link as $field) {
        if (is_string($field) && $field !== "" && strpos($field, "_") !== false) {
          $seenInLink[$field] = true;
        }
      }
      foreach (array_keys($seenInLink) as $id) $credit[$id] = ($credit[$id] ?? 0) + 1;
    }
  }
  $layers = $GLOBALS["layers"] ?? [];
  if (is_array($layers)) {
    $seenLayers = [];
    foreach ($layers as $field) {
      if (is_string($field) && $field !== "" && strpos($field, "_") !== false) {
        $seenLayers[$field] = true;
      }
    }
    foreach (array_keys($seenLayers) as $id) $credit[$id] = ($credit[$id] ?? 0) + 1;
  }
  return $credit;
}

// Missing-card canary (global over both players): every decklist card
// must be findable in pool + public zones, or referenced by the chain /
// layers ID set. A card that is nowhere accounted sits in a zone the
// determinizer does not model (mid-effect limbo) — fail closed.
// Extras are tolerated (tokens like "fealty" are generated, not in any
// decklist; double-homed cards count twice in `have`). Global accounting
// is exact for the mirror (identical lists); per-player attribution of
// chain cards is ambiguous with identical decklists anyway.
// Returns the missing multiset (empty = world fully accounted).
function SimSearch_MissingCards($deckFiles) {
  $deckAll = [];
  foreach ([1, 2] as $p) {
    foreach (SimSearch_DecklistCounts($deckFiles[$p]) as $id => $n) {
      $deckAll[$id] = ($deckAll[$id] ?? 0) + $n;
    }
  }
  $have = [];
  foreach ([1, 2] as $p) {
    SimSearch_CountInto($have, SimSearch_PoolIDs($p));
    foreach (SimSearch_PublicCounts($p) as $id => $n) {
      $have[$id] = ($have[$id] ?? 0) + $n;
    }
  }
  $credit = SimSearch_ChainLayerCredits();
  $missing = [];
  foreach ($deckAll as $id => $n) {
    $h = intval($have[$id] ?? 0);
    $gap = $n - $h;
    if ($gap <= 0) continue;
    $gap -= intval($credit[$id] ?? 0);
    if ($gap > 0) $missing[$id] = $gap;
  }
  return $missing;
}

function SimSearch_Canary($deckFiles) {
  $missing = SimSearch_MissingCards($deckFiles);
  if ($missing !== []) {
    $GLOBALS["ssLastCanaryMissing"] = $missing;
    return false;
  }
  return true;
}

// ------------------------------------------------------- determinization

// Sample a determinized world for root player $root and return an
// assignment (pure data; apply with SimSearch_ApplyAssignment):
//   ["hand" => [ids], "arsenal" => id|null, "oppDeck" => [ids],
//    "ownDeck" => [ids]]
// Opponent = 3 - $root. Opponent hand/arsenal SIZES are observed facts
// (zone sizes), their contents are sampled from the pool by conservation.
function SimSearch_Determinize($root, $seed) {
  $opp = 3 - intval($root);
  $oppHandSize = count(SimSearch_FlatIDs(SimSearch_ReadZone($opp, "hand")));
  $ars = SimSearch_ReadZone($opp, "arsenal");
  $pieces = ArsenalPieces();
  $oppArsCount = 0;
  $n = is_array($ars) ? count($ars) : 0;
  for ($i = 0; $i + $pieces - 1 < $n; $i += $pieces) {
    if (($ars[$i] ?? "") !== "") ++$oppArsCount;
  }
  // Arsenal slots: a face-up card is PUBLIC information - it stays
  // fixed (excluded from the unseen pool, kept in its slot). Hidden
  // (face-down) slots are sampled from the pool like the hand.
  $arsSlots = [];   // per slot: ["id" =>, "fixed" => bool]
  for ($i = 0, $k = 0; $i + $pieces - 1 < $n; $i += $pieces, ++$k) {
    $cid = strval($ars[$i] ?? "");
    if ($cid === "") continue;
    $facing = strval($ars[$i + 1] ?? "DOWN");
    $arsSlots[] = ["id" => $cid, "fixed" => $facing !== "DOWN"];
  }
  $pool = SimSearch_PoolIDs($opp);
  foreach ($arsSlots as $s) {
    if (!$s["fixed"]) continue;
    $ix = array_search($s["id"], $pool, true);
    if ($ix !== false) array_splice($pool, $ix, 1);
  }
  SimSearch_SeedShuffle($seed);
  $pool = SimSearch_Shuffle($pool);
  $hand = array_slice($pool, 0, $oppHandSize);
  $rest = array_slice($pool, $oppHandSize);
  $arsenalIDs = [];
  foreach ($arsSlots as $s) {
    if ($s["fixed"]) { $arsenalIDs[] = $s["id"]; continue; }
    $arsenalIDs[] = $rest[0] ?? null;
    $rest = array_slice($rest, 1);
  }
  $ownDeck = SimSearch_Shuffle(SimSearch_FlatIDs(SimSearch_ReadZone($root, "deck")));
  return [
    "root" => intval($root), "opp" => $opp,
    "hand" => $hand, "arsenal" => $arsenalIDs,
    "oppDeck" => array_values($rest), "ownDeck" => $ownDeck,
  ];
}

function SimSearch_ApplyAssignment($a) {
  // RETIRED (2026-10-18): memory-only application is the bug that
  // voided every rollout - the engine re-derives state from the
  // serialization at the first step. Use ApplyAssignmentToFile.
  throw new Exception("SimSearch_ApplyAssignment is retired; use SimSearch_ApplyAssignmentToFile");
}

// Persist a determinization into a copied game dir's serialized state
// BEFORE parsing. ApplyAssignment alone edits memory only, and the
// engine's first step re-derives state from the serialization (file +
// SHMOP cache), discarding memory-only edits. Editing the file makes
// every representation derive from the determinized state. Content
// line indices per vendor ParseGamestate.php (p1: hand 1, deck 2,
// arsenal 5; p2: hand 19, deck 20, arsenal 23).
function SimSearch_ApplyAssignmentToFile($dir, $a) {
  // FAIL CLOSED: returns false on any inconsistency; callers abort
  // the world. A silent partial edit recreates the true-state bug.
  $file = rtrim($dir, "/") . "/gamestate.txt";
  $raw = @file_get_contents($file);
  if ($raw === false) return false;
  $lines = explode("\r\n", $raw);
  if (count($lines) < 24) return false;
  $opp = intval($a["opp"]); $root = intval($a["root"]);
  $handIdx = $opp === 1 ? 1 : 19;
  $deckIdx = $opp === 1 ? 2 : 20;
  $arsIdx  = $opp === 1 ? 5 : 23;
  $rootDeckIdx = $root === 1 ? 2 : 20;
  if (!isset($lines[$handIdx]) || !isset($lines[$deckIdx])
      || !isset($lines[$rootDeckIdx]) || !isset($lines[$arsIdx])) return false;
  $lines[$handIdx] = implode(" ", array_values($a["hand"]));
  $lines[$deckIdx] = implode(" ", array_values($a["oppDeck"]));
  $lines[$rootDeckIdx] = implode(" ", array_values($a["ownDeck"]));
  // Arsenal: REBUILD each sampled slot from a whitelist - the
  // assigned card id plus the slot's public facing field, with the
  // structural fields at their canonical constants (field2=1, rest
  // 0; measured constant across 1,524 snap slots). Fields must stay
  // NON-EMPTY: the parser drops empty tokens and the stride parse
  // collapses, vanishing the card. Field 5 (a descriptor naming the
  // true card) becomes "0" (none) unless SIM_ARS_DESC=1 (experiment:
  // descriptor for the sampled card). A slot whose assigned id is
  // the true card (face-up fixed, or sampled by coincidence) keeps
  // its original fields - that card's true state is correct for it.
  $arsIDs = array_values((array)($a["arsenal"] ?? []));
  $fields = $lines[$arsIdx] === "" ? [] : explode(" ", $lines[$arsIdx]);
  $pieces = ArsenalPieces();
  $slots = 0;
  for ($i = 0; $i + $pieces - 1 < count($fields); $i += $pieces) {
    if (($fields[$i] ?? "") !== "") ++$slots;
  }
  if (count($arsIDs) !== $slots) return false;
  for ($k = 0; $k < $slots; ++$k) {
    $base = $k * $pieces;
    if (strval($fields[$base] ?? "") === strval($arsIDs[$k])) continue;
    $facing = strval($fields[$base + 1] ?? "DOWN");
    $desc = "0";
    if (getenv("SIM_ARS_DESC") === "1") {
      $dp = explode(";", strval($fields[$base + 5] ?? ""));
      $desc = "2;" . strval($arsIDs[$k]) . ";" . ($dp[2] ?? "0");
    }
    $fields[$base] = strval($arsIDs[$k]);
    $fields[$base + 1] = $facing;
    $fields[$base + 2] = "1";
    $fields[$base + 3] = "0";
    $fields[$base + 4] = "0";
    $fields[$base + 5] = $desc;
    $fields[$base + 6] = "0";
  }
  if ($slots > 0) $lines[$arsIdx] = implode(" ", $fields);
  return file_put_contents($file, implode("\r\n", $lines)) !== false;
}

// Strip true-state residue from a child's private game dir: engine
// backup snapshots and the game log carry the TRUE state/cards and
// must not ride along with the determinized copy. (R3: after this +
// ApplyAssignmentToFile, two children built from parents that differ
// only in the true split are byte-identical over the whole directory.)
function SimSearch_SanitizeChildDir($dir) {
  $dir = rtrim($dir, "/") . "/";
  foreach (glob($dir . "gamestateBackup*.txt") ?: [] as $f) @unlink($f);
  foreach (["startChainLinkGamestate.txt", "gamestateBackup.txt",
            "gamelog.txt"] as $f) @unlink($dir . $f);
}

// Runtime canary (R2): after ParseGamestate, the child's zones must
// equal the assignment exactly - hand, both decks (ordered), arsenal
// ids by slot. Any mismatch means the determinization did not take.
function SimSearch_VerifyAssignment($a) {
  $opp = intval($a["opp"]); $root = intval($a["root"]);
  $ids = function ($xs) { return array_map("strval", array_values((array)$xs)); };
  if ($ids(SimSearch_FlatIDs(SimSearch_ReadZone($opp, "hand"))) !== $ids($a["hand"])) return false;
  if ($ids(SimSearch_FlatIDs(SimSearch_ReadZone($opp, "deck"))) !== $ids($a["oppDeck"])) return false;
  if ($ids(SimSearch_FlatIDs(SimSearch_ReadZone($root, "deck"))) !== $ids($a["ownDeck"])) return false;
  $ars = SimSearch_ReadZone($opp, "arsenal");
  $pieces = ArsenalPieces();
  $got = [];
  $n = is_array($ars) ? count($ars) : 0;
  for ($i = 0; $i + $pieces - 1 < $n; $i += $pieces) {
    if (($ars[$i] ?? "") !== "") $got[] = strval($ars[$i]);
  }
  return $got === $ids((array)($a["arsenal"] ?? []));
}

// ============================================================== eval client

class SimSearchLeaf extends Exception {}
class SimSearchAbort extends Exception {}

function SimSearch_DropInheritedSockets() {
  if (isset($GLOBALS["simPolicySock"]) && is_resource($GLOBALS["simPolicySock"])) {
    @fclose($GLOBALS["simPolicySock"]);
  }
  unset($GLOBALS["simPolicySock"]);
  unset($GLOBALS["simSearchSock"]);
}

function SimSearch_Connect() {
  if (isset($GLOBALS["simSearchSock"]) && is_resource($GLOBALS["simSearchSock"])) {
    return $GLOBALS["simSearchSock"];
  }
  $sock = @stream_socket_client("unix://" . SimPolicyServer_SockPath(), $errno, $errstr, 5);
  if ($sock === false) return null;
  stream_set_timeout($sock, 30);
  $GLOBALS["simSearchSock"] = $sock;
  return $sock;
}

// One eval round-trip. Returns [priors(array), value(float)] or null.
function SimSearch_Eval($state, $candRecs) {
  $payload = json_encode(["mode" => "eval", "state" => $state, "candidates" => $candRecs, "learner_seat" => intval(getenv("TCG_LEARNER_SEAT") ?: 0)]);
  $msg = pack("N", strlen($payload)) . $payload;
  for ($attempt = 0; $attempt < 2; ++$attempt) {
    $sock = SimSearch_Connect();
    if ($sock === null) return null;
    $off = 0; $ok = true;
    while ($off < strlen($msg)) {
      $w = @fwrite($sock, substr($msg, $off));
      if ($w === false || $w <= 0) { $ok = false; break; }
      $off += $w;
    }
    if (!$ok) { @fclose($sock); unset($GLOBALS["simSearchSock"]); continue; }
    $hdr = @fread($sock, 4);
    if ($hdr === false || strlen($hdr) < 4) { @fclose($sock); unset($GLOBALS["simSearchSock"]); continue; }
    $len = unpack("N", $hdr)[1];
    if ($len <= 0 || $len > 50 * 1024 * 1024) { @fclose($sock); unset($GLOBALS["simSearchSock"]); continue; }
    $body = "";
    while (strlen($body) < $len) {
      $chunk = @fread($sock, $len - strlen($body));
      if ($chunk === false || $chunk === "") break;
      $body .= $chunk;
    }
    if (strlen($body) < $len) { @fclose($sock); unset($GLOBALS["simSearchSock"]); continue; }
    $resp = json_decode($body, true);
    if (is_array($resp) && ($resp["error"] ?? "") === "seat_mismatch") {
      // R12: same loud failure as the bridge funnel (the paired
      // driver counts the SEAT_MISMATCH token in the game log).
      fwrite(STDERR, "search: SEAT_MISMATCH server_seat="
        . intval($resp["learner_seat"] ?? -1) . " request_seat="
        . intval(getenv("TCG_LEARNER_SEAT") ?: 0) . "\n");
      return null;
    }
    if (!is_array($resp) || !isset($resp["priors"]) || !isset($resp["value"])) {
      @fclose($sock); unset($GLOBALS["simSearchSock"]); continue;
    }
    return [$resp["priors"], floatval($resp["value"])];
  }
  return null;
}

// Build the masked state for a decision and evaluate it. Canary runs as
// in production; a leak throws (fail-closed) and is treated as eval null.
function SimSearch_EvalState($player, $branch, $candRecs) {
  try {
    $state = SimFeat_BuildState($player, $branch, $candRecs);
    SimFeat_Canary($player, $state);
  } catch (Throwable $e) {
    return null;
  }
  $ev = SimSearch_Eval($state, $candRecs);
  if (SimTrace_On()) {
    $GLOBALS["ssTraceLastEval"] = [
      "state_hash" => SimTrace_Hash($state),
      "priors" => ($ev !== null && isset($ev[0])) ? $ev[0] : null];
  }
  return $ev;
}

// ============================================================== tree (child)

function SimSearch_NewNode() {
  return ["player" => null, "branch" => null, "cands" => null,
          "P" => null, "N" => 0, "W" => 0.0,
          "children" => null, "expanded" => false];
}

// Backprop a root-frame value along the path (node ids, root first).
// W is stored in ROOT frame for every node; PUCT converts to the
// selecting mover's frame at selection time. (Placeholder nodes have no
// mover yet, so mover-frame storage would be ill-defined for them.)
function SimSearch_Backprop($path, $vRoot) {
  foreach ($path as $nid) {
    $GLOBALS["ssTree"][$nid]["N"] += 1;
    $GLOBALS["ssTree"][$nid]["W"] += $vRoot;
  }
}

// Evaluate the current decision as a leaf, backprop, and end the sim.
// $state is the masked state the caller already built (and canaried).
function SimSearch_LeafCapture($player, $branch, $candRecs, $state) {
  $dir = getenv("LEAF_HARVEST_DIR");
  if ($dir === false || $dir === "") return;
  if (!empty($GLOBALS["ssLeafCaptured"])) return;
  if (intval($GLOBALS["ssDepth"] ?? 0) < 2) return;
  if ((SimSearch_XorNext() % 1000) >= 30) return; // ~3% of eligible leaves
  $GLOBALS["ssLeafCaptured"] = true;
  try {
    DoGamestateUpdate();
    $GLOBALS["skipWriteGamestate"] = false;
    SimSearch_IncludeWithGlobals("WriteGamestate.php");
    $leafId = strval($GLOBALS["gameName"] ?? "") . str_pad(strval(intval($GLOBALS["ssHooks"] ?? 0)), 3, "0", STR_PAD_LEFT);
    $dst = rtrim($dir, "/") . "/" . $leafId . "/";
    SimSearch_CopyDir($GLOBALS["filepath"], $dst);
    file_put_contents(rtrim($dir, "/") . "/leaf_index.jsonl", json_encode([
      "snap" => $leafId, "game" => $leafId, "leaf" => 1,
      "parent_game" => strval($GLOBALS["ssParentGame"] ?? ""),
      "branch" => $branch, "player" => intval($player),
      "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "depth" => intval($GLOBALS["ssDepth"] ?? 0),
      "cands" => $candRecs, "state" => $state,
    ]) . "\n", FILE_APPEND);
  } catch (Throwable $e) { /* capture must never break the search */ }
}

function SimSearch_LeafOut($player, $branch, $candRecs, $state) {
  SimSearch_LeafCapture($player, $branch, $candRecs, $state);
  $ev = SimSearch_Eval($state, $candRecs);
  $val = $ev ? $ev[1] : 0.0;
  $vRoot = (intval($player) === intval($GLOBALS["ssRootPlayer"])) ? $val : -$val;
  SimSearch_Backprop($GLOBALS["ssStack"], $vRoot);
  throw new SimSearchLeaf();
}

// Branch-decision hook inside a search child. $cands/$candRecs/$gate come
// from SimPolicyServer_Choose (collection already done there, exactly as
// in production). Returns [true, node|null] like Choose.
function SimSearch_ChildChoose($branch, $cands, $candRecs, $state, $gate) {
  $GLOBALS["ssHooks"] = ($GLOBALS["ssHooks"] ?? 0) + 1;
  if (!$gate || count($cands) === 0) return [true, null];
  if (count($cands) === 1) {
    if (($GLOBALS["ssHooks"] ?? 0) > 500) {
      $player = intval($GLOBALS["currentPlayer"] ?? 1);
      SimSearch_LeafOut($player, $branch, $candRecs, $state);
    }
    return [true, $cands[0]];
  }
  $player = intval($GLOBALS["currentPlayer"] ?? 1);
  // Sim budget: hooks, branching depth, and one-turn horizon.
  if (($GLOBALS["ssHooks"] ?? 0) > 500
      || ($GLOBALS["ssDepth"] ?? 0) >= 24
      || intval($GLOBALS["currentTurn"] ?? 0) > intval($GLOBALS["ssRootTurn"] ?? 0) + 1) {
    SimSearch_LeafOut($player, $branch, $candRecs, $state);
  }
  $curId = intval(end($GLOBALS["ssStack"]));
  $node = &$GLOBALS["ssTree"][$curId];
  if (!$node["expanded"]) {
    // Root-identity check: the first branching hook of every sim must be
    // the real root decision; a child whose replay diverges before the
    // root is searching the wrong decision and must report nothing.
    if ($curId === 0 && !empty($GLOBALS["ssRootKey"])) {
      $key = $branch . "|" . $player . "|" . implode(",", array_map(
        function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $candRecs));
      if ($key !== $GLOBALS["ssRootKey"]) {
        throw new SimSearchAbort();
      }
    }
    if ($curId === 0 && empty($GLOBALS["ssHookChecked"])) {
      $GLOBALS["ssHookChecked"] = true;
      $hcErr = SimSearch_HookCheck();
      if ($hcErr !== null) {
        $GLOBALS["ssChildError"] = $hcErr;
        throw new SimSearchAbort();
      }
    }
    // Materialize + expand this node.
    $ev = SimSearch_Eval($state, $candRecs);
    $priors = $ev ? $ev[0] : array_fill(0, count($candRecs), 1.0 / max(1, count($candRecs)));
    $val = $ev ? $ev[1] : 0.0;
    $node["player"] = $player;
    $node["branch"] = $branch;
    $node["cands"] = $candRecs;
    $node["P"] = $priors;
    $node["children"] = [];
    foreach ($candRecs as $i => $_) {
      $GLOBALS["ssTree"][] = SimSearch_NewNode();
      $node["children"][$i] = count($GLOBALS["ssTree"]) - 1;
    }
    $node["expanded"] = true;
    $vRoot = ($player === intval($GLOBALS["ssRootPlayer"])) ? $val : -$val;
    SimSearch_Backprop($GLOBALS["ssStack"], $vRoot);
    throw new SimSearchLeaf();
  }
  // Expanded node: the replay must have arrived at the same decision.
  if ($node["branch"] !== $branch || $node["player"] !== $player
      || count($node["cands"]) !== count($candRecs)) {
    SimSearch_LeafOut($player, $branch, $candRecs, $state); // chance divergence
  }
  // PUCT selection.
  $bestI = -1; $bestScore = -INF;
  $sqrtN = sqrt(max(1, $node["N"]));
  foreach ($node["children"] as $ci => $childId) {
    $ch = $GLOBALS["ssTree"][$childId];
    $meanRoot = $ch["N"] > 0 ? $ch["W"] / $ch["N"] : 0.0;
    $q = ($node["player"] === intval($GLOBALS["ssRootPlayer"])) ? $meanRoot : -$meanRoot;
    if ($ch["N"] === 0) $q = 0.0;
    $u = 1.25 * floatval($node["P"][$ci] ?? 0.0) * $sqrtN / (1 + $ch["N"]);
    $score = $q + $u;
    if ($score > $bestScore) { $bestScore = $score; $bestI = $ci; }
  }
  $GLOBALS["ssStack"][] = $node["children"][$bestI];
  $GLOBALS["ssDepth"] = ($GLOBALS["ssDepth"] ?? 0) + 1;
  unset($node);
  return [true, $cands[$bestI]];
}

// DQ hook inside a search child: net argmax over options, no tree node.
function SimSearch_ChildDQ($player, $candRecs, $state, $options, $v1choice) {
  $GLOBALS["ssHooks"] = ($GLOBALS["ssHooks"] ?? 0) + 1;
  if (($GLOBALS["ssHooks"] ?? 0) > 500
      || intval($GLOBALS["currentTurn"] ?? 0) > intval($GLOBALS["ssRootTurn"] ?? 0) + 1) {
    SimSearch_LeafOut($player, "DQ", $candRecs, $state);
  }
  try { SimFeat_Canary($player, $state); } catch (Throwable $e) { return $v1choice; }
  $ev = SimSearch_Eval($state, $candRecs);
  if (!$ev) return $v1choice;
  $priors = $ev[0];
  $best = 0; $bs = -INF;
  foreach ($priors as $i => $p) { if ($p > $bs) { $bs = $p; $best = $i; } }
  return $options[$best] ?? $v1choice;
}

// ============================================================== child driver

function SimSearch_CopyDir($src, $dst) {
  if (!is_dir($dst)) @mkdir($dst, 0700, true);
  foreach (glob($src . "*") ?: [] as $f) {
    if (is_file($f)) @copy($f, $dst . basename($f));
  }
}

function SimSearch_WipeDir($dir) {
  foreach (glob($dir . "*") ?: [] as $f) @unlink($f);
  @rmdir($dir);
}

// Runs INSIDE a forked child. Never returns (exits the child).
// Children get ONLY the files they need (whitelist, not blacklist):
// the serialized state, the game metadata, and the two deck lists
// (deck knowledge + the conservation canary). Engine backup states,
// game logs and lock files never ride into a child.
function SimSearch_CopyChildDir($src, $dst) {
  $src = rtrim($src, "/") . "/";
  $dst = rtrim($dst, "/") . "/";
  if (!is_dir($dst)) @mkdir($dst, 0777, true);
  foreach (["gamestate.txt", "GameFile.txt", "p1Deck.txt",
            "p2Deck.txt"] as $f) {
    if (is_file($src . $f)) @copy($src . $f, $dst . $f);
  }
}

// Consumer-side determinization check (R2, second placement), run
// at the child's first root-decision hook: the zone split must still
// equal the assignment after the engine's first step, and the global
// missing-card canary must pass on the child's own deck files.
// Returns an error tag, or null when clean.
function SimSearch_HookCheck() {
  $a = $GLOBALS["ssAssignment"] ?? null;
  if (!is_array($a)) return null;
  if (!SimSearch_VerifyAssignment($a)) return "det_verify_hook_failed";
  $fp = $GLOBALS["filepath"] ?? "";
  $deckFiles = [1 => $fp . "p1Deck.txt", 2 => $fp . "p2Deck.txt"];
  if (!SimSearch_Canary($deckFiles)) return "canary_hook_failed";
  return null;
}

function SimSearch_RunChild($dIdx, $parentGame, $parentDir, $resFile, $assignment, $cfg) {
  try {
    SimSearch_DropInheritedSockets();
    $GLOBALS["simSearchChild"] = true;
    $childGame = (string)random_int(100000000, 999999999);
    $snapDir = $GLOBALS["ssGamesRoot"] . $childGame . "_snap/";
    $workDir = $GLOBALS["ssGamesRoot"] . $childGame . "/";
    SimSearch_CopyChildDir($parentDir, $snapDir);
    $GLOBALS["gameName"] = strval($cfg["snapGame"] ?? $childGame);
    $GLOBALS["filepath"] = $workDir;
    $GLOBALS["filename"] = $workDir . "gamestate.txt";
    $GLOBALS["logWriteBuffer"] = [];
    $root = intval($cfg["rootPlayer"]);
    $GLOBALS["ssRootPlayer"] = $root;
    $GLOBALS["ssParentGame"] = $parentGame;
    $GLOBALS["ssRootKey"] = strval($cfg["rootKey"] ?? "");
    $GLOBALS["ssAssignment"] = $assignment;
    $GLOBALS["ssTree"] = [SimSearch_NewNode()];
    $GLOBALS["ssTree"][0]["player"] = $root;
    $simsDone = 0;
    for ($s = 0; $s < intval($cfg["S"]); ++$s) {
      SimSearch_WipeDir($workDir);
      SimSearch_CopyChildDir($snapDir, $workDir);
      $GLOBALS["filename"] = $workDir . "gamestate.txt";
      $GLOBALS["filepath"] = $workDir;
      if (function_exists("DeleteCache")) DeleteCache($childGame);
      if (!SimSearch_ApplyAssignmentToFile($workDir, $assignment)) {
        @file_put_contents($resFile, json_encode(["error" => "det_persist_failed"]));
        SimSearch_WipeDir($workDir);
        SimSearch_WipeDir($snapDir);
        if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
      }
      ParseGamestate();
      if (!SimSearch_VerifyAssignment($assignment)) {
        @file_put_contents($resFile, json_encode(["error" => "det_verify_failed"]));
        SimSearch_WipeDir($workDir);
        SimSearch_WipeDir($snapDir);
        if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
      }
      mt_srand(intval($cfg["seedBase"]) + $s * 7919 + $dIdx * 104729);
      $GLOBALS["ssStack"] = [0];
      $GLOBALS["ssHookChecked"] = false;
      $GLOBALS["ssDepth"] = 0;
      $GLOBALS["ssHooks"] = 0;
      $GLOBALS["ssRootTurn"] = intval($GLOBALS["currentTurn"] ?? 0);
      try {
        $guard = 0; $lastKey = ""; $stuck = 0;
        while (!IsGameOver() && $guard < 400) {
          ++$guard;
          $pl = $GLOBALS["currentPlayer"] ?? 1;
          PuzzleBeginStep($pl);
          for ($k = 0; $k < 20 && !IsGameOver(); ++$k) PuzzleFinishStep();
          $key = SimStateHash($GLOBALS["lastWrittenGamestate"] ?? "", $GLOBALS["p1Key"] ?? "");
          if ($key === $lastKey) { if (++$stuck > 60) break; }
          else { $stuck = 0; $lastKey = $key; }
        }
      } catch (SimSearchLeaf $e) {
        // backprop already done at the leaf
      } catch (SimSearchAbort $e) {
        @file_put_contents($resFile, json_encode(["error" => $GLOBALS["ssChildError"] ?? "root_mismatch"]));
        SimSearch_WipeDir($workDir);
        SimSearch_WipeDir($snapDir);
        if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
      }
      if (IsGameOver()) {
        $winner = intval($GLOBALS["winner"] ?? 0);
        $vRoot = $winner === 0 ? 0.0 : ($winner === $root ? 1.0 : -1.0);
        SimSearch_Backprop($GLOBALS["ssStack"], $vRoot);
      }
      ++$simsDone;
    }
    $rootNode = $GLOBALS["ssTree"][0];
    $visits = []; $wroot = [];
    if ($rootNode["children"]) {
      foreach ($rootNode["children"] as $ci => $childId) {
        $ch = $GLOBALS["ssTree"][$childId];
        $visits[$ci] = intval($ch["N"]);
        $wroot[$ci] = $ch["N"] > 0 ? $ch["W"] / $ch["N"] : 0.0;
      }
    }
    @file_put_contents($resFile, json_encode([
      "det_persisted" => 1, "visits" => $visits, "wroot" => $wroot, "sims" => $simsDone]));
    SimSearch_WipeDir($workDir);
    SimSearch_WipeDir($snapDir);
    if (function_exists("DeleteCache")) DeleteCache($childGame);
  } catch (Throwable $e) {
    @file_put_contents($resFile, json_encode(["error" => $e->getMessage()]));
  }
  if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
}

// ============================================================== root decider

function SimSearch_IncludeWithGlobals($__file) {
  foreach (array_keys($GLOBALS) as $__name) {
    if ($__name !== "GLOBALS" && $__name !== "__file" && $__name !== "__name") global $$__name;
  }
  include $__file;
}

function SimSearch_LogStat($rec) {
  $dir = getenv("TCG_SEARCH_LOG");
  if ($dir === false || $dir === "") return;
  if (!is_dir($dir)) @mkdir($dir, 0700, true);
  $rec["game"] = strval($GLOBALS["gameName"] ?? "");
  @file_put_contents($dir . "/search_stats.jsonl", json_encode($rec) . "\n", FILE_APPEND);
}

// ==============================================================
// Round-9 Stage 2: the live teacher tuple. The run's parameters
// are pinned by env TEACHER_TUPLE_JSON (a JSON object set by the
// runner from rounds/round9/code/settings_stage2.json, the file
// placement of the same values; the games analyzer audits every
// stat row's stamp against that file -- the second placement,
// stage1 pattern). SimTeacher_Tuple() is called at the top of
// SimTeacher_DecideInner, BEFORE any eval or decision: a present
// but malformed pin throws, the Decide wrapper logs the abort,
// and the run's manifest gate fails on the abort row -- a
// mis-pinned run degrades loudly, never silently. An ABSENT pin
// is the legacy instrument: the pre-Stage-2 live constants,
// which are also the registered label defaults, so the label
// path's unparameterized behavior is untouched.
function SimTeacher_Tuple() {
  static $tuple = null;
  if ($tuple !== null) return $tuple;
  $raw = getenv("TEACHER_TUPLE_JSON");
  if ($raw === false || strval($raw) === "") {
    $tuple = ["name" => "unpinned", "hooks" => 4000,
              "deadline_s" => 180, "horizon" => 0,
              "horizon_value" => 0.0, "k" => 25, "margin" => 1.5,
              "pinned" => 0];
    return $tuple;
  }
  $t = json_decode(strval($raw), true);
  $bad = null;
  if (!is_array($t)) $bad = "not_a_json_object";
  elseif (!isset($t["name"]) || strval($t["name"]) === "") $bad = "name";
  elseif (!isset($t["hooks"]) || !is_numeric($t["hooks"])
          || intval($t["hooks"]) != $t["hooks"]
          || intval($t["hooks"]) < 1) $bad = "hooks";
  elseif (!isset($t["deadline_s"]) || !is_numeric($t["deadline_s"])
          || intval($t["deadline_s"]) != $t["deadline_s"]
          || intval($t["deadline_s"]) < 1) $bad = "deadline_s";
  elseif (!isset($t["horizon"]) || !is_numeric($t["horizon"])
          || intval($t["horizon"]) != $t["horizon"]
          || intval($t["horizon"]) < 0) $bad = "horizon";
  elseif (!isset($t["horizon_value"]) || !is_numeric($t["horizon_value"]))
    $bad = "horizon_value";
  elseif (!isset($t["k"]) || !is_numeric($t["k"])
          || intval($t["k"]) != $t["k"] || intval($t["k"]) < 20
          || intval($t["k"]) > 1000) $bad = "k";
  elseif (!isset($t["margin"]) || !is_numeric($t["margin"])
          || floatval($t["margin"]) <= 0.0) $bad = "margin";
  if ($bad !== null) {
    throw new Exception("teacher tuple pin malformed: field " . $bad);
  }
  $tuple = ["name" => strval($t["name"]),
            "hooks" => intval($t["hooks"]),
            "deadline_s" => intval($t["deadline_s"]),
            "horizon" => intval($t["horizon"]),
            "horizon_value" => floatval($t["horizon_value"]),
            "k" => intval($t["k"]),
            "margin" => floatval($t["margin"]),
            "pinned" => 1];
  return $tuple;
}

// The stamp for rows written on paths where the tuple itself may
// be the failure (the Decide wrapper's exception row): the tuple
// when it parses, a named marker when it does not.
function SimTeacher_TupleStamp() {
  try { return SimTeacher_Tuple(); }
  catch (Throwable $e) { return ["name" => "malformed"]; }
}

// Parent-side: run the search for one real decision. Returns the chosen
// candidate index, or null to fall back to plain net play.
// ============================================================== teacher
// Rollout policy-improvement operator (Claude round 7, teacher gate).
// At a live root decision: restrict to the top-3 prior candidates (plus
// any with prior >= 0.10, cap 4); roll each out k=25 over shared
// determinized worlds (conservation + canary, as in search/labeling);
// continuation pair "va" = argmax v15, the deployed continuation.
// Overturn the prior pick only when the paired mean margin over the
// prior pick exceeds 1.5 paired SE (n >= 20 shared finished worlds).
// (Stage 2: k, the margin, the deadline, the rollout horizon and
// hook budget, and the price of a drawn world are the run-pinned
// tuple's; unpinned they take exactly the values in this comment
// and the pre-Stage-2 constants -- see SimTeacher_Tuple.)
function SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  // Abort-reason logging wrapper (round 4): the gate body lives in
  // SimTeacher_DecideInner below, byte-identical. This wrapper only
  // guarantees that a Decide which produces no pick SAYS WHY: the
  // reason lands in $GLOBALS["ssTeacherAbortReason"], a stat row
  // for the aborted decision is written here on the exception path
  // (the eval-null path writes its own, inside Inner), and
  // RootDecide stamps the reason on the marker trace row.
  $GLOBALS["ssTeacherAbortReason"] = null;
  try {
    return SimTeacher_DecideInner($branch, $cands, $candRecs, $player, $gameDir, $bridgeState);
  } catch (Throwable $e) {
    $GLOBALS["ssTeacherAbortReason"] = "exception:" . get_class($e)
      . ":" . substr(strval($e->getMessage()), 0, 120);
    SimSearch_LogStat(["teacher" => 1, "fallback" => "exception",
      "setting" => SimTeacher_TupleStamp(),
      "abort_reason" => $GLOBALS["ssTeacherAbortReason"],
      "branch" => $branch, "player" => $player,
      "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "game" => strval($GLOBALS["gameName"] ?? "")]);
    return null;
  }
}

function SimTeacher_DecideInner($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  $t0 = microtime(true);
  $ncand = count($candRecs);
  // Stage 2: resolve (and validate) the run-pinned tuple BEFORE
  // any eval or decision; a malformed pin throws here and the
  // Decide wrapper logs the abort. Every stat row below carries
  // the tuple as "setting".
  $T = SimTeacher_Tuple();
  // R17: the ROOT priors come from the state the bridge built
  // (passed down from Choose through RootDecide), evaluated as-is.
  // The trace stash is set from that same state, so the root row's
  // feat_post_hash equals its feat_pre_hash by construction. The
  // fallback (no passed state, legacy callers) is the old behavior:
  // re-featurize here, after the checkpoint sync.
  $evRoot = null;
  if ($bridgeState !== null) {
    try {
      SimFeat_Canary($player, $bridgeState);
      $evRoot = SimSearch_Eval($bridgeState, $candRecs);
    } catch (Throwable $e) {
      // Abort-reason logging: a canary throw is a different event
      // from an eval transport failure; give it its own reason.
      $evRoot = null;
      $GLOBALS["ssTeacherAbortReason"] = "root_eval_canary:"
        . get_class($e) . ":" . substr(strval($e->getMessage()), 0, 120);
    }
    if (SimTrace_On()) {
      $GLOBALS["ssTraceLastEval"] = [
        "state_hash" => SimTrace_Hash($bridgeState),
        "priors" => ($evRoot !== null && isset($evRoot[0]))
          ? $evRoot[0] : null];
    }
  } else {
    $evRoot = SimSearch_EvalState($player, $branch, $candRecs);
  }
  if (!$evRoot || !isset($evRoot[0])) {
    // Abort-reason logging: name the cause and the decision. The
    // gate build's row carried only {teacher, fallback, branch},
    // so the fleet's aborted decisions could not be attributed
    // to a game, let alone a cause.
    if (empty($GLOBALS["ssTeacherAbortReason"])) {
      $GLOBALS["ssTeacherAbortReason"] = "root_eval_failed";
    }
    SimSearch_LogStat(["teacher" => 1, "fallback" => "eval", "setting" => $T,
                       "abort_reason" => $GLOBALS["ssTeacherAbortReason"],
                       "branch" => $branch, "player" => $player,
                       "turn" => intval($GLOBALS["currentTurn"] ?? 0),
                       "game" => strval($GLOBALS["gameName"] ?? "")]);
    return null;
  }
  $priors = array_map("floatval", $evRoot[0]);
  $priorPick = SimLabel_PriorArgmax($priors);
  $bp = $priors[$priorPick] ?? 0.0;
  if ($ncand <= 1 || $bp >= 0.97) {
    if (getenv("TEACHER_CAPTURE") && getenv("TEACHER_CAPTURE_UNCONTESTED")
        && $ncand >= 2 && $bp >= 0.97) {
      // Round-10 Step 0 probe (search_s3 only; stock
      // search_s2 has no such block): snapshot SAMPLED
      // uncontested decisions for offline evaluation.
      // Stock behavior returns from this branch with
      // only a stat row -- no snapshot, no priors -- so
      // an uncontested decision leaves nothing an
      // offline eval can run on. When both capture
      // envs are set, this block snapshots the game
      // dir and appends an index row in the contested
      // capture arm's exact shape (same snap counter,
      // same index file), marked "uncontested" => 1
      // with the top prior recorded and the candidate
      // set the search would have used (the Decide
      // selection below: top-3 by prior, then any
      // prior >= 0.10 up to 4 -- with $bp >= 0.97 the
      // tail sums to <= 0.03, so the second loop adds
      // nothing; it is kept so the set is the rule's,
      // not an approximation of it). Sampling is per
      // game, systematic: every
      // TEACHER_CAPTURE_UNCONTESTED_EVERY-th eligible
      // decision (env, default 2). The played pick is
      // untouched: the stat row and the return below
      // are stock, and the capture arm's games are
      // raw-policy games by construction.
      $uncEvery = intval(getenv("TEACHER_CAPTURE_UNCONTESTED_EVERY") ?: 2);
      if ($uncEvery < 1) $uncEvery = 1;
      $gnameU = strval($GLOBALS["gameName"] ?? "");
      $GLOBALS["ssTeacherUncCount"][$gnameU] =
        ($GLOBALS["ssTeacherUncCount"][$gnameU] ?? 0) + 1;
      if (($GLOBALS["ssTeacherUncCount"][$gnameU] % $uncEvery) === 0) {
        $snapDirU = getenv("TEACHER_SNAP_DIR");
        if ($snapDirU !== false && $snapDirU !== "") {
          $GLOBALS["ssTeacherSnapCount"][$gnameU] =
            ($GLOBALS["ssTeacherSnapCount"][$gnameU] ?? 0) + 1;
          $hcU = $GLOBALS["ssTeacherSnapCount"][$gnameU];
          $dstU = rtrim($snapDirU, "/") . "/" . $gnameU . "_t" . $hcU . "/";
          if (!is_dir($dstU)) {
            SimSearch_CopyDir($gameDir, $dstU);
            $stU = null;
            try { $stU = SimFeat_BuildState($player, $branch, $candRecs); }
            catch (Throwable $e) { $stU = null; }
            $orderU = array_keys($priors);
            usort($orderU, function ($a, $b) use ($priors) {
              return $priors[$b] <=> $priors[$a]; });
            $selU = [];
            foreach ($orderU as $i) { if (count($selU) < 3) $selU[] = intval($i); }
            foreach ($orderU as $i) {
              if (count($selU) >= 4) break;
              if ($priors[$i] >= 0.10 && !in_array(intval($i), $selU, true)) {
                $selU[] = intval($i);
              }
            }
            sort($selU);
            file_put_contents(rtrim($snapDirU, "/")
              . "/teacher_snap_index.jsonl",
              json_encode(["snap" => $gnameU . "_t" . $hcU, "game" => $gnameU,
                "hcount" => $hcU, "branch" => $branch, "player" => $player,
                "turn" => intval($GLOBALS["currentTurn"] ?? 0),
                "cands" => $candRecs, "state" => $stU,
                "priors" => $priors, "prior_pick" => $priorPick,
                "selected" => $selU, "uncontested" => 1,
                "top_prior" => $bp]) . "\n", FILE_APPEND);
          }
        }
      }
    }
    SimSearch_LogStat(["teacher" => 1, "contested" => 0, "setting" => $T, "branch" => $branch,
      "player" => $player, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "ncand" => $ncand, "prior_pick" => $priorPick, "pick" => $priorPick,
      "ms" => intval((microtime(true) - $t0) * 1000)]);
    return $priorPick;
  }
  $order = array_keys($priors);
  usort($order, function ($a, $b) use ($priors) {
    return $priors[$b] <=> $priors[$a]; });
  $sel = [];
  foreach ($order as $i) { if (count($sel) < 3) $sel[] = intval($i); }
  foreach ($order as $i) {
    if (count($sel) >= 4) break;
    if ($priors[$i] >= 0.10 && !in_array(intval($i), $sel, true)) {
      $sel[] = intval($i);
    }
  }
  sort($sel);
  if (getenv("TEACHER_CAPTURE")) {
    // Measurement harvest: snapshot EVERY contested decision, play
    // the prior pick, never roll out (trajectory stays plain v15).
    $snapDir0 = getenv("TEACHER_SNAP_DIR");
    if ($snapDir0 !== false && $snapDir0 !== "") {
      $gname = strval($GLOBALS["gameName"] ?? "");
      $GLOBALS["ssTeacherSnapCount"][$gname] =
        ($GLOBALS["ssTeacherSnapCount"][$gname] ?? 0) + 1;
      $hc = $GLOBALS["ssTeacherSnapCount"][$gname];
      $dst = rtrim($snapDir0, "/") . "/" . $gname . "_t" . $hc . "/";
      if (!is_dir($dst)) {
        SimSearch_CopyDir($gameDir, $dst);
        $st = null;
        try { $st = SimFeat_BuildState($player, $branch, $candRecs); }
        catch (Throwable $e) { $st = null; }
        file_put_contents(rtrim($snapDir0, "/")
          . "/teacher_snap_index.jsonl",
          json_encode(["snap" => $gname . "_t" . $hc, "game" => $gname,
            "hcount" => $hc, "branch" => $branch, "player" => $player,
            "turn" => intval($GLOBALS["currentTurn"] ?? 0),
            "cands" => $candRecs, "state" => $st,
            "priors" => $priors, "prior_pick" => $priorPick,
            "selected" => $sel]) . "\n", FILE_APPEND);
      }
    }
    SimSearch_LogStat(["teacher" => 1, "contested" => 1, "capture" => 1, "setting" => $T,
      "det" => "file-v3", "branch" => $branch, "player" => $player,
      "turn" => intval($GLOBALS["currentTurn"] ?? 0), "ncand" => $ncand,
      "selected" => $sel, "prior_pick" => $priorPick,
      "pick" => $priorPick,
      "ms" => intval((microtime(true) - $t0) * 1000)]);
    return $priorPick;
  }
  $K = intval($T["k"]);
  $seedBase = random_int(1, PHP_INT_MAX - 1000000);
  $rootKey = $branch . "|" . $player . "|" . implode(",", array_map(
    function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); },
    $candRecs));
  $assignments = []; $canaryWorlds = 0;
  $abortReasons = []; $abortByCand = [];
  for ($w = 0; $w < $K; ++$w) {
    $a = SimSearch_Determinize($player, $seedBase + $w * 31337);
    if (!is_array($a)) { ++$canaryWorlds; $assignments[$w] = null; }
    else { $assignments[$w] = $a; }
  }
  $outcomes = []; $childFallbacks = 0; $errors = 0;
  $hzWorlds = []; $drawWorlds = []; $hzLife = [];
  foreach ($sel as $ci) {
    $outcomes[$ci] = [];
    $hzWorlds[$ci] = 0; $drawWorlds[$ci] = 0;
    $hzLife[$ci] = ["ahead" => 0, "behind" => 0, "tied" => 0,
                    "life_root_sum" => 0, "life_opp_sum" => 0];
    $kids = [];
    foreach ($assignments as $w => $a) {
      if ($a === null) continue;
      $resFile = sys_get_temp_dir() . "/tch_res_" . getmypid() . "_" . bin2hex(random_bytes(4)) . "_" . $ci
        . "_" . $w . ".json";
      @unlink($resFile);
      $pid = pcntl_fork();
      if ($pid === -1) continue;
      if ($pid === 0) {
        SimLabel_RunRollout(rtrim($gameDir, "/") . "/", $resFile, $a,
          ["rootPlayer" => $player, "rootKey" => $rootKey, "forceIdx" => $ci,
           "snapGame" => strval($GLOBALS["gameName"] ?? ""),
           "horizon" => intval($T["horizon"]),
           "hookBudget" => intval($T["hooks"]),
           "pair" => "va", "seed" => $seedBase + $w * 31337]);
        if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
      }
      $kids[$pid] = [$resFile, $w];
    }
    $deadline = time() + intval($T["deadline_s"]);
    while (!empty($kids) && time() < $deadline) {
      $pid = pcntl_waitpid(-1, $status, WNOHANG);
      if ($pid > 0 && isset($kids[$pid])) {
        list($resFile, $w) = $kids[$pid];
        unset($kids[$pid]);
        $raw = @file_get_contents($resFile);
        @unlink($resFile);
        $res = $raw ? json_decode($raw, true) : null;
        if (is_array($res) && !isset($res["error"]) && !empty($res["finished"])) {
          $oc = floatval($res["outcome"]);
          if (intval($res["winner"] ?? -1) === 0) {
            // A drawn world -- horizon-ended or natural -- is
            // priced at the pinned horizon_value INSIDE the
            // candidate means (ruling sec.3.1). Unpinned, the
            // value is 0.0, the raw outcome: legacy behavior.
            $oc = floatval($T["horizon_value"]);
            ++$drawWorlds[$ci];
            if (!empty($res["horizon"])) {
              ++$hzWorlds[$ci];
              $lr = $res["life_root"] ?? null;
              $lo = $res["life_opp"] ?? null;
              if ($lr !== null && $lo !== null) {
                $lr = intval($lr); $lo = intval($lo);
                if ($lr > $lo) ++$hzLife[$ci]["ahead"];
                elseif ($lr < $lo) ++$hzLife[$ci]["behind"];
                else ++$hzLife[$ci]["tied"];
                $hzLife[$ci]["life_root_sum"] += $lr;
                $hzLife[$ci]["life_opp_sum"] += $lo;
              }
            }
          }
          $outcomes[$ci][$w] = $oc;
          $childFallbacks += intval($res["fallbacks"] ?? 0);
        } else {
          ++$errors;
          $rk = is_array($res) ? strval($res["error"] ?? "bad_result")
                               : "no_result";
          $abortReasons[$rk] = ($abortReasons[$rk] ?? 0) + 1;
          $abortByCand[$ci] = ($abortByCand[$ci] ?? 0) + 1;
        }
      } else { usleep(50000); }
    }
    foreach ($kids as $pid => $rw) {
      @posix_kill($pid, 9); @pcntl_waitpid($pid, $status); ++$errors;
    }
  }
  $means = []; $nWorlds = [];
  foreach ($sel as $ci) {
    $vals = array_values($outcomes[$ci] ?? []);
    $nWorlds[$ci] = count($vals);
    $means[$ci] = count($vals) ? array_sum($vals) / count($vals) : null;
  }
  $base = ["teacher" => 1, "contested" => 1, "det" => "file-v3",
    "det_persisted" => 1, "setting" => $T, "branch" => $branch,
    "player" => $player, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
    "ncand" => $ncand, "selected" => $sel, "prior_pick" => $priorPick,
    "means" => $means, "n_worlds" => $nWorlds,
    "n_horizon" => $hzWorlds, "n_draws" => $drawWorlds,
    "horizon_life" => $hzLife,
    "canary_worlds" => $canaryWorlds, "errors" => $errors,
    "child_fallbacks" => $childFallbacks,
    "ms" => intval((microtime(true) - $t0) * 1000)];
  if (($means[$priorPick] ?? null) === null || count($outcomes[$priorPick]) < 20) {
    $base["fallback"] = "thin_prior";
    $base["pick"] = $priorPick;
    SimSearch_LogStat($base);
    return $priorPick;
  }
  $best = $priorPick; $bestMean = $means[$priorPick];
  foreach ($sel as $ci) {
    if ($means[$ci] !== null && $means[$ci] > $bestMean) {
      $bestMean = $means[$ci]; $best = $ci;
    }
  }
  $pick = $priorPick; $overturn = 0; $meanD = null; $seD = null;
  if ($best !== $priorPick) {
    $ds = [];
    foreach ($outcomes[$best] as $w => $v) {
      if (isset($outcomes[$priorPick][$w])) {
        $ds[] = $v - $outcomes[$priorPick][$w];
      }
    }
    if (count($ds) >= 20) {
      $meanD = array_sum($ds) / count($ds);
      $var = 0.0;
      foreach ($ds as $d) { $var += ($d - $meanD) * ($d - $meanD); }
      $seD = sqrt($var / max(1, count($ds) - 1)) / sqrt(count($ds));
      if ($meanD > floatval($T["margin"]) * $seD) { $pick = $best; $overturn = 1; }
    }
  }
  $base["abort_reasons"] = $abortReasons;
  $base["abort_by_cand"] = $abortByCand;
  if (getenv("TEACHER_GHOST")) {
    // Pre-gate regression arm: full machinery, pick forced to the
    // prior's. The live game must stay action-identical to raw v15.
    $base["ghost"] = 1;
    $base["ghost_would_pick"] = $pick;
    $base["ghost_would_overturn"] = $overturn;
    $pick = $priorPick; $overturn = 0;
  }
  $base["priors"] = $priors;
  $base["pick"] = $pick; $base["overturn"] = $overturn;
  $base["mean_diff"] = $meanD; $base["se_diff"] = $seD;
  SimSearch_LogStat($base);
  $snapDir0 = getenv("TEACHER_SNAP_DIR");
  if ($overturn === 1 && $snapDir0 !== false && $snapDir0 !== "") {
    $gname = strval($GLOBALS["gameName"] ?? "");
    $GLOBALS["ssTeacherSnapCount"][$gname] =
      ($GLOBALS["ssTeacherSnapCount"][$gname] ?? 0) + 1;
    $hc = $GLOBALS["ssTeacherSnapCount"][$gname];
    $dst = rtrim($snapDir0, "/") . "/" . $gname . "_t" . $hc . "/";
    if (!is_dir($dst)) {
      SimSearch_CopyDir($gameDir, $dst);
      $st = null;
      try { $st = SimFeat_BuildState($player, $branch, $candRecs); }
      catch (Throwable $e) { $st = null; }
      file_put_contents(rtrim($snapDir0, "/") . "/teacher_snap_index.jsonl",
        json_encode(["snap" => $gname . "_t" . $hc, "game" => $gname,
          "hcount" => $hc, "branch" => $branch, "player" => $player,
          "turn" => intval($GLOBALS["currentTurn"] ?? 0),
          "cands" => $candRecs, "state" => $st,
          "teacher_pick" => $pick, "prior_pick" => $priorPick,
          "mean_diff" => $meanD, "se_diff" => $seD]) . "\n", FILE_APPEND);
    }
  }
  return $pick;
}

function SimSearch_RootDecide($branch, $cands, $candRecs, $player, $bridgeState = null) {
  $GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
  $t0 = microtime(true);
  $D = intval(getenv("ISMCTS_D") ?: 10);
  $S = intval(getenv("ISMCTS_S") ?: 12);
  $gameDir = $GLOBALS["filepath"] ?? "";
  $deckFiles = [1 => $gameDir . "p1Deck.txt", 2 => $gameDir . "p2Deck.txt"];
  // R14: the root canary runs AFTER the checkpoint block below -
  // see the note there. It used to run at this point, before the
  // sync, where its mixed store/view accounting reported in-transit
  // cards as missing.
  // Round-3 trace: PRE capture on the untouched live globals (the
  // state the bridge would featurize), before the checkpoint block.
  $trc = null;
  if (SimTrace_On() && empty($GLOBALS["simSearchChild"])
      && empty($GLOBALS["simLabelChild"])) {
    // R17: record the bridge's own state when Choose passed it;
    // only a legacy caller without one takes the old rebuild path.
    $stPre = $bridgeState;
    if ($stPre === null) {
      try { $stPre = SimFeat_BuildState($player, $branch, $candRecs); }
      catch (Throwable $e) { $stPre = null; }
    }
    $evPre = ($stPre !== null) ? SimSearch_Eval($stPre, $candRecs) : null;
    $trc = ["seq" => intval($GLOBALS["ssTraceDec"] ?? -1),
      "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "branch" => $branch, "player" => $player,
      "feat_pre_hash" => ($stPre !== null) ? SimTrace_Hash($stPre) : null,
      "priors_pre" => ($evPre !== null && isset($evPre[0])) ? $evPre[0] : null,
      "zone_pre" => SimTrace_ZoneHash(),
      "zone_store_pre" => SimTrace_StoreHash(),
      "rng_pre" => SimTrace_RngFingerprint(),
      "cand_hash" => SimTrace_CandHash($candRecs),
      "ncand" => count($candRecs), "state_pre" => $stPre];
  }
  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();
  $GLOBALS["skipWriteGamestate"] = false;
  SimSearch_IncludeWithGlobals("WriteGamestate.php");
  // R17: post-sync featurization of the same decision, logged on
  // the teacher trace row as feat_sync_hash - DIAGNOSTIC ONLY (the
  // census of sync-straddling decisions). It is not an equality
  // input: the within-row feat pair is pre vs post on the PASSED
  // bridge state, equal by construction.
  if ($trc !== null) {
    $stSync = null;
    try { $stSync = SimFeat_BuildState($player, $branch, $candRecs); }
    catch (Throwable $e) { $stSync = null; }
    $trc["feat_sync_hash"] = ($stSync !== null)
      ? SimTrace_Hash($stSync) : null;
  }
  // R14: root canary, single-source accounting. The sync above has
  // just made store == view, so the canary's store-preferring hidden
  // reads and its getter (view) reads describe the same world. A
  // refusal still returns null: the decision goes down the plain
  // bridge path, logs a bridge_pick trace row, and writes no teacher
  // trace row (the row is written only after Decide).
  if (!SimSearch_Canary($deckFiles)) {
    SimSearch_LogStat(["branch" => $branch, "fallback" => "canary",
                       "missing" => $GLOBALS["ssLastCanaryMissing"] ?? null]);
    return null;
  }
  // Phase 2b snapshot harvest (throwaway tree only): at sampled root
  // decisions, copy the checkpointed game dir + record the decision's
  // metadata so the labeler can determinize/restore it offline.
  $hvDir = getenv("HARVEST_DIR");
  if ($hvDir !== false && $hvDir !== "") {
    $gname = strval($GLOBALS["gameName"] ?? "");
    $GLOBALS["ssHarvestCount"][$gname] = ($GLOBALS["ssHarvestCount"][$gname] ?? 0) + 1;
    $hc = $GLOBALS["ssHarvestCount"][$gname];
    if (in_array($hc, [4, 11, 19, 28, 38, 49, 61, 74], true)) {
      $dst = rtrim($hvDir, "/") . "/" . $gname . "_" . $hc . "/";
      if (!is_dir($dst)) {
        SimSearch_CopyDir($gameDir, $dst);
        $st = null;
        try { $st = SimFeat_BuildState($player, $branch, $candRecs); } catch (Throwable $e) { $st = null; }
        file_put_contents(rtrim($hvDir, "/") . "/harvest_index.jsonl", json_encode([
          "snap" => $gname . "_" . $hc, "game" => $gname, "hcount" => $hc,
          "branch" => $branch, "player" => $player,
          "turn" => intval($GLOBALS["currentTurn"] ?? 0),
          "cands" => $candRecs, "state" => $st,
        ]) . "\n", FILE_APPEND);
      }
    }
  }
  if (getenv("TEACHER_MODE")) {
    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState);
    if ($trc !== null) {
      $post = $GLOBALS["ssTraceLastEval"] ?? [];
      $trc["feat_post_hash"] = $post["state_hash"] ?? null;
      $trc["priors_post"] = $post["priors"] ?? null;
      $trc["zone_post"] = SimTrace_ZoneHash();
      $trc["zone_store_post"] = SimTrace_StoreHash();
      $trc["rng_post"] = SimTrace_RngFingerprint();
      $trc["decide_pick"] = $pick;
      if ($pick === null) {
        // Abort-reason logging: this row is the marker (a teacher
        // row with no pick, twinned by Choose's bridge_pick at the
        // same seq). It now carries WHY Decide produced no pick.
        $trc["abort_reason"] = strval($GLOBALS["ssTeacherAbortReason"] ?? "decide_null");
      }
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
  }
  $seedBase = random_int(1, PHP_INT_MAX - 1000000);
  $parentGame = strval($GLOBALS["gameName"] ?? "");
  $children = [];
  for ($d = 0; $d < $D; ++$d) {
    $assignment = SimSearch_Determinize($player, $seedBase + $d * 31337);
    $resFile = sys_get_temp_dir() . "/ss_res_" . getmypid() . "_" . $d . ".json";
    @unlink($resFile);
    $pid = pcntl_fork();
    if ($pid === -1) continue;
    if ($pid === 0) {
      $rootKey = $branch . "|" . $player . "|" . implode(",", array_map(
        function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $candRecs));
      SimSearch_RunChild($d, $parentGame, $gameDir, $resFile, $assignment,
        ["S" => $S, "seedBase" => $seedBase, "rootPlayer" => $player,
         "rootKey" => $rootKey]);
      if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
    }
    $children[$pid] = $resFile;
  }
  $totVisits = []; $totW = []; $got = 0;
  $deadline = time() + 45;
  while (!empty($children) && time() < $deadline) {
    $pid = pcntl_waitpid(-1, $status, WNOHANG);
    if ($pid > 0 && isset($children[$pid])) {
      $resFile = $children[$pid];
      unset($children[$pid]);
      $raw = @file_get_contents($resFile);
      @unlink($resFile);
      if ($raw) {
        $res = json_decode($raw, true);
        if (is_array($res) && isset($res["visits"])) {
          ++$got;
          foreach ($res["visits"] as $ci => $n) {
            $totVisits[$ci] = ($totVisits[$ci] ?? 0) + intval($n);
            $totW[$ci] = ($totW[$ci] ?? 0.0) + floatval($res["wroot"][$ci] ?? 0.0) * intval($n);
          }
        }
      }
    } else {
      usleep(50000);
    }
  }
  foreach ($children as $pid => $resFile) {
    @posix_kill($pid, 9);
    @pcntl_waitpid($pid, $status);
    @unlink($resFile);
  }
  $ms = intval((microtime(true) - $t0) * 1000);
  if ($got === 0 || $totVisits === []) {
    SimSearch_LogStat(["branch" => $branch, "fallback" => "no_results", "ms" => $ms, "worlds" => $got]);
    return null;
  }
  // Root priors from the parent's own eval of the true state: the final
  // tie-break (spec: visits, then mean value, then prior argmax — never
  // list position; at S=1 all visits are zero and this IS the decision).
  $evRoot = SimSearch_EvalState($player, $branch, $candRecs);
  $priors = $evRoot ? $evRoot[0] : null;
  $best = -1; $bestV = -1; $bestW = -INF; $bestP = -INF;
  $ncand = count($candRecs);
  for ($ci = 0; $ci < $ncand; ++$ci) {
    $n = intval($totVisits[$ci] ?? 0);
    $w = $n > 0 ? floatval($totW[$ci] ?? 0.0) / $n : 0.0;
    $p = $priors !== null ? floatval($priors[$ci] ?? 0.0) : 0.0;
    if ($n > $bestV
        || ($n === $bestV && $w > $bestW)
        || ($n === $bestV && $w === $bestW && $p > $bestP)) {
      $bestV = $n; $bestW = $w; $bestP = $p; $best = $ci;
    }
  }
  $wrootLog = [];
  foreach ($totVisits as $ci => $n) {
    $wrootLog[$ci] = $n > 0 ? floatval($totW[$ci] ?? 0.0) / $n : 0.0;
  }
  SimSearch_LogStat(["branch" => $branch, "chosen" => $best, "visits" => $totVisits,
                     "priors" => $priors, "wroot" => $wrootLog,
                     "ms" => $ms, "worlds" => $got]);
  return $best >= 0 ? $best : null;
}

// ============================================================== labeler
// Phase 2b rollout labeling (throwaway tree). A rollout child restores a
// determinized snapshot, forces one root candidate, then plays the game
// out with a continuation pair: net seat SAMPLED from eval priors (private
// RNG), heuristic seat = argmax v1_score (exactly the eval opponent) or
// the provided v1 choice for DQ. Pair "vv" makes both seats net-sampled.

function SimLabel_SampleIdx($priors) {
  $u = SimSearch_XorNext() / 4294967296.0;
  $acc = 0.0;
  foreach ($priors as $i => $p) {
    $acc += floatval($p);
    if ($u <= $acc) return intval($i);
  }
  return count($priors) - 1;
}

function SimLabel_PriorArgmax($priors) {
  $best = 0; $bp = -INF;
  foreach ($priors as $i => $p) {
    $p = floatval($p);
    if ($p > $bp) { $bp = $p; $best = intval($i); }
  }
  return $best;
}

function SimLabel_V1Argmax($candRecs) {
  $best = 0; $bs = -INF;
  foreach ($candRecs as $i => $c) {
    $s = floatval($c["v1_score"] ?? 0.0);
    if ($s > $bs) { $bs = $s; $best = intval($i); }
  }
  return $best;
}

function SimLabel_ChildChoose($branch, $cands, $candRecs, $state, $gate) {
  $GLOBALS["ssHooks"] = ($GLOBALS["ssHooks"] ?? 0) + 1;
  if (($GLOBALS["ssHooks"] ?? 0) > intval($GLOBALS["ssLabelHookBudget"] ?? 4000)) throw new SimSearchAbort();
  if (!$gate || count($cands) === 0) return [true, null];
  $player = intval($GLOBALS["currentPlayer"] ?? 1);
  if (empty($GLOBALS["ssLabelRooted"])) {
    $key = $branch . "|" . $player . "|" . implode(",", array_map(
      function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $candRecs));
    if ($key !== strval($GLOBALS["ssLabelRootKey"] ?? "")) throw new SimSearchAbort();
    $GLOBALS["ssLabelRooted"] = true;
    $hcErr = SimSearch_HookCheck();
    if ($hcErr !== null) {
      $GLOBALS["ssLabelError"] = $hcErr;
      throw new SimSearchAbort();
    }
    $fi = intval($GLOBALS["ssLabelForceIdx"] ?? 0);
    if ($fi < 0 || $fi >= count($cands)) $fi = 0;
    return [true, $cands[$fi]];
  }
  // Capture the first root-player branch state after the forced move:
  // the child state for the advantage study.
  if ($player === intval($GLOBALS["ssRootPlayer"])
      && empty($GLOBALS["ssLabelChildState"])) {
    $GLOBALS["ssLabelChildState"] = $state;
  }
  $netSeat = ($GLOBALS["ssLabelPair"] ?? "vh") === "vv"
    ? true : ($player === intval($GLOBALS["ssRootPlayer"]));
  if (!$netSeat) {
    return [true, $cands[SimLabel_V1Argmax($candRecs)]];
  }
  if (count($cands) === 1) return [true, $cands[0]];
  try { SimFeat_Canary($player, $state); } catch (Throwable $e) {
    $GLOBALS["ssLabelFallbacks"] = ($GLOBALS["ssLabelFallbacks"] ?? 0) + 1;
    return [true, $cands[SimLabel_V1Argmax($candRecs)]];
  }
  $ev = SimSearch_Eval($state, $candRecs);
  if (!$ev) {
    $GLOBALS["ssLabelFallbacks"] = ($GLOBALS["ssLabelFallbacks"] ?? 0) + 1;
    return [true, $cands[SimLabel_V1Argmax($candRecs)]];
  }
  $pairNow = strval($GLOBALS["ssLabelPair"] ?? "vh");
  $pickIdx = $pairNow === "va" ? SimLabel_PriorArgmax($ev[0])
                               : SimLabel_SampleIdx($ev[0]);
  return [true, $cands[$pickIdx]];
}

function SimLabel_ChildDQ($player, $candRecs, $state, $options, $v1choice) {
  $GLOBALS["ssHooks"] = ($GLOBALS["ssHooks"] ?? 0) + 1;
  if (($GLOBALS["ssHooks"] ?? 0) > intval($GLOBALS["ssLabelHookBudget"] ?? 4000)) throw new SimSearchAbort();
  $netSeat = ($GLOBALS["ssLabelPair"] ?? "vh") === "vv"
    ? true : (intval($player) === intval($GLOBALS["ssRootPlayer"]));
  if (!$netSeat) return $v1choice;
  try { SimFeat_Canary(intval($player), $state); } catch (Throwable $e) { return $v1choice; }
  $ev = SimSearch_Eval($state, $candRecs);
  if (!$ev) return $v1choice;
  $pairNow = strval($GLOBALS["ssLabelPair"] ?? "vh");
  $pickIdx = $pairNow === "va" ? SimLabel_PriorArgmax($ev[0])
                               : SimLabel_SampleIdx($ev[0]);
  return $options[$pickIdx] ?? $v1choice;
}

// Runs inside a forked child. Never returns.
function SimLabel_RunRollout($snapDir, $resFile, $assignment, $cfg) {
  try {
    SimSearch_DropInheritedSockets();
    $GLOBALS["simLabelChild"] = true;
    $childGame = (string)random_int(100000000, 999999999);
    $workDir = ($GLOBALS["ssGamesRoot"] ?? "./Games/") . $childGame . "/";
    SimSearch_CopyChildDir($snapDir, $workDir);
    $GLOBALS["gameName"] = $childGame;
    $GLOBALS["filepath"] = $workDir;
    $GLOBALS["filename"] = $workDir . "gamestate.txt";
    $GLOBALS["logWriteBuffer"] = [];
    $root = intval($cfg["rootPlayer"]);
    // Round-9 D7: run-pinned rollout horizon (absolute currentTurn);
    // 0 = off, the registered label instrument unchanged.
    $horizon = intval($cfg["horizon"] ?? 0);
    $horizonHit = false;
    $GLOBALS["ssRootPlayer"] = $root;
    $GLOBALS["ssLabelRootKey"] = strval($cfg["rootKey"] ?? "");
    $GLOBALS["ssLabelForceIdx"] = intval($cfg["forceIdx"] ?? 0);
    $GLOBALS["ssLabelPair"] = strval($cfg["pair"] ?? "vh");
    $GLOBALS["ssLabelRooted"] = false;
    $GLOBALS["ssLabelChildState"] = null;
    $GLOBALS["ssLabelFallbacks"] = 0;
    $GLOBALS["ssLabelHookBudget"] = intval($cfg["hookBudget"] ?? 4000);
    $GLOBALS["ssHooks"] = 0;
    if (!SimSearch_ApplyAssignmentToFile($workDir, $assignment)) {
      @file_put_contents($resFile, json_encode(["error" => "det_persist_failed"]));
      SimSearch_WipeDir($workDir);
      if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
    }
    ParseGamestate();
    if (!SimSearch_VerifyAssignment($assignment)) {
      @file_put_contents($resFile, json_encode(["error" => "det_verify_failed"]));
      SimSearch_WipeDir($workDir);
      if (function_exists("DeleteCache")) DeleteCache($childGame);
      if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
    }
    $GLOBALS["ssAssignment"] = $assignment;
    mt_srand(intval($cfg["seed"]));
    SimSearch_SeedShuffle(intval($cfg["seed"]) ^ 0x51ab);
    try {
      $guard = 0; $lastKey = ""; $stuck = 0;
      while (!IsGameOver() && $guard < 400) {
        ++$guard;
        $pl = $GLOBALS["currentPlayer"] ?? 1;
        PuzzleBeginStep($pl);
        for ($k = 0; $k < 20 && !IsGameOver(); ++$k) {
          PuzzleFinishStep();
          // Sec.14 horizon alignment: check after EACH
          // finish step, as the live instrument checks
          // its cap (play_game.php: "a drive step can
          // span dozens of turns, so checking only per
          // drive step overshoots the cap"). The
          // once-per-iteration check that stood here
          // (and remains after the loop below) let a
          // world run up to 20 finish steps past the
          // trigger between checks.
          if ($horizon > 0 && intval($GLOBALS["currentTurn"] ?? 0) >= $horizon) { $horizonHit = true; break; }
        }
        $key = SimStateHash($GLOBALS["lastWrittenGamestate"] ?? "", $GLOBALS["p1Key"] ?? "");
        if ($key === $lastKey) { if (++$stuck > 60) break; }
        else { $stuck = 0; $lastKey = $key; }
        if ($horizon > 0 && intval($GLOBALS["currentTurn"] ?? 0) >= $horizon) { $horizonHit = true; break; }
      }
    } catch (SimSearchAbort $e) {
      @file_put_contents($resFile, json_encode(["error" => $GLOBALS["ssLabelError"] ?? "abort"]));
      SimSearch_WipeDir($workDir);
      if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
    }
    // Sec.14: horizonHit overrides a same-step win. If
    // the step that first carried currentTurn to the
    // trigger also ended the game, the live instrument
    // scores that game a draw (its per-step cap check
    // sets $draw and $winner = $draw ? 0 : ...), so a
    // decisive result is recorded only when the game
    // ended at currentTurn < horizon. The pre-fix form
    // (horizonApplied = horizonHit && !IsGameOver())
    // recorded such a world as decisive at turns >=
    // horizon -- an outcome the real game cannot
    // produce.
    $horizonApplied = $horizonHit ? 1 : 0;
    $winner = ($horizonApplied === 1) ? 0
      : (IsGameOver() ? intval($GLOBALS["winner"] ?? 0) : 0);
    $outcome = $winner === 0 ? 0.0 : ($winner === $root ? 1.0 : -1.0);
    $resOut = [
      "det_persisted" => 1,
      "winner" => $winner, "outcome" => $outcome,
      "horizon" => $horizonApplied,
      "finished" => (IsGameOver() || $horizonApplied) ? 1 : 0,
      "turns" => intval($GLOBALS["currentTurn"] ?? 0),
      "hooks" => intval($GLOBALS["ssHooks"] ?? 0),
      "fallbacks" => intval($GLOBALS["ssLabelFallbacks"] ?? 0),
      "child_state" => $GLOBALS["ssLabelChildState"],
    ];
    if ($horizonApplied === 1) {
      // Ruling sec.3.2: both players' life totals on every
      // horizon-ended world, root frame (life_root = the root
      // player's life, life_opp = the opponent's), read through
      // GetHealth -- the same accessor play_game's result JSON
      // uses for p1life/p2life. The life-differential price
      // (ahead = win, behind = loss, tied = draw at the read's
      // draw price) is computed from these two fields by the
      // analyzers; the raw outcome stays the instrument's draw.
      $resOut["life_root"] = function_exists("GetHealth")
        ? intval(GetHealth($root)) : null;
      $resOut["life_opp"] = function_exists("GetHealth")
        ? intval(GetHealth(3 - $root)) : null;
    }
    @file_put_contents($resFile, json_encode($resOut));
    SimSearch_WipeDir($workDir);
    if (function_exists("DeleteCache")) DeleteCache($childGame);
  } catch (Throwable $e) {
    @file_put_contents($resFile, json_encode(["error" => $e->getMessage()]));
  }
  if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
}

// Parent side (runs in the play_game process under LABEL_MODE): label one
// snapshot across W determinized worlds x up to CAP candidates.
function SimLabel_RunForSnapshot($snapDir, $meta, $cfg) {
  $dbg = function($m) { if (getenv("LABEL_DEBUG")) fwrite(STDERR, "LBL " . $m . "\n"); };
  $dbg("enter cwd=" . getcwd());
  $GLOBALS["ssGamesRoot"] = getcwd() . "/Games/";
  $root = intval($meta["player"]);
  $scratch = getcwd() . "/Games/label_scratch/";
  $dbg("wiping scratch");
  SimSearch_WipeDir($scratch);
  SimSearch_CopyDir(rtrim($snapDir, "/") . "/", $scratch);
  // ParseGamestate.php self-executes a parse and guards on a NUMERIC
  // global $gameName (a bare exit otherwise): point filename/filepath at
  // the snapshot copy under its own game id for the include, then switch
  // to the scratch dir for the working parse.
  $snapGameDir = ($GLOBALS["ssGamesRoot"] ?? (getcwd() . "/Games/")) . strval($meta["game"]) . "/";
  SimSearch_WipeDir($snapGameDir);
  SimSearch_CopyDir(rtrim($snapDir, "/") . "/", $snapGameDir);
  $GLOBALS["gameName"] = strval($meta["game"]);
  $GLOBALS["filepath"] = $snapGameDir;
  $GLOBALS["filename"] = $snapGameDir . "gamestate.txt";
  $GLOBALS["logWriteBuffer"] = [];
  // ParseGamestate reads the SHMOP cache BEFORE the file: a segment
  // left by the snapshot's original game (e.g. one killed mid-run,
  // whose CloseGame never deleted it) would silently replace the
  // snapshot state. Clear it so the driver parses the FILE.
  if (function_exists("DeleteCache")) DeleteCache(strval($meta["game"]));
  if (!function_exists("ParseGamestate")) {
    SimSearch_IncludeWithGlobals("ParseGamestate.php");
    $GLOBALS["gameName"] = strval($meta["game"]);
    $GLOBALS["filepath"] = $snapGameDir;
    $GLOBALS["filename"] = $snapGameDir . "gamestate.txt";
  }
  $dbg("copy done, parsing");
  ParseGamestate();
  $dbg("parsed turn=" . strval($GLOBALS["currentTurn"] ?? "?"));
  $rootKey = strval($meta["branch"]) . "|" . $root . "|" . implode(",", array_map(
    function ($c) { return strval($c["card_id"]) . "@" . strval($c["zone"]); }, $meta["cands"]));
  $W = intval($cfg["W"]); $cap = intval($cfg["cap"]);
  $ncand = min(count($meta["cands"]), $cap);
  $out = [];
  $dbg("rootkey=" . $rootKey);
  $ciList = $cfg["candIdx"] ?? null;
  if (!is_array($ciList)) $ciList = range(0, $ncand - 1);
  foreach ($ciList as $ci) {
    $ci = intval($ci);
    if ($ci < 0 || $ci >= $ncand) continue;
    $kids = [];
    for ($w = 0; $w < $W; ++$w) {
      $seed = intval($cfg["seedBase"]) + $w * 31337;
      $assignment = SimSearch_Determinize($root, $seed);
      $dbg("det ci=" . $ci . " w=" . $w . " ok=" . (is_array($assignment) ? "y" : "n"));
      $resFile = sys_get_temp_dir() . "/lab_res_" . getmypid() . "_" . bin2hex(random_bytes(4)) . "_" . $ci . "_" . $w . ".json";
      @unlink($resFile);
      $pid = pcntl_fork();
      if ($pid === -1) continue;
      if ($pid === 0) {
        SimLabel_RunRollout(rtrim($snapDir, "/") . "/", $resFile, $assignment,
          ["rootPlayer" => $root, "rootKey" => $rootKey, "forceIdx" => $ci,
           "snapGame" => strval($meta["game"]),
           "horizon" => intval($cfg["horizon"] ?? 0),
           "hookBudget" => intval($cfg["hookBudget"] ?? 4000),
           "pair" => strval($cfg["pair"]), "seed" => $seed]);
        if (function_exists("posix_kill")) posix_kill(posix_getpid(), 9); exit(0);
      }
      $kids[$pid] = [$resFile, $w];
    }
    $deadline = time() + intval($cfg["deadlineS"] ?? 300);
    while (!empty($kids) && time() < $deadline) {
      $pid = pcntl_waitpid(-1, $status, WNOHANG);
      if ($pid > 0 && isset($kids[$pid])) {
        list($resFile, $w) = $kids[$pid];
        unset($kids[$pid]);
        $raw = @file_get_contents($resFile);
        @unlink($resFile);
        $res = $raw ? json_decode($raw, true) : null;
        $out[] = ["snap" => $meta["snap"], "cand" => $ci, "world" => $w,
                  "result" => $res];
      } else {
        usleep(50000);
      }
    }
    foreach ($kids as $pid => $rw) {
      @posix_kill($pid, 9);
      @pcntl_waitpid($pid, $status);
      $out[] = ["snap" => $meta["snap"], "cand" => $ci, "world" => $rw[1],
                "result" => ["error" => "timeout"]];
    }
  }
  SimSearch_WipeDir($scratch);
  if (isset($snapGameDir)) SimSearch_WipeDir($snapGameDir);
  return $out;
}
