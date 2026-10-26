#!/usr/bin/env python3
"""Round-9 Stage 1 analyzer (design sec.4.3-4.4 as settled by
claude-reply-16f02e2 sec.4; clause 8's second placement).

Reads the panel jobs, the registered settings
(settings_stage1.json) and, per setting, the evaluator's
world rows + stat rows, and computes:

  * COMPLETION (the selection metric; per-state, as
    registered and as fixed per claude-reply-edddf5e
    sec.1): a candidate evaluation completes iff it has
    >= validity_floor (20) finished worlds of its k (25);
    a panel STATE completes iff EVERY selected candidate
    for that state completes. A setting's completion is
    the fraction of panel states that complete. The
    candidate-level completion rate and the pooled
    finished-world share are computed and reported as
    DIAGNOSTICS only -- they are not selection inputs.
    (The three part company exactly when a few candidates
    stall just under the floor in many states: the
    candidate-level rate can clear the bar while a tenth
    or more of states still hold an incomplete candidate,
    which is the round-7 symptom the bar exists to close
    -- a decision cannot overturn unless the challenger
    completes.)
  * THIN-PRIOR rate per setting (co-report): the fraction
    of states whose PRIOR candidate does not complete --
    beside the fleet's 31.7% for B0 (different population:
    raw-trajectory roots vs the fleet teacher's own
    trajectory; a comparability check, not an identity).
  * COST per setting: per-decision wall (stat rows):
    mean / p95 / max, and the total.
  * OVERTURN co-reports: the teacher's decision rule
    (SimTeacher_DecideInner, replicated exactly: candidate
    means over finished worlds; best by strict improvement
    in ascending candidate order; paired test over shared
    finished worlds, >= floor shared, mean > margin x SE)
    applied per non-thin state under BOTH registered
    valuations of a drawn world (winner == 0, which covers
    natural draws and horizon-ended worlds alike):
    draw = 0 (outcome-scale -1; the ruling sec.3 primary)
    and 0.5 (outcome-scale 0; co-reported for continuity).
    A setting's NATIVE valuation is its pinned
    horizon_value: B0's is the 0.5 price (the fleet
    teacher's own), every +H setting's is draw = 0. The
    selection never depends on the valuation.
  * SELECTION (ruling sec.4.3; review sec.2): the cheapest
    qualifying setting -- lowest mean per-decision wall,
    ties by p95 then max -- among the +H settings whose
    state-level completion >= the registered bar (0.95).
    The horizon-less setting (B0) is the CONTROL: audited,
    read and reported like every other setting (its
    completion, its thin-prior beside the fleet's, its
    walls), but EXCLUDED from selection -- it is the fleet
    teacher as it ran, at the legacy draw price (its tuple
    carries horizon_value 0), and selecting it would
    contradict D7 and the sec.3 tie registration. If no
    +H setting qualifies: NO CALIBRATED SETTING, and the
    round stops.

Audits (any failure aborts, exit 2, before any read):
every world row and stat row must carry the setting tuple
pinned in the settings file for its pass (the driver aborts
on job/pin mismatch before evaluating; this is the second
placement of the clause-8 rule); exactly k rows per
(state, candidate); stat rows cover exactly the panel;
stat per-candidate row/finished counts agree with the
world rows; no duplicate (state, candidate, world); on
finished rows, winner == 0 iff outcome == 0 (the draw
markers must agree -- the valuation never guesses).

Usage:
  stage1_analyze.py --panel panel_jobs.jsonl \
      --settings settings_stage1.json --evals-dir DIR \
      [--json-out stage1_report.json]
World rows: DIR/evals_<setting>.jsonl; stat rows:
DIR/stats_<setting>.jsonl.
"""
import argparse
import json
import sys
from collections import defaultdict

# Determinization refusals (stage0_report.py's taxonomy):
# tallied by class, tagged REFUSAL; every other error class
# is a non-termination. For Stage 1 both kinds count simply
# as not finished; the tallies keep the classes visible.
REFUSAL_CLASSES = frozenset({
    "canary_hook_failed", "det_persist_failed",
    "det_verify_failed", "det_verify_hook_failed",
})
TUPLE_FIELDS = ("name", "hooks", "deadline_s", "horizon",
                "horizon_value", "k")


def abort(msg):
    print("ABORT: " + msg)
    sys.exit(2)


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    i = q * (len(sorted_vals) - 1)
    lo = int(i)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def tuple_eq(stamped, pinned):
    if not isinstance(stamped, dict):
        return False
    for f in TUPLE_FIELDS:
        if f not in stamped:
            return False
        if f == "name":
            if str(stamped[f]) != str(pinned[f]):
                return False
        elif f == "horizon_value":
            if float(stamped[f]) != float(pinned[f]):
                return False
        else:
            if int(stamped[f]) != int(pinned[f]):
                return False
    return True


