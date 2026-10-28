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
  5. (fix pass, review sec.2.1) the SAMPLING-WEIGHT
     round trip, planted in the capture hook's REAL
     index shape: index rows -> eval jobs -> eval
     states -> label jobs -> label rows -> the label
     read, run at EVERY = 2 and again at EVERY = 1.
     The uncontested per-game gain at EVERY = 2 must
     equal exactly 2x the EVERY = 1 gain with the CI
     scaled by the same factor, the contested-band
     gain must be identical in both runs, and the
     CLASS line must print the weight.
  6. (fix pass, review sec.3/F2) uncontested class
     boundaries in build_probe_jobs: z = 1.0 (no
     job), z in (1.0, 1.5] (the DIAGNOSTIC class,
     incl. z exactly 1.5), z > 1.5 (class (a)); the
     report's by_class and the realized counts under
     all three margins.
  7. (fix pass, review sec.2.2 + sec.3) probe_report
     on synthetic analyzer outputs with hand-computed
     expectations: the calibration line inside its
     band (no flag) and outside it (flag line printed
     ABOVE the recommendation, recommendation still
     emitted); the informational Step 2 power print
     against an independently computed Phi value; the
     Step 2 / fleet price lines for both levers.

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
    # the band); B is uncontested with z in (1.0, 1.5] ->
    # since the fix pass it is ONE DIAGNOSTIC-class job
    # (before the fix pass this check expected zero jobs;
    # the superset labeling is the registered change),
    # and the alt count @1.25 is 1.
    rj = json.load(open(jrep))
    check("label-jobs: B is one diagnostic job at margin "
          "1.5; alt@1.25 = 1",
          len(lj) == 1 and lj[0]["snap"] == "gA_t2"
          and lj[0]["probe_band"] == "uncontested_diag"
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
    check("label read: edge 1.0, per-game gain 0.5 over "
          "4 games (sampling weight 2 on the uncontested "
          "job since the fix pass; one zero-job game "
          "counted)",
          rd["jobs"] == 1 and abs(rd["edge"] - 1.0) < 1e-12
          and abs(gain["gain"] - 0.5) < 1e-12
          and gain["weight"] == 2.0
          and lr["jobs_no_shared_worlds"] == 0,
          "edge=%s gain=%s" % (rd["edge"], gain["gain"]))
    # world-count guard: drop one row -> abort
    jl(labf, lab[:-1])
    p = run([os.path.join(CODE, "probe_label_analyze.py"),
             "--jobs", jobsf, "--labels", labf,
             "--capture-games", capgames,
             "--settings", settings], expect_rc=2)
    check("label world-count guard abort", p.returncode == 2)

    # ---- 5. sampling-weight round trip (review 2.1) ------------------
    # Index rows in the capture hook's REAL shape (the
    # search_s3 json_encode field set for uncontested
    # rows; contested rows are the stock arm's shape,
    # the same fields minus uncontested/top_prior).
    def hookrow(snap, game, unc, priors, player):
        r = {"snap": snap, "game": game, "hcount": 1,
             "branch": "main", "player": player, "turn": 6,
             "cands": [{"a": 1}, {"a": 2}, {"a": 3}],
             "state": None, "priors": priors,
             "prior_pick": 0, "selected": [0, 1, 2]}
        if unc:
            r["uncontested"] = 1
            r["top_prior"] = max(priors)
        return r

    idx5 = os.path.join(tmp, "idx5.jsonl")
    jl(idx5, [hookrow("gW_t1", "gW", 1, [0.99, 0.006, 0.004], 1),
              hookrow("gX_t1", "gX", 0, [0.6, 0.3, 0.1], 2)])
    ej5 = os.path.join(tmp, "ej5.jsonl")
    ejr5 = os.path.join(tmp, "ejr5.json")
    p = run([os.path.join(CODE, "build_probe_eval_jobs.py"),
             "--stream", "s5=" + idx5, "--settings", settings,
             "--out", ej5, "--report", ejr5])
    check("W0: hook-shape index rows build eval jobs",
          p.returncode == 0)
    rows5 = []
    # gW_t1 uncontested: cand1 beats prior by +2 in
    # every world -> z = +inf -> class (a) at 1.5
    for w in range(25):
        rows5.append(wrow("gW_t1", 0, w, fin(-1)))
        rows5.append(wrow("gW_t1", 1, w, fin(1)))
        rows5.append(wrow("gW_t1", 2, w, fin(-1)))
    # gX_t1 contested: the sqrt(2) construction of
    # case B -> z in (1.25, 1.5] -> contested_band
    for w in range(25):
        rows5.append(wrow("gX_t1", 0, w, fin(priorB[w])))
        rows5.append(wrow("gX_t1", 1, w, fin(candB[w])))
        rows5.append(wrow("gX_t1", 2, w, fin(-1)))
    rows5f = os.path.join(tmp, "evals5.jsonl")
    jl(rows5f, rows5)
    st5 = os.path.join(tmp, "states5.jsonl")
    sm5 = os.path.join(tmp, "summary5.json")
    p = run([os.path.join(CODE, "probe_eval_analyze.py"),
             "--jobs", ej5, "--rows", rows5f,
             "--jobs-report", ejr5, "--settings", settings,
             "--states-out", st5, "--json-out", sm5])
    jobs5 = os.path.join(tmp, "jobs5.jsonl")
    jrep5 = os.path.join(tmp, "jobs5_report.json")
    p = run([os.path.join(CODE, "build_probe_jobs.py"),
             "--states", st5, "--eval-jobs", ej5,
             "--settings", settings, "--out", jobs5,
             "--shard-prefix", os.path.join(tmp, "jobs5_shard"),
             "--report", jrep5])
    check("W0b: states build one job per class",
          p.returncode == 0
          and json.load(open(jrep5))["by_class"]
          == {"uncontested": 1, "contested_band": 1})
    # label rows, in the read's SCORE units (win = 1,
    # loss = 0 per world): gW job diff exactly 0.8
    # (teacher scores in 40 worlds, prior in 0); gX
    # job diff exactly 0.4 (teacher 35, prior 15, the
    # prior's scoring worlds nested inside the
    # teacher's -> 20 worlds of +1)
    lab5 = []
    for snap, tw, pw in (("gW_t1", 40, 0), ("gX_t1", 35, 15)):
        for w in range(50):
            lab5.append({"snap": snap, "cand": 1, "world": w,
                         "pair": "va", "setting": LT,
                         "result": fin(1 if w < tw else -1)})
            lab5.append({"snap": snap, "cand": 0, "world": w,
                         "pair": "va", "setting": LT,
                         "result": fin(1 if w < pw else -1)})
    lab5f = os.path.join(tmp, "labels5.jsonl")
    jl(lab5f, lab5)
    cap5 = os.path.join(tmp, "capgames5.json")
    json.dump({"games_list": ["gW", "gX", "gY", "gZ"]},
              open(cap5, "w"))

    def label_read_at(settings_path, tag):
        out = os.path.join(tmp, "lr_%s.json" % tag)
        pp = run([os.path.join(CODE, "probe_label_analyze.py"),
                  "--jobs", jobs5, "--labels", lab5f,
                  "--capture-games", cap5,
                  "--settings", settings_path,
                  "--json-out", out])
        return pp, json.load(open(out))

    p2, lr_w = label_read_at(settings, "w2")
    st_e1 = json.load(open(settings))
    st_e1["capture"]["uncontested_every"] = 1
    se1f = os.path.join(tmp, "settings_every1.json")
    json.dump(st_e1, open(se1f, "w"))
    p1, lr_u = label_read_at(se1f, "w1")
    gw = lr_w["per_game_gain"]["uncontested"]
    gu = lr_u["per_game_gain"]["uncontested"]
    cw = lr_w["per_game_gain"]["contested_band"]
    cu = lr_u["per_game_gain"]["contested_band"]
    check("W1: EVERY=2 uncontested gain == 2x unweighted "
          "(0.8/4 games, weighted 1.6/4)",
          p2.returncode == 0 and p1.returncode == 0
          and abs(gu["gain"] - 0.20) < 1e-12
          and abs(gw["gain"] - 0.40) < 1e-12
          and abs(gw["gain"] - 2 * gu["gain"]) < 1e-12,
          "weighted=%s unweighted=%s" % (gw["gain"], gu["gain"]))
    check("W2: the CI scales by the same factor",
          abs(gw["ci"][0] - 2 * gu["ci"][0]) < 1e-9
          and abs(gw["ci"][1] - 2 * gu["ci"][1]) < 1e-9,
          "w CI %s vs 2x %s" % (gw["ci"],
                                [2 * x for x in gu["ci"]]))
    check("W3: contested-band gain + CI unchanged by the "
          "weighting code path",
          abs(cw["gain"] - cu["gain"]) < 1e-12
          and cw["ci"] == cu["ci"]
          and abs(cw["gain"] - 0.10) < 1e-12,
          "contested gain=%s both runs" % cw["gain"])
    check("W4: CLASS lines print the sampling weight "
          "(2 uncontested, 1 contested)",
          "CLASS uncontested:" in p2.stdout
          and "sampling weight 2" in p2.stdout
          and "sampling weight 1" in p2.stdout
          and gw["weight"] == 2.0 and cw["weight"] == 1.0)

    # ---- 6. uncontested class boundaries (review 3/F2) ---------------
    def staterow(snap, game, z):
        return {"snap": snap, "game": game, "player": 1,
                "branch": "main", "turn": 2,
                "uncontested": 1, "top_prior": 0.99,
                "prior_band": [0.97, 1.01], "z": z,
                "search_pick": 1, "prior_pick": 0,
                "mean_diff": 0.1, "se_diff": 0.05,
                "status": "ok"}

    states6 = [staterow("u10_t1", "u10", 1.0),
               staterow("u12_t1", "u12", 1.2),
               staterow("u15_t1", "u15", 1.5),
               staterow("u151_t1", "u151", 1.51)]
    st6f = os.path.join(tmp, "states6.jsonl")
    jl(st6f, states6)
    ej6 = [{"snap": r["snap"], "snap_dir": "d/" + r["snap"],
            "cands": [{}, {}]} for r in states6]
    ej6f = os.path.join(tmp, "ej6.jsonl")
    jl(ej6f, ej6)
    jobs6 = os.path.join(tmp, "jobs6.jsonl")
    jrep6 = os.path.join(tmp, "jobs6_report.json")
    p = run([os.path.join(CODE, "build_probe_jobs.py"),
             "--states", st6f, "--eval-jobs", ej6f,
             "--settings", settings, "--out", jobs6,
             "--shard-prefix", os.path.join(tmp, "jobs6_shard"),
             "--report", jrep6])
    lj6 = [json.loads(l) for l in open(jobs6)]
    by6 = {}
    for j in lj6:
        by6.setdefault(j["probe_band"], set()).add(j["snap"])
    check("B1: boundaries -- z=1.0 no job; (1.0,1.5] "
          "diagnostic (incl. z=1.5); z>1.5 class (a)",
          p.returncode == 0
          and by6.get("uncontested") == {"u151_t1"}
          and by6.get("uncontested_diag") == {"u12_t1", "u15_t1"}
          and len(lj6) == 3,
          str({k: sorted(v) for k, v in by6.items()}))
    rj6 = json.load(open(jrep6))
    check("B2: report carries the diagnostic class and "
          "the realized counts at all three margins",
          rj6["by_class"].get("uncontested_diag") == 2
          and rj6["alt_uncontested_counts"].get(
              "uncontested@1.50") == 1
          and rj6["alt_uncontested_counts"].get(
              "uncontested@1.00") == 3
          and rj6["uncontested_diag_margin"] == 1.0)

    # ---- 7. report prints (review 2.2 + sec.3 prints) ----------------
    def report_inputs(fires15):
        es = {"games": 90, "world_rows": 0,
              "eval_wall_ms_total": 138860000,
              "by_prior_band": {
                  "0.97-1.01": {"states": 3100,
                                "would_fire": {"1.5": 8},
                                "tail": 2}},
              "contested": {"states": 2000,
                            "would_fire": {"1.5": fires15,
                                           "1.25": 245,
                                           "1.0": 276}},
              "contested_band_125_150": {"states": 105,
                                         "per_game": 105 / 90},
              "per_game": {
                  "uncontested_states": 68.89,
                  "contested_would_fire": {
                      "1.5": fires15 / 90, "1.25": 2.72}}}
        ejr = {"states": 5240,
               "classes": {"uncontested": 3100,
                           "contested": 2140},
               "games": 90}
        lr = {"by_class": {
                  "uncontested": {"jobs": 6, "edge": 0.40,
                                  "ci": [0.10, 0.70]},
                  "uncontested_tail": {"jobs": 1,
                                       "edge": 0.50,
                                       "ci": [0.50, 0.50]},
                  "uncontested_by_prior_band": {},
                  "uncontested_diag": {"jobs": 11,
                                       "edge": 0.006,
                                       "ci": [-0.004, 0.016]},
                  "contested_band": {"jobs": 105,
                                     "edge": 0.011,
                                     "ci": [0.002, 0.020]}},
              "per_game_gain": {
                  "uncontested": {"gain": 0.05,
                                  "ci": [0.01, 0.09],
                                  "lb95_1sided": 0.01,
                                  "games": 90, "weight": 2.0},
                  "contested_band": {"gain": 0.077,
                                     "ci": [0.03, 0.124],
                                     "lb95_1sided": 0.03,
                                     "games": 90, "weight": 1.0}}}
        return es, ejr, lr

    def run_report(fires15, tag):
        es, ejr, lr = report_inputs(fires15)
        esf = os.path.join(tmp, "es_%s.json" % tag)
        ejf = os.path.join(tmp, "ejr_%s.json" % tag)
        lrf7 = os.path.join(tmp, "lr_%s_in.json" % tag)
        outf = os.path.join(tmp, "report_%s.json" % tag)
        json.dump(es, open(esf, "w"))
        json.dump(ejr, open(ejf, "w"))
        json.dump(lr, open(lrf7, "w"))
        pp = run([os.path.join(CODE, "probe_report.py"),
                  "--eval-summary", esf,
                  "--eval-jobs-report", ejf,
                  "--label-read", lrf7,
                  "--settings", settings,
                  "--json-out", outf])
        return pp, json.load(open(outf))

    FLAG = "offline eval does not reproduce"
    p_in, rep_in = run_report(150, "in")
    check("P1: calibration inside the band -- line "
          "printed at 0.0750/state, NO flag line",
          p_in.returncode == 0
          and "would-fire rate @1.5: 0.0750 per state"
          in p_in.stdout
          and FLAG not in p_in.stdout
          and rep_in["calibration"]["flag"] is False)
    om = rep_in["margin_lever"]["step2_outlook"]

    # ---- P2 (second fix pass, claude-reply-af9e9f8
    # sec.2.1): the power formula's two BY-HAND cases,
    # driven through probe_report.py's outlook() code
    # path with the contested band's gain object
    # replaced. (The pre-fix P2 verified Phi of the
    # WRONG formula -- (gain - 0.0649) against the
    # increment's own SE -- so it could not catch the
    # increment/total mix-up; these cases can: they
    # pin inc, se_inc,400, SE_new, z and the power to
    # hand values.)
    def run_report_gain(band_gain, tag):
        es, ejr, lr = report_inputs(150)
        lr["per_game_gain"]["contested_band"] = band_gain
        esf = os.path.join(tmp, "es_%s.json" % tag)
        ejf = os.path.join(tmp, "ejr_%s.json" % tag)
        lrf7 = os.path.join(tmp, "lr_%s_in.json" % tag)
        outf = os.path.join(tmp, "report_%s.json" % tag)
        json.dump(es, open(esf, "w"))
        json.dump(ejr, open(ejf, "w"))
        json.dump(lr, open(lrf7, "w"))
        pp = run([os.path.join(CODE, "probe_report.py"),
                  "--eval-summary", esf,
                  "--eval-jobs-report", ejf,
                  "--label-read", lrf7,
                  "--settings", settings,
                  "--json-out", outf])
        return pp, json.load(open(outf))

    # case (i): inc = 0 -> z = 0 -> power =
    # Phi(-1.645) = 0.04997, the bar's own alpha.
    p2a, rep2a = run_report_gain(
        {"gain": 0.0, "ci": [-0.02, 0.02],
         "lb95_1sided": -0.02, "games": 90,
         "weight": 1.0}, "p2a")
    o2a = rep2a["margin_lever"]["step2_outlook"]
    check("P2a: power formula -- inc = 0 gives the "
          "bar's own alpha (~0.05)",
          p2a.returncode == 0
          and abs(o2a["z_stat"]) < 1e-12
          and abs(o2a["power"] - 0.05) < 0.002
          and "[informational] MARGIN 1.25 Step 2 outlook"
          in p2a.stdout,
          "z=%.4f power=%.5f (Phi(-1.645) = 0.04998)"
          % (o2a["z_stat"], o2a["power"]))
    # case (ii): inc = 0.03 with se_inc,400 = 0.005
    # exactly -- the 90-game increment SE is chosen
    # as 0.005/sqrt(90/400) and the CI built around
    # the gain from it (input construction only; the
    # formula under test runs in probe_report.py).
    # By hand: SE_new = sqrt(0.009^2 + 0.005^2) =
    # 0.01030; z = 0.03/sqrt(SE_new^2 + 0.009^2) =
    # 2.194; power = Phi(0.549) = 0.708.
    se_inc90 = 0.005 / math.sqrt(90 / 400)
    half = 1.96 * se_inc90
    p2b, rep2b = run_report_gain(
        {"gain": 0.03, "ci": [0.03 - half, 0.03 + half],
         "lb95_1sided": 0.03 - half, "games": 90,
         "weight": 1.0}, "p2b")
    o2b = rep2b["margin_lever"]["step2_outlook"]
    check("P2b: power formula -- inc 0.03, se_inc,400 "
          "0.005: SE_new 0.0103, z 2.194, power 0.708",
          p2b.returncode == 0
          and abs(o2b["se_inc_at_bar_games"] - 0.005)
              < 1e-9
          and round(o2b["se_new_at_bar_games"], 4)
              == 0.0103
          and abs(o2b["z_stat"] - 2.194) < 0.002
          and abs(o2b["power"] - 0.708) < 0.002
          and "SE_new 0.0103" in p2b.stdout
          and "base gain is taken as Stage 3's"
              in p2b.stdout,
          "SE_new=%.6f z=%.4f power=%.4f"
          % (o2b["se_new_at_bar_games"], o2b["z_stat"],
             o2b["power"]))
    ot = rep_in["threshold_lever"]["step2_outlook"]
    unc_pg_exp = (3100 / 90) * 2
    cost_t_exp = 503 + unc_pg_exp * 19.5
    check("P3: price prints -- Step 2 + fleet box-hours "
          "at both levers' per-game costs",
          abs(om["step2_teacher_box_hours"]
              - 400 * 503 / 3600) < 1e-9
          and abs(om["fleet_teacher_box_hours_per_100_pairs"]
                  - 100 * 503 / 3600) < 1e-9
          and abs(ot["teacher_game_cost_s"]
                  - cost_t_exp) < 1e-9
          and abs(ot["step2_teacher_box_hours"]
                  - 400 * cost_t_exp / 3600) < 1e-6,
          "margin step2 %.2f h; threshold cost %.1f s, "
          "step2 %.2f h" % (om["step2_teacher_box_hours"],
                            ot["teacher_game_cost_s"],
                            ot["step2_teacher_box_hours"]))
    p_out, rep_out = run_report(500, "out")
    i_flag = p_out.stdout.find(FLAG)
    i_rec = p_out.stdout.find("RECOMMENDATION")
    check("P4: calibration outside the band (0.2500/"
          "state) -- flag line printed ABOVE the "
          "recommendation, which is still emitted",
          p_out.returncode == 0 and i_flag >= 0
          and 0 <= i_flag < i_rec
          and rep_out["calibration"]["flag"] is True
          and rep_out["recommendation"] != "")

    print("fx_probe_python: %s"
          % ("ALL PASS" if not FAILS else
             "FAILURES: %s" % FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
