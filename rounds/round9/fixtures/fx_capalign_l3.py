#!/usr/bin/env python3
"""Fixture: the sec.14 round-9 cap-aligned co-report
(stage3-capalign-addendum.json, produced by
code/capalign_l3.py) against the published reads it
co-reports and the figures in claude-reply-28c2065
sec.2.

A1 the addendum's as-run blocks equal the published
   primaries exactly (mean, CI, jobs) for both
   stages -- capalign_l3.py aborts otherwise at
   generation time; this pins the committed
   artifact.
A2 the cap-aligned point estimates round to
   Claude's figures at his precision: Stage 2
   +0.0565, Stage 3 +0.0417.
A3 the cap-aligned CIs sit within 0.0007 of
   Claude's on every bound (the stated bootstrap
   draw difference), and neither interval crosses
   0.
A4 the overshoot table: horizon end-turn median 93
   and max 268 at both stages; decisive worlds
   after turn 61 number 591 (Stage 2) and 589
   (Stage 3) on the addendum's stated basis.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R9 = os.path.join(HERE, "..")
FAILED = []


def check(name, cond, extra=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name,
                       (" -- " + extra) if extra else ""))
    if not cond:
        FAILED.append(name)


def main():
    add = json.load(open(os.path.join(
        R9, "stage3-capalign-addendum.json")))
    pub2 = json.load(open(os.path.join(
        R9, "data", "stage2", "stage2_read.json")))
    pub3 = json.load(open(os.path.join(
        R9, "data", "stage3", "attr_read.json")))
    for stage, add_s, pub in (("stage2", add["stage2"], pub2),
                              ("stage3", add["stage3"], pub3)):
        ar = add_s["as_run"]
        check("A1 %s: addendum as-run == published "
              "primary exactly" % stage,
              ar["mean_diff"] == pub["primary"]["mean_diff"]
              and ar["ci"] == pub["primary"]["ci"]
              and ar["jobs"] == pub["primary"]["jobs"])
    check("A2: cap-aligned point estimates round to "
          "Claude's +0.0565 / +0.0417",
          round(add["stage2"]["cap_aligned"]["mean_diff"], 4)
          == 0.0565
          and round(add["stage3"]["cap_aligned"]
                    ["mean_diff"], 4) == 0.0417,
          "s2 %.6f s3 %.6f"
          % (add["stage2"]["cap_aligned"]["mean_diff"],
             add["stage3"]["cap_aligned"]["mean_diff"]))
    for stage, his in (("stage2", (0.0406, 0.0737)),
                       ("stage3", (0.0320, 0.0527))):
        ci = add[stage]["cap_aligned"]["ci"]
        check("A3 %s: cap CI within 0.0007 of Claude's "
              "and clear of 0" % stage,
              abs(ci[0] - his[0]) <= 0.0007
              and abs(ci[1] - his[1]) <= 0.0007
              and ci[0] > 0,
              "mine [%0.4f, %0.4f], his [%0.4f, %0.4f]"
              % (ci[0], ci[1], his[0], his[1]))
    for stage, n61 in (("stage2", 591), ("stage3", 589)):
        ov = add[stage]["overshoot"]
        check("A4 %s: horizon median 93 / max 268; "
              "decisive after turn 61 = %d" % (stage, n61),
              ov["horizon_turns_median"] == 93
              and ov["horizon_turns_max"] == 268
              and ov["decisive_after_turn61"] == n61)
    print("fx_capalign_l3: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
