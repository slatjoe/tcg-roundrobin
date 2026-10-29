#!/usr/bin/env python3
"""Fixture: the influence read's COMPOSED path --
code/probe_influence.py's main() driven
end-to-end (subprocess, argv set) on synthetic
published-form inputs (fix pass 6, package doc
sec.15).

Why this fixture exists: the recovery run of
2026-10-29 crashed in main() at the LOGO loop
with "NameError: name 'logo_by_lever' is not
defined". The fix-pass-5 fixtures
(fx_probe_influence.py, L1-L3) exercise
compute_logo / decide_hold with hand-built
inputs; no fixture had ever run main() itself,
so the uninitialized accumulator on the
composed path was invisible to the suite. This
fixture runs the real main() twice -- once
cap-aligned (the mode the recovery runs), once
as-run -- over a small synthetic set in the
real files' shapes:

  * game A (700000001) carries three recovered
    jobs (bare-Infinity z, the merged file's
    shape), each inspected from synthetic eval
    rows: the prior pick's 4 worlds are 3
    horizon draws priced -1 + 1 outright loss;
    the search pick's are 3 wins by turn 61 +
    1 win after turn 61;
  * the threshold lever's labeled gain sits in
    ONE game (B: one job, diff +1.0, sampling
    weight 2 -> per-game total 2.0 of a 2.0
    total over 6 capture games), so excluding
    B zeroes it: with a buildable report the
    hold line must fire THROUGH main();
  * the margin lever's report lower bound is
    <= 0 (not buildable), so its hold stays
    silent;
  * one job's cap-aligned class is null (a
    drop-out): excluded and counted.

M13 also syntax-checks the completion step
(code/run_probe_completion.sh, bash -n). The
completion script is NOT executed here -- it
runs once, after review, against the real
published outputs.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
FAILED = []

A, B, C, D, E, F = ("70000000%d" % i
                    for i in range(1, 7))
GAMES = [A, B, C, D, E, F]


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL",
                        name, extra))
    if not cond:
        FAILED.append(name)


def job(snap, game, turn, z, band):
    return {"snap": snap, "game": game,
            "turn": turn, "z": z,
            "prior_pick": 0, "teacher_pick": 1,
            "cands": [{"card_id": "prior_card_x"},
                      {"card_id": "search_card_x"}],
            "top_prior": 1.0, "probe_band": band,
            "prior_band": [0.97, 1.01]}


def rows_for(snap, teacher_res, prior_res, n=4):
    out = []
    for w in range(n):
        out.append({"snap": snap, "cand": 1,
                    "world": w, "result": teacher_res})
        out.append({"snap": snap, "cand": 0,
                    "world": w, "result": prior_res})
    return out


def fin(outcome, turns, horizon=0):
    return {"finished": 1, "outcome": outcome,
            "turns": turns, "horizon": horizon}


def build_inputs(d):
    jobs = []
    labels = []
    cmap = {}
    # the three recovered jobs (game A): labeled
    # diff 0 cap-aligned (teacher wins only after
    # the cap; the prior's worlds are draws).
    for t in (64, 65, 66):
        snap = "%s_t%d" % (A, t)
        jobs.append(job(snap, A, t, float("inf"),
                        "uncontested"))
        cmap[snap] = "uncontested"
        labels += rows_for(snap, fin(1, 70),
                           fin(0, 95, horizon=1))
    # game B: the threshold carrier, diff +1.0.
    jobs.append(job("%s_t10" % B, B, 10, 4.5,
                    "uncontested"))
    cmap["%s_t10" % B] = "uncontested"
    labels += rows_for("%s_t10" % B, fin(1, 50),
                       fin(-1, 40))
    # games C, E, F: threshold jobs at diff 0.
    for g in (C, E, F):
        snap = "%s_t10" % g
        jobs.append(job(snap, g, 10, 2.0,
                        "uncontested"))
        cmap[snap] = "uncontested"
        labels += rows_for(snap, fin(-1, 40),
                           fin(-1, 40))
    # game C: a margin (contested_band) job, diff 0.
    jobs.append(job("%s_t20" % C, C, 20, 2.0,
                    "contested_band"))
    cmap["%s_t20" % C] = "contested_band"
    labels += rows_for("%s_t20" % C, fin(-1, 40),
                       fin(-1, 40))
    # game D: a drop-out -- cap-aligned class
    # null; diff +1.0 as-run, excluded aligned.
    jobs.append(job("%s_t10" % D, D, 10, 3.0,
                    "contested_band"))
    cmap["%s_t10" % D] = None
    labels += rows_for("%s_t10" % D, fin(1, 50),
                       fin(-1, 40))
    # game E: a diagnostic-superset job.
    jobs.append(job("%s_t20" % E, E, 20, 1.2,
                    "uncontested_diag"))
    cmap["%s_t20" % E] = "uncontested_diag"
    labels += rows_for("%s_t20" % E, fin(-1, 40),
                       fin(-1, 40))

    def w(name, text):
        p = os.path.join(d, name)
        with open(p, "w") as f:
            f.write(text)
        return p

    # json.dumps writes the bare Infinity token
    # for the recovered jobs -- the merged file's
    # real shape.
    jobs_p = w("jobs.jsonl", "".join(
        json.dumps(j) + "\n" for j in jobs))
    labels_p = w("labels.jsonl", "".join(
        json.dumps(r) + "\n" for r in labels))
    cmap_p = w("capalign_classes.json",
               json.dumps(cmap))
    settings_p = w("settings.json", json.dumps(
        {"capture": {"uncontested_every": 2}}))
    games_p = w("capture_games.json", json.dumps(
        {"games_list": GAMES}))
    report_p = w("report.json", json.dumps({
        "margin_lever": {"gain": {
            "lb95_1sided": -0.01}},
        "threshold_lever": {"gain": {
            "lb95_1sided": 0.15}}}))
    # the eval side for game A's three snaps:
    # cand 0 (prior): 3 horizon draws + 1 loss;
    # cand 1 (search): 3 wins by 61 + 1 after.
    ej, es, ev = [], [], []
    diag = {"finished": 4, "unfinished": 0,
            "refusal": 0}
    for t in (64, 65, 66):
        snap = "%s_t%d" % (A, t)
        ej.append({"snap": snap, "selected": [0, 1]})
        es.append({"snap": snap, "cand_diag": {
            "0": dict(diag), "1": dict(diag)}})
        for wd in range(3):
            ev.append({"snap": snap, "cand": 0,
                       "world": wd,
                       "result": fin(0, 95, horizon=1)})
            ev.append({"snap": snap, "cand": 1,
                       "world": wd,
                       "result": fin(1, 50)})
        ev.append({"snap": snap, "cand": 0, "world": 3,
                   "result": fin(-1, 40)})
        ev.append({"snap": snap, "cand": 1, "world": 3,
                   "result": fin(1, 70)})
    ej_p = w("eval_jobs.jsonl", "".join(
        json.dumps(x) + "\n" for x in ej))
    es_p = w("eval_states.jsonl", "".join(
        json.dumps(x) + "\n" for x in es))
    ev_p = w("evals.jsonl", "".join(
        json.dumps(x) + "\n" for x in ev))
    drv_p = w("driver_rows.jsonl", json.dumps({
        "gamename": A, "seat": 2, "seed": 24070,
        "winner": 0, "draw": True, "capped": True,
        "cap_reason": "turns", "turns": 63,
        "p1life": 19, "p2life": 8}) + "\n")
    return {"jobs": jobs_p, "labels": labels_p,
            "cmap": cmap_p, "settings": settings_p,
            "games": games_p, "report": report_p,
            "eval_jobs": ej_p, "eval_states": es_p,
            "evals": ev_p, "driver": drv_p}


def run_main(inp, d, capaligned):
    out_json = os.path.join(
        d, "influence_%s.json"
        % ("cap" if capaligned else "asrun"))
    argv = [sys.executable,
            os.path.join(CODE, "probe_influence.py"),
            "--jobs", inp["jobs"],
            "--labels", inp["labels"],
            "--capture-games", inp["games"],
            "--settings", inp["settings"],
            "--eval-jobs", inp["eval_jobs"],
            "--evals", inp["evals"],
            "--eval-states", inp["eval_states"],
            "--driver-rows", inp["driver"],
            "--report-json", inp["report"],
            "--game", A,
            "--json-out", out_json]
    if capaligned:
        argv += ["--capalign-classes", inp["cmap"]]
    p = subprocess.run(argv, capture_output=True,
                       text=True)
    js = None
    if os.path.exists(out_json):
        js = json.load(open(out_json))
    return p, js


def main():
    d = tempfile.mkdtemp(prefix="fx_infl_main_")
    inp = build_inputs(d)

    # ---- cap-aligned run (the recovery's mode)
    p, js = run_main(inp, d, capaligned=True)
    txt = p.stdout
    check("M1 cap-aligned main() runs end-to-end "
          "(exit 0; the 2026-10-29 NameError path)",
          p.returncode == 0,
          "rc=%d stderr=%s" % (p.returncode,
                               p.stderr.strip()[-200:]))
    ok = js is not None and "game_inspection" in js \
        and "logo" in js and "hold" in js \
        and "hold_lines" in js
    check("M2 influence JSON carries inspection, "
          "LOGO, hold and hold_lines", ok)
    if not ok:
        print("fx_influence_main: FAILURES %s"
              % FAILED)
        return 1
    snaps = js["game_inspection"]["snaps"]
    s0 = snaps[0]
    check("M3 inspection finds the driver row "
          "(capped, 63 turns)",
          js["game_inspection"]["driver_row"]
          ["turns"] == 63
          and js["game_inspection"]["driver_row"]
          ["capped"] is True)
    check("M4 inspection counts for the first "
          "recovered snap (3 horizon draws, 1 "
          "loss; 3 wins by 61, 1 after)",
          s0["prior_horizon_draws_priced_minus1"] == 3
          and s0["prior_outright_losses"] == 1
          and s0["prior_other_worlds"] == 0
          and s0["search_wins_by_turn61"] == 3
          and s0["search_wins_after_turn61"] == 1
          and s0["cand_diag_agrees"] is True,
          "got %s" % {k: s0[k] for k in (
              "prior_horizon_draws_priced_minus1",
              "prior_outright_losses",
              "search_wins_by_turn61",
              "search_wins_after_turn61")})
    check("M5 text reports cand_diag agreement",
          "eval cand_diag agrees: yes" in txt)
    logo = js["logo"]["threshold"]
    check("M6 threshold LOGO through main(): full "
          "gain 2/6, carrier B with share 1.0",
          abs(logo["full_gain"] - 2.0 / 6) < 1e-9
          and logo["top_game"] == B
          and abs(logo["top_share"] - 1.0) < 1e-9,
          "gain %s share %s"
          % (logo["full_gain"], logo["top_share"]))
    check("M7 threshold LOGO range [0, 0.4]",
          abs(logo["logo_min_gain"]) < 1e-9
          and abs(logo["logo_max_gain"] - 0.4) < 1e-9,
          "got [%s, %s]" % (logo["logo_min_gain"],
                            logo["logo_max_gain"]))
    check("M8 weakest exclusion lower bound is "
          "exactly 0 (carrier excluded)",
          logo["min_lb"] == 0.0
          and logo["top_game_excl_lb"] == 0.0,
          "min_lb %s" % logo["min_lb"])
    check("M9 hold line fires through main() for "
          "the buildable concentrated lever",
          js["hold_lines"] == [
              "  threshold: buildable, "
              "single-game dependent"]
          and "threshold: buildable, single-game "
              "dependent" in txt)
    check("M10 no hold for the non-buildable "
          "margin lever",
          js["hold"]["margin"]["hold"] is None
          and "margin: hold rule not triggered"
          in txt)
    check("M11 the drop-out job is excluded and "
          "counted (cap-aligned)",
          js.get("capaligned_excluded_jobs") == 1
          and "1 drop-out jobs excluded" in txt)

    # ---- as-run mode (no --capalign-classes)
    p2, js2 = run_main(inp, d, capaligned=False)
    check("M12 as-run main() runs end-to-end; no "
          "cap-aligned block; hold still fires",
          p2.returncode == 0 and js2 is not None
          and "scoring" not in js2
          and js2["hold_lines"] == [
              "  threshold: buildable, "
              "single-game dependent"],
          "rc=%d" % p2.returncode)

    # ---- the completion step: syntax only
    comp = os.path.join(CODE, "run_probe_completion.sh")
    q = subprocess.run(["bash", "-n", comp],
                       capture_output=True, text=True)
    check("M13 run_probe_completion.sh is "
          "bash -n clean (not executed here)",
          q.returncode == 0, q.stderr.strip()[:200])

    print("fx_influence_main: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
