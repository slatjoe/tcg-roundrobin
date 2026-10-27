#!/usr/bin/env python3
"""fx_s3_l3_roundtrip checker: s2_label_main.php (Stage 3
pins, MEAS_SEED=50055001) against this dir's cand-parity
stub play_game.php, then the genuine rows through the
REAL stage3_attr_analyze.py.

Hand-computed reads (stub docstring): fxA diff 0.4, fxB
diff 0 -> primary / draw05 / lifediff mean diffs all 0.2.
Planted games report: overturns_per_game 1.0 -> per-game
gain = 0.2 x 1.0 = 0.2. Planted Stage 3 read:
primary.mean_diff = 0.05, CI [0.01, 0.09] (excludes 0)
-> ratio_to_delta = 0.2 / 0.05 = 4.0 exactly, printed
plain. No tripwire (gain 0.2 not > 0.25; mean 0.2 not
> 0.20). Stamp audit over the genuine rows: rows ==
200, bad == 0; the JSON carries "attribution" (no
PROCEED/STOP verdict).
RATIO GUARD cases (claude-reply-c924b19 sec.4), same
genuine rows, two more planted Stage 3 reads:
  delta -0.01, CI [-0.03, 0.01] -> prints "n/a (Δ ≤ 0)"
    with the CI beside it; ratio_to_delta is null and
    ratio_note set in the JSON.
  delta +0.01, CI [-0.02, 0.04] -> prints "unstable
    (Δ CI includes 0)" with the CI beside it; ratio null.
Usage: check_fx_s3_l3.py <workdir>"""
import json
import os
import subprocess
import sys
import tempfile

FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def approx(x, y, tol=1e-9):
    return x is not None and abs(x - y) <= tol


