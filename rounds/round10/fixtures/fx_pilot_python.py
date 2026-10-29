#!/usr/bin/env python3
"""Step 1 pilot fixture: writer->reader round trips on
real output shapes + the read's arithmetic computed
by hand.

  J. build_pilot_jobs.py on synthetic snap-index rows
     (the search_s3_thr overturn block's real shape)
     and stat rows (the live row's real shape):
     order-aware pairing at a repeated key assigns
     classes by the paired rows' priors; a se_diff=0
     job carries the strict sentinel (z 999.0,
     z_nonfinite) and the file parses as strict
     JSON; a missing stat row aborts (exit 2).
  G. pilot_games_report.py on a synthetic OUT: wall
     mean/p95(nearest-rank)/max by hand; a timeout
     row counted, not walled; tuple audit passes;
     a bad stamp aborts (exit 2).
  R. pilot_read.py's arithmetic on synthetic jobs +
     label rows (result shape incl. turns inside the
     result dict), with every number computed by
     hand in this fixture:
       job A (g1, contested, z 2.0): diff +0.5
       job B (g2, newly_contested, z 4.0): diff +0.5
       job C (g2, contested, z 999 sentinel):
         teacher's only "win" ended turn 70 -> the
         cap-aligned score is 0 -> diff 0.0
     per-game totals: g1 .5, g2 .5, g3 0, g4 0
     (g3/g4 are zero-job population games);
     total gain 0.25; contested gain 0.125;
     newly gain 0.125; LOGO total range
     [1/6, 1/3]; largest share 0.5; edges by class
     and band; the STOP line reads DO NOT STOP.
     A second planted set with all-negative diffs
     reads STOP.
  T. the STOP gate's ONE-SIDED bound (fix pass 1,
     claude-reply-acc55a1 sec.2.2): a planted
     100-game population -- 4 games with per-game
     total 1.12 (2 jobs x 14/25 winning worlds),
     96 games at 0 -- whose registered bootstrap
     (B=10000, seed 20261020) gives, computed here
     from the replicate distribution's closed form
     and asserted exactly: 95th percentile 0.0784
     (< 0.0849) but 97.5th percentile 0.0896
     (>= 0.0849). Under the two-sided ub the read
     would NOT stop; the read MUST print STOP.
  S. sizing_read against hand arithmetic:
     lb 0.1649, SE 0.02, n-games 100 ->
     Delta 0.1000; R = (0.1/2.4866)^2 - 0.009^2;
     n = ceil(100 x 0.02^2 / R) = 27 (hand-computed
     here from the registered formula, not via the
     module); Delta <= 0 -> n None.
"""
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
sys.path.insert(0, S1)
fails = []
checks = 0


def check(name, good, detail=""):
    global checks
    checks += 1
    print("%s %s %s" % ("PASS" if good else "FAIL",
                        name, detail))
    if not good:
        fails.append(name)


def run(args, **kw):
    return subprocess.run(args, capture_output=True,
                          text=True, **kw)


def w(path, obj):
    with open(path, "w") as f:
        f.write(json.dumps(obj, allow_nan=False) + "\n")


TUPLE = {"name": "H8k-180+H", "hooks": 8000,
         "deadline_s": 180, "horizon": 62,
         "horizon_value": -1, "k": 25, "margin": 1.5,
         "pinned": 1}
SETTINGS = json.load(open(os.path.join(
    S1, "settings_pilot.json")))


def stat_row(game, branch, player, turn, pp, pick,
             priors, md, sd, overturn=1):
    return {"teacher": 1, "contested": 1, "setting": TUPLE,
            "branch": branch, "player": player,
            "turn": turn, "game": game, "priors": priors,
            "prior_pick": pp, "pick": pick,
            "overturn": overturn, "mean_diff": md,
            "se_diff": sd, "selected": [pp, pick]}


def index_row(snap, game, branch, player, turn, pp, tp):
    return {"snap": snap, "game": game, "hcount": 1,
            "branch": branch, "player": player,
            "turn": turn,
            "cands": [{"card_id": "a", "zone": "Hand"},
                      {"card_id": "b", "zone": "Hand"}],
            "state": None, "teacher_pick": tp,
            "prior_pick": pp, "mean_diff": 0.1,
            "se_diff": 0.05}


