#!/usr/bin/env python3
"""Round-9 Stage 0 sec.3 co-read: TIE-AS-LOSS (registered in
claude-reply-a00dad5 sec.3; recorded in stage0-launch.md).

A second version of each Stage 0 read (primary pass and horizon
pass), computed OFFLINE from the published label rows: identical
population, pairing, aggregation and bootstrap as the registered
read (analyze_l3_deploy.py, imported), with ONE change -- a drawn
world is scored as a LOSS (world score 0) instead of 0.5.

Method, exactly:
  * Population and pairing: analyze_l3_deploy.aggregate's rules.
    A world enters a job's paired set iff BOTH candidates
    (teacher_pick and prior_pick) have a label row for it whose
    result is a dict with no "error" and finished != 0; the
    first row wins on a duplicate world (duplicates counted).
    Error rows and unfinished rows are outside BOTH reads.
  * Standard score of a finished world: (outcome + 1) / 2, the
    registered conversion (outcome is from the deciding
    player's side; +1 win, 0 draw, -1 loss).
  * Tie-as-loss score: 0.0 when the world's winner == 0 (the
    labeler's draw marker), else the standard score. Wins stay
    1.0, losses stay 0.0; only draws move, 0.5 -> 0.0.
  * Per job: mean over shared worlds of (teacher score -
    prior score). The read is the mean over jobs; the CI is
    the deployment scorer's own game-clustered bootstrap
    (B=10000, seed 20261020, imported unmodified); frac
    better/tied/worse over job diffs; per-game gain = mean x
    (jobs scored / TEACHER_GAMES=400).

Controls run with every invocation:
  * The STANDARD read is recomputed through this same code
    path; with --expect-standard <report.json> (the box's
    (D) report for the pass) every headline figure must agree
    with the box's published primary to 1e-9 or the run
    aborts -- the tie-as-loss numbers are only ever produced
    by machinery that first reproduces the registered read.
  * Draw-marker agreement: on every finished row, winner == 0
    must hold iff outcome == 0; violations are counted and
    reported (and abort the run if any occur in the paired
    population).
  * A finished row with no "winner" field aborts the run if
    it sits in the paired population -- the draw test must
    never guess.

Report-only: this read decides nothing at Stage 0
(registration, stage0-launch.md sec.3).

Usage:
  tie_as_loss.py --jobs jobs.jsonl --labels l.jsonl [...] \
      --pass-name primary [--expect-standard report.json] \
      [--json-out tal.json]
"""
import argparse
import importlib.util
import json
import sys
from collections import defaultdict

HERE = __file__.rsplit("/", 1)[0]


