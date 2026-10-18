#!/usr/bin/env python3
"""Teacher capture mode + labeler candidate-subset support.

Built for the round-robin measurement (Claude's pre-registered design,
2026-10-18): harvest ~40 PLAIN v15-vs-heuristic games, snapshot EVERY
teacher-contested decision, label the teacher's selected set at k=25
under pair va, and compute split-half per-decision gains (ungated and
1.5-SE gated) summed per game.

1. TEACHER_CAPTURE=1 in SimTeacher_Decide: at each contested decision,
   copy the checkpoint dir into TEACHER_SNAP_DIR and append an index
   row carrying priors + prior_pick + the teacher's selected set, then
   return the prior pick WITHOUT rolling out. The applied play is pure
   net argmax, so harvested trajectories are plain v15 games; the
   machinery cost per decision is one EvalState + one dir copy.
2. SimLabel_RunForSnapshot honors cfg["candIdx"] (a list of candidate
   indices to label; default remains all candidates up to cap), so the
   labeler can label exactly the teacher's selected set while the root
   key still covers the full candidate list.
"""
import sys

path = sys.argv[1]
src = open(path).read()

def sub(old, new, n=1):
    global src
    c = src.count(old)
    assert c == n, "anchor count %d (want %d) for %r" % (c, n, old[:70])
    src = src.replace(old, new)

# ---- 1. capture hook, right after the selection set is computed ----
old_sel = """  sort($sel);
  $K = 25;"""
new_sel = """  sort($sel);
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
            "selected" => $sel]) . "\\n", FILE_APPEND);
      }
    }
    SimSearch_LogStat(["teacher" => 1, "contested" => 1, "capture" => 1,
      "det" => "file-v3", "branch" => $branch, "player" => $player,
      "turn" => intval($GLOBALS["currentTurn"] ?? 0), "ncand" => $ncand,
      "selected" => $sel, "prior_pick" => $priorPick,
      "pick" => $priorPick,
      "ms" => intval((microtime(true) - $t0) * 1000)]);
    return $priorPick;
  }
  $K = 25;"""
sub(old_sel, new_sel)

# ---- 2. candIdx support in the labeler ----
old_loop = """  for ($ci = 0; $ci < $ncand; ++$ci) {
    $kids = [];"""
new_loop = """  $ciList = $cfg["candIdx"] ?? null;
  if (!is_array($ciList)) $ciList = range(0, $ncand - 1);
  foreach ($ciList as $ci) {
    $ci = intval($ci);
    if ($ci < 0 || $ci >= $ncand) continue;
    $kids = [];"""
sub(old_loop, new_loop)

open(path, "w").write(src)
print("teacher-capture patch applied to", path)
