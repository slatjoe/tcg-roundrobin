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

  PILOT (planned): labels base 570055001 + shard x
  10^8, 4 shards, at the ENFORCED cap 512 jobs/shard,
  W = 50 (span per shard 52,637,046 < 10^8).

Assertions: the pilot family's RANGES are disjoint
from every prior family's range; the pilot VALUES
are disjoint from every prior family's values; the
pilot capture seed block 25001-25050 (x both seats)
and the pre-gate block 8601-8610 are disjoint from
every used game-seed block (incl. reserved 9001-9200
and the probe's 24001-24090).
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
    (1001, 1200), (2001, 2200), (8001, 8200),
    (9001, 9200),          # RESERVED -- untouched
    (10001, 10400), (21001, 21100), (22001, 22100),
    (23001, 23200), (24001, 24090),
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
                       ("pregate", 8601, 8610)):
        bad = [(a, b) for a, b in USED_GAME_BLOCKS
               if not (hi < a or lo > b)]
        check("%s seeds %d-%d disjoint from used blocks"
              % (nm, lo, hi), not bad, str(bad))
    print("fx_pilot_seeds: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
