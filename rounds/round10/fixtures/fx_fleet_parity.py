#!/usr/bin/env python3
"""Step 2+3 fleet invocation parity (the
fx_pilot_invocation_parity form):

(a) PREGATE-GATE key coverage: every man.get(...) key
    the fleet games runner's PREGATE-GATE block reads
    exists in the REAL attempt-2 manifest (published:
    data/step1/pregate_attempt2/pregate_manifest.json).
(b) TUPLE form: the TEACHER_TUPLE_JSON the games
    runner's SETREAD builds from settings_fleet.json
    equals the attempt-2 manifest's recorded
    teacher_tuple_json string AND the pilot's canonical
    tuple (settings_pilot.json); the L3 runner's
    LABEL_TUPLE_JSON likewise equals the pilot's label
    canonical. This is the equality that makes the
    launch-time PREGATE-GATE pass on real data.
(c) DRIVER flag parity: the teacher and raw
    paired_driver_gravy.py invocations inside
    run_fleet_games.sh carry the SAME flag-name set
    (values differ only in --arm, per-block
    --seeds/--out/--logdir/--sock); the RAW-RERUN
    invocation carries the same set too.
(d) READ flag parity: fleet_read.py's invocation in
    run_fleet_games.sh vs run_fleet_l3.sh differs
    exactly by --primary-only (games) vs the full
    mode's --jobs/--labels/--games-rows (L3).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
STEP2 = os.path.join(R10, "code", "step2")
MANIFEST = json.load(open(os.path.join(
    R10, "data", "step1", "pregate_attempt2",
    "pregate_manifest.json")))
PILOT_SETTINGS = json.load(open(os.path.join(
    R10, "code", "step1", "settings_pilot.json")))
FLEET_SETTINGS = json.load(open(os.path.join(
    STEP2, "settings_fleet.json")))
GAMES = open(os.path.join(STEP2, "run_fleet_games.sh")).read()
L3 = open(os.path.join(STEP2, "run_fleet_l3.sh")).read()

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def block(text, tag):
    i = text.index("##### ===== %s" % tag)
    j = text.index("##### =====", i + 10)
    return text[i:j]


def canon(d, keys):
    return json.dumps({k: d[k] for k in keys},
                      sort_keys=True, separators=(",", ":"))


TKEYS = ("deadline_s", "hooks", "horizon", "horizon_value",
         "k", "margin", "name")
LKEYS = ("deadline_s", "hooks", "horizon", "horizon_value",
         "k", "name")

# ---- (a) PREGATE-GATE key coverage ----
gate = block(GAMES, "PREGATE-GATE")
keys = set(re.findall(r'man\.get\("([a-z_0-9]+)"', gate))
check("PREGATE-GATE reads only keys the real attempt-2 "
      "manifest carries", keys
      and keys <= set(MANIFEST.keys()),
      "gate keys %s; manifest keys %s"
      % (sorted(keys), sorted(MANIFEST.keys())))
check("the real manifest satisfies the gate's value "
      "conditions under the fleet pins",
      MANIFEST.get("verdict") == "IDENTICAL"
      and MANIFEST.get("search_s3_thr_sha256")
      == FLEET_SETTINGS["pregate"]["search_s3_thr_sha256"])

# ---- (b) tuple canonical forms ----
# The manifest comparison is a STRING comparison (the
# launch-time gate's form): the manifest recorded the
# tuple in json.dumps' default spaced form.
fleet_teacher = json.dumps(
    {k: FLEET_SETTINGS["teacher_tuple"][k] for k in TKEYS},
    sort_keys=True)
check("fleet TEACHER_TUPLE_JSON (SETREAD construction) "
      "== attempt-2 manifest's recorded tuple",
      fleet_teacher == MANIFEST["teacher_tuple_json"],
      "fleet %s vs manifest %s"
      % (fleet_teacher, MANIFEST["teacher_tuple_json"]))
check("fleet teacher tuple == the pilot's (dict "
      "equality)", FLEET_SETTINGS["teacher_tuple"]
      == PILOT_SETTINGS["teacher_tuple"])
# Execute the games runner's OWN SETREAD python and
# string-compare its TEACHER_TUPLE_JSON output to the
# manifest -- the exact comparison PREGATE-GATE runs.
import subprocess
seg = block(GAMES, "SETREAD")
py_src = seg.split("<<'PYEOF'", 1)[1].split("PYEOF", 1)[0]
env_out = subprocess.run(
    ["python3", "-", os.path.join(STEP2,
                                  "settings_fleet.json")],
    input=py_src, capture_output=True, text=True)
built = dict(re.findall(r"^([A-Z_0-9]+)=(.*)$",
                        env_out.stdout, re.M))
tuple_env = (built.get("TEACHER_TUPLE_JSON") or "") \
    .strip("'")
check("the games runner's SETREAD, executed, builds "
      "TEACHER_TUPLE_JSON == the manifest's string",
      tuple_env == MANIFEST["teacher_tuple_json"],
      "built %r" % tuple_env)
fleet_label = canon(FLEET_SETTINGS["label_tuple"], LKEYS)
check("fleet LABEL_TUPLE_JSON == the pilot's label "
      "canonical (settings_pilot label.tuple)",
      fleet_label == canon(
          PILOT_SETTINGS["label"]["tuple"], LKEYS))
check("settings label.tuple deep-equals label_tuple "
      "(the jobs builder reads label.tuple)",
      FLEET_SETTINGS["label"]["tuple"]
      == FLEET_SETTINGS["label_tuple"])

# ---- (c) driver flag parity ----
def driver_flags(seg):
    """Flag names of the paired_driver_gravy.py
    invocation inside a runner section (continuation-
    line walk from the invocation line)."""
    lines = seg.splitlines()
    for i, l in enumerate(lines):
        if "paired_driver_gravy.py" in l:
            flags = set()
            j = i
            while True:
                flags |= set(re.findall(
                    r"--([a-z][a-z0-9-]*)", lines[j]))
                if not lines[j].rstrip().endswith("\\"):
                    break
                j += 1
            return flags
    return set()


ts = block(GAMES, "TS-DRIVERS")
rs = block(GAMES, "RS-DRIVERS")
rr = block(GAMES, "RAW-RERUN")
check("teacher and raw driver invocations carry the "
      "same flag-name set", driver_flags(ts)
      == driver_flags(rs),
      "teacher %s raw %s" % (sorted(driver_flags(ts)),
                             sorted(driver_flags(rs))))
check("the raw-rerun invocation carries the same set",
      driver_flags(rr) == driver_flags(ts),
      "rerun %s" % (sorted(driver_flags(rr)),))
check("both driver invocations pass --timeout from "
      "the settings-sourced GAME_TIMEOUT",
      ts.count("--timeout") == 1 and rs.count("--timeout") == 1
      and "--timeout \"$GAME_TIMEOUT\"" in ts
      and "--timeout \"$GAME_TIMEOUT\"" in rs)

# ---- (d) read invocation parity ----
def read_flags(seg):
    return set(re.findall(r"--([a-z][a-z0-9-]*)", seg))


g_read = block(GAMES, "READ.G")
l_read = block(L3, "READ.F")
gf, lf = read_flags(g_read), read_flags(l_read)
check("games read is --primary-only; L3 read is full "
      "mode; the delta is exactly {primary-only} vs "
      "{jobs, labels, games-rows}",
      "primary-only" in gf and "primary-only" not in lf
      and gf - lf == {"primary-only"}
      and lf - gf == {"jobs", "labels", "games-rows"},
      "games %s l3 %s" % (sorted(gf), sorted(lf)))
check("both reads share pairing/games-report/settings/"
      "json-out", {"pairing", "games-report", "settings",
                   "json-out"} <= gf & lf)

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
