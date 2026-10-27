#!/usr/bin/env python3
"""fx_stage3_analyze: stage3_analyze.py, four cases.

CASE A (bands; round-trips the REAL games report): the
fx_stage3_games_report planted population WITHOUT seed
23003 (4 pairs). Hand-computed: diffs (23001,1) 0,
(23002,1) 0, (23001,2) -1, (23002,2) -1 -> primary mean
-0.5; every seed cluster carries exactly one -1 pair, so
the clustered CI is exactly [-0.5, -0.5] -> HARMS.
lifediff diffs (0, +1, -1, -1) -> -0.25; delta05 diffs
(0, +0.5, -1, -0.5) -> -0.25; per-seat seat1 0.0, seat2
-1.0; pairs_scored == 4.

CASE B (timeout + impeachment + inconclusive): synthetic
pairing.json + minimal games_report.json planted directly
(Case A already round-trips the real report): 400 pairs,
seeds 23001-23200 x 2 seats; 9 pairs (seeds 23001-23009,
seat 1) are teacher_timeout with a raw loss (diff 0); the
other 391 pairs are teacher win / raw loss (diff +1).
Primary mean = 391/400 = 0.9775 (> +0.25 -> impeachment
BEFORE the verdict). Teacher timeout rate 9/400 = 0.0225
> 0.02 -> verdict INCONCLUSIVE (overrides the CI, whose
lower bound is > 0). LOGO range = [389/398, 390/398]
(removing a normal seed / a timeout seed). NOTE: the
registration text's planted figures for this case (mean
+1.0, LOGO [1.0, 1.0]) are arithmetically incompatible
with 9 teacher-timeout pairs inside the same scored
population -- a timeout pair scores diff 0 here, never
+1 -- so this fixture asserts the consistent values and
the build report flags the discrepancy.
Sensitivity (drop the 9 timeout pairs) = 391/391 = 1.0.

CASE C (converts edge): 400 pairs; 100 seeds have both
pairs diff +1, 100 seeds both diff 0 -> mean +0.5,
seed-clustered CI lower > 0 -> CONVERTS (bootstrap seeded
20261027, deterministic; verified empirically).

CASE D (dropped pair): Case A population + a 5th pair
(23003: teacher completed W, raw timeout, rerun timeout)
via the REAL report -> status dropped_raw_timeout,
pairs_scored stays 4, primary unchanged (-0.5), dropped
listed with reason.
Run: python3 fx_stage3_analyze.py (own temp dirs)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
ANALYZER = os.path.join(CODE, "stage3_analyze.py")
SETTINGS = os.path.join(CODE, "settings_stage3.json")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def approx(x, y, tol=1e-9):
    return x is not None and abs(x - y) <= tol


spec = importlib.util.spec_from_file_location(
    "fxgr", os.path.join(HERE, "fx_stage3_games_report.py"))
fxgr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fxgr)


def run_analyzer(tmp, expect_pairs):
    out = os.path.join(tmp, "stage3_read.json")
    r = subprocess.run(
        [sys.executable, ANALYZER,
         "--pairing", os.path.join(tmp, "pairing.json"),
         "--games-report", os.path.join(tmp, "games_report.json"),
         "--settings", SETTINGS,
         "--expect-pairs", str(expect_pairs),
         "--json-out", out],
        capture_output=True, text=True)
    read = json.load(open(out)) if os.path.exists(out) \
        and r.returncode == 0 else None
    return r, read


def plant(tmp, pairs):
    pairing = {"pairs": pairs,
               "counts": {"pairs_attempted": len(pairs),
                          "by_status": {}},
               "stat_files": [], "rerun_files": []}
    json.dump(pairing, open(os.path.join(tmp, "pairing.json"), "w"))
    grep = {"teacher_stat_rows": 0,
            "tuple_audit": {"ok": True, "bad_rows": 0,
                            "malformed_pin_aborts": 0}}
    json.dump(grep, open(os.path.join(tmp, "games_report.json"), "w"))


def prow(seed, seat, trow, rrow, status):
    return {"seed": seed, "seat": seat,
            "teacher": {"file": "games_t1a.jsonl",
                        "gamename": trow.get("gamename"),
                        "row": trow},
            "raw": {"file": "games_r1a.jsonl",
                    "gamename": rrow.get("gamename"),
                    "row": rrow},
            "status": status, "reason": None}


def winrow(seed, seat, arm, gn):
    return {"seed": seed, "arm": arm, "seat": seat,
            "gamename": gn, "winner": seat, "draw": 0,
            "capped": 0, "p1life": 20, "p2life": 5}


def lossrow(seed, seat, arm, gn):
    return {"seed": seed, "arm": arm, "seat": seat,
            "gamename": gn, "winner": 3 - seat, "draw": 0,
            "capped": 0, "p1life": 0, "p2life": 15}


def case_b(tmp):
    pairs = []
    for seed in range(23001, 23201):
        for seat in (1, 2):
            gn = "fxb%d_%d" % (seed, seat)
            if seat == 1 and seed <= 23009:
                t = {"seed": seed, "arm": "teacher", "seat": 1,
                     "invalid": "timeout"}
                pairs.append(prow(seed, seat, t,
                                  lossrow(seed, seat, "raw", gn + "r"),
                                  "teacher_timeout"))
            else:
                pairs.append(prow(
                    seed, seat, winrow(seed, seat, "teacher", gn),
                    lossrow(seed, seat, "raw", gn + "r"), "scored"))
    plant(tmp, pairs)
    return run_analyzer(tmp, 400)


def case_c(tmp):
    pairs = []
    for seed in range(23001, 23201):
        for seat in (1, 2):
            gn = "fxc%d_%d" % (seed, seat)
            if seed <= 23100:
                pairs.append(prow(
                    seed, seat, winrow(seed, seat, "teacher", gn),
                    lossrow(seed, seat, "raw", gn + "r"), "scored"))
            else:
                pairs.append(prow(
                    seed, seat, lossrow(seed, seat, "teacher", gn),
                    lossrow(seed, seat, "raw", gn + "r"), "scored"))
    plant(tmp, pairs)
    return run_analyzer(tmp, 400)


def main():
    # ---- CASE A ------------------------------------------------
    tmp = tempfile.mkdtemp()
    _r, _rep, _p = fxgr.build(tmp, variant="no_timeout")
    r, read = run_analyzer(tmp, 4)
    check("A: analyzer exit 0 (real report round-trip)",
          r.returncode == 0, r.stdout.strip()[-200:] if r.returncode else "")
    if read:
        check("A: primary mean == -0.5, pairs_scored 4, CI "
              "exactly [-0.5, -0.5]",
              approx(read["primary"]["mean_diff"], -0.5)
              and read["primary"]["pairs_scored"] == 4
              and read["primary"]["ci"] == [-0.5, -0.5],
              "got %r" % read["primary"])
        check("A: verdict HARMS", read["verdict"] == "HARMS",
              "got %r" % read["verdict"])
        check("A: lifediff == -0.25, delta05 == -0.25",
              approx(read["delta_lifediff"]["mean_diff"], -0.25)
              and approx(read["delta05"]["mean_diff"], -0.25))
        check("A: per-seat seat1 0.0 / seat2 -1.0",
              approx(read["per_seat"]["1"]["mean_diff"], 0.0)
              and approx(read["per_seat"]["2"]["mean_diff"], -1.0))
        check("A: canary reconciliation prints the class by "
              "name with count 1",
              "R14 root-canary refusal records" in r.stdout
              and read["reconciliation"]["canary_refusal_rows"] == 1)
    # ---- CASE B -------------------------------------------------
    r, read = case_b(tempfile.mkdtemp())
    check("B: analyzer exit 0", r.returncode == 0,
          r.stdout.strip()[-200:] if r.returncode else "")
    if read:
        check("B: primary mean == 391/400 = 0.9775",
              approx(read["primary"]["mean_diff"], 391 / 400),
              "got %r" % read["primary"]["mean_diff"])
        check("B: timeout rate 9/400 = 0.0225 -> INCONCLUSIVE "
              "overrides CI lower > 0",
              approx(read["teacher_timeout_rate"], 0.0225)
              and read["primary"]["ci"][0] > 0
              and read["verdict"] == "INCONCLUSIVE",
              "verdict=%r ci=%r" % (read["verdict"],
                                    read["primary"]["ci"]))
        check("B: sensitivity (drop 9 timeout pairs) == 1.0",
              approx(read["sensitivity_primary"]["mean_diff"], 1.0)
              and read["sensitivity_primary"]
                     ["teacher_timeout_pairs_dropped"] == 9)
        check("B: impeachment LOGO range == [389/398, 390/398]",
              read["impeachment"] is not None
              and approx(read["impeachment"]["logo_range"][0],
                         389 / 398, 1e-9)
              and approx(read["impeachment"]["logo_range"][1],
                         390 / 398, 1e-9),
              "got %r" % (read["impeachment"] or {}).get("logo_range"))
        check("B: impeachment printed BEFORE the VERDICT line, "
              "verdict last",
              r.stdout.index("IMPEACHMENT") < r.stdout.index("VERDICT:")
              and r.stdout.strip().splitlines()[-1].startswith("VERDICT:"))
    # ---- CASE C -------------------------------------------------
    r, read = case_c(tempfile.mkdtemp())
    check("C: mean +0.5, CI lower > 0 -> CONVERTS",
          r.returncode == 0 and read
          and approx(read["primary"]["mean_diff"], 0.5)
          and read["primary"]["ci"][0] > 0
          and read["verdict"] == "CONVERTS",
          "got %r" % ((read and (read["primary"], read["verdict"])),))
    # ---- CASE D -------------------------------------------------
    tmp = tempfile.mkdtemp()
    fxgr.build(tmp, variant="dropped")
    # 'dropped' = the Case A population + pair (23003,1):
    # teacher completed W, raw timeout, rerun timeout.
    r, read = run_analyzer(tmp, 5)
    check("D: pairs_scored stays 4, dropped listed, primary "
          "unchanged (-0.5)",
          r.returncode == 0 and read
          and read["primary"]["pairs_scored"] == 4
          and approx(read["primary"]["mean_diff"], -0.5)
          and len(read["dropped"]) == 1
          and read["dropped"][0]["seed"] == 23003,
          "got %r" % ((read and (read["primary"], read["dropped"])),))
    print("FX-STAGE3-ANALYZE: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