def valued(outcome, v):
    """A finished world's outcome-scale score under draw
    valuation v: drawn worlds (outcome 0 -- natural draws
    and horizon-ended worlds alike) score v; every other
    world scores its outcome."""
    return v if outcome == 0.0 else outcome


def decide(fin, prior, selected, v, floor, margin):
    """Replicate SimTeacher_DecideInner on finished worlds.
    fin: {cand: {world: outcome}}. Returns (kind, pick):
    kind is 'thin', 'prior' (no overturn) or 'overturn'."""
    fin_prior = fin.get(prior, {})
    if len(fin_prior) < floor:
        return "thin", prior
    means = {}
    for ci in selected:
        vals = [valued(o, v) for o in fin.get(ci, {}).values()]
        means[ci] = (sum(vals) / len(vals)) if vals else None
    best = prior
    best_mean = means[prior]
    for ci in sorted(selected):
        if means.get(ci) is not None and means[ci] > best_mean:
            best_mean = means[ci]
            best = ci
    if best == prior:
        return "prior", prior
    shared = sorted(set(fin.get(best, {})) & set(fin_prior))
    if len(shared) < floor:
        return "prior", prior
    ds = [valued(fin[best][w], v) - valued(fin_prior[w], v)
          for w in shared]
    n = len(ds)
    mean_d = sum(ds) / n
    var = sum((d - mean_d) ** 2 for d in ds)
    se_d = (var / max(1, n - 1)) ** 0.5 / (n ** 0.5)
    if mean_d > margin * se_d:
        return "overturn", best
    return "prior", prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--evals-dir", required=True)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    spec = json.load(open(a.settings))
    const = spec["constants"]
    floor = int(const["validity_floor"])
    bar = float(const["completion_bar"])
    margin = float(const["margin_se"])
    fleet_ref = float(const["fleet_thin_prior_ref"])

    panel = {}
    for l in open(a.panel):
        if l.strip():
            j = json.loads(l)
            panel[str(j["snap"])] = j
    if not panel:
        abort("panel is empty")

    out = {"panel_states": len(panel), "settings": {},
           "states": []}
    table = []
    for pinned in spec["settings"]:
        name = str(pinned["name"])
        k = int(pinned["k"])
        wpath = "%s/evals_%s.jsonl" % (a.evals_dir, name)
        spath = "%s/stats_%s.jsonl" % (a.evals_dir, name)
        try:
            wrows = [json.loads(l) for l in open(wpath) if l.strip()]
        except OSError:
            abort("missing world rows for setting %s (%s)"
                  % (name, wpath))
        try:
            srows = [json.loads(l) for l in open(spath) if l.strip()]
        except OSError:
            abort("missing stat rows for setting %s (%s)"
                  % (name, spath))

        # ---- tuple audit (clause 8, second placement)
        for r in wrows:
            if not tuple_eq(r.get("setting"), pinned):
                abort("setting %s: world row for snap %s carries "
                      "tuple %r != pin %r"
                      % (name, r.get("snap"), r.get("setting"),
                         pinned))
        stats = {}
        for r in srows:
            if not tuple_eq(r.get("setting"), pinned):
                abort("setting %s: stat row for snap %s carries "
                      "tuple %r != pin %r"
                      % (name, r.get("snap"), r.get("setting"),
                         pinned))
            stats[str(r["snap"])] = r
        if set(stats) != set(panel):
            abort("setting %s: stat rows cover %d states, the "
                  "panel has %d (missing %s, extra %s)"
                  % (name, len(stats), len(panel),
                     sorted(set(panel) - set(stats))[:3],
                     sorted(set(stats) - set(panel))[:3]))

        # ---- world-row aggregation + guards
        fin = defaultdict(dict)      # (snap, cand) -> {world: outcome}
        cnt = defaultdict(int)       # (snap, cand) -> rows
        seen = set()
        err_tally = defaultdict(int)
        fallbacks = 0
        for r in wrows:
            snap = str(r.get("snap"))
            if snap not in panel:
                abort("setting %s: world row for unknown snap %s"
                      % (name, snap))
            cand = int(r["cand"])
            w = int(r["world"])
            key = (snap, cand, w)
            if key in seen:
                abort("setting %s: duplicate world row %s"
                      % (name, key))
            seen.add(key)
            cnt[(snap, cand)] += 1
            res = r.get("result")
            if not isinstance(res, dict):
                err_tally["null_result"] += 1
                continue
            if "error" in res:
                err_tally[str(res["error"])] += 1
                continue
            fallbacks += int(res.get("fallbacks") or 0)
            if int(res.get("finished") or 0) == 1:
                if "winner" not in res:
                    abort("setting %s: finished row %s lacks a "
                          "winner field; the draw test cannot "
                          "guess" % (name, key))
                outcome = float(res["outcome"])
                if (int(res["winner"]) == 0) != (outcome == 0.0):
                    abort("setting %s: finished row %s has "
                          "winner %r with outcome %r; the draw "
                          "markers disagree"
                          % (name, key, res["winner"], outcome))
                fin[(snap, cand)][w] = outcome
        for snap, j in panel.items():
            for cand in (int(c) for c in j["selected"]):
                if cnt.get((snap, cand), 0) != k:
                    abort("setting %s: world-count guard: snap "
                          "%s candidate %d has %d rows, expected "
                          "exactly %d"
                          % (name, snap, cand,
                             cnt.get((snap, cand), 0), k))

        # ---- stat cross-checks
        walls = []
        for snap, s in stats.items():
            j = panel[snap]
            if [int(c) for c in s["selected"]] != \
                    [int(c) for c in j["selected"]]:
                abort("setting %s: stat row for snap %s has a "
                      "different candidate set than the panel job"
                      % (name, snap))
            if int(s["prior_pick"]) != int(j["prior_pick"]):
                abort("setting %s: stat row for snap %s has a "
                      "different prior_pick than the panel job"
                      % (name, snap))
            walls.append(float(s["wall_ms"]) / 1000.0)
            for cand in (int(c) for c in j["selected"]):
                cf = (s.get("cand_finished") or {}).get(str(cand))
                cr = (s.get("cand_rows") or {}).get(str(cand))
                if cf is None or int(cf) != len(fin.get((snap, cand), {})):
                    abort("setting %s: stat cand_finished for "
                          "snap %s candidate %d is %r, the world "
                          "rows give %d"
                          % (name, snap, cand, cf,
                             len(fin.get((snap, cand), {}))))
                if cr is None or int(cr) != cnt.get((snap, cand), 0):
                    abort("setting %s: stat cand_rows for snap "
                          "%s candidate %d is %r, the world rows "
                          "give %d"
                          % (name, snap, cand, cr,
                             cnt.get((snap, cand), 0)))

        # ---- per-setting measures
        cand_evals = 0
        completes = 0
        states_complete = 0
        thin_states = 0
        pooled_fin = 0
        pooled_rows = 0
        ot = {-1.0: 0, 0.0: 0}
        nonthin = 0
        for snap, j in panel.items():
            prior = int(j["prior_pick"])
            selected = [int(c) for c in j["selected"]]
            fmap = {ci: fin.get((snap, ci), {}) for ci in selected}
            for ci in selected:
                cand_evals += 1
                pooled_fin += len(fmap[ci])
                pooled_rows += cnt.get((snap, ci), 0)
                if len(fmap[ci]) >= floor:
                    completes += 1
            if all(len(fmap[ci]) >= floor for ci in selected):
                states_complete += 1
            thin = len(fmap[prior]) < floor
            if thin:
                thin_states += 1
                continue
            nonthin += 1
            rec = {"setting": name, "snap": snap,
                   "game": str(j["game"]), "thin": False,
                   "prior_finished": len(fmap[prior]),
                   "means": {}}
            for ci in selected:
                rec["means"][str(ci)] = {
                    "draw0": (sum(valued(o, -1.0)
                                  for o in fmap[ci].values())
                              / len(fmap[ci])) if fmap[ci] else None,
                    "half": (sum(valued(o, 0.0)
                                 for o in fmap[ci].values())
                             / len(fmap[ci])) if fmap[ci] else None}
            for v, tag in ((-1.0, "draw0"), (0.0, "half")):
                kind, _pick = decide(fmap, prior, selected, v,
                                     floor, margin)
                rec["overturn_" + tag] = (kind == "overturn")
                if kind == "overturn":
                    ot[v] += 1
            out["states"].append(rec)
        for snap, j in panel.items():
            prior = int(j["prior_pick"])
            if len(fin.get((snap, prior), {})) < floor:
                out["states"].append(
                    {"setting": name, "snap": snap,
                     "game": str(j["game"]), "thin": True,
                     "prior_finished":
                         len(fin.get((snap, prior), {}))})

        walls_sorted = sorted(walls)
        completion = (states_complete / len(panel)) if panel else 0.0
        cand_completion = ((completes / cand_evals)
                           if cand_evals else 0.0)
        role = ("control" if int(pinned["horizon"]) == 0
                else "candidate")
        entry = {
            "tuple": {f: pinned[f] for f in TUPLE_FIELDS},
            "role": role,
            "states": len(panel),
            "states_completing": states_complete,
            "completion": completion,
            "candidate_evals": cand_evals,
            "completes": completes,
            "candidate_completion": cand_completion,
            "qualifies": completion >= bar,
            "thin_prior_rate": (thin_states / len(panel)),
            "pooled_finished_share":
                (pooled_fin / pooled_rows) if pooled_rows else None,
            "wall_s": {"mean": (sum(walls) / len(walls)) if walls else None,
                       "p95": quantile(walls_sorted, 0.95),
                       "max": walls_sorted[-1] if walls_sorted else None,
                       "total": sum(walls)},
            "overturn_draw0": (ot[-1.0] / nonthin) if nonthin else None,
            "overturn_half": (ot[0.0] / nonthin) if nonthin else None,
            "nonthin_states": nonthin,
            "error_tally": {ec: n for ec, n in
                            sorted(err_tally.items(),
                                   key=lambda kv: (-kv[1], kv[0]))},
            "error_classes_tagged": {
                ec: ("REFUSAL" if ec in REFUSAL_CLASSES
                     else "unfinished")
                for ec in err_tally},
            "fallbacks": fallbacks,
        }
        out["settings"][name] = entry
        table.append((name, entry))

    # ---- selection (ruling sec.4.3): qualifying +H
    # settings only -- the control is read, never selected
    # (claude-reply-edddf5e sec.2)
    qualifiers = [(n, e) for n, e in table
                  if e["qualifies"] and e["role"] != "control"]
    qualifiers.sort(key=lambda ne: (ne[1]["wall_s"]["mean"],
                                    ne[1]["wall_s"]["p95"],
                                    ne[1]["wall_s"]["max"]))
    if qualifiers:
        sel_name, sel = qualifiers[0]
        selection = {"verdict": "CALIBRATED SETTING",
                     "setting": sel_name,
                     "completion": sel["completion"],
                     "wall_s": sel["wall_s"]}
    else:
        selection = {"verdict": "NO CALIBRATED SETTING",
                     "setting": None}
    out["selection"] = selection

    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)

    print("=== STAGE 1 CALIBRATION REPORT ===")
    print("panel: %d states; validity floor %d of k; completion "
          "bar %.2f; margin %.1f paired SE"
          % (len(panel), floor, bar, margin))
    hdr = ("%-12s %6s %6s %6s %6s %9s %9s %9s %8s %8s"
           % ("setting", "compl", "cand", "pooled", "thin",
              "mean_s", "p95_s", "max_s", "ot_d0", "ot_0.5"))
    print(hdr)
    for name, e in table:
        if e["role"] == "control":
            tag = "CONTROL (not selectable)"
        elif e["qualifies"]:
            tag = "QUALIFIES"
        else:
            tag = ""
        print("%-12s %6.4f %6.4f %6.4f %6.4f %9.2f %9.2f %9.2f "
              "%8.4f %8.4f  %s"
              % (name, e["completion"], e["candidate_completion"],
                 e["pooled_finished_share"] or 0.0,
                 e["thin_prior_rate"], e["wall_s"]["mean"],
                 e["wall_s"]["p95"], e["wall_s"]["max"],
                 e["overturn_draw0"] or 0.0,
                 e["overturn_half"] or 0.0, tag))
        if e["error_tally"]:
            print("    errors: %s" % ", ".join(
                "%s %d [%s]" % (ec, n, e["error_classes_tagged"][ec])
                for ec, n in e["error_tally"].items()))
    if "B0" in out["settings"]:
        print("B0 panel thin-prior %.4f beside the fleet's %.4f "
              "(different population -- raw-trajectory roots vs "
              "the fleet teacher's own trajectory; a comparability "
              "check, not an identity)"
              % (out["settings"]["B0"]["thin_prior_rate"], fleet_ref))
    print("completion is the per-state rate (panel states "
          "where EVERY selected candidate reached the "
          "validity floor / panel states) and IS the "
          "selection metric; the cand and pooled columns "
          "are diagnostics only. The horizon-less setting "
          "is the control: read and reported, never "
          "selectable")
    if selection["setting"]:
        print("SELECTION: CALIBRATED SETTING %s (completion "
              "%.4f; mean wall %.2f s, p95 %.2f s, max %.2f s)"
              % (selection["setting"], selection["completion"],
                 selection["wall_s"]["mean"],
                 selection["wall_s"]["p95"],
                 selection["wall_s"]["max"]))
    else:
        print("SELECTION: NO CALIBRATED SETTING -- no +H "
              "setting reached per-state completion >= %.2f; "
              "the round stops here (ruling sec.4.3)" % bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
