#!/usr/bin/env python3
"""Step 2+3 fleet pin coverage (the fx_pilot_pins form,
extended to two runners). For EACH runner
(run_fleet_games.sh, run_fleet_l3.sh):

- the deployed-file list is parsed out of the runner's
  own deployed_code_hashes recording loop;
- every deployed NON-shell file carries an expect_hash
  site in that runner whose literal is 64-hex AND
  equals the staged file's sha256 (a deployed file
  with no pin, or a stale pin, is exactly the Oct 28
  runner pin gap);
- every $CODE_DIR expect_hash literal in the runner
  equals the staged file's sha256;
- settings-literal cross-checks: GAME_TIMEOUT source
  (settings games.timeout_s = 8031, read by both
  runners' SETREAD), LABEL_BASE in run_fleet_l3.sh ==
  settings label.seed_base, the MEAS_SEED stride
  literal == settings label.seed_stride_per_shard,
  the EVAL_* env names present, the registry tag read
  from settings, the snap-dir layout token
  (games_<blk>_log/snaps, the pilot's layout).

NEGATIVE CASE: a copy of run_fleet_games.sh with the
fleet_read.py expect_hash site stripped must FAIL the
coverage check (detected by name).
"""
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
STEP2 = os.path.join(R10, "code", "step2")
SETTINGS = json.load(open(os.path.join(
    STEP2, "settings_fleet.json")))
RUNNERS = ["run_fleet_games.sh", "run_fleet_l3.sh"]

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def deployed_files(text):
    m = re.search(r"for f in (.*?);\s*do", text, re.S)
    assert m, "deployed loop not found"
    return m.group(1).replace("\\", " ").split()


def pin_sites(text):
    """{basename: literal} for $CODE_DIR expect_hash sites."""
    out = {}
    pat = re.compile(
        r'expect_hash "\$CODE_DIR/([A-Za-z0-9_.]+)"\s*\\\s*\n'
        r'\s*(\S+)')
    for name, lit in pat.findall(text):
        out[name] = lit
    return out


def coverage_failures(text):
    """Deployed non-.sh files lacking a correct pin."""
    deployed = deployed_files(text)
    sites = pin_sites(text)
    bad = []
    for f in deployed:
        if f.endswith(".sh"):
            continue
        lit = sites.get(f)
        if lit is None or not re.fullmatch(r"[0-9a-f]{64}",
                                           lit or ""):
            bad.append((f, "no 64-hex pin site"))
        elif lit != sha(os.path.join(STEP2, f)):
            bad.append((f, "pin != staged sha256"))
    return bad


for runner in RUNNERS:
    text = open(os.path.join(STEP2, runner)).read()
    bad = coverage_failures(text)
    check("%s: every deployed non-shell file is pinned "
          "with its staged sha256" % runner, not bad,
          "failures: %s" % (bad,))
    sites = pin_sites(text)
    stale = [(f, lit) for f, lit in sites.items()
             if lit != sha(os.path.join(STEP2, f))]
    check("%s: every CODE_DIR pin literal equals the "
          "staged file" % runner, not stale,
          "stale: %s" % (stale,))
    check("%s: settings read via SETREAD (timeout, tag, "
          "blocks from settings_fleet.json)" % runner
          if runner == "run_fleet_games.sh" else
          "%s: label parameters read via SETREAD" % runner,
          "settings_fleet.json" in text
          and ("GAME_TIMEOUT=%d" in text
               or "LABEL_SEED_BASE=%d" in text))

games = open(os.path.join(STEP2, "run_fleet_games.sh")).read()
l3 = open(os.path.join(STEP2, "run_fleet_l3.sh")).read()
check("settings games.timeout_s is 8031 and the games "
      "runner's SETREAD sources GAME_TIMEOUT from it",
      int(SETTINGS["games"]["timeout_s"]) == 8031
      and 'g["timeout_s"]' in games)
m = re.search(r"^LABEL_BASE=(\d+)$", l3, re.M)
check("run_fleet_l3.sh LABEL_BASE == settings "
      "label.seed_base (1100055001)",
      m and int(m.group(1)) == int(SETTINGS["label"]
                                   ["seed_base"]) == 1100055001)
check("run_fleet_l3.sh MEAS_SEED stride literal == "
      "settings stride (10^8)",
      "s * 100000000" in l3
      and int(SETTINGS["label"]["seed_stride_per_shard"])
      == 100000000)
check("run_fleet_l3.sh label env carries the registered "
      "EVAL_* names from SETREAD vars",
      all(t in l3 for t in ("EVAL_SETTING_NAME=",
                            "EVAL_HOOKS=", "EVAL_DEADLINE_S=",
                            "LABEL_HORIZON=",
                            "EVAL_HORIZON_VALUE=", "EVAL_K=",
                            "MEAS_SEED=", "TCG_POLICY_SOCK=")))
check("run_fleet_games.sh snap layout is the pilot's "
      "(games_<blk>_log/snaps + teacher_snap_index "
      "consumed by the L3 runner)",
      'TEACHER_SNAP_DIR="$OUT/games_${blk}_log/snaps"'
      in games and "teacher_snap_index.jsonl" in l3)
check("registry tag comes from settings in the games "
      "runner", 'REGISTRY_TAG=%s' in games
      and SETTINGS["games"]["registry_tag"]
      == "r10_step2_fleet")

# ---- negative case ----
stripped = re.sub(
    r'expect_hash "\$CODE_DIR/fleet_read\.py"\s*\\\s*\n'
    r'\s*[0-9a-f]{64}\n', "", games)
assert stripped != games, "strip failed"
bad = coverage_failures(stripped)
check("negative: a pin-stripped runner copy fails "
      "coverage, naming fleet_read.py",
      any(f == "fleet_read.py" for f, _why in bad),
      "failures: %s" % (bad,))

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
