#!/usr/bin/env python3
"""fx_stage2_analyze: stage2_analyze.py on planted label
rows with hand-computed answers (W=4 via --expect-rows 4).

Planted population: 4 jobs over 2 games (gA: j1, j2; gB:
j3, j4), teacher_pick=1, prior_pick=0. Worlds per job
(teacher cand / prior cand), outcomes with horizon+life
where noted:
  j1: T [+1, +1, HZ life 12>9, -1]  P [-1, HZ tied 5=5, -1, -1]
      primary diff +0.5, draw05 +0.5, lifediff +0.75
  j2: T all +1, P all -1 -> all diffs +1
  j3: T [-1, -1, HZ life 3<10, +1]  P [+1, -1, -1, -1]
      primary 0, draw05 +0.125, lifediff 0
  j4: T [win, ERROR abort, loss, REFUSAL canary_hook_failed]
      P [+1, +1, -1, +1]
      primary/draw05/lifediff diff 0 over the 2 shared
      finished worlds; sensitivity diff -1/6 (the aborted
      world priced 0.5 vs the prior's win)
Hand-computed reads over the 4 jobs:
  primary mean 0.375; draw05 mean 0.40625; lifediff 0.4375
  per-game gain 0.375 x 1.0 = 0.375 -> TRIPWIRE (also mean
  > 0.20); LOGO range [0.0, 0.75]; sensitivity mean
  (0.5 + 1 + 0.125 - 1/6) / 4 = 0.364583...
  unfinished pooled share 1/31; refusal tally 1.
A negated copy must read STOP with no tripwire; a row with
a wrong tuple stamp aborts (exit 2); a dropped row trips
the world-count guard (exit 2). A variant with a fifth job
whose prior candidate finishes no world (no shared
finished world) must report jobs_no_shared_worlds == 1
beside jobs and leave the read unchanged (review sec.4).
Run: python3 fx_stage2_analyze.py (own temp dirs)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "code")
ANALYZER = os.path.join(CODE, "stage2_analyze.py")
SETTINGS = os.path.join(CODE, "settings_stage2.json")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def approx(x, y, tol=1e-9):
    return x is not None and abs(x - y) <= tol


LT = json.load(open(SETTINGS))["label_tuple"]


def fin(outcome, horizon=0, lr=None, lo=None):
    res = {"finished": 1, "outcome": float(outcome),
           "winner": (1 if outcome > 0 else
                      (0 if outcome == 0 else 2)),
           "horizon": horizon, "fallbacks": 0}
    if lr is not None:
        res["life_root"] = lr
        res["life_opp"] = lo
    return res


def err(cls):
    return {"error": cls}


# (teacher worlds, prior worlds) per job, worlds 0..3
JOBSPEC = {
    "j1": ([fin(1), fin(1), fin(0, 1, 12, 9), fin(-1)],
           [fin(-1), fin(0, 1, 5, 5), fin(-1), fin(-1)]),
    "j2": ([fin(1)] * 4, [fin(-1)] * 4),
    "j3": ([fin(-1), fin(-1), fin(0, 1, 3, 10), fin(1)],
           [fin(1), fin(-1), fin(-1), fin(-1)]),
    "j4": ([fin(1), err("abort"), fin(-1),
            err("canary_hook_failed")],
           [fin(1), fin(1), fin(-1), fin(1)]),
}
GAME = {"j1": "gA", "j2": "gA", "j3": "gB", "j4": "gB"}


def build(tmp, negate=False, bad_stamp=False, drop=False,
          no_shared=False):
    jobs, labels = [], []
    for snap in ("j1", "j2", "j3", "j4"):
        jobs.append({"snap": snap, "game": GAME[snap],
                     "player": 1, "branch": "M",
                     "prior_pick": 0, "teacher_pick": 1,
                     "setting": LT})
        tw, pw = JOBSPEC[snap]
        for cand, world_list in ((1, tw), (0, pw)):
            for w, res in enumerate(world_list):
                r = dict(res)
                if negate and "outcome" in r:
                    r["outcome"] = -r["outcome"]
                    r["winner"] = (2 if r["outcome"] < 0 else
                                   (1 if r["outcome"] > 0 else 0))
                st = dict(LT)
                st["pinned"] = 1
                if bad_stamp and snap == "j1" and cand == 1 and w == 0:
                    st["k"] = 25
                labels.append({"snap": snap, "cand": cand,
                               "world": w, "result": r,
                               "setting": st,
                               "prior_pick": 0, "teacher_pick": 1})
    if no_shared:
        # j5: the teacher candidate finishes all 4 worlds,
        # the prior candidate finishes none (aborts) -> the
        # job produces NO shared finished world and must be
        # counted as jobs_no_shared_worlds, not in the read.
        jobs.append({"snap": "j5", "game": "gB",
                     "player": 1, "branch": "M",
                     "prior_pick": 0, "teacher_pick": 1,
                     "setting": LT})
        for cand, world_list in ((1, [fin(1)] * 4),
                                 (0, [err("abort")] * 4)):
            for w, res in enumerate(world_list):
                st = dict(LT)
                st["pinned"] = 1
                labels.append({"snap": "j5", "cand": cand,
                               "world": w, "result": dict(res),
                               "setting": st,
                               "prior_pick": 0, "teacher_pick": 1})
    if drop:
        labels = labels[:-1]
    jp = os.path.join(tmp, "jobs.jsonl")
    lp = os.path.join(tmp, "labels.jsonl")
    with open(jp, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(lp, "w") as f:
        for r in labels:
            f.write(json.dumps(r) + "\n")
    grep = {"overturn_rows": 4, "games_completed": 4,
            "overturns_per_game": 1.0, "thin_prior_rate": 0.0,
            "overturn_rate": 0.25,
            "teacher_outcomes_draw_scored": {
                "W": 2, "D": 1, "L": 1, "points": 2.5,
                "points_per_game": 0.625}}
    gp = os.path.join(tmp, "games_report.json")
    json.dump(grep, open(gp, "w"))
    out = os.path.join(tmp, "read.json")
    r = subprocess.run(
        [sys.executable, ANALYZER, "--jobs", jp, "--labels", lp,
         "--games-report", gp, "--settings", SETTINGS,
         "--expect-rows", "4", "--json-out", out],
        capture_output=True, text=True)
    return r, (json.load(open(out)) if os.path.exists(out)
               and r.returncode == 0 else None)


def main():
    r, read = build(tempfile.mkdtemp())
    check("analyzer exit 0", r.returncode == 0,
          r.stderr.strip()[-200:] if r.returncode else "")
    if read:
        check("primary mean == 0.375",
              approx(read["primary"]["mean_diff"], 0.375),
              "got %r" % read["primary"]["mean_diff"])
        check("draw05 mean == 0.40625",
              approx(read["coreport_draw05"]["mean_diff"],
                     0.40625))
        check("lifediff mean == 0.4375 (ahead wins, behind "
              "loses, tied draws at 0)",
              approx(read["coreport_lifediff"]["mean_diff"],
                     0.4375))
        check("per-game gain == 0.375 (live overturns/game)",
              approx(read["per_game_gain"], 0.375))
        tw = read.get("tripwire")
        check("tripwire fired (per-game > 0.25, mean > 0.20)",
              tw is not None)
        if tw:
            check("LOGO range == [0.0, 0.75]",
                  approx(tw["logo_range"][0], 0.0)
                  and approx(tw["logo_range"][1], 0.75),
                  "got %r" % tw.get("logo_range"))
            check("sensitivity mean == 0.364583...",
                  approx(tw["sensitivity"]["mean_diff"],
                         (0.5 + 1 + 0.125 - 1.0 / 6) / 4, 1e-6),
                  "got %r" % tw["sensitivity"]["mean_diff"])
        check("impeachment printed BEFORE the read",
              r.stdout.index("TRIPWIRE FIRED")
              < r.stdout.index("PRIMARY (draw = 0)"))
        check("unfinished pooled share == 1/31, refusals 1",
              approx(read["unfinished"]["share_pooled"],
                     1.0 / 31, 1e-6)
              and read["unfinished"]["teacher"]["refusal"] == 1)
        check("verdict is a band verdict (not STOP)",
              read["verdict"] in ("PROCEED", "DOES NOT PROCEED"),
              "got %r" % read["verdict"])
    r2, read2 = build(tempfile.mkdtemp(), negate=True)
    # Negated primary mean is -0.4375, not -0.375: at draw
    # = 0 the read is NOT antisymmetric under outcome
    # negation (drawn worlds score 0 on both sides) -- j3's
    # planted 0 diff becomes -0.25 in the negated copy.
    check("negated population: STOP, no tripwire",
          r2.returncode == 0 and read2
          and read2["verdict"] == "STOP"
          and read2["tripwire"] is None
          and approx(read2["primary"]["mean_diff"], -0.4375),
          "verdict=%r mean=%r" % (read2 and read2["verdict"],
                                  read2 and
                                  read2["primary"]["mean_diff"]))
    r5, read5 = build(tempfile.mkdtemp(), no_shared=True)
    check("no-shared-world job counted beside jobs "
          "(jobs_no_shared_worlds 1, read unchanged)",
          r5.returncode == 0 and read5
          and read5["jobs_no_shared_worlds"] == 1
          and read5["primary"]["jobs"] == 4
          and approx(read5["primary"]["mean_diff"], 0.375),
          "got %r" % (read5 and
                      read5.get("jobs_no_shared_worlds")))
    check("PRIMARY line prints jobs_no_shared_worlds",
          "jobs_no_shared_worlds 1 (of 5 jobs)" in r5.stdout)
    r3, _ = build(tempfile.mkdtemp(), bad_stamp=True)
    check("wrong tuple stamp on a row aborts (exit 2)",
          r3.returncode == 2)
    r4, _ = build(tempfile.mkdtemp(), drop=True)
    check("dropped row trips the world-count guard (exit 2)",
          r4.returncode == 2)
    print("FX-STAGE2-ANALYZE: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
