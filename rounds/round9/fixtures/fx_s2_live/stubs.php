<?php
// fx_s2_live fixture stubs: the vendor / featurize / bootstrap
// functions that code/search_s2.php CALLS but does not define,
// given planted implementations so the REAL build's live Decide
// path (SimTeacher_Decide -> SimTeacher_DecideInner -> forked
// SimLabel_RunRollout children) and the REAL label parent
// (SimLabel_RunForSnapshot) run end to end in this fixture.
//
// The stub boundary is the engine's own interface:
//   * zone getters (GetDeck/GetHand/GetArsenal/...) return
//     references to the canonical $p{N}{Zone} globals, exactly
//     as the vendor's; ParseGamestate populates those globals
//     FROM the gamestate.txt file on disk (the same zone line
//     indices SimSearch_ApplyAssignmentToFile edits: p1 hand 1,
//     deck 2, arsenal 5; p2 hand 19, deck 20, arsenal 23), so the
//     determinization file-edit + verify leg runs for real.
//   * PuzzleBeginStep is the scripted engine: the first call in
//     a rollout child makes the REAL rooted SimLabel_ChildChoose
//     call (root key check + SimSearch_HookCheck canary, both
//     real code), later calls advance the planted world script
//     selected by $GLOBALS["fxBehavior"][forceIdx]:
//       "lose"  - opponent wins at step 2 (outcome -1)
//       "win"   - root wins at step 2 (outcome +1)
//       "draw"  - nobody wins; currentTurn advances 7/step
//                 until the horizon check fires (if armed);
//                 life totals planted via $GLOBALS["fxHealth"]
//       "hooks" - step 1 burns 5,999 extra hook calls through
//                 the REAL SimLabel_ChildChoose (6,000 total
//                 with the rooted call), step 2 root wins:
//                 completes iff the hook budget exceeds 6,000.
//   * SimSearch_Eval is NOT stubbed: it runs for real against a
//     fake policy server (fx_server.php) on the socket path
//     SimPolicyServer_SockPath() returns here.
//   * SimFeat_Canary is a no-op: the hidden-information canary
//     is exercised by the production runs and the pre-gate, not
//     by this fixture, whose subject is valuation, pinning, the
//     hook guard, and life recording. SimSearch_HookCheck's
//     determinization canary DOES run for real (it is inside
//     search_s2.php): the fixture's p{N}Deck.txt files list
//     exactly the planted pool cards, so the missing-card leg
//     passes by construction of the fixture state.

function &fx_zone_ref($player, $zone) {
  $v = "p" . intval($player) . ucfirst($zone);
  if (!isset($GLOBALS[$v]) || !is_array($GLOBALS[$v])) $GLOBALS[$v] = [];
  return $GLOBALS[$v];
}
function &GetDeck($p) { $r = &fx_zone_ref($p, "deck"); return $r; }
function &GetHand($p) { $r = &fx_zone_ref($p, "hand"); return $r; }
function &GetArsenal($p) { $r = &fx_zone_ref($p, "arsenal"); return $r; }
function &GetDiscard($p) { $r = &fx_zone_ref($p, "discard"); return $r; }
function &GetBanish($p) { $r = &fx_zone_ref($p, "banish"); return $r; }
function &GetPitch($p) { $r = &fx_zone_ref($p, "pitch"); return $r; }
function &GetAllies($p) { $r = &fx_zone_ref($p, "allies"); return $r; }
function &GetAuras($p) { $r = &fx_zone_ref($p, "auras"); return $r; }
function &GetItems($p) { $r = &fx_zone_ref($p, "items"); return $r; }
function &GetPlayerCharacter($p) { $r = &fx_zone_ref($p, "character"); return $r; }

function ArsenalPieces() { return 7; }
function DiscardPieces() { return 1; }
function BanishPieces() { return 1; }
function PitchPieces() { return 1; }
function AllyPieces() { return 1; }
function AuraPieces() { return 1; }
function ItemPieces() { return 1; }
function CharacterPieces() { return 1; }

// Featurize zone-ID extraction at a stride (fixture form: the
// planted public zones are empty, so this is only reached with
// empty arrays in practice).
function SimFeat_ZoneIDs($arr, $pieces) {
  $ids = [];
  $n = is_array($arr) ? count($arr) : 0;
  for ($i = 0; $i < $n; $i += max(1, intval($pieces))) {
    if (($arr[$i] ?? "") !== "") $ids[] = strval($arr[$i]);
  }
  return $ids;
}
function SimFeat_Canary($player, $state) { /* no-op, see header */ }
function SimFeat_BuildState($player, $branch, $candRecs) {
  return ["fx" => "built"];
}

