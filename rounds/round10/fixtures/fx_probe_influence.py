#!/usr/bin/env python3
"""Fixture: the registered influence read's LOGO and
hold rule (code/probe_influence.py, fix pass 5,
claude-reply-9dae0e2 sec.2.3), driven on synthetic
per-game gain tables through the script's own
compute_logo / decide_hold (which run
probe_label_analyze.per_game_gain -- the registered
machinery, fixed-seed bootstrap, so every number
below is deterministic).

L1 CONCENTRATED: ten games; G9 carries +9.0 of a
   +9.7 total (five games +0.3, four -0.2). LOGO
   must identify G9 with share 9/9.7, range
   [0.7/9, 1.1], and the G9 exclusion's lower bound
   must be <= 0 -- so with a buildable report the
   hold line prints for that lever.
L2 DIFFUSE: ten games at +0.5 each; every exclusion
   leaves gain 0.5 with lower bound 0.5 > 0, so no
   hold line even though the lever is buildable.
L3 NOT BUILDABLE: the concentrated table with a
   report lower bound <= 0 -- the hold rule stays
   silent (it fires only on a buildable lever).
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
FAILED = []


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(CODE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL",
                        name, extra))
    if not cond:
        FAILED.append(name)


def rec(game, diff):
    return {"game": game, "diff": diff,
            "probe_band": "uncontested",
            "prior_band": [0.97, 1.01], "z": 4.0,
            "n_worlds": 25}


def main():
    inf = load_mod("probe_influence")
    games = ["G%d" % i for i in range(10)]

    conc = [rec("G9", 4.0), rec("G9", 5.0)]
    conc += [rec("G%d" % i, 0.3) for i in range(5)]
    conc += [rec("G%d" % i, -0.2) for i in range(5, 9)]
    logo = inf.compute_logo(conc, games, 1.0)
    check("L1 full gain = 0.97",
          abs(logo["full_gain"] - 0.97) < 1e-9,
          "got %s" % logo["full_gain"])
    check("L1 top game is G9 with share 9/9.7",
          logo["top_game"] == "G9"
          and abs(logo["top_share"] - 9.0 / 9.7) < 1e-9,
          "share %s" % logo["top_share"])
    check("L1 LOGO range = [0.7/9, 1.1]",
          abs(logo["logo_min_gain"] - 0.7 / 9) < 1e-9
          and abs(logo["logo_max_gain"] - 1.1) < 1e-9,
          "got [%s, %s]" % (logo["logo_min_gain"],
                            logo["logo_max_gain"]))
    check("L1 weakest exclusion lower bound <= 0 "
          "(game G9)", logo["min_lb"] <= 0
          and logo["min_lb_game"] == "G9",
          "lb %s at %s" % (logo["min_lb"],
                           logo["min_lb_game"]))
    check("L1 G9-excluded gain = 0.7/9",
          abs(logo["top_game_excl_gain"] - 0.7 / 9)
          < 1e-9)

    report = {"margin_lever": {"gain": {
                  "lb95_1sided": -0.01}},
              "threshold_lever": {"gain": {
                  "lb95_1sided": 0.02}}}
    hold = inf.decide_hold(report,
                           {"threshold": logo,
                            "margin": logo})
    check("L1 hold line prints for the buildable "
          "concentrated lever",
          hold["threshold"]["hold"]
          == "buildable, single-game dependent")
    check("L1 no hold for the non-buildable lever on "
          "the same table",
          hold["margin"]["hold"] is None)

    diff = [rec(g, 0.5) for g in games]
    logo_d = inf.compute_logo(diff, games, 1.0)
    check("L2 diffuse: every exclusion leaves gain "
          "and lower bound at 0.5",
          abs(logo_d["logo_min_gain"] - 0.5) < 1e-9
          and abs(logo_d["min_lb"] - 0.5) < 1e-9,
          "min_lb %s" % logo_d["min_lb"])
    hold_d = inf.decide_hold(report,
                             {"threshold": logo_d,
                              "margin": logo_d})
    check("L2 no hold line for the diffuse table",
          hold_d["threshold"]["hold"] is None)

    report_nb = {"margin_lever": {"gain": {
                     "lb95_1sided": 0.0}},
                 "threshold_lever": {"gain": {
                     "lb95_1sided": -0.03}}}
    hold_nb = inf.decide_hold(report_nb,
                              {"threshold": logo,
                               "margin": logo})
    check("L3 no hold when neither lever is "
          "buildable, however concentrated",
          hold_nb["threshold"]["hold"] is None
          and hold_nb["margin"]["hold"] is None)

    print("fx_probe_influence: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
