#!/usr/bin/env python3
"""Round-10 Step 0 probe: the L3 label read.

Construction mirrors stage3_attr_analyze.run_read
(primary, draw = 0) exactly -- worlds paired by world
index across each job's two candidates, refusal
worlds skipped, only worlds finished in BOTH
candidates counted, score = 1.0 if outcome > 0 else
0.0, job diff = mean of the per-world differences --
with three probe-specific differences, all in what
is grouped and reported, none in the read itself:

  * jobs are grouped by probe_band ("uncontested" /
    "contested_band") and, inside "uncontested", by
    the z > tail_z tail subset; the third class,
    "uncontested_diag" (the (1.0, 1.5] superset,
    fix pass), is read for counts and edge only --
    it is EXCLUDED from per-game gain and from the
    decision rule;
  * per-game gain is computed Claude's sec.5 form:
    per capture game, the summed diffs of that game's
    jobs of the class (capture games with no jobs of
    the class contribute 0), averaged over ALL
    capture games, with a game-clustered CI and a
    one-sided 95% lower bound -- the product form
    (edge x rate) is printed as a cross-check only;
  * SAMPLING WEIGHTS (fix pass, claude-reply-402c92f
    sec.2.1, BLOCKING): uncontested states were
    captured by systematic sampling, every
    capture.uncontested_every-th eligible decision,
    so each uncontested job's diff is weighted by
    that factor (Horvitz-Thompson) INSIDE the
    per-game sum, and the bootstrap runs over the
    weighted per-game totals. Contested-band jobs
    are unsampled and keep weight 1. The weight is
    printed on the CLASS line and recorded in the
    JSON gain object;
  * no verdict: the reads feed probe_report.py's
    registered decision rule.

Guards (round-9 forms): the label-tuple audit
projects every row's stamp on the label tuple's keys
(the stage2-analyzer-fix form); the world-count
guard demands exactly --expect-rows rows per
(snap, candidate); the refusal taxonomy and
jobs_no_shared_worlds are reported as in Stage 3.

Sec.14 (2026-10-29, claude-reply-28c2065 sec.3.3):
with --capalign-classes <capalign_classes.json>
(and --capalign-states <capalign_states.jsonl> for
the cap-aligned z), the read computes BOTH scorings
from the same label rows. CAP-ALIGNED is the
registered primary: a world scores 1.0 only if its
outcome > 0 AND it ended by turn 61 (a decisive
world ending after turn 61 is a horizon draw under
the live instrument and scores 0, as a flagged
horizon world already does), and jobs are grouped
by their CAP-ALIGNED class from capalign_eval.py --
jobs whose cap-aligned class is null (the drop-outs)
are excluded and counted. The as-run read (the job
file's own classes, the original scoring) is
computed exactly as before and printed beside it,
labeled, as a co-report. Without the flag the
output is the pre-sec.14 read, unchanged.

Usage: probe_label_analyze.py --jobs jobs_all.jsonl
  --labels labels_all.jsonl --capture-games
  capture_games.json (the eval jobs report, whose
  games_list is the capture population)
  --settings settings_probe.json
  [--expect-rows 50] [--json-out label_read.json]
  [--capalign-classes capalign_classes.json
   --capalign-states capalign_states.jsonl]
"""
import argparse
import importlib.util
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

# sec.14 registered rule: the live instrument's cap
# trigger is currentTurn 62 (play_game.php), so a
# decisive world is one that ended by turn 61.
CAP_LAST_DECISIVE_TURN = 61


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def job_diffs(jobs, rows, s0, cap_aligned=False):
    """The read's per-job paired diffs, computed
    exactly as this script's main() has always
    computed them (worlds paired by world index
    across each job's two candidates, refusal worlds
    skipped, only worlds finished in BOTH candidates
    counted). Lifted to module level in fix pass 5
    (claude-reply-9dae0e2 sec.2.3) so that
    probe_influence.py reuses THIS machinery for its
    leave-one-game-out read instead of reimplementing
    it; the math is unchanged. Returns
    (diff_by_snap, counts).

    Sec.14: with cap_aligned=True the world score
    applies the registered cap-aligned rule -- a
    world counts as a win only if outcome > 0 AND
    it ended by turn 61 (CAP_LAST_DECISIVE_TURN);
    a decisive world ending later is a horizon draw
    and scores 0, exactly as winner == 0 worlds
    already score. Nothing else changes."""
    job_by_snap = {str(j["snap"]): j for j in jobs}
    worlds = defaultdict(dict)
    fallbacks = 0
    fin = unf = ref = 0
    for r in rows:
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            continue
        j = job_by_snap[snap]
        cand = int(r["cand"])
        if cand not in (int(j["teacher_pick"]),
                        int(j["prior_pick"])):
            continue
        kind, _ = s0.classify(r.get("result"))
        if kind == "finished":
            fin += 1
        elif kind == "refusal":
            ref += 1
        else:
            unf += 1
        if isinstance(r.get("result"), dict):
            fallbacks += int(r["result"].get("fallbacks") or 0)
        if int(r["world"]) not in worlds[(snap, cand)]:
            worlds[(snap, cand)][int(r["world"])] = (
                kind, r.get("result"))

    def score(res):
        if float(res["outcome"]) > 0:
            if cap_aligned and int(res.get("turns") or 0) \
                    > CAP_LAST_DECISIVE_TURN:
                return 0.0
            return 1.0
        return 0.0

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
                "game": str(j["game"]),
                "probe_band": str(j["probe_band"]),
                "prior_band": j.get("prior_band"),
                "z": float(j["z"]),
                "n_worlds": len(diffs)}
    counts = {"finished": fin, "unfinished": unf,
              "refusals": ref,
              "fallbacks": fallbacks,
              "jobs_no_shared_worlds":
                  len(jobs) - len(diff_by_snap)}
    return diff_by_snap, counts


