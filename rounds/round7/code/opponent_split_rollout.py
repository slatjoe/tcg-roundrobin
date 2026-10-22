#!/usr/bin/env python3
"""Appendix analysis for the fleet-alignment registration (Claude
claude-reply-01250ac sec.3, report-only): split the stage-3 report's
rollout capped-share series BY OPPONENT TYPE at the band level.

Method = stage3-report.md sec.2, unchanged: version acceptance
timestamps from trainer_v4.log ("ACCEPTED -> version N" lines); each
rollout game's timestamp and opponent class from
traj_w*/games_meta.jsonl (fields: game, learner_seat, opp, ts); its
capped flag from games_w*.jsonl joined on game id (meta "game" ==
games row "gamename"); a game is binned to the version whose
acceptance interval contains its ts (games before the first
acceptance are version 0). Bands are the report's (25-version
bands). Opponent classes are the meta rows' own opp values
("self" = learner-vs-learner, "heuristic", "bc" = the BC anchor).

Read-only. Prints one row per band x opponent class plus band and
overall totals, which must reproduce the report's pooled band table
(games / capped) exactly.
"""
import json
import re
import sys
from collections import defaultdict

TREE = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3"

# acceptance timestamps: version -> ts (log lines are UTC ISO)
import datetime
acc = {}
for ln in open(TREE + "/trainer_v4.log"):
    m = re.search(r"^(\S+) .*ACCEPTED -> version (\d+)", ln)
    if m:
        ts = datetime.datetime.fromisoformat(
            m.group(1).replace("Z", "+00:00")).timestamp()
        acc[int(m.group(2))] = ts
versions = sorted(acc)

def version_of(ts):
    v = 0
    for ver in versions:
        if acc[ver] <= ts:
            v = ver
        else:
            break
    return v

capped = {}
import glob
for path in glob.glob(TREE + "/games_w*.jsonl"):
    for ln in open(path):
        r = json.loads(ln)
        capped[str(r["gamename"])] = 1 if r.get("capped") else 0

bands = [(i, i + 24) for i in range(0, 400, 25)]
counts = defaultdict(lambda: [0, 0])   # (band_lo, opp) -> [games, capped]
band_tot = defaultdict(lambda: [0, 0])
opp_tot = defaultdict(lambda: [0, 0])
missing = 0
for path in sorted(glob.glob(TREE + "/traj_w*/games_meta.jsonl")):
    for ln in open(path):
        m = json.loads(ln)
        gid = str(m["game"])
        if gid not in capped:
            missing += 1
            continue
        v = version_of(float(m["ts"]))
        lo = (v // 25) * 25
        c = capped[gid]
        counts[(lo, m["opp"])][0] += 1
        counts[(lo, m["opp"])][1] += c
        band_tot[lo][0] += 1
        band_tot[lo][1] += c
        opp_tot[m["opp"]][0] += 1
        opp_tot[m["opp"]][1] += c

opps = sorted(opp_tot)
print("band        " + "".join("%-28s" % ("opp=" + o) for o in opps)
      + "band total")
for lo, hi in bands:
    cells = []
    for o in opps:
        n, c = counts[(lo, o)]
        cells.append("%d/%d %.4f" % (c, n, c / n if n else float("nan")))
    n, c = band_tot[lo]
    print("v%-3d-%-6d" % (lo, hi)
          + "".join("%-28s" % x for x in cells)
          + "%d/%d %.4f" % (c, n, c / n if n else float("nan")))
print("OVERALL     " + "".join(
    "%-28s" % ("%d/%d %.4f" % (opp_tot[o][1], opp_tot[o][0],
                               opp_tot[o][1] / opp_tot[o][0]))
    for o in opps))
tn = sum(v[0] for v in band_tot.values())
tc = sum(v[1] for v in band_tot.values())
print("TOTAL %d games, %d capped, share %.4f | meta rows without a "
      "games row: %d" % (tn, tc, tc / tn, missing))
