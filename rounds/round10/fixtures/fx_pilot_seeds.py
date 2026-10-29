#!/usr/bin/env python3
"""Step 1 pilot fixture: seed clearance by ENUMERATION.

Families on the shared lattice (value(job j, world w)
= base + j x 100,003 + w x 31,337, w < W; label seed
bases are MEAS_SEED = base + shard x 10^8):

  PRIOR (recorded counts): the fx_seed_clearance.py
  list (round-8 labels at 547 jobs W<=100 in all
  shard-offset variants, r9s0 855001, r9s1 eval
  885001, r9s2 labels 955001, r9s3 labels 50055001)
  PLUS the probe's families at their enumerated
  counts (eval 30055001, 3300/shard, W=25; labels
  70055001, 256/shard, W=50) and sec.14's
  supplementary families (A 970055001, 10 jobs;
  B 470055001, 69 jobs AND at the 256 cap).

  PILOT (planned): labels base read from
  settings_pilot.json (700055001) + shard x 10^8,
  4 shards, at the ENFORCED cap 512 jobs/shard,
  W = 50 (span per shard 52,637,046 < 10^8).

USED_GAME_BLOCKS -- COMPLETED at fix pass 1
(claude-reply-acc55a1 sec.2.1: the first list omitted
the round-7 contention probe 8601-8604 -- which the
pre-gate's original 8601-8610 block overlapped --
and ten further D2 blocks). Sources:

  Round 9's D2 record (rounds/round9/
  gravy-calibrated-search-design.md sec.9, D2),
  which lists, checked against every range in the
  record to that date:
    fleets 1001-1200 / 2001-2200 / 8001-8200;
    probes 3000-series; controls 4001-4014;
    smokes 5001-5010 / 7001-7002; census 6001-6040;
    round-8 corpus 10001-10400; pre-gate control
    11001-11010; pilot equivalence 12001-12010;
    Gravy pre-gate 8501-8510; contention probe
    8601-8604; Gravy census 8801-8820; round-8 gate
    block 9001-9200 (RESERVED, never run, untouched).
  The 3000-series is entered as 3001-3022, from:
    3001/3002 concurrency probe (rounds/round3/
    builder-response-6a0d7d4.md); 3003-3006 fleet
    probe (rounds/round7/fleet-alignment.md);
    3007-3010 extended probe wave 1, run, with
    waves to 3022 registered (rounds/round7/
    extended-probe.md); 3011-3014 also played by
    the round-3 gate-fix test copy (rounds/round3/
    builder-response-8d13b0f.md).
  Blocks used SINCE D2 (rounds 9-10 packages):
    21001-21040 round-9 Stage 0/1 capture (D2
    proposal, run); 21041-21100 the registered
    Stage 1 extension range (a contingency block,
    registered in the probe's settings; never run,
    kept out of reuse); 22001-22100 Stage 2 games;
    23001-23200 Stage 3 fleet; 24001-24090 round-10
    probe capture (step0-probe-package.md);
    25001-25050 THIS pilot's capture block
    (step1-pilot-package.md sec.3 -- listed so the
    pre-gate check below proves the two pilot
    blocks also disjoint from each other via the
    same list mechanics: the capture check excludes
    its own entry by construction of the loop, see
    the checks; the pre-gate block 13001-13010 is
    checked against ALL entries incl. 25001-25050).

Assertions: the pilot family's RANGES are disjoint
from every prior family's range; the pilot VALUES
are disjoint from every prior family's values; the
pilot capture seed block 25001-25050 (x both seats)
and the pre-gate block 13001-13010 (moved at fix
pass 1 from 8601-8610, which overlapped the
contention probe 8601-8604) are disjoint from
every used game-seed block.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
STRIDE_J = 100003
STRIDE_W = 31337
SHARD = 100000000

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
    ("r10-probe-eval-30055001",
     [30055001 + s * SHARD for s in range(4)], 3300, 25),
    ("r10-probe-labels-70055001",
     [70055001 + s * SHARD for s in range(4)], 256, 50),
    ("r10-supp-A-970055001", [970055001], 10, 50),
    ("r10-supp-B-470055001", [470055001], 256, 50),
]

USED_GAME_BLOCKS = [
    # round 9's D2 list (sources in the docstring)
    (1001, 1200), (2001, 2200), (3001, 3022),
    (4001, 4014), (5001, 5010), (6001, 6040),
    (7001, 7002), (8001, 8200), (8501, 8510),
    (8601, 8604), (8801, 8820),
    (9001, 9200),          # RESERVED -- untouched
    (10001, 10400), (11001, 11010), (12001, 12010),
    # used since D2 (rounds 9-10)
    (21001, 21040), (21041, 21100), (22001, 22100), (23001, 23200),
    (24001, 24090),
    # this pilot's own capture block (the capture
    # check below skips its own entry; every other
    # block is checked against it too)
    (25001, 25050),
]


def values(base, njobs, W):
    out = set()
    for j in range(njobs):
        sb = base + j * STRIDE_J
        for w in range(W):
            out.add(sb + w * STRIDE_W)
    return out


def span(base, njobs, W):
    return (base, base + (njobs - 1) * STRIDE_J
            + (W - 1) * STRIDE_W)


def main():
    st = json.load(open(os.path.join(S1,
                                     "settings_pilot.json")))
    base = st["label"]["seed_base"]
    cap = st["label"]["shard_cap_jobs"]
    nsh = st["label"]["shards"]
    fails = []
    checks = 0

    def check(name, good, detail=""):
        nonlocal checks
        checks += 1
        print("%s %s %s" % ("PASS" if good else "FAIL",
                            name, detail))
        if not good:
            fails.append(name)

    prior_vals = set()
    prior_ranges = []
    for name, bases, nj, W in PRIOR:
        for b in bases:
            prior_vals |= values(b, nj, W)
            prior_ranges.append((span(b, nj, W), name))
    print("prior families: %d enumerated values"
          % len(prior_vals))

    pilot_vals = set()
    pilot_ranges = []
    for s in range(nsh):
        b = base + s * SHARD
        pilot_vals |= values(b, cap, 50)
        pilot_ranges.append(span(b, cap, 50))
    check("pilot span per shard < 10^8",
          all(hi - lo < SHARD for lo, hi in pilot_ranges),
          "span %d" % (pilot_ranges[0][1]
                       - pilot_ranges[0][0]))
    overlap = []
    for plo, phi in pilot_ranges:
        for (lo, hi), nm in prior_ranges:
            if not (phi < lo or plo > hi):
                overlap.append((nm, plo, phi, lo, hi))
    check("pilot ranges disjoint from every prior range",
          not overlap, str(overlap[:2]))
    inter = pilot_vals & prior_vals
    check("pilot values disjoint from every prior family",
          not inter, "%d collisions" % len(inter))
    print("pilot family: base %d, %d shards at cap %d, "
          "range [%d, %d]; %d values"
          % (base, nsh, cap, pilot_ranges[0][0],
             pilot_ranges[-1][1], len(pilot_vals)))

    for nm, lo, hi in (("capture", 25001, 25050),
                       ("pregate", 13001, 13010)):
        bad = [(a, b) for a, b in USED_GAME_BLOCKS
               if not (hi < a or lo > b)
               and (a, b) != (lo, hi)]
        check("%s seeds %d-%d disjoint from used blocks"
              % (nm, lo, hi), not bad, str(bad))
    print("fx_pilot_seeds: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
