#!/usr/bin/env python3
"""Step 1 pilot fixture: the pre-gate checker's exact
form on synthetic records (no games run).

Planted populations, per seat (driver rows for seeds
13001-13010 in all arms; stat rows for one game):
  * identical contested decisions in both ghost arms
    (same priors, same selected) -> identity holds;
  * a newly-contested pair: sec.14 arm an uncontested
    early-return row (contested == 0, NO priors --
    the real shape), thr arm a full search row with
    top prior 0.99 -> counted as the expected
    divergence, verdict still IDENTICAL;
  * K6-clean rollout rows in both arms.
Negative cases (separate invocations):
  * one contested pair's priors differ -> NOT
    IDENTICAL;
  * the sec.14 arm skips a decision whose thr-arm
    top prior is 0.50 (below the boundary) -> NOT
    IDENTICAL (not the registered divergence).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
fails = []
checks = 0


def check(name, good, detail=""):
    global checks
    checks += 1
    print("%s %s %s" % ("PASS" if good else "FAIL",
                        name, detail))
    if not good:
        fails.append(name)


def drow(seed, sha):
    return {"seed": seed, "winner": 1, "draw": False,
            "capped": False, "turns": 40,
            "gamelog_sha": sha,
            "gamestate_norm_sha": "n%d" % seed}


def ghost_stats(priors_b=0.99, contested_priors=None,
                skip_below=False):
    """sec.14 arm rows, thr arm rows."""
    base = {"teacher": 1, "game": "gX", "branch": "M",
            "player": 1}
    a = []
    b = []
    # contested pair (both searched)
    pa = contested_priors or {"0": 0.5, "1": 0.4}
    pb = contested_priors or {"0": 0.5, "1": 0.4}
    a.append(dict(base, turn=5, contested=1, priors=pa,
                  selected=[0, 1], prior_pick=0, pick=0,
                  ghost=1, means=[0.0, 0.1], n_worlds=25))
    b.append(dict(base, turn=5, contested=1, priors=pb,
                  selected=[0, 1], prior_pick=0, pick=0,
                  ghost=1, means=[0.0, 0.1], n_worlds=25))
    # newly-contested (or the below-boundary skip case)
    a.append(dict(base, turn=9, contested=0, prior_pick=0,
                  pick=0, ncand=4))
    pb2 = {"0": priors_b, "1": 0.005}
    b.append(dict(base, turn=9, contested=1, priors=pb2,
                  selected=[0, 1], prior_pick=0, pick=0,
                  ghost=1, means=[0.0, 0.2], n_worlds=25))
    return a, b


def build(tmp, a_stats, b_stats):
    files = {}
    def w(name, rows):
        p = os.path.join(tmp, name)
        with open(p, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        files[name] = p
    for tag in ("raw_s1", "raw2_s1", "raw_s2",
                    "ghost14_s1", "ghost14_s2",
                    "ghostthr_s1", "ghostthr_s2"):
        rows = [drow(s, "h%d" % s) for s in
                range(13001, 13011)]
        if tag == "raw_s2":
            rows = [dict(r, gamestate_norm_sha="m%d"
                         % r["seed"]) for r in rows]
        w(tag + ".jsonl", rows)
    man = {"checks": {"stat_teacher_rows_present": True,
                      "trace_teacher_rows_present": True,
                      "ghost_flag_on_all_rollouts": False}}
    for tag in ("ghost14_s1", "ghost14_s2",
                "ghostthr_s1", "ghostthr_s2"):
        p = os.path.join(tmp, tag + ".manifest.json")
        with open(p, "w") as f:
            json.dump(man, f)
        files[tag + ".manifest"] = p
    w("ghost14_s1.jsonl.stats", a_stats)
    w("ghost14_s2.jsonl.stats", a_stats)
    w("ghostthr_s1.jsonl.stats", b_stats)
    w("ghostthr_s2.jsonl.stats", b_stats)
    args = [sys.executable,
            os.path.join(S1, "pregate_check_pilot.py")]
    for tag in ("raw_s1", "raw2_s1", "raw_s2",
                "ghost14_s1", "ghost14_s2",
                "ghostthr_s1", "ghostthr_s2"):
        args += ["--rows", "%s=%s" % (tag,
                                      files[tag + ".jsonl"])]
    for tag in ("ghost14_s1", "ghost14_s2",
                "ghostthr_s1", "ghostthr_s2"):
        args += ["--manifest",
                 "%s=%s" % (tag, files[tag + ".manifest"])]
        args += ["--stats",
                 "%s=%s" % (tag,
                            files[tag + ".jsonl.stats"])]
    return subprocess.run(args, capture_output=True,
                          text=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        a, b = ghost_stats()
        r = build(tmp, a, b)
        check("P identical + newly-contested divergence "
              "-> IDENTICAL",
              r.returncode == 0
              and "PREGATE: IDENTICAL" in r.stdout,
              r.stdout[-300:] if r.returncode else "")
        check("P newly-contested divergence counted",
              "newly-contested divergences" in r.stdout
              and ": 1" in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        a, b = ghost_stats()
        b[0] = dict(b[0], priors={"0": 0.55, "1": 0.4})
        r = build(tmp, a, b)
        check("P contested priors mismatch -> NOT "
              "IDENTICAL", r.returncode == 2
              and "NOT IDENTICAL" in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        a, b = ghost_stats(priors_b=0.50)
        r = build(tmp, a, b)
        check("P sec.14 skip below the boundary -> NOT "
              "IDENTICAL", r.returncode == 2
              and "NOT IDENTICAL" in r.stdout)
    print("fx_pilot_pregate: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
