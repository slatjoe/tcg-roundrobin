#!/usr/bin/env python3
"""fx_stage3_games_report: stage3_games_report.py on planted
paired games output, with hand-computed expectations.

MAIN population (5 pairs, seeds 23001-23003):
  teacher t1a (seat 1): 23001 W (winner 1), 23002 capped
    winner 0 draw 0, p1life 30 > p2life 22 (ahead), 23003
    invalid timeout.
  teacher t2a (seat 2): 23001 L (winner 1), 23002 capped
    winner 0, p1life 18 == p2life 18 (tied).
  raw r1a (seat 1): 23001 raw W (winner 1 == seat), 23002
    raw L (winner 2), 23003 invalid timeout.
  raw r2a (seat 2): 23001 raw W (winner 2 == seat), 23002
    raw W (winner 2 == seat).
  rerun games_r1a_rerun.jsonl: 23003 COMPLETED (winner 2;
    raw seat 1 -> raw loss).
Pairing: (23001,1) scored, (23002,1) scored, (23003,1)
teacher_timeout (raw from the rerun file), (23001,2)
scored, (23002,2) scored.
Stat rows (t1a log, attributed by "game" to completed
teacher games fxg23001/fxg23002): 5 teacher rows (4
contested: 1 thin-prior, 1 overturn; 1 uncontested) + 1
R14 canary line {"branch":"M","fallback":"canary",
"missing":{...}} with NO teacher key ->
canary_refusal_rows == 1 and teacher_stat_rows == 5
excludes it. Band rates: thin 0.25, overturn 0.25,
overturns/game 1/4 completed teacher games = 0.25.
Teacher outcomes: W1 D2 L1. Capped life tallies: ahead 1,
tied 1, behind 0. Pairs attempted (5) == distinct
(seed, seat) in the driver files (the merge -> report
chain consistency assert; see fx_s3_registry.py).
VARIANT rerun_timeout: the r1a 23003 rerun row is ALSO
invalid timeout (and the teacher 23003 row is a completed
W) -> pair status dropped_raw_timeout.
A corrupted tuple stat row aborts (exit 2).
Run: python3 fx_stage3_games_report.py (own temp dirs)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
REPORT = os.path.join(CODE, "stage3_games_report.py")
SETTINGS = os.path.join(CODE, "settings_stage3.json")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


T = dict(json.load(open(SETTINGS))["teacher_tuple"])
T["pinned"] = 1


def build(tmp, variant="main"):
    """variant: main | no_timeout (drop seed 23003 entirely) |
    rerun_timeout | dropped (teacher W + raw/rerun timeout) |
    corrupt. Returns (proc, report_dict, pairing_dict)."""
    t1a = [
        {"seed": 23001, "arm": "teacher", "seat": 1,
         "gamename": "fxg23001", "winner": 1, "draw": 0,
         "capped": 0, "p1life": 20, "p2life": 5},
        {"seed": 23002, "arm": "teacher", "seat": 1,
         "gamename": "fxg23002", "winner": 0, "draw": 0,
         "capped": 1, "p1life": 30, "p2life": 22},
    ]
    t2a = [
        {"seed": 23001, "arm": "teacher", "seat": 2,
         "gamename": "fxg33001", "winner": 1, "draw": 0,
         "capped": 0, "p1life": 25, "p2life": -2},
        {"seed": 23002, "arm": "teacher", "seat": 2,
         "gamename": "fxg33002", "winner": 0, "draw": 0,
         "capped": 1, "p1life": 18, "p2life": 18},
    ]
    r1a = [
        {"seed": 23001, "arm": "raw", "seat": 1,
         "gamename": "fxr23001", "winner": 1, "draw": 0,
         "capped": 0, "p1life": 20, "p2life": 5},
        {"seed": 23002, "arm": "raw", "seat": 1,
         "gamename": "fxr23002", "winner": 2, "draw": 0,
         "capped": 0, "p1life": 0, "p2life": 15},
    ]
    r2a = [
        {"seed": 23001, "arm": "raw", "seat": 2,
         "gamename": "fxr33001", "winner": 2, "draw": 0,
         "capped": 0, "p1life": 0, "p2life": 12},
        {"seed": 23002, "arm": "raw", "seat": 2,
         "gamename": "fxr33002", "winner": 2, "draw": 0,
         "capped": 0, "p1life": 3, "p2life": 20},
    ]
    rerun = []
    if variant == "main":
        t1a.append({"seed": 23003, "arm": "teacher", "seat": 1,
                    "invalid": "timeout"})
        r1a.append({"seed": 23003, "arm": "raw", "seat": 1,
                    "invalid": "timeout"})
        rerun = [{"seed": 23003, "arm": "raw", "seat": 1,
                  "gamename": "fxr23003", "winner": 2, "draw": 0,
                  "capped": 0, "p1life": 0, "p2life": 15}]
    if variant in ("rerun_timeout", "dropped"):
        t1a.append({"seed": 23003, "arm": "teacher", "seat": 1,
                    "gamename": "fxg23003", "winner": 1,
                    "draw": 0, "capped": 0,
                    "p1life": 20, "p2life": 5})
        r1a.append({"seed": 23003, "arm": "raw", "seat": 1,
                    "invalid": "timeout"})
        rerun = [{"seed": 23003, "arm": "raw", "seat": 1,
                  "invalid": "timeout"}]
    files = {"games_t1a.jsonl": t1a, "games_t2a.jsonl": t2a,
             "games_r1a.jsonl": r1a, "games_r2a.jsonl": r2a}
    if rerun:
        files["games_r1a_rerun.jsonl"] = rerun
    for name, rows in files.items():
        with open(os.path.join(tmp, name), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    logdir = os.path.join(tmp, "games_t1a_log")
    os.makedirs(logdir)
    stats = [
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg23001", "fallback": "thin_prior",
         "pick": 0, "prior_pick": 0, "child_fallbacks": 3},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg23001", "overturn": 1, "pick": 1,
         "prior_pick": 0},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg23002", "overturn": 0, "pick": 0,
         "prior_pick": 0},
        {"teacher": 1, "contested": 1, "setting": T,
         "game": "fxg23002", "overturn": 0, "pick": 2,
         "prior_pick": 2, "abort_reasons": {"abort": 2}},
        {"teacher": 1, "contested": 0, "setting": T,
         "game": "fxg23002", "pick": 0, "prior_pick": 0},
        {"branch": "M", "fallback": "canary",
         "missing": {"cards": ["fxcard"]}},
    ]
    if variant == "corrupt":
        stats[1] = dict(stats[1])
        stats[1]["setting"] = dict(T)
        stats[1]["setting"]["hooks"] = 4000
    with open(os.path.join(logdir, "search_stats.jsonl"), "w") as f:
        for r in stats:
            f.write(json.dumps(r) + "\n")
    out = os.path.join(tmp, "games_report.json")
    r = subprocess.run(
        [sys.executable, REPORT, "--out-dir", tmp,
         "--settings", SETTINGS, "--json-out", out],
        capture_output=True, text=True)
    rep = json.load(open(out)) if os.path.exists(out) else None
    pp = os.path.join(tmp, "pairing.json")
    pairing = json.load(open(pp)) if os.path.exists(pp) else None
    return r, rep, pairing


def pairmap(pairing):
    return {(p["seed"], p["seat"]): p for p in pairing["pairs"]}


def main():
    r, rep, pairing = build(tempfile.mkdtemp())
    check("report exit 0", r.returncode == 0,
          r.stdout.strip()[-160:] if r.returncode else "")
    if rep and pairing:
        pm = pairmap(pairing)
        check("pairing statuses (4 scored + teacher_timeout)",
              pm[(23001, 1)]["status"] == "scored"
              and pm[(23002, 1)]["status"] == "scored"
              and pm[(23003, 1)]["status"] == "teacher_timeout"
              and pm[(23001, 2)]["status"] == "scored"
              and pm[(23002, 2)]["status"] == "scored")
        check("teacher_timeout pair's raw row comes from the "
              "rerun file",
              pm[(23003, 1)]["raw"]["file"]
              == "games_r1a_rerun.jsonl")
        check("pairs attempted == distinct (seed,seat) in "
              "driver files (merge->report chain)",
              pairing["counts"]["pairs_attempted"] == 5)
        check("teacher accounting (5 rows, 4 completed, 1 "
              "timeout)", rep["teacher_games_rows"] == 5
              and rep["teacher_games_completed"] == 4
              and rep["teacher_timeouts"] == 1)
        check("raw accounting (5 rows + 1 rerun, 4 completed, "
              "1 timeout)", rep["raw_games_rows"] == 5
              and rep["raw_games_completed"] == 4
              and rep["raw_games_invalid"] == {"timeout": 1}
              and rep["raw_rerun_rows"] == 1)
        o = rep["teacher_outcomes_draw_scored"]
        check("teacher outcomes W1/D2/L1, per-seat + per-block",
              o["W"] == 1 and o["D"] == 2 and o["L"] == 1
              and rep["teacher_outcomes_per_seat"]["1"]["W"] == 1
              and rep["teacher_outcomes_per_seat"]["2"]["L"] == 1
              and rep["teacher_outcomes_per_block"]["t1a"]["D"] == 1)
        check("capped life tallies ahead 1 / tied 1 / behind 0",
              rep["teacher_capped_life"].get("ahead") == 1
              and rep["teacher_capped_life"].get("tied") == 1
              and rep["teacher_capped_life"].get("behind", 0) == 0)
        check("band rates (thin 0.25, overturn 0.25, 0.25/game)",
              rep["thin_prior_rate"] == 0.25
              and rep["overturn_rate"] == 0.25
              and rep["overturns_per_game"] == 0.25)
        check("tuple audit OK; teacher_stat_rows 5 excludes "
              "the canary line; canary_refusal_rows == 1",
              rep["tuple_audit"]["ok"]
              and rep["teacher_stat_rows"] == 5
              and rep["canary_refusal_rows"] == 1)
    r2, rep2, pairing2 = build(tempfile.mkdtemp(),
                               variant="rerun_timeout")
    check("rerun-also-timeout variant: pair dropped_raw_timeout",
          r2.returncode == 0 and pairing2
          and pairmap(pairing2)[(23003, 1)]["status"]
          == "dropped_raw_timeout")
    r3, _rep3, _p3 = build(tempfile.mkdtemp(), variant="corrupt")
    check("corrupted tuple row aborts (exit 2)",
          r3.returncode == 2)
    print("FX-STAGE3-GAMES-REPORT: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
