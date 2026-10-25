<?php
// featurize.php — Phase A: per-seat masked state featurization for the
// PHP/Python policy bridge.
//
// SimFeat_BuildState($player, $branch, $candidates) returns a plain array
// describing everything the acting player legally knows:
//   - own hand (card IDs, padded to intellect)
//   - own remaining deck composition (counts by card — never order)
//   - public board: allies/auras/items/character for BOTH players,
//     graveyard + banish + pitch counts for both (public zones)
//   - own arsenal (known to its owner)
//   - combat chain snapshot, life totals, action points, turn, resources
//   - legal actions enumerated with indices (= $candidates)
//
// STRICT FAIR-PLAY: opponent hand, opponent deck order/content, and opponent
// arsenal are NEVER read here. SimFeat_Canary() enforces this after the fact
// with count-based reasoning: every card occurrence serialized in the state
// must be explainable by a legally-readable zone (same getters as the
// featurizer). Masking is our discipline — the engine exposes everything via
// globals, so the canary is the enforcement. See the canary section below.

function SimFeat_ZoneIDs($arr, $pieces) {
  $ids = [];
  $n = is_array($arr) ? count($arr) : 0;
  for ($i = 0; $i + $pieces - 1 < $n; $i += $pieces) {
    $cid = $arr[$i] ?? "";
    if ($cid !== "" && $cid !== null) $ids[] = strval($cid);
  }
  return $ids;
}

function SimFeat_Counts($ids) {
  $c = [];
  foreach ($ids as $id) $c[$id] = ($c[$id] ?? 0) + 1;
  return $c;
}

function SimFeat_BoardSide($p) {
  $allies = &GetAllies($p);
  $auras = &GetAuras($p);
  $items = &GetItems($p);
  $char = &GetPlayerCharacter($p);
  $allyIDs = SimFeat_ZoneIDs($allies, AllyPieces());
  $allyPower = [];
  foreach ($allyIDs as $cid) {
    try { $allyPower[$cid] = intval(PowerValue($cid, $p, "PLAY", -1, false, false)); }
    catch (Throwable $e) { $allyPower[$cid] = 0; }
  }
  return [
    "allies" => $allyIDs,
    "ally_power" => $allyPower,
    "auras" => SimFeat_ZoneIDs($auras, AuraPieces()),
    "items" => SimFeat_ZoneIDs($items, ItemPieces()),
    "character" => SimFeat_ZoneIDs($char, CharacterPieces()),
    "graveyard" => SimFeat_Counts(SimFeat_ZoneIDs(GetDiscard($p), DiscardPieces())),
    "banished" => SimFeat_Counts(SimFeat_ZoneIDs(GetBanish($p), BanishPieces())),
    "pitch" => SimFeat_ZoneIDs(GetPitch($p), PitchPieces()),
  ];
}

function SimFeat_DeckIDs($player) {
  // Round-8 (b) correction: the deck zone read through the getter
  // VIEW (GetDeck, CardGetters.php - the same getter family every
  // other zone in this file is read through), with the featurizer's
  // own per-zone treatment (ZoneIDs with DeckPieces()). Before this
  // correction the two deck-count reads below used SimV1_DeckCards,
  // which reads the STORE globals ($p1Deck/$p2Deck, policy_v1.php).
  // SimV1_DeckCards itself is NOT changed: the heuristic's own
  // deck-awareness (policy_v1.php) keeps reading the store; only the
  // featurizer's reads move to the view.
  $deck = &GetDeck($player);
  return SimFeat_ZoneIDs($deck, DeckPieces());
}

function SimFeat_BuildState($player, $branch, $candidates) {
  $player = intval($player);
  $hand = &GetHand($player);
  $handIDs = [];
  foreach ($hand as $cid) if ($cid !== "" && $cid !== null) $handIDs[] = strval($cid);
  $char = &GetPlayerCharacter($player);
  $intellect = 4;
  try { $intellect = max(1, intval(CharacterIntellect($char[0] ?? ""))); } catch (Throwable $e) {}
  $padded = $handIDs;
  while (count($padded) < $intellect) $padded[] = "";
  $res = &GetResources($player);
  // Combat chain snapshot (public).
  $chainCount = 0; $attackID = "";
  try {
    $cc = $GLOBALS["combatChain"] ?? [];
    if (is_array($cc)) {
      $pieces = function_exists("CombatChainPieces") ? CombatChainPieces() : 12;
      $chainCount = intdiv(count($cc), max(1, $pieces));
      if (count($cc) > 0 && ($cc[0] ?? "") !== "") $attackID = strval($cc[0]);
    }
  } catch (Throwable $e) {}
  $arsenalIDs = SimFeat_ZoneIDs(GetArsenal($player), ArsenalPieces());
  $state = [
    "v" => 1,
    "player" => $player,
    "branch" => strval($branch),
    "turn" => intval($GLOBALS["currentTurn"] ?? 0),
    "first_player" => intval($GLOBALS["firstPlayer"] ?? 0),
    "main_player" => intval($GLOBALS["mainPlayer"] ?? 0),
    "action_points" => intval($GLOBALS["actionPoints"] ?? 0),
    "life" => [intval(GetHealth(1)), intval(GetHealth(2))],
    "resources" => max(0, intval($res[0] ?? 0)),
    "hand" => array_slice($padded, 0, $intellect),
    "hand_size" => count($handIDs),
    "intellect" => $intellect,
    "arsenal" => $arsenalIDs,
    "deck_counts" => SimFeat_Counts(SimFeat_DeckIDs($player)),
    "board" => [1 => SimFeat_BoardSide(1), 2 => SimFeat_BoardSide(2)],
    "chain_links" => $chainCount,
    "chain_attack" => $attackID,
    "candidates" => array_values(array_map(function ($c, $i) {
      return [
        "index" => $i,
        "card_id" => strval($c["card_id"] ?? ""),
        "zone" => strval($c["zone"] ?? ""),
        "v1_score" => floatval($c["v1_score"] ?? 0),
      ];
    }, $candidates, array_keys($candidates))),
  ];
  return $state;
}

