#!/usr/bin/env python3
"""Round-10 Step 0 fixture: seed clearance for the
probe's two seed families, proven by ENUMERATION at
the planned counts (claude-reply-9b04ad1 sec.6: label
seed bases range-disjoint proven from PLANNED job
counts; the round-9 standard for eval families is
value-disjointness on the shared lattice).

Lattice (all rounds): value(job j, world w) =
base + j x 100,003 + w x 31,337, w < W.

Prior families at their RECORDED counts (sources:
rounds/round8/ data manifests + settings_round8.json;
rounds/round9/data/stage{0,1,2,3}/ reports and
settings files). Where a family's sharding is
uncertain (round 8), every shard-offset variant is
enumerated at the full recorded count -- an
over-approximation that only strengthens the proof.

Probe families at the PLANNED counts
(settings_probe.json): eval <= 3,300 states/shard,
W = 25; labels <= 256 jobs/shard (the builder's
enforced cap), W = 50.

Assertions:
  1. probe label RANGES [base, span top] are disjoint
     from every prior family's range (interval check)
     and the probe label base exceeds every prior
     family's span top at recorded counts;
  2. probe label VALUES are disjoint from all prior
     values (set check) and from probe eval values;
  3. probe eval VALUES are disjoint from all prior
     values;
  4. capture game seeds 24001-24090 are disjoint from
     every used game-seed block (incl. the reserved
     9001-9200, which stays untouched).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.abspath(os.path.join(HERE, ".."))
STRIDE_J = 100003
STRIDE_W = 31337
SHARD = 100000000

# (label, bases, max jobs per base, W)
PRIOR = [
    ("r8-labels-555001", [555001 + s * SHARD for s in range(4)]
     + [555001], 547, 100),
    ("r8-labels-777001", [777001 + s * SHARD for s in range(4)]
     + [777001], 547, 100),
    ("r9s0-labels-855001", [855001], 118, 50),
    ("r9s1-eval-885001", [885001 + s * SHARD for s in range(4)],
     240, 25),
    ("r9s2-labels-955001", [955001 + s * SHARD for s in range(4)],
     353, 50),
    ("r9s3-labels-50055001",
     [50055001 + s * SHARD for s in range(4)], 176, 50),
]

USED_GAME_BLOCKS = [
    (1001, 1200), (2001, 2200), (8001, 8200),
    (9001, 9200),          # RESERVED -- untouched
    (10001, 10400), (21001, 21100),  # stage-1 base + extensions
    (22001, 22100), (23001, 23200),
]


def values(base, njobs, W):
    out = set()
    for j in range(njobs):
        sb = base + j * STRIDE_J
        for w in range(W):
            out.add(sb + w * STRIDE_W)
    return out


def span_top(base, njobs, W):
    return base + (njobs - 1) * STRIDE_J + (W - 1) * STRIDE_W


def main():
    st = json.load(open(os.path.join(R10, "code",
                                     "settings_probe.json")))
    eval_base = st["eval"]["seed_base"]
    eval_max = st["eval"]["planned_states_per_shard_max"]
    lab_base = st["label"]["seed_base"]
    lab_cap = st["label"]["shard_cap_jobs"]
    fails = []

    prior_vals = set()
    prior_tops = []
    for name, bases, nj, W in PRIOR:
        for b in bases:
            prior_vals |= values(b, nj, W)
            prior_tops.append((span_top(b, nj, W), name, b))
    print("prior families: %d enumerated values; highest "
          "span top %d (%s)"
          % (len(prior_vals), max(t for t, _, _ in prior_tops),
             max(prior_tops)[1]))

    # probe label ranges vs prior ranges (per shard variant)
    for s in range(4):
        b = lab_base + s * SHARD
        top = span_top(b, lab_cap, 50)
        for t, name, pb in prior_tops:
            pbase = pb
            if not (top < pbase or b > t):
                fails.append("label range shard %d [%d, %d] "
                             "overlaps %s [%d, %d]"
                             % (s, b, top, name, pbase, t))
        if b <= 69091039 and s == 0:
            fails.append("label base %d does not clear the "
                         "Stage 3 span top 69,091,039" % b)
        if top >= (s + 1) * SHARD:
            fails.append("label span shard %d top %d crosses "
                         "the 10^8 shard boundary" % (s, top))
    print("label family: base %d, cap %d jobs/shard, span "
          "top %d (shard 0)" % (lab_base, lab_cap,
                                span_top(lab_base, lab_cap, 50)))

    lab_vals = set()
    for s in range(4):
        lab_vals |= values(lab_base + s * SHARD, lab_cap, 50)
    inter = lab_vals & prior_vals
    if inter:
        fails.append("label values collide with prior "
                     "families: %d values" % len(inter))

    eval_vals = set()
    for s in range(4):
        eval_vals |= values(eval_base + s * SHARD, eval_max, 25)
    inter = eval_vals & prior_vals
    if inter:
        fails.append("eval values collide with prior "
                     "families: %d values" % len(inter))
    inter = eval_vals & lab_vals
    if inter:
        fails.append("eval values collide with probe label "
                     "values: %d" % len(inter))
    print("probe values: eval %d, labels %d, disjoint from "
          "prior and each other: %s"
          % (len(eval_vals), len(lab_vals), not fails))

    cap = st["capture"]
    lo = int(cap["seeds_seat1"].split("-")[0])
    hi = int(cap["seeds_seat2"].split("-")[1])
    for a, b in USED_GAME_BLOCKS:
        if not (hi < a or lo > b):
            fails.append("capture seeds %d-%d overlap used "
                         "block %d-%d" % (lo, hi, a, b))
    print("capture seeds %d-%d disjoint from %d used blocks "
          "(incl. reserved 9001-9200)" % (lo, hi,
                                          len(USED_GAME_BLOCKS)))

    if fails:
        for f in fails:
            print("FAIL fx_seed_clearance: " + f)
        return 1
    print("PASS fx_seed_clearance: label ranges disjoint "
          "from all prior families at planned counts; eval "
          "and label values disjoint from prior values and "
          "each other; capture seeds clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
