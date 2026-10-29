#!/usr/bin/env python3
"""Fixture: the sec.14 cap-aligned eval rescoring
(code/capalign_eval.py) and its published outputs
(data/step0_capalign/), checked against the
published attempt-3 rows they were computed from.

C1 STRICT JSON: every output parses with a parser
that REJECTS the bare Infinity / NaN tokens (the
fix-pass-4 discipline -- the published jobs file's
own ten bare-Infinity lines are the standing
counterexample).
C2 INDEPENDENT RECOMPUTATION: three states are
rescored from data/step0/evals_all.jsonl.gz by
this fixture's own small implementation of the
sec.3.2 rule (written from the rule, not imported):
540261752_t64 (cap-aligned z 13.2665, stays
uncontested), 540261752_t66 (z exactly 1.0, drops
out), 540261752_t73 (no contrast cap-aligned --
the search pick's mean no longer beats the prior's
once its post-cap wins price as draws).
C3 THE TEN recovered-game jobs: t64 / t65 stay
uncontested; t66-t73 are drop-outs; t64 / t65 are
not.
C4 STRUCTURE: the transition matrix sums to the
5,253 states; firing counts at 1.5/1.25/1.0 match
a recount from capalign_states.jsonl; the
cap-aligned class totals match the matrix
(uncontested 305, diag 226, band 94); the summary's
embedded as-run block equals the published
eval_summary.json; the classes map agrees with the
states file on every snap.
C5 SUPPLEMENTARY JOBS: 69 jobs, disjoint from the
attempt-3 job set, each carrying its state's
cap-aligned class and search pick, strict JSON,
selected = sorted {prior, teacher}; the seed span
at 69 jobs tops at 478,390,718 (the clearance
against every family is fx_seed_clearance's case).
"""
import gzip
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.join(HERE, "..")
STEP0 = os.path.join(R10, "data", "step0")
OUT = os.path.join(R10, "data", "step0_capalign")
FAILED = []


def check(name, cond, extra=""):
    print("%s %s%s" % ("PASS" if cond else "FAIL", name,
                       (" -- " + extra) if extra else ""))
    if not cond:
        FAILED.append(name)


def strict_loads(s):
    def bad(x):
        raise ValueError("bare token %s" % x)
    return json.loads(s, parse_constant=bad)


def rescore(snap):
    """The fixture's own cap-aligned statistic for
    one state, from the published rows."""
    ej = None
    for l in open(os.path.join(STEP0, "eval_jobs.jsonl")):
        j = json.loads(l)
        if j["snap"] == snap:
            ej = j
            break
    sel = [int(x) for x in ej["selected"]]
    pp = int(ej["prior_pick"])
    worlds = {}
    with gzip.open(os.path.join(
            STEP0, "evals_all.jsonl.gz"), "rt") as fh:
        for l in fh:
            r = json.loads(l)
            if str(r.get("snap")) != snap:
                continue
            res = r.get("result") or {}
            if int(res.get("finished") or 0) != 1:
                continue
            oc = float(res["outcome"])
            if int(res.get("winner") or 0) == 0 \
                    or int(res.get("turns") or 0) > 61:
                oc = -1.0
            worlds.setdefault(int(r["cand"]), {})[
                int(r["world"])] = oc
    priced = {c: worlds.get(c, {}) for c in sel}
    if len(priced[pp]) < 20:
        return {"status": "thin_prior", "z": None}
    means = {c: sum(v.values()) / len(v)
             for c, v in priced.items() if v}
    best = pp
    for c in sel:
        if means.get(c) is not None and means[c] > means[best]:
            best = c
    if best == pp:
        return {"status": "no_contrast", "z": None}
    shared = sorted(set(priced[best]) & set(priced[pp]))
    if len(shared) < 20:
        return {"status": "insufficient", "z": None}
    ds = [priced[best][w] - priced[pp][w] for w in shared]
    md = sum(ds) / len(ds)
    var = sum((x - md) ** 2 for x in ds) / (len(ds) - 1)
    se = math.sqrt(var) / math.sqrt(len(ds))
    z = (math.inf if md > 0 else 0.0) if se == 0 else md / se
    return {"status": "ok", "z": z, "search_pick": best}


