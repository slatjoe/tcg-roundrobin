#!/usr/bin/env python3
"""R17 (Claude round-3 rerun): the teacher's root evaluation uses the
state the bridge built.

Before this patch, SimPolicyServer_Choose built and canaried $state,
then SimSearch_RootDecide rebuilt an equivalent pre-sync state for
its trace, checkpoint-synced the live game (DoGamestateUpdate +
WriteGamestate), and SimTeacher_Decide computed its ROOT priors by
re-featurizing through SimSearch_EvalState - i.e. on the POST-sync
state. At a pitch-settling decision the featurizer's deck slice
(SimV1_DeckCards reads the p1Deck/p2Deck STORE) differs before and
after the sync, so the ghost's priorPick (Decide's post-sync argmax)
was not, by construction, the bridge's pick (Choose's pre-sync
argmax over the state it built).

This patch passes Choose's $state through RootDecide into
SimTeacher_Decide:

  * policy_server.php: the RootDecide call gains $state.
  * SimSearch_RootDecide gains an optional $bridgeState parameter.
    The trace PRE capture records THE PASSED STATE (feat_pre_hash
    and priors_pre are computed on it). A null state (legacy
    callers) falls back to building the pre-sync state exactly as
    before. After the checkpoint block, the row also records
    feat_sync_hash - a fresh post-sync featurization, DIAGNOSTIC
    ONLY (it is not read by the classifier or any assertion).
  * SimTeacher_Decide gains the same optional parameter. Its ROOT
    priors are computed with SimSearch_Eval($bridgeState, $candRecs)
    and the trace stash for the root row is set from that same
    passed state, so feat_post_hash == feat_pre_hash by
    construction. With no passed state it uses SimSearch_EvalState
    exactly as before.

Deliberately NOT changed:
  * SimSearch_EvalState itself, and every other use of it (the
    non-teacher ISMCTS root tie-break at the end of RootDecide, the
    EQ_LOG comparison in Choose).
  * The featurizations inside Decide that are not the root prior
    computation: the capture block's snapshot state and the
    overturn snapshot's state are still built where they were -
    they describe the checkpointed game dir, not the root priors.
  * Children and rollouts: they re-parse the synced store, where
    store == view, exactly as before.

Usage: patch_teacher_bridge_state.py <tree>
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
    # Pass the state Choose built (and canaried) into the search root.
    ("""    $sidx = SimSearch_RootDecide($branch, $cands, $candRecs, intval($player));""",
     """    // R17: hand RootDecide the state THIS function built and
    // canaried above, so the teacher's root evaluation uses the
    // bridge's own featurization rather than a post-sync rebuild.
    $sidx = SimSearch_RootDecide($branch, $cands, $candRecs, intval($player), $state);"""),
])

patch("search.php", [
    # 1. Decide: optional bridge-state parameter + root priors from it.
    ("""function SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir) {
  $t0 = microtime(true);
  $ncand = count($candRecs);
  $evRoot = SimSearch_EvalState($player, $branch, $candRecs);""",
     """function SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState = null) {
  $t0 = microtime(true);
  $ncand = count($candRecs);
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
    } catch (Throwable $e) { $evRoot = null; }
    if (SimTrace_On()) {
      $GLOBALS["ssTraceLastEval"] = [
        "state_hash" => SimTrace_Hash($bridgeState),
        "priors" => ($evRoot !== null && isset($evRoot[0]))
          ? $evRoot[0] : null];
    }
  } else {
    $evRoot = SimSearch_EvalState($player, $branch, $candRecs);
  }"""),
    # 2. RootDecide: optional bridge-state parameter.
    ("""function SimSearch_RootDecide($branch, $cands, $candRecs, $player) {""",
     """function SimSearch_RootDecide($branch, $cands, $candRecs, $player, $bridgeState = null) {"""),
    # 3. PRE capture records the passed state; null falls back to the
    #    pre-sync rebuild exactly as before.
    ("""    $stPre = null;
    try { $stPre = SimFeat_BuildState($player, $branch, $candRecs); }
    catch (Throwable $e) { $stPre = null; }
    $evPre = ($stPre !== null) ? SimSearch_Eval($stPre, $candRecs) : null;""",
     """    // R17: record the bridge's own state when Choose passed it;
    // only a legacy caller without one takes the old rebuild path.
    $stPre = $bridgeState;
    if ($stPre === null) {
      try { $stPre = SimFeat_BuildState($player, $branch, $candRecs); }
      catch (Throwable $e) { $stPre = null; }
    }
    $evPre = ($stPre !== null) ? SimSearch_Eval($stPre, $candRecs) : null;"""),
    # 4. Post-sync diagnostic hash, recorded on the trace row after
    #    the checkpoint block. Diagnostic only: nothing reads it.
    ("""  SimSearch_IncludeWithGlobals("WriteGamestate.php");
  // R14: root canary, single-source accounting.""",
     """  SimSearch_IncludeWithGlobals("WriteGamestate.php");
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
  // R14: root canary, single-source accounting."""),
    # 5. Hand the bridge state on to Decide.
    ("""    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir);""",
     """    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir, $bridgeState);"""),
])

print("teacher-bridge-state patch applied to", tree)
