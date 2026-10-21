#!/usr/bin/env python3
"""Round-6 pick-flip probe (claude-reply-f7e4534 sec.3): at every
ARS featurization in plain bridge play, evaluate BOTH the current
state (deck_counts from the store, exactly as SimFeat_BuildState
serialized it) and a view-consistent variant (identical in every
field except deck_counts, replaced by the view-derived counts)
through the production server's eval endpoint, and log the pair.
Play continues on the current state's normal pick path - the two
eval requests are side queries that change no game.

Why this measurement (claude-reply-f7e4534 sec.2): the round-5
census found the store/view deck-count disagreement concentrated
at ARS (163 of 267 ARS featurizations, all view > store). That is
a representational blind spot, not a train/serve inconsistency -
every training record behind v15 was featurized through the same
path, so the net trained WITH the omission. Correcting the
featurizer for the current net would CREATE a mismatch at exactly
these decisions. The only open question for the current nets is
behavioral: does the omission change v15's picks? This probe
answers it.

Site (decided from the code; defended in pickflip-package.md):
policy_server.php, SimPolicyServer_Choose - the ONLY funnel that
ever sees branch ARS (the decision-queue funnel hardcodes branch
"DQ", policy_server.php:448, so ARS featurizations occur solely in
Choose). Two edits:
  1. Two helper functions inserted before SimPolicyServer_Choose:
     SimFlip_Eval - an eval-shaped sibling of the bridge's pick
     query, mirroring SimSearch_Eval's wire behavior
     (search.php:431) on the bridge's own connection
     (SimPolicyServer_Connect, policy_server.php:35 - the single
     transport choke point both bridge funnels share; the pick
     query SimPolicyServer_Query cannot be reused because it is
     pick-shaped: it requires an action_index in the response and
     returns an int, policy_server.php:86-108), and
     SimFlip_Argmax (first strict maximum, the codebase's own
     tie-break: v1_argmax and the bridge's EQ_LOG scan).
  2. One probe block in Choose, after the state is built and
     canaried and the decision counter assigned, before the
     label/search child branches (both unset in plain bridge
     mode). It fires only when $branch === "ARS".

Eval shape (pinned from the code): the production server's
handle_conn (search_server.py:265) routes mode == "eval" to
evaluate(state, candidates) and answers {"priors", "value"}; the
handler reads NO seat field - the state dict's own perspective
rules (featurize_state_v3 reads state["player"]), so both seats'
ARS states evaluate through v15, and the payload's learner_seat
(sent verbatim, as SimSearch_Eval sends it) is ignored by the
eval handler. SimSearch_EvalState (search.php:474) canNOT be
used for the variant: it rebuilds the state via BuildState, which
would rebuild the CURRENT state. The raw eval send with an
explicit state is the only correct shape. The two requests the
probe sends are built from one $candRecs array and two state
arrays differing only at ["deck_counts"] - mode, candidates and
learner_seat are the same values in both.

Definitions (pickflip-package.md sec.3):
  store side = $state["deck_counts"] verbatim ("" key dropped),
    the exact map serialized for the net.
  view side  = SimFeat_Counts(SimFeat_ZoneIDs(GetDeck($player),
    DeckPieces())) - the census's operational definition,
    unchanged, so agree flags reconcile 1:1 with census rows.
  variant    = $state with ["deck_counts"] replaced by the view
    side (PHP arrays are value types: every other field is the
    same value by construction). The variant is NEVER canaried,
    never played, never written anywhere except this log - it is
    a hypothetical input to a stateless eval query.
  flip       = argmax(cur_priors) !== argmax(var_priors), argmax
    by first strict maximum over the shared candidate order.

Probe discipline: gated on FLIP_LOG (unset => for ARS calls one
getenv, for all other branches one string comparison - the only
added work); the dual eval fires ONLY at ARS featurizations when
the env is set; a row is logged for every ARS Choose call, with
pick=false and null eval fields when the gate failed or there
are no candidates (no pick exists to flip); on any eval failure
the row records eval_error=true and flip=null; the body is
wrapped so a probe error can never reach play; the played pick
proceeds through the untouched SimPolicyServer_Query path.

Deliberately NOT changed:
  * featurize.php (stays at the O build f81193e0...), search.php
    (stays 8f6b35da...), the canary, the sync discipline, the
    pick path, the DQ funnel, and every other function.
  * $state itself - the probe reads it; the variant is a copy.

Applies to the O tree's policy_server.php
(sha256 64c215392ddcac0dc92ce1e4a3c455969d87423e23d71be57991247ce53827b3).

Usage: patch_pickflip_probe.py <tree>   (tree contains policy_server.php)
"""
import hashlib
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fliptree")


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def patch(fname, pairs):
    p = tree / fname
    before = sha256(p)
    s = p.read_text()
    for old, new in pairs:
        assert old in s, f"anchor missing in {fname}: {old[:70]!r}"
        assert s.count(old) == 1, \
            f"anchor not unique in {fname}: {old[:70]!r}"
        s = s.replace(old, new)
    p.write_text(s)
    print(f"{fname}: {len(pairs)} edits OK")
    print(f"{fname}: sha256 before {before}")
    print(f"{fname}: sha256 after  {sha256(p)}")


