#!/usr/bin/env python3
"""Round-10 Step 0 probe, sec.14: CAP-ALIGNED eval
rescoring, computed from the PUBLISHED attempt-3 rows
only (claude-reply-28c2065 sec.3.1-3.2).

The registered cap-aligned rule: a finished world is
DECISIVE only if it ended by turn 61 (the live
instrument's cap trigger is currentTurn 62 --
play_game.php scores the game a draw the moment
currentTurn reaches 62, so turn 61 is the last
decisive turn). Every other finished world scores
as a horizon draw: priced at horizon_value (-1) in
the eval's paired statistic, exactly as a
horizon-flagged world already is. Worlds the engine
flagged (winner == 0) price as before; unfinished /
refusal rows are excluded as before.

The statistic is probe_eval_analyze.py's, mirrored
line for line (Decide's pricing, the >= 20 finished
prior floor, paired diffs over worlds finished in
both candidates, se == 0 -> z = +inf): the ONLY
change is the pricing of a finished world whose
winner != 0 and whose recorded turns > 61. Before
any cap-aligned number is emitted, the as-run
recomputation is VERIFIED against the published
eval_states.jsonl (every state's status, search
pick, paired count and z must reproduce; a mismatch
aborts -- the mirror is wrong, not the data).

Outputs (all under --out-dir):
  capalign_states.jsonl   per state: the as-run and
    cap-aligned statistics side by side, would-fire
    at the settings margins under both, and the
    label class under both (build_probe_jobs'
    classes, mirrored). Strict JSON throughout: a
    non-finite z is written as the 999.0 sentinel
    with a z_nonfinite flag (the fix-pass-4
    discipline), never a bare Infinity token.
  capalign_summary.json   eval_summary.json's shape
    computed on the cap-aligned states, plus
    "scoring": "cap_aligned" and the published
    as-run summary embedded verbatim under "as_run".
  capalign_classes.json   {snap: class or null}
    under the cap-aligned scoring -- the mapping the
    sec.14 read (probe_label_analyze --capalign
    -classes) groups label rows by.
  capalign_reclassification.json / .txt
    the class-transition matrix (as-run class ->
    cap-aligned class, nulls included); the
    DROP-OUTS (attempt-3 label jobs whose states no
    longer qualify under cap-aligned scoring --
    excluded from the cap-aligned read, listed in
    the recovery manifest); the NEWLY QUALIFYING
    states (a cap-aligned class, no attempt-3 label
    job -- they need supplementary labeling).
  supplementary_jobs.jsonl + _report.json
    label jobs for the newly qualifying states,
    built exactly as build_probe_jobs builds them
    (same shape, same sentinel discipline, same
    shard assignment and cap), carrying the
    CAP-ALIGNED z and search pick. The recovery
    labels them under the fresh seed family based
    at 470,055,001 (sec.14; see fx_seed_clearance).

Usage: capalign_eval.py
  --jobs data/step0/eval_jobs.jsonl
  --rows data/step0/evals_all.jsonl.gz
  --states-published data/step0/eval_states.jsonl
  --summary-published data/step0/eval_summary.json
  --label-jobs data/step0/jobs_all.jsonl
  --settings code/settings_probe.json
  --out-dir data/step0_capalign
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
Z_NONFINITE_SENTINEL = 999.0
CAP_LAST_DECISIVE_TURN = 61


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prior_band(top, bands):
    for lo, hi in bands:
        if lo <= top < hi:
            return [lo, hi]
    return None


def classify(uncontested, z, unc_margin, diag_margin,
             lo, hi):
    """build_probe_jobs' classes, mirrored exactly."""
    if z is None:
        return None
    if uncontested == 1 and z > unc_margin:
        return "uncontested"
    if uncontested == 1 and diag_margin < z <= unc_margin:
        return "uncontested_diag"
    if uncontested == 0 and lo < z <= hi:
        return "contested_band"
    return None


