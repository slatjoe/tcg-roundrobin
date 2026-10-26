#!/bin/bash
# fx_b0_gate - the runner's B0 stop condition (ruling
# sec.4.4, as ruled in claude-reply-edddf5e sec.4.4): B0
# IS the smoke. If B0's pass aborts (an eval-shard exit,
# in the runner) OR B0's rows fail any analyzer integrity
# check, the runner stops BEFORE the +H settings instead
# of continuing in file order.
#
# This fixture does not re-implement the gate: it
# EXTRACTS the runner's own block (between the
# B0GATE-BEGIN / B0GATE-END markers in
# code/run_stage1.sh) and executes it verbatim against
# planted B0 outputs in stub $OUT dirs:
#   case 1  intact B0 rows, more settings follow:
#           exit 0, "B0 gate PASSED", gate report written
#           (the run would proceed to the +H settings).
#   case 2  one stat row's cand_finished corrupted (the
#           world rows disagree): the analyzer aborts
#           inside the block; the block exits 1 with the
#           ABORT line naming the stop before the +H
#           settings.
#   case 3  B0 is the only setting (NSETTINGS=1): no-op,
#           exit 0, no gate files (nothing follows B0).
#   case 4  a later setting's iteration (NAME=B0+H):
#           no-op, exit 0, no gate files.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$FX/../code/run_stage1.sh"
CODE="$(cd "$FX/../code" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAIL=0
check() { # name condition...
  local name=$1; shift
  if "$@"; then echo "PASS $name"; else echo "FAIL $name"; FAIL=1; fi
}

# --- extract the runner's own gate block ----------------
sed -n '/# B0GATE-BEGIN/,/# B0GATE-END/p' "$RUNNER" \
  > "$WORK/gate.sh"
grep -q 'stage1_analyze.py' "$WORK/gate.sh" \
  && grep -q 'B0 gate PASSED' "$WORK/gate.sh" \
  || { echo "FAIL extraction (gate block not found)"; exit 1; }
echo "PASS extraction (the runner's B0GATE block, verbatim)"

# --- plant B0 outputs: good/ and bad/ -------------------
python3 - "$WORK" "$CODE" <<'PYEOF'
import json, os, sys
work, code = sys.argv[1], sys.argv[2]
spec = json.load(open(os.path.join(code, "settings_stage1.json")))
b0 = [s for s in spec["settings"] if s["name"] == "B0"][0]
tuple_ = {k: b0[k] for k in ("name", "hooks", "deadline_s",
                             "horizon", "horizon_value", "k")}

def fin(o):
    return {"finished": 1, "outcome": o,
            "winner": 1 if o > 0 else 2, "fallbacks": 0}

states = [("sA", "gA", 1), ("sB", "gB", 2)]
for tag, corrupt in (("good", False), ("bad", True)):
    d = os.path.join(work, tag)
    os.makedirs(d)
    with open(os.path.join(d, "panel_jobs.jsonl"), "w") as f:
        for snap, g, p in states:
            f.write(json.dumps(
                {"snap_dir": "/fx/" + snap, "snap": snap,
                 "game": g, "player": p, "branch": "P",
                 "turn": 7, "cands": [0, 1, 2],
                 "selected": [0, 1], "prior_pick": 0}) + "\n")
    with open(os.path.join(d, "evals_B0.jsonl"), "w") as f:
        for snap, g, p in states:
            for cand in (0, 1):
                for w in range(25):
                    o = 1.0 if (w + cand) % 2 == 0 else -1.0
                    f.write(json.dumps(
                        {"snap": snap, "cand": cand, "world": w,
                         "result": fin(o),
                         "setting": tuple_}) + "\n")
    with open(os.path.join(d, "stats_B0.jsonl"), "w") as f:
        for snap, g, p in states:
            cf = {"0": 25, "1": 25}
            if corrupt and snap == "sA":
                cf["0"] = 24  # world rows give 25: the
                # analyzer's stat cross-check must abort
            f.write(json.dumps(
                {"snap": snap, "game": g, "player": p,
                 "branch": "P", "setting": tuple_,
                 "wall_ms": 5000, "cand_finished": cf,
                 "cand_rows": {"0": 25, "1": 25},
                 "errors": {}, "fallbacks": 0,
                 "prior_pick": 0, "selected": [0, 1]}) + "\n")
print("planted good/ and bad/ B0 outputs")
PYEOF

run_gate() { # outdir NAME NSETTINGS -> stdout+stderr, rc
  ( cd "$1" && env PY=python3 CODE_DIR="$CODE" OUT="$1" \
      NAME="$2" NSETTINGS="$3" \
      bash "$WORK/gate.sh" ) 2>&1
}

# --- case 1: intact B0, grid follows -> proceeds --------
out1=$(run_gate "$WORK/good" B0 6); rc1=$?
[ $rc1 -eq 0 ]; check "case1 exit 0 (gate passes, run proceeds)" test $? -eq 0
case "$out1" in *"B0 gate PASSED"*) echo "PASS case1 'B0 gate PASSED' printed";; *) echo "FAIL case1 output: $out1"; FAIL=1;; esac
check "case1 gate report + B0-only settings written" \
  test -s "$WORK/good/b0_gate_report.json"
python3 - "$WORK/good/b0_gate_settings.json" <<'PYEOF'
import json, sys
spec = json.load(open(sys.argv[1]))
assert [s["name"] for s in spec["settings"]] == ["B0"], spec
print("PASS case1 B0-only settings file holds exactly B0")
PYEOF
[ $? -eq 0 ] || FAIL=1

# --- case 2: corrupted B0 stats -> stops before +H ------
out2=$(run_gate "$WORK/bad" B0 6); rc2=$?
[ $rc2 -eq 1 ]; check "case2 exit 1 (gate stops the run)" test $? -eq 0
case "$out2" in *"stopping BEFORE the +H settings"*) echo "PASS case2 ABORT line names the stop before the +H settings";; *) echo "FAIL case2 output: $out2"; FAIL=1;; esac
grep -q "ABORT" "$WORK/bad/b0_gate_report.txt"
check "case2 gate report carries the analyzer's ABORT" test $? -eq 0

# --- case 3: B0 alone -> no-op ---------------------------
mkdir -p "$WORK/only"
out3=$(run_gate "$WORK/only" B0 1); rc3=$?
[ $rc3 -eq 0 ] && [ ! -e "$WORK/only/b0_gate_settings.json" ]
check "case3 B0-only run: no-op, exit 0, no gate files" test $? -eq 0

# --- case 4: a +H iteration -> no-op ---------------------
mkdir -p "$WORK/later"
out4=$(run_gate "$WORK/later" "B0+H" 6); rc4=$?
[ $rc4 -eq 0 ] && [ ! -e "$WORK/later/b0_gate_settings.json" ]
check "case4 +H iteration: no-op, exit 0, no gate files" test $? -eq 0

echo "FX-B0-GATE: $([ $FAIL -eq 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
