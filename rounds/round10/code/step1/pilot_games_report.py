#!/usr/bin/env python3
"""Round-10 Step 1 pilot games report: the games run's
audited facts (claude-reply-243b9d8 sec.3.2/3.3):

  * TUPLE AUDIT: every teacher stat row's "setting" must
    equal the settings file's teacher_tuple (pinned). A
    mismatch, a malformed-pin abort, or a missing stamp
    fails the report (exit 2).
  * Outcomes from the driver rows (no paired arm:
    timeouts are reported; a teacher timeout is a row
    with invalid == "timeout").
  * WALL per game from the driver rows' "secs": mean,
    p95 (nearest-rank: the ceil(0.95*n)-th smallest),
    max -- over completed games; timed-out rows carry
    no completed wall and are counted separately.
  * CLASS TALLIES over searched decisions (stat rows
    with priors): contested (top prior < 0.97) vs
    newly_contested (top prior >= 0.97), fires
    (overturn == 1) per class and per game, thin-prior
    and fallback tallies. Rates count stat rows in
    COMPLETED games only (the round-9 sec.2.2 basis);
    the *_all keys co-report over all stat rows.

Usage:
  pilot_games_report.py --out-dir <games OUT>
      --settings settings_pilot.json
      --json-out games_report.json
The OUT dir holds games_s{1,2}{a,b}.jsonl driver rows
and games_s{1,2}{a,b}_log/search_stats.jsonl stat logs
(the pilot runner's layout).
"""
import argparse
import glob
import json
import math
import os
import sys
from collections import Counter

BOUNDARY = 0.97


def top_prior(r):
    pv = r.get("priors")
    if isinstance(pv, dict):
        vals = [float(x) for x in pv.values()]
    elif isinstance(pv, list):
        vals = [float(x) for x in pv]
    else:
        return None
    return max(vals) if vals else None


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

    completed = [r for r in rows if "invalid" not in r]
    invalid = Counter(str(r.get("invalid")) for r in rows
                      if "invalid" in r)
    timeouts = int(invalid.get("timeout", 0))
    completed_names = {str(r["gamename"]) for r in completed
                       if r.get("gamename") is not None}
    games_completed = len(completed)

    walls = sorted(float(r["secs"]) for r in completed
                   if r.get("secs") is not None)
    if walls:
        n = len(walls)
        wall = {"n": n, "mean": sum(walls) / n,
                "p95": walls[math.ceil(0.95 * n) - 1],
                "max": walls[-1]}
    else:
        wall = {"n": 0, "mean": None, "p95": None, "max": None}

    teacher_rows = [r for r in stats if r.get("teacher") == 1]
    audit_bad = []
    for i, r in enumerate(teacher_rows):
        s = r.get("setting")
        if not isinstance(s, dict):
            audit_bad.append((i, "missing setting stamp"))
            continue
        sn = {k: s.get(k) for k in
              ("name", "hooks", "deadline_s", "horizon",
               "horizon_value", "k", "margin", "pinned")}
        if sn != T_full:
            audit_bad.append((i, "setting %r != pin %r"
                              % (sn, T_full)))
    malformed = [r for r in teacher_rows
                 if r.get("fallback") == "exception"
                 and "teacher tuple pin malformed"
                 in str(r.get("abort_reason", ""))]

    def class_tallies(pop):
        out = {}
        for cls in ("contested", "newly_contested"):
            sel = [r for r in pop if r.get("cls") == cls]
            fires = sum(1 for r in sel
                        if r.get("overturn") == 1)
            out[cls] = {
                "decisions": len(sel), "fires": fires,
                "fires_per_game": (fires / games_completed
                                   if games_completed else None),
                "thin_prior": sum(
                    1 for r in sel
                    if r.get("fallback") == "thin_prior")}
        return out

    searched = []
    for r in teacher_rows:
        if "priors" not in r:
            continue
        tp = top_prior(r)
        if tp is None:
            continue
        rr = dict(r)
        rr["cls"] = ("contested" if tp < BOUNDARY
                     else "newly_contested")
        searched.append(rr)
    pop_completed = [r for r in searched
                     if str(r.get("game")) in completed_names]

    wdl = Counter()
    points0 = 0.0
    for r in completed:
        seat = int(r["seat"])
        winner = int(r.get("winner") or 0)
        if winner == 0 or int(r.get("draw") or 0) == 1:
            wdl["D"] += 1
        elif winner == seat:
            wdl["W"] += 1
            points0 += 1.0
        else:
            wdl["L"] += 1

    report = {
        "games_rows": len(rows),
        "games_completed": games_completed,
        "games_invalid": dict(invalid),
        "teacher_timeouts": timeouts,
        "teacher_outcomes_draw0": {
            "W": wdl["W"], "D": wdl["D"], "L": wdl["L"],
            "points": points0,
            "points_per_game": (points0 / games_completed
                                if games_completed else None)},
        "wall_s": wall,
        "teacher_stat_rows": len(teacher_rows),
        "searched_rows": len(searched),
        "classes_completed_games": class_tallies(pop_completed),
        "classes_all": class_tallies(searched),
        "child_fallbacks": sum(int(r.get("child_fallbacks") or 0)
                               for r in searched),
        "eval_fail_rows": sum(1 for r in teacher_rows
                              if r.get("fallback") == "eval"),
        "tuple_audit": {
            "pin": T_full, "rows_checked": len(teacher_rows),
            "bad_rows": len(audit_bad),
            "malformed_pin_aborts": len(malformed),
            "ok": not audit_bad and not malformed},
    }
    with open(a.json_out, "w") as f:
        json.dump(report, f, indent=1, allow_nan=False)
    print("games: %d rows, %d completed, invalid %s; teacher "
          "W/D/L %d/%d/%d (draw=0 points %.4f/game)"
          % (len(rows), games_completed, dict(invalid),
             wdl["W"], wdl["D"], wdl["L"],
             report["teacher_outcomes_draw0"]
                   ["points_per_game"] or 0.0))
    print("wall per game (completed): n=%d mean %s p95 %s "
          "max %s; teacher timeouts %d"
          % (wall["n"],
             ("%.1f" % wall["mean"]) if wall["mean"] else "n/a",
             ("%.1f" % wall["p95"]) if wall["p95"] else "n/a",
             ("%.1f" % wall["max"]) if wall["max"] else "n/a",
             timeouts))
    for cls in ("contested", "newly_contested"):
        t = report["classes_completed_games"][cls]
        print("class %s (completed games): %d decisions, %d "
              "fires (%.4f/game), thin-prior %d"
              % (cls, t["decisions"], t["fires"],
                 t["fires_per_game"] or 0.0, t["thin_prior"]))
    print("tuple audit: %d rows checked, %d bad, %d "
          "malformed-pin aborts -> %s"
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
