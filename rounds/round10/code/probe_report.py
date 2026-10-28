#!/usr/bin/env python3
"""Round-10 Step 0 probe: the registered report.

Assembles the probe's three measured pieces --
capture populations (eval jobs report), the offline
eval (eval summary), the L3 label read (label read
JSON) -- into the report shape the package registers
(claude-reply-9b04ad1 sec.3 + sec.5):

  1. tail rate per state and edge, by prior band
     (including >= 0.97, the uncontested population);
  2. the (1.25, 1.5] contested band: fires/game from
     the eval, edge and per-game gain from the labels;
  3. per lever: predicted per-game gain (the label
     read's per-game gain, game-clustered, with its
     CI) and predicted teacher-game cost;
  4. the recommendation under the registered
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
import sys


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


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
    lines.append("\nRECOMMENDATION (registered rule): %s -- %s"
                 % (rec, why))
    lines.append("rule: %s" % rep["decision_rule"])

    out = {"band_tail_rates": band_rows,
           "margin_lever": {"gain": gain_m,
                            "edge": edge_m,
                            "teacher_game_cost_s": base_wall},
           "threshold_lever": {
               "gain": gain_t,
               "uncontested_decisions_per_game": unc_pop_pg,
               "added_search_s_per_game": thr_cost,
               "teacher_game_cost_s":
                   base_wall + (thr_cost or 0)},
           "recommendation": rec, "recommendation_why": why}
    print("\n".join(lines))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
