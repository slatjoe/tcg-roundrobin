#!/usr/bin/env python3
"""Round-10 Step 0 fixtures: writer/reader round trips
for the probe's Python chain, fed the writers' real
output shapes (the standing rule), with hand-computed
expectations:

  1. build_probe_eval_jobs over synthetic capture
     index streams (contested + uncontested rows in
     search_s3's real shapes), incl. the two poison
     rows (contested row with top prior >= 0.97;
     uncontested row below 0.97) which must abort;
  2. probe_eval_analyze over synthetic s1_eval_main
     world rows, incl.:
       A contested, constant paired diffs -> z = +inf,
         fires at all margins;
       B uncontested, diffs with an independently
         computed z in (1.25, 1.5];
       C prior candidate with 19 finished worlds ->
         thin_prior, no statistic;
       D best == prior -> no_contrast;
       E horizon pricing: drawn worlds (winner 0)
         priced -1, so equal-priced candidates give
         no contrast where raw outcomes would fire;
  3. build_probe_jobs over the analyzer's real state
     rows: class assignment (uncontested@1.5,
     contested (1.25,1.5]), the alternate-margin
     counts, and the shard-cap abort (two jobs, same
     game, cap 1);
  4. probe_label_analyze over synthetic s2_label_main
     rows for the built jobs: per-world scoring incl.
     a refusal world skipped in both candidates, the
     exactly-50 world-count guard, per-game gain over
     a capture population incl. a zero-job game.

Every check prints PASS/FAIL; exit 1 on any FAIL.
"""
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", "code"))
FAILS = []


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, extra))
    if not cond:
        FAILS.append(name)


def run(args, expect_rc=0):
    p = subprocess.run([sys.executable] + args,
                       capture_output=True, text=True)
    if p.returncode != expect_rc:
        print(p.stdout[-2000:])
        print(p.stderr[-2000:])
    return p


def jl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def fin(oc, winner=1):
    return {"outcome": oc, "winner": winner, "finished": 1,
            "horizon": 0, "errors": {}, "fallbacks": 0}


