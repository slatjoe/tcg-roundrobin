#!/usr/bin/env python3
"""Step 1 pilot fixture: the pre-gate checker's exact
form on synthetic records (no games run). REWRITTEN
in fix pass 2 (2026-10-29) to plant the REAL shapes
of attempt 1 -- the Layer B lesson of
step1-pilot-launch.md: the v1 fixture reused the SAME
game ids in both arms, so its pairing key overlapped
and it passed, while the real instrument's arm-local
instance ids are disjoint and the v1 checker paired
zero decisions.

Planted shapes, per seat:
  * DISJOINT game-id sets: the sec.14 arm's games are
    "g14s<seat>_<seed>", the thr arm's are
    "gths<seat>_<seed>"; the arms share NOTHING but
    the seed, and the driver rows carry each arm's
    seed -> gamename mapping (the real row shape).
  * a newly-contested pair at decision INDEX 0 (the
    first decision of the game): sec.14 uncontested
    early-return row (contested == 0, NO priors --
    the real shape), thr a full search row with top
    prior 0.99994 -> counted, expected shape, verdict
    still IDENTICAL;
  * a contested pair whose priors differ at ~1e-7
    (the observed GPU float noise) with identical
    selected -> a contested pair, within the 1e-6
    tolerance;
  * K6-clean rollout rows in both arms.
Negative / control cases (separate invocations):
  * the SAME base population run against the v1
    checker (fixtures/pregate_check_pilot_v1.py, the
    pre-fix bytes) -> NOT IDENTICAL with "0 contested
    pairs" and a large "other divergences" count:
    the Layer B failure, reproduced;
  * a contested pair's priors differing at 1e-4 ->
    contested_bad -> NOT IDENTICAL;
  * an off-shape pair (sec.14 searched x thr
    uncontested) -> counted by name -> NOT IDENTICAL;
  * the sec.14 arm skipping a decision whose thr-arm
    top prior is 0.50 (below the boundary) -> counted
    by name -> NOT IDENTICAL;
  * a thr driver row that is a TIMEOUT row (the real
    attempt-1 shape: invalid == "timeout", no
    gamename) -> reported as a named timeout, never
    an identity failure; identity is judged on the
    completed games and the verdict stays IDENTICAL.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
NEW = os.path.join(S1, "pregate_check_pilot.py")
OLD = os.path.join(HERE, "pregate_check_pilot_v1.py")
fails = []
checks = 0


def check(name, good, detail=""):
    global checks
    checks += 1
    print("%s %s %s" % ("PASS" if good else "FAIL",
                        name, detail))
    if not good:
        fails.append(name)


def drow(seed, sha, gamename=None, timeout=False):
    if timeout:
        return {"seed": seed, "arm": "ghost", "seat": 1,
                "invalid": "timeout",
                "timeout_new_games": ["x%d" % seed],
                "timeout_cache_cleaned": ["x%d" % seed]}
    r = {"seed": seed, "winner": 1, "draw": False,
         "capped": False, "turns": 40,
         "gamelog_sha": sha,
         "gamestate_norm_sha": "n%d" % seed}
    if gamename is not None:
        r["gamename"] = gamename
    return r


def gid(arm, seat, seed):
    return "%s%d_%d" % (arm, seat, seed)


def plant(seat, priors_b_top=0.99994,
          contested_b=None, off_shape=False):
    """sec.14 arm rows, thr arm rows, for seed 13001's
    game (each arm under its OWN instance id)."""
    ga = gid("g14s", seat, 13001)
    gb = gid("gths", seat, 13001)
    base = {"teacher": 1, "branch": "M", "player": seat}
    a, b = [], []
    # index 0: newly-contested (sec.14 early return,
    # thr searches at top prior priors_b_top)
    a.append(dict(base, game=ga, turn=9, contested=0,
                  prior_pick=0, pick=0, ncand=4))
    b.append(dict(base, game=gb, turn=9, contested=1,
                  priors={"0": priors_b_top,
                          "1": 0.00005},
                  selected=[0], prior_pick=0, pick=0,
                  ghost=1, means=[0.0, 0.2],
                  n_worlds=25))
    # index 1: contested pair (both searched)
    pa = {"0": 0.5, "1": 0.4}
    pb = contested_b or {"0": 0.5000001, "1": 0.3999999}
    if off_shape:
        a.append(dict(base, game=ga, turn=5, contested=1,
                      priors=pa, selected=[0, 1],
                      prior_pick=0, pick=0, ghost=1,
                      means=[0.0, 0.1], n_worlds=25))
        b.append(dict(base, game=gb, turn=5, contested=0,
                      prior_pick=0, pick=0, ncand=3))
    else:
        a.append(dict(base, game=ga, turn=5, contested=1,
                      priors=pa, selected=[0, 1],
                      prior_pick=0, pick=0, ghost=1,
                      means=[0.0, 0.1], n_worlds=25))
        b.append(dict(base, game=gb, turn=5, contested=1,
                      priors=pb, selected=[0, 1],
                      prior_pick=0, pick=0, ghost=1,
                      means=[0.0, 0.1], n_worlds=25))
    return a, b


def build(tmp, plant_kw=None, timeout_thr_seed=None,
          checker=NEW):
    plant_kw = plant_kw or {}
    files = {}

    def w(name, rows):
        p = os.path.join(tmp, name)
        with open(p, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        files[name] = p

    for tag in ("raw_s1", "raw2_s1", "raw_s2"):
        rows = [drow(s, "h%d" % s)
                for s in range(13001, 13011)]
        if tag == "raw_s2":
            rows = [dict(r, gamestate_norm_sha="m%d"
                         % r["seed"]) for r in rows]
        w(tag + ".jsonl", rows)
    for seat in (1, 2):
        for arm, pre in (("ghost14", "g14s"),
                         ("ghostthr", "gths")):
            tag = "%s_s%d" % (arm, seat)
            rows = []
            for s in range(13001, 13011):
                if arm == "ghostthr" \
                        and s == timeout_thr_seed:
                    rows.append(drow(s, None, timeout=True))
                else:
                    rows.append(drow(
                        s, "h%d" % s,
                        gamename=gid(pre, seat, s)))
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
    for seat in (1, 2):
        a, b = plant(seat, **plant_kw)
        w("ghost14_s%d.jsonl.stats" % seat, a)
        w("ghostthr_s%d.jsonl.stats" % seat, b)
    args = [sys.executable, checker]
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
        r = build(tmp)
        check("P disjoint ids + noise 1e-7 + newly at "
              "index 0 -> IDENTICAL",
              r.returncode == 0
              and "PREGATE: IDENTICAL" in r.stdout,
              r.stdout[-300:] if r.returncode else "")
        check("P newly-contested counted (expected "
              "shape)", "newly-contested divergences "
              "(expected shape): 1" in r.stdout)
        check("P contested pair found by seed pairing",
              "1 contested pairs, 0 bad" in r.stdout)
        check("P observed max |dprior| printed, within "
              "tol", "max |dprior| 1.000e-07" in r.stdout
              or "max |dprior| 9.999e-08" in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        r = build(tmp, checker=OLD)
        check("P v1 checker FAILS the disjoint-ids "
              "population (Layer B reproduced)",
              r.returncode == 2
              and "NOT IDENTICAL" in r.stdout
              and "0 contested pairs" in r.stdout,
              r.stdout[-300:] if r.returncode != 2
              else "")
    with tempfile.TemporaryDirectory() as tmp:
        r = build(tmp, plant_kw={
            "contested_b": {"0": 0.5001, "1": 0.4}})
        check("P contested priors off by 1e-4 -> "
              "contested_bad -> NOT IDENTICAL",
              r.returncode == 2
              and "NOT IDENTICAL" in r.stdout
              and "1 contested pairs, 1 bad"
              in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        r = build(tmp, plant_kw={"off_shape": True})
        check("P off-shape pair counted by name -> "
              "NOT IDENTICAL",
              r.returncode == 2
              and "NOT IDENTICAL" in r.stdout
              and "sec14-searched_x_thr-uncontested"
              in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        r = build(tmp, plant_kw={"priors_b_top": 0.50})
        check("P sec.14 skip below the boundary "
              "counted by name -> NOT IDENTICAL",
              r.returncode == 2
              and "NOT IDENTICAL" in r.stdout
              and "sec14-uncontested_x_thr-searched_"
              "below-0.97" in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        r = build(tmp, timeout_thr_seed=13002)
        check("P timeout row reported as a timeout, "
              "identity on completed games -> "
              "IDENTICAL",
              r.returncode == 0
              and "PREGATE: IDENTICAL" in r.stdout
              and "timeouts: 1 seed(s): seed 13002 "
              "(thr)" in r.stdout,
              r.stdout[-300:] if r.returncode else "")
    print("fx_pilot_pregate: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
