#!/usr/bin/env python3
"""Independent audit of round-9 Stage 1 analyze outputs.

Written from the registered definitions (launch package sec.2;
claude-reply-edddf5e sec.1-2), NOT from stage1_analyze.py's code.
Reads the raw rows in OUT and the analyzer's stage1_report.json,
recomputes per setting:
  (a) row counts (world rows, stat rows)
  (b) per-state completion (state completes iff EVERY selected
      candidate has >= 20 finished worlds; finished counted
      from the world rows themselves), plus candidate-level
      rate, pooled finished share, thin-prior rate as the same
      aggregates the report prints
  (c) mean / p95 / max per-decision wall from stat rows
  (d) overturn co-reports under both valuations (decide rule
      as specified: candidate means over finished worlds,
      strict-improvement best ascending, paired test over
      shared finished worlds >= 20, mean > 1.5 x paired SE
      with sample-variance SE)
and the stat cand_finished cross-check against world rows.
Prints a JSON comparison: mine vs the analyzer's.
"""
import json
import math
import sys
from collections import defaultdict

OUT = "/home/joe/tcg/r9s1_out"
FLOOR = 20
K = 25
BAR = 0.95
MARGIN = 1.5
SETTINGS = ["B0", "B0+H", "H8k-180+H", "H8k-360+H",
            "H16k-180+H", "H16k-360+H"]


def q95(vals):
    s = sorted(vals)
    i = 0.95 * (len(s) - 1)
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def val(outcome, v):
    return v if outcome == 0.0 else outcome


def decide(fin, prior, selected, v):
    fp = fin.get(prior, {})
    if len(fp) < FLOOR:
        return "thin"
    means = {}
    for ci in selected:
        vs = [val(o, v) for o in fin.get(ci, {}).values()]
        means[ci] = sum(vs) / len(vs) if vs else None
    best = prior
    bm = means[prior]
    for ci in sorted(selected):
        if means.get(ci) is not None and means[ci] > bm:
            bm = means[ci]
            best = ci
    if best == prior:
        return "prior"
    shared = sorted(set(fin.get(best, {})) & set(fp))
    if len(shared) < FLOOR:
        return "prior"
    ds = [val(fin[best][w], v) - val(fp[w], v) for w in shared]
    n = len(ds)
    md = sum(ds) / n
    var = sum((d - md) ** 2 for d in ds)
    se = math.sqrt(var / max(1, n - 1)) / math.sqrt(n)
    return "overturn" if md > MARGIN * se else "prior"


panel = {}
for l in open(OUT + "/panel_jobs.jsonl"):
    if l.strip():
        j = json.loads(l)
        panel[str(j["snap"])] = j

report = json.load(open(OUT + "/stage1_report.json"))
mine = {}
for name in SETTINGS:
    fin = defaultdict(dict)   # (snap, cand) -> {world: outcome}
    cnt = defaultdict(int)
    errs = defaultdict(int)
    nrows = 0
    for l in open("%s/evals_%s.jsonl" % (OUT, name)):
        if not l.strip():
            continue
        nrows += 1
        r = json.loads(l)
        snap = str(r["snap"])
        cand = int(r["cand"])
        w = int(r["world"])
        cnt[(snap, cand)] += 1
        res = r.get("result")
        if not isinstance(res, dict):
            errs["null_result"] += 1
            continue
        if "error" in res:
            errs[str(res["error"])] += 1
            continue
        if int(res.get("finished") or 0) == 1:
            fin[(snap, cand)][w] = float(res["outcome"])
    srows = [json.loads(l) for l in
             open("%s/stats_%s.jsonl" % (OUT, name)) if l.strip()]
    walls = [float(s["wall_ms"]) / 1000.0 for s in srows]
    # cross-check stats cand_finished vs world-row finished
    mismatch = 0
    for s in srows:
        snap = str(s["snap"])
        for cstr, cf in (s.get("cand_finished") or {}).items():
            if int(cf) != len(fin.get((snap, int(cstr)), {})):
                mismatch += 1
    states_complete = 0
    cand_evals = 0
    cand_complete = 0
    pooled_fin = 0
    pooled_rows = 0
    thin = 0
    nonthin = 0
    ot = {-1.0: 0, 0.0: 0}
    for snap, j in panel.items():
        sel = [int(c) for c in j["selected"]]
        prior = int(j["prior_pick"])
        fmap = {ci: fin.get((snap, ci), {}) for ci in sel}
        ok = True
        for ci in sel:
            cand_evals += 1
            pooled_fin += len(fmap[ci])
            pooled_rows += cnt.get((snap, ci), 0)
            if len(fmap[ci]) >= FLOOR:
                cand_complete += 1
            else:
                ok = False
        if ok:
            states_complete += 1
        if len(fmap[prior]) < FLOOR:
            thin += 1
            continue
        nonthin += 1
        for v in (-1.0, 0.0):
            if decide(fmap, prior, sel, v) == "overturn":
                ot[v] += 1
    mine[name] = {
        "evals_rows": nrows,
        "stats_rows": len(srows),
        "states_complete": states_complete,
        "completion": states_complete / len(panel),
        "candidate_completion": cand_complete / cand_evals,
        "pooled_finished_share": pooled_fin / pooled_rows,
        "thin_prior_rate": thin / len(panel),
        "wall_mean": sum(walls) / len(walls),
        "wall_p95": q95(walls),
        "wall_max": max(walls),
        "wall_total": sum(walls),
        "overturn_draw0": ot[-1.0] / nonthin,
        "overturn_half": ot[0.0] / nonthin,
        "nonthin": nonthin,
        "errors": dict(errs),
        "cand_finished_mismatches": mismatch,
    }