def test_jobs(tmp):
    idx = os.path.join(tmp, "teacher_snap_index.jsonl")
    stats = os.path.join(tmp, "search_stats.jsonl")
    rows_i = [
        index_row("g1_t1", "g1", "M", 1, 5, 0, 1),
        index_row("g1_t2", "g1", "M", 1, 5, 0, 1),
        index_row("g2_t1", "g2", "M", 2, 7, 0, 1)]
    rows_s = [
        stat_row("g1", "M", 1, 5, 0, 1,
                 {"0": 0.5, "1": 0.4}, 0.2, 0.1),
        stat_row("g1", "M", 1, 5, 0, 1,
                 {"0": 0.99, "1": 0.005}, 0.3, 0.1),
        stat_row("g2", "M", 2, 7, 0, 1,
                 {"0": 0.6, "1": 0.3}, 1.2, 0.0)]
    with open(idx, "w") as f:
        for r in rows_i:
            f.write(json.dumps(r) + "\n")
    with open(stats, "w") as f:
        for r in rows_s:
            f.write(json.dumps(r) + "\n")
    out = os.path.join(tmp, "jobs_all.jsonl")
    r = run([sys.executable,
             os.path.join(S1, "build_pilot_jobs.py"),
             "--stream", "SNAPS=" + idx,
             "--stats", stats,
             "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--out", out, "--shard-prefix",
             os.path.join(tmp, "jobs_shard"),
             "--report", os.path.join(tmp, "jr.json")])
    check("J jobs builder runs", r.returncode == 0,
          r.stderr[-200:] if r.returncode else "")
    jobs = [json.loads(l) for l in open(out)]
    by_snap = {j["snap"]: j for j in jobs}
    check("J order-aware pairing: first at key is "
          "contested", by_snap["g1_t1"]["class"]
          == "contested")
    check("J order-aware pairing: second at key is "
          "newly_contested", by_snap["g1_t2"]["class"]
          == "newly_contested")
    check("J z from the paired stat row",
          abs(by_snap["g1_t1"]["z"] - 2.0) < 1e-9
          and abs(by_snap["g1_t2"]["z"] - 3.0) < 1e-9)
    check("J se_diff=0 -> strict sentinel",
          by_snap["g2_t1"]["z"] == 999.0
          and by_snap["g2_t1"]["z_nonfinite"] is True)
    raw = open(out).read()
    check("J jobs file is strict JSON (no Infinity/"
          "NaN tokens)", "Infinity" not in raw
          and "NaN" not in raw)
    # negative: drop one stat row -> pairing abort
    with open(stats, "w") as f:
        for r in rows_s[:2]:
            f.write(json.dumps(r) + "\n")
    r = run([sys.executable,
             os.path.join(S1, "build_pilot_jobs.py"),
             "--stream", "SNAPS=" + idx,
             "--stats", stats,
             "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--out", out, "--shard-prefix",
             os.path.join(tmp, "jobs_shard"),
             "--report", os.path.join(tmp, "jr.json")])
    check("J missing stat row aborts (exit 2)",
          r.returncode == 2)


def test_games_report(tmp):
    out = os.path.join(tmp, "games")
    os.makedirs(os.path.join(out, "games_s1a_log"))
    with open(os.path.join(out, "games_s1a.jsonl"),
              "w") as f:
        for r in ({"seed": 1, "seat": 1, "winner": 1,
                   "draw": False, "secs": 100.0,
                   "gamename": "g1"},
                  {"seed": 2, "seat": 1, "winner": 2,
                   "draw": False, "secs": 300.0,
                   "gamename": "g2"},
                  {"seed": 3, "seat": 1,
                   "invalid": "timeout",
                   "gamename": "g3"}):
            f.write(json.dumps(r) + "\n")
    stats = [stat_row("g1", "M", 1, 5, 0, 1,
                      {"0": 0.5, "1": 0.4}, 0.2, 0.1),
             stat_row("g2", "M", 1, 9, 0, 1,
                      {"0": 0.99, "1": 0.005}, 0.3, 0.1)]
    sp = os.path.join(out, "games_s1a_log",
                      "search_stats.jsonl")
    with open(sp, "w") as f:
        for r in stats:
            f.write(json.dumps(r) + "\n")
    jr = os.path.join(out, "games_report.json")
    r = run([sys.executable,
             os.path.join(S1, "pilot_games_report.py"),
             "--out-dir", out, "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--json-out", jr])
    check("G games report runs", r.returncode == 0,
          r.stderr[-200:] if r.returncode else "")
    rep = json.load(open(jr))
    check("G wall mean/p95/max by hand (200/300/300)",
          rep["wall_s"]["mean"] == 200.0
          and rep["wall_s"]["p95"] == 300.0
          and rep["wall_s"]["max"] == 300.0)
    check("G timeout counted, not walled",
          rep["teacher_timeouts"] == 1
          and rep["wall_s"]["n"] == 2)
    check("G class tallies by top prior",
          rep["classes_completed_games"]["contested"]
          ["fires"] == 1
          and rep["classes_completed_games"]
          ["newly_contested"]["fires"] == 1)
    bad = dict(stats[0])
    bad["setting"] = dict(TUPLE, margin=9.9)
    with open(sp, "w") as f:
        f.write(json.dumps(bad) + "\n")
        f.write(json.dumps(stats[1]) + "\n")
    r = run([sys.executable,
             os.path.join(S1, "pilot_games_report.py"),
             "--out-dir", out, "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--json-out", jr])
    check("G bad tuple stamp aborts (exit 2)",
          r.returncode == 2)


