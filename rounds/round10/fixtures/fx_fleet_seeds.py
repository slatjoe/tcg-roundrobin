#!/usr/bin/env python3
"""Step 2+3 fleet seed freshness + label-family
disjointness (read-only; the label enumeration reads
only this package's own registration record -- the
families enumerated in fx_pilot_seeds.py's PRIOR plus
the pilot family at its registered cap).

GAME SEEDS: the fleet block 26001-26061 must be
disjoint from every completed block in
USED_GAME_BLOCKS (copied verbatim from
fixtures/fx_pilot_seeds.py, whose own header carries
the per-block sources), and it is the next
x0001-aligned block above the pilot's 25001-25050 --
the block convention of the whole record (21001,
22001, 23001, 24001, 25001, ...). Candidates checked
and rejected, stated in step2-fleet-package.md: any
reuse of 21001-25050 (all completed); 25051-25111
(unreserved but breaks the x0001 block convention and
sits inside the pilot block's decade).

LABEL SEEDS: families live on the lattice
seedBase + job x 100,003 + world x 31,337 (world <
W). The fleet family (base 1100055001, 4 shards at
+10^8, enforced cap 512 jobs/shard, W=50) is proven
disjoint -- RANGES and VALUES -- from every prior
family at its registered counts, with the pilot
family enumerated at its CAP (512/shard), the
strictest reading of its registration. The drafting
brief's candidate base 800055001 is REFUTED here: it
equals the pilot family's shard-1 base exactly.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
SETTINGS = json.load(open(os.path.join(
    R10, "code", "step2", "settings_fleet.json")))

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


# ---- game-seed blocks (verbatim from fx_pilot_seeds.py) ----
USED_GAME_BLOCKS = [
    (1001, 1200), (2001, 2200), (3001, 3022),
    (8001, 8200), (8501, 8510), (8601, 8604),
    (8601, 8610), (8801, 8820), (9001, 9200),
    (10001, 10040), (10501, 10520), (11001, 11010),
    (11011, 11040), (12001, 12010), (13001, 13010),
    (14001, 14006), (15001, 15004), (15501, 15530),
    (16001, 16004), (17001, 17004), (18001, 18004),
    (19001, 19012), (21001, 21040), (21041, 21100),
    (22001, 22100), (23001, 23200), (24001, 24090),
    (25001, 25050),
]
FLEET = (26001, 26061)

overlaps = [(lo, hi) for lo, hi in USED_GAME_BLOCKS
            if not (FLEET[1] < lo or FLEET[0] > hi)]
check("fleet game block 26001-26061 disjoint from "
      "every completed block", not overlaps,
      "overlaps: %s" % (overlaps,))
below = [hi for lo, hi in USED_GAME_BLOCKS if hi < FLEET[0]]
check("highest completed block below the fleet block "
      "is the pilot's 25050", max(below) == 25050,
      "max below = %d" % max(below))
above = [(lo, hi) for lo, hi in USED_GAME_BLOCKS
         if lo > FLEET[1]]
check("no completed block above the fleet block",
      not above, "above: %s" % (above,))
check("fleet block follows the record's x0001 block "
      "convention", FLEET[0] % 1000 == 1
      and FLEET[0] == 25001 + 1000,
      "fleet starts %d" % FLEET[0])
g = SETTINGS["games"]
check("settings register the fleet block",
      g["seeds"] == "26001-26061" and g["pairs"] == 122
      and g["teacher_games"] == 122
      and g["games_total"] == 244)
blocks = {(b["tag"], b["arm"], b["seat"], b["seeds"])
          for b in g["blocks"]}
check("settings blocks are the 8 registered blocks",
      blocks == {
          ("t1a", "teacher", 1, "26001-26031"),
          ("t1b", "teacher", 1, "26032-26061"),
          ("t2a", "teacher", 2, "26001-26031"),
          ("t2b", "teacher", 2, "26032-26061"),
          ("r1a", "raw", 1, "26001-26031"),
          ("r1b", "raw", 1, "26032-26061"),
          ("r2a", "raw", 2, "26001-26031"),
          ("r2b", "raw", 2, "26032-26061")},
      "blocks: %s" % (sorted(blocks),))

# ---- the SMOKE block (package sec.19.4) ----
# One seed, played at both seats in both arms
# through the rebuilt runner's own blocks behind
# SMOKE=1 (claude-reply-5ea3a72 sec.2.3). Registered
# here and in fx_pilot_seeds.py's USED_GAME_BLOCKS
# so nothing reuses it. It continues the record's
# x0001 block convention one step above the fleet
# block; the runner's SMOKE section carries the
# literal seed.
SMOKE = (27001, 27001)
smoke_clash = [(lo, hi) for lo, hi in
               USED_GAME_BLOCKS + [FLEET]
               if not (SMOKE[1] < lo or SMOKE[0] > hi)]
check("smoke block 27001 disjoint from every "
      "completed block and the fleet block",
      not smoke_clash, "clashes: %s" % (smoke_clash,))
check("smoke block continues the x0001 convention "
      "one step above the fleet block",
      SMOKE[0] == FLEET[0] + 1000
      and SMOKE[0] % 1000 == 1,
      "smoke starts %d" % SMOKE[0])
check("smoke block is a single seed",
      SMOKE[0] == SMOKE[1])
games_sh = open(os.path.join(
    R10, "code", "step2", "run_fleet_games.sh")).read()
check("the games runner's SMOKE section carries "
      "the registered smoke seed 27001",
      "BLOCK_T1A_SEEDS=27001" in games_sh
      and "BLOCK_R2A_SEEDS=27001" in games_sh)

# ---- label-seed families ----
STRIDE_J, STRIDE_W = 100003, 31337
SHARD_STRIDE = 100000000


def span(base, jobs, w):
    if jobs <= 0:
        return None
    return (base, base + (jobs - 1) * STRIDE_J
            + (w - 1) * STRIDE_W)


def fam_spans(base, jobs, w, nshards, offsets):
    out = []
    for s in range(nshards):
        b = base + (s * SHARD_STRIDE if offsets else 0)
        sp = span(b, jobs, w)
        if sp:
            out.append(sp)
    return out


def fam_values(base, jobs, w, nshards, offsets):
    vals = set()
    for s in range(nshards):
        b = base + (s * SHARD_STRIDE if offsets else 0)
        for j in range(jobs):
            sb = b + j * STRIDE_J
            for wd in range(w):
                vals.add(sb + wd * STRIDE_W)
    return vals


# (name, base, jobs, W, nshards, shard-offsets) -- the
# fx_pilot_seeds.py PRIOR record, verbatim.
PRIOR = [
    ("r8-labels", 555001, 547, 100, 5, True),
    ("r8-labels", 777001, 547, 100, 5, True),
    ("r9s0-eval", 855001, 118, 50, 1, False),
    ("r9s1-eval", 885001, 240, 25, 1, False),
    ("r9s2-labels", 955001, 353, 50, 1, False),
    ("r9s3-labels", 50055001, 176, 50, 4, True),
    ("probe-eval", 30055001, 3300, 25, 4, True),
    ("probe-labels", 70055001, 256, 50, 4, True),
    ("probe-supp-A", 970055001, 10, 50, 1, False),
    ("probe-supp-B", 470055001, 256, 50, 1, False),
]
PILOT_CAP = ("pilot-labels@cap", 700055001, 512, 50, 4,
             True)

lab = SETTINGS["label"]
FLEET_LAB = ("fleet-labels", int(lab["seed_base"]),
             int(lab["shard_cap_jobs"]),
             int(lab["tuple"]["k"]), int(lab["shards"]),
             True)

check("the brief's candidate 800055001 IS the pilot "
      "family's shard-1 base (refuted as a fleet base)",
      800055001 == 700055001 + 1 * SHARD_STRIDE)
check("fleet label base differs from every prior base",
      all(FLEET_LAB[1] != p[1] for p in PRIOR + [PILOT_CAP]))

fleet_spans = fam_spans(*FLEET_LAB[1:])
prior_spans = []
for p in PRIOR + [PILOT_CAP]:
    prior_spans += [(p[0], sp) for sp in fam_spans(*p[1:])]
clash = []
for fs in fleet_spans:
    for name, ps in prior_spans:
        if not (fs[1] < ps[0] or fs[0] > ps[1]):
            clash.append((fs, name, ps))
check("fleet label RANGES disjoint from every prior "
      "family (pilot at cap)", not clash,
      "clashes: %s" % (clash[:3],))
internal = any(
    not (fleet_spans[i][1] < fleet_spans[j][0]
         or fleet_spans[i][0] > fleet_spans[j][1])
    for i in range(len(fleet_spans))
    for j in range(i + 1, len(fleet_spans)))
check("fleet label shards mutually disjoint", not internal)
span1 = fleet_spans[0][1] - fleet_spans[0][0] + 1
check("fleet per-shard span < the 10^8 shard stride",
      span1 - 1 < SHARD_STRIDE, "span %d" % (span1 - 1,))
nearest_below = max(ps[1] for _n, ps in prior_spans
                    if ps[1] < FLEET_LAB[1])
check("fleet base sits 47,362,954 above the nearest "
      "prior span below (pilot shard-3 top at cap)",
      FLEET_LAB[1] - nearest_below == 47362954,
      "distance %d" % (FLEET_LAB[1] - nearest_below,))

fleet_vals = fam_values(*FLEET_LAB[1:])
prior_vals = set()
for p in PRIOR + [PILOT_CAP]:
    prior_vals |= fam_values(*p[1:])
inter = fleet_vals & prior_vals
check("fleet label VALUES disjoint from every prior "
      "family (pilot at cap)", not inter,
      "intersections: %d (fleet %d values vs prior %d)"
      % (len(inter), len(fleet_vals), len(prior_vals)))
check("settings register the fleet label family",
      FLEET_LAB[1] == 1100055001
      and int(lab["seed_stride_per_shard"]) == SHARD_STRIDE
      and int(lab["shards"]) == 4)

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
