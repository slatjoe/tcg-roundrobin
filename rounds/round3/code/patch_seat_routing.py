#!/usr/bin/env python3
"""R12 (Claude round-3 rerun): seat routing named on every request.

The pre-gate launch's seat-2 pairings were void because the policy
server routes bridge picks by a LEARNER_SEAT constant read once from
the SERVER process's environment at start (rl/search_server.py:41,
default 1; routing at :225), while paired_driver.py set
TCG_LEARNER_SEAT only in the PHP child's environment. One seat-1
server served every arm, so "raw seat 2" was the heuristic playing
seat 2 and ghost seat 2 compared net priors against heuristic picks.

Fix, client side (this patch) + server side (patched
rl/search_server.py: ping + per-request seat check + learner_seat in
every response):
  policy_server.php - SimPolicyServer_Query is the single funnel for
    every normal bridge request (Choose, DecisionOption, and the
    shadow path's direct Query call all pass through it). It now
    stamps "learner_seat" (from the PHP process's TCG_LEARNER_SEAT)
    onto every payload, and a {"error":"seat_mismatch"} response
    surfaces immediately: a SEAT_MISMATCH line on STDERR (the line the
    paired driver counts), a simPolicySeatMismatches increment, and a
    null return into the existing counted v1-fallback path.
  search.php - SimSearch_Eval stamps "learner_seat" onto eval
    payloads the same way and returns null (with the same STDERR
    line) on a seat_mismatch response, which Decide already treats
    as an eval failure.

Requests from legacy callers that never set TCG_LEARNER_SEAT stamp 0
and are rejected by any correctly seated server (seats are 1|2):
fail-closed, loudly, instead of silently mis-seated.

Usage: patch_seat_routing.py <tree>
"""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/reruntree")


def patch(fname, pairs):
    p = tree / fname
    s = p.read_text()
    for old, new in pairs:
        assert old in s, f"anchor missing in {fname}: {old[:70]!r}"
        assert s.count(old) == 1, \
            f"anchor not unique in {fname}: {old[:70]!r}"
        s = s.replace(old, new)
    p.write_text(s)
    print(f"{fname}: {len(pairs)} edits OK")


patch("policy_server.php", [
    ("""function SimPolicyServer_Query($payload) {
  // Returns action_index int, or null on transport failure.
  $GLOBALS["simPolicyQueries"] = ($GLOBALS["simPolicyQueries"] ?? 0) + 1;""",
     """function SimPolicyServer_Query($payload) {
  // Returns action_index int, or null on transport failure.
  $GLOBALS["simPolicyQueries"] = ($GLOBALS["simPolicyQueries"] ?? 0) + 1;
  // R12: every bridge request names the learner seat this process is
  // playing. A server seated differently rejects the request (see
  // the seat_mismatch branch below) instead of silently routing the
  // pick to the other seat's policy.
  $payload["learner_seat"] = intval(getenv("TCG_LEARNER_SEAT") ?: 0);"""),
    ("""    $resp = json_decode($body, true);
    if (!is_array($resp) || !isset($resp["action_index"])) {""",
     """    $resp = json_decode($body, true);
    if (is_array($resp) && ($resp["error"] ?? "") === "seat_mismatch") {
      // R12: fail LOUD. This STDERR line is what the paired driver
      // counts (seat_mismatch_errors); returning null routes into
      // the existing counted in-process v1 fallback. A game with
      // any mismatch is invalid under the rerun reads.
      $GLOBALS["simPolicySeatMismatches"] =
        ($GLOBALS["simPolicySeatMismatches"] ?? 0) + 1;
      fwrite(STDERR, "policy_server: SEAT_MISMATCH server_seat="
        . intval($resp["learner_seat"] ?? -1) . " request_seat="
        . intval($payload["learner_seat"]) . "\\n");
      return null;
    }
    if (!is_array($resp) || !isset($resp["action_index"])) {"""),
])

patch("search.php", [
    ("""  $payload = json_encode(["mode" => "eval", "state" => $state, "candidates" => $candRecs]);""",
     """  $payload = json_encode(["mode" => "eval", "state" => $state, "candidates" => $candRecs, "learner_seat" => intval(getenv("TCG_LEARNER_SEAT") ?: 0)]);"""),
    ("""    $resp = json_decode($body, true);
    if (!is_array($resp) || !isset($resp["priors"]) || !isset($resp["value"])) {""",
     """    $resp = json_decode($body, true);
    if (is_array($resp) && ($resp["error"] ?? "") === "seat_mismatch") {
      // R12: same loud failure as the bridge funnel (the paired
      // driver counts the SEAT_MISMATCH token in the game log).
      fwrite(STDERR, "search: SEAT_MISMATCH server_seat="
        . intval($resp["learner_seat"] ?? -1) . " request_seat="
        . intval(getenv("TCG_LEARNER_SEAT") ?: 0) . "\\n");
      return null;
    }
    if (!is_array($resp) || !isset($resp["priors"]) || !isset($resp["value"])) {"""),
])

print("seat-routing patch applied to", tree)