def load_scorer():
    spec = importlib.util.spec_from_file_location(
        "analyze_l3_deploy", HERE + "/analyze_l3_deploy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def collect(jobs, label_rows):
    """Walk the rows once, under analyze_l3_deploy.aggregate's
    population rules. Returns (per-(snap,cand) world maps with
    (outcome, winner, horizon) per finished world, integrity
    counts, marker diagnostics)."""
    job_by_snap = {str(j["snap"]): j for j in jobs}
    worlds = defaultdict(dict)
    integ = {"rows": 0, "error_rows": 0, "unfinished": 0,
             "fallbacks": 0, "null_results": 0, "unknown_snap": 0,
             "dup_world": 0}
    diag = {"finished_rows": 0, "outcome_values": defaultdict(int),
            "marker_violations": 0, "paired_marker_violations": 0,
            "paired_missing_winner": 0,
            "horizon1_finished": 0, "horizon1_winner_nonzero": 0}
    for r in label_rows:
        integ["rows"] += 1
        snap = str(r.get("snap"))
        if snap not in job_by_snap:
            integ["unknown_snap"] += 1
            continue
        res = r.get("result")
        if not isinstance(res, dict):
            integ["null_results"] += 1
            continue
        if "error" in res:
            integ["error_rows"] += 1
            continue
        integ["fallbacks"] += int(res.get("fallbacks") or 0)
        if int(res.get("finished") or 0) == 0:
            integ["unfinished"] += 1
            continue
        diag["finished_rows"] += 1
        outcome = float(res["outcome"])
        diag["outcome_values"][repr(outcome)] += 1
        winner = res.get("winner")
        if (winner is None or int(winner) == 0) != (outcome == 0.0):
            diag["marker_violations"] += 1
        if int(res.get("horizon") or 0) == 1:
            diag["horizon1_finished"] += 1
            if winner is not None and int(winner) != 0:
                diag["horizon1_winner_nonzero"] += 1
        key = (snap, int(r["cand"]))
        w = int(r["world"])
        if w in worlds[key]:
            integ["dup_world"] += 1
            continue
        worlds[key][w] = (outcome, winner,
                          int(res.get("horizon") or 0))
    integ["jobs_total"] = len(job_by_snap)
    return job_by_snap, worlds, integ, diag


def build_records(job_by_snap, worlds, mode, diag, collect_diag=False):
    """Per-job records under one scoring mode ("standard" or
    "tie_as_loss"); mirrors analyze_l3_deploy.aggregate's
    pairing exactly. Draw counts and marker diagnostics are
    mode-independent; they are collected only on the call
    with collect_diag set (the standard pass), so the two
    modes never double-count them."""
    records = []
    jobs_missing = 0
    worlds_min = None
    draws = {"teacher": 0, "prior": 0}
    for snap, j in sorted(job_by_snap.items()):
        pp = int(j["prior_pick"])
        tp = int(j["teacher_pick"])
        a = worlds.get((snap, tp), {})
        b = worlds.get((snap, pp), {})
        shared = sorted(set(a) & set(b))
        if not shared:
            jobs_missing += 1
            continue
        diffs = []
        for w in shared:
            pair = []
            for cand_map, role in ((a, "teacher"), (b, "prior")):
                outcome, winner, _hz = cand_map[w]
                if collect_diag:
                    if winner is None:
                        diag["paired_missing_winner"] += 1
                    elif (int(winner) == 0) != (outcome == 0.0):
                        diag["paired_marker_violations"] += 1
                    if winner is not None and int(winner) == 0:
                        draws[role] += 1
                if (mode == "tie_as_loss" and winner is not None
                        and int(winner) == 0):
                    pair.append(0.0)
                else:
                    pair.append((outcome + 1.0) / 2.0)
            diffs.append(pair[0] - pair[1])
        records.append({"snap": snap, "game": str(j["game"]),
                        "diff": sum(diffs) / len(diffs),
                        "n_worlds": len(shared)})
        if worlds_min is None or len(shared) < worlds_min:
            worlds_min = len(shared)
    return records, jobs_missing, worlds_min, draws


def one_read(scorer, jobs, label_rows, expect_standard=None):
    job_by_snap, worlds, integ, diag = collect(jobs, label_rows)
    out = {"integrity": integ, "diag": {k: (dict(v) if isinstance(v, defaultdict) else v) for k, v in diag.items()}}
    reads = {}
    for mode in ("standard", "tie_as_loss"):
        records, missing, wmin, draws = build_records(
            job_by_snap, worlds, mode, diag,
            collect_diag=(mode == "standard"))
        s = scorer.summarize(records, dict(integ,
                                           jobs_missing=missing,
                                           worlds_min=wmin))
        s["paired_drawn_worlds"] = draws
        reads[mode] = s
    # the drawn-world counts describe the (shared) paired
    # population, not the scoring mode: report the standard
    # pass's counts on both reads.
    reads["tie_as_loss"]["paired_drawn_worlds"] = \
        reads["standard"]["paired_drawn_worlds"]
    out["reads"] = reads
    if diag["paired_missing_winner"]:
        raise SystemExit("ABORT: %d paired worlds lack a winner "
                         "field; the draw test cannot guess"
                         % diag["paired_missing_winner"])
    if diag["paired_marker_violations"]:
        raise SystemExit("ABORT: winner/outcome draw markers "
                         "disagree inside the paired population")
    if expect_standard is not None:
        box = expect_standard["primary"]
        mine = reads["standard"]
        for key in ("jobs_scored", "mean_diff", "per_game_gain",
                    "frac_pos", "frac_zero", "frac_neg"):
            if abs(float(box[key]) - float(mine[key])) > 1e-9:
                raise SystemExit(
                    "ABORT: standard-mode %s=%r disagrees with "
                    "the box report's %r" % (key, mine[key], box[key]))
        for i in (0, 1):
            if abs(float(box["ci"][i]) - float(mine["ci"][i])) > 1e-9:
                raise SystemExit("ABORT: standard-mode CI disagrees "
                                 "with the box report's CI")
        out["standard_cross_check"] = ("AGREE (1e-9) with the box "
                                        "report's primary read")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--pass-name", required=True)
    ap.add_argument("--expect-standard")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    rows = []
    for path in a.labels:
        with open(path) as f:
            for l in f:
                if l.strip():
                    rows.append(json.loads(l))
    expect = None
    if a.expect_standard:
        expect = json.load(open(a.expect_standard))
    scorer = load_scorer()
    out = one_read(scorer, jobs, rows, expect)
    out["pass"] = a.pass_name
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    std = out["reads"]["standard"]
    tal = out["reads"]["tie_as_loss"]
    print("=== TIE-AS-LOSS CO-READ — pass: %s ===" % a.pass_name)
    if "standard_cross_check" in out:
        print("standard-mode cross-check: %s" % out["standard_cross_check"])
    print("  STANDARD    : jobs %d; mean paired diff %.4f; CI [%.4f, %.4f]; "
          "per-game gain %.4f" % (std["jobs_scored"], std["mean_diff"],
                                  std["ci"][0], std["ci"][1],
                                  std["per_game_gain"]))
    print("  TIE-AS-LOSS: jobs %d; mean paired diff %.4f; CI [%.4f, %.4f]; "
          "per-game gain %.4f" % (tal["jobs_scored"], tal["mean_diff"],
                                  tal["ci"][0], tal["ci"][1],
                                  tal["per_game_gain"]))
    print("  frac better/tied/worse (tie-as-loss): %.4f / %.4f / %.4f"
          % (tal["frac_pos"], tal["frac_zero"], tal["frac_neg"]))
    print("  paired drawn worlds (winner==0): teacher %d, prior %d"
          % (std["paired_drawn_worlds"]["teacher"],
             std["paired_drawn_worlds"]["prior"]))
    d = out["diag"]
    print("  marker check: finished rows %d; winner==0 iff outcome==0 "
          "violations %d (paired %d); horizon==1 finished %d, of "
          "which winner!=0: %d" % (d["finished_rows"],
                                   d["marker_violations"],
                                   d["paired_marker_violations"],
                                   d["horizon1_finished"],
                                   d["horizon1_winner_nonzero"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
