#!/usr/bin/env python3
"""Fixture: the sec.14 READ -- probe_label_analyze.py
computing BOTH scorings, probe_report.py deciding
on the cap-aligned one, and probe_influence.py's
hold rule evaluated on cap-aligned numbers.

Synthetic label set, 4 jobs x 2 candidates x 4
worlds (--expect-rows 4), every expectation
hand-computed. Root wins are outcome +1; prior
candidate worlds are all outright losses (score 0
under both scorings), so each job's diff is its
teacher candidate's mean score:

  S1 (G1, uncontested, z 4.0): teacher wins at
     turns 40 / 90 / 30, one loss. As-run diff
     3/4 = 0.75; cap-aligned the turn-90 win is a
     horizon draw: diff 2/4 = 0.50.
  S2 (G2, contested_band, z 1.4): wins at 50 / 70.
     As-run 0.50; cap-aligned 0.25.
  S3 (G1, uncontested_diag, z 1.2): one win, at
     turn 100. As-run 0.25; cap-aligned 0.00.
  S4 (G2, uncontested, z 2.0): wins at 80 / 85.
     As-run 0.50; cap-aligned class NULL (drop-out)
     -- excluded from the cap-aligned read.

Per-game gains (capture games G1, G2; uncontested
weight 2, contested weight 1):
  as-run uncontested: (0.75x2 + 0.50x2) / 2 = 1.25
  cap    uncontested: (0.50x2 + 0)      / 2 = 0.50
  as-run contested:   (0 + 0.50)        / 2 = 0.25
  cap    contested:   (0 + 0.25)        / 2 = 0.125

Report case (hand-built JSONs in the real shapes):
cap-aligned gains make ONLY the margin buildable
(LB +0.004 vs threshold -0.02) while the as-run
gains make ONLY the threshold buildable (-0.05 vs
+0.004). With --capalign-summary the recommendation
must be the cap-aligned one (margin 1.25) and the
as-run recommendation (threshold 0.97) must appear
only in the labeled co-report; without the flag
the same files must produce the as-run
recommendation (the legacy path intact).

Hold case: decide_hold on the cap-aligned report +
cap-aligned LOGO numbers fires exactly when a
buildable lever's cap-aligned LOGO lower bound
dips to <= 0.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
FAILED = []


def check(name, cond, extra=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name,
                       (" -- " + extra) if extra else ""))
    if not cond:
        FAILED.append(name)


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(CODE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def row(snap, cand, world, outcome, turns, setting):
    return {"snap": snap, "cand": cand, "world": world,
            "setting": setting,
            "result": {"outcome": outcome,
                       "winner": 1 if outcome > 0 else 2,
                       "horizon": 0, "finished": 1,
                       "turns": turns, "fallbacks": 0}}


def main():
    settings = json.load(open(os.path.join(
        CODE, "settings_probe.json")))
    LT = settings["label"]["tuple"]
    tmp = tempfile.mkdtemp(prefix="fx_capalign_read_")

    jobs = [
        {"snap": "S1", "game": "G1", "player": 1,
         "branch": "M", "turn": 5, "prior_pick": 0,
         "teacher_pick": 1, "probe_band": "uncontested",
         "prior_band": [0.85, 0.97], "z": 4.0,
         "setting": LT},
        {"snap": "S2", "game": "G2", "player": 1,
         "branch": "M", "turn": 5, "prior_pick": 0,
         "teacher_pick": 1,
         "probe_band": "contested_band",
         "prior_band": [0.5, 0.7], "z": 1.4,
         "setting": LT},
        {"snap": "S3", "game": "G1", "player": 1,
         "branch": "M", "turn": 5, "prior_pick": 0,
         "teacher_pick": 1,
         "probe_band": "uncontested_diag",
         "prior_band": [0.85, 0.97], "z": 1.2,
         "setting": LT},
        {"snap": "S4", "game": "G2", "player": 1,
         "branch": "M", "turn": 5, "prior_pick": 0,
         "teacher_pick": 1, "probe_band": "uncontested",
         "prior_band": [0.85, 0.97], "z": 2.0,
         "setting": LT},
    ]
    wins = {"S1": [(1, 40), (1, 90), (1, 30), (-1, 20)],
            "S2": [(1, 50), (1, 70), (-1, 25), (-1, 25)],
            "S3": [(1, 100), (-1, 20), (-1, 20), (-1, 20)],
            "S4": [(1, 80), (1, 85), (-1, 20), (-1, 20)]}
    rows = []
    for j in jobs:
        for w, (oc, t) in enumerate(wins[j["snap"]]):
            rows.append(row(j["snap"], 1, w, oc, t, LT))
        for w in range(4):
            rows.append(row(j["snap"], 0, w, -1, 20, LT))
    p_jobs = os.path.join(tmp, "jobs.jsonl")
    with open(p_jobs, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    p_labels = os.path.join(tmp, "labels.jsonl")
    with open(p_labels, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    p_games = os.path.join(tmp, "games.json")
    with open(p_games, "w") as f:
        json.dump({"games_list": ["G1", "G2"]}, f)
    p_classes = os.path.join(tmp, "classes.json")
    with open(p_classes, "w") as f:
        json.dump({"S1": "uncontested",
                   "S2": "contested_band",
                   "S3": "uncontested_diag",
                   "S4": None}, f)
    p_states = os.path.join(tmp, "capstates.jsonl")
    with open(p_states, "w") as f:
        for snap, z in (("S1", 4.0), ("S2", 1.4),
                        ("S3", 1.2), ("S4", 0.5)):
            f.write(json.dumps(
                {"snap": snap,
                 "cap_aligned": {"z": z}}) + "\n")
    p_settings = os.path.join(CODE, "settings_probe.json")

    def run_analyze(extra):
        out = os.path.join(tmp, "read%s.json"
                           % ("_cap" if extra else ""))
        cmd = [sys.executable,
               os.path.join(CODE, "probe_label_analyze.py"),
               "--jobs", p_jobs, "--labels", p_labels,
               "--capture-games", p_games,
               "--settings", p_settings,
               "--expect-rows", "4",
               "--json-out", out] + extra
        r = subprocess.run(cmd, capture_output=True,
                           text=True, timeout=300)
        if r.returncode != 0:
            return None, r.stdout + r.stderr
        return json.load(open(out)), r.stdout

    rd, txt = run_analyze(["--capalign-classes", p_classes,
                           "--capalign-states", p_states])
    check("R1: cap-mode analyze runs", rd is not None,
          (txt or "")[-300:])
    if rd is None:
        return 1
    g = rd["per_game_gain"]
    cg = rd["capaligned"]["per_game_gain"]
    check("R2: as-run gains are the hand-computed "
          "1.25 (uncontested) / 0.25 (contested)",
          abs(g["uncontested"]["gain"] - 1.25) < 1e-9
          and abs(g["contested_band"]["gain"] - 0.25) < 1e-9,
          "unc %s con %s" % (g["uncontested"]["gain"],
                             g["contested_band"]["gain"]))
    check("R3: cap-aligned gains are the "
          "hand-computed 0.50 / 0.125 -- the post-61 "
          "wins reprice to draws",
          abs(cg["uncontested"]["gain"] - 0.50) < 1e-9
          and abs(cg["contested_band"]["gain"] - 0.125)
          < 1e-9,
          "unc %s con %s" % (cg["uncontested"]["gain"],
                             cg["contested_band"]["gain"]))
    check("R4: drop-out S4 excluded exactly once; "
          "cap edges: uncontested 0.50 (S1 alone), "
          "contested 0.25, diag 0.00",
          rd["capaligned"]["excluded_jobs"] == 1
          and abs(rd["capaligned"]["by_class"]
                  ["uncontested"]["edge"] - 0.50) < 1e-9
          and abs(rd["capaligned"]["by_class"]
                  ["contested_band"]["edge"] - 0.25) < 1e-9
          and abs(rd["capaligned"]["by_class"]
                  ["uncontested_diag"]["edge"] - 0.0) < 1e-9)
    check("R5: cap tail subset follows the "
          "cap-aligned z (S1, edge 0.50 cap vs 0.75 "
          "as-run)",
          rd["capaligned"]["by_class"]
          ["uncontested_tail"]["jobs"] == 1
          and abs(rd["capaligned"]["by_class"]
                  ["uncontested_tail"]["edge"] - 0.50)
          < 1e-9
          and abs(rd["by_class"]["uncontested_tail"]
                  ["edge"] - 0.75) < 1e-9)
    check("R6: text labels both scorings, cap-aligned "
          "as the registered primary",
          "CAP-ALIGNED (registered primary)" in txt
          and "AS-RUN (pre-alignment scoring" in txt)
    rd2, _ = run_analyze([])
    check("R7: legacy mode (no flag) carries no "
          "capaligned block and the as-run gains",
          rd2 is not None and "capaligned" not in rd2
          and abs(rd2["per_game_gain"]["uncontested"]
                  ["gain"] - 1.25) < 1e-9)

    # ---- the report --------------------------------
    def esummary(fires15):
        return {"games": 90,
                "by_prior_band": {"0.85-0.97": {
                    "states": 50, "tail": 5,
                    "would_fire": {"1.5": 10}}},
                "contested": {"states": 200,
                              "would_fire":
                                  {"1.5": fires15}},
                "per_game": {
                    "contested_would_fire":
                        {"1.5": 0.2, "1.25": 0.3},
                    "uncontested_states": 30.0},
                "contested_band_125_150":
                    {"per_game": 0.05},
                "eval_wall_ms_total": 1000000}
    p_es_a = os.path.join(tmp, "es_asrun.json")
    with open(p_es_a, "w") as f:
        json.dump(esummary(20), f)
    cap_es = esummary(18)
    cap_es["scoring"] = "cap_aligned"
    cap_es["as_run"] = esummary(20)
    p_es_c = os.path.join(tmp, "es_cap.json")
    with open(p_es_c, "w") as f:
        json.dump(cap_es, f)
    p_ejr = os.path.join(tmp, "ejr.json")
    with open(p_ejr, "w") as f:
        json.dump({"states": 400, "classes":
                   {"uncontested": 300,
                    "contested": 100}}, f)

    def gain(g_, lo, hi, lb, w=1.0):
        return {"gain": g_, "ci": [lo, hi],
                "lb95_1sided": lb, "games": 90,
                "weight": w}
    lr = {"by_class": {
              "uncontested_tail": {"edge": 0.5,
                                   "ci": [0.1, 0.9],
                                   "jobs": 3},
              "uncontested_by_prior_band": {},
              "uncontested_diag": {"edge": 0.2,
                                   "ci": [0.0, 0.4],
                                   "jobs": 5},
              "contested_band": {"edge": 0.3,
                                 "ci": [0.1, 0.5],
                                 "jobs": 7}},
          "per_game_gain": {
              "contested_band": gain(-0.01, -0.05, 0.03,
                                     -0.05),
              "uncontested": gain(0.03, 0.004, 0.056,
                                  0.004, 2.0)},
          "capaligned": {
              "by_class": {
                  "uncontested_tail": {"edge": 0.4,
                                       "ci": [0.0, 0.8],
                                       "jobs": 2},
                  "uncontested_by_prior_band": {},
                  "uncontested_diag": {"edge": 0.1,
                                       "ci": [-0.1, 0.3],
                                       "jobs": 4},
                  "contested_band": {"edge": 0.35,
                                     "ci": [0.1, 0.6],
                                     "jobs": 6}},
              "per_game_gain": {
                  "contested_band": gain(0.02, 0.004,
                                         0.036, 0.004),
                  "uncontested": gain(0.01, -0.02, 0.04,
                                      -0.02, 2.0)},
              "excluded_jobs": 1}}
    p_lr = os.path.join(tmp, "label_read.json")
    with open(p_lr, "w") as f:
        json.dump(lr, f)

    def run_report(extra, es_path):
        out = os.path.join(
            tmp, "report%s.json" % ("_cap" if extra
                                    else "_asrun"))
        cmd = [sys.executable,
               os.path.join(CODE, "probe_report.py"),
               "--eval-summary", es_path,
               "--eval-jobs-report", p_ejr,
               "--label-read", p_lr,
               "--settings", p_settings,
               "--json-out", out] + extra
        r = subprocess.run(cmd, capture_output=True,
                           text=True, timeout=120)
        if r.returncode != 0:
            return None, r.stdout + r.stderr
        return json.load(open(out)), r.stdout

    rep_c, txt_c = run_report(
        ["--capalign-summary", p_es_c], p_es_a)
    check("R8: cap-mode report runs and RECOMMENDS "
          "ON THE CAP-ALIGNED GAINS (margin 1.25, the "
          "only cap-buildable lever)",
          rep_c is not None
          and rep_c["recommendation"] == "margin 1.25"
          and rep_c["scoring"] == "cap_aligned",
          (txt_c or "")[-200:])
    check("R9: the as-run recommendation (threshold "
          "0.97) appears only as the labeled "
          "co-report, in text and JSON",
          rep_c is not None
          and rep_c["as_run"]["recommendation"]
          == "threshold 0.97"
          and "AS-RUN co-report" in txt_c
          and "RECOMMENDATION (registered rule): "
              "margin 1.25" in txt_c)
    rep_a, _ = run_report([], p_es_a)
    check("R10: without the flag the same files "
          "recommend on the as-run gains (threshold "
          "0.97) -- legacy path intact",
          rep_a is not None
          and rep_a["recommendation"] == "threshold 0.97"
          and "as_run" not in rep_a)

    # ---- the hold rule on cap-aligned numbers ------
    inf = load_mod("probe_influence")
    logo_cap = {"margin": {"min_lb": 0.001},
                "threshold": {"min_lb": -0.03}}
    rep_both = {"margin_lever": {"gain": {
                    "lb95_1sided": 0.004}},
                "threshold_lever": {"gain": {
                    "lb95_1sided": 0.01}}}
    hold = inf.decide_hold(rep_both, logo_cap)
    check("R11: hold fires for the threshold lever "
          "on its CAP-ALIGNED numbers (buildable at "
          "LB +0.01, cap LOGO min LB -0.03) and not "
          "for the margin (cap LOGO min LB +0.001)",
          hold["threshold"]["hold"]
          == "buildable, single-game dependent"
          and hold["margin"]["hold"] is None)
    logo_asrun = {"margin": {"min_lb": 0.001},
                  "threshold": {"min_lb": 0.002}}
    hold2 = inf.decide_hold(rep_both, logo_asrun)
    check("R12: the same report with as-run LOGO "
          "numbers fires no hold -- the rule follows "
          "the numbers it is fed, and sec.14 feeds "
          "it the cap-aligned ones",
          hold2["threshold"]["hold"] is None)

    print("fx_capalign_read: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