def state_statistic(j, worlds, s0, hval, cap_aligned):
    """probe_eval_analyze's per-state statistic with
    one pricing switch. Returns the rec fields."""
    sel = [int(x) for x in j["selected"]]
    pp = int(j["prior_pick"])
    priced = {}
    diag = {}
    for ci in sel:
        vals = {}
        errs = Counter()
        for w, (kind, res) in worlds.get(
                (str(j["snap"]), ci), {}).items():
            if kind == "finished":
                oc = float(res["outcome"])
                wn = res.get("winner")
                if wn is not None and int(wn) == 0:
                    oc = hval
                elif (cap_aligned and wn is not None
                      and int(res.get("turns") or 0)
                      > CAP_LAST_DECISIVE_TURN):
                    # the sec.14 rule: a decisive world
                    # ending after turn 61 is a horizon
                    # draw under the live instrument
                    oc = hval
                vals[w] = oc
            else:
                errs[kind] += 1
        priced[ci] = vals
        diag[ci] = {"finished": len(vals),
                    "unfinished": errs.get("unfinished", 0),
                    "refusal": errs.get("refusal", 0)}
    rec = {"search_pick": pp, "mean_diff": None,
           "se_diff": None, "z": None, "status": "ok",
           "n_worlds_paired": 0,
           "cand_diag": {str(k): v for k, v in diag.items()}}
    if len(priced.get(pp, {})) < 20:
        rec["status"] = "thin_prior"
        return rec
    means = {ci: (sum(v.values()) / len(v) if v else None)
             for ci, v in priced.items()}
    best = pp
    for ci in sel:
        if means.get(ci) is not None and means[ci] > means[best]:
            best = ci
    rec["search_pick"] = best
    if best == pp:
        rec["status"] = "no_contrast"
        return rec
    shared = sorted(set(priced[best]) & set(priced[pp]))
    rec["n_worlds_paired"] = len(shared)
    if len(shared) < 20:
        rec["status"] = "insufficient"
        return rec
    ds = [priced[best][w] - priced[pp][w] for w in shared]
    md = sum(ds) / len(ds)
    var = sum((x - md) ** 2 for x in ds) / (len(ds) - 1)
    sd = math.sqrt(var) / math.sqrt(len(ds))
    rec["mean_diff"] = md
    rec["se_diff"] = sd
    rec["z"] = (math.inf if md > 0 else 0.0) if sd == 0 \
        else md / sd
    return rec


