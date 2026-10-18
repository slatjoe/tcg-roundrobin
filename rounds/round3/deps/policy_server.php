<?php
// policy_server.php — Phase A: PHP side of the PHP/Python policy bridge.
//
// When play_game.php gets --policy-server, decision routing goes through
// here instead of the in-process v1 path:
//
//   SimPolicyServer_Choose($branch, ...)  — called from hooks in
//     vendor/talishar/AI/EncounterAI.php for the candidate-choice branches
//     (B=block, M=main action, M_END=end-of-turn ability, A=attack reaction,
//     D=defense reaction, P=pitch, ARS=arsenal). Replicates each branch's
//     candidate collection (GeneratePriorityValues + playability filter +
//     gating) EXACTLY, then asks the Python server for the chosen index.
//   SimPolicyServer_DecisionOption(...) — called from the
//     BotChooseDecisionOption dispatcher hook; routes decision-queue choices.
//
// Phase A fidelity: v1 scores are computed in-process by the REAL
// SimV1_Priority code path (via GeneratePriorityValues) and shipped with the
// candidates; the Python server returns argmax(v1_score), which reproduces
// v1's choice bit-for-bit. The bridge proves the plumbing; the featurizer
// output + trajectory logs are what Phase B builds on.
//
// Protocol: unix socket ($TCG_POLICY_SOCK or /tmp/tcg_policy.sock),
// 4-byte big-endian length prefix + JSON. One persistent connection per
// worker process. On socket failure: reconnect once, then fall back to the
// in-process v1 choice and count the fallback (a nonzero fallback count
// invalidates a fidelity batch — see SimPolicyServer_Stats()).

function SimPolicyServer_SockPath() {
  $p = getenv("TCG_POLICY_SOCK");
  return ($p === false || $p === "") ? "/tmp/tcg_policy.sock" : $p;
}

function SimPolicyServer_Connect() {
  if (isset($GLOBALS["simPolicySock"]) && is_resource($GLOBALS["simPolicySock"])) {
    return $GLOBALS["simPolicySock"];
  }
  $sock = @stream_socket_client("unix://" . SimPolicyServer_SockPath(), $errno, $errstr, 5);
  if ($sock === false) {
    fwrite(STDERR, "policy_server: connect failed: $errstr ($errno)\n");
    return null;
  }
  stream_set_timeout($sock, 10);
  $GLOBALS["simPolicySock"] = $sock;
  return $sock;
}

function SimPolicyServer_Query($payload) {
  // Returns action_index int, or null on transport failure.
  $GLOBALS["simPolicyQueries"] = ($GLOBALS["simPolicyQueries"] ?? 0) + 1;
  $json = json_encode($payload);
  $msg = pack("N", strlen($json)) . $json;
  for ($attempt = 0; $attempt < 2; ++$attempt) {
    $sock = SimPolicyServer_Connect();
    if ($sock === null) return null;
    $off = 0; $ok = true;
    while ($off < strlen($msg)) {
      $w = @fwrite($sock, substr($msg, $off));
      if ($w === false || $w <= 0) { $ok = false; break; }
      $off += $w;
    }
    if (!$ok) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    $hdr = @fread($sock, 4);
    if ($hdr === false || strlen($hdr) < 4) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    $len = unpack("N", $hdr)[1];
    if ($len <= 0 || $len > 50 * 1024 * 1024) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    $body = "";
    while (strlen($body) < $len) {
      $chunk = @fread($sock, $len - strlen($body));
      if ($chunk === false || $chunk === "") break;
      $body .= $chunk;
    }
    if (strlen($body) < $len) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    $resp = json_decode($body, true);
    if (!is_array($resp) || !isset($resp["action_index"])) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    $GLOBALS["simPolicyQueries"] = ($GLOBALS["simPolicyQueries"] ?? 0) + 1;
    return intval($resp["action_index"]);
  }
  return null;
}

function SimPolicyServer_Stats() {
  return [
    "queries" => intval($GLOBALS["simPolicyQueries"] ?? 0),
    "fallbacks" => intval($GLOBALS["simPolicyFallbacks"] ?? 0),
  ];
}

