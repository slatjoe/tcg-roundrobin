#!/bin/bash
# fx_s3_blocks - verbatim-extraction fixtures for EVERY
# spawn/wait block in the two Stage 3 runners (the fx_s2_blocks
# pattern), plus the PREGATE-GATE round-trip against the REAL
# Stage 2 pre-gate manifest and the FREESPACE pre-flight
# cases. For each runner:
#   * the block inventory must equal the expected table;
#   * neither runner (nor g8_sweep2.sh) may contain the
#     three-name assignment form `FAIL=0 pid`;
#   * the FREESPACE block must sit BEFORE the first tree copy
#     (line-order check);
#   * each extracted block is EXECUTED verbatim in a sandbox
#     with stubbed externals.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
CODE="$FX/../code"
R9="$FX/.."
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAIL=0
FX_STUB_MARKERS="$WORK/markers.txt"
FX_STUB_TAGFILE="$WORK/tag"
FX_STUB_DRAFT="$WORK/draft.json"
export FX_STUB_MARKERS FX_STUB_TAGFILE FX_STUB_DRAFT
note() { echo "$1"; }
bad() { echo "FAIL $1"; FAIL=1; }

# ---- stub python: behavior by argv --------------------------
mkdir -p "$WORK/stub" "$WORK/gtree"
cat > "$WORK/stub/py" <<'STUBEOF'
#!/bin/bash
# Stub for $PY. Server mode: print the load lines to stdout.
# Sweeper mode: marker, exit 0. Driver mode: worker marker,
# exit per FX_STUB_FAIL_<TAG>. Report --pairing-only: plant
# the fixture's draft pairing. Bare "-": run the REAL python
# on stdin (the blocks' inline list builders).
for a in "$@"; do
  case "$a" in
    *search_server.py)
      [ -n "${FX_STUB_SILENT:-}" ] || {
        echo "search model loaded (/x/ckpt_v10.pt)"
        echo "ckpt_v10 served"; }
      exit 0;;
    *shm_sweep.py)
      echo "sweeper $$" >> "$FX_STUB_MARKERS"
      exit 0;;
    *stage3_games_report.py)
      outdir=""
      prev=""
      for b in "$@"; do
        [ "$prev" = "--out-dir" ] && outdir="$b"
        prev="$b"
      done
      cp "$FX_STUB_DRAFT" "$outdir/pairing_draft.json"
      echo "report draft" >> "$FX_STUB_MARKERS"
      exit 0;;
    *paired_driver_gravy.py)
      tag=""
      for b in "$@"; do case "$b" in
        *games_*.jsonl) tag=$(basename "$b" .jsonl);;
      esac; done
      echo "worker $tag" >> "$FX_STUB_MARKERS"
      eval "fv=\${FX_STUB_FAIL_$tag:-}"
      [ -n "$fv" ] && exit 1
      exit 0;;
    -)
      shift; exec python3 - "$@";;
    *)
      exit 0;;
  esac
done
exit 0
STUBEOF
chmod +x "$WORK/stub/py"
mkdir -p "$WORK/stubbin"
cat > "$WORK/stubbin/php" <<'STUBEOF'
#!/bin/bash
tag=$(basename "${MEAS_OUT:-none}" .jsonl)
echo "worker php $tag" >> "$FX_STUB_MARKERS"
eval "fv=\${FX_STUB_FAIL_$tag:-}"
[ -n "$fv" ] && exit 1
exit 0
STUBEOF
chmod +x "$WORK/stubbin/php"
for s in 0 1 2 3; do mkdir -p "/tmp/r9s3_l3_tree_$s"; done
sleep() { :; }
export -f sleep 2>/dev/null || true

extract() {
  awk "/# BLOCK:$2-BEGIN/{f=1;next} /# BLOCK:$2-END/{f=0} f" "$1" > "$3"
  [ -s "$3" ]
}