def per_game_gain(recs, cap_games, stock, weight=1.0):
    """Claude's sec.5 per-game gain: per capture game,
    the summed (weighted) diffs of that game's jobs,
    averaged over ALL capture games in cap_games
    (games with no jobs of the class contribute 0),
    with the game-clustered CI; the one-sided 95%
    lower bound is the two-sided CI's lower bound,
    the registered conservative stand-in. Lifted to
    module level in fix pass 5 for probe_influence.py
    (its LOGO read calls this on game-excluded record
    and population sets); the math is unchanged."""
    per = defaultdict(float)
    for r in recs:
        per[r["game"]] += r["diff"] * weight
    grecs = [{"game": g, "diff": per.get(g, 0.0)}
             for g in cap_games]
    if not grecs:
        return {"gain": None, "ci": None,
                "lb95_1sided": None, "weight": weight}
    m = sum(r["diff"] for r in grecs) / len(grecs)
    lo, hi = stock.cluster_bootstrap(grecs)
    # one-sided 95% lower bound from the same bootstrap
    # distribution would need the replicates; the
    # registered form uses the two-sided CI's lower
    # bound as the conservative stand-in and says so.
    return {"gain": m, "ci": [lo, hi], "lb95_1sided": lo,
            "games": len(grecs), "weight": weight}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--capture-games", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--expect-rows", type=int, default=50)
    ap.add_argument("--json-out")
    ap.add_argument("--capalign-classes")
    ap.add_argument("--capalign-states")
    a = ap.parse_args()

    s0 = load_mod("stage0_report")
    stock = load_mod("analyze_l3")
    settings = json.load(open(a.settings))
    LT = settings["label"]["tuple"]
    tail_z = float(settings["report"]["tail_z"])
    unc_every = int(settings["capture"]["uncontested_every"])
    cap_games = [str(g) for g in
                 json.load(open(a.capture_games))["games_list"]]
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    job_by_snap = {str(j["snap"]): j for j in jobs}
    rows = []
    for path in a.labels:
        for l in open(path):
            if l.strip():
                rows.append(json.loads(l))

    bad = 0
    for r in rows:
        s = r.get("setting")
        if not isinstance(s, dict) or {
                k: s.get(k) for k in LT} != LT:
            bad += 1
    if bad:
        print("ABORT: %d label rows carry a setting stamp "
              "!= the registered label tuple" % bad)
        return 2

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
                      "exactly %d" % (snap, cand, n,
                                      a.expect_rows))
                return 2

    diff_by_snap, dc = job_diffs(jobs, rows, s0)
    fin, unf, ref = dc["finished"], dc["unfinished"], \
        dc["refusals"]
    fallbacks = dc["fallbacks"]
    jobs_no_shared = dc["jobs_no_shared_worlds"]

    def read(recs):
        if not recs:
            return {"jobs": 0, "edge": None, "ci": None}
        m = sum(r["diff"] for r in recs) / len(recs)
        lo, hi = stock.cluster_bootstrap(
            [{"game": r["game"], "diff": r["diff"]} for r in recs])
        return {"jobs": len(recs), "edge": m, "ci": [lo, hi]}

    def class_reads(recs_all):
        """The per-class reads and their text lines for
        ONE scoring of the rows (grouping by each
        record's probe_band, tail by its z). Used for
        the as-run read and, under sec.14, for the
        cap-aligned read on regrouped records."""
        by_class = {}
        gains = {}
        blines = []
        for cls in ("uncontested", "contested_band"):
            recs = [r for r in recs_all
                    if r["probe_band"] == cls]
            rd = read(recs)
            # sec.2.1: uncontested jobs carry the
            # sampling weight; contested-band jobs are
            # unsampled.
            w = float(unc_every) if cls == "uncontested" \
                else 1.0
            gain = per_game_gain(recs, cap_games, stock, w)
            by_class[cls] = rd
            gains[cls] = gain
            blines.append(
                "CLASS %s: jobs %d; edge %s CI [%s, %s]; "
                "per-game gain %s CI [%s, %s] over %d "
                "capture games; sampling weight %s"
                % (cls, rd["jobs"], pct(rd["edge"]),
                   pct(rd["ci"][0]) if rd["ci"] else "n/a",
                   pct(rd["ci"][1]) if rd["ci"] else "n/a",
                   pct(gain["gain"]),
                   pct(gain["ci"][0]) if gain["ci"]
                   else "n/a",
                   pct(gain["ci"][1]) if gain["ci"]
                   else "n/a",
                   gain.get("games") or 0, "%g" % w))
            if cls == "uncontested":
                tail = [r for r in recs if r["z"] > tail_z]
                trd = read(tail)
                by_class["uncontested_tail"] = trd
                blines.append(
                    "CLASS uncontested TAIL (z > %.1f): "
                    "jobs %d; edge %s CI [%s, %s]"
                    % (tail_z, trd["jobs"], pct(trd["edge"]),
                       pct(trd["ci"][0]) if trd["ci"]
                       else "n/a",
                       pct(trd["ci"][1]) if trd["ci"]
                       else "n/a"))
                pb = defaultdict(list)
                for r in recs:
                    pb[str(r["prior_band"])].append(r)
                by_class["uncontested_by_prior_band"] = {
                    k: read(v) for k, v in sorted(pb.items())}
        # the diagnostic superset class: counts and
        # edge only -- NO per-game gain entry, so
        # nothing downstream can fold it into the
        # threshold gain or the decision rule
        # (fix pass, sec.3/F2).
        diag = [r for r in recs_all
                if r["probe_band"] == "uncontested_diag"]
        drd = read(diag)
        by_class["uncontested_diag"] = drd
        blines.append(
            "CLASS uncontested_diag (DIAGNOSTIC ONLY -- "
            "the (1.0, 1.5] uncontested superset; "
            "excluded from the threshold gain and the "
            "decision rule): jobs %d; edge %s CI [%s, %s]"
            % (drd["jobs"], pct(drd["edge"]),
               pct(drd["ci"][0]) if drd["ci"] else "n/a",
               pct(drd["ci"][1]) if drd["ci"] else "n/a"))
        return by_class, gains, blines

    recs_all = list(diff_by_snap.values())
    by_class, gains, block_lines = class_reads(recs_all)
    out = {"jobs": len(jobs),
           "jobs_no_shared_worlds": jobs_no_shared,
           "label_rows": len(rows),
           "finished": fin, "unfinished": unf, "refusals": ref,
           "fallbacks": fallbacks,
           "by_class": by_class, "per_game_gain": gains}
    lines = ["=== ROUND-10 STEP 0 PROBE -- L3 LABEL READ "
             "(primary: horizon 62, draw = 0) ==="]
    lines += block_lines
    if a.capalign_classes:
        cmap = json.load(open(a.capalign_classes))
        capz = {}
        if a.capalign_states:
            for l in open(a.capalign_states):
                if l.strip():
                    r = json.loads(l)
                    capz[str(r["snap"])] = float(
                        r["cap_aligned"]["z"]) \
                        if r["cap_aligned"]["z"] is not None \
                        else 0.0
        missing = [s for s in job_by_snap if s not in cmap]
        if missing:
            print("ABORT: %d label jobs have no entry in "
                  "the cap-aligned class map (first: %s) -- "
                  "the map must cover every eval state"
                  % (len(missing), missing[0]))
            return 2
        diff_cap, _dc = job_diffs(jobs, rows, s0,
                                  cap_aligned=True)
        cap_recs = []
        excluded = 0
        for snap, rec in diff_cap.items():
            cls = cmap[snap]
            if cls is None:
                excluded += 1
                continue
            r2 = dict(rec)
            r2["probe_band"] = cls
            if snap in capz:
                r2["z"] = capz[snap]
            cap_recs.append(r2)
        cb, cg, clines = class_reads(cap_recs)
        out["capaligned"] = {
            "by_class": cb, "per_game_gain": cg,
            "excluded_jobs": excluded,
            "jobs_with_diffs": len(diff_cap),
            "scoring": "cap_aligned: a world scores 1.0 "
                       "only if outcome > 0 and it ended "
                       "by turn 61; classes from "
                       "capalign_eval.py"}
        lines = ["=== ROUND-10 STEP 0 PROBE -- L3 LABEL "
                 "READ (sec.14: CAP-ALIGNED is the "
                 "registered primary; decisive only by "
                 "turn 61, draw = 0) ===",
                 "--- CAP-ALIGNED (registered primary) ---"]
        lines += clines
        lines.append("cap-aligned grouping excluded %d "
                     "jobs (drop-outs: their states no "
                     "longer qualify)" % excluded)
        lines.append("--- AS-RUN (pre-alignment scoring "
                     "of the same rows; co-report only) "
                     "---")
        lines += block_lines
    lines.append("jobs_no_shared_worlds %d of %d; label rows "
                 "%d (finished %d, unfinished %d, refusals %d); "
                 "fallbacks %d"
                 % (jobs_no_shared, len(jobs), len(rows), fin,
                    unf, ref, fallbacks))
    txt = "\n".join(lines) + "\n"
    print(txt)
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