// Collect playable candidates best-first, replicating each branch's pop loop.
// Returns [candidates, gate_pass] where each candidate is
// [card_id, zone, zone_index, v1_score] and gate_pass mirrors the branch's
// act-vs-pass gating.
function SimPolicyServer_Collect($branch, $hand, $character, $arsenal, $items, $allies, $banish, $resources) {
  $player = intval($GLOBALS["currentPlayer"] ?? 1);
  $cands = [];
  $gate = false;
  switch ($branch) {
    case "B": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Block");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (CardIsBlockable($node)) $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
      }
      $gate = count($cands) > 0 && ShouldBlock(true, [$cands[0][0], $cands[0][1], $cands[0][2], $cands[0][3]]);
      break;
    }
    case "M": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Action");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (CardIsPlayable($node, $hand, $resources)) {
          if ($node[0] != "Hand" || count($hand) > 1 || BotIsPuzzle()) {
            $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
          }
        }
      }
      $gate = count($cands) > 0 && floatval($cands[0][3]) != 0.0;
      break;
    }
    case "M_END": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Action");
      $threshold = BotEndOfTurnAbilityThreshold();
      while ($pa !== []) {
        $node = array_pop($pa);
        if ($node[1] != "Character" || intval($node[2]) != 0) continue;
        if (floatval($node[3]) <= $threshold) continue;
        if (CardIsPlayable($node, $hand, $resources)) {
          $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
        }
      }
      $gate = count($cands) > 0;
      break;
    }
    case "A": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Reaction");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (ReactionCardIsPlayable($node, $hand, $resources)) {
          $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
        }
      }
      $gate = count($cands) > 0 && floatval($cands[0][3]) != 0.0;
      break;
    }
    case "D": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Reaction");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (ReactionCardIsPlayable($node, $hand, $resources)) {
          $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
        }
      }
      $gate = count($cands) > 0
        && ShouldBlock(true, [$cands[0][0], $cands[0][1], $cands[0][2], $cands[0][3]])
        && floatval($cands[0][3]) != 0.0;
      break;
    }
    case "P": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "Pitch");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (CardIsPitchable($node)) $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
      }
      $gate = count($cands) > 0 && floatval($cands[0][3]) != 0.0;
      break;
    }
    case "ARS": {
      $pa = GeneratePriorityValues($hand, $character, $arsenal, $items, $allies, $banish, "ToArsenal");
      while ($pa !== []) {
        $node = array_pop($pa);
        if (CardIsArsenalable($node)) $cands[] = [$node[0], $node[1], $node[2], floatval($node[3])];
      }
      $gate = count($cands) > 0 && floatval($cands[0][3]) != 0.0;
      break;
    }
  }
  return [$cands, $gate];
}

// Optional PHP-side trajectory logging (pass decisions + all choices when
// TCG_TRAJECTORY_LOG is set). The Python server also logs when it answers.
function SimPolicyServer_LogTrajectory($branch, $player, $state, $cands, $actionIndex, $dec = null) {
  $dir = getenv("TCG_TRAJECTORY_LOG");
  if ($dir === false || $dir === "") return;
  if (!is_dir($dir)) @mkdir($dir, 0700, true);
  if ($dec === null) $dec = intval($GLOBALS["simPolicyDecision"] = ($GLOBALS["simPolicyDecision"] ?? 0) + 1);
  $line = json_encode([
    "game" => strval($GLOBALS["gameName"] ?? ""),
    "decision" => $dec,
    "branch" => $branch,
    "player" => intval($player),
    "state" => $state,
    "action_index" => intval($actionIndex),
  ]);
  @file_put_contents($dir . "/trajectories.jsonl", $line . "\n", FILE_APPEND);
}

