"""Round-9 Stage 3 L3 ATTRIBUTION analyzer (ruling sec.4.6).

Fork of stage2_analyze.py (the ee4daa88 state -- the FIXED
stamp audit: each label row's stamp is projected on the
settings label_tuple keys only, extras ignored). The reads
are identical in construction: PRIMARY horizon-aligned (62)
at draw = 0, co-reports at draw = 0.5 and life-differential,
over the SAME paired worlds, with the world-count guard,
the Stage 0 refusal taxonomy and coverage counter kept.

What changes is what the read is READ AGAINST:
  * the games inputs are the STAGE 3 games report's teacher
    figures: live overturns/game = games_report.
    overturns_per_game (Stage 3 teacher games),
    overturn_rows, games_completed = teacher games
    completed;
  * per_game_gain = primary mean diff x live overturns/game;
  * ratio_to_delta = per_game_gain / stage3_read.
    primary.mean_diff (the Stage 3 paired fleet delta, from
    --stage3-read), printed on the ATTRIBUTION line against
    the Fai gate references (87% and 101%); the numeric
    ratio prints ONLY when delta > 0 and its CI excludes 0:
    delta <= 0 prints "n/a (Δ ≤ 0)" and a CI including 0
    prints "unstable (Δ CI includes 0)", with delta's CI
    beside the label in both cases (claude-reply-c924b19
    sec.4);
  * verdict vocabulary: PROCEED-style bands DO NOT APPLY --
    this is a co-report, not a gate. The output header is
    "ATTRIBUTION READ" and the JSON carries an
    "attribution" field (no PROCEED/STOP verdict);
  * the tripwire machinery is RETAINED (per-game gain >
    +0.25 OR primary mean diff > +0.20 -> the L1/L2-form
    impeachment checks print BEFORE the read): it impeaches
    the attribution read itself;
  * panel/fleet co-report lines are replaced: live rates
    against the STAGE 2 record (settings stage2_reference:
    thin 0.0, overturn rate 0.0694, overturns/game 1.765)
    and the games-outcomes line reads the Stage 3 games
    report's teacher outcomes.

Usage:
  stage3_attr_analyze.py --jobs jobs_all.jsonl --labels l.jsonl
      --games-report games_report.json --stage3-read
      stage3_read.json --settings settings_stage3.json
      [--expect-rows 50] [--json-out attr_read.json]
"""
import argparse
import importlib.util
import json
import sys
from collections import defaultdict

HERE = __file__.rsplit("/", 1)[0]


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, HERE + "/" + name + ".py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def score_primary(res):
    return 1.0 if float(res["outcome"]) > 0 else 0.0


def score_draw05(res):
    return (float(res["outcome"]) + 1.0) / 2.0


def score_lifediff(res):
    if int(res.get("horizon") or 0) == 1:
        lr, lo = res.get("life_root"), res.get("life_opp")
        if lr is not None and lo is not None:
            if int(lr) > int(lo):
                return 1.0
            if int(lr) < int(lo):
                return 0.0
            return 0.0  # tied: draw at the primary's price (0)
    return score_primary(res)


