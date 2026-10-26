#!/usr/bin/env python3
"""Round-9 Stage 2 games report: reads the games run's own
records (paired-driver rows + teacher stat logs) and produces
the run's audited facts (ruling sec.3.4 / sec.3.7 co-reports):

  * TUPLE AUDIT (the second placement of the pin): every
    teacher stat row must carry "setting" == the settings
    file's teacher_tuple, pinned. Any mismatch, any
    tuple-malformation abort row, or any missing stamp fails
    the report (exit 2) -- a mis-pinned run is not a
    measurement, however the games went.
  * game outcomes from the driver rows: completed / invalid /
    teacher timeouts (no paired arm in Stage 2; timeouts are
    reported, per the registration), and the games' draw-
    scored outcomes from the teacher's seat (win 1, draw 0.5,
    loss 0) for the co-report beside the fleet's record.
  * LIVE RATES for the sec.3.7 co-report: contested
    decisions, thin-prior share of contested, overturn share
    of contested, overturns per completed teacher game.
  * fallbacks + abort-reason tallies from the stat rows.

Usage:
  stage2_games_report.py --out-dir <games OUT> \
      --settings settings_stage2.json --json-out games_report.json
The OUT dir holds games_s{1,2}{a,b}.jsonl driver rows and
games_s{1,2}{a,b}_log/search_stats.jsonl stat logs (the
games runner's layout).
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict


def cmap(x):
    if isinstance(x, list):
        return {i: v for i, v in enumerate(x)}
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--json-out", required=True)
    a = ap.parse_args()
    settings = json.load(open(a.settings))
    T = settings["teacher_tuple"]
    T_full = dict(T)
    T_full["pinned"] = 1

    rows = []
    for p in sorted(glob.glob(os.path.join(a.out_dir,
                                           "games_*.jsonl"))):
        if p.endswith(".manifest.json"):
            continue
        for l in open(p):
            if l.strip():
                rows.append(json.loads(l))
    stats = []
    for p in sorted(glob.glob(os.path.join(
            a.out_dir, "games_*_log", "search_stats.jsonl"))):
        for l in open(p):
            if l.strip():
                stats.append(json.loads(l))

    # ---- outcome accounting (driver rows) -------------------
    completed = [r for r in rows if "invalid" not in r]
    invalid = Counter(str(r.get("invalid")) for r in rows
                      if "invalid" in r)
    timeouts = int(invalid.get("timeout", 0))
    wdl = Counter()
    points = 0.0
    for r in completed:
        seat = int(r["seat"])
        winner = int(r.get("winner") or 0)
        if winner == 0 or int(r.get("draw") or 0) == 1:
            wdl["D"] += 1
            points += 0.5
        elif winner == seat:
            wdl["W"] += 1
            points += 1.0
        else:
            wdl["L"] += 1
    games_completed = len(completed)

    # ---- tuple audit + live rates (stat rows) ---------------
    teacher_rows = [r for r in stats if r.get("teacher") == 1]
    contested = [r for r in teacher_rows if r.get("contested") == 1]
    audit_bad = []
    for i, r in enumerate(teacher_rows):
        s = r.get("setting")
        if not isinstance(s, dict):
            audit_bad.append((i, "missing setting stamp"))
            continue
        sn = {k: s.get(k) for k in
              ("name", "hooks", "deadline_s", "horizon",
               "horizon_value", "k", "margin", "pinned")}
        want = dict(T_full)
        if sn != want:
            audit_bad.append((i, "setting %r != pin %r"
                              % (sn, want)))
    malformed = [r for r in teacher_rows
                 if r.get("fallback") == "exception"
                 and "teacher tuple pin malformed"
                 in str(r.get("abort_reason", ""))]
    exceptions = [r for r in teacher_rows
                  if r.get("fallback") == "exception"]
    thin = sum(1 for r in contested
               if r.get("fallback") == "thin_prior")
    overturns = sum(1 for r in contested if r.get("overturn") == 1)
    child_fb = sum(int(r.get("child_fallbacks") or 0)
                   for r in contested)
    abort_reasons = Counter()
    for r in contested:
        ar = r.get("abort_reasons") or {}
        if isinstance(ar, dict):
            for k, v in ar.items():
                abort_reasons[str(k)] += int(v)
    eval_fail = sum(1 for r in teacher_rows
                    if r.get("fallback") == "eval")

    report = {
        "games_rows": len(rows),
        "games_completed": games_completed,
        "games_invalid": dict(invalid),
        "teacher_timeouts": timeouts,
        "teacher_outcomes_draw_scored": {
            "W": wdl["W"], "D": wdl["D"], "L": wdl["L"],
            "points": points,
            "points_per_game": (points / games_completed
                                if games_completed else None)},
        "teacher_stat_rows": len(teacher_rows),
        "contested_rows": len(contested),
        "thin_prior_rows": thin,
        "thin_prior_rate": (thin / len(contested)
                            if contested else None),
        "overturn_rows": overturns,
        "overturn_rate": (overturns / len(contested)
                          if contested else None),
        "overturns_per_game": (overturns / games_completed
                               if games_completed else None),
        "child_fallbacks": child_fb,
        "abort_reasons": dict(abort_reasons),
        "eval_fail_rows": eval_fail,
        "exception_rows": len(exceptions),
        "tuple_audit": {
            "pin": T_full,
            "rows_checked": len(teacher_rows),
            "bad_rows": len(audit_bad),
            "malformed_pin_aborts": len(malformed),
            "ok": not audit_bad and not malformed},
    }
    with open(a.json_out, "w") as f:
        json.dump(report, f, indent=1)
    print("games: %d rows, %d completed, invalid %s; teacher "
          "W/D/L %d/%d/%d = %.1f pts (%.4f/game)"
          % (len(rows), games_completed, dict(invalid),
             wdl["W"], wdl["D"], wdl["L"], points,
             report["teacher_outcomes_draw_scored"]
                   ["points_per_game"] or 0.0))
    print("teacher rows %d, contested %d, thin-prior %d "
          "(%.4f), overturns %d (%.4f of contested, %.4f/game)"
          % (len(teacher_rows), len(contested), thin,
             report["thin_prior_rate"] or 0.0, overturns,
             report["overturn_rate"] or 0.0,
             report["overturns_per_game"] or 0.0))
    print("tuple audit: %d rows checked, %d bad, %d malformed-"
          "pin aborts -> %s"
          % (len(teacher_rows), len(audit_bad), len(malformed),
             "OK" if report["tuple_audit"]["ok"] else "FAILED"))
    if not report["tuple_audit"]["ok"]:
        for i, why in audit_bad[:5]:
            print("  bad row %d: %s" % (i, why))
        print("ABORT: tuple audit failed - the run is not a "
              "measurement")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
