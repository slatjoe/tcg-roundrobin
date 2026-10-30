#!/usr/bin/env python3
"""Step 2+3 fleet writer->reader round trips.

REAL shapes throughout (field sets read off the
published round-9 Stage 3 rows and the published
Step 1 label rows): driver rows are planted per
block, fleet_games_report.py (the writer) builds
pairing.json + games_report.json from them, and
fleet_read.py (the reader) consumes the writer's OWN
output -- never a hand-built pairing. Gamenames are
ARM-LOCAL: the teacher and raw rows of a pair carry
DIFFERENT gamenames, as in the real fleets; pairing
is by (seed, seat) and the round trip proves it.

Cases:
 SMALL  6 planted pairs covering every pairing
        status: identical pair (diff 0), teacher-win
        pair (+1), draw pair (capped shape: winner 0,
        capped/draw true; primary 0, delta05 0, life
        differential +1 by p1life/p2life),
        teacher-timeout pair (scored as a teacher
        LOSS), raw-timeout pair with a rerun row that
        also times out (dropped_raw_timeout), raw
        no_result pair (excluded). One canary stat row
        planted and counted by name.
 VERDICTS  122-pair populations through the full
        pipeline: CONVERTS (+ impeachment print),
        DOES NOT CONVERT, INCONCLUSIVE at 3 teacher
        timeouts (3/122 > 0.02) with the band verdict
        standing at 2, INCONCLUSIVE at 3 excluded
        pairs with the verdict standing at 2.
 CO-READ  jobs built by build_fleet_jobs.py ITSELF
        from planted snap-index + stat rows; label
        rows planted in the published s2 shape (key
        set asserted equal to a published row's).
        Hand-computed: per-game totals [1.0, 0.5, 0.5,
        0.0] -> gain 0.5, SE 0.20412, two-sample
        z = 2.1295 -> STEP 2 GATE: PASS. A second
        plant ([0.1, 0, 0, 0]) -> z < 0 -> NOT PASSED.
        Attribution: numeric ratio at Delta = 1.0 (CI
        excludes 0); the two guarded branches driven
        directly (unstable / n/a).
"""
import contextlib
import gzip
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
STEP2 = os.path.join(R10, "code", "step2")
sys.path.insert(0, STEP2)

import fleet_games_report as FGR  # noqa: E402
import fleet_read as FR  # noqa: E402
import build_fleet_jobs as BFJ  # noqa: E402

SETTINGS_P = os.path.join(STEP2, "settings_fleet.json")
SETTINGS = json.load(open(SETTINGS_P))
TT = dict(SETTINGS["teacher_tuple"])
TT["pinned"] = 1
LT = dict(SETTINGS["label_tuple"])

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def drow(seed, seat, gamename, winner, capped=False,
         draw=False, p1=40, p2=40, invalid=None):
    r = {"seed": seed, "seat": seat, "gamename": gamename,
         "winner": winner, "capped": capped, "draw": draw,
         "p1life": p1, "p2life": p2, "turns": 40,
         "decisions": 120, "secs": 12.5, "arm": "x",
         "gamelog_sha": "0" * 64}
    if invalid is not None:
        r["invalid"] = invalid
    return r


def srow(game, **kw):
    r = {"game": game, "teacher": 1, "overturn": 1,
         "branch": "root", "player": 1, "turn": 7,
         "prior_pick": 0, "pick": 1,
         "priors": [0.4, 0.35, 0.25], "mean_diff": 1.0,
         "se_diff": 0.5, "setting": dict(TT)}
    r.update(kw)
    return r


BLOCKS = ["t1a", "t1b", "t2a", "t2b",
          "r1a", "r1b", "r2a", "r2b"]


