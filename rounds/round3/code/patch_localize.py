#!/usr/bin/env python3
"""Diagnostic (NOT package code): Claude's localization probe for the
round-3 seq-38 within-row zone hit. Adds SimLoc_Dump (five points in
SimSearch_RootDecide + the bridge pick points in Choose) recording
the canonical p1* globals AND the engine's view arrays / getter
returns at one target seq, gated on TCG_LOC_SEQ / TCG_LOC_LOG.
Apply AFTER patch_trace_shadow.py on a scratch tree."""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1])

HELPER = '''
function SimLoc_Dump($tag, $seq) {
  $want = getenv("TCG_LOC_SEQ"); $file = getenv("TCG_LOC_LOG");
  if ($want === false || $file === false || $file === ""
      || intval($want) !== intval($seq)) return;
  $row = ["tag" => $tag, "seq" => intval($seq),
    "p1Hand" => $GLOBALS["p1Hand"] ?? null,
    "p1Pitch" => $GLOBALS["p1Pitch"] ?? null,
    "p1Resources" => $GLOBALS["p1Resources"] ?? null,
    "getHand1" => function_exists("GetHand") ? GetHand(1) : "no-getter",
    "getResources1" => function_exists("GetResources") ? GetResources(1) : "no-getter",
    "mainHand" => $GLOBALS["mainHand"] ?? null,
    "myHand" => $GLOBALS["myHand"] ?? null,
    "theirHand" => $GLOBALS["theirHand"] ?? null,
    "mainPitch" => $GLOBALS["mainPitch"] ?? null,
    "myPitch" => $GLOBALS["myPitch"] ?? null,
    "mainResources" => $GLOBALS["mainResources"] ?? null,
    "myResources" => $GLOBALS["myResources"] ?? null,
    "viewFlags" => ["mpStillBuilt" => $GLOBALS["mainPlayerGamestateStillBuilt"] ?? null,
                    "myBuiltFor" => $GLOBALS["myStateBuiltFor"] ?? null,
                    "mainPlayer" => $GLOBALS["mainPlayer"] ?? null],
    "decisionQueue" => array_slice($GLOBALS["decisionQueue"] ?? [], 0, 6),
    "layers" => array_slice($GLOBALS["layers"] ?? [], 0, 6)];
  file_put_contents($file, json_encode($row) . "\\n", FILE_APPEND);
}
'''

pp = tree / "policy_server.php"
s = pp.read_text()
anchor = "function SimPolicyServer_Collect"
assert anchor in s
s = s.replace(anchor, HELPER + "\n" + anchor, 1)
old = '''  SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $idx, $dec);
  return [true, $cands[$idx]];'''
assert old in s
s = s.replace(old, '''  SimLoc_Dump("raw_pick", $dec);
  SimLoc_Dump("raw_next", $dec - 1);
  SimPolicyServer_LogTrajectory($branch, $player, $state, $candRecs, $idx, $dec);
  return [true, $cands[$idx]];''', 1)
pp.write_text(s)
print("policy_server.php: localize helper + raw dumps OK")

sp = tree / "search.php"
s = sp.read_text()
edits = [
    ('''  // Checkpoint the live state so children re-parse a consistent world.
  DoGamestateUpdate();''',
     '''  // Checkpoint the live state so children re-parse a consistent world.
  SimLoc_Dump("L1_entry", intval($GLOBALS["ssTraceDec"] ?? -1));
  DoGamestateUpdate();
  SimLoc_Dump("L2_after_update", intval($GLOBALS["ssTraceDec"] ?? -1));'''),
    ('''  SimSearch_IncludeWithGlobals("WriteGamestate.php");
  // Phase 2b snapshot harvest (throwaway tree only): at sampled root''',
     '''  SimSearch_IncludeWithGlobals("WriteGamestate.php");
  SimLoc_Dump("L3_after_write", intval($GLOBALS["ssTraceDec"] ?? -1));
  // Phase 2b snapshot harvest (throwaway tree only): at sampled root'''),
    ('''    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir);''',
     '''    $pick = SimTeacher_Decide($branch, $cands, $candRecs, $player, $gameDir);
    SimLoc_Dump("L4_after_decide", intval($GLOBALS["ssTraceDec"] ?? -1));'''),
    ('''      SimTrace_Log($trc);
    }
    return $pick;''',
     '''      SimTrace_Log($trc);
    }
    SimLoc_Dump("L5_before_return", intval($GLOBALS["ssTraceDec"] ?? -1));
    return $pick;'''),
]
for old, new in edits:
    assert old in s, old[:60]
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new, 1)
sp.write_text(s)
print("search.php: 5-point dumps OK")
print("patch_localize: applied")