HELPERS = r'''// ---- pick-flip probe helpers (round 6; claude-reply-f7e4534 sec.3) ----
// SimFlip_Eval mirrors SimSearch_Eval's wire behavior
// (search.php:431) on the bridge's own connection: same socket
// (SimPolicyServer_Connect), same 4-byte big-endian length prefix,
// same payload shape ({"mode":"eval","state","candidates",
// "learner_seat"}), same two-attempt discipline - the pick query
// SimPolicyServer_Query cannot carry an eval because it requires
// an action_index in the response and returns an int. The
// production server's eval handler answers {"priors","value"}
// and reads no seat field; the state's own perspective rules.
// Returns [priors(array), value(float)] or null on failure; on a
// transport failure the shared socket global is dropped so the
// next pick query reconnects transparently.
function SimFlip_Eval($state, $candRecs) {
  $payload = json_encode(["mode" => "eval", "state" => $state, "candidates" => $candRecs, "learner_seat" => intval(getenv("TCG_LEARNER_SEAT") ?: 0)]);
  $msg = pack("N", strlen($payload)) . $payload;
  for ($attempt = 0; $attempt < 2; ++$attempt) {
    $sock = SimPolicyServer_Connect();
    if ($sock === null) return null;
    $off = 0; $ok = true;
    while ($off < strlen($msg)) {
      $w = @fwrite($sock, substr($msg, $off));
      if ($w === false || $w <= 0) { $ok = false; break; }
      $off += $w;
    }
    if (!$ok) { @fclose($sock); unset($GLOBALS["simPolicySock"]); continue; }
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
    if (!is_array($resp) || isset($resp["error"]) || !isset($resp["priors"]) || !isset($resp["value"])) {
      @fclose($sock); unset($GLOBALS["simPolicySock"]); continue;
    }
    return [$resp["priors"], floatval($resp["value"])];
  }
  return null;
}

// First strict maximum - the codebase's own tie-break
// (v1_argmax's scan; the bridge's EQ_LOG argmax scan).
function SimFlip_Argmax($priors) {
  $best = null; $bi = -1;
  foreach ($priors as $i => $p) {
    $p = floatval($p);
    if ($best === null || $p > $best) { $best = $p; $bi = intval($i); }
  }
  return $bi;
}

'''