cmp_out = {"panel_states": len(panel), "per_setting": {}}
all_agree = True
for name in SETTINGS:
    a = report["settings"][name]
    m = mine[name]
    checks = {
        "evals_rows": (m["evals_rows"], 17025),
        "stats_rows": (m["stats_rows"], 240),
        "states_complete": (m["states_complete"],
                            a["states_completing"]),
        "completion": (m["completion"], a["completion"]),
        "candidate_completion": (m["candidate_completion"],
                                 a["candidate_completion"]),
        "pooled_finished_share": (m["pooled_finished_share"],
                                  a["pooled_finished_share"]),
        "thin_prior_rate": (m["thin_prior_rate"],
                            a["thin_prior_rate"]),
        "wall_mean": (m["wall_mean"], a["wall_s"]["mean"]),
        "wall_p95": (m["wall_p95"], a["wall_s"]["p95"]),
        "wall_max": (m["wall_max"], a["wall_s"]["max"]),
        "wall_total": (m["wall_total"], a["wall_s"]["total"]),
        "overturn_draw0": (m["overturn_draw0"], a["overturn_draw0"]),
        "overturn_half": (m["overturn_half"], a["overturn_half"]),
        "cand_finished_mismatches": (m["cand_finished_mismatches"], 0),
        "error_tally": (m["errors"], a["error_tally"]),
    }
    row = {}
    for key, (mv, av) in checks.items():
        if isinstance(mv, float) or isinstance(av, float):
            agree = abs(float(mv) - float(av)) < 1e-9
        else:
            agree = mv == av
        row[key] = {"mine": mv, "analyzer": av, "agree": agree}
        if not agree:
            all_agree = False
    cmp_out["per_setting"][name] = row
cmp_out["analyzer_selection"] = report["selection"]
qual = [(n, mine[n]) for n in SETTINGS
        if n != "B0" and mine[n]["completion"] >= BAR]
qual.sort(key=lambda ne: (ne[1]["wall_mean"], ne[1]["wall_p95"],
                          ne[1]["wall_max"]))
cmp_out["my_selection"] = ({"verdict": "CALIBRATED SETTING",
                            "setting": qual[0][0]} if qual else
                           {"verdict": "NO CALIBRATED SETTING",
                            "setting": None})
cmp_out["all_agree"] = all_agree
json.dump(cmp_out, open(OUT + "/audit_stage1.json", "w"), indent=1)
print(json.dumps({"all_agree": all_agree,
                  "my_selection": cmp_out["my_selection"],
                  "analyzer_selection": report["selection"]}))
for n in SETTINGS:
    bad = [k for k, v in cmp_out["per_setting"][n].items()
           if not v["agree"]]
    print(n, "AGREE" if not bad else "DISAGREE on %s" % bad)
