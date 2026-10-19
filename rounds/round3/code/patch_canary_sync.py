#!/usr/bin/env python3
"""R14 (Claude round-3 rerun): the root canary reads one world.

In the launch build, SimSearch_RootDecide ran SimSearch_Canary BEFORE
the checkpoint block. The canary reads hidden zones through
SimSearch_ReadZone, which prefers the p1*/p2* STORE, and public zones
through the getters, which return the VIEWS. Between syncs the store
lags the view (round-3 localization: the engine plays from the views;
DoGamestateUpdate syncs store := view), so a card that had moved in
the view since the last sync was counted in neither source and the
canary reported it missing - 11 refusals in ghost s1, 16 in ghost s2,
29 across capture, every one at an arsenal decision with a card like
dragon_power_blue "missing". Those refusals invalidated 8-13 seeds
per pairing under the launch reads.

This patch moves the canary call to immediately AFTER the checkpoint
block (DoGamestateUpdate + WriteGamestate include) and before the
TEACHER_MODE dispatch: at that point store == view by construction,
so both halves of the check describe the same world. The sync is
benign (localization, previous round: the checkpoint sync is
load-bearing and changes nothing the engine plays from).

Behavior on refusal is unchanged: log the stat row (fallback canary +
missing multiset) and return null, so the decision goes down the
plain bridge path. Note the trace consequence, which the amended
reads rely on: the round-3 trace's PRE capture sits before the
checkpoint, and the teacher trace row is only written after Decide
runs - a refused decision therefore leaves NO teacher trace row,
only the bridge's bridge_pick row.

The child hook canary (SimSearch_HookCheck) is untouched.

Usage: patch_canary_sync.py <tree>
"""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/reruntree")
p = tree / "search.php"
s = p.read_text()


def sub(old, new):
    global s
    assert old in s, f"anchor missing: {old[:70]!r}"
    assert s.count(old) == 1, f"anchor not unique: {old[:70]!r}"
    s = s.replace(old, new)


# 1. Remove the pre-sync canary from the top of RootDecide.
sub("""  if (!SimSearch_Canary($deckFiles)) {
    SimSearch_LogStat(["branch" => $branch, "fallback" => "canary",
                       "missing" => $GLOBALS["ssLastCanaryMissing"] ?? null]);
    return null;
  }""",
    """  // R14: the root canary runs AFTER the checkpoint block below -
  // see the note there. It used to run at this point, before the
  // sync, where its mixed store/view accounting reported in-transit
  // cards as missing.""")

# 2. Re-insert it immediately after the checkpoint block.
sub("""  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();
  $GLOBALS["skipWriteGamestate"] = false;
  SimSearch_IncludeWithGlobals("WriteGamestate.php");""",
    """  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();
  $GLOBALS["skipWriteGamestate"] = false;
  SimSearch_IncludeWithGlobals("WriteGamestate.php");
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
  }""")

p.write_text(s)
print("canary-sync patch applied to", p)
