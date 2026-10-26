#!/usr/bin/env python3
"""Fixture for code/tie_as_loss.py (round-9 Stage 0 sec.3
tie-as-loss co-read). Synthetic jobs/rows with expectations
computed by hand below; exit 0 iff every check passes.

PLANTED FIXTURE (all jobs player 1; winner is 1 on a win for
the deciding side, 2 on a loss, 0 on a draw -- outcome +1/-1/0):

  Job fA (game g1), worlds 0-3 shared:
    teacher outcomes [+1, 0, -1, +1] -> std scores [1, .5, 0, 1]
    prior   outcomes [ 0, 0, -1, -1] -> std scores [.5, .5, 0, 0]
    std diff = .625 - .25 = +0.375
    TAL scores: teacher [1, 0, 0, 1] -> .5 ; prior [0, 0, 0, 0] -> 0
    TAL diff = +0.5
    (plus: teacher world 4 is an error row; prior world 4 is
     finished but unpaired -- both outside both reads)
  Job fB (game g1), worlds 0-1 shared:
    teacher [+1, +1], prior [+1, 0]
    std diff = 1.0 - .75 = +0.25 ; TAL diff = 1.0 - .5 = +0.5
    (plus: prior world 2 has finished == 0 -- excluded)
  Job fC (game g2), worlds 0-1 shared:
    teacher [0, 0], prior [+1, -1]
    std diff = .5 - .5 = 0.0 ; TAL diff = 0.0 - .5 = -0.5
    (plus: a duplicate teacher world-0 row with outcome -1 --
     counted as dup_world, first row wins)

EXPECTATIONS:
  jobs scored 3; worlds_min 2
  integrity: rows 20, error_rows 1, unfinished 1, dup_world 1,
    null_results 0, unknown_snap 0
  paired drawn worlds: teacher 3 (fA w1; fC w0, w1),
    prior 3 (fA w0, w1; fB w1)
  standard   : mean (0.375 + 0.25 + 0) / 3 = 0.208333...
               frac pos 2/3, zero 1/3, neg 0
               per-game gain = mean x 3/400 = 0.0015625
  tie-as-loss: mean (0.5 + 0.5 - 0.5) / 3 = 0.166666...
               frac pos 2/3, zero 0, neg 1/3
               per-game gain = 0.00125
  marker violations 0 (winner == 0 iff outcome == 0 throughout)
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAILURES = []


def check(name, cond, detail=""):
    print("%s: %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILURES.append(name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tal_mod = load("tie_as_loss", os.path.join(HERE, "..", "code",
                                           "tie_as_loss.py"))
scorer = tal_mod.load_scorer()


def row(snap, cand, world, outcome=None, winner=None, **kw):
    res = {"finished": 1, "fallbacks": 0}
    if outcome is not None:
        res["outcome"] = outcome
    if winner is not None:
        res["winner"] = winner
    res.update(kw)
    return {"snap": snap, "cand": cand, "world": world, "result": res}


W = {1.0: 1, 0.0: 0, -1.0: 2}  # outcome -> winner (player 1 deciding)

jobs = [
    {"snap": "fA", "game": "g1", "player": 1, "prior_pick": 0,
     "teacher_pick": 1},
    {"snap": "fB", "game": "g1", "player": 1, "prior_pick": 0,
     "teacher_pick": 1},
    {"snap": "fC", "game": "g2", "player": 1, "prior_pick": 0,
     "teacher_pick": 1},
]
rows = []
for w, o in enumerate([1.0, 0.0, -1.0, 1.0]):
    rows.append(row("fA", 1, w, o, W[o]))
for w, o in enumerate([0.0, 0.0, -1.0, -1.0]):
    rows.append(row("fA", 0, w, o, W[o]))
rows.append({"snap": "fA", "cand": 1, "world": 4,
             "result": {"error": "abort"}})
rows.append(row("fA", 0, 4, 1.0, 1))
for w, o in enumerate([1.0, 1.0]):
    rows.append(row("fB", 1, w, o, W[o]))
for w, o in enumerate([1.0, 0.0]):
    rows.append(row("fB", 0, w, o, W[o]))
rows.append(row("fB", 0, 2, finished=0))
for w, o in enumerate([0.0, 0.0]):
    rows.append(row("fC", 1, w, o, W[o]))
rows.append(row("fC", 1, 0, -1.0, 2))  # duplicate; first wins
for w, o in enumerate([1.0, -1.0]):
    rows.append(row("fC", 0, w, o, W[o]))

job_by_snap, worlds, integ, diag = tal_mod.collect(jobs, rows)
check("FX-TAL integrity rows", integ["rows"] == 20, str(integ["rows"]))
check("FX-TAL integrity error/unfinished/dup",
      (integ["error_rows"], integ["unfinished"], integ["dup_world"],
       integ["null_results"], integ["unknown_snap"]) == (1, 1, 1, 0, 0),
      str({k: integ[k] for k in ("error_rows", "unfinished", "dup_world")}))

exp = {"standard": {"fA": 0.375, "fB": 0.25, "fC": 0.0},
       "tie_as_loss": {"fA": 0.5, "fB": 0.5, "fC": -0.5}}
for mode in ("standard", "tie_as_loss"):
    records, missing, wmin, draws = tal_mod.build_records(
        job_by_snap, worlds, mode, diag,
        collect_diag=(mode == "standard"))
    got = {r["snap"]: r["diff"] for r in records}
    check("FX-TAL %s per-job diffs" % mode,
          got == exp[mode] and missing == 0 and wmin == 2, str(got))
    if mode == "standard":
        check("FX-TAL paired drawn worlds",
              draws == {"teacher": 3, "prior": 3}, str(draws))

out = tal_mod.one_read(scorer, jobs, rows)
std, tal = out["reads"]["standard"], out["reads"]["tie_as_loss"]
check("FX-TAL standard mean",
      abs(std["mean_diff"] - 0.625 / 3) < 1e-12, repr(std["mean_diff"]))
check("FX-TAL tie-as-loss mean",
      abs(tal["mean_diff"] - 0.5 / 3) < 1e-12, repr(tal["mean_diff"]))
check("FX-TAL standard fracs",
      (std["frac_pos"], std["frac_zero"], std["frac_neg"]) ==
      (2 / 3, 1 / 3, 0.0), str((std["frac_pos"], std["frac_zero"],
                                std["frac_neg"])))
check("FX-TAL tie-as-loss fracs",
      (tal["frac_pos"], tal["frac_zero"], tal["frac_neg"]) ==
      (2 / 3, 0.0, 1 / 3), str((tal["frac_pos"], tal["frac_zero"],
                                tal["frac_neg"])))
check("FX-TAL per-game gains",
      abs(std["per_game_gain"] - 0.0015625) < 1e-12 and
      abs(tal["per_game_gain"] - 0.00125) < 1e-12,
      "%r / %r" % (std["per_game_gain"], tal["per_game_gain"]))
check("FX-TAL CIs bracket their means",
      std["ci"][0] <= std["mean_diff"] <= std["ci"][1] and
      tal["ci"][0] <= tal["mean_diff"] <= tal["ci"][1],
      "%s / %s" % (std["ci"], tal["ci"]))
check("FX-TAL marker violations zero",
      diag["marker_violations"] == 0 and
      diag["paired_marker_violations"] == 0 and
      diag["paired_missing_winner"] == 0, str(diag))

print("FX-TAL: %s" % ("ALL PASS" if not FAILURES else
                      "FAILURES: %s" % FAILURES))
sys.exit(1 if FAILURES else 0)