def z_close(a, b):
    if a is None or b is None:
        return a is b
    if math.isinf(a) or math.isinf(b):
        return math.isinf(a) and math.isinf(b) \
            and (a > 0) == (b > 0)
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def z_out(z):
    """(json-safe z, nonfinite flag) -- pass-4 sentinel."""
    if z is None:
        return None, False
    if not math.isfinite(z):
        return Z_NONFINITE_SENTINEL, True
    return z, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--states-published", required=True)
    ap.add_argument("--summary-published", required=True)
    ap.add_argument("--label-jobs", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    settings = json.load(open(a.settings))
    et = settings["eval"]["tuple"]
    hval = float(et["horizon_value"])
    margins = [float(m) for m in settings["report"]["margins"]]
    tail_z = float(settings["report"]["tail_z"])
    bands = [tuple(b) for b in settings["report"]["prior_bands"]]
    lab = settings["label"]
    label_tuple = lab["tuple"]
    unc_margin = float(lab["uncontested_margin"])
    diag_margin = float(lab["uncontested_diag_margin"])
    band_lo, band_hi = float(lab["band_lo"]), float(lab["band_hi"])
    shard_cap = int(lab["shard_cap_jobs"])
    nshard = int(lab["shards"])
    summary_pub = json.load(open(a.summary_published))
    n_games = int(summary_pub["games"])

    jobs = {}
    for l in open(a.jobs):
        if l.strip():
            j = json.loads(l)
            jobs[str(j["snap"])] = j

    worlds = defaultdict(dict)
    n_rows = 0
    opener = gzip.open if a.rows.endswith(".gz") else open
    with opener(a.rows, "rt") as fh:
        for l in fh:
            if not l.strip():
                continue
            r = json.loads(l)
            n_rows += 1
            snap = str(r.get("snap"))
            if snap not in jobs:
                continue
            kind, err = s0.classify(r.get("result"))
            key = (snap, int(r["cand"]))
            if int(r["world"]) not in worlds[key]:
                worlds[key][int(r["world"])] = (
                    kind, r.get("result"))

    published = {}
    for l in open(a.states_published):
        if l.strip():
            r = json.loads(l)
            published[str(r["snap"])] = r

    states = []
    n_mismatch = 0
    for snap in sorted(jobs):
        j = jobs[snap]
        asrun = state_statistic(j, worlds, s0, hval, False)
        pub = published.get(snap)
        if pub is None:
            print("ABORT: no published state for %s" % snap)
            return 2
        ok = (pub["status"] == asrun["status"]
              and int(pub["search_pick"]) == asrun["search_pick"]
              and int(pub["n_worlds_paired"])
              == asrun["n_worlds_paired"]
              and z_close(pub["z"], asrun["z"])
              and z_close(pub["mean_diff"], asrun["mean_diff"])
              and z_close(pub["se_diff"], asrun["se_diff"]))
        if not ok:
            n_mismatch += 1
            if n_mismatch <= 5:
                print("MISMATCH %s: published z=%s status=%s; "
                      "recomputed z=%s status=%s"
                      % (snap, pub["z"], pub["status"],
                         asrun["z"], asrun["status"]))
        cap = state_statistic(j, worlds, s0, hval, True)
        unc = int(j.get("uncontested") or 0)
        za, znf_a = z_out(asrun["z"])
        zc, znf_c = z_out(cap["z"])
        rec = {
            "snap": snap, "game": str(j["game"]),
            "player": int(j["player"]),
            "branch": str(j["branch"]),
            "turn": int(j.get("turn") or 0),
            "uncontested": unc,
            "top_prior": float(j["top_prior"]),
            "prior_band": prior_band(float(j["top_prior"]),
                                     bands),
            "ncand": len(j["cands"]),
            "selected": [int(x) for x in j["selected"]],
            "prior_pick": int(j["prior_pick"]),
            "as_run": {
                "status": asrun["status"],
                "search_pick": asrun["search_pick"],
                "mean_diff": asrun["mean_diff"],
                "se_diff": asrun["se_diff"], "z": za,
                "z_nonfinite": znf_a,
                "n_worlds_paired": asrun["n_worlds_paired"],
                "would_fire": {
                    str(m): bool(asrun["z"] is not None
                                 and asrun["z"] > m)
                    for m in margins},
                "class": classify(unc, asrun["z"], unc_margin,
                                  diag_margin, band_lo, band_hi)},
            "cap_aligned": {
                "status": cap["status"],
                "search_pick": cap["search_pick"],
                "mean_diff": cap["mean_diff"],
                "se_diff": cap["se_diff"], "z": zc,
                "z_nonfinite": znf_c,
                "n_worlds_paired": cap["n_worlds_paired"],
                "would_fire": {
                    str(m): bool(cap["z"] is not None
                                 and cap["z"] > m)
                    for m in margins},
                "class": classify(unc, cap["z"], unc_margin,
                                  diag_margin, band_lo, band_hi)},
        }
        states.append(rec)
    if n_mismatch:
        print("ABORT: the as-run mirror mismatches the "
              "published states on %d states -- the "
              "mirror is wrong, not the data" % n_mismatch)
        return 2

    os.makedirs(a.out_dir, exist_ok=True)

    def dump(obj):
        return json.dumps(obj, allow_nan=False)

    with open(os.path.join(a.out_dir,
                           "capalign_states.jsonl"), "w") as f:
        for rec in states:
            f.write(dump(rec) + "\n")

    def summarize(pop, key):
        s = {"states": len(pop),
             "with_statistic": sum(
                 1 for r in pop if r[key]["z"] is not None),
             "thin_prior": sum(
                 1 for r in pop
                 if r[key]["status"] == "thin_prior"),
             "insufficient": sum(
                 1 for r in pop
                 if r[key]["status"] == "insufficient"),
             "no_contrast": sum(
                 1 for r in pop
                 if r[key]["status"] == "no_contrast"),
             "tail": sum(
                 1 for r in pop
                 if r[key]["z"] is not None
                 and (r[key]["z_nonfinite"]
                      or r[key]["z"] > tail_z)),
             "would_fire": {}}
        for m in margins:
            s["would_fire"][str(m)] = sum(
                1 for r in pop if r[key]["would_fire"][str(m)])
        return s

    def summary_for(key):
        unc = [r for r in states if r["uncontested"] == 1]
        con = [r for r in states if r["uncontested"] == 0]
        by_band = {}
        for b in bands:
            pop = [r for r in states
                   if r["prior_band"] == [b[0], b[1]]]
            if pop:
                by_band["%s-%s" % (b[0], b[1])] = \
                    summarize(pop, key)
        band125 = [r for r in con
                   if r[key]["z"] is not None
                   and not r[key]["z_nonfinite"]
                   and band_lo < r[key]["z"] <= band_hi]
        return {
            "games": n_games, "world_rows": n_rows,
            "all": summarize(states, key),
            "uncontested": summarize(unc, key),
            "contested": summarize(con, key),
            "by_prior_band": by_band,
            "contested_band_125_150": {
                "states": len(band125),
                "per_game": len(band125) / n_games
                if n_games else None},
            "per_game": {
                "uncontested_states": len(unc) / n_games
                if n_games else None,
                "contested_states": len(con) / n_games
                if n_games else None,
                "uncontested_would_fire": {
                    str(m): summarize(unc, key)
                    ["would_fire"][str(m)] / n_games
                    if n_games else None for m in margins},
                "contested_would_fire": {
                    str(m): summarize(con, key)
                    ["would_fire"][str(m)] / n_games
                    if n_games else None for m in margins},
            },
        }

    cap_summary = summary_for("cap_aligned")
    cap_summary["scoring"] = "cap_aligned"
    cap_summary["as_run"] = summary_pub
    # probe_report's cross-check line reads this key
    # off the summary it is given; the total is the
    # published per-state walls summed.
    cap_summary["eval_wall_ms_total"] = sum(
        int(r.get("wall_ms") or 0)
        for r in published.values())
    with open(os.path.join(a.out_dir,
                           "capalign_summary.json"), "w") as f:
        f.write(json.dumps(cap_summary, indent=1,
                           allow_nan=False) + "\n")

    classes = {r["snap"]: r["cap_aligned"]["class"]
               for r in states}
    with open(os.path.join(a.out_dir,
                           "capalign_classes.json"), "w") as f:
        f.write(json.dumps(classes, indent=1, sort_keys=True,
                           allow_nan=False) + "\n")

    # ---- reclassification -------------------------------------
    label_jobs = {}
    for l in open(a.label_jobs):
        if l.strip():
            j = json.loads(l)
            label_jobs[str(j["snap"])] = j
    # mirror check: the as-run classes must reproduce
    # the attempt-3 job set exactly
    asrun_job_snaps = {r["snap"] for r in states
                       if r["as_run"]["class"] is not None}
    if asrun_job_snaps != set(label_jobs):
        print("ABORT: as-run classes reproduce %d jobs, "
              "the published job set holds %d -- mirror "
              "broken" % (len(asrun_job_snaps),
                          len(label_jobs)))
        return 2
    for snap, j in label_jobs.items():
        rec = next(r for r in states if r["snap"] == snap)
        if rec["as_run"]["class"] != j["probe_band"]:
            print("ABORT: job %s class %s != mirrored %s"
                  % (snap, j["probe_band"],
                     rec["as_run"]["class"]))
            return 2

    matrix = Counter()
    for r in states:
        matrix[(r["as_run"]["class"],
                r["cap_aligned"]["class"])] += 1
    dropouts = []
    for snap in sorted(label_jobs):
        rec = next(r for r in states if r["snap"] == snap)
        if rec["cap_aligned"]["class"] is None:
            j = label_jobs[snap]
            # the published attempt-3 jobs file is the
            # pre-fix-pass-4 writer's output: its ten
            # z = +inf lines carry the bare Infinity
            # token and no sentinel flag. Emit the
            # sentinel form here (never a bare token).
            jz, jznf = z_out(float(j["z"]))
            dropouts.append({
                "snap": snap, "game": str(j["game"]),
                "turn": int(j.get("turn") or 0),
                "as_run_class": j["probe_band"],
                "as_run_z": jz,
                "z_nonfinite": bool(j.get("z_nonfinite"))
                               or jznf,
                "cap_aligned_z": rec["cap_aligned"]["z"],
                "cap_aligned_status":
                    rec["cap_aligned"]["status"]})
    newly = [r for r in states
             if r["cap_aligned"]["class"] is not None
             and r["snap"] not in label_jobs]
    regrouped = [r["snap"] for r in states
                 if r["snap"] in label_jobs
                 and r["cap_aligned"]["class"] is not None
                 and r["cap_aligned"]["class"]
                 != r["as_run"]["class"]]

    # ---- supplementary jobs (build_probe_jobs shape) ----------
    supp = []
    for r in newly:
        snap = r["snap"]
        ej = jobs[snap]
        cap = r["cap_aligned"]
        pp, tp = int(r["prior_pick"]), int(cap["search_pick"])
        if tp == pp:
            print("ABORT: newly qualifying state %s has "
                  "search pick == prior pick" % snap)
            return 2
        job = {
            "snap_dir": ej["snap_dir"], "snap": snap,
            "game": str(r["game"]),
            "player": int(r["player"]),
            "branch": str(r["branch"]),
            "turn": int(r.get("turn") or 0),
            "cands": ej["cands"],
            "selected": sorted({pp, tp}),
            "prior_pick": pp, "teacher_pick": tp,
            "setting": label_tuple,
            "probe_band": cap["class"],
            "prior_band": r["prior_band"],
            "z": cap["z"],
            "top_prior": r["top_prior"],
        }
        if cap["z_nonfinite"]:
            job["z_nonfinite"] = True
        supp.append(job)
    supp_lines = []
    for j in supp:
        try:
            supp_lines.append(json.dumps(j, allow_nan=False))
        except ValueError:
            print("ABORT: supplementary job %s carries a "
                  "non-finite float outside the sentinel "
                  "path" % j["snap"])
            return 2
    shards = Counter()
    for j in supp:
        s = int(hashlib.sha256(
            str(j["game"]).encode()).hexdigest(),
            16) % nshard
        shards[s] += 1
    for s, n in shards.items():
        if n > shard_cap:
            print("ABORT: supplementary shard %d holds %d "
                  "jobs > the registered cap %d"
                  % (s, n, shard_cap))
            return 2
    with open(os.path.join(
            a.out_dir, "supplementary_jobs.jsonl"), "w") as f:
        for ln in supp_lines:
            f.write(ln + "\n")
    supp_report = {
        "jobs": len(supp),
        "z_nonfinite_jobs": sum(
            1 for j in supp if j.get("z_nonfinite")),
        "by_class": dict(Counter(
            j["probe_band"] for j in supp)),
        "shards": {str(k): v for k, v in sorted(shards.items())},
        "seed_family": {
            "base": 470055001, "lattice_shard": 4,
            "rule": "seedBase = 470055001 + job_index x "
                    "100,003; worlds at + w x 31,337 "
                    "(s2_label_main, unchanged)",
            "span_at_n_jobs": None},
        "label_tuple": label_tuple,
        "games": len({j["game"] for j in supp}),
        "scoring": "cap_aligned (sec.14): classes and "
                   "z from the cap-aligned rescoring",
    }
    n = len(supp)
    supp_report["seed_family"]["span_at_n_jobs"] = (
        (470055001 + (n - 1) * 100003 + 49 * 31337)
        if n else None)
    with open(os.path.join(
            a.out_dir, "supplementary_jobs_report.json"),
            "w") as f:
        f.write(json.dumps(supp_report, indent=1,
                           allow_nan=False) + "\n")

    recl = {
        "scoring_rule": "cap-aligned (sec.14): a finished "
                        "world is decisive only if it "
                        "ended by turn 61; every other "
                        "finished world prices as a "
                        "horizon draw (-1 in the paired "
                        "statistic)",
        "states": len(states),
        "as_run_verification": "the as-run recomputation "
                               "reproduced every published "
                               "eval state (status, search "
                               "pick, paired count, z) and "
                               "the attempt-3 job set "
                               "(snaps and classes) exactly",
        "transition_matrix": {
            "%s -> %s" % (a_, b_): n_
            for (a_, b_), n_ in sorted(
                matrix.items(),
                key=lambda kv: (str(kv[0][0]), str(kv[0][1])))},
        "firing_changes": {
            str(m): {
                "as_run": sum(
                    1 for r in states
                    if r["as_run"]["would_fire"][str(m)]),
                "cap_aligned": sum(
                    1 for r in states
                    if r["cap_aligned"]["would_fire"][str(m)]),
                "lost": sum(
                    1 for r in states
                    if r["as_run"]["would_fire"][str(m)]
                    and not r["cap_aligned"]
                    ["would_fire"][str(m)]),
                "gained": sum(
                    1 for r in states
                    if r["cap_aligned"]["would_fire"][str(m)]
                    and not r["as_run"]
                    ["would_fire"][str(m)])}
            for m in margins},
        "dropouts": dropouts,
        "dropout_count": len(dropouts),
        "newly_qualifying": [
            {"snap": r["snap"], "game": r["game"],
             "turn": r["turn"],
             "class": r["cap_aligned"]["class"],
             "cap_aligned_z": r["cap_aligned"]["z"],
             "z_nonfinite": r["cap_aligned"]["z_nonfinite"],
             "as_run_z": r["as_run"]["z"],
             "as_run_status": r["as_run"]["status"]}
            for r in newly],
        "newly_qualifying_count": len(newly),
        "newly_by_class": dict(Counter(
            r["cap_aligned"]["class"] for r in newly)),
        "regrouped_jobs": regrouped,
        "tail": {"as_run": summary_pub["all"]["tail"],
                 "cap_aligned": cap_summary["all"]["tail"],
                 "uncontested_as_run":
                     summary_pub["uncontested"]["tail"],
                 "uncontested_cap_aligned":
                     cap_summary["uncontested"]["tail"],
                 "contested_as_run":
                     summary_pub["contested"]["tail"],
                 "contested_cap_aligned":
                     cap_summary["contested"]["tail"]},
    }
    with open(os.path.join(
            a.out_dir, "capalign_reclassification.json"),
            "w") as f:
        f.write(json.dumps(recl, indent=1,
                           allow_nan=False) + "\n")
    lines = []
    lines.append("sec.14 cap-aligned reclassification "
                 "(from the published attempt-3 rows)")
    lines.append("rule: a finished world is decisive "
                 "only if it ended by turn 61; every "
                 "other finished world prices as a "
                 "horizon draw (-1 in the statistic).")
    lines.append("")
    lines.append("class transitions (as-run -> "
                 "cap-aligned), all %d states:"
                 % len(states))
    for (a_, b_), n_ in sorted(
            matrix.items(),
            key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        lines.append("  %-18s -> %-18s %d"
                     % (a_, b_, n_))
    lines.append("")
    for m in margins:
        fc = recl["firing_changes"][str(m)]
        lines.append("would-fire @%s: as-run %d -> "
                     "cap-aligned %d (lost %d, gained %d)"
                     % (m, fc["as_run"], fc["cap_aligned"],
                        fc["lost"], fc["gained"]))
    lines.append("")
    lines.append("DROP-OUTS: %d attempt-3 label jobs "
                 "whose states no longer qualify "
                 "cap-aligned (excluded from the "
                 "cap-aligned read):" % len(dropouts))
    for d in dropouts:
        lines.append("  %s (game %s, turn %s, was %s, "
                     "as-run z %s, cap-aligned z %s, "
                     "status %s)"
                     % (d["snap"], d["game"], d["turn"],
                        d["as_run_class"], d["as_run_z"],
                        d["cap_aligned_z"],
                        d["cap_aligned_status"]))
    lines.append("")
    lines.append("NEWLY QUALIFYING: %d states gain a "
                 "class cap-aligned and need "
                 "supplementary labeling, by class %s:"
                 % (len(newly), recl["newly_by_class"]))
    for r in newly:
        lines.append("  %s (game %s, turn %s, class %s, "
                     "cap-aligned z %s, as-run z %s)"
                     % (r["snap"], r["game"], r["turn"],
                        r["cap_aligned"]["class"],
                        r["cap_aligned"]["z"],
                        r["as_run"]["z"]))
    lines.append("")
    lines.append("REGROUPED: %d attempt-3 jobs keep a "
                 "class but change it: %s"
                 % (len(regrouped), regrouped))
    with open(os.path.join(
            a.out_dir, "capalign_reclassification.txt"),
            "w") as f:
        f.write("\n".join(lines) + "\n")
    print("capalign: %d states verified as-run; "
          "drop-outs %d; newly qualifying %d %s; "
          "regrouped %d"
          % (len(states), len(dropouts), len(newly),
             recl["newly_by_class"], len(regrouped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