def main():
    work = sys.argv[1]
    rows = [json.loads(l) for l in open(os.path.join(work, "out.jsonl"))]
    stats = [json.loads(l) for l in open(os.path.join(work, "stats.jsonl"))]
    cfgs = [json.loads(l) for l in open(os.path.join(work, "cfg.jsonl"))]
    check("row count = 2 jobs x 2 selected x 50", len(rows) == 200,
          "rows=%d" % len(rows))
    here = os.path.dirname(os.path.abspath(__file__))
    code = os.path.join(here, "..", "..", "code")
    LT = json.load(open(os.path.join(
        code, "settings_stage3.json")))["label_tuple"]
    check("every row stamped with the Stage 3 label tuple",
          all(r.get("setting") == LT for r in rows))
    check("cfg forwarded per job (W=50, horizon 62, hooks "
          "8000, deadline 180, pair va)",
          len(cfgs) == 2 and all(
              c["W"] == 50 and c["horizon"] == 62
              and c["hookBudget"] == 8000 and c["deadlineS"] == 180
              and c["pair"] == "va" for c in cfgs))
    check("stat rows carry teacher_pick + setting",
          len(stats) == 2 and all(
              "teacher_pick" in s and s.get("setting") == LT
              for s in stats))
    for name in ("badk", "nosetting"):
        err = open(os.path.join(work, name + ".stderr")).read()
        check("%s aborted (ABORT logged, no rows)" % name,
              "ABORT:" in err
              and not os.path.exists(os.path.join(
                  work, name + ".out.jsonl")))
    # ---- round-trip: genuine rows -> stage3_attr_analyze --
    tmp = tempfile.mkdtemp()
    grep = {"overturn_rows": 4, "games_completed": 4,
            "overturns_per_game": 1.0, "thin_prior_rate": 0.01,
            "overturn_rate": 0.02,
            "teacher_outcomes_draw_scored": {
                "W": 2, "D": 1, "L": 1, "points": 2.5,
                "points_per_game": 0.625}}
    gp = os.path.join(tmp, "games_report.json")
    json.dump(grep, open(gp, "w"))
    s3r = {"primary": {"pairs_scored": 400, "mean_diff": 0.05,
                       "ci": [0.01, 0.09]}}
    sp = os.path.join(tmp, "stage3_read.json")
    json.dump(s3r, open(sp, "w"))
    def run_attr(s3r_obj, tag):
        spx = os.path.join(tmp, "stage3_read_%s.json" % tag)
        json.dump(s3r_obj, open(spx, "w"))
        outx = os.path.join(tmp, "attr_read_%s.json" % tag)
        rx = subprocess.run(
            [sys.executable,
             os.path.join(code, "stage3_attr_analyze.py"),
             "--jobs", os.path.join(here, "jobs_ok.jsonl"),
             "--labels", os.path.join(work, "out.jsonl"),
             "--games-report", gp, "--stage3-read", spx,
             "--settings", os.path.join(code,
                                         "settings_stage3.json"),
             "--expect-rows", "50", "--json-out", outx],
            capture_output=True, text=True)
        rdx = json.load(open(outx)) if rx.returncode == 0 \
            and os.path.exists(outx) else None
        return rx, rdx
    r, read = run_attr(s3r, "plain")
    check("round-trip: attr analyzer exit 0 on genuine rows",
          r.returncode == 0,
          "exit=%r %s" % (r.returncode, r.stdout.strip()[-160:]))
    if r.returncode == 0:
        check("stamp audit rows == 200, bad == 0",
              read["label_tuple_audit"] == {"rows": 200, "bad": 0},
              "got %r" % read.get("label_tuple_audit"))
        check("primary mean diff == 0.2 (hand-computed)",
              approx(read["primary"]["mean_diff"], 0.2),
              "got %r" % read["primary"]["mean_diff"])
        att = read.get("attribution") or {}
        check("ATTRIBUTION arithmetic: per-game gain 0.2 = "
              "0.2 x 1.0; ratio 0.2 / 0.05 == 4.0",
              approx(att.get("per_game_gain"), 0.2)
              and approx(att.get("ratio_to_delta"), 4.0),
              "got %r" % att)
        check("ATTRIBUTION line printed with the ratio and "
              "the Fai references; no verdict bands",
              "ATTRIBUTION: per-game gain" in r.stdout
              and "fleet delta = 4.0000" in r.stdout
              and "VERDICT:" not in r.stdout
              and "verdict" not in read)
    # ---- RATIO GUARD branches (sec.4) -----------------------
    r, read = run_attr(
        {"primary": {"pairs_scored": 400, "mean_diff": -0.01,
                     "ci": [-0.03, 0.01]}}, "neg")
    att = (read or {}).get("attribution") or {}
    check("ratio guard: delta <= 0 -> prints 'n/a (Δ ≤ 0)' "
          "with delta's CI beside it; JSON ratio null + note",
          r.returncode == 0 and read
          and "fleet delta = n/a (Δ ≤ 0), fleet Δ -0.0100 "
              "CI [-0.0300, 0.0100]" in r.stdout
          and att.get("ratio_to_delta") is None
          and att.get("ratio_note") == "n/a (Δ ≤ 0)"
          and att.get("stage3_primary_ci") == [-0.03, 0.01],
          "got %r" % att)
    r, read = run_attr(
        {"primary": {"pairs_scored": 400, "mean_diff": 0.01,
                     "ci": [-0.02, 0.04]}}, "unstable")
    att = (read or {}).get("attribution") or {}
    check("ratio guard: delta > 0, CI includes 0 -> prints "
          "'unstable (Δ CI includes 0)' with the CI beside "
          "it; JSON ratio null + note",
          r.returncode == 0 and read
          and "fleet delta = unstable (Δ CI includes 0), "
              "fleet Δ 0.0100 CI [-0.0200, 0.0400]" in r.stdout
          and att.get("ratio_to_delta") is None
          and att.get("ratio_note") == "unstable (Δ CI includes 0)"
          and att.get("stage3_primary_ci") == [-0.02, 0.04],
          "got %r" % att)
    print("FX-S3-L3-ROUNDTRIP: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
