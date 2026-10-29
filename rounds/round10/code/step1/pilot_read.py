#!/usr/bin/env python3
"""Round-10 Step 1 pilot READ (registered in
step1-pilot-package.md sec.4, terms from
claude-reply-243b9d8 sec.3.3-3.4).

Inputs: the pilot's jobs (all captured overturns, both
classes, from build_pilot_jobs.py), the L3 label rows
(W=50, CRN, production server), the games driver rows
(the 100-game population), the games report, settings.

SCORING (cap-aligned, sec.14): a label world scores
1.0 iff outcome > 0 AND it ended by turn 61, else 0.
Per job, the paired diff is the mean over worlds
finished in BOTH candidates (refusal worlds skipped)
of score[teacher_pick] - score[prior_pick] -- the
probe_label_analyze.job_diffs construction at
cap_aligned=True, re-implemented here so this file
carries no cross-package import; the fixture
(fx_pilot_python.py) hand-checks it.

READS, all in the DIRECT form (no sampling weights --
pilot capture is complete):
  * per-game totals: for each class C in {contested,
    newly_contested} and for the total, per-game total
    = summed diffs of that game's class-C jobs over
    ALL 100 games (zero-job games contribute 0).
  * gain(C) = mean of per-game totals; CI by cluster
    bootstrap over games (B=10000, seed 20261020,
    analyze_l3.cluster_bootstrap on per-game totals).
    lb = CI lower (the one-sided 95% lower bound, the
    registered conservative stand-in); ub = CI upper.
  * fires/game by class (from the jobs over the 100
    games); edge by class (mean job diff) and by
    z-band ((1.5,2], (2,2.5], (2.5,3.5], >3.5; the
    z=999 sentinel bands > 3.5).
  * wall per game (mean, p95 nearest-rank, max) and
    timeout count, from the games report.
  * INFLUENCE: per class and total, leave-one-game-out
    gains (the full gain with each game excluded,
    averaged over the remaining 99), the LOGO range,
    and the largest single-game share
    (game total / grand total of job diffs, signed
    form: share of the summed diffs).
  * STOP evaluation: STOP iff ub(total) < 0.0849
    (= Stage 3 gain 0.0649 + 0.020).
  * STEP 2 SIZING print: Delta_plan = lb(total)
    - 0.0649; SE_pilot = sd(per-game totals, ddof=1)
    / sqrt(100); SE_new(n) = SE_pilot * sqrt(100/n);
    the two-sample bar needs
    Delta_plan / sqrt(SE_new(n)^2 + 0.0090^2)
    = 1.645 + 0.8416 = 2.4866 at 80% power, so with
    R = (Delta_plan/2.4866)^2 - 0.0090^2: if
    Delta_plan <= 0 or R <= 0, n = inf (no finite
    size reaches the bar); else
    n = ceil(100 * SE_pilot^2 / R). n > 400 prints
    the JOE-COST-DECISION flag. The pilot's games
    are never pooled into Step 2 (registration).

Usage:
  pilot_read.py --jobs jobs_all.jsonl
      --labels labels_all.jsonl
      --games-rows games_s1a.jsonl [... driver rows]
      --games-report games_report.json
      --settings settings_pilot.json
      --json-out pilot_read.json
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CAP_LAST_DECISIVE_TURN = 61
CLASSES = ("contested", "newly_contested")


def load_mod(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def world_score(res):
    if float(res["outcome"]) > 0 and \
            int(res.get("turns") or 0) <= CAP_LAST_DECISIVE_TURN:
        return 1.0
    return 0.0


def job_diffs(jobs, rows, s0):
    """(diff_by_snap, counts) -- cap-aligned paired
    diffs, the probe construction."""
    job_by_snap = {str(j["snap"]): j for j in jobs}
    worlds = defaultdict(dict)
    fin = unf = ref = fb = 0
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand not in (int(j["teacher_pick"]),
                        int(j["prior_pick"])):
            continue
        kind, _ = s0.classify(r.get("result"))
        if kind == "finished":
            fin += 1
        elif kind == "refusal":
            ref += 1
        else:
            unf += 1
        if isinstance(r.get("result"), dict):
            fb += int(r["result"].get("fallbacks") or 0)
        if int(r["world"]) not in worlds[(snap, cand)]:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, r.get("result"))
    diff_by_snap = {}
    for snap, j in job_by_snap.items():
        tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
        wt = worlds.get((snap, tp), {})
        wp = worlds.get((snap, pp), {})
        diffs = []
        for w in sorted(set(wt) & set(wp)):
            kt, rt = wt[w]
            kp, rp = wp[w]
            if kt != "finished" or kp != "finished":
                continue
            diffs.append(world_score(rt) - world_score(rp))
        if diffs:
            diff_by_snap[snap] = {
                "diff": sum(diffs) / len(diffs),
                "game": str(j["game"]),
                "class": str(j["class"]),
                "z": float(j["z"]),
                "z_nonfinite": bool(j.get("z_nonfinite")),
                "n_worlds": len(diffs)}
    counts = {"finished": fin, "unfinished": unf,
              "refusals": ref, "fallbacks": fb,
              "jobs_no_shared_worlds":
                  len(jobs) - len(diff_by_snap)}
    return diff_by_snap, counts


def per_game_totals(recs, games, cls=None):
    per = {g: 0.0 for g in games}
    for r in recs:
        if cls is not None and r["class"] != cls:
            continue
        per[r["game"]] = per.get(r["game"], 0.0) + r["diff"]
    return per


def gain_read(per, stock):
    """per: {game: total}. Returns the registered gain
    object (bootstrap CI over games)."""
    grecs = [{"game": g, "diff": per[g]} for g in sorted(per)]
    n = len(grecs)
    gain = sum(r["diff"] for r in grecs) / n if n else None
    lo, hi = stock.cluster_bootstrap(grecs)
    if n > 1:
        var = sum((r["diff"] - gain) ** 2
                  for r in grecs) / (n - 1)
        se = math.sqrt(var) / math.sqrt(n)
    else:
        se = None
    return {"gain": gain, "ci": [lo, hi], "lb": lo,
            "ub": hi, "se_clustered": se, "games": n}


def logo_read(per):
    """Leave-one-game-out over per-game totals: for each
    game, the gain with that game excluded (mean over
    the remaining games). Returns the range, the
    weakest (minimum) exclusion and its game, and the
    largest single-game share of the summed diffs."""
    games = sorted(per)
    total = sum(per[g] for g in games)
    n = len(games)
    excl = {}
    for g in games:
        excl[g] = (total - per[g]) / (n - 1) if n > 1 else None
    weakest = min(excl, key=lambda g: excl[g]) if excl else None
    shares = {g: (per[g] / total if total != 0 else 0.0)
              for g in games}
    largest = max(shares, key=lambda g: abs(shares[g])) \
        if shares else None
    return {"range": [min(excl.values()), max(excl.values())]
            if excl else None,
            "weakest_exclusion_game": weakest,
            "weakest_exclusion_gain": excl.get(weakest),
            "largest_share_game": largest,
            "largest_share": shares.get(largest)}


def sizing_read(gain_obj, settings_read):
    """The registered Step 2 sizing (see module doc)."""
    s3 = float(settings_read["stage3_gain"])
    s3se = float(settings_read["stage3_gain_se"])
    za = float(settings_read["sizing"]["z_one_sided"])
    zp = float(settings_read["sizing"]["z_power_80"])
    zsum = za + zp
    lb = gain_obj["lb"]
    se = gain_obj["se_clustered"]
    n_games = gain_obj["games"]
    delta = lb - s3
    out = {"delta_plan": delta, "se_pilot": se,
           "z_sum": zsum, "stage3_gain": s3,
           "stage3_gain_se": s3se}
    if delta <= 0 or se is None:
        out["n"] = None
        out["note"] = ("Delta_plan <= 0: no finite Step 2 "
                       "size reaches the bar at 80% power")
        return out
    R = (delta / zsum) ** 2 - s3se ** 2
    out["R"] = R
    if R <= 0:
        out["n"] = None
        out["note"] = ("R <= 0: Stage 3's own SE alone "
                       "exhausts the detectable margin; "
                       "no finite n reaches the bar")
        return out
    n = math.ceil(n_games * se * se / R)
    out["n"] = n
    out["flag_above_400"] = n > int(
        settings_read["sizing"]["flag_above_games"])
    return out


def z_band(z, znf, bands):
    for lo, hi in bands:
        if znf:
            return ">3.5"
        if z > lo and (hi is None or z <= hi):
            return ("(%.1f, %.1f]" % (lo, hi)) if hi \
                else (">%.1f" % lo)
    return "<=1.5"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--games-rows", nargs="+", required=True)
    ap.add_argument("--games-report", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--json-out", required=True)
    a = ap.parse_args()
    settings = json.load(open(a.settings))
    rd = settings["read"]
    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")

    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = [json.loads(l) for l in open(a.labels) if l.strip()]
    games = []
    for p in a.games_rows:
        for l in open(p):
            if l.strip():
                r = json.loads(l)
                if "invalid" not in r:
                    games.append(str(r["gamename"]))
    games = sorted(set(games))
    grep = json.load(open(a.games_report))

    diff_by_snap, counts = job_diffs(jobs, rows, s0)
    recs = list(diff_by_snap.values())
    out = {"games_population": len(games), "jobs": len(jobs),
           "jobs_scored": len(recs), "label_counts": counts,
           "classes": {}, "bands": {}, "total": {}}

    bands = [(float(x[0]), (float(x[1]) if x[1] is not None
                            else None))
             for x in rd["z_bands"]]
    band_recs = defaultdict(list)
    for r in recs:
        band_recs[z_band(r["z"], r["z_nonfinite"],
                         bands)].append(r)
    for b, brs in sorted(band_recs.items()):
        out["bands"][b] = {
            "jobs": len(brs),
            "edge": sum(r["diff"] for r in brs) / len(brs)}

    for cls in CLASSES + ("total",):
        sel = recs if cls == "total" else [
            r for r in recs if r["class"] == cls]
        per = per_game_totals(recs, games,
                              None if cls == "total" else cls)
        g = gain_read(per, stock)
        entry = {"jobs": len(sel),
                 "fires_per_game": len(sel) / len(games)
                 if games else None,
                 "edge": (sum(r["diff"] for r in sel)
                          / len(sel)) if sel else None,
                 "gain": g, "logo": logo_read(per)}
        if cls == "total":
            out["total"] = entry
        else:
            out["classes"][cls] = entry

    stop_ub = float(rd["stage3_gain"]) + 0.020
    ub = out["total"]["gain"]["ub"]
    out["stop"] = {"threshold": stop_ub, "total_ub": ub,
                   "STOP": ub < stop_ub}
    out["sizing"] = sizing_read(out["total"]["gain"], rd)
    out["wall_s"] = grep.get("wall_s")
    out["teacher_timeouts"] = grep.get("teacher_timeouts")

    with open(a.json_out, "w") as f:
        json.dump(out, f, indent=1, allow_nan=False)

    lines = []
    lines.append("=== ROUND-10 STEP 1 PILOT -- READ ===")
    lines.append("games %d; jobs %d (scored %d); label rows "
                 "finished %d / unfinished %d / refusals %d; "
                 "fallbacks %d; jobs_no_shared_worlds %d"
                 % (len(games), len(jobs), len(recs),
                    counts["finished"], counts["unfinished"],
                    counts["refusals"], counts["fallbacks"],
                    counts["jobs_no_shared_worlds"]))
    for cls in CLASSES:
        e = out["classes"][cls]
        g = e["gain"]
        lines.append(
            "class %s: fires/game %.4f (%d jobs); edge %s; "
            "per-game gain %.4f CI [%.4f, %.4f] (lb %.4f); "
            "LOGO range [%.4f, %.4f], largest share %.4f "
            "(game %s)"
            % (cls, e["fires_per_game"] or 0.0, e["jobs"],
               ("%.4f" % e["edge"]) if e["edge"] is not None
               else "n/a", g["gain"], g["ci"][0], g["ci"][1],
               g["lb"], e["logo"]["range"][0],
               e["logo"]["range"][1],
               e["logo"]["largest_share"],
               e["logo"]["largest_share_game"]))
    for b, br in sorted(out["bands"].items()):
        lines.append("z-band %s: %d jobs, edge %.4f"
                     % (b, br["jobs"], br["edge"]))
    g = out["total"]["gain"]
    w = out["wall_s"] or {}
    lines.append(
        "TOTAL: per-game gain %.4f CI [%.4f, %.4f]; "
        "LOGO range [%.4f, %.4f], largest share %.4f "
        "(game %s); wall mean %s p95 %s max %s; timeouts %s"
        % (g["gain"], g["ci"][0], g["ci"][1],
           out["total"]["logo"]["range"][0],
           out["total"]["logo"]["range"][1],
           out["total"]["logo"]["largest_share"],
           out["total"]["logo"]["largest_share_game"],
           w.get("mean"), w.get("p95"), w.get("max"),
           out["teacher_timeouts"]))
    lines.append(
        "STOP rule: STOP iff total upper bound < %.4f; "
        "total ub %.4f -> %s"
        % (stop_ub, ub,
           "STOP (no Step 2)" if out["stop"]["STOP"]
           else "DO NOT STOP"))
    sz = out["sizing"]
    if sz["n"] is None:
        lines.append("Step 2 sizing: Delta_plan %.4f; %s"
                     % (sz["delta_plan"], sz["note"]))
    else:
        lines.append(
            "Step 2 sizing: Delta_plan %.4f (pilot lb "
            "%.4f - 0.0649); SE_pilot %.4f; n = %d games "
            "at 80%% power%s"
            % (sz["delta_plan"], g["lb"], sz["se_pilot"],
               sz["n"],
               "; JOE-COST-DECISION: n > 400"
               if sz["flag_above_400"] else ""))
    txt = "\n".join(lines) + "\n"
    print(txt, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