run_block() { # name runner blockid extra_env...
  local name=$1 runner=$2 blk=$3; shift 3
  local bf="$WORK/blk_$blk.sh"
  extract "$runner" "$blk" "$bf" || { bad "$name extraction empty"; return 1; }
  : > "$FX_STUB_MARKERS"
  ( export PY="$WORK/stub/py" OUT="$WORK/out_$blk" CODE_DIR="$CODE" \
      SIM="$WORK/sim" GTREE="$WORK/gtree" CKPT="/x/ckpt_v10.pt" \
      PROD="$WORK/search_server.py" LABEL_BASE=1055001 NSHARD=4 \
      GAME_TIMEOUT=3214 SRV_WAIT_TRIES=3 SRV_PIDS="999991 999992" \
      PATH="$WORK/stubbin:$PATH" \
      FX_STUB_MARKERS FX_STUB_TAGFILE="$WORK/tag" FX_STUB_DRAFT "$@"
    mkdir -p "$OUT"
    bash "$bf" )
}

declare -A EXPECT=(
  [run_stage3_games.sh]="FREESPACE PREGATE-GATE RAW-RERUN RS-DRIVERS RS-SRV RS-SWEEP TS-DRIVERS TS-SRV TS-SWEEP"
  [run_stage3_l3.sh]="FREESPACE LS-SHARD LS-SRV LS-SWEEP"
)
for runner in run_stage3_games.sh run_stage3_l3.sh; do
  if grep -n "FAIL=0 pid" "$CODE/$runner" > /dev/null; then
    bad "$runner contains the lethal three-name form"
  else
    note "PASS $runner: no three-name assignment form"
  fi
  got=$(grep -o "# BLOCK:[A-Z0-9-]*-BEGIN" "$CODE/$runner" \
        | sed 's/# BLOCK://; s/-BEGIN//' | sort | tr '\n' ' ')
  want=$(echo "${EXPECT[$runner]}" | tr ' ' '\n' | sort | tr '\n' ' ')
  if [ "$got" = "$want" ]; then
    note "PASS $runner block inventory: $got"
  else
    bad "$runner block inventory: got [$got] want [$want]"
  fi
  fs_line=$(grep -n "# BLOCK:FREESPACE-BEGIN" "$CODE/$runner" | cut -d: -f1)
  cp_line=$(grep -n "cp -r" "$CODE/$runner" | head -1 | cut -d: -f1)
  if [ -n "$fs_line" ] && [ -n "$cp_line" ] && [ "$fs_line" -lt "$cp_line" ]; then
    note "PASS $runner: FREESPACE (line $fs_line) before first tree copy (line $cp_line)"
  else
    bad "$runner: FREESPACE not before first tree copy (fs=$fs_line cp=$cp_line)"
  fi
done
if grep -n "FAIL=0 pid" "$CODE/g8_sweep2.sh" > /dev/null; then
  bad "g8_sweep2.sh contains the lethal three-name form"
else
  note "PASS g8_sweep2.sh: no three-name assignment form"
fi

# ---- server blocks: loaded stub passes, silent stub aborts --
for pair in "run_stage3_games.sh TS-SRV" "run_stage3_games.sh RS-SRV" "run_stage3_l3.sh LS-SRV"; do
  set -- $pair
  if run_block "$2-ok" "$CODE/$1" "$2" > "$WORK/$2_ok.log" 2>&1; then
    note "PASS $2: stub server loads -> block completes"
  else
    bad "$2: stub server loads -> block failed"; sed -n 1,3p "$WORK/$2_ok.log"
  fi
  if FX_STUB_SILENT=1 run_block "$2-silent" "$CODE/$1" "$2" > "$WORK/$2_silent.log" 2>&1; then
    bad "$2: silent server -> block should have aborted"
  else
    note "PASS $2: silent server -> block aborts"
  fi
done

# ---- sweeper blocks: one PID per tree ------------------------
for pair in "run_stage3_games.sh TS-SWEEP 4" "run_stage3_games.sh RS-SWEEP 4" "run_stage3_l3.sh LS-SWEEP 4"; do
  set -- $pair
  run_block "$2" "$CODE/$1" "$2" > "$WORK/$2.log" 2>&1
  n=0
  for i in $(seq 1 100); do
    n=$(grep -c sweeper "$FX_STUB_MARKERS" 2>/dev/null || echo 0)
    [ "$n" -ge "$3" ] && break
    python3 -c "import time; time.sleep(0.05)"
  done
  if [ "$n" = "$3" ]; then
    note "PASS $2: $3 sweepers spawned"
  else
    bad "$2: sweeper spawn count (got $n, want $3)"; sed -n 1,3p "$WORK/$2.log"
  fi