def label_row(snap, cand, world, outcome, turns):
    return {"snap": snap, "cand": cand, "world": world,
            "result": {"outcome": outcome, "finished": 1,
                       "fallbacks": 0, "turns": turns}}


def test_read(tmp):
    import pilot_read as pr
    games = ["g1", "g2", "g3", "g4"]
    recs = [{"diff": 0.5, "game": "g1",
             "class": "contested"},
            {"diff": 0.5, "game": "g2",
             "class": "newly_contested"},
            {"diff": 0.0, "game": "g2",
             "class": "contested"}]
    per = pr.per_game_totals(recs, games)
    check("R per-game totals by hand",
          per == {"g1": 0.5, "g2": 0.5, "g3": 0.0,
                  "g4": 0.0}, str(per))
    logo = pr.logo_read(per)
    check("R LOGO range by hand [1/6, 1/3]",
          abs(logo["range"][0] - 1 / 6) < 1e-9
          and abs(logo["range"][1] - 1 / 3) < 1e-9)
    check("R largest share by hand (0.5)",
          abs(logo["largest_share"] - 0.5) < 1e-9)
    sz = pr.sizing_read({"lb": 0.1649,
                         "se_clustered": 0.02,
                         "games": 100},
                        SETTINGS["read"])
    R = (0.1 / 2.4866) ** 2 - 0.009 ** 2
    n_hand = math.ceil(100 * 0.02 ** 2 / R)
    check("R sizing by hand (n == %d)" % n_hand,
          sz["n"] == n_hand == 27, str(sz))
    sz0 = pr.sizing_read({"lb": 0.05,
                          "se_clustered": 0.02,
                          "games": 100},
                         SETTINGS["read"])
    check("R sizing Delta <= 0 -> no finite n",
          sz0["n"] is None)

    # end-to-end main() on planted rows
    jobs = [
        {"snap": "A", "game": "g1", "player": 1,
         "branch": "M", "prior_pick": 0, "teacher_pick": 1,
         "class": "contested", "z": 2.0,
         "z_nonfinite": False},
        {"snap": "B", "game": "g2", "player": 2,
         "branch": "M", "prior_pick": 0, "teacher_pick": 1,
         "class": "newly_contested", "z": 4.0,
         "z_nonfinite": False},
        {"snap": "C", "game": "g2", "player": 2,
         "branch": "M", "prior_pick": 0, "teacher_pick": 1,
         "class": "contested", "z": 999.0,
         "z_nonfinite": True}]
    rows = []
    for w, (ot, op) in enumerate(((1, -1), (1, 1))):
        rows.append(label_row("A", 1, w, ot, 30))
        rows.append(label_row("A", 0, w, op, 30))
    for w, (ot, op) in enumerate(((1, -1), (-1, -1))):
        rows.append(label_row("B", 1, w, ot, 30))
        rows.append(label_row("B", 0, w, op, 30))
    rows.append(label_row("C", 1, 0, 1, 70))   # post-cap
    rows.append(label_row("C", 0, 0, -1, 40))
    jp = os.path.join(tmp, "jobs.jsonl")
    lp = os.path.join(tmp, "labels.jsonl")
    with open(jp, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(lp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    grows = []
    for i, g in enumerate(games):
        grows.append({"seed": i + 1, "seat": 1,
                      "winner": 1, "draw": False,
                      "secs": 10.0, "gamename": g})
    gp = os.path.join(tmp, "games.jsonl")
    with open(gp, "w") as f:
        for r in grows:
            f.write(json.dumps(r) + "\n")
    gr = os.path.join(tmp, "games_report.json")
    with open(gr, "w") as f:
        json.dump({"wall_s": {"n": 4, "mean": 10.0,
                              "p95": 10.0, "max": 10.0},
                   "teacher_timeouts": 0}, f)
    jo = os.path.join(tmp, "read.json")
    r = run([sys.executable,
             os.path.join(S1, "pilot_read.py"),
             "--jobs", jp, "--labels", lp,
             "--games-rows", gp, "--games-report", gr,
             "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--json-out", jo])
    check("R read main runs", r.returncode == 0,
          r.stderr[-300:] if r.returncode else "")
    out = json.load(open(jo))
    check("R cap-aligned diffs: total gain 0.25 by hand",
          abs(out["total"]["gain"]["gain"] - 0.25) < 1e-9,
          str(out["total"]["gain"]["gain"]))
    check("R class gains 0.125 / 0.125 by hand",
          abs(out["classes"]["contested"]["gain"]
              ["gain"] - 0.125) < 1e-9
          and abs(out["classes"]["newly_contested"]
                  ["gain"]["gain"] - 0.125) < 1e-9)
    check("R post-cap win scores 0 (job C in >3.5 with "
          "job B; band edge 0.25 == (0.5 + 0.0)/2, not "
          "0.75)", out["bands"][">3.5"]["jobs"] == 2
          and abs(out["bands"][">3.5"]["edge"] - 0.25)
          < 1e-9, str(out["bands"].get(">3.5")))
    check("R STOP evaluation: DO NOT STOP on planted "
          "positive", out["stop"]["STOP"] is False)
    check("R read prints the STOP line",
          "DO NOT STOP" in r.stdout)


def test_stop_onesided(tmp):
    games = ["s%d" % i for i in range(1, 101)]
    jobs = []
    rows = []
    k = 0
    for g in games[:4]:
        for _ in range(2):
            k += 1
            snap = "T%d" % k
            jobs.append({"snap": snap, "game": g,
                         "player": 1, "branch": "M",
                         "prior_pick": 0, "teacher_pick": 1,
                         "class": "contested", "z": 2.0,
                         "z_nonfinite": False})
            for w in range(25):
                rows.append(label_row(
                    snap, 1, w, 1 if w < 14 else -1, 30))
                rows.append(label_row(snap, 0, w, -1, 30))
    jp = os.path.join(tmp, "jobs.jsonl")
    lp = os.path.join(tmp, "labels.jsonl")
    with open(jp, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(lp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    gp = os.path.join(tmp, "games.jsonl")
    with open(gp, "w") as f:
        for i, g in enumerate(games):
            f.write(json.dumps(
                {"seed": i + 1, "seat": 1, "winner": 1,
                 "draw": False, "secs": 10.0,
                 "gamename": g}) + "\n")
    gr = os.path.join(tmp, "games_report.json")
    with open(gr, "w") as f:
        json.dump({"wall_s": {"n": 100, "mean": 10.0,
                              "p95": 10.0, "max": 10.0},
                   "teacher_timeouts": 0}, f)
    jo = os.path.join(tmp, "read.json")
    r = run([sys.executable,
             os.path.join(S1, "pilot_read.py"),
             "--jobs", jp, "--labels", lp,
             "--games-rows", gp, "--games-report", gr,
             "--settings",
             os.path.join(S1, "settings_pilot.json"),
             "--json-out", jo])
    check("T stop-plant read runs", r.returncode == 0,
          r.stderr[-300:] if r.returncode else "")
    out = json.load(open(jo))
    g = out["total"]["gain"]
    check("T bootstrap 95th percentile 0.0784 < 0.0849 "
          "while the 97.5th is 0.0896 >= 0.0849",
          abs(g["ub"] - 0.0784) < 1e-9
          and abs(g["ci"][1] - 0.0896) < 1e-9,
          "ub(95th)=%.4f ci_hi(97.5th)=%.4f"
          % (g["ub"], g["ci"][1]))
    check("T STOP fires on the one-sided bound",
          out["stop"]["STOP"] is True
          and "STOP (no Step 2)" in r.stdout)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_jobs(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        test_games_report(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        test_read(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        test_stop_onesided(tmp)
    print("fx_pilot_python: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
