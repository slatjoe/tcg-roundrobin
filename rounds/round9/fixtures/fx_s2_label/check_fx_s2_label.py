#!/usr/bin/env python3
"""fx_s2_label checker: s2_label_main.php against the stub
play_game.php in this dir. Known answers:
  * happy path: exit 0, S2-LABEL-DONE; 2 jobs x selected cands
    x W=50 rows; every row stamped with the full L3 tuple +
    prior_pick + teacher_pick from its job; horizon-ended
    rows keep their life fields through the driver; cfg log
    shows W=50, horizon 62, hookBudget 8000, deadlineS 180
    forwarded per job; stat rows carry teacher_pick.
  * jobs_badk (job k=25 vs pin 50) and jobs_nosetting abort
    with exit 2 before any row is written.
Usage: check_fx_s2_label.py <workdir>"""
import json
import os
import sys

FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def main():
    work = sys.argv[1]
    rows = [json.loads(l) for l in open(os.path.join(work, "out.jsonl"))]
    stats = [json.loads(l) for l in open(os.path.join(work, "stats.jsonl"))]
    cfgs = [json.loads(l) for l in open(os.path.join(work, "cfg.jsonl"))]
    check("row count = 2 jobs x 2 selected x 50", len(rows) == 200,
          "rows=%d" % len(rows))
    T = {"name": "L3-W50+H", "hooks": 8000, "deadline_s": 180,
         "horizon": 62, "horizon_value": -1, "k": 50}
    check("every row stamped with the L3 tuple",
          all(r.get("setting") == T for r in rows))
    by_snap = {}
    for r in rows:
        by_snap.setdefault(r["snap"], []).append(r)
    check("teacher_pick stamped per job (fxA=1, fxB=0)",
          all(r["teacher_pick"] == 1 for r in by_snap["fxA"])
          and all(r["teacher_pick"] == 0 for r in by_snap["fxB"]))
    check("prior_pick stamped per job (fxA=0, fxB=2)",
          all(r["prior_pick"] == 0 for r in by_snap["fxA"])
          and all(r["prior_pick"] == 2 for r in by_snap["fxB"]))
    hz = [r for r in rows if r["result"].get("horizon") == 1]
    check("horizon rows keep life_root/life_opp through the "
          "driver", len(hz) == 40 and all(
              r["result"].get("life_root") == 9
              and r["result"].get("life_opp") == 12 for r in hz),
          "horizon rows=%d" % len(hz))
    check("cfg forwarded per job (W=50, horizon 62, hooks "
          "8000, deadline 180, pair va)",
          len(cfgs) == 2 and all(
              c["W"] == 50 and c["horizon"] == 62
              and c["hookBudget"] == 8000 and c["deadlineS"] == 180
              and c["pair"] == "va" for c in cfgs))
    check("stat rows carry teacher_pick + setting",
          len(stats) == 2 and all(
              "teacher_pick" in s and s.get("setting") == T
              for s in stats))
    for name in ("badk", "nosetting"):
        err = open(os.path.join(work, name + ".stderr")).read()
        check("%s aborted (exit 2 recorded by runner, ABORT "
              "logged)" % name, "ABORT:" in err)
        check("%s wrote no rows" % name,
              not os.path.exists(os.path.join(work,
                                              name + ".out.jsonl")))
    print("FX-S2-LABEL: %s" % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
