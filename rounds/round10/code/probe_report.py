#!/usr/bin/env python3
"""Round-10 Step 0 probe: the registered report.

Assembles the probe's three measured pieces --
capture populations (eval jobs report), the offline
eval (eval summary), the L3 label read (label read
JSON) -- into the report shape the package registers
(claude-reply-9b04ad1 sec.3 + sec.5):

  1. tail rate per state and edge, by prior band
     (including >= 0.97, the uncontested population);
     the (1.0, 1.5] uncontested DIAGNOSTIC class
     (fix pass) is reported here too -- counts and
     edge, never a gain;
  2. the (1.25, 1.5] contested band: fires/game from
     the eval, edge and per-game gain from the labels;
  3. the CALIBRATION print (fix pass,
     claude-reply-402c92f sec.2.2): the probe's
     contested would-fire rate at margin 1.5, per
     state and per game, beside Stage 1's panel
     (22/240 = 0.092 per state) and the live rates
     (0.069 Stage 2, 0.065 Stage 3 per state); a
     per-state rate outside [0.04, 0.13] prints the
     flag line "offline eval does not reproduce the
     search's firing behavior" above the
     recommendation. A print and a flag, not a gate;
  4. per lever: predicted per-game gain (the label
     read's per-game gain, game-clustered, with its
     CI) and predicted teacher-game cost; plus the
     INFORMATIONAL prints (fix pass, sec.3): the
     predicted Step 2 power against the registered
     two-sample bar (settings report.step2_bar), the
     lever's gain SE scaled from the probe's games
     to 400 by the sqrt(n) rule, and the Step 2 +
     fleet teacher-arm prices at the lever's
     per-game cost;
  5. the recommendation under the registered
     decision rule (settings report.decision_rule).

Predicted costs. The margin lever adds NO searches:
the search already runs on every contested decision;
only the fire rule changes. Its predicted teacher-
game cost is the current cost (Stage 3 measured
503 s/game) and its fires rise from 1.555 to the
probe-measured margin-1.25 rate. The threshold lever
at threshold 0.97 adds one search per uncontested
decision: added seconds/game = uncontested
states/game x the live per-search wall (settings:
19.5 s, Stage 2/3's measured per-decision mean; the
probe's own offline wall per state is printed as a
cross-check) on top of the same 503 s base. A lower
threshold would add the contested band's searches
too -- those already run, so 0.97 is the only
threshold whose cost is new money; the report says
so rather than pricing thresholds it cannot price
from probe data (a sub-0.97 threshold changes which
states are searched, but every such state is
contested and already searched today -- its cost is
also zero, and its gain is the labeled band edges by
prior band; the report prints those reads and lets
the Step 1 design draw the conclusion).

Usage: probe_report.py --eval-summary eval_summary.json
  --eval-jobs-report eval_jobs_report.json
  --label-read label_read.json --settings
  settings_probe.json --json-out probe_report.json
  (text to stdout; the runner saves it)
"""
import argparse
import json
import math
import sys


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def phi(x):
    """Standard normal CDF, for the informational
    Step 2 power print (fix pass)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-summary", required=True)
    ap.add_argument("--eval-jobs-report", required=True)
    ap.add_argument("--label-read", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    es = json.load(open(a.eval_summary))
    ejr = json.load(open(a.eval_jobs_report))
    lr = json.load(open(a.label_read))
    settings = json.load(open(a.settings))
    rep = settings["report"]
    base_wall = float(rep["stage3_teacher_game_wall_s"])
    search_wall = float(rep["live_search_wall_s"])
    bar = rep["step2_bar"]
    bar_gain = float(bar["stage3_gain"])
    bar_se = float(bar["stage3_gain_se"])
    bar_games = int(bar["step2_games"])
    bar_z = float(bar["z_one_sided"])

    lines = ["=== ROUND-10 STEP 0 PROBE -- REPORT ==="]
    lines.append("capture: %d games; eval states %d "
                 "(uncontested %d sampled 1-in-%d, contested %d)"
                 % (es["games"], ejr["states"],
                    ejr["classes"].get("uncontested", 0),
                    settings["capture"]["uncontested_every"],
                    ejr["classes"].get("contested", 0)))

    lines.append("\n-- tail rate per state and edge, by "
                 "prior band (eval z > %.1f = tail)"
                 % float(rep["tail_z"]))
    band_rows = {}
    for name, s in es["by_prior_band"].items():
        rate = (s["tail"] / s["states"]) if s["states"] else None
        band_rows[name] = {"states": s["states"],
                           "would_fire_1.5": s["would_fire"]["1.5"],
                           "tail": s["tail"], "tail_rate": rate}
        lines.append("  prior [%s): states %d, would-fire@1.5 "
                     "%d, tail %d, tail rate %s"
                     % (name, s["states"], s["would_fire"]["1.5"],
                        s["tail"], pct(rate)))
    unc_tail = lr["by_class"].get("uncontested_tail", {})
    lines.append("  uncontested tail edge (labeled): %s CI "
                 "[%s, %s] over %d jobs"
                 % (pct(unc_tail.get("edge")),
                    pct(unc_tail["ci"][0]) if unc_tail.get("ci")
                    else "n/a",
                    pct(unc_tail["ci"][1]) if unc_tail.get("ci")
                    else "n/a", unc_tail.get("jobs", 0)))
    for bname, rd in sorted(
            lr["by_class"].get(
                "uncontested_by_prior_band", {}).items()):
        lines.append("  uncontested labeled edge, prior band "
                     "%s: %s CI [%s, %s] over %d jobs"
                     % (bname, pct(rd.get("edge")),
                        pct(rd["ci"][0]) if rd.get("ci") else "n/a",
                        pct(rd["ci"][1]) if rd.get("ci") else "n/a",
                        rd.get("jobs", 0)))
    diag_rd = lr["by_class"].get("uncontested_diag", {})
    lines.append("  uncontested DIAGNOSTIC class (1.0, 1.5] "
                 "(labeled; excluded from the threshold "
                 "gain and the decision rule): edge %s CI "
                 "[%s, %s] over %d jobs"
                 % (pct(diag_rd.get("edge")),
                    pct(diag_rd["ci"][0]) if diag_rd.get("ci")
                    else "n/a",
                    pct(diag_rd["ci"][1]) if diag_rd.get("ci")
                    else "n/a", diag_rd.get("jobs", 0)))

    gain_m = lr["per_game_gain"].get("contested_band", {})
    gain_t = lr["per_game_gain"].get("uncontested", {})
    edge_m = lr["by_class"].get("contested_band", {})
    lines.append("\n-- the (1.25, 1.5] contested band")
    lines.append("  fires/game (eval): %s; labeled edge %s CI "
                 "[%s, %s] over %d jobs; per-game gain %s CI "
                 "[%s, %s]"
                 % (pct(es["contested_band_125_150"]["per_game"]),
                    pct(edge_m.get("edge")),
                    pct(edge_m["ci"][0]) if edge_m.get("ci")
                    else "n/a",
                    pct(edge_m["ci"][1]) if edge_m.get("ci")
                    else "n/a", edge_m.get("jobs", 0),
                    pct(gain_m.get("gain")),
                    pct(gain_m["ci"][0]) if gain_m.get("ci")
                    else "n/a",
                    pct(gain_m["ci"][1]) if gain_m.get("ci")
                    else "n/a"))

    # -- calibration (fix pass, sec.2.2): does the
    # offline eval reproduce the search's known firing
    # behavior on the CONTESTED population, the one
    # population with live reads to compare against?
    con_states = es["contested"]["states"]
    con_fires15 = es["contested"]["would_fire"]["1.5"]
    cal_ps = (con_fires15 / con_states) if con_states else None
    cal_pg = es["per_game"]["contested_would_fire"]["1.5"]
    cal_flag = cal_ps is None or not (0.04 <= cal_ps <= 0.13)
    lines.append("\n-- calibration (offline eval vs known "
                 "firing behavior)")
    lines.append("  probe contested would-fire rate @1.5: "
                 "%s per state (%s per game; %d fires / %d "
                 "contested states)"
                 % (pct(cal_ps), pct(cal_pg), con_fires15,
                    con_states))
    lines.append("  references: Stage 1 panel 0.0917 per "
                 "state (22/240, raw-policy capture "
                 "states); live rates 0.069 (Stage 2), "
                 "0.065 (Stage 3) per state; flag band "
                 "[0.04, 0.13]")

    unc_pg = es["per_game"]["uncontested_states"]
    unc_sampled = ejr["classes"].get("uncontested", 0)
    # states/game in the CAPTURED (sampled) population; the
    # population rate uses the sampling factor:
    unc_pop_pg = None
    if es["games"]:
        # uncontested decisions/game = sampled states/game x
        # every (systematic sampling is unbiased for counts)
        unc_pop_pg = (unc_sampled / es["games"]
                      ) * settings["capture"]["uncontested_every"]
    thr_cost = (unc_pop_pg * search_wall
                if unc_pop_pg is not None else None)
    lines.append("\n-- per-lever predictions")
    lines.append("  MARGIN 1.25: predicted per-game gain %s "
                 "(lower bound %s); fires/game %s -> %s; "
                 "predicted teacher-game cost %.0f s "
                 "(no added searches)"
                 % (pct(gain_m.get("gain")),
                    pct(gain_m.get("lb95_1sided")),
                    pct(es["per_game"]["contested_would_fire"]["1.5"]),
                    pct(es["per_game"]["contested_would_fire"]["1.25"]),
                    base_wall))
    lines.append("  THRESHOLD 0.97: predicted per-game gain %s "
                 "(lower bound %s); uncontested decisions/game "
                 "%s (x%.1f sampled); added search cost %s "
                 "s/game at %.1f s/search -> teacher game "
                 "%.0f s (%.2fx)"
                 % (pct(gain_t.get("gain")),
                    pct(gain_t.get("lb95_1sided")),
                    pct(unc_pop_pg),
                    float(settings["capture"]["uncontested_every"]),
                    pct(thr_cost), search_wall,
                    base_wall + (thr_cost or 0),
                    (base_wall + (thr_cost or 0)) / base_wall))
    lines.append("  (cross-check: probe offline eval wall "
                 "total %d ms over %d states = %.1f s/state at "
                 "k=25, fleet-contention-free)"
                 % (es["eval_wall_ms_total"], ejr["states"],
                    es["eval_wall_ms_total"] / 1000.0
                    / max(1, ejr["states"])))

    def outlook(g, cost_s):
        """INFORMATIONAL (fix pass, sec.3): predicted
        Step 2 power against the registered two-sample
        bar, and the Step 2 + fleet teacher-arm prices
        at this lever's per-game cost. The gain SE at
        the probe's games is read off its CI
        (width / (2 x 1.96)); the SE at the bar's game
        count scales by the sqrt(n) rule."""
        if (not g or g.get("gain") is None
                or not g.get("ci")):
            return None
        n_probe = int(g.get("games") or es["games"])
        se_probe = (g["ci"][1] - g["ci"][0]) / (2 * 1.96)
        se_bar = se_probe * math.sqrt(n_probe / bar_games)
        z = ((g["gain"] - bar_gain)
             / math.sqrt(se_bar ** 2 + bar_se ** 2))
        return {"se_probe_games": se_probe,
                "probe_games": n_probe,
                "se_at_bar_games": se_bar,
                "bar_z": z,
                "power": phi(z - bar_z),
                "teacher_game_cost_s": cost_s,
                "step2_teacher_box_hours":
                    bar_games * cost_s / 3600.0,
                "fleet_teacher_box_hours_per_100_pairs":
                    100 * cost_s / 3600.0}

    thr_cost_s = base_wall + (thr_cost or 0)
    outl_m = outlook(gain_m, base_wall)
    outl_t = outlook(gain_t, thr_cost_s)
    for name, o in (("MARGIN 1.25", outl_m),
                    ("THRESHOLD 0.97", outl_t)):
        if o is None:
            lines.append("  [informational] %s: no labeled "
                         "gain -- Step 2 outlook n/a" % name)
            continue
        lines.append(
            "  [informational] %s Step 2 outlook: "
            "predicted power %.3f against the registered "
            "two-sample bar (gain - %.4f) / sqrt(SE_new^2 "
            "+ %.4f^2) >= %.3f, with SE_new at %d games "
            "= %.4f (scaled by sqrt(n) from the probe's "
            "%d-game gain SE %.4f; bar z = %.3f); prices "
            "at %.0f s/teacher game: Step 2 (%d games) "
            "%.1f box-h teacher arm; fleet %.1f box-h "
            "per 100 pairs teacher arm"
            % (name, o["power"], bar_gain, bar_se, bar_z,
               bar_games, o["se_at_bar_games"],
               o["probe_games"], o["se_probe_games"],
               o["bar_z"], o["teacher_game_cost_s"],
               bar_games, o["step2_teacher_box_hours"],
               o["fleet_teacher_box_hours_per_100_pairs"]))

    def buildable(g):
        lb = g.get("lb95_1sided")
        return lb is not None and lb > 0

    bm, bt = buildable(gain_m), buildable(gain_t)
    if bm and bt:
        lm = gain_m["lb95_1sided"]
        lt = gain_t["lb95_1sided"]
        overlap = (
            gain_m["ci"] and gain_t["ci"]
            and gain_m["ci"][0] <= gain_t["ci"][1]
            and gain_t["ci"][0] <= gain_m["ci"][1])
        if lm > lt and not overlap:
            rec = "margin 1.25"
        elif lt > lm and not overlap:
            rec = "threshold 0.97"
        else:
            rec = ("margin 1.25 (tie-break: lower bounds "
                   "within each other's CI, cheaper lever)")
        why = ("both buildable; lower bounds margin %s, "
               "threshold %s" % (pct(lm), pct(lt)))
    elif bm:
        rec = "margin 1.25"
        why = "only the margin's gain lower bound exceeds 0"
    elif bt:
        rec = "threshold 0.97"
        why = "only the threshold's gain lower bound exceeds 0"
    else:
        rec = "NO Step 1 build"
        why = ("neither lever's predicted gain lower bound "
               "exceeds 0")
    if cal_flag:
        lines.append("\noffline eval does not reproduce "
                     "the search's firing behavior")
    lines.append("\nRECOMMENDATION (registered rule): %s -- %s"
                 % (rec, why))
    lines.append("rule: %s" % rep["decision_rule"])

    out = {"band_tail_rates": band_rows,
           "calibration": {
               "contested_would_fire_rate_1.5_per_state": cal_ps,
               "contested_would_fire_rate_1.5_per_game": cal_pg,
               "fires": con_fires15, "contested_states":
                   con_states,
               "flag_band": [0.04, 0.13], "flag": cal_flag},
           "uncontested_diag": diag_rd,
           "margin_lever": {"gain": gain_m,
                            "edge": edge_m,
                            "teacher_game_cost_s": base_wall,
                            "step2_outlook": outl_m},
           "threshold_lever": {
               "gain": gain_t,
               "uncontested_decisions_per_game": unc_pop_pg,
               "added_search_s_per_game": thr_cost,
               "teacher_game_cost_s":
                   base_wall + (thr_cost or 0),
               "step2_outlook": outl_t},
           "recommendation": rec, "recommendation_why": why}
    print("\n".join(lines))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
