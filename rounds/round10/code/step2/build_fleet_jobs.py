#!/usr/bin/env python3
"""Round-10 Step 2+3 fleet L3 jobs builder: every
overturn the live threshold-lifted teacher captured in
the FLEET's teacher arm becomes one label job
(claude-reply-26cc773 sec.3: L3 at the registered
configuration on ALL teacher-arm overturns, both
classes, for the Step 2 co-read).

Byte-derived from the Step 1 pilot's
build_pilot_jobs.py (d855c7aa...) with ONLY this
docstring and the print branding changed -- the
pairing, class enrichment, sharding and cap semantics
are the pilot's, unchanged. Inputs:

  --stream PREFIX=INDEX_PATH ...   the games streams'
      teacher_snap_index.jsonl files (one row per
      overturn, written by Decide's overturn block)
  --stats PATH ...                 the same streams'
      search_stats.jsonl files (the live stat rows;
      every searched decision's row carries priors,
      pick, overturn, mean_diff, se_diff, setting)

CLASS PAIRING (of record for this package): each index
row is paired to its live stat row by the ORDER-AWARE
key join -- the n-th index row at key (game, branch,
player, turn, prior_pick, teacher_pick) pairs the n-th
overturn stat row at the same key in stream order. (The
probe package sec.1.2 validated this join against the
snapshot pairing on 975/975 round-9 jobs.) The builder
ABORTS if any key's index count != its overturn-stat
count, or if the totals disagree -- a mispairing is a
build failure, never a silent class error.

Each job carries, beside the s2 shape:
  class       "contested" (top prior < 0.97) or
              "newly_contested" (top prior >= 0.97),
              from the paired stat row's priors
  top_prior   max(priors) of the paired stat row
  mean_diff / se_diff   the live statistic
  z           mean_diff / se_diff; se_diff == 0 with
              mean_diff > 0 -> z = 999.0 with
              z_nonfinite true (STRICT JSON: every
              write uses allow_nan=False, so a
              non-finite value anywhere aborts the
              build instead of reaching a PHP reader)

Jobs are sharded by sha256(game) mod NSHARD (a game's
jobs share a shard: the game-clustered read and the
label seed bases stay well-defined). A shard over the
settings cap aborts (the seed family's span proof in
fixtures/fx_pilot_seeds.py runs at the cap).

Usage:
  build_pilot_jobs.py --stream PREFIX=INDEX_PATH
      [--stream ...] --stats STATS_PATH [--stats ...]
      --settings settings_fleet.json --out jobs_all.jsonl
      --shard-prefix jobs_shard --report jobs_report.json
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

BOUNDARY = 0.97


def dumps_strict(obj):
    return json.dumps(obj, allow_nan=False)


def job_key(game, branch, player, turn, prior_pick, pick):
    return (str(game), str(branch), int(player),
            int(turn), int(prior_pick), int(pick))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", action="append", required=True)
    ap.add_argument("--stats", action="append", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard-prefix", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--nshard", type=int, default=4)
    a = ap.parse_args()

    settings = json.load(open(a.settings))
    label_tuple = settings["label"]["tuple"]
    cap = int(settings["label"]["shard_cap_jobs"])

    # ---- stat rows: the overturn population, in stream order
    stat_by_key = defaultdict(list)
    stat_rows_total = 0
    for path in a.stats:
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("teacher") != 1 or r.get("overturn") != 1:
                continue
            stat_rows_total += 1
            k = job_key(r["game"], r["branch"], r["player"],
                        r.get("turn") or 0, r["prior_pick"],
                        r["pick"])
            stat_by_key[k].append(r)

    # ---- index rows, paired order-aware
    jobs = []
    seen = set()
    rows_in = 0
    used = Counter()
    for spec in a.stream:
        prefix, path = spec.split("=", 1)
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            rows_in += 1
            for key in ("snap", "game", "cands", "teacher_pick",
                        "prior_pick"):
                if key not in r:
                    print("ABORT: %s row %s is not a live "
                          "overturn row (missing %s)"
                          % (path, r.get("snap"), key))
                    return 2
            snap = str(r["snap"])
            if snap in seen:
                print("ABORT: duplicate snap %s across games "
                      "streams" % snap)
                return 2
            seen.add(snap)
            tp, pp = int(r["teacher_pick"]), int(r["prior_pick"])
            if tp == pp:
                print("ABORT: snap %s has teacher_pick == "
                      "prior_pick (%d): not an overturn"
                      % (snap, tp))
                return 2
            k = job_key(r["game"], r["branch"], r["player"],
                        r.get("turn") or 0, pp, tp)
            n = used[k]
            if n >= len(stat_by_key.get(k, [])):
                print("ABORT: snap %s key %s has no unpaired "
                      "overturn stat row (index/stat pairing "
                      "mismatch)" % (snap, k))
                return 2
            used[k] += 1
            st = stat_by_key[k][n]
            priors = st.get("priors")
            if not isinstance(priors, dict) and \
                    not isinstance(priors, list):
                print("ABORT: paired stat row for snap %s "
                      "carries no priors array" % snap)
                return 2
            pv = list(priors.values()) if isinstance(
                priors, dict) else list(priors)
            top_prior = max(float(x) for x in pv)
            cls = ("contested" if top_prior < BOUNDARY
                   else "newly_contested")
            md = st.get("mean_diff")
            sd = st.get("se_diff")
            if md is None or sd is None:
                print("ABORT: paired stat row for snap %s "
                      "has no contrast (mean_diff/se_diff "
                      "null) but overturn == 1" % snap)
                return 2
            md, sd = float(md), float(sd)
            if sd == 0.0:
                if md <= 0:
                    print("ABORT: snap %s se_diff 0 with "
                          "mean_diff %.4f (cannot fire)"
                          % (snap, md))
                    return 2
                z, znf = 999.0, True
            else:
                z, znf = md / sd, False
            jobs.append({
                "snap_dir": prefix + "/" + snap,
                "snap": snap, "game": str(r["game"]),
                "player": int(r["player"]),
                "branch": str(r["branch"]),
                "turn": int(r.get("turn") or 0),
                "cands": r["cands"],
                "selected": sorted({pp, tp}),
                "prior_pick": pp, "teacher_pick": tp,
                "class": cls, "top_prior": top_prior,
                "mean_diff": md, "se_diff": sd,
                "z": z, "z_nonfinite": znf,
                "setting": label_tuple,
            })

    unpaired = {k: len(v) - used[k]
                for k, v in stat_by_key.items()
                if used[k] != len(v)}
    if unpaired:
        print("ABORT: %d overturn stat rows never paired to "
              "an index row (first keys: %s)"
              % (sum(unpaired.values()),
                 list(unpaired)[:3]))
        return 2
    if len(jobs) != stat_rows_total:
        print("ABORT: jobs %d != overturn stat rows %d"
              % (len(jobs), stat_rows_total))
        return 2

    with open(a.out, "w") as f:
        for j in jobs:
            f.write(dumps_strict(j) + "\n")
    shards = {s: [] for s in range(a.nshard)}
    for j in jobs:
        s = int(hashlib.sha256(
            str(j["game"]).encode()).hexdigest(), 16) % a.nshard
        shards[s].append(j)
    counts = {}
    for s, rows in shards.items():
        if len(rows) > cap:
            print("ABORT: shard %d holds %d jobs, over the "
                  "registered cap %d (the seed span proof "
                  "runs at the cap)" % (s, len(rows), cap))
            return 2
        with open("%s%d.jsonl" % (a.shard_prefix, s), "w") as f:
            for j in rows:
                f.write(dumps_strict(j) + "\n")
        counts[str(s)] = len(rows)
    classes = Counter(j["class"] for j in jobs)
    games = sorted({j["game"] for j in jobs})
    report = {"jobs": len(jobs), "games_with_jobs": len(games),
              "index_rows_total": rows_in,
              "overturn_stat_rows": stat_rows_total,
              "classes": dict(classes),
              "shards": counts, "nshard": a.nshard,
              "shard_cap_jobs": cap,
              "label_tuple": label_tuple}
    with open(a.report, "w") as f:
        json.dump(report, f, indent=1, allow_nan=False)
    print("fleet jobs: %d overturns over %d games (index "
          "rows %d; classes %s; shards %s)"
          % (len(jobs), len(games), rows_in, dict(classes),
             counts))
    if not jobs:
        print("ABORT: zero overturns captured - nothing to "
              "label")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