def main():
    # ---- C1: strict JSON everywhere ----------------
    ok = True
    for fn in ("capalign_summary.json",
               "capalign_classes.json",
               "capalign_reclassification.json",
               "supplementary_jobs_report.json"):
        try:
            strict_loads(open(os.path.join(OUT, fn)).read())
        except ValueError:
            ok = False
    for fn in ("capalign_states.jsonl",
               "supplementary_jobs.jsonl"):
        for l in open(os.path.join(OUT, fn)):
            if l.strip():
                try:
                    strict_loads(l)
                except ValueError:
                    ok = False
    check("C1: every capalign output is strict JSON "
          "(no bare Infinity / NaN tokens)", ok)

    states = {}
    for l in open(os.path.join(OUT, "capalign_states.jsonl")):
        r = strict_loads(l)
        states[r["snap"]] = r
    recl = strict_loads(open(os.path.join(
        OUT, "capalign_reclassification.json")).read())
    classes = strict_loads(open(os.path.join(
        OUT, "capalign_classes.json")).read())
    summary = strict_loads(open(os.path.join(
        OUT, "capalign_summary.json")).read())
    supp = [strict_loads(l) for l in open(os.path.join(
        OUT, "supplementary_jobs.jsonl")) if l.strip()]
    jobs_all = set()
    for l in open(os.path.join(STEP0, "jobs_all.jsonl")):
        if l.strip():
            jobs_all.add(json.loads(l)["snap"])

    # ---- C2: independent recomputation -------------
    r64 = rescore("540261752_t64")
    check("C2: t64 recomputed cap-aligned z = "
          "13.2665 (search pick still wins on its "
          "by-61 worlds)",
          r64["status"] == "ok"
          and abs(r64["z"] - 13.2664991614216) < 1e-6,
          "z %s" % r64.get("z"))
    r66 = rescore("540261752_t66")
    check("C2: t66 recomputed cap-aligned z = 1.0 "
          "exactly (one by-61 win of 25 cannot hold "
          "any class)",
          r66["status"] == "ok" and abs(r66["z"] - 1.0) < 1e-9,
          "z %s" % r66.get("z"))
    r73 = rescore("540261752_t73")
    check("C2: t73 recomputed: no contrast "
          "cap-aligned (its wins were all post-cap)",
          r73["status"] == "no_contrast",
          "status %s" % r73["status"])
    check("C2: the pipeline's states file agrees on "
          "all three",
          abs(states["540261752_t64"]["cap_aligned"]["z"]
              - 13.2664991614216) < 1e-6
          and abs(states["540261752_t66"]["cap_aligned"]["z"]
                  - 1.0) < 1e-9
          and states["540261752_t73"]["cap_aligned"]["z"]
          is None)

    # ---- C3: the ten --------------------------------
    drops = {d["snap"] for d in recl["dropouts"]}
    ten = {"540261752_t%d" % t for t in range(64, 74)}
    check("C3: of the ten recovered-game jobs, t66-t73 "
          "drop out and t64/t65 stay uncontested",
          ten - {"540261752_t64", "540261752_t65"} <= drops
          and "540261752_t64" not in drops
          and "540261752_t65" not in drops
          and states["540261752_t64"]["cap_aligned"]
          ["class"] == "uncontested"
          and states["540261752_t65"]["cap_aligned"]
          ["class"] == "uncontested")

    # ---- C4: structure ------------------------------
    matrix = recl["transition_matrix"]
    check("C4: transition matrix sums to 5,253 states",
          sum(matrix.values()) == 5253
          and len(states) == 5253)
    totals = Counter(r["cap_aligned"]["class"]
                     for r in states.values())
    check("C4: cap-aligned class totals: uncontested "
          "305, diag 230, contested_band 94, none 4624",
          totals["uncontested"] == 305
          and totals["uncontested_diag"] == 230
          and totals["contested_band"] == 94
          and totals[None] == 4624,
          str(dict(totals)))
    for m, want in (("1.5", (448, 424)),
                    ("1.25", (697, 673)),
                    ("1.0", (799, 780))):
        fc = recl["firing_changes"][m]
        recount_a = sum(1 for r in states.values()
                        if r["as_run"]["would_fire"][m])
        recount_c = sum(1 for r in states.values()
                        if r["cap_aligned"]["would_fire"][m])
        check("C4: would-fire @%s as-run %d -> "
              "cap-aligned %d, recounted from the "
              "states file" % (m, want[0], want[1]),
              (fc["as_run"], fc["cap_aligned"]) == want
              and (recount_a, recount_c) == want)
    pub_summary = json.load(open(os.path.join(
        STEP0, "eval_summary.json")))
    check("C4: the summary's embedded as-run block is "
          "the published eval summary, and its "
          "cap-aligned would-fire counts match the "
          "states recount",
          summary["as_run"] == pub_summary
          and summary["scoring"] == "cap_aligned"
          and summary["all"]["would_fire"]["1.5"] == 424
          and summary["uncontested"]["would_fire"]["1.5"]
          == sum(1 for r in states.values()
                 if r["uncontested"] == 1
                 and r["cap_aligned"]["would_fire"]["1.5"]))
    check("C4: the classes map agrees with the states "
          "file on every snap",
          all(classes[s] == r["cap_aligned"]["class"]
              for s, r in states.items())
          and len(classes) == 5253)
    check("C4: drop-outs 86, newly qualifying 69 "
          "(8 uncontested / 32 diag / 29 band), "
          "regrouped 39",
          recl["dropout_count"] == 86
          and recl["newly_qualifying_count"] == 69
          and recl["newly_by_class"] == {
              "uncontested": 8, "uncontested_diag": 32,
              "contested_band": 29}
          and len(recl["regrouped_jobs"]) == 39)

    # ---- C5: supplementary jobs ----------------------
    check("C5: 69 supplementary jobs, disjoint from "
          "the attempt-3 job set, each carrying its "
          "state's cap-aligned class + search pick",
          len(supp) == 69
          and not ({j["snap"] for j in supp} & jobs_all)
          and all(
              j["probe_band"]
              == states[j["snap"]]["cap_aligned"]["class"]
              and j["teacher_pick"]
              == states[j["snap"]]["cap_aligned"]
              ["search_pick"]
              and j["selected"] == sorted(
                  {j["prior_pick"], j["teacher_pick"]})
              for j in supp))
    check("C5: seed span at 69 jobs tops at "
          "478,390,718",
          470055001 + 68 * 100003 + 49 * 31337
          == 478390718)

    print("fx_capalign: %s"
          % ("ALL PASS" if not FAILED else
             "FAILURES %s" % FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