SCORINGS = [("primary_draw0", score_primary),
            ("coreport_draw05", score_draw05),
            ("coreport_lifediff", score_lifediff)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--games-report", required=True)
    ap.add_argument("--stage3-read", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--expect-rows", type=int, default=50)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")
    settings = json.load(open(a.settings))
    grep = json.load(open(a.games_report))
    s3read = json.load(open(a.stage3_read))
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = []
    for path in a.labels:
        with open(path) as f:
            for l in f:
                if l.strip():
                    rows.append(json.loads(l))
    job_by_snap = {str(j["snap"]): j for j in jobs}

    # ---- label tuple audit (always, before any read) ------
    # Project each row's stamp on the registered label_tuple
    # fields ONLY (the keys of settings["label_tuple"]): the
    # label driver (s2_label_main.php) stamps exactly those
    # fields; extra keys in a stamp are ignored, a wrong value
    # or a missing field fails. (Fix: stage2-analyzer-fix.md --
    # the audit formerly demanded a seventh key, "pinned",
    # that only the LIVE path's stamps carry.)
    LT = settings["label_tuple"]
    bad_stamp = 0
    for r in rows:
        s = r.get("setting")
        if not isinstance(s, dict) or {
                k: s.get(k) for k in LT} != LT:
            bad_stamp += 1
    if bad_stamp:
        print("ABORT: %d label rows carry a setting stamp != "
              "the registered label tuple" % bad_stamp)
        return 2

    # ---- world-count guard (registered width) -------------
    pair_counts = defaultdict(int)
    for r in rows:
        if str(r.get("snap")) in job_by_snap:
            pair_counts[(str(r["snap"]), int(r["cand"]))] += 1
    for snap, j in sorted(job_by_snap.items()):
        for cand in sorted({int(j["teacher_pick"]),
                            int(j["prior_pick"])}):
            n = pair_counts.get((snap, cand), 0)
            if n != a.expect_rows:
                print("ABORT: world-count guard: job %s "
                      "candidate %d has %d rows, expected "
                      "exactly %d"
                      % (snap, cand, n, a.expect_rows))
                return 2

    # ---- per-world tables ----------------------------------
    worlds = defaultdict(dict)   # (snap, cand) -> world -> (kind, res)
    role_counts = {"teacher": defaultdict(int),
                   "prior": defaultdict(int)}
    class_tallies = {"teacher": defaultdict(int),
                     "prior": defaultdict(int)}
    fallbacks = 0
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand == int(j["teacher_pick"]):
            role = "teacher"
        elif cand == int(j["prior_pick"]):
            role = "prior"
        else:
            continue
        res = r.get("result")
        kind, err_class = s0.classify(res)
        role_counts[role]["rows"] += 1
        role_counts[role][kind] += 1
        if err_class is not None:
            class_tallies[role][err_class] += 1
        if isinstance(res, dict):
            fallbacks += int(res.get("fallbacks") or 0)
        prev = worlds[(snap, cand)].get(int(r["world"]))
        if prev is None:
            worlds[(snap, cand)][int(r["world"])] = (kind, res)

    def share(role):
        c = role_counts[role]
        denom = c["finished"] + c["unfinished"]
        return (c["unfinished"] / denom) if denom else None

    fin = sum(role_counts[r]["finished"] for r in role_counts)
    unf = sum(role_counts[r]["unfinished"] for r in role_counts)
    ref = sum(role_counts[r]["refusal"] for r in role_counts)
    sh_pool = (unf / (fin + unf)) if (fin + unf) else None
    pooled_tally = defaultdict(int)
    for role in ("teacher", "prior"):
        for ec, n in class_tallies[role].items():
            pooled_tally[ec] += n

    # ---- the three reads ------------------------------------
    def run_read(scorefn, sens=False):
        recs = []
        for snap, j in sorted(job_by_snap.items()):
            tp, pp = int(j["teacher_pick"]), int(j["prior_pick"])
            wt = worlds.get((snap, tp), {})
            wp = worlds.get((snap, pp), {})
            diffs = []
            for w in sorted(set(wt) & set(wp)):
                kt, rt = wt[w]
                kp, rp = wp[w]
                if kt == "refusal" or kp == "refusal":
                    continue
                if sens:
                    st = (score_draw05(rt) if kt == "finished"
                          else 0.5)
                    sp = (score_draw05(rp) if kp == "finished"
                          else 0.5)
                else:
                    if kt != "finished" or kp != "finished":
                        continue
                    st, sp = scorefn(rt), scorefn(rp)
                diffs.append(st - sp)
            if diffs:
                recs.append({"snap": snap,
                             "game": str(j["game"]),
                             "diff": sum(diffs) / len(diffs),
                             "n_worlds": len(diffs)})
        if not recs:
            return {"jobs": 0, "mean_diff": None, "ci": None,
                    "records": []}
        mean = sum(r["diff"] for r in recs) / len(recs)
        lo, hi = stock.cluster_bootstrap(recs)
        return {"jobs": len(recs), "mean_diff": mean,
                "ci": [lo, hi], "records": recs}

    reads = {}
    for name, fn in SCORINGS:
        r = run_read(fn)
        reads[name] = {k: r[k] for k in ("jobs", "mean_diff", "ci")}
        reads[name]["_records"] = r["records"]
    primary = reads["primary_draw0"]
    mean = primary["mean_diff"]
    lo = primary["ci"][0] if primary["ci"] else None
    jobs_no_shared = len(jobs) - primary["jobs"]

    live_opg = grep.get("overturns_per_game")
    per_game = (mean * live_opg
                if (mean is not None and live_opg is not None)
                else None)

    # ---- bands + tripwires -----------------------------------
    tripwire = None
    if mean is not None and (
            (per_game is not None and per_game > 0.25)
            or mean > 0.20):
        tripwire = {"per_game_gain": per_game, "mean_diff": mean}
    fleet_delta = (s3read.get("primary") or {}).get("mean_diff")
    fleet_ci = (s3read.get("primary") or {}).get("ci")
    # Ratio guard (claude-reply-c924b19 sec.4): a ratio over a
    # near-zero or negative denominator reads as a number when
    # it isn't one. The plain numeric ratio prints ONLY when
    # delta > 0 and its CI excludes 0; delta <= 0 prints
    # "n/a (delta <= 0)"; delta > 0 with a CI including 0
    # prints "unstable (delta CI includes 0)" -- delta's CI is
    # printed beside the label in both guarded cases.
    ratio = None
    ratio_note = None
    if per_game is not None and fleet_delta is not None:
        if fleet_delta <= 0:
            ratio_note = "n/a (Δ ≤ 0)"
        elif fleet_ci is not None and fleet_ci[0] > 0:
            ratio = per_game / fleet_delta
        else:
            ratio_note = "unstable (Δ CI includes 0)"
    ratio_str = pct(ratio)
    if ratio_note is not None:
        ratio_str = "%s, fleet Δ %s CI [%s, %s]" % (
            ratio_note, pct(fleet_delta),
            pct(fleet_ci[0]) if fleet_ci else "n/a",
            pct(fleet_ci[1]) if fleet_ci else "n/a")
    verdict = None  # attribution is a co-report, not a gate

    out = {
        "jobs_no_shared_worlds": jobs_no_shared,
        "primary": {k: primary[k] for k in ("jobs", "mean_diff",
                                            "ci")},
        "coreport_draw05": {k: reads["coreport_draw05"][k]
                            for k in ("jobs", "mean_diff", "ci")},
        "coreport_lifediff": {k: reads["coreport_lifediff"][k]
                              for k in ("jobs", "mean_diff",
                                        "ci")},
        "per_game_gain": per_game,
        "live_overturns_per_game": live_opg,
        "attribution": {"per_game_gain": per_game,
                        "l3_mean_diff": mean,
                        "live_overturns_per_game": live_opg,
                        "stage3_primary_mean_diff": fleet_delta,
                        "stage3_primary_ci": fleet_ci,
                        "ratio_to_delta": ratio,
                        "ratio_note": ratio_note},
        "tripwire": tripwire,
        "unfinished": {
            "teacher": dict(role_counts["teacher"]),
            "prior": dict(role_counts["prior"]),
            "share_teacher": share("teacher"),
            "share_prior": share("prior"),
            "share_pooled": sh_pool,
            "error_classes": {
                "teacher": dict(class_tallies["teacher"]),
                "prior": dict(class_tallies["prior"]),
                "pooled": dict(pooled_tally)}},
        "fallbacks": fallbacks,
        "label_tuple_audit": {"rows": len(rows), "bad": 0},
    }

    lines = []
    lines.append("=== STAGE 3 L3 ATTRIBUTION READ (primary: "
                 "horizon 62, draw = 0) ===")
    if tripwire is not None:
        # Impeachment BEFORE the read (registered order).
        lines.append("TRIPWIRE FIRED (per-game gain %s, mean "
                     "diff %s): L1/L2-form impeachment checks "
                     "run BEFORE the read:"
                     % (pct(per_game), pct(mean)))
        recs = primary["_records"]
        by_game = defaultdict(list)
        for r in recs:
            by_game[r["game"]].append(r)
        logo = []
        for g in sorted(by_game):
            rest = [r for r in recs if r["game"] != g]
            if rest:
                logo.append((g, sum(r["diff"] for r in rest)
                             / len(rest)))
        if logo:
            lv = [v for _, v in logo]
            lines.append("  L1 leave-one-game-out: primary "
                         "mean ranges [%s, %s] over %d games; "
                         "no single game removal flips its "
                         "sign: %s"
                         % (pct(min(lv)), pct(max(lv)),
                            len(logo),
                            "yes" if (min(lv) > 0) == (max(lv) > 0)
                            and min(lv) != 0 else "NO"))
            out["tripwire"]["logo_range"] = [min(lv), max(lv)]
        sens = run_read(score_draw05, sens=True)
        lines.append("  L2 sensitivity (unfinished worlds "
                     "priced as draws at 0.5 in score units): "
                     "mean diff %s, CI [%s, %s] over %d jobs"
                     % (pct(sens["mean_diff"]),
                        pct(sens["ci"][0]) if sens["ci"] else "n/a",
                        pct(sens["ci"][1]) if sens["ci"] else "n/a",
                        sens["jobs"]))
        out["tripwire"]["sensitivity"] = {
            "mean_diff": sens["mean_diff"], "ci": sens["ci"]}
        lines.append("  per-game table (jobs, mean diff):")
        for g in sorted(by_game):
            rs = by_game[g]
            lines.append("    game %s: %d jobs, %s"
                         % (g, len(rs),
                            pct(sum(r["diff"] for r in rs)
                                / len(rs))))
        lines.append("TRIPWIRE CHECKS COMPLETE - the read "
                     "follows.")
    p = primary
    lines.append("PRIMARY (draw = 0): jobs %d; "
                 "jobs_no_shared_worlds %d (of %d jobs); "
                 "mean paired diff %s; CI [%s, %s]"
                 % (p["jobs"], jobs_no_shared, len(jobs),
                    pct(p["mean_diff"]),
                    pct(p["ci"][0]) if p["ci"] else "n/a",
                    pct(p["ci"][1]) if p["ci"] else "n/a"))
    lines.append("  per-game gain %s (mean diff x LIVE "
                 "overturns/game %s from %d captured overturns "
                 "over %d completed teacher games)"
                 % (pct(per_game), pct(live_opg),
                    grep.get("overturn_rows", -1),
                    grep.get("games_completed", -1)))
    lines.append("ATTRIBUTION: per-game gain %s = L3 mean diff "
                 "%s x live overturns/game %s; per-game gain / "
                 "fleet delta = %s (Fai gate references: 87%% "
                 "and 101%%)"
                 % (pct(per_game), pct(mean), pct(live_opg),
                    ratio_str))
    for name in ("coreport_draw05", "coreport_lifediff"):
        r = reads[name]
        lines.append("CO-REPORT %s: mean diff %s; CI [%s, %s] "
                     "over %d jobs"
                     % (name, pct(r["mean_diff"]),
                        pct(r["ci"][0]) if r["ci"] else "n/a",
                        pct(r["ci"][1]) if r["ci"] else "n/a",
                        r["jobs"]))
    lines.append("UNFINISHED (refusals excluded from shares): "
                 "pooled share %s (finished %d, unfinished %d, "
                 "refusals %d); fallbacks %d"
                 % (pct(sh_pool), fin, unf, ref, fallbacks))
    if pooled_tally:
        for ec, n in sorted(pooled_tally.items(),
                            key=lambda kv: (-kv[1], kv[0])):
            tag = ("REFUSAL" if ec in s0.REFUSAL_CLASSES
                   else "unfinished")
            lines.append("  %-24s %4d  [%s]" % (ec, n, tag))
    s2ref = settings["stage2_reference"]
    lines.append("CO-REPORT live rates vs the Stage 2 record: "
                 "thin-prior %s (Stage 2 %s); overturn rate %s "
                 "of contested (Stage 2 %s); overturns/game %s "
                 "(Stage 2 %s)"
                 % (pct(grep.get("thin_prior_rate")),
                    pct(s2ref["thin_prior_rate"]),
                    pct(grep.get("overturn_rate")),
                    pct(s2ref["overturn_rate"]),
                    pct(grep.get("overturns_per_game")),
                    pct(s2ref["overturns_per_game"])))
    go = grep.get("teacher_outcomes_draw_scored", {})
    lines.append("CO-REPORT games outcomes (draw-scored): "
                 "Stage 3 teacher %dW/%dD/%dL = %s pts over %d "
                 "games (%.4f/game)"
                 % (go.get("W", 0), go.get("D", 0), go.get("L", 0),
                    pct(go.get("points")) if go.get("points")
                    is not None else "n/a",
                    grep.get("games_completed", 0),
                    go.get("points_per_game") or 0.0))
    lines.append("ATTRIBUTION READ COMPLETE (co-report, not a "
                 "gate: no PROCEED/STOP bands apply%s)"
                 % ("; tripwire-fired, impeachment checks above "
                    "precede this read" if tripwire is not None
                    else ""))
    for name in reads:
        reads[name].pop("_records", None)
    out["primary"] = {k: primary[k] for k in ("jobs", "mean_diff",
                                              "ci")}
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