function SimPolicyServer_SockPath() {
  return strval($GLOBALS["fxSockPath"] ?? "/tmp/fx_s2_no_sock");
}
function SimTrace_On() { return false; }
function SimTrace_Hash($s) { return "fx"; }

function GetHealth($p) {
  $h = $GLOBALS["playerHealths"] ?? [20, 20];
  return intval($h[intval($p) - 1] ?? 0);
}

function DeleteCache($g) { /* fixture: no SHMOP cache */ }
function IsGameOver() { return intval($GLOBALS["winner"] ?? 0) !== 0; }
function SimStateHash($s, $k) {
  return "fxh" . strval(intval($GLOBALS["fxStep"] ?? 0)) . "_" .
         strval(intval($GLOBALS["currentTurn"] ?? 0));
}

// Parse the planted gamestate.txt into the canonical zone
// globals (the vendor's line indices, as documented in
// SimSearch_ApplyAssignmentToFile). Turn / health come from the
// harness's planted globals, as a real parse would derive them
// from the full serialization this fixture does not model.
function ParseGamestate() {
  $file = strval($GLOBALS["filename"] ?? "");
  $raw = $file !== "" ? @file_get_contents($file) : false;
  $lines = $raw === false ? [] : explode("\r\n", $raw);
  $zone = function ($idx) use ($lines) {
    if (!isset($lines[$idx]) || trim($lines[$idx]) === "") return [];
    return array_values(array_filter(
      explode(" ", trim($lines[$idx])),
      function ($x) { return $x !== ""; }));
  };
  $GLOBALS["p1Hand"] = $zone(1);
  $GLOBALS["p1Deck"] = $zone(2);
  $GLOBALS["p1Arsenal"] = $zone(5);
  $GLOBALS["p2Hand"] = $zone(19);
  $GLOBALS["p2Deck"] = $zone(20);
  $GLOBALS["p2Arsenal"] = $zone(23);
  $GLOBALS["currentTurn"] = intval($GLOBALS["fxStartTurn"] ?? 40);
  $GLOBALS["currentPlayer"] = 1;
  $GLOBALS["playerHealths"] = $GLOBALS["fxHealth"] ?? [20, 20];
  $GLOBALS["winner"] = 0;
  $GLOBALS["lastWrittenGamestate"] = "fx";
  $GLOBALS["p1Key"] = "fxk";
  $GLOBALS["fxStep"] = 0;
}

function PuzzleBeginStep($pl) {
  $GLOBALS["fxStep"] = intval($GLOBALS["fxStep"] ?? 0) + 1;
  $step = $GLOBALS["fxStep"];
  if (empty($GLOBALS["fxRooted"])) {
    $GLOBALS["fxRooted"] = true;
    // The engine's first decision in the rollout is the root
    // decision itself: make the REAL label hook call, which
    // checks the root key, runs the determinization canary,
    // and returns the forced candidate.
    SimLabel_ChildChoose(
      strval($GLOBALS["fxRootBranch"] ?? "M"),
      $GLOBALS["fxRootCands"] ?? [0],
      $GLOBALS["fxRootCandRecs"] ?? [],
      ["fx" => "root"], true);
    return;
  }
  $fi = intval($GLOBALS["ssLabelForceIdx"] ?? 0);
  $beh = strval(($GLOBALS["fxBehavior"] ?? [])[$fi] ?? "win");
  $root = intval($GLOBALS["ssRootPlayer"] ?? 1);
  if ($beh === "draw") {
    $GLOBALS["currentTurn"] = intval($GLOBALS["currentTurn"] ?? 0) + 7;
    return;
  }
  if ($beh === "hooks") {
    if ($step === 2) {
      // Burn hooks through the real guard: 5,999 single-
      // candidate calls (each +1 hook, no eval at count 1).
      for ($i = 0; $i < 5999; ++$i) {
        SimLabel_ChildChoose("M", [0],
          [["card_id" => "fxD", "zone" => "hand"]],
          ["fx" => "dummy"], true);
      }
    } elseif ($step === 3) {
      $GLOBALS["winner"] = $root;
    }
    return;
  }
  if ($step === 2) {
    $GLOBALS["winner"] = ($beh === "win") ? $root : 3 - $root;
    $GLOBALS["currentTurn"] = intval($GLOBALS["currentTurn"] ?? 0) + 1;
  }
}
function PuzzleFinishStep() { /* scripted engine: nothing */ }