done

# ---- driver / shard blocks -----------------------------------
run_workers_env() { # name runner blockid n failvar
  local name=$1 runner=$2 blk=$3 n=$4 fvar=$5
  if run_block "$name" "$runner" "$blk" > "$WORK/$blk.log" 2>&1 \
     && [ "$(grep -c worker "$FX_STUB_MARKERS")" = "$n" ]; then
    note "PASS $name: $n workers ran, block completes"
  else
    bad "$name: happy path"; sed -n 1,3p "$WORK/$blk.log"
  fi
  if env "$fvar=1" run_block "$name-fail" "$runner" "$blk" \
       > "$WORK/${blk}_fail.log" 2>&1; then
    bad "$name: a failing worker must fail the block"
  else
    note "PASS $name: a failing worker fails the block"
  fi
}
run_workers_env "TS-DRIVERS" "$CODE/run_stage3_games.sh" TS-DRIVERS 4 FX_STUB_FAIL_games_t1a
run_workers_env "RS-DRIVERS" "$CODE/run_stage3_games.sh" RS-DRIVERS 4 FX_STUB_FAIL_games_r1a
run_workers_env "LS-SHARD" "$CODE/run_stage3_l3.sh" LS-SHARD 8 FX_STUB_FAIL_labels_shard0_p1

# ---- RAW-RERUN: draft-driven reruns ---------------------------
plant_draft() { # timeout|none
  python3 - "$FX_STUB_DRAFT" "$1" <<'PYEOF'
import json, sys
kind = sys.argv[2]
if kind == "timeout":
    row = {"seed": 23003, "arm": "raw", "seat": 1,
           "invalid": "timeout"}
else:
    row = {"seed": 23003, "arm": "raw", "seat": 1,
           "gamename": "fxrr", "winner": 2, "draw": 0}
pairs = [{"seed": 23003, "seat": 1, "teacher": None,
          "raw": {"file": "games_r1a.jsonl",
                  "gamename": row.get("gamename"), "row": row},
          "status": "excluded", "reason": "planted"}]
json.dump({"pairs": pairs, "counts": {"pairs_attempted": 1,
          "by_status": {}}, "stat_files": [], "rerun_files": []},
          open(sys.argv[1], "w"))
PYEOF
}
plant_draft timeout
if run_block "RAW-RERUN-one" "$CODE/run_stage3_games.sh" RAW-RERUN \
     > "$WORK/rerun_one.log" 2>&1 \
   && [ "$(grep -c worker "$FX_STUB_MARKERS")" = "1" ]; then
  note "PASS RAW-RERUN: one raw timeout in draft -> exactly 1 rerun worker"
else
  bad "RAW-RERUN one-timeout case"; sed -n 1,5p "$WORK/rerun_one.log"
fi
plant_draft none
if run_block "RAW-RERUN-none" "$CODE/run_stage3_games.sh" RAW-RERUN \
     > "$WORK/rerun_none.log" 2>&1 \
   && [ "$(grep -c worker "$FX_STUB_MARKERS")" = "0" ]; then
  note "PASS RAW-RERUN: no raw timeouts in draft -> 0 rerun workers"
else
  bad "RAW-RERUN no-timeout case"; sed -n 1,5p "$WORK/rerun_none.log"
fi

