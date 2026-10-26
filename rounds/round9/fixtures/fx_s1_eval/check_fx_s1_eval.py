#!/usr/bin/env python3
"""Checker for fx_s1_eval: verifies the driver's emitted rows
and stats from the happy-path run, against hand-computed
expectations (see fx_s1_eval/README in fixtures/README.md).

fxA: 2 candidates x 25 worlds, all finished -> cand_finished
  25/25, no errors.
fxB: 2 candidates x 25 worlds: 21 decisive + 1 draw
  (finished) + 3 abort errors per candidate -> cand_finished
  22/22, errors {"abort": 6} for the job.
Every world row must be stamped with the full run tuple
(B0+H / 4000 / 180 / 62 / -1 / 25), prior_pick and game.
The cfg log must show the pins forwarded into the label
machinery: hookBudget 4000, deadlineS 180, horizon 62,
W 25, pair "va", seedBase 885001 and 885001 + 100003.
"""
import json
import sys

TUPLE = {"name": "B0+H", "hooks": 4000, "deadline_s": 180,
         "horizon": 62, "horizon_value": -1, "k": 25}
fails = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        fails.append(name)


def main(rows_path, stats_path, cfglog_path):
    rows = [json.loads(l) for l in open(rows_path) if l.strip()]
    stats = [json.loads(l) for l in open(stats_path) if l.strip()]
    cfgs = [json.loads(l) for l in open(cfglog_path) if l.strip()]

    by_snap = {}
    for r in rows:
        by_snap.setdefault(r["snap"], []).append(r)
    check("row count fxA", len(by_snap.get("fxA", [])) == 50,
          "got %d" % len(by_snap.get("fxA", [])))
    check("row count fxB", len(by_snap.get("fxB", [])) == 50,
          "got %d" % len(by_snap.get("fxB", [])))
    check("all rows stamped with the run tuple",
          all(r.get("setting") == TUPLE for r in rows))
    check("fxA rows stamped prior_pick 0 / game gA",
          all(r["prior_pick"] == 0 and r["game"] == "gA"
              for r in by_snap["fxA"]))
    check("fxB rows stamped prior_pick 1 / game gB",
          all(r["prior_pick"] == 1 and r["game"] == "gB"
              for r in by_snap["fxB"]))

    st = {s["snap"]: s for s in stats}
    a, b = st["fxA"], st["fxB"]
    check("fxA stat cand_finished 25/25",
          a["cand_finished"] == {"0": 25, "1": 25},
          json.dumps(a["cand_finished"]))
    check("fxA stat errors empty", a["errors"] == {})
    check("fxB stat cand_finished 22/22",
          b["cand_finished"] == {"0": 22, "1": 22},
          json.dumps(b["cand_finished"]))
    check("fxB stat cand_rows 25/25",
          b["cand_rows"] == {"0": 25, "1": 25})
    check("fxB stat errors {abort: 6}", b["errors"] == {"abort": 6},
          json.dumps(b["errors"]))
    check("fxB stat: draw counts finished, so 22 = 21 decisive "
          "+ 1 drawn world",
          sum(1 for r in by_snap["fxB"]
              if isinstance(r.get("result"), dict)
              and r["result"].get("winner") == 0) == 2)
    check("stat rows carry the tuple + wall_ms",
          all(s.get("setting") == TUPLE and
              isinstance(s.get("wall_ms"), int) for s in stats))

    check("two label calls recorded", len(cfgs) == 2)
    c0, c1 = cfgs
    check("cfg pins forwarded (job 1)",
          c0["hookBudget"] == 4000 and c0["deadlineS"] == 180
          and c0["horizon"] == 62 and c0["W"] == 25
          and c0["pair"] == "va" and c0["seedBase"] == 885001
          and c0["candIdx"] == [0, 1], json.dumps(c0))
    check("cfg seedBase strides by job index (job 2)",
          c1["seedBase"] == 885001 + 100003, json.dumps(c1))

    print("FX-S1-EVAL checker: %s"
          % ("ALL PASS" if not fails else "FAILURES: %s" % fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
