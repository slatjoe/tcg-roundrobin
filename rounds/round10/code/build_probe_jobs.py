#!/usr/bin/env python3
"""Round-10 Step 0 probe: build the L3 label job set
from the offline eval's per-state statistics.

Two classes (settings label.classes), and ONLY these:

  * "uncontested": uncontested states whose statistic
    would fire at the CURRENT margin
    (settings label.uncontested_margin -- PROPOSED
    1.5, flagged for the review in the package doc:
    the class prices what a threshold build gains
    under today's decision rule). teacher_pick = the
    eval's search pick.
  * "contested_band": contested states with z in
    (band_lo, band_hi] = (1.25, 1.5] -- the fires a
    margin of 1.25 would add over the current rule.

Job shape = the build_s3_jobs shape (so the
byte-identical s2_label_main driver runs them):
  {snap_dir, snap, game, player, branch, turn, cands,
   selected, prior_pick, teacher_pick, setting}
plus probe fields the label analyzer groups by:
  {probe_band, prior_band, z, top_prior}
selected = sorted {prior_pick, teacher_pick} exactly
as build_s3_jobs. A state whose search pick equals
its prior pick in a labeled class is a construction
error and aborts (exit 2), as does any shard
exceeding settings label.shard_cap_jobs -- the cap
is the range-disjointness bound for the label seed
family (span at the cap: (cap-1) x 100,003 + 49 x
31,337 = 27,036,278 from base 70055001, top
97,091,279 < 10^8, clear of the Stage 3 family's
span top 69,091,039). If the cap trips, the run
stops; it does not subsample quietly.

The report also prints the EXPECTED counts under the
alternative uncontested-margin definitions (1.25 and
1.0), so the review can rule on the class definition
with all three counts in front of it.

Usage: build_probe_jobs.py --states eval_states.jsonl
  --eval-jobs eval_jobs.jsonl --settings
  settings_probe.json --out jobs_all.jsonl
  --shard-prefix jobs_shard --report jobs_report.json
"""
import argparse
import hashlib
import json
import sys
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", required=True)
    ap.add_argument("--eval-jobs", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard-prefix", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    settings = json.load(open(a.settings))
    lab = settings["label"]
    label_tuple = lab["tuple"]
    unc_margin = float(lab["uncontested_margin"])
    lo, hi = float(lab["band_lo"]), float(lab["band_hi"])
    cap = int(lab["shard_cap_jobs"])
    nshard = int(lab["shards"])

    ejobs = {}
    for l in open(a.eval_jobs):
        if l.strip():
            j = json.loads(l)
            ejobs[str(j["snap"])] = j

    states = [json.loads(l) for l in open(a.states) if l.strip()]
    alt_counts = Counter()
    jobs = []
    seen = set()
    for r in states:
        if r["z"] is None:
            continue
        snap = str(r["snap"])
        for m in (1.25, 1.0):
            if int(r["uncontested"]) == 1 and r["z"] > m:
                alt_counts["uncontested@%.2f" % m] += 1
        cls = None
        if int(r["uncontested"]) == 1 and r["z"] > unc_margin:
            cls = "uncontested"
        elif int(r["uncontested"]) == 0 and lo < r["z"] <= hi:
            cls = "contested_band"
        if cls is None:
            continue
        ej = ejobs.get(snap)
        if ej is None:
            print("ABORT: state %s has no eval job" % snap)
            return 2
        if snap in seen:
            print("ABORT: duplicate state %s" % snap)
            return 2
        seen.add(snap)
        tp, pp = int(r["search_pick"]), int(r["prior_pick"])
        if tp == pp:
            print("ABORT: state %s in class %s has search "
                  "pick == prior pick" % (snap, cls))
            return 2
        jobs.append({
            "snap_dir": ej["snap_dir"], "snap": snap,
            "game": str(r["game"]), "player": int(r["player"]),
            "branch": str(r["branch"]),
            "turn": int(r.get("turn") or 0),
            "cands": ej["cands"],
            "selected": sorted({pp, tp}),
            "prior_pick": pp, "teacher_pick": tp,
            "setting": label_tuple,
            "probe_band": cls,
            "prior_band": r["prior_band"],
            "z": r["z"], "top_prior": r["top_prior"],
        })

    shards = {s: [] for s in range(nshard)}
    for j in jobs:
        s = int(hashlib.sha256(
            str(j["game"]).encode()).hexdigest(), 16) % nshard
        shards[s].append(j)
    counts = {}
    for s, rows in shards.items():
        if len(rows) > cap:
            print("ABORT: shard %d holds %d jobs > the "
                  "registered cap %d (the label seed "
                  "family's range-disjointness bound); "
                  "the run stops here -- subsampling is "
                  "a review decision, not a builder one"
                  % (s, len(rows), cap))
            return 2
        with open("%s%d.jsonl" % (a.shard_prefix, s), "w") as f:
            for j in rows:
                f.write(json.dumps(j) + "\n")
        counts[str(s)] = len(rows)
    with open(a.out, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    by_class = Counter(j["probe_band"] for j in jobs)
    report = {"jobs": len(jobs),
              "by_class": dict(by_class),
              "uncontested_margin": unc_margin,
              "band": [lo, hi],
              "alt_uncontested_counts": dict(alt_counts),
              "shards": counts, "nshard": nshard,
              "shard_cap_jobs": cap,
              "label_tuple": label_tuple,
              "games": len({j["game"] for j in jobs})}
    with open(a.report, "w") as f:
        json.dump(report, f, indent=1)
    print("probe label jobs: %d (%s); shards %s; "
          "uncontested counts at other margins: %s"
          % (len(jobs), dict(by_class), counts,
             dict(alt_counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