// ---------- fair-play canary ----------
//
// Threat model: the engine exposes EVERYTHING via globals, so masking is our
// discipline. If a future edit adds a hidden-zone read (opponent hand/deck/
// arsenal) to the featurizer, the canary must scream.
//
// Design: count-based, not string-match-based. Card IDs are NOT unique per
// copy (both players can hold Phoenix Flame), so naive string matching false-
// positives. Instead:
//   SimFeat_LegalCounts($player) = cardID => count across every zone the
//     featurizer is allowed to read (own hand/deck/arsenal + both players'
//     public zones + combat chain), using the SAME helpers as the featurizer.
//   SimFeat_StateCounts($state) = cardID => count as serialized in the state
//     array, per the known schema. (Candidates are NOT double-counted: they
//     are a selection among already-counted cards.)
// Every occurrence in the state must be explainable by a legal zone:
// seen[id] > legal[id] for any id => LEAK, throw loudly.
// Fail-closed: if someone adds a zone to features without adding it to
// SimFeat_LegalCounts, the canary false-positives in testing until both are
// updated. Residual gaps (documented): own deck ORDER (we only send counts),
// non-ID leaks (e.g. a new scalar revealing hidden info) — those need review,
// not string matching.

function SimFeat_MergeCounts(&$into, $counts) {
  foreach ($counts as $id => $n) {
    if ($id === "" || $id === null) continue;
    $into[strval($id)] = ($into[strval($id)] ?? 0) + intval($n);
  }
}

function SimFeat_LegalCounts($player) {
  $player = intval($player);
  $legal = [];
  $hand = &GetHand($player);
  SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs($hand, HandPieces())));
  SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_DeckIDs($player)));
  SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetArsenal($player), ArsenalPieces())));
  foreach ([1, 2] as $q) {
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetAllies($q), AllyPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetAuras($q), AuraPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetItems($q), ItemPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetPlayerCharacter($q), CharacterPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetDiscard($q), DiscardPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetBanish($q), BanishPieces())));
    SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetPitch($q), PitchPieces())));
  }
  try {
    $cc = $GLOBALS["combatChain"] ?? [];
    if (is_array($cc) && count($cc) > 0 && ($cc[0] ?? "") !== "") {
      $id = strval($cc[0]);
      $legal[$id] = ($legal[$id] ?? 0) + 1;
    }
  } catch (Throwable $e) {}
  return $legal;
}

function SimFeat_StateCounts($state) {
  $seen = [];
  $addIDs = function ($ids) use (&$seen) {
    if (!is_array($ids)) return;
    foreach ($ids as $id) {
      if ($id === "" || $id === null) continue;
      $id = strval($id);
      $seen[$id] = ($seen[$id] ?? 0) + 1;
    }
  };
  $addMap = function ($map) use (&$seen) {
    if (!is_array($map)) return;
    foreach ($map as $id => $n) {
      if ($id === "" || $id === null) continue;
      $id = strval($id);
      $seen[$id] = ($seen[$id] ?? 0) + intval($n);
    }
  };
  $addIDs($state["hand"] ?? []);
  $addIDs($state["arsenal"] ?? []);
  $addMap($state["deck_counts"] ?? []);
  foreach ([1, 2] as $q) {
    $b = $state["board"][$q] ?? [];
    foreach (["allies", "auras", "items", "character", "pitch"] as $k) $addIDs($b[$k] ?? []);
    foreach (["graveyard", "banished"] as $k) $addMap($b[$k] ?? []);
  }
  if (($state["chain_attack"] ?? "") !== "") $addIDs([$state["chain_attack"]]);
  // NOTE: candidates intentionally not counted (selection among counted cards).
  return $seen;
}

// Canary: fail loudly if any card occurrence in the state is not explainable
// by a legally-readable zone. Takes the STATE ARRAY (not JSON).
function SimFeat_Canary($player, $state) {
  if (!is_array($state)) throw new Exception("SimFeat_Canary: state is not an array");
  $legal = SimFeat_LegalCounts(intval($player));
  $seen = SimFeat_StateCounts($state);
  $leaks = [];
  foreach ($seen as $id => $n) {
    $ok = intval($legal[$id] ?? 0);
    if ($n > $ok) $leaks[] = "$id x$n (legal x$ok)";
  }
  if ($leaks !== []) {
    $msg = "SimFeat_Canary LEAK for player " . intval($player) . ": " . implode(", ", $leaks);
    fwrite(STDERR, $msg . "\n");
    throw new Exception($msg);
  }
  return true;
}
