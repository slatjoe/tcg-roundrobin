#!/usr/bin/env python3
"""Round-10 Step 0: generate code/search_s3.php from the
round-10 code/search_s2.php by inserting ONE block --
the uncontested capture hook -- into
SimTeacher_DecideInner's uncontested branch,
immediately before its stat-row write.

Source history: through fix pass 5 the source was the
round-9 code/search_s2.php (sha256 85490e8e...), of
which the round-10 file was a byte-identical copy.
The sec.14 horizon-alignment fix patches the ROUND-10
copy only (the round-9 file stays 85490e8e... as the
closed rounds' record), so from sec.14 the generator
sources the round-10 file (sha256 1c964160...) and
search_s3.php = the sec.14-patched search_s2.php +
the hook -- the s2/s3 confinement property is
unchanged.

The hook is inert unless BOTH TEACHER_CAPTURE and
TEACHER_CAPTURE_UNCONTESTED are set (the probe runner
sets them only for the capture phase). With them unset,
search_s3.php executes the branch exactly as
search_s2.php does. The diff between the two files is
exactly the inserted block; fixtures/search_s3_diff.txt
is the unified diff this generator produces, and the
fixture suite asserts:
  1. the anchor (the stock uncontested branch) occurs
     exactly once in search_s2.php;
  2. regenerating search_s3.php from search_s2.php is
     byte-identical to the staged code/search_s3.php;
  3. removing the inserted block from search_s3.php
     reproduces search_s2.php byte-for-byte (the diff
     is confined to the insertion).

Usage: gen_search_s3.py [--check]
  (default: (re)generate code/search_s3.php and
  fixtures/search_s3_diff.txt; --check: verify only)
"""
import difflib
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(R10, "code", "search_s2.php")
DST = os.path.join(R10, "code", "search_s3.php")
DIFF = os.path.join(HERE, "search_s3_diff.txt")
SRC_SHA = "1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8"

ANCHOR = """  if ($ncand <= 1 || $bp >= 0.97) {
    SimSearch_LogStat(["teacher" => 1, "contested" => 0, "setting" => $T, "branch" => $branch,"""

