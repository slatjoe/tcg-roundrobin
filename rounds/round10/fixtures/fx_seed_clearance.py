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

Fix pass (claude-reply-402c92f sec.3/F2): the label
plan is ENLARGED by the z > 1.0 uncontested superset
(class (a) + the (1.0, 1.5] diagnostic class + the
contested band). settings now records
planned_jobs_total_max (160) and
planned_jobs_per_shard_max (256 -- EQUAL to the
enforced cap). This fixture asserts the recorded
plan sits at or under the cap, so the enumeration
below, which runs AT the cap, is the re-proof at
the enlarged counts: no planned population can
exceed the enumerated one in any shard.

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

Sec.14 (2026-10-29): the recovery's TWO supplementary
families are enumerated too --
  A. 970,055,001 (fix pass 4): the 10 recovered jobs,
     W = 50, 500 values;
  B. 470,055,001 (sec.14): the newly qualifying
     states' supplementary labels. The job count is
     read from the published
     data/step0_capalign/supplementary_jobs.jsonl
     (69 jobs; span top at the count 478,390,718),
     and the family is ALSO cleared at the label
     shard cap (256 jobs; span top 497,091,279) --
     its lattice position (shard index 4) sits
     between shard 3's span top (397,091,279) and
     family A's base, value-disjoint from the
     shard-3 family on the shared lattice by the
     same offset argument as the round-9 families.
Both families' VALUES must be disjoint from every
prior family, from the probe eval and label families
(at their enumerated counts), and from each other;
family B's RANGE at the cap must clear shard 3's
span top and stay below family A's base.
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

    # fix pass: the recorded (enlarged) plan must sit
    # at or under the enforced cap the enumeration
    # below runs at -- per shard and in total.
    plan_shard = st["label"]["planned_jobs_per_shard_max"]
    plan_total = st["label"]["planned_jobs_total_max"]
    if plan_shard > lab_cap:
        fails.append("planned per-shard %d exceeds the "
                     "enforced cap %d the enumeration "
                     "proves at" % (plan_shard, lab_cap))
    if plan_total > 4 * lab_cap:
        fails.append("planned total %d exceeds 4 x cap "
                     "%d" % (plan_total, lab_cap))
    print("planned label counts (enlarged, superset "
          "included): total <= %d, per-shard <= %d, "
          "enforced cap %d -- enumeration at the cap "
          "covers the plan: %s"
          % (plan_total, plan_shard, lab_cap,
             plan_shard <= lab_cap
             and plan_total <= 4 * lab_cap))

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

    # ---- sec.14: the two supplementary families --------------
    supp_a_base = 970055001
    supp_a_vals = values(supp_a_base, 10, 50)
    supp_b_base = 470055001
    supp_b_path = os.path.join(
        R10, "data", "step0_capalign",
        "supplementary_jobs.jsonl")
    supp_b_n = sum(1 for l in open(supp_b_path)
                   if l.strip())
    supp_b_vals = values(supp_b_base, supp_b_n, 50)
    supp_b_cap_vals = values(supp_b_base, lab_cap, 50)
    shard3_top = span_top(lab_base + 3 * SHARD, lab_cap, 50)
    supp_b_top_n = span_top(supp_b_base, supp_b_n, 50)
    supp_b_top_cap = span_top(supp_b_base, lab_cap, 50)
    for nm, vs in (("supp-A 970055001 (10 jobs)", supp_a_vals),
                   ("supp-B 470055001 (%d jobs)" % supp_b_n,
                    supp_b_vals),
                   ("supp-B at the 256 cap", supp_b_cap_vals)):
        for other_nm, other in (
                ("prior", prior_vals), ("probe labels",
                                         lab_vals),
                ("probe eval", eval_vals)):
            inter = vs & other
            if inter:
                fails.append("%s values collide with %s: "
                             "%d values" % (nm, other_nm,
                                            len(inter)))
    if supp_a_vals & supp_b_cap_vals:
        fails.append("supp-A values collide with supp-B "
                     "values at the cap")
    if not (shard3_top < supp_b_base
            and supp_b_top_cap < supp_a_base):
        fails.append("supp-B range at the cap [%d, %d] "
                     "does not sit strictly between "
                     "shard 3's span top %d and supp-A's "
                     "base %d"
                     % (supp_b_base, supp_b_top_cap,
                        shard3_top, supp_a_base))
    print("supplementary families (sec.14): A base %d "
          "(10 jobs, %d values); B base %d (%d jobs "
          "from the published supplementary set, span "
          "top %d; at the cap %d, top %d, between "
          "shard-3 top %d and A's base): disjoint "
          "from all families and each other: %s"
          % (supp_a_base, len(supp_a_vals), supp_b_base,
             supp_b_n, supp_b_top_n, lab_cap,
             supp_b_top_cap, shard3_top, not fails))

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
