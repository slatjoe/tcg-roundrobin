#!/usr/bin/env python3
"""Round-10 Step 0 probe: the L3 label read.

Construction mirrors stage3_attr_analyze.run_read
(primary, draw = 0) exactly -- worlds paired by world
index across each job's two candidates, refusal
worlds skipped, only worlds finished in BOTH
candidates counted, score = 1.0 if outcome > 0 else
0.0, job diff = mean of the per-world differences --
with three probe-specific differences, all in what
is grouped and reported, none in the read itself:

  * jobs are grouped by probe_band ("uncontested" /
    "contested_band") and, inside "uncontested", by
    the z > tail_z tail subset; the third class,
    "uncontested_diag" (the (1.0, 1.5] superset,
    fix pass), is read for counts and edge only --
    it is EXCLUDED from per-game gain and from the
    decision rule;
  * per-game gain is computed Claude's sec.5 form:
    per capture game, the summed diffs of that game's
    jobs of the class (capture games with no jobs of
    the class contribute 0), averaged over ALL
    capture games, with a game-clustered CI and a
    one-sided 95% lower bound -- the product form
    (edge x rate) is printed as a cross-check only;
  * SAMPLING WEIGHTS (fix pass, claude-reply-402c92f
    sec.2.1, BLOCKING): uncontested states were
    captured by systematic sampling, every
    capture.uncontested_every-th eligible decision,
    so each uncontested job's diff is weighted by
    that factor (Horvitz-Thompson) INSIDE the
    per-game sum, and the bootstrap runs over the
    weighted per-game totals. Contested-band jobs
    are unsampled and keep weight 1. The weight is
    printed on the CLASS line and recorded in the
    JSON gain object;
  * no verdict: the reads feed probe_report.py's
    registered decision rule.

Guards (round-9 forms): the label-tuple audit
projects every row's stamp on the label tuple's keys
(the stage2-analyzer-fix form); the world-count
guard demands exactly --expect-rows rows per
(snap, candidate); the refusal taxonomy and
jobs_no_shared_worlds are reported as in Stage 3.

Usage: probe_label_analyze.py --jobs jobs_all.jsonl
  --labels labels_all.jsonl --capture-games
  capture_games.json (the eval jobs report, whose
  games_list is the capture population)
  --settings settings_probe.json
  [--expect-rows 50] [--json-out label_read.json]
"""
import argparse
import importlib.util
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--capture-games", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--expect-rows", type=int, default=50)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")
    settings = json.load(open(a.settings))
    LT = settings["label"]["tuple"]
    tail_z = float(settings["report"]["tail_z"])
    unc_every = int(settings["capture"]["uncontested_every"])
    cap_games = [str(g) for g in
                 json.load(open(a.capture_games))["games_list"]]
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    job_by_snap = {str(j["snap"]): j for j in jobs}
    rows = []
    for path in a.labels:
        for l in open(path):
            if l.strip():
                rows.append(json.loads(l))

    bad = 0
    for r in rows:
        s = r.get("setting")
        if not isinstance(s, dict) or {
                k: s.get(k) for k in LT} != LT:
            bad += 1
    if bad:
        print("ABORT: %d label rows carry a setting stamp "
              "!= the registered label tuple" % bad)
        return 2

    pair_counts = defaultdict(int)
    for r in rows:
        if str(r.get("snap")) in job_by_snap:
            pair_counts[(str(r["snap"]), int(r["cand"]))] += 1
    for snap, j in sorted(job_by_snap.items()):
        for cand in sorted({int(j["teacher_pick"]),
                            int(j["prior_pick"])}):
            n = pair_counts.get((snap, cand), 0)
            if n != a.expect_rows:
                print("ABORT: world-count guard: job %s "
                      "candidate %d has %d rows, expected "
                      "exactly %d" % (snap, cand, n,
                                      a.expect_rows))
                return 2

    worlds = defaultdict(dict)
    fallbacks = 0
    fin = unf = ref = 0
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
            fallbacks += int(r["result"].get("fallbacks") or 0)
        if int(r["world"]) not in worlds[(snap, cand)]:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, r.get("result"))

    def score(res):
        return 1.0 if float(res["outcome"]) > 0 else 0.0

    diff_by_snap = {}
    for snap, j in job_by_snap.items():
        tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
        wt = worlds.get((snap, tp), {})
        wp = worlds.get((snap, pp), {})
        diffs = []
        for w in sorted(set(wt) & set(wp)):
            kt, rt = wt[w]
            kp, rp = wp[w]
            if kt == "refusal" or kp == "refusal":
                continue
            if kt != "finished" or kp != "finished":
                continue
            diffs.append(score(rt) - score(rp))
        if diffs:
            diff_by_snap[snap] = {
                "diff": sum(diffs) / len(diffs),
                "game": str(j["game"]),
                "probe_band": str(j["probe_band"]),
                "prior_band": j.get("prior_band"),
                "z": float(j["z"]),
                "n_worlds": len(diffs)}
    jobs_no_shared = len(jobs) - len(diff_by_snap)

    def read(recs):
        if not recs:
            return {"jobs": 0, "edge": None, "ci": None}
        m = sum(r["diff"] for r in recs) / len(recs)
        lo, hi = stock.cluster_bootstrap(
            [{"game": r["game"], "diff": r["diff"]} for r in recs])
        return {"jobs": len(recs), "edge": m, "ci": [lo, hi]}

    def per_game_gain(recs, weight=1.0):
        per = defaultdict(float)
        for r in recs:
            per[r["game"]] += r["diff"] * weight
        grecs = [{"game": g, "diff": per.get(g, 0.0)}
                 for g in cap_games]
        if not grecs:
            return {"gain": None, "ci": None,
                    "lb95_1sided": None, "weight": weight}
        m = sum(r["diff"] for r in grecs) / len(grecs)
        lo, hi = stock.cluster_bootstrap(grecs)
        # one-sided 95% lower bound from the same bootstrap
        # distribution would need the replicates; the
        # registered form uses the two-sided CI's lower
        # bound as the conservative stand-in and says so.
        return {"gain": m, "ci": [lo, hi], "lb95_1sided": lo,
                "games": len(grecs), "weight": weight}

    recs_all = list(diff_by_snap.values())
    out = {"jobs": len(jobs),
           "jobs_no_shared_worlds": jobs_no_shared,
           "label_rows": len(rows),
           "finished": fin, "unfinished": unf, "refusals": ref,
           "fallbacks": fallbacks,
           "by_class": {}, "per_game_gain": {}}
    lines = ["=== ROUND-10 STEP 0 PROBE -- L3 LABEL READ "
             "(primary: horizon 62, draw = 0) ==="]
    for cls in ("uncontested", "contested_band"):
        recs = [r for r in recs_all if r["probe_band"] == cls]
        rd = read(recs)
        # sec.2.1: uncontested jobs carry the sampling
        # weight; contested-band jobs are unsampled.
        w = float(unc_every) if cls == "uncontested" else 1.0
        gain = per_game_gain(recs, w)
        out["by_class"][cls] = rd
        out["per_game_gain"][cls] = gain
        lines.append(
            "CLASS %s: jobs %d; edge %s CI [%s, %s]; "
            "per-game gain %s CI [%s, %s] over %d capture "
            "games; sampling weight %s"
            % (cls, rd["jobs"], pct(rd["edge"]),
               pct(rd["ci"][0]) if rd["ci"] else "n/a",
               pct(rd["ci"][1]) if rd["ci"] else "n/a",
               pct(gain["gain"]),
               pct(gain["ci"][0]) if gain["ci"] else "n/a",
               pct(gain["ci"][1]) if gain["ci"] else "n/a",
               gain.get("games") or 0, "%g" % w))
        if cls == "uncontested":
            tail = [r for r in recs if r["z"] > tail_z]
            trd = read(tail)
            out["by_class"]["uncontested_tail"] = trd
            lines.append(
                "CLASS uncontested TAIL (z > %.1f): jobs %d; "
                "edge %s CI [%s, %s]"
                % (tail_z, trd["jobs"], pct(trd["edge"]),
                   pct(trd["ci"][0]) if trd["ci"] else "n/a",
                   pct(trd["ci"][1]) if trd["ci"] else "n/a"))
            pb = defaultdict(list)
            for r in recs:
                pb[str(r["prior_band"])].append(r)
            out["by_class"]["uncontested_by_prior_band"] = {
                k: read(v) for k, v in sorted(pb.items())}
    # the diagnostic superset class: counts and edge
    # only -- NO per-game gain entry, so nothing
    # downstream can fold it into the threshold gain
    # or the decision rule (fix pass, sec.3/F2).
    diag = [r for r in recs_all
            if r["probe_band"] == "uncontested_diag"]
    drd = read(diag)
    out["by_class"]["uncontested_diag"] = drd
    lines.append(
        "CLASS uncontested_diag (DIAGNOSTIC ONLY -- the "
        "(1.0, 1.5] uncontested superset; excluded from "
        "the threshold gain and the decision rule): "
        "jobs %d; edge %s CI [%s, %s]"
        % (drd["jobs"], pct(drd["edge"]),
           pct(drd["ci"][0]) if drd["ci"] else "n/a",
           pct(drd["ci"][1]) if drd["ci"] else "n/a"))
    lines.append("jobs_no_shared_worlds %d of %d; label rows "
                 "%d (finished %d, unfinished %d, refusals %d); "
                 "fallbacks %d"
                 % (jobs_no_shared, len(jobs), len(rows), fin,
                    unf, ref, fallbacks))
    txt = "\n".join(lines) + "\n"
    print(txt)
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
