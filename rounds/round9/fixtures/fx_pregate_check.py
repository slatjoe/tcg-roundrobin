#!/usr/bin/env python3
"""fx_pregate_check: pregate_check.py on planted pre-gate
records. Four scenarios, each a full planted record set:
  clean  - ghost rows all stamped; outcomes/gamelogs equal;
           K6 line (n, 0, 0, 0) -> IDENTICAL, exit 0.
  k6     - 3 unstamped rollout rows, all thin-prior with
           pick == prior; the manifest's
           ghost_flag_on_all_rollouts is false, every other
           check true; K6 line (n, 3, 0, 0) -> IDENTICAL.
  bad    - one unstamped rollout row that is NOT thin-prior
           -> NOT IDENTICAL, exit 2.
  diverg - one ghost gamelog differs from raw -> NOT
           IDENTICAL, exit 2.
Run: python3 fx_pregate_check.py (own temp dirs)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "..", "code", "pregate_check.py")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def game_rows(seat, diverge_seed=None):
    rows = []
    for i, seed in enumerate(range(8501, 8511)):
        rows.append({
            "seed": seed, "arm": "x", "seat": seat, "winner": 1,
            "draw": 0, "capped": 0, "turns": 30,
            "gamelog_sha": "aa%014d" % seed,
            "gamestate_norm_sha": "bb%014d" % (seed + seat * 7)})
        if diverge_seed == seed:
            rows[-1]["gamelog_sha"] = "zz%014d" % seed
    return rows


def stat_rows(unstamped):
    rows = []
    for i in range(10):
        rows.append({"teacher": 1, "contested": 1, "ghost": 1,
                     "means": {"0": 0.1}, "pick": 0,
                     "prior_pick": 0})
    for kind in unstamped:
        r = {"teacher": 1, "contested": 1,
             "means": {"0": 0.1}, "pick": 0, "prior_pick": 0}
        if kind == "thin":
            r["fallback"] = "thin_prior"
        rows.append(r)
    # a non-rollout teacher row (no means): never counted
    rows.append({"teacher": 1, "contested": 0, "pick": 0,
                 "prior_pick": 0})
    return rows


def manifest(ghost_flag_ok):
    return {"checks": {
        "pick_eq_prior_all_teacher": True,
        "ghost_flag_on_all_rollouts": ghost_flag_ok,
        "rollouts_present": True,
        "trace_rules_all_ghost_prior": True,
        "trace_teacher_pick_is_prior_argmax": True},
        "assert_ok": ghost_flag_ok}


def build(tmp, unstamped=(), ghost_flag_ok=True, diverge=None):
    def w(name, rows):
        p = os.path.join(tmp, name)
        with open(p, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        return p
    files = {
        "raw_s1": w("raw_s1.jsonl", game_rows(1)),
        "raw2_s1": w("raw2_s1.jsonl", game_rows(1)),
        "raw_s2": w("raw_s2.jsonl", game_rows(2)),
        "ghost_s1": w("ghost_s1.jsonl",
                      game_rows(1, diverge_seed=diverge)),
        "ghost_s2": w("ghost_s2.jsonl", game_rows(2)),
    }
    mans, stats = {}, {}
    for seat in (1, 2):
        p = os.path.join(tmp, "man_s%d.json" % seat)
        json.dump(manifest(ghost_flag_ok), open(p, "w"))
        mans["ghost_s%d" % seat] = p
        stats["ghost_s%d" % seat] = w(
            "stats_s%d.jsonl" % seat, stat_rows(unstamped))
    args = [sys.executable, CHECKER]
    for tag, p in files.items():
        args += ["--rows", "%s=%s" % (tag, p)]
    for tag, p in mans.items():
        args += ["--manifest", "%s=%s" % (tag, p)]
    for tag, p in stats.items():
        args += ["--stats", "%s=%s" % (tag, p)]
    return subprocess.run(args, capture_output=True, text=True)


def main():
    r = build(tempfile.mkdtemp())
    check("clean: IDENTICAL, exit 0",
          r.returncode == 0 and "PREGATE: IDENTICAL" in r.stdout,
          r.stdout.strip().splitlines()[-1] if r.stdout else "")
    r = build(tempfile.mkdtemp(), unstamped=("thin",) * 3,
              ghost_flag_ok=False)
    check("k6: unstamped thin-prior rows only -> IDENTICAL",
          r.returncode == 0 and "PREGATE: IDENTICAL" in r.stdout)
    check("k6: mechanical line printed (13 3 0 0)",
          "13 3 0 0" in r.stdout)
    r = build(tempfile.mkdtemp(), unstamped=("bad",),
              ghost_flag_ok=False)
    check("bad: one unstamped non-thin row -> NOT IDENTICAL",
          r.returncode == 2 and "NOT IDENTICAL" in r.stdout)
    r = build(tempfile.mkdtemp(), diverge=8504)
    check("diverged gamelog -> NOT IDENTICAL",
          r.returncode == 2 and "NOT IDENTICAL" in r.stdout)
    print("FX-PREGATE-CHECK: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