PROBE = r'''  // ---- pick-flip probe (round 6; claude-reply-f7e4534 sec.3) ----
  // Inference-only: at ARS featurizations, evaluate BOTH the
  // current state (deck_counts from the store, as built above)
  // and a view-consistent variant (deck_counts replaced by the
  // view-derived counts, every other field the same value)
  // through the server's eval endpoint, and log the pair to
  // FLIP_LOG. Play continues on the untouched pick path below;
  // the variant is never canaried, never played, never written
  // anywhere except this log. Store/view definitions are the
  // census's (round 5), unchanged, so agree flags reconcile with
  // census rows. With FLIP_LOG unset the only added work at an
  // ARS call is one getenv (other branches: one comparison).
  if ($branch === "ARS") {
    $flipLog = getenv("FLIP_LOG");
    if ($flipLog !== false && $flipLog !== "") {
      try {
        $flipStore = $state["deck_counts"] ?? [];
        unset($flipStore[""]);
        $flipDeckView = &GetDeck($player);
        $flipView = SimFeat_Counts(SimFeat_ZoneIDs($flipDeckView, DeckPieces()));
        unset($flipView[""]);
        $flipDiffs = [];
        $flipIds = array_unique(array_merge(array_keys($flipStore), array_keys($flipView)));
        foreach ($flipIds as $flipCid) {
          $flipSv = intval($flipStore[$flipCid] ?? 0);
          $flipVv = intval($flipView[$flipCid] ?? 0);
          if ($flipSv !== $flipVv) $flipDiffs[$flipCid] = [$flipSv, $flipVv];
        }
        $flipCandIds = [];
        foreach ($candRecs as $flipC) {
          $flipCandIds[] = ["card_id" => strval($flipC["card_id"] ?? ""), "zone" => strval($flipC["zone"] ?? ""), "zone_index" => intval($flipC["zone_index"] ?? 0)];
        }
        $flipRow = [
          "game" => strval($GLOBALS["gameName"] ?? ""),
          "player" => $player,
          "branch" => $branch,
          "turn" => intval($state["turn"] ?? 0),
          "decision" => $dec,
          "agree" => ($flipDiffs === []),
          "diffs" => $flipDiffs,
          "pick" => ($gate && count($candRecs) >= 1),
          "ncand" => count($candRecs),
          "candidates" => $flipCandIds,
          "cur_argmax" => null,
          "var_argmax" => null,
          "flip" => null,
          "cur_priors" => null,
          "var_priors" => null,
          "cur_value" => null,
          "var_value" => null,
          "eval_error" => false,
        ];
        if ($flipRow["pick"]) {
          $flipVariant = $state;
          $flipVariant["deck_counts"] = $flipView;
          $flipCur = SimFlip_Eval($state, $candRecs);
          $flipVar = SimFlip_Eval($flipVariant, $candRecs);
          if ($flipCur !== null && $flipVar !== null
              && count($flipCur[0]) === count($candRecs)
              && count($flipVar[0]) === count($candRecs)) {
            $flipRow["cur_priors"] = array_map("floatval", array_values($flipCur[0]));
            $flipRow["var_priors"] = array_map("floatval", array_values($flipVar[0]));
            $flipRow["cur_value"] = $flipCur[1];
            $flipRow["var_value"] = $flipVar[1];
            $flipRow["cur_argmax"] = SimFlip_Argmax($flipRow["cur_priors"]);
            $flipRow["var_argmax"] = SimFlip_Argmax($flipRow["var_priors"]);
            $flipRow["flip"] = ($flipRow["cur_argmax"] !== $flipRow["var_argmax"]);
          } else {
            $flipRow["eval_error"] = true;
          }
        }
        @file_put_contents($flipLog, json_encode($flipRow) . "\n", FILE_APPEND | LOCK_EX);
      } catch (Throwable $flipErr) {
        // A probe failure must never reach play.
      }
    }
  }
'''

patch("policy_server.php", [
    # Edit 1: the two helpers, inserted immediately before
    # SimPolicyServer_Choose (the comment block + signature is the
    # unique anchor).
    ("""// Returns [handled=true, node|null]. node is the chosen priority node
// [card_id, zone, zone_index, v1_score], or null for pass.
function SimPolicyServer_Choose($branch, $hand, $character, $arsenal, $items, $allies, $banish, $resources) {""",
     HELPERS + """// Returns [handled=true, node|null]. node is the chosen priority node
// [card_id, zone, zone_index, v1_score], or null for pass.
function SimPolicyServer_Choose($branch, $hand, $character, $arsenal, $items, $allies, $banish, $resources) {"""),
    # Edit 2: the probe block in Choose, after the decision counter
    # is assigned and before the label-child branch (the
    # ChildChoose line makes the anchor unique to Choose - the DQ
    # funnel's matching lines name ChildDQ instead).
    ("""  $dec = intval($GLOBALS["simPolicyDecision"] = ($GLOBALS["simPolicyDecision"] ?? 0) + 1);
  if (!empty($GLOBALS["simLabelChild"])) {
    return SimLabel_ChildChoose($branch, $cands, $candRecs, $state, $gate);""",
     """  $dec = intval($GLOBALS["simPolicyDecision"] = ($GLOBALS["simPolicyDecision"] ?? 0) + 1);
""" + PROBE + """  if (!empty($GLOBALS["simLabelChild"])) {
    return SimLabel_ChildChoose($branch, $cands, $candRecs, $state, $gate);"""),
])

print("pickflip-probe patch applied to", tree)
