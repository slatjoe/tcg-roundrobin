#!/usr/bin/env python3
"""Round-10 Step 0 probe: turn the offline eval's world
rows into per-state search statistics.

Input rows are s1_eval_main.php's output (the
byte-identical round-9 eval driver run at the probe
eval tuple, k = 25): one row per (snap, cand, world)
with result {outcome, winner, horizon, finished,
error?, fallbacks}. This analyzer recomputes, per
snapshot, EXACTLY the statistic SimTeacher_Decide
computes live (search_s2.php DecideInner), so a
would-fire here is the fire the live rule would have
produced on the same worlds:

  * a world's priced outcome is horizon_value (-1)
    when winner == 0 (horizon-ended or natural draw),
    else its raw outcome -- Decide's pricing inside
    the candidate means;
  * error / unfinished worlds are excluded per
    candidate (counted as diagnostics);
  * candidate mean = mean of its priced finished
    outcomes; the prior candidate is the baseline;
  * validity floor: the prior candidate needs >= 20
    finished worlds, else the state is "thin"
    (Decide's thin_prior fallback) and carries no
    statistic;
  * best = argmax mean over the selected set; if
    best == prior pick there is no contrast and the
    state carries mean_diff = null;
  * paired diffs over the worlds finished in BOTH
    best and prior; >= 20 required, else
    "insufficient"; mean_diff / se_diff with se the
    sample sd / sqrt(n); z = mean_diff / se_diff
    (se == 0: z = +inf when mean_diff > 0, else 0 --
    the live rule meanD > margin * seD fires for any
    margin in the first case);
  * would_fire(m) for m in the settings' margins:
    best != prior and z > m. One eval serves all
    margins because z is margin-independent.

Per state the analyzer also records: the prior band
of the top prior (settings report.prior_bands), the
search's pick vs the policy's (prior) pick, finished
counts and error tallies per candidate, and the eval
wall (from the driver's EVAL_STATS file).

Outputs: --states-out (one JSON row per state) and
--json-out (the summary: populations and would-fire
counts by class, prior band and margin; tail counts
z > settings report.tail_z; per-game rates against
the capture-games count from the jobs report).

Usage: probe_eval_analyze.py --jobs eval_jobs.jsonl
  --rows evals.jsonl [--stats eval_stats.jsonl]
  --jobs-report eval_jobs_report.json
  --settings settings_probe.json
  --states-out eval_states.jsonl --json-out eval_summary.json
"""
import argparse
import importlib.util
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prior_band(top, bands):
    for lo, hi in bands:
        if lo <= top < hi:
            return [lo, hi]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--rows", nargs="+", required=True)
    ap.add_argument("--stats")
    ap.add_argument("--jobs-report", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--states-out", required=True)
    ap.add_argument("--json-out", required=True)
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    settings = json.load(open(a.settings))
    et = settings["eval"]["tuple"]
    hval = float(et["horizon_value"])
    margins = [float(m) for m in settings["report"]["margins"]]
    tail_z = float(settings["report"]["tail_z"])
    bands = [tuple(b) for b in settings["report"]["prior_bands"]]
    jrep = json.load(open(a.jobs_report))
    n_games = int(jrep["games"])

    jobs = {}
    for l in open(a.jobs):
        if l.strip():
            j = json.loads(l)
            jobs[str(j["snap"])] = j

    walls = {}
    if a.stats and os.path.exists(a.stats):
        for l in open(a.stats):
            if l.strip():
                r = json.loads(l)
                walls[str(r["snap"])] = int(r.get("wall_ms") or 0)

    # worlds[(snap, cand)][world] = (kind, result)
    worlds = defaultdict(dict)
    n_rows = 0
    for path in a.rows:
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            n_rows += 1
            snap = str(r.get("snap"))
            if snap not in jobs:
                continue
            kind, err = s0.classify(r.get("result"))
            key = (snap, int(r["cand"]))
            if int(r["world"]) not in worlds[key]:
                worlds[key][int(r["world"])] = (kind, r.get("result"))

    states = []
    for snap in sorted(jobs):
        j = jobs[snap]
        sel = [int(x) for x in j["selected"]]
        pp = int(j["prior_pick"])
        priced = {}   # cand -> {world: priced outcome} finished only
        diag = {}
        for ci in sel:
            vals = {}
            errs = Counter()
            for w, (kind, res) in worlds.get((snap, ci), {}).items():
                if kind == "finished":
                    oc = float(res["outcome"])
                    wn = res.get("winner")
                    if wn is not None and int(wn) == 0:
                        oc = hval
                    vals[w] = oc
                else:
                    errs[kind] += 1
            priced[ci] = vals
            diag[ci] = {"finished": len(vals),
                        "unfinished": errs.get("unfinished", 0),
                        "refusal": errs.get("refusal", 0)}
        rec = {"snap": snap, "game": str(j["game"]),
               "player": int(j["player"]),
               "branch": str(j["branch"]),
               "turn": int(j.get("turn") or 0),
               "uncontested": int(j.get("uncontested") or 0),
               "top_prior": float(j["top_prior"]),
               "prior_band": prior_band(float(j["top_prior"]), bands),
               "ncand": len(j["cands"]), "selected": sel,
               "prior_pick": pp, "search_pick": pp,
               "mean_diff": None, "se_diff": None, "z": None,
               "would_fire": {str(m): False for m in margins},
               "status": "ok", "n_worlds_paired": 0,
               "cand_diag": {str(k): v for k, v in diag.items()},
               "wall_ms": walls.get(snap)}
        if len(priced.get(pp, {})) < 20:
            rec["status"] = "thin_prior"
            states.append(rec)
            continue
        means = {ci: (sum(v.values()) / len(v) if v else None)
                 for ci, v in priced.items()}
        best = pp
        for ci in sel:
            if means.get(ci) is not None and means[ci] > means[best]:
                best = ci
        rec["search_pick"] = best
        if best == pp:
            rec["status"] = "no_contrast"
            states.append(rec)
            continue
        shared = sorted(set(priced[best]) & set(priced[pp]))
        rec["n_worlds_paired"] = len(shared)
        if len(shared) < 20:
            rec["status"] = "insufficient"
            states.append(rec)
            continue
        ds = [priced[best][w] - priced[pp][w] for w in shared]
        md = sum(ds) / len(ds)
        var = sum((x - md) ** 2 for x in ds) / (len(ds) - 1)
        sd = math.sqrt(var) / math.sqrt(len(ds))
        rec["mean_diff"] = md
        rec["se_diff"] = sd
        if sd == 0:
            zz = math.inf if md > 0 else 0.0
        else:
            zz = md / sd
        rec["z"] = zz
        for m in margins:
            rec["would_fire"][str(m)] = bool(zz > m)
        states.append(rec)

    with open(a.states_out, "w") as f:
        for rec in states:
            f.write(json.dumps(rec) + "\n")

    def summarize(pop):
        s = {"states": len(pop),
             "with_statistic": sum(1 for r in pop if r["z"] is not None),
             "thin_prior": sum(1 for r in pop
                               if r["status"] == "thin_prior"),
             "insufficient": sum(1 for r in pop
                                 if r["status"] == "insufficient"),
             "no_contrast": sum(1 for r in pop
                                if r["status"] == "no_contrast"),
             "tail": sum(1 for r in pop
                         if r["z"] is not None and r["z"] > tail_z),
             "would_fire": {}}
        for m in margins:
            s["would_fire"][str(m)] = sum(
                1 for r in pop if r["would_fire"][str(m)])
        return s

    unc = [r for r in states if r["uncontested"] == 1]
    con = [r for r in states if r["uncontested"] == 0]
    by_band = {}
    for b in bands:
        pop = [r for r in states
               if r["prior_band"] == [b[0], b[1]]]
        if pop:
            by_band["%s-%s" % (b[0], b[1])] = summarize(pop)
    band125 = [r for r in con if r["z"] is not None
               and float(settings["label"]["band_lo"]) < r["z"]
               <= float(settings["label"]["band_hi"])]
    summary = {
        "games": n_games, "world_rows": n_rows,
        "all": summarize(states),
        "uncontested": summarize(unc),
        "contested": summarize(con),
        "by_prior_band": by_band,
        "contested_band_125_150": {
            "states": len(band125),
            "per_game": len(band125) / n_games if n_games else None},
        "per_game": {
            "uncontested_states": len(unc) / n_games if n_games else None,
            "contested_states": len(con) / n_games if n_games else None,
            "uncontested_would_fire": {
                str(m): summarize(unc)["would_fire"][str(m)] / n_games
                if n_games else None for m in margins},
            "contested_would_fire": {
                str(m): summarize(con)["would_fire"][str(m)] / n_games
                if n_games else None for m in margins},
        },
        "eval_wall_ms_total": sum(w for w in walls.values()),
    }
    with open(a.json_out, "w") as f:
        json.dump(summary, f, indent=1)
    print("probe eval: %d states over %d games "
          "(uncontested %d, contested %d); would-fire/game "
          "uncontested %s, contested %s; tail (z>%.1f): "
          "uncontested %d, contested %d"
          % (len(states), n_games, len(unc), len(con),
             summary["per_game"]["uncontested_would_fire"],
             summary["per_game"]["contested_would_fire"],
             tail_z, summary["uncontested"]["tail"],
             summary["contested"]["tail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
