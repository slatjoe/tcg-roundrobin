#!/usr/bin/env python3
"""fx_build_s2_jobs: build_s2_jobs.py on planted snap-index
streams. Known answers: 3 overturn rows over 2 streams ->
3 jobs; selected = sorted {prior, teacher}; cands carried
verbatim (the candidate RECORDS); the label tuple stamped
from the settings file; snap_dir = PREFIX/<snap>; shards
partition the jobs; a teacher==prior row aborts (exit 2);
a duplicate snap aborts. Run: python3 fx_build_s2_jobs.py
(builds its own temp dir; exit 1 on any failure)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(HERE, "..", "code", "build_s2_jobs.py")
SETTINGS = os.path.join(HERE, "..", "code", "settings_stage2.json")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def idx_row(snap, game, tp, pp):
    return {"snap": snap, "game": game, "hcount": 1,
            "branch": "M", "player": 1, "turn": 30,
            "cands": [{"card_id": "a", "zone": "hand"},
                      {"card_id": "b", "zone": "hand"},
                      {"card_id": "c", "zone": "hand"}],
            "teacher_pick": tp, "prior_pick": pp,
            "mean_diff": 0.4, "se_diff": 0.1}


def run(streams, tmp):
    args = [sys.executable, BUILDER,
            "--settings", SETTINGS,
            "--out", tmp + "/jobs.jsonl",
            "--shard-prefix", tmp + "/shard",
            "--report", tmp + "/report.json"]
    for prefix, rows in streams:
        p = os.path.join(tmp, "idx_%s.jsonl" % prefix)
        with open(p, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        args += ["--stream", "%s=%s" % (prefix, p)]
    return subprocess.run(args, capture_output=True, text=True)


def main():
    tmp = tempfile.mkdtemp()
    streams = [("snapsA", [idx_row("g1_t1", "g1", 2, 0),
                           idx_row("g1_t2", "g1", 0, 1)]),
               ("snapsB", [idx_row("g2_t1", "g2", 1, 2)])]
    r = run(streams, tmp)
    check("builder exit 0", r.returncode == 0, r.stderr.strip())
    jobs = [json.loads(l) for l in open(tmp + "/jobs.jsonl")]
    check("3 jobs", len(jobs) == 3)
    j = {x["snap"]: x for x in jobs}
    check("selected = sorted {prior, teacher}",
          j["g1_t1"]["selected"] == [0, 2]
          and j["g1_t2"]["selected"] == [0, 1]
          and j["g2_t1"]["selected"] == [1, 2])
    check("cands carried verbatim (records)",
          j["g1_t1"]["cands"][1] == {"card_id": "b",
                                     "zone": "hand"})
    st = json.load(open(SETTINGS))
    check("label tuple stamped from settings",
          all(x["setting"] == st["label_tuple"] for x in jobs))
    check("snap_dir = PREFIX/<snap>",
          j["g2_t1"]["snap_dir"] == "snapsB/g2_t1")
    tot = 0
    for s in range(4):
        p = "%s/shard%d.jsonl" % (tmp, s)
        if os.path.exists(p):
            tot += sum(1 for _ in open(p))
    check("shards partition the jobs", tot == 3)
    rep = json.load(open(tmp + "/report.json"))
    check("report: 3 jobs over 2 games",
          rep["jobs"] == 3 and rep["games"] == 2)

    tmp2 = tempfile.mkdtemp()
    r = run([("snapsA", [idx_row("g1_t1", "g1", 1, 1)])], tmp2)
    check("teacher==prior row aborts (exit 2)",
          r.returncode == 2, "rc=%d" % r.returncode)
    tmp3 = tempfile.mkdtemp()
    r = run([("snapsA", [idx_row("g1_t1", "g1", 2, 0)]),
             ("snapsB", [idx_row("g1_t1", "g1", 0, 2)])], tmp3)
    check("duplicate snap aborts (exit 2)", r.returncode == 2)
    print("FX-BUILD-S2-JOBS: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