// Returns [handled=true, node|null]. node is the chosen priority node
// [card_id, zone, zone_index, v1_score], or null for pass.
function SimPolicyServer_Choose($branch, $hand, $character, $arsenal, $items, $allies, $banish, $resources) {
  $player = intval($GLOBALS["currentPlayer"] ?? 1);
  list($cands, $gate) = SimPolicyServer_Collect($branch, $hand, $character, $arsenal, $items, $allies, $banish, $resources);
  $candRecs = [];
  foreach ($cands as $c) {
    $candRecs[] = ["card_id" => strval($c[0]), "zone" => strval($c[1]), "zone_index" => intval($c[2]), "v1_score" => floatval($c[3])];
  }
  $state = SimFeat_BuildState($player, $branch, $candRecs);
  SimFeat_Canary($player, $state); // fail loudly on hidden-info leak
  $dec = intval($GLOBALS["simPolicyDecision"] = ($GLOBALS["simPolicyDecision"] ?? 0) + 1);
  if (!empty($GLOBALS["simLabelChild"])) {
    return SimLabel_ChildChoose($branch, $cands, $candRecs, $state, $gate);
  }
  if (!empty($GLOBALS["simSearchChild"])) {
    // Inside an ISMCTS child: the tree (or the leaf rule) decides.
    return SimSearch_ChildChoose($branch, $cands, $candRecs, $state, $gate);
  }
  if (!$gate || $cands === []) {
    // No real choice (gate failed or nothing playable): pass, log locally.
    SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, -1, $dec);
    return [true, null];
  }
  $sdPath = getenv("SEARCH_STATE_DUMP");
  if ($sdPath !== false && $sdPath !== "" && intval($player) === intval($GLOBALS["simSearchSeat"] ?? -1)) {
    file_put_contents($sdPath, json_encode(["game" => strval($GLOBALS["gameName"] ?? ""), "state" => $state, "cands" => $candRecs, "player" => intval($player), "branch" => $branch]) . "\n", FILE_APPEND);
  }
  if (!empty($GLOBALS["simSearchEnabled"]) && count($cands) >= 2
      && intval($player) === intval($GLOBALS["simSearchSeat"] ?? -1)) {
    $sidx = SimSearch_RootDecide($branch, $cands, $candRecs, intval($player));
    $eqPath = getenv("EQ_LOG");
    if ($eqPath !== false && $eqPath !== "") {
      $ev = SimSearch_EvalState(intval($player), $branch, $candRecs);
      $priors = ($ev !== null) ? ($ev[0] ?? []) : [];
      $am = null; $best = -1.0;
      foreach ($priors as $pi => $pv) { if ($pv > $best) { $best = $pv; $am = $pi; } }
      file_put_contents($eqPath, json_encode(["game" => strval($GLOBALS["gameName"] ?? ""), "branch" => $branch, "player" => intval($player), "search_idx" => $sidx, "argmax_idx" => $am, "n" => count($cands)]) . "\n", FILE_APPEND);
    }
    if ($sidx !== null && $sidx >= 0 && $sidx < count($cands)) {
      SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $sidx, $dec);
      return [true, $cands[$sidx]];
    }
  }
  $idx = SimPolicyServer_Query([
    "v" => 1,
    "game" => strval($GLOBALS["gameName"] ?? ""),
    "decision" => $dec,
    "branch" => $branch,
    "player" => $player,
    "state" => $state,
    "candidates" => $candRecs,
    "gate_pass" => true,
  ]);
  if ($idx === null || $idx < 0 || $idx >= count($cands)) {
    // Transport failure (or insane index): fall back to in-process v1 choice
    // and count it. A nonzero fallback count invalidates fidelity batches.
    $GLOBALS["simPolicyFallbacks"] = ($GLOBALS["simPolicyFallbacks"] ?? 0) + 1;
    fwrite(STDERR, "policy_server: fallback to v1 (branch $branch)\n");
    return [true, $cands[0]];
  }
  SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $idx, $dec);
  return [true, $cands[$idx]];
}

// Decision-queue routing. v1's choice is computed by the original logic;
// the server echoes it back (Phase A fidelity). Candidates carry v1_score
// 1.0 for v1's pick, 0.0 otherwise so argmax reproduces it.
function SimPolicyServer_DecisionOption($phase, $options, $playerID, $context = "") {
  $options = array_values(array_filter($options, fn($o) => $o !== ""));
  if (count($options) == 0) return "PASS";
  $v1choice = BotChooseDecisionOption_Original($phase, $options, $playerID, $context);
  $v1idx = array_search($v1choice, $options, true);
  if ($v1idx === false) return $v1choice; // edge: original returned something outside $options
  $candRecs = [];
  foreach ($options as $i => $opt) {
    $candRecs[] = ["card_id" => strval($opt), "zone" => "DQ", "zone_index" => $i, "v1_score" => ($i === $v1idx ? 1.0 : 0.0)];
  }
  $state = SimFeat_BuildState($playerID, "DQ", $candRecs);
  SimFeat_Canary(intval($playerID), $state);
  if (!empty($GLOBALS["simLabelChild"])) {
    return SimLabel_ChildDQ(intval($playerID), $candRecs, $state, $options, $v1choice);
  }
  if (!empty($GLOBALS["simSearchChild"])) {
    return SimSearch_ChildDQ(intval($playerID), $candRecs, $state, $options, $v1choice);
  }
  $dec = intval($GLOBALS["simPolicyDecision"] = ($GLOBALS["simPolicyDecision"] ?? 0) + 1);
  $idx = SimPolicyServer_Query([
    "v" => 1,
    "game" => strval($GLOBALS["gameName"] ?? ""),
    "decision" => $dec,
    "branch" => "DQ",
    "player" => intval($playerID),
    "state" => $state,
    "candidates" => $candRecs,
    "gate_pass" => true,
  ]);
  if ($idx === null || $idx < 0 || $idx >= count($options)) {
    $GLOBALS["simPolicyFallbacks"] = ($GLOBALS["simPolicyFallbacks"] ?? 0) + 1;
    return $v1choice;
  }
  SimPolicyServer_LogTrajectory("DQ", $playerID, $state, $candRecs, $idx, $dec);
  return $options[$idx];
}
