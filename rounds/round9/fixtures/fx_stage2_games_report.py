#!/usr/bin/env python3
"""fx_stage2_games_report: stage2_games_report.py on planted
games output. Known answers: 4 driver rows (2 completed --
one teacher win, one draw; 1 timeout; 1 seat_mismatch),
each carrying gamename fxg22001..fxg22004, and stat rows
attributed by "game" to the two completed games, with 4
contested rows (1 thin-prior, 1 overturn) -> completed 2,
timeouts 1, W/D/L 1/1/0 = 1.5 pts at draw=0.5 and 1.0 pts
at draw=0 (printed on the same line), band thin-prior rate
0.25, overturn rate 0.25, overturns/game 0.5, tuple audit
OK. Variant timeout_overturn adds a contested row with an
overturn in the TIMED-OUT game (fxg22003): it must be
excluded from the band rate (overturns/game stays 0.5)
and present in the all-rows co-report (overturns/game_all
1.0) -- review sec.2.2. A stat row with a wrong tuple
value fails the audit (exit 2); so does a
tuple-malformation abort row.
Run: python3 fx_stage2_games_report.py (own temp dirs)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
REPORT = os.path.join(CODE, "stage2_games_report.py")
SETTINGS = os.path.join(CODE, "settings_stage2.json")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


T = dict(json.load(open(SETTINGS))["teacher_tuple"])
T["pinned"] = 1


def build(tmp, corrupt=None, timeout_overturn=False):
    rows = [
        {"seed": 22001, "arm": "teacher", "seat": 1,
         "gamename": "fxg22001", "winner": 1, "draw": 0},
        {"seed": 22002, "arm": "teacher", "seat": 1,
         "gamename": "fxg22002", "winner": 0, "draw": 1},
        {"seed": 22003, "arm": "teacher", "seat": 1,
         "gamename": "fxg22003", "invalid": "timeout"},
        {"seed": 22004, "arm": "teacher", "seat": 1,
         "gamename": "fxg22004", "invalid": "seat_mismatch"},
    ]
    with open(os.path.join(tmp, "games_s1a.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    logdir = os.path.join(tmp, "games_s1a_log")
    os.makedirs(logdir)
    stats = [
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg22001",
         "fallback": "thin_prior", "pick": 0, "prior_pick": 0,
         "child_fallbacks": 3},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg22001",
         "overturn": 1, "pick": 1, "prior_pick": 0},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg22002",
         "overturn": 0, "pick": 0, "prior_pick": 0},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg22002",
         "overturn": 0, "pick": 2, "prior_pick": 2,
         "abort_reasons": {"abort": 2}},
        {"teacher": 1, "contested": 0, "setting": T,
         "game": "fxg22002", "pick": 0, "prior_pick": 0},
    ]
    if timeout_overturn:
        stats.append({"teacher": 1, "contested": 1,
                      "setting": T, "game": "fxg22003",
                      "overturn": 1, "pick": 1,
                      "prior_pick": 0})
    if corrupt == "hooks":
        stats[1] = dict(stats[1])
        stats[1]["setting"] = dict(T)
        stats[1]["setting"]["hooks"] = 4000
    if corrupt == "malformed":
        stats.append({"teacher": 1, "fallback": "exception",
                      "setting": {"name": "malformed"},
                      "abort_reason": "exception:Exception:"
                      "teacher tuple pin malformed: field k"})
    with open(os.path.join(logdir, "search_stats.jsonl"),
              "w") as f:
        for r in stats:
            f.write(json.dumps(r) + "\n")
    out = os.path.join(tmp, " games_report.json".strip())
    r = subprocess.run(
        [sys.executable, REPORT, "--out-dir", tmp,
         "--settings", SETTINGS, "--json-out", out],
        capture_output=True, text=True)
    rep = json.load(open(out)) if os.path.exists(out) else None
    return r, rep


def main():
    r, rep = build(tempfile.mkdtemp())
    check("report exit 0", r.returncode == 0,
          r.stdout.strip()[-160:] if r.returncode else "")
    if rep:
        check("games accounting (2 completed, 1 timeout)",
              rep["games_completed"] == 2
              and rep["teacher_timeouts"] == 1
              and rep["games_invalid"] ==
              {"timeout": 1, "seat_mismatch": 1})
        o = rep["teacher_outcomes_draw_scored"]
        check("draw-scored outcomes 1W/1D/0L = 1.5 pts",
              o["W"] == 1 and o["D"] == 1 and o["L"] == 0
              and o["points"] == 1.5
              and o["points_per_game"] == 0.75)
        check("live rates (thin 0.25, overturn 0.25, "
              "overturns/game 0.5)",
              rep["thin_prior_rate"] == 0.25
              and rep["overturn_rate"] == 0.25
              and rep["overturns_per_game"] == 0.5)
        check("tuple audit OK over 5 teacher rows",
              rep["tuple_audit"]["ok"]
              and rep["tuple_audit"]["rows_checked"] == 5)
        check("abort tallies carried (abort 2, child fb 3)",
              rep["abort_reasons"].get("abort") == 2
              and rep["child_fallbacks"] == 3)
        line = next((l for l in r.stdout.splitlines()
                     if l.startswith("games:")), "")
        check("outcome line: draw=0.5 and draw=0 points on "
              "the same line (review sec.4)",
              "1.5 pts at draw=0.5" in line
              and "1.0 pts at draw=0" in line, line)
    r4, rep4 = build(tempfile.mkdtemp(), timeout_overturn=True)
    check("timeout-overturn variant: report exit 0",
          r4.returncode == 0,
          r4.stdout.strip()[-160:] if r4.returncode else "")
    if rep4:
        check("timed-out game's overturn EXCLUDED from the "
              "band rate (overturns 1, contested 4, 0.5/game)",
              rep4["overturn_rows"] == 1
              and rep4["contested_rows"] == 4
              and rep4["overturns_per_game"] == 0.5)
        check("timed-out game's overturn PRESENT in the "
              "all-rows co-report (overturns_all 2, "
              "contested_all 5, 1.0/game)",
              rep4["overturn_rows_all"] == 2
              and rep4["contested_rows_all"] == 5
              and rep4["overturns_per_game_all"] == 1.0)
    r2, _ = build(tempfile.mkdtemp(), corrupt="hooks")
    check("wrong tuple value on a row fails the audit "
          "(exit 2)", r2.returncode == 2)
    r3, _ = build(tempfile.mkdtemp(), corrupt="malformed")
    check("tuple-malformation abort row fails the audit "
          "(exit 2)", r3.returncode == 2)
    print("FX-STAGE2-GAMES-REPORT: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