def write_out(base, rows_by_block, stats_by_block,
              rerun_rows=None):
    os.makedirs(base, exist_ok=True)
    for blk in BLOCKS:
        with open(os.path.join(base, "games_%s.jsonl" % blk),
                  "w") as f:
            for r in rows_by_block.get(blk, []):
                f.write(json.dumps(r) + "\n")
        logdir = os.path.join(base, "games_%s_log" % blk)
        os.makedirs(logdir, exist_ok=True)
        with open(os.path.join(logdir, "search_stats.jsonl"),
                  "w") as f:
            for r in stats_by_block.get(blk, []):
                f.write(json.dumps(r) + "\n")
    for blk, rows in (rerun_rows or {}).items():
        with open(os.path.join(
                base, "games_%s_rerun.jsonl" % blk), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")


def run_report(base, pairing_only=False):
    argv = ["fleet_games_report.py", "--out-dir", base,
            "--settings", SETTINGS_P,
            "--json-out", os.path.join(base,
                                       "games_report.json")]
    if pairing_only:
        argv.append("--pairing-only")
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = FGR.main()
    finally:
        sys.argv = old
    assert rc == 0, "games report rc %s" % rc
    name = "pairing_draft.json" if pairing_only \
        else "pairing.json"
    return json.load(open(os.path.join(base, name)))


def run_read(base, expect=None, primary_only=True,
             extra=None):
    argv = ["fleet_read.py", "--pairing",
            os.path.join(base, "pairing.json"),
            "--games-report",
            os.path.join(base, "games_report.json"),
            "--settings", SETTINGS_P,
            "--json-out", os.path.join(base,
                                       "fleet_read.json")]
    if expect is not None:
        argv += ["--expect-pairs", str(expect)]
    if primary_only:
        argv.append("--primary-only")
    argv += (extra or [])
    old = sys.argv
    sys.argv = argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = FR.main()
    finally:
        sys.argv = old
    assert rc == 0, "fleet read rc %s" % rc
    return (json.load(open(os.path.join(base,
                                        "fleet_read.json"))),
            buf.getvalue())


TMP = tempfile.mkdtemp(prefix="fx_fleet_read_")

# =====================================================================
# SMALL -- every pairing status, hand-computed read
# =====================================================================
d = os.path.join(TMP, "small")
rows = {
    # seat 1, block t1a/r1a
    "t1a": [drow(26001, 1, "511111111", 1),
            drow(26002, 1, "511111112", 1),
            drow(26003, 1, "511111113", 0, capped=True,
                 draw=True, p1=30, p2=25)],
    "r1a": [drow(26001, 1, "611111111", 1),
            drow(26002, 1, "611111112", 2),
            drow(26003, 1, "611111113", 0, capped=True,
                 draw=True, p1=20, p2=28)],
    # seat 2, block t2a/r2a
    "t2a": [drow(26001, 2, "522222221", 0,
                 invalid="timeout"),
            drow(26002, 2, "522222222", 2),
            drow(26003, 2, "522222223", 2)],
    "r2a": [drow(26001, 2, "622222221", 2),
            drow(26002, 2, "622222222", 0,
                 invalid="timeout"),
            drow(26003, 2, "622222223", 0,
                 invalid="no_result")],
}
stats = {
    "t1a": [srow("511111111"), srow("511111112"),
            srow("511111113"),
            {"fallback": "canary", "game": "511111111"}],
    "t2a": [srow("522222221"), srow("522222222"),
            srow("522222223")],
}
rerun = {"r2a": [drow(26002, 2, "622222229", 0,
                      invalid="timeout")]}
write_out(d, rows, stats, rerun)
pairing = run_report(d)
status = {(p["seed"], p["seat"]): p["status"]
          for p in pairing["pairs"]}
check("SMALL pairing forms by (seed, seat) across "
      "arm-local gamenames", status == {
          (26001, 1): "scored", (26002, 1): "scored",
          (26003, 1): "scored",
          (26001, 2): "teacher_timeout",
          (26002, 2): "dropped_raw_timeout",
          (26003, 2): "excluded"},
      "statuses: %s" % (status,))
out, txt = run_read(d, expect=6)
check("SMALL primary mean over scored pairs = "
      "(0 + 1 + 0 - 1)/4 = 0.0 (timeout scored as a "
      "teacher loss)", abs(out["primary"]["mean_diff"]
                           - 0.0) < 1e-12,
      "mean %s" % out["primary"]["mean_diff"])
check("SMALL delta05 mean = 0.0 (the draw pair prices "
      "0.5 both arms)", abs(out["delta05"]["mean_diff"])
      < 1e-12)
check("SMALL life differential = +0.25 (the capped "
      "draw decided on life)", abs(
          out["delta_lifediff"]["mean_diff"] - 0.25) < 1e-12,
      "life %s" % out["delta_lifediff"]["mean_diff"])
check("SMALL drop-timeout sensitivity = (0 + 1 + 0)/3",
      abs(out["sensitivity_primary"]["mean_diff"]
          - 1.0 / 3.0) < 1e-9)
check("SMALL reconciliation: canary counted by name "
      "(1), stat rows recounted (6)",
      out["reconciliation"]["canary_refusal_rows"] == 1
      and out["reconciliation"]["teacher_stat_rows"] == 6)
check("SMALL verdict INCONCLUSIVE (timeout rate 1/6 "
      "and out rate 2/6 both > 0.02 at this N -- the "
      "registered rule, scale-free)",
      out["verdict"] == "INCONCLUSIVE", out["verdict"])

# =====================================================================
# VERDICTS -- 122-pair populations
# =====================================================================
def fleet_rows(fn):
    """fn(seed, seat) -> (t_winner, r_winner, t_inv,
    r_inv). Builds all 8 blocks + stat rows."""
    rows = {b: [] for b in BLOCKS}
    stats = {b: [] for b in BLOCKS}
    for seed in range(26001, 26062):
        half = "a" if seed <= 26031 else "b"
        for seat in (1, 2):
            tw, rw, ti, ri = fn(seed, seat)
            tb, rb = "t%s%s" % (seat, half), "r%s%s" % (seat,
                                                        half)
            tg = "5%d%d" % (seed, seat)
            rg = "6%d%d" % (seed, seat)
            rows[tb].append(drow(seed, seat, tg, tw,
                                 invalid=ti))
            rows[rb].append(drow(seed, seat, rg, rw,
                                 invalid=ri))
            if ti is None:
                stats[tb].append(srow(tg))
    return rows, stats


def verdict_case(name, fn, want_verdict, want_text=None):
    d = os.path.join(TMP, name)
    rows, stats = fleet_rows(fn)
    write_out(d, rows, stats)
    run_report(d)
    out, txt = run_read(d)
    ok = out["verdict"] == want_verdict
    if want_text:
        ok = ok and want_text in txt
    check("VERDICT %s -> %s" % (name, want_verdict), ok,
          "got %s; mean %s" % (out["verdict"],
                               out["primary"]["mean_diff"]))
    return out, txt


verdict_case("v_converts",
             lambda s, seat: (seat, 3 - seat, None, None),
             "CONVERTS", "IMPEACHMENT")
verdict_case("v_null",
             lambda s, seat: ((seat, 3 - seat, None, None)
                              if s % 2 == 0 else
                              (3 - seat, seat, None, None)),
             "DOES NOT CONVERT")


def with_timeouts(n):
    def fn(s, seat):
        if seat == 1 and s <= 26001 + n - 1:
            return (0, 2, "timeout", None)
        return (seat, 3 - seat, None, None)
    return fn


verdict_case("v_inc_timeouts3", with_timeouts(3),
             "INCONCLUSIVE")
verdict_case("v_timeouts2_stand", with_timeouts(2),
             "CONVERTS")


def with_excluded(n):
    def fn(s, seat):
        if seat == 1 and s <= 26001 + n - 1:
            return (seat, 0, None, "no_result")
        return (seat, 3 - seat, None, None)
    return fn


verdict_case("v_inc_excluded3", with_excluded(3),
             "INCONCLUSIVE")
verdict_case("v_excluded2_stand", with_excluded(2),
             "CONVERTS")

# =====================================================================
# CO-READ -- jobs built by the real builder; hand-computed gate
# =====================================================================
PUB_KEYS = None
with gzip.open(os.path.join(
        R10, "data", "step1", "l3",
        "labels_shard0_p1.jsonl.gz"), "rt") as f:
    PUB_KEYS = set(json.loads(f.readline()).keys())


def build_coread(name, world_diffs):
    """world_diffs: {game_idx: [(t_outcome, p_outcome),
    ...]} -- one job per game over 4 teacher games."""
    d = os.path.join(TMP, name)
    games = ["93333333%d" % i for i in range(1, 5)]
    rows = {"t1a": [], "r1a": []}
    stats = {"t1a": []}
    for i, gname in enumerate(games):
        seed = 26001 + i
        rows["t1a"].append(drow(seed, 1, gname, 1))
        rows["r1a"].append(drow(seed, 1, "8" + gname[1:], 2))
        stats["t1a"].append(srow(gname))
    write_out(d, rows, stats)
    run_report(d)
    # snap index + snap dirs (the builder's inputs)
    logdir = os.path.join(d, "games_t1a_log")
    snaps_dir = os.path.join(logdir, "snaps")
    os.makedirs(snaps_dir, exist_ok=True)
    with open(os.path.join(snaps_dir,
                           "teacher_snap_index.jsonl"),
              "w") as f:
        for gname in games:
            snap = gname + "_t7"
            os.makedirs(os.path.join(snaps_dir, snap),
                        exist_ok=True)
            f.write(json.dumps({
                "snap": snap, "game": gname,
                "cands": [0, 1, 2], "teacher_pick": 1,
                "prior_pick": 0, "branch": "root",
                "player": 1, "turn": 7}) + "\n")
    argv = ["build_fleet_jobs.py",
            "--stream", "%s=%s" % (
                snaps_dir, os.path.join(
                    snaps_dir, "teacher_snap_index.jsonl")),
            "--stats", os.path.join(logdir,
                                    "search_stats.jsonl"),
            "--settings", SETTINGS_P,
            "--out", os.path.join(d, "jobs_all.jsonl"),
            "--shard-prefix", os.path.join(d, "jobs_shard"),
            "--report", os.path.join(d, "jobs_report.json")]
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = BFJ.main()
    finally:
        sys.argv = old
    assert rc == 0, "jobs build rc %s" % rc
    jobs = [json.loads(l) for l in
            open(os.path.join(d, "jobs_all.jsonl"))]
    assert len(jobs) == 4, "jobs %d" % len(jobs)
    # label rows, published key set
    lrows = []
    for job in jobs:
        gi = games.index(str(job["game"]))
        for w, (to_, po_) in enumerate(world_diffs[gi]):
            for cand, oc in ((1, to_), (0, po_)):
                lrows.append({
                    "snap": job["snap"], "game": job["game"],
                    "cand": cand, "world": w,
                    "teacher_pick": 1, "prior_pick": 0,
                    "setting": dict(LT),
                    "result": {
                        "finished": 1, "outcome": oc,
                        "turns": 40,
                        "winner": 1 if oc > 0 else 2,
                        "fallbacks": 0, "hooks": 100,
                        "horizon": 0, "child_state": "x",
                        "det_persisted": True}})
    assert all(set(r.keys()) == PUB_KEYS for r in lrows), \
        "planted label row key set != published"
    with open(os.path.join(d, "labels_all.jsonl"), "w") as f:
        for r in lrows:
            f.write(json.dumps(r) + "\n")
    out, txt = run_read(
        d, expect=4, primary_only=False,
        extra=["--jobs", os.path.join(d, "jobs_all.jsonl"),
               "--labels", os.path.join(d, "labels_all.jsonl"),
               "--games-rows",
               os.path.join(d, "games_t1a.jsonl")])
    return out, txt


out, txt = build_coread("coread_pass", {
    0: [(1, -1)],
    1: [(1, -1), (-1, -1)],
    2: [(1, -1), (-1, -1)],
    3: [(-1, -1)]})
cr = out["coread"]
check("CO-READ plant label key set == published row "
      "key set", PUB_KEYS == {"cand", "game", "prior_pick",
                              "result", "setting", "snap",
                              "teacher_pick", "world"})
check("CO-READ gain over per-game totals [1.0, 0.5, "
      "0.5, 0.0] = 0.5", abs(cr["total"]["gain"]["gain"]
                             - 0.5) < 1e-9,
      "gain %s" % cr["total"]["gain"]["gain"])
check("CO-READ SE = sd/sqrt(4) = 0.20412",
      abs(cr["total"]["gain"]["se_clustered"] - 0.204124)
      < 1e-4, "se %s" % cr["total"]["gain"]["se_clustered"])
gate = cr["step2_gate"]
check("STEP 2 GATE hand-computed: z = (0.5 - 0.0649)/"
      "sqrt(0.20412^2 + 0.0090^2) = 2.1295 -> PASS",
      gate["PASS"] is True and abs(gate["z"] - 2.1295)
      < 5e-3, "z %s PASS %s" % (gate["z"], gate["PASS"]))
check("ATTRIBUTION at fleet Delta = 1.0 (CI excludes "
      "0): ratio = 0.5 numeric",
      cr["attribution"]["ratio_to_delta"] is not None
      and abs(cr["attribution"]["ratio_to_delta"] - 0.5)
      < 1e-9, "attr %s" % (cr["attribution"],))

out2, _ = build_coread("coread_fail", {
    0: [(1, -1)] + [(-1, -1)] * 9,
    1: [(-1, -1)], 2: [(-1, -1)], 3: [(-1, -1)]})
gate2 = out2["coread"]["step2_gate"]
check("CO-READ FAIL plant ([0.1, 0, 0, 0] -> gain "
      "0.025, z < 0): gate does NOT pass",
      gate2["PASS"] is False and gate2["z"] < 0,
      "z %s" % gate2["z"])

# ---- attribution guard branches, driven directly ----
jobs = [json.loads(l) for l in open(os.path.join(
    TMP, "coread_pass", "jobs_all.jsonl"))]
lrows = [json.loads(l) for l in open(os.path.join(
    TMP, "coread_pass", "labels_all.jsonl"))]
games4 = ["93333333%d" % i for i in range(1, 5)]
grep4 = {"teacher_timeouts": 0}
for fdelta, fci, want_note in (
        (0.05, [-0.01, 0.11], "unstable (Δ CI includes 0)"),
        (-0.02, [-0.05, 0.01], "n/a (Δ ≤ 0)")):
    fp = {"primary": {"mean_diff": fdelta, "ci": fci},
          "verdict": "DOES NOT CONVERT"}
    co, _lines = FR.coread(jobs, lrows, games4, grep4,
                           SETTINGS, fp)
    check("ATTRIBUTION guard: Delta %s CI %s -> %r, "
          "ratio null" % (fdelta, fci, want_note),
          co["attribution"]["ratio_to_delta"] is None
          and co["attribution"]["ratio_note"] == want_note,
          "attr %s" % (co["attribution"],))

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
