#!/usr/bin/env python3
"""Gate hardening (Claude round 2, 2026-10-18):

1. R2 second placement: a consumer-side determinization check at the
   child's FIRST root-decision hook (after the engine's first step
   re-derives state) - SimSearch_HookCheck verifies the zone split
   against the assignment AND runs the global conservation canary
   over the child's deck files. Parse-time verify alone cannot see
   a step-time revert, which was the original defect's mechanism.
2. Copy-by-whitelist for children: only gamestate.txt, GameFile.txt,
   p1Deck.txt, p2Deck.txt are copied (replaces copy-all + blacklist
   sanitization at the child sites). The R3 byte-diff remains the
   regression for the next engine file that tries to ride along.
3. Teacher stat rows log abort reasons and abort counts by candidate
   (an abort rate that correlates with candidate type is a bias, not
   noise), and carry det_persisted=1.
4. TEACHER_GHOST=1: full teacher machinery, pick forced to the prior
   pick (the pre-gate regression arm: ghost must be action-identical
   to raw v15 on the same seeds).
"""
import sys

path = sys.argv[1]
src = open(path).read()

def sub(old, new, n=1):
    global src
    c = src.count(old)
    assert c == n, "anchor count %d (want %d) for %r" % (c, n, old[:70])
    src = src.replace(old, new)

# ---- helpers: whitelist copy + hook check (before RunChild) ----
anchor = "\nfunction SimSearch_RunChild("
helpers = '''
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
'''
assert src.count(anchor) == 1
src = src.replace(anchor, helpers + anchor)

# ---- RunChild: whitelist copies, assignment stash, hook check ----
sub("    SimSearch_CopyDir($parentDir, $snapDir);",
    "    SimSearch_CopyChildDir($parentDir, $snapDir);")
sub("""      SimSearch_CopyDir($snapDir, $workDir);
      SimSearch_SanitizeChildDir($workDir);""",
    """      SimSearch_CopyChildDir($snapDir, $workDir);""")
sub('    $GLOBALS["ssRootKey"] = strval($cfg["rootKey"] ?? "");',
    '''    $GLOBALS["ssRootKey"] = strval($cfg["rootKey"] ?? "");
    $GLOBALS["ssAssignment"] = $assignment;''')
sub("""        @file_put_contents($resFile, json_encode(["error" => "root_mismatch"]));""",
    """        @file_put_contents($resFile, json_encode(["error" => $GLOBALS["ssChildError"] ?? "root_mismatch"]));""")
# per-sim hook-check reset (next to the stack reset)
sub('      $GLOBALS["ssStack"] = [0];',
    '''      $GLOBALS["ssStack"] = [0];
      $GLOBALS["ssHookChecked"] = false;''')

# ---- search ChildChoose: hook check at the first root hook ----
sub("""      if ($key !== $GLOBALS["ssRootKey"]) {
        throw new SimSearchAbort();
      }
    }
    // Materialize + expand this node.""",
    """      if ($key !== $GLOBALS["ssRootKey"]) {
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
    // Materialize + expand this node.""")

# ---- RunRollout: whitelist copy, assignment stash, error passthrough ----
sub("    SimSearch_CopyDir($snapDir, $workDir);",
    "    SimSearch_CopyChildDir($snapDir, $workDir);")
sub("""    SimSearch_SanitizeChildDir($workDir);
    if (!SimSearch_ApplyAssignmentToFile($workDir, $assignment)) {""",
    """    if (!SimSearch_ApplyAssignmentToFile($workDir, $assignment)) {""")
sub("""    if (!SimSearch_VerifyAssignment($assignment)) {
      @file_put_contents($resFile, json_encode(["error" => "det_verify_failed"]));
      SimSearch_WipeDir($workDir);
      if (function_exists("DeleteCache")) DeleteCache($childGame);
      exit(0);
    }""",
    """    if (!SimSearch_VerifyAssignment($assignment)) {
      @file_put_contents($resFile, json_encode(["error" => "det_verify_failed"]));
      SimSearch_WipeDir($workDir);
      if (function_exists("DeleteCache")) DeleteCache($childGame);
      exit(0);
    }
    $GLOBALS["ssAssignment"] = $assignment;""")
sub("""      @file_put_contents($resFile, json_encode(["error" => "abort"]));""",
    """      @file_put_contents($resFile, json_encode(["error" => $GLOBALS["ssLabelError"] ?? "abort"]));""")

# ---- label ChildChoose: hook check at the rooted moment ----
sub("""    $GLOBALS["ssLabelRooted"] = true;
    $fi = intval($GLOBALS["ssLabelForceIdx"] ?? 0);""",
    """    $GLOBALS["ssLabelRooted"] = true;
    $hcErr = SimSearch_HookCheck();
    if ($hcErr !== null) {
      $GLOBALS["ssLabelError"] = $hcErr;
      throw new SimSearchAbort();
    }
    $fi = intval($GLOBALS["ssLabelForceIdx"] ?? 0);""")

# ---- teacher: abort accounting + ghost + det_persisted stamp ----
sub('  $assignments = []; $canaryWorlds = 0;',
    '''  $assignments = []; $canaryWorlds = 0;
  $abortReasons = []; $abortByCand = [];''')
sub('''        } else { ++$errors; }''',
    '''        } else {
          ++$errors;
          $rk = is_array($res) ? strval($res["error"] ?? "bad_result")
                               : "no_result";
          $abortReasons[$rk] = ($abortReasons[$rk] ?? 0) + 1;
          $abortByCand[$ci] = ($abortByCand[$ci] ?? 0) + 1;
        }''')
sub('''  $base = ["teacher" => 1, "contested" => 1, "det" => "file-v3", "branch" => $branch,''',
    '''  $base = ["teacher" => 1, "contested" => 1, "det" => "file-v3",
    "det_persisted" => 1, "branch" => $branch,''')
sub('''  $base["priors"] = $priors;''',
    '''  $base["abort_reasons"] = $abortReasons;
  $base["abort_by_cand"] = $abortByCand;
  if (getenv("TEACHER_GHOST")) {
    // Pre-gate regression arm: full machinery, pick forced to the
    // prior's. The live game must stay action-identical to raw v15.
    $base["ghost"] = 1;
    $base["ghost_would_pick"] = $pick;
    $base["ghost_would_overturn"] = $overturn;
    $pick = $priorPick; $overturn = 0;
  }
  $base["priors"] = $priors;''')

open(path, "w").write(src)
print("gate-hardening patch applied to", path)