def main():
    tmp = tempfile.mkdtemp(prefix="fx_probe_")
    settings = os.path.join(CODE, "settings_probe.json")
    et = json.load(open(settings))["eval"]["tuple"]

    # ---- 1. capture index -> eval jobs ------------------------------
    def caprow(snap, game, unc, top):
        priors = [top, 0.02, 0.01] if unc else [0.6, 0.3, 0.1]
        r = {"snap": snap, "game": game, "hcount": 1,
             "branch": "combat", "player": 1, "turn": 5,
             "cands": [{"a": 1}, {"a": 2}, {"a": 3}],
             "state": None, "priors": priors,
             "prior_pick": 0, "selected": [0, 1, 2]}
        if unc:
            r["uncontested"] = 1
            r["top_prior"] = top
        return r

    idx1 = os.path.join(tmp, "idx1.jsonl")
    jl(idx1, [caprow("gA_t1", "gA", 0, 0.6),
              caprow("gA_t2", "gA", 1, 0.99),
              caprow("gB_t1", "gB", 1, 0.975)])
    out_jobs = os.path.join(tmp, "eval_jobs.jsonl")
    rep = os.path.join(tmp, "eval_jobs_report.json")
    p = run([os.path.join(CODE, "build_probe_eval_jobs.py"),
             "--stream", "snapsdir=" + idx1,
             "--settings", settings, "--out", out_jobs,
             "--report", rep])
    check("eval-jobs build rc", p.returncode == 0)
    jobs = [json.loads(l) for l in open(out_jobs)]
    check("eval-jobs count/classes",
          len(jobs) == 3
          and sum(j["uncontested"] for j in jobs) == 2
          and jobs[0]["snap_dir"] == "snapsdir/gA_t1"
          and jobs[0]["setting"] == et)
    rj = json.load(open(rep))
    check("eval-jobs report games",
          rj["games"] == 2 and rj["games_list"] == ["gA", "gB"])
    # poison rows
    for name, bad in (
            ("contested>=0.97",
             caprow("gX_t1", "gX", 0, 0.6) | {"priors": [0.99, 0.01]}),
            ("uncontested<0.97",
             caprow("gX_t1", "gX", 1, 0.95))):
        badf = os.path.join(tmp, "bad.jsonl")
        jl(badf, [bad])
        p = run([os.path.join(CODE, "build_probe_eval_jobs.py"),
                 "--stream", "s=" + badf, "--settings", settings,
                 "--out", out_jobs, "--report", rep], expect_rc=2)
        check("eval-jobs poison abort: " + name, p.returncode == 2)

    # ---- 2. eval world rows -> per-state statistics -----------------
    rows = []

    def wrow(snap, cand, w, res):
        return {"snap": snap, "cand": cand, "world": w,
                "result": res, "prior_pick": 0, "game": snap[:2],
                "setting": et}

    # A: contested, cand1 beats prior by +2 every world
    for w in range(25):
        rows.append(wrow("gA_t1", 0, w, fin(-1)))
        rows.append(wrow("gA_t1", 1, w, fin(1)))
        rows.append(wrow("gA_t1", 2, w, fin(-1)))
    # B: uncontested gA_t2, paired outcome diffs
    # 9 x +2, 4 x +1, 12 x -1 built from valid outcome
    # pairs (prior -1/cand +1; prior -1/cand 0;
    # prior +1/cand 0): mean 0.40, z = sqrt(2) = 1.414,
    # in the (1.25, 1.5] band.
    diffsB = [2.0] * 9 + [1.0] * 4 + [-1.0] * 12
    priorB = [-1] * 13 + [1] * 12
    candB = [1] * 9 + [0] * 16
    for w in range(25):
        rows.append(wrow("gA_t2", 0, w, fin(priorB[w])))
        rows.append(wrow("gA_t2", 1, w, fin(candB[w])))
        rows.append(wrow("gA_t2", 2, w, fin(-1)))
    # C: uncontested gB_t1, prior only 19 finished worlds
    for w in range(25):
        rows.append(wrow("gB_t1", 0, w,
                         fin(-1) if w < 19 else
                         {"outcome": 0, "winner": -1, "finished": 0,
                          "horizon": 0, "errors": {"E": 1}}))
        rows.append(wrow("gB_t1", 1, w, fin(1)))
        rows.append(wrow("gB_t1", 2, w, fin(-1)))
    # D+E need jobs: extend the eval-jobs file with two
    # synthetic states fed straight to the analyzer
    extra_jobs = [
        {"snap_dir": "snapsdir/gC_t1", "snap": "gC_t1",
         "game": "gC", "player": 2, "branch": "main",
         "turn": 3, "cands": [{}, {}, {}], "selected": [0, 1, 2],
         "prior_pick": 0, "setting": et, "priors": [0.5, 0.3, 0.2],
         "top_prior": 0.5, "uncontested": 0},
        {"snap_dir": "snapsdir/gD_t1", "snap": "gD_t1",
         "game": "gD", "player": 1, "branch": "main",
         "turn": 3, "cands": [{}, {}, {}], "selected": [0, 1, 2],
         "prior_pick": 0, "setting": et, "priors": [0.5, 0.3, 0.2],
         "top_prior": 0.5, "uncontested": 0},
    ]
    with open(out_jobs, "a") as f:
        for j in extra_jobs:
            f.write(json.dumps(j) + "\n")
    # D: cand means tie at the top (best == prior by strict >)
    for w in range(25):
        rows.append(wrow("gC_t1", 0, w, fin(0)))
        rows.append(wrow("gC_t1", 1, w, fin(0)))
        rows.append(wrow("gC_t1", 2, w, fin(-1)))
    # E: cand1 worlds all drawn (winner 0, raw outcome +1)
    # -> priced -1, equal to prior's -1 -> no fire; raw
    # outcomes would give mean_diff +2.
    for w in range(25):
        rows.append(wrow("gD_t1", 0, w, fin(-1)))
        rows.append(wrow("gD_t1", 1, w, fin(1, winner=0)))
        rows.append(wrow("gD_t1", 2, w, fin(-1)))
    rowsf = os.path.join(tmp, "evals.jsonl")
    jl(rowsf, rows)
    # jobs report must now cover 4 games for per-game rates
    json.dump({"games": 4, "games_list": ["gA", "gB", "gC", "gD"],
               "states": 5, "classes": {"contested": 3,
                                        "uncontested": 2}},
              open(rep, "w"))
    statesf = os.path.join(tmp, "eval_states.jsonl")
    sumf = os.path.join(tmp, "eval_summary.json")
    p = run([os.path.join(CODE, "probe_eval_analyze.py"),
             "--jobs", out_jobs, "--rows", rowsf,
             "--jobs-report", rep, "--settings", settings,
             "--states-out", statesf, "--json-out", sumf])
    check("eval-analyze rc", p.returncode == 0)
    st = {json.loads(l)["snap"]: json.loads(l)
          for l in open(statesf)}
    a = st["gA_t1"]
    check("A: z inf, fires all margins, pick 1",
          a["z"] == math.inf and a["search_pick"] == 1
          and all(a["would_fire"].values())
          and a["mean_diff"] == 2.0)
    b = st["gA_t2"]
    md = statistics.mean(diffsB)
    se = statistics.stdev(diffsB) / math.sqrt(25)
    zexp = md / se
    check("B: z in (1.25, 1.5], matches independent z",
          1.25 < zexp <= 1.5 and abs(b["z"] - zexp) < 1e-9
          and b["would_fire"]["1.25"]
          and not b["would_fire"]["1.5"],
          "z=%.4f expected %.4f" % (b["z"] or -1, zexp))
    c = st["gB_t1"]
    check("C: thin_prior, no statistic",
          c["status"] == "thin_prior" and c["z"] is None)
    d = st["gC_t1"]
    check("D: no_contrast on tie",
          d["status"] == "no_contrast" and d["z"] is None)
    e = st["gD_t1"]
    check("E: drawn worlds priced -1 -> no_contrast",
          e["status"] == "no_contrast" and e["z"] is None)
    sm = json.load(open(sumf))
    check("summary: uncontested would-fire@1.25 = 1, tail A = 1",
          sm["uncontested"]["would_fire"]["1.25"] == 1
          and sm["contested"]["tail"] == 1
          and sm["contested_band_125_150"]["states"] == 0)

    # ---- 3. states -> label jobs -------------------------------------
    jobsf = os.path.join(tmp, "jobs_all.jsonl")
    jrep = os.path.join(tmp, "jobs_report.json")
    p = run([os.path.join(CODE, "build_probe_jobs.py"),
             "--states", statesf, "--eval-jobs", out_jobs,
             "--settings", settings, "--out", jobsf,
             "--shard-prefix", os.path.join(tmp, "jobs_shard"),
             "--report", jrep])
    check("label-jobs build rc", p.returncode == 0)
    lj = [json.loads(l) for l in open(jobsf)]
    # only B qualifies: A is contested with z=inf (outside
    # the band); B is uncontested but z <= 1.5 -> NOT at
    # margin 1.5! Expect ZERO jobs and alt count 1 @1.25.
    rj = json.load(open(jrep))
    check("label-jobs: 0 jobs at margin 1.5; alt@1.25 = 1",
          len(lj) == 0
          and rj["alt_uncontested_counts"].get(
              "uncontested@1.25") == 1)
    # flip the class definition to 1.25 in a settings copy
    st2 = json.load(open(settings))
    st2["label"]["uncontested_margin"] = 1.25
    st2f = os.path.join(tmp, "settings_m125.json")
    json.dump(st2, open(st2f, "w"))
    p = run([os.path.join(CODE, "build_probe_jobs.py"),
             "--states", statesf, "--eval-jobs", out_jobs,
             "--settings", st2f, "--out", jobsf,
             "--shard-prefix", os.path.join(tmp, "jobs_shard"),
             "--report", jrep])
    lj = [json.loads(l) for l in open(jobsf)]
    check("label-jobs @1.25: B is the one uncontested job",
          p.returncode == 0 and len(lj) == 1
          and lj[0]["snap"] == "gA_t2"
          and lj[0]["probe_band"] == "uncontested"
          and lj[0]["selected"] == [0, 1]
          and lj[0]["teacher_pick"] == 1)
    # shard-cap abort: cap 0 with one job anywhere
    st2["label"]["shard_cap_jobs"] = 0
    json.dump(st2, open(st2f, "w"))
    p = run([os.path.join(CODE, "build_probe_jobs.py"),
             "--states", statesf, "--eval-jobs", out_jobs,
             "--settings", st2f, "--out", jobsf,
             "--shard-prefix", os.path.join(tmp, "jobs_shard"),
             "--report", jrep], expect_rc=2)
    check("label-jobs shard-cap abort", p.returncode == 2)

    # ---- 4. label rows -> label read ---------------------------------
    st3 = json.load(open(settings))
    st3["label"]["uncontested_margin"] = 1.25
    json.dump(st3, open(st2f, "w"))
    run([os.path.join(CODE, "build_probe_jobs.py"),
         "--states", statesf, "--eval-jobs", out_jobs,
         "--settings", st2f, "--out", jobsf,
         "--shard-prefix", os.path.join(tmp, "jobs_shard"),
         "--report", jrep])
    LT = st3["label"]["tuple"]
    lab = []
    for w in range(50):
        # teacher cand 1: +1 every world; world 7 is a
        # refusal in BOTH candidates -> skipped
        lab.append({"snap": "gA_t2", "cand": 1, "world": w,
                    "pair": "va", "setting": LT,
                    "result": ({"outcome": 0, "winner": -1,
                                "finished": 0, "horizon": 0,
                                "errors": {"SimSearch_Refused": 1}}
                               if w == 7 else fin(1))})
        lab.append({"snap": "gA_t2", "cand": 0, "world": w,
                    "pair": "va", "setting": LT,
                    "result": ({"outcome": 0, "winner": -1,
                                "finished": 0, "horizon": 0,
                                "errors": {"SimSearch_Refused": 1}}
                               if w == 7 else fin(-1))})
    labf = os.path.join(tmp, "labels.jsonl")
    jl(labf, lab)
    capgames = os.path.join(tmp, "capgames.json")
    json.dump({"games_list": ["gA", "gB", "gC", "gD"]},
              open(capgames, "w"))
    lrf = os.path.join(tmp, "label_read.json")
    p = run([os.path.join(CODE, "probe_label_analyze.py"),
             "--jobs", jobsf, "--labels", labf,
             "--capture-games", capgames,
             "--settings", settings, "--json-out", lrf])
    check("label-analyze rc", p.returncode == 0)
    lr = json.load(open(lrf))
    rd = lr["by_class"]["uncontested"]
    gain = lr["per_game_gain"]["uncontested"]
    check("label read: edge 1.0, per-game gain 0.25 over "
          "4 games (one zero-job game counted)",
          rd["jobs"] == 1 and abs(rd["edge"] - 1.0) < 1e-12
          and abs(gain["gain"] - 0.25) < 1e-12
          and lr["jobs_no_shared_worlds"] == 0,
          "edge=%s gain=%s" % (rd["edge"], gain["gain"]))
    # world-count guard: drop one row -> abort
    jl(labf, lab[:-1])
    p = run([os.path.join(CODE, "probe_label_analyze.py"),
             "--jobs", jobsf, "--labels", labf,
             "--capture-games", capgames,
             "--settings", settings], expect_rc=2)
    check("label world-count guard abort", p.returncode == 2)

    print("fx_probe_python: %s"
          % ("ALL PASS" if not FAILS else
             "FAILURES: %s" % FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
