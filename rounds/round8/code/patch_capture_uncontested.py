#!/usr/bin/env python3
"""patch_capture_uncontested.py - round-8 corpus-tree extension:
snapshot UNCONTESTED decisions during capture games.

Why this exists (named gap, build-package sec.2): the driver's
capture arm snapshots every CONTESTED decision (search.php,
TEACHER_CAPTURE block), but SimTeacher_Decide's uncontested early
return (top prior >= 0.97 or a single candidate) only logs a stat
row - no snapshot, and trace rows carry hashes, not states. The T1
loss (claude-reply-926f6c3 sec.3) needs the same corpus games'
UNCONTESTED states for its beta * KL(v15 || student) term. This
patch is the smallest way to get them: inside the uncontested
return, when TEACHER_CAPTURE and TEACHER_CAPTURE_UNCONTESTED are
both set, copy the game dir and append an index row in the capture
index's own shape plus "uncontested": 1 (contested rows carry
"selected"; uncontested rows have no selection and omit it).

Properties:
  * Snapshot only. The block runs after the pick is decided, is
    wrapped in try/catch ("capture must never break the search" -
    the contested block's own discipline at search.php:533), and
    the return value is untouched. Picks cannot change.
  * Same per-game counter (ssTeacherSnapCount) and the same
    <game>_t<hc> directory naming as the contested block, so the
    two snapshot classes share one collision-free namespace.
  * The state recorded is the bridge state when Choose passed one
    (R17), else a fresh SimFeat_BuildState - the contested block's
    own fallback order.

Scope: applies ONLY to the corpus tree (a copy of the native tree
the capture runner builds and hash-pins at launch). The two gate
trees' search.php stays at the gate pin 6cd6f980...; nothing here
touches it.

Base: search.php sha256
6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a.
The product hash is whatever this patch produces; the capture
runner records it in the corpus manifest at build time (the patch
is anchor-asserted, count == 1, so the product is deterministic).

Usage: patch_capture_uncontested.py <tree>   (tree contains search.php)
"""
import hashlib
import pathlib
import sys

BASE_SHA = "6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a"

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/distilltree_corpus")


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


p = tree / "search.php"
before = sha256(p)
assert before == BASE_SHA, \
    f"refusing: {p} sha256 {before} != base {BASE_SHA}"
s = p.read_text()

OLD = """  if ($ncand <= 1 || $bp >= 0.97) {
    SimSearch_LogStat(["teacher" => 1, "contested" => 0, "branch" => $branch,
      "player" => $player, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "ncand" => $ncand, "prior_pick" => $priorPick, "pick" => $priorPick,
      "ms" => intval((microtime(true) - $t0) * 1000)]);
    return $priorPick;
  }"""

NEW = """  if ($ncand <= 1 || $bp >= 0.97) {
    SimSearch_LogStat(["teacher" => 1, "contested" => 0, "branch" => $branch,
      "player" => $player, "turn" => intval($GLOBALS["currentTurn"] ?? 0),
      "ncand" => $ncand, "prior_pick" => $priorPick, "pick" => $priorPick,
      "ms" => intval((microtime(true) - $t0) * 1000)]);
    if (getenv("TEACHER_CAPTURE") && getenv("TEACHER_CAPTURE_UNCONTESTED")) {
      // Round-8 corpus extension: snapshot UNCONTESTED decisions
      // too (the T1 KL term needs their states; see
      // patch_capture_uncontested.py). Snapshot only - the pick
      // above is already decided and never changes here.
      try {
        $snapDir0 = getenv("TEACHER_SNAP_DIR");
        if ($snapDir0 !== false && $snapDir0 !== "") {
          $gname = strval($GLOBALS["gameName"] ?? "");
          $GLOBALS["ssTeacherSnapCount"][$gname] =
            ($GLOBALS["ssTeacherSnapCount"][$gname] ?? 0) + 1;
          $hc = $GLOBALS["ssTeacherSnapCount"][$gname];
          $dst = rtrim($snapDir0, "/") . "/" . $gname . "_t" . $hc . "/";
          if (!is_dir($dst)) {
            SimSearch_CopyDir($gameDir, $dst);
            $st = $bridgeState;
            if ($st === null) {
              try { $st = SimFeat_BuildState($player, $branch, $candRecs); }
              catch (Throwable $e) { $st = null; }
            }
            file_put_contents(rtrim($snapDir0, "/")
              . "/teacher_snap_index.jsonl",
              json_encode(["snap" => $gname . "_t" . $hc, "game" => $gname,
                "hcount" => $hc, "branch" => $branch, "player" => $player,
                "turn" => intval($GLOBALS["currentTurn"] ?? 0),
                "cands" => $candRecs, "state" => $st,
                "priors" => $priors, "prior_pick" => $priorPick,
                "uncontested" => 1]) . "\\n", FILE_APPEND);
          }
        }
      } catch (Throwable $e) { /* capture must never break play */ }
    }
    return $priorPick;
  }"""

assert s.count(OLD) == 1, "uncontested-block anchor not unique"
s = s.replace(OLD, NEW)
p.write_text(s)
print("search.php: 1 edit OK (uncontested capture snapshot)")
print(f"search.php: sha256 before {before}")
print(f"search.php: sha256 after  {sha256(p)}")
print("capture-uncontested patch applied to", tree)