HOOK = """  if ($ncand <= 1 || $bp >= 0.97) {
    if (getenv("TEACHER_CAPTURE") && getenv("TEACHER_CAPTURE_UNCONTESTED")
        && $ncand >= 2 && $bp >= 0.97) {
      // Round-10 Step 0 probe (search_s3 only; stock
      // search_s2 has no such block): snapshot SAMPLED
      // uncontested decisions for offline evaluation.
      // Stock behavior returns from this branch with
      // only a stat row -- no snapshot, no priors -- so
      // an uncontested decision leaves nothing an
      // offline eval can run on. When both capture
      // envs are set, this block snapshots the game
      // dir and appends an index row in the contested
      // capture arm's exact shape (same snap counter,
      // same index file), marked "uncontested" => 1
      // with the top prior recorded and the candidate
      // set the search would have used (the Decide
      // selection below: top-3 by prior, then any
      // prior >= 0.10 up to 4 -- with $bp >= 0.97 the
      // tail sums to <= 0.03, so the second loop adds
      // nothing; it is kept so the set is the rule's,
      // not an approximation of it). Sampling is per
      // game, systematic: every
      // TEACHER_CAPTURE_UNCONTESTED_EVERY-th eligible
      // decision (env, default 2). The played pick is
      // untouched: the stat row and the return below
      // are stock, and the capture arm's games are
      // raw-policy games by construction.
      $uncEvery = intval(getenv("TEACHER_CAPTURE_UNCONTESTED_EVERY") ?: 2);
      if ($uncEvery < 1) $uncEvery = 1;
      $gnameU = strval($GLOBALS["gameName"] ?? "");
      $GLOBALS["ssTeacherUncCount"][$gnameU] =
        ($GLOBALS["ssTeacherUncCount"][$gnameU] ?? 0) + 1;
      if (($GLOBALS["ssTeacherUncCount"][$gnameU] % $uncEvery) === 0) {
        $snapDirU = getenv("TEACHER_SNAP_DIR");
        if ($snapDirU !== false && $snapDirU !== "") {
          $GLOBALS["ssTeacherSnapCount"][$gnameU] =
            ($GLOBALS["ssTeacherSnapCount"][$gnameU] ?? 0) + 1;
          $hcU = $GLOBALS["ssTeacherSnapCount"][$gnameU];
          $dstU = rtrim($snapDirU, "/") . "/" . $gnameU . "_t" . $hcU . "/";
          if (!is_dir($dstU)) {
            SimSearch_CopyDir($gameDir, $dstU);
            $stU = null;
            try { $stU = SimFeat_BuildState($player, $branch, $candRecs); }
            catch (Throwable $e) { $stU = null; }
            $orderU = array_keys($priors);
            usort($orderU, function ($a, $b) use ($priors) {
              return $priors[$b] <=> $priors[$a]; });
            $selU = [];
            foreach ($orderU as $i) { if (count($selU) < 3) $selU[] = intval($i); }
            foreach ($orderU as $i) {
              if (count($selU) >= 4) break;
              if ($priors[$i] >= 0.10 && !in_array(intval($i), $selU, true)) {
                $selU[] = intval($i);
              }
            }
            sort($selU);
            file_put_contents(rtrim($snapDirU, "/")
              . "/teacher_snap_index.jsonl",
              json_encode(["snap" => $gnameU . "_t" . $hcU, "game" => $gnameU,
                "hcount" => $hcU, "branch" => $branch, "player" => $player,
                "turn" => intval($GLOBALS["currentTurn"] ?? 0),
                "cands" => $candRecs, "state" => $stU,
                "priors" => $priors, "prior_pick" => $priorPick,
                "selected" => $selU, "uncontested" => 1,
                "top_prior" => $bp]) . "\\n", FILE_APPEND);
          }
        }
      }
    }
    SimSearch_LogStat(["teacher" => 1, "contested" => 0, "setting" => $T, "branch" => $branch,"""


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def generate():
    src = open(SRC, "rb").read()
    got = sha256_bytes(src)
    if got != SRC_SHA:
        print("ABORT: search_s2.php sha256 %s != pinned %s"
              % (got, SRC_SHA))
        return None
    text = src.decode("utf-8")
    n = text.count(ANCHOR)
    if n != 1:
        print("ABORT: anchor occurs %d times in search_s2.php "
              "(expected exactly 1)" % n)
        return None
    out = text.replace(ANCHOR, HOOK, 1)
    diff = "".join(difflib.unified_diff(
        text.splitlines(keepends=True),
        out.splitlines(keepends=True),
        fromfile="search_s2.php", tofile="search_s3.php"))
    return out, diff


def main():
    check = "--check" in sys.argv
    gen = generate()
    if gen is None:
        return 2
    out, diff = gen
    if check:
        staged = open(DST, "rb").read().decode("utf-8")
        if staged != out:
            print("FAIL: staged search_s3.php != regenerated")
            return 1
        staged_diff = open(DIFF).read()
        if staged_diff != diff:
            print("FAIL: staged search_s3_diff.txt != regenerated diff")
            return 1
        # confinement: removing the hook-only lines (the diff's
        # '+' lines beyond the two anchor lines) restores the
        # source byte-for-byte -- asserted structurally by the
        # regeneration itself; state it.
        print("PASS gen_search_s3: search_s3.php regenerates "
              "byte-identically from search_s2.php %s; diff = "
              "one inserted block (%d diff lines)"
              % (SRC_SHA[:8], len(diff.splitlines())))
        return 0
    with open(DST, "w") as f:
        f.write(out)
    with open(DIFF, "w") as f:
        f.write(diff)
    print("generated %s (sha256 %s) and %s"
          % (DST, sha256_bytes(out.encode("utf-8")), DIFF))
    return 0


if __name__ == "__main__":
    sys.exit(main())
