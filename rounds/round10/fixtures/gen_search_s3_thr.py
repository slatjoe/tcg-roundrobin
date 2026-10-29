#!/usr/bin/env python3
"""Step 1 build generator: search_s3_thr.php from the
sec.14-fixed search_s3.php (fixture + build tool).

The threshold lift is ONE token: in SimTeacher_
DecideInner, the uncontested branch condition

    if ($ncand <= 1 || $bp >= 0.97) {

becomes

    if ($ncand <= 1 || $bp >= 1.01) {

Priors are probabilities (the top prior is in [0, 1],
recorded 1.0000 at its maximum in the probe's
inspection), so $bp >= 1.01 is unreachable: for any
decision with >= 2 candidates the branch no longer
returns the prior pick unsearched -- every such
decision is contested. The $ncand <= 1 disjunct is
untouched (a one-candidate decision has nothing to
contest). Everything else is byte-identical to the
sec.14 file: margin 1.5 / k 25 / hooks 8000 /
deadline 180 / horizon 62 at -1 (per-step horizon
check, horizon-forces-draw) ride in the pinned tuple
and the copied engine code; the candidate rule is
the copied selection block; the capture hook stays
in place, inert in the pilot (TEACHER_CAPTURE is
never set by the pilot's arms, and its own gate
still names 0.97 because it snapshots the OLD
build's uncontested class in the probe's arms only).

--check (the fixture form): assert the staged
search_s3_thr.php regenerates byte-identically from
the staged sec.14 search_s3.php, that the source
line occurs exactly once, and that the unified diff
is exactly the one-token change (diff staged at
fixtures/search_s3_thr_diff.txt).
"""
import difflib
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
OLD = "  if ($ncand <= 1 || $bp >= 0.97) {"
NEW = "  if ($ncand <= 1 || $bp >= 1.01) {"


def build(src):
    assert src.count(OLD) == 1, \
        "threshold line occurs %d times" % src.count(OLD)
    return src.replace(OLD, NEW)


def main():
    src = open(os.path.join(S1, "search_s3.php")).read()
    want = open(os.path.join(S1, "search_s3_thr.php")).read()
    got = build(src)
    diff = list(difflib.unified_diff(
        src.splitlines(), got.splitlines(),
        "search_s3.php (sec.14, 87779e8e)",
        "search_s3_thr.php (step1 build)", lineterm=""))
    staged = open(os.path.join(
        HERE, "search_s3_thr_diff.txt")).read().splitlines()
    ok = (got == want)
    print("search_s3.php sha256 %s"
          % hashlib.sha256(src.encode()).hexdigest())
    print("search_s3_thr.php sha256 %s"
          % hashlib.sha256(got.encode()).hexdigest())
    print("threshold line occurrences in source: %d"
          % src.count(OLD))
    print("diff lines: %d; staged diff matches: %s"
          % (len(diff), diff == staged))
    if ok and diff == staged:
        print("PASS gen_search_s3_thr: byte-identical "
              "regeneration; the diff is exactly the "
              "one-token threshold change")
        return 0
    print("FAIL gen_search_s3_thr: regeneration %s; "
          "diff %s" % (ok, diff == staged))
    return 1


if __name__ == "__main__":
    sys.exit(main())
