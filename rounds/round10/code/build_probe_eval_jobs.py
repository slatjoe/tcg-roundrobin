#!/usr/bin/env python3
"""Round-10 Step 0 probe: build the offline-eval job set
from the capture streams.

Fork of build_panel.py (round 9, 8f22d845...) with the
panel logic replaced: NO panel-size cap and NO per-game
cap -- the probe evaluates EVERY captured snapshot,
because its estimands are rates (tail fires per state
by prior band), and a capped panel would censor
exactly the denominators those rates need. Two row
classes arrive in the capture index (one stream per
seat, written by search_s3.php):

  * contested capture rows (the round-9 capture arm,
    unchanged): carry selected / priors, no
    "uncontested" key;
  * uncontested rows (the search_s3 hook): carry
    "uncontested": 1, top_prior, selected (the set the
    search would have used), priors, prior_pick --
    already SAMPLED at capture time (systematic
    per-game sampling, settings capture.
    uncontested_every); this builder does not resample.

Job shape = the s1_eval_main job shape (so the
byte-identical round-9 eval driver runs them) plus
the probe fields the analyzer needs:
  {snap_dir, snap, game, player, branch, turn, cands,
   selected, prior_pick, setting,
   priors, top_prior, uncontested}

A row missing selected/priors, a duplicated snap, or
a row whose setting would not match the run pin
aborts (exit 2) -- the eval driver re-checks the
setting per job before evaluating anything.

Usage: build_probe_eval_jobs.py --stream PREFIX=PATH
  [--stream ...] --settings settings_probe.json
  --out eval_jobs.jsonl --report eval_jobs_report.json
"""
import argparse
import json
import sys
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", action="append", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    settings = json.load(open(a.settings))
    eval_tuple = settings["eval"]["tuple"]

    jobs = []
    seen = set()
    rows_in = 0
    classes = Counter()
    per_game = Counter()
    games = set()
    for spec in a.stream:
        prefix, path = spec.split("=", 1)
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            rows_in += 1
            if "selected" not in r or "priors" not in r:
                print("ABORT: %s row %s is not a capture row "
                      "(no selected/priors)" % (path, r.get("snap")))
                return 2
            snap = str(r["snap"])
            if snap in seen:
                print("ABORT: duplicate snap %s across capture "
                      "streams" % snap)
                return 2
            seen.add(snap)
            unc = 1 if int(r.get("uncontested") or 0) == 1 else 0
            priors = [float(x) for x in r["priors"]]
            top = max(priors) if priors else 0.0
            if unc and top < 0.97:
                print("ABORT: uncontested row %s has top prior "
                      "%.4f < 0.97" % (snap, top))
                return 2
            if not unc and top >= 0.97:
                print("ABORT: contested row %s has top prior "
                      "%.4f >= 0.97" % (snap, top))
                return 2
            classes["uncontested" if unc else "contested"] += 1
            per_game[str(r["game"])] += 1
            games.add(str(r["game"]))
            jobs.append({
                "snap_dir": prefix + "/" + snap,
                "snap": snap, "game": str(r["game"]),
                "player": int(r["player"]),
                "branch": str(r["branch"]),
                "turn": int(r.get("turn") or 0),
                "cands": r["cands"],
                "selected": [int(x) for x in r["selected"]],
                "prior_pick": int(r["prior_pick"]),
                "setting": eval_tuple,
                "priors": priors,
                "top_prior": top,
                "uncontested": unc,
            })

    with open(a.out, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    report = {"states": len(jobs), "index_rows_total": rows_in,
              "classes": dict(classes),
              "games": len(games),
              "games_list": sorted(games),
              "eval_tuple": eval_tuple}
    with open(a.report, "w") as f:
        json.dump(report, f, indent=1)
    print("probe eval jobs: %d states (%s) over %d games "
          "(index rows %d)"
          % (len(jobs), dict(classes), len(games), rows_in))
    if not jobs:
        print("ABORT: zero captured states")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
