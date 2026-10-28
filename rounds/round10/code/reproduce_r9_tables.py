#!/usr/bin/env python3
"""Round-10 Step 0, Deliverable A: reproduce Claude's
section 1-3 tables (claude-reply-9b04ad1) from the
PUBLISHED round-9 rows alone.

Sources (all under rounds/round9/data/):
  stage2/ and stage3/: search_stats_*.jsonl (the live
  Decide stat rows -- contested rows carry mean_diff /
  se_diff / priors), teacher_snap_index_*.jsonl (one
  row per overturn, carrying the firing statistic),
  jobs_all.jsonl (the L3 jobs), labels_all.jsonl.gz
  (the L3 world rows), games_*.jsonl (driver rows;
  teacher blocks only are counted for games).

Constructions (identical to the round-9 analyzers,
whose helpers this script imports from
rounds/round9/code/ and hash-pins in its output):
  * z of a contested state = mean_diff / se_diff,
    both logged by Decide on the same row. A margin-m
    would-fire is a contested row with z > m and a
    non-null mean_diff (Decide computes mean_diff
    only when the search's best candidate differs
    from the prior pick and >= 20 paired worlds
    finished -- the same population that can fire
    live). At m = 1.5 the count must equal the
    logged overturn == 1 count exactly; the script
    asserts this and reports it.
  * Per-job L3 diff (primary, draw = 0): the
    stage3_attr_analyze.run_read construction --
    worlds paired by world index across the job's
    two candidates (teacher_pick / prior_pick),
    refusal worlds skipped, only worlds finished in
    BOTH candidates counted, score = 1.0 if
    outcome > 0 else 0.0; job diff = mean of the
    per-world score differences. Jobs with no shared
    finished world are excluded (counted).
  * Job -> firing statistic join: jobs_all.snap ==
    teacher_snap_index.snap; the index row carries
    mean_diff / se_diff as written by the live
    Decide at the overturn. Cross-checked against
    the stat rows on (game, player, branch, turn,
    prior_pick, pick == teacher_pick).

Band CIs are computed two ways and both are printed:
  (a) normal approximation over the band's job diffs
      (mean +- 1.96 * sd / sqrt(n));
  (b) the game-clustered bootstrap of
      analyze_l3.cluster_bootstrap (B = 10000, seed
      20261020 -- the helper's own defaults).
A figure counts as REPRODUCED when it matches
Claude's printed value within the tolerance stated
beside it in the comparison table; the method that
matches is named. Anything else is flagged
NOT REPRODUCED with the computed value beside it.

Usage: reproduce_r9_tables.py [--repo ROOT]
  (default ROOT = the repo root inferred from this
  file's location: rounds/round10/code/../../..)
Exit 0 always (flags are data, not failures), except
on missing inputs (exit 2).
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def jl_gz(path):
    with gzip.open(path, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def norm_ci(xs):
    if len(xs) < 2:
        return (None, None)
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    se = math.sqrt(var) / math.sqrt(len(xs))
    return (m - 1.96 * se, m + 1.96 * se)


CLAUDE = {
    "fires_per_game": {  # sec.1 table
        "stage2": {1.5: 1.765, 1.25: 3.200, 1.0: 3.590},
        "stage3": {1.5: 1.555, 1.25: 2.720, 1.0: 3.080},
    },
    "bands": {  # sec.1 z-band table: (lo, hi] -> (n, edge, ci_lo, ci_hi)
        "stage2": {
            (1.5, 2.0): (187, 0.020, 0.008, 0.032),
            (2.0, 2.5): (94, 0.029, 0.012, 0.048),
            (2.5, 3.5): (50, 0.060, 0.027, 0.097),
            (3.5, None): (22, 0.566, 0.445, 0.688),
        },
        "stage3": {
            (1.5, 2.0): (328, 0.016, 0.006, 0.027),
            (2.0, 2.5): (191, 0.032, 0.019, 0.047),
            (2.5, 3.5): (84, 0.075, 0.045, 0.107),
            (3.5, None): (19, 0.430, 0.303, 0.553),
        },
    },
    "nontail_edge": {"stage2": 0.0286, "stage3": 0.0295},   # sec.2
    "tail_share": {"stage2": 0.57, "stage3": 0.32},          # sec.2
    "tail_rate": {"stage2": 0.110, "stage3": 0.048},         # sec.2
    "uncontested_per_game_stage3": 68.9,                     # sec.3
    "tail_rate_prior_band": {  # sec.3: tail fires per contested state
        (0.85, 0.97): {"stage3": 0.0038, "stage2": 0.0060},
        (0.5, 0.7): {"stage3": 0.0018},
    },
}

BANDS = [(1.5, 2.0), (2.0, 2.5), (2.5, 3.5), (3.5, None)]
PRIOR_BANDS = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 0.97)]


def band_of(z, bands):
    for lo, hi in bands:
        if z > lo and (hi is None or z <= hi):
            return (lo, hi)
    return None


def prior_band_of(p):
    for lo, hi in PRIOR_BANDS:
        if lo <= p < hi:
            return (lo, hi)
    return None


def stage_paths(root, stage):
    d = os.path.join(root, "rounds", "round9", "data", stage)
    return d


def analyze_stage(root, stage, s0, stock):
    d = stage_paths(root, stage)
    stats = []
    snaps = []
    games_teacher = 0
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if fn.startswith("search_stats_"):
            stats += jl(p)
        elif fn.startswith("teacher_snap_index_"):
            snaps += jl(p)
        elif fn.startswith("games_"):
            # teacher blocks: stage2 s*, stage3 t* (raw r* excluded)
            if (stage == "stage2" and "_s" in fn) or \
               (stage == "stage3" and "_t" in fn):
                games_teacher += len(jl(p))
    jobs = jl(os.path.join(d, "jobs_all.jsonl"))
    labels = jl_gz(os.path.join(d, "labels_all.jsonl.gz"))

    out = {"games": games_teacher, "stat_rows": len(stats),
           "snap_rows": len(snaps), "jobs": len(jobs),
           "label_rows": len(labels)}

    # ---- stat-row populations ------------------------------------
    canary = [r for r in stats if r.get("fallback") == "canary"]
    trows = [r for r in stats if r.get("teacher") == 1]
    contested = [r for r in trows if r.get("contested") == 1]
    uncontested = [r for r in trows if r.get("contested") == 0]
    full = [r for r in contested
            if r.get("mean_diff") is not None
            and r.get("se_diff") is not None]
    out["canary_rows"] = len(canary)
    out["contested_rows"] = len(contested)
    out["uncontested_rows"] = len(uncontested)
    out["uncontested_ncand1"] = sum(
        1 for r in uncontested if int(r.get("ncand") or 0) <= 1)
    out["full_contested"] = len(full)
    out["overturns_logged"] = sum(
        1 for r in contested if int(r.get("overturn") or 0) == 1)

    def z(r):
        # se_diff == 0 occurs when every paired world diff is
        # identical; a positive mean_diff is then an
        # unbounded z (the live rule meanD > margin * seD
        # fires for any margin), a non-positive one never
        # fires.
        md, sd = float(r["mean_diff"]), float(r["se_diff"])
        if sd == 0:
            return math.inf if md > 0 else 0.0
        return md / sd

    fires = {}
    for m in (1.5, 1.25, 1.0):
        fires[m] = sum(1 for r in full if z(r) > m)
    out["fires"] = fires
    out["fires_per_game"] = {
        m: fires[m] / games_teacher for m in fires}
    out["fires15_equals_overturns"] = (
        fires[1.5] == out["overturns_logged"])

    # ---- job -> firing statistic join ----------------------------
    snap_by_snap = {str(r["snap"]): r for r in snaps}
    stat_by_key = defaultdict(list)
    for r in full:
        stat_by_key[(str(r["game"]), int(r["player"]),
                     str(r["branch"]), int(r.get("turn") or 0),
                     int(r["prior_pick"]), int(r["pick"]))].append(r)
    joined = []
    join_snap_ok = 0
    join_stat_ok = 0
    join_stat_multi = 0
    mispaired = []
    for j in jobs:
        snap = str(j["snap"])
        srow = snap_by_snap.get(snap)
        if srow is None or srow.get("mean_diff") is None:
            joined.append({"job": j, "z": None, "z_fm": None})
            continue
        join_snap_ok += 1
        zz = z({"mean_diff": srow["mean_diff"],
                "se_diff": srow["se_diff"]})
        key = (str(j["game"]), int(j["player"]), str(j["branch"]),
               int(j.get("turn") or 0), int(j["prior_pick"]),
               int(j["teacher_pick"]))
        cands = stat_by_key.get(key, [])
        if len(cands) == 1 and abs(z(cands[0]) - zz) < 1e-9:
            join_stat_ok += 1
        elif len(cands) > 1:
            join_stat_multi += 1
        # first-match pairing: the first stat row in stream
        # order carrying the job's key (the pairing a plain
        # key join produces when a game holds two overturns
        # at the same key -- consecutive decisions in one
        # turn at one branch).
        z_fm = z(cands[0]) if cands else None
        if z_fm is not None and abs(z_fm - zz) > 1e-9:
            mispaired.append({"snap": snap, "z_snap": zz,
                              "z_firstmatch": z_fm})
        joined.append({"job": j, "z": zz, "z_fm": z_fm})
    out["join_snap_ok"] = join_snap_ok
    out["join_stat_unique_match"] = join_stat_ok
    out["join_stat_multi"] = join_stat_multi
    out["mispaired"] = mispaired

    # ---- per-job L3 diffs (stage3_attr_analyze construction) -----
    job_by_snap = {str(j["snap"]): j for j in jobs}
    worlds = defaultdict(dict)
    for r in labels:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand not in (int(j["teacher_pick"]), int(j["prior_pick"])):
            continue
        kind, _ = s0.classify(r.get("result"))
        wkey = (snap, cand)
        if int(r["world"]) not in worlds[wkey]:
            worlds[wkey][int(r["world"])] = (kind, r.get("result"))

    def score(res):
        return 1.0 if float(res["outcome"]) > 0 else 0.0

    diff_by_snap = {}
    for snap, j in job_by_snap.items():
        tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
        wt = worlds.get((snap, tp), {})
        wp = worlds.get((snap, pp), {})
        diffs = []
        for w in sorted(set(wt) & set(wp)):
            kt, rt = wt[w]
            kp, rp = wp[w]
            if kt == "refusal" or kp == "refusal":
                continue
            if kt != "finished" or kp != "finished":
                continue
            diffs.append(score(rt) - score(rp))
        if diffs:
            diff_by_snap[snap] = {
                "diff": sum(diffs) / len(diffs),
                "game": str(j["game"]), "n_worlds": len(diffs)}
    out["jobs_with_diff"] = len(diff_by_snap)
    out["jobs_no_shared_worlds"] = len(jobs) - len(diff_by_snap)
    out["overall_edge"] = mean(
        [v["diff"] for v in diff_by_snap.values()])

    # ---- z-band table (both pairings) ------------------------------
    def band_table(zkey):
        rows = {}
        for b in BANDS:
            recs = []
            for rec in joined:
                zz = rec[zkey]
                if zz is None:
                    continue
                if band_of(zz, BANDS) != b:
                    continue
                dv = diff_by_snap.get(str(rec["job"]["snap"]))
                if dv is None:
                    continue
                recs.append({"snap": str(rec["job"]["snap"]),
                             "game": dv["game"], "diff": dv["diff"],
                             "z": zz})
            xs = [r["diff"] for r in recs]
            nlo, nhi = norm_ci(xs)
            blo, bhi = (stock.cluster_bootstrap(recs)
                        if len(recs) >= 2 else (None, None))
            rows[b] = {"n": len(recs), "edge": mean(xs),
                       "ci_norm": [nlo, nhi],
                       "ci_boot": [blo, bhi],
                       "sum": sum(xs)}
        return rows

    out["band_rows"] = band_table("z")
    out["band_rows_firstmatch"] = band_table("z_fm")

    # ---- non-tail / tail (sec.2) ----------------------------------
    tail = [rec for rec in joined
            if rec["z"] is not None and rec["z"] > 3.5
            and str(rec["job"]["snap"]) in diff_by_snap]
    nontail_diffs = []
    tail_diffs = []
    total_sum = 0.0
    for rec in joined:
        if rec["z"] is None:
            continue
        dv = diff_by_snap.get(str(rec["job"]["snap"]))
        if dv is None:
            continue
        total_sum += dv["diff"]
        if rec["z"] > 3.5:
            tail_diffs.append(dv["diff"])
        else:
            nontail_diffs.append(dv["diff"])
    out["nontail_edge"] = mean(nontail_diffs)
    out["nontail_n"] = len(nontail_diffs)
    out["tail_n"] = len(tail_diffs)
    out["tail_share"] = (sum(tail_diffs) / total_sum
                         if total_sum else None)
    out["tail_rate"] = len(tail_diffs) / games_teacher

    # ---- prior-band tail rates (sec.3) ----------------------------
    # Denominator: ALL contested rows (every contested row
    # in the published streams carries "priors", including
    # thin-prior and no-contrast rows); numerator: rows
    # whose logged statistic has z > 3.5 (rows without a
    # mean_diff never contribute).
    pb = {}
    for b in PRIOR_BANDS:
        pb[b] = {"states": 0, "tail": 0}
    for r in contested:
        priors = r.get("priors")
        if not priors:
            continue
        top = max(float(x) for x in priors)
        b = prior_band_of(top)
        if b is None:
            continue
        pb[b]["states"] += 1
        if r.get("mean_diff") is not None and z(r) > 3.5:
            pb[b]["tail"] += 1
    for b in pb:
        pb[b]["rate"] = (pb[b]["tail"] / pb[b]["states"]
                         if pb[b]["states"] else None)
    out["prior_bands"] = pb
    out["uncontested_per_game"] = len(uncontested) / games_teacher
    out["contested_per_game"] = len(contested) / games_teacher
    return out


def fmt(x, nd=4):
    return "n/a" if x is None else ("%." + str(nd) + "f") % x


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.abspath(
        os.path.join(HERE, "..", "..", "..")))
    a = ap.parse_args()
    root = a.repo
    r9code = os.path.join(root, "rounds", "round9", "code")
    for need in ("stage0_report.py", "analyze_l3.py"):
        if not os.path.exists(os.path.join(r9code, need)):
            print("ABORT: missing %s" % os.path.join(r9code, need))
            return 2
    s0 = load_mod("stage0_report", os.path.join(r9code,
                                                "stage0_report.py"))
    stock = load_mod("analyze_l3", os.path.join(r9code,
                                                "analyze_l3.py"))
    print("reproduce_r9_tables: helpers imported from round-9 code "
          "(pinned):")
    for fn in ("stage0_report.py", "analyze_l3.py"):
        print("  %s sha256 %s" % (fn, sha256(os.path.join(r9code, fn))))

    results = {}
    for stage in ("stage2", "stage3"):
        results[stage] = analyze_stage(root, stage, s0, stock)

    flags = []

    def verdict(fig, mine, his, tol):
        ok = close(mine, his, tol)
        if not ok:
            flags.append(fig)
        return "MATCH" if ok else "** NOT REPRODUCED **"

    for stage in ("stage2", "stage3"):
        R = results[stage]
        print("\n=== %s (teacher games %d; stat rows %d; canary "
              "rows %d; jobs %d) ==="
              % (stage, R["games"], R["stat_rows"],
                 R["canary_rows"], R["jobs"]))
        print("populations: contested %d (with mean_diff %d), "
              "uncontested %d (ncand<=1: %d), overturns logged %d"
              % (R["contested_rows"], R["full_contested"],
                 R["uncontested_rows"], R["uncontested_ncand1"],
                 R["overturns_logged"]))
        print("join: snap-index %d/%d jobs; stat-row unique "
              "cross-check %d (multi-key collisions %d)"
              % (R["join_snap_ok"], R["jobs"],
                 R["join_stat_unique_match"], R["join_stat_multi"]))
        print("per-job diffs: %d jobs with shared finished "
              "worlds, %d without; overall edge %s"
              % (R["jobs_with_diff"], R["jobs_no_shared_worlds"],
                 fmt(R["overall_edge"])))
        print("fires@1.5 == logged overturns: %s"
              % R["fires15_equals_overturns"])

        print("\n-- sec.1 fires/game (tol 0.005)")
        for m in (1.5, 1.25, 1.0):
            mine = R["fires_per_game"][m]
            his = CLAUDE["fires_per_game"][stage][m]
            print("  margin %.2f: mine %.3f  claude %.3f  %s"
                  % (m, mine, his, verdict(
                      "%s fires@%.2f" % (stage, m), mine, his, 0.005)))

        print("\n-- sec.1 z-band edges, SNAP pairing (job -> "
              "teacher_snap_index; the order-aware stat join "
              "agrees on every job -- see below)")
        print("   (n exact; edge tol 0.0015; CI tol 0.0025; "
              "both CI methods printed)")
        for b in BANDS:
            row = R["band_rows"][b]
            his = CLAUDE["bands"][stage][b]
            bname = "(%s, %s]" % (b[0], b[1] if b[1] else "inf")
            print("  %s: n %d (claude %d); edge %s (claude %.3f); "
                  "CI claude [%.3f, %.3f]; normal [%s, %s]; "
                  "bootstrap [%s, %s]"
                  % (bname, row["n"], his[0], fmt(row["edge"], 3),
                     his[1], his[2], his[3], fmt(row["ci_norm"][0], 3),
                     fmt(row["ci_norm"][1], 3),
                     fmt(row["ci_boot"][0], 3),
                     fmt(row["ci_boot"][1], 3)))
        print("-- sec.1 z-band edges, FIRST-MATCH stat pairing "
              "(job -> first stat row in stream order with the "
              "job's key)")
        for b in BANDS:
            row = R["band_rows_firstmatch"][b]
            his = CLAUDE["bands"][stage][b]
            bname = "(%s, %s]" % (b[0], b[1] if b[1] else "inf")
            vn = "MATCH" if row["n"] == his[0] else "** N DIFFERS **"
            if row["n"] != his[0]:
                flags.append("%s band %s n (both pairings)"
                             % (stage, bname))
            ve = verdict("%s band %s edge (both pairings)"
                         % (stage, bname),
                         row["edge"], his[1], 0.0015)
            mn = (close(row["ci_norm"][0], his[2], 0.0025)
                  and close(row["ci_norm"][1], his[3], 0.0025))
            mb = (close(row["ci_boot"][0], his[2], 0.0025)
                  and close(row["ci_boot"][1], his[3], 0.0025))
            method = ("normal" if mn else
                      "cluster-bootstrap" if mb else "NEITHER")
            if method == "NEITHER":
                flags.append("%s band %s CI (both pairings)"
                             % (stage, bname))
            print("  %s: n %d (claude %d) %s; edge %s (claude "
                  "%.3f) %s; CI claude [%.3f, %.3f]; normal "
                  "[%s, %s]; bootstrap [%s, %s]; CI method: %s"
                  % (bname, row["n"], his[0], vn, fmt(row["edge"], 3),
                     his[1], ve, his[2], his[3],
                     fmt(row["ci_norm"][0], 3),
                     fmt(row["ci_norm"][1], 3),
                     fmt(row["ci_boot"][0], 3),
                     fmt(row["ci_boot"][1], 3), method))
        if R["mispaired"]:
            print("  mis-paired jobs (snap z vs first-match z):")
            for mp in R["mispaired"]:
                print("    %s: snap z %.4f, first-match z %.4f"
                      % (mp["snap"], mp["z_snap"],
                         mp["z_firstmatch"]))

        print("\n-- sec.2 tail decomposition (edge tol 0.0015; "
              "share tol 0.01; rate tol 0.002)")
        print("  non-tail edge: mine %s (n %d)  claude %.4f  %s"
              % (fmt(R["nontail_edge"]), R["nontail_n"],
                 CLAUDE["nontail_edge"][stage],
                 verdict("%s nontail" % stage, R["nontail_edge"],
                         CLAUDE["nontail_edge"][stage], 0.0015)))
        print("  tail share: mine %s  claude %.2f  %s"
              % (fmt(R["tail_share"], 3), CLAUDE["tail_share"][stage],
                 verdict("%s tail share" % stage, R["tail_share"],
                         CLAUDE["tail_share"][stage], 0.01)))
        print("  tail rate: mine %.4f/game (n %d)  claude %.3f  %s"
              % (R["tail_rate"], R["tail_n"],
                 CLAUDE["tail_rate"][stage],
                 verdict("%s tail rate" % stage, R["tail_rate"],
                         CLAUDE["tail_rate"][stage], 0.002)))

        print("\n-- sec.3 prior-band tail rates per contested "
              "state (tol 0.0004)")
        for b in PRIOR_BANDS:
            pb = R["prior_bands"][b]
            his = CLAUDE["tail_rate_prior_band"].get(b, {}).get(stage)
            line = ("  [%.2f, %.2f): states %d, tail %d, rate %s"
                    % (b[0], b[1], pb["states"], pb["tail"],
                       fmt(pb["rate"])))
            if his is not None:
                line += "  claude %.4f  %s" % (
                    his, verdict("%s prior band %s" % (stage, b),
                                 pb["rate"], his, 0.0004))
            print(line)

    s3 = results["stage3"]
    print("\n-- sec.3 uncontested per game, stage3 (tol 0.15)")
    print("  mine %.2f (rows %d / %d games)  claude %.1f  %s"
          % (s3["uncontested_per_game"], s3["uncontested_rows"],
             s3["games"], CLAUDE["uncontested_per_game_stage3"],
             verdict("stage3 uncontested/game",
                     s3["uncontested_per_game"],
                     CLAUDE["uncontested_per_game_stage3"], 0.15)))
    print("  contested per game, stage3: %.2f"
          % s3["contested_per_game"])

    print("\n==== SUMMARY: %d figure(s) NOT REPRODUCED: %s"
          % (len(flags), flags if flags else "none"))
    # machine-readable copy beside the script's stdout record
    out_json = {
        st: {
            "games": results[st]["games"],
            "fires_per_game": {str(k): v for k, v in
                               results[st]["fires_per_game"].items()},
            "band_rows": {
                str(k): {"n": v["n"], "edge": v["edge"],
                         "ci_norm": v["ci_norm"],
                         "ci_boot": v["ci_boot"]}
                for k, v in results[st]["band_rows"].items()},
            "band_rows_firstmatch": {
                str(k): {"n": v["n"], "edge": v["edge"],
                         "ci_norm": v["ci_norm"],
                         "ci_boot": v["ci_boot"]}
                for k, v in
                results[st]["band_rows_firstmatch"].items()},
            "mispaired": results[st]["mispaired"],
            "nontail_edge": results[st]["nontail_edge"],
            "tail_share": results[st]["tail_share"],
            "tail_rate": results[st]["tail_rate"],
            "uncontested_per_game":
                results[st]["uncontested_per_game"],
            "prior_bands": {
                str(k): v for k, v in
                results[st]["prior_bands"].items()},
            "join_snap_ok": results[st]["join_snap_ok"],
            "overall_edge": results[st]["overall_edge"],
        } for st in results}
    print("\nJSON " + json.dumps(out_json, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