# ---- PREGATE-GATE: the REAL Stage 2 manifest, verbatim block --
GATE_TUPLE=$(python3 -c 'import json, sys; print(json.dumps(json.load(open(sys.argv[1]))["teacher_tuple"]))' "$CODE/settings_stage3.json")
GATE_SHA=85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa
REAL_MAN="$R9/data/stage2/pregate_manifest.json"
gate_case() { # name manifest_path want(pass|abort)
  local name=$1 mf=$2 want=$3 rc
  if run_block "PREGATE-GATE-$name" "$CODE/run_stage3_games.sh" \
       PREGATE-GATE "PY=python3" "PREGATE_MANIFEST=$mf" \
       "PIN_SEARCH_S2_SHA256=$GATE_SHA" \
       "TEACHER_TUPLE_JSON=$GATE_TUPLE" \
       > "$WORK/gate_$name.log" 2>&1; then rc=0; else rc=1; fi
  if { [ "$want" = pass ] && [ "$rc" = 0 ]; } || \
     { [ "$want" = abort ] && [ "$rc" = 1 ]; }; then
    note "PASS PREGATE-GATE $name (want $want, block exit $rc)"
  else
    bad "PREGATE-GATE $name (want $want, block exit $rc)"
    sed -n 1,3p "$WORK/gate_$name.log"
  fi
}
mkdir -p "$WORK/gate_real"
cp "$REAL_MAN" "$WORK/gate_real/pregate_manifest.json"
gate_case real "$WORK/gate_real/pregate_manifest.json" pass
python3 - "$WORK" <<'PYEOF'
import json, os, sys
w = sys.argv[1]
man = json.load(open(os.path.join(w, "gate_real",
                                  "pregate_manifest.json")))
for name, mut in (("verdict", lambda m: m.update(
        verdict="NOT IDENTICAL")),
                  ("sha", lambda m: m.update(
        search_s2_sha256="0" * 64)),
                  ("tuple", lambda m: m.update(
        teacher_tuple_json=m["teacher_tuple_json"].replace(
            "1.5", "2.5")))):
    d = os.path.join(w, "gate_" + name)
    os.makedirs(d, exist_ok=True)
    m2 = dict(man)
    mut(m2)
    json.dump(m2, open(os.path.join(d, "pregate_manifest.json"), "w"))
PYEOF
gate_case verdict "$WORK/gate_verdict/pregate_manifest.json" abort
gate_case sha "$WORK/gate_sha/pregate_manifest.json" abort
gate_case tuple "$WORK/gate_tuple/pregate_manifest.json" abort
gate_case absent "$WORK/gate_absent/pregate_manifest.json" abort

# ---- FREESPACE: verbatim block, both branches -----------------
fs_case() { # name runner req avail want(pass|abort) want_req
  local name=$1 runner=$2 req=$3 avail=$4 want=$5 wreq=$6 rc
  if run_block "FREESPACE-$name" "$runner" FREESPACE \
       "S3_REQ_PER_TREE_OVERRIDE=$req" \
       "S3_DF_AVAIL_OVERRIDE=$avail" \
       > "$WORK/fs_$name.log" 2>&1; then rc=0; else rc=1; fi
  if { [ "$want" = pass ] && [ "$rc" = 0 ]; } || \
     { [ "$want" = abort ] && [ "$rc" = 1 ]; } \
     && grep -q "required_bytes=$wreq" "$WORK/fs_$name.log" \
     && grep -q "available_bytes=$avail" "$WORK/fs_$name.log"; then
    note "PASS FREESPACE $name (want $want; required_bytes=$wreq available_bytes=$avail printed)"
  else
    bad "FREESPACE $name (want $want, exit $rc)"; sed -n 1,3p "$WORK/fs_$name.log"
  fi
}
fs_case games-huge "$CODE/run_stage3_games.sh" 1000 1000000000 pass 8000
fs_case games-tiny "$CODE/run_stage3_games.sh" 1000 1 abort 8000
fs_case games-straddle "$CODE/run_stage3_games.sh" 1000 9999 abort 8000
fs_case games-boundary "$CODE/run_stage3_games.sh" 1000 10000 pass 8000
fs_case l3-straddle-proceeds "$CODE/run_stage3_l3.sh" 1000 9999 pass 4000
fs_case l3-tiny "$CODE/run_stage3_l3.sh" 1000 4999 abort 4000

rmdir /tmp/r9s3_l3_tree_0 /tmp/r9s3_l3_tree_1 \
      /tmp/r9s3_l3_tree_2 /tmp/r9s3_l3_tree_3 2>/dev/null
echo "FX-S3-BLOCKS: $([ $FAIL = 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
