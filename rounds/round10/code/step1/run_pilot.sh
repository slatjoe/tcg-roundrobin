#!/bin/bash
# Round-10 Step 1 PILOT (step1-pilot-package.md;
# claude-reply-243b9d8 sec.3 terms): 100 live
# threshold-lifted-teacher games vs the heuristic,
# Gravy mirror, seeds 25001-25050 x both seats in 4
# blocks, instrument 87/62; every overturn captured;
# L3 (W=50, CRN, production server, sec.14 label
# engine) on ALL captured overturns; the registered
# read (per-class on-trajectory gain, STOP rule,
# Step 2 sizing).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this
# package at its committed sha, a PASSED pilot
# pre-gate (run_pilot_pregate.sh, IDENTICAL --
# enforced mechanically by the PREGATE-GATE block
# below), and Joe's explicit go.
#
# The teacher build is code/step1/search_s3_thr.php
# (the sec.14 build with the uncontested threshold
# lifted, one token) installed into per-block tree
# copies; the tuple is pinned by TEACHER_TUPLE_JSON
# built here from settings_pilot.json (H8k-180+H:
# hooks 8000, deadline 180, horizon 62 at -1, k 25,
# margin 1.5 -- the tuple is IDENTICAL to Stage 3's;
# only the build differs). Overturn capture: the
# runner exports TEACHER_SNAP_DIR per block (the
# driver passes its environment through to the game
# processes; Decide's overturn block snapshots when
# the variable is set). TEACHER_CAPTURE is never
# set: the pilot plays the teacher's picks.
#
# Game timeout 7845 s (settings_pilot.json
# games.timeout_derivation: Stage 2's published
# maximum game wall 2143.2 s x the probe's measured
# 3.66 threshold cost factor, ceiling). Provisional:
# the pilot's own wall tail sets Step 2's timeout.
# Single-shot: this script refuses if its outputs
# already exist in OUT.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round10_code/step1}
ROOT_OUT=${PILOT_OUT:-/home/joe/tcg/r10pilot_out}
OUT=$ROOT_OUT/games
GTREE=${GTREE_SRC:-/tmp/gravytree}
PROD=$SIM/rl/search_server.py
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
REG=/home/joe/tcg/registry-vault/do_not_train_registry.json
GAME_TIMEOUT=7845
LABEL_BASE=700055001
NSHARD=4
SRV_WAIT_TRIES=${SRV_WAIT_TRIES:-60}
mkdir -p "$OUT"

# PINFN-BEGIN
expect_hash() {
  [[ "$2" =~ ^[0-9a-f]{64}$ ]] || {
    echo "ABORT: pin for $3 is not a 64-char sha256 (got ${#2} chars)" >&2; exit 1; }
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
# PINFN-END

# --- single-shot refusal -------------------------------------------
for f in games_manifest.json pilot_read.json pilot_manifest.json; do
  [ ! -f "$ROOT_OUT/$f" ] && [ ! -f "$OUT/$f" ] || {
    echo "ABORT: single-shot: $f already exists (pilot outputs are present)" >&2
    exit 1; }
done

# --- pre-flight pins ---------------------------------------------
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$GTREE/rl/search_server.py" \
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c \
  "patched server (tree copy)"
expect_hash "$GTREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "fleet tree search.php (K2 source)"
expect_hash "$GTREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "fleet tree featurize.php"
expect_hash "$GTREE/play_game.php" \
  4ac2d62ddf64c8e8b6dfb64fac59beb639cb697026aaeb4b968fd91aa707f1d8 \
  "fleet tree play_game.php"
expect_hash "$GTREE/vendor/talishar/ParseGamestate.php" \
  0e88dd584c5c1e4df5ca491d16d5a8c742f85f34efad52b3e51a547cc6acb782 \
  "fleet tree ParseGamestate.php"
expect_hash "$GTREE/$DECK_REL" \
  b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed \
  "fleet tree Gravy deck"
expect_hash "$CKPT" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "Gravy ckpt_v10"
expect_hash "$CODE_DIR/search_s3_thr.php" \
  4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49 \
  "search_s3_thr.php (pilot live teacher build)"
expect_hash "$CODE_DIR/search_s3.php" \
  87779e8ec96935776ce35d94ae350647d8f4174c8a17ed572b1bd4887b9a7ba7 \
  "search_s3.php (sec.14 build; pre-gate baseline record)"
expect_hash "$CODE_DIR/search_s2.php" \
  1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8 \
  "search_s2.php (sec.14 label engine)"
expect_hash "$CODE_DIR/s2_label_main.php" \
  1c1dfd9f9349e8db815f23e31637dee558a9ec36e09179142f71748a6bce72aa \
  "s2_label_main.php (L3 driver, loud loader)"
expect_hash "$CODE_DIR/s1_eval_main.php" \
  0cb9d3c73114d5c6e54e93dd2dc122f20bd06ea8d8968fc4e703e8191b41e853 \
  "s1_eval_main.php (loud loader, sec.3.5)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py"
expect_hash "$CODE_DIR/build_pilot_jobs.py" \
  d855c7aa7155f6aba23027c45180571948325ed13dbd9f01c182b92739c360f5 \
  "build_pilot_jobs.py"
expect_hash "$CODE_DIR/pilot_games_report.py" \
  30bb888ee12b1c0e0a64ea8466ba44d56979849095ff862a460109f81196229a \
  "pilot_games_report.py"
expect_hash "$CODE_DIR/pilot_read.py" \
  69cae8601265a1eb87aadea95589f1d1f07bb3c15c5f19d04bf030a1a495b537 \
  "pilot_read.py"
expect_hash "$CODE_DIR/pregate_check_pilot.py" \
  260e0797560c7a0ad8055069833f044bb5bef8594f79a4517227f007140f4299 \
  "pregate_check_pilot.py"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py"
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "stage0_report.py (taxonomy import)"
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 \
  "analyze_l3.py (bootstrap import)"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17 \
  "g8_sweep2.sh (G8 containment)"
expect_hash "$CODE_DIR/settings_pilot.json" \
  0571e03a31f1d1aa947c3989dba86946bcaf064eff19f523b1b5582d834ca0d7 \
  "settings_pilot.json"

: > "$OUT/deployed_code_hashes.txt"
for f in search_s3_thr.php search_s3.php search_s2.php \
         s2_label_main.php s1_eval_main.php \
         paired_driver_gravy.py build_pilot_jobs.py \
         pilot_games_report.py pilot_read.py \
         pregate_check_pilot.py merge_registry.py \
         stage0_report.py analyze_l3.py g8_sweep2.sh \
         shm_sweep.py settings_pilot.json \
         run_pilot.sh run_pilot_pregate.sh; do
  sha256sum "$CODE_DIR/$f" >> "$OUT/deployed_code_hashes.txt"
done

# TUPLE-BUILD-BEGIN
TEACHER_TUPLE_JSON=$($PY - "$CODE_DIR/settings_pilot.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps(s["teacher_tuple"]))
PYEOF
) || exit 1
export TEACHER_TUPLE_JSON
# TUPLE-BUILD-END

# The pre-gate gate reads the LATEST attempt's
# manifest (fix pass 2): attempt<N> dirs in version
# order; the flat attempt-1 layout (which wrote no
# manifest) is the fallback path.
PREGATE_MANIFEST=$(ls "$ROOT_OUT"/pregate/attempt[0-9]*/pregate_manifest.json 2>/dev/null | sort -V | tail -n 1)
PREGATE_MANIFEST=${PREGATE_MANIFEST:-$ROOT_OUT/pregate/pregate_manifest.json}
PIN_SEARCH_THR_SHA256=4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49

# BLOCK:PREGATE-GATE-BEGIN
[[ "$PIN_SEARCH_THR_SHA256" =~ ^[0-9a-f]{64}$ ]] || {
  echo "ABORT: pre-gate gate pin is not a 64-char sha256" >&2
  exit 1; }
$PY - "$PREGATE_MANIFEST" "$PIN_SEARCH_THR_SHA256" <<'PYEOF' || exit 1
import json, os, sys
man_p, want_sha = sys.argv[1], sys.argv[2]
want_tuple = os.environ.get("TEACHER_TUPLE_JSON", "")
def abort(why):
    sys.stderr.write("ABORT: pre-gate gate: %s\n" % why)
    sys.exit(1)
if not want_tuple:
    abort("TEACHER_TUPLE_JSON is unset in this run")
try:
    man = json.load(open(man_p))
except Exception as e:
    abort("pre-gate manifest absent or unreadable at %s (%s)"
          % (man_p, e))
if man.get("verdict") != "IDENTICAL":
    abort("pre-gate verdict is %r, not IDENTICAL"
          % (man.get("verdict"),))
if man.get("search_s3_thr_sha256") != want_sha:
    abort("pre-gate ran under search_s3_thr.php %s; this run "
          "pins %s" % (man.get("search_s3_thr_sha256"), want_sha))
if man.get("teacher_tuple_json") != want_tuple:
    abort("pre-gate ran under a different TEACHER_TUPLE_JSON "
          "than this run builds from settings_pilot.json")
print("pre-gate gate: manifest IDENTICAL under this run's "
      "search_s3_thr.php pin and tuple - proceeding")
PYEOF
# BLOCK:PREGATE-GATE-END

# BLOCK:FREESPACE-BEGIN
PER_TREE=$(du -sb "$GTREE" | cut -f1)
NTREES=8
REQUIRED=$((PER_TREE * NTREES))
AVAILABLE=$(df -B1 /tmp | tail -1 | awk '{print $4}')
echo "free-space pre-flight: required_bytes=$REQUIRED (per-tree $PER_TREE x $NTREES trees) available_bytes=$AVAILABLE headroom_factor=1.25"
if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
  echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$REQUIRED x 1.25" >&2
  exit 1
fi
# BLOCK:FREESPACE-END

bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_pilot" || exit 1

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

start_sweeper() {
  ipcs -m > "$OUT/ipcs_$2.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$2.txt" > "$OUT/shm_start_$2.txt"
  rm -f "$OUT/shm_sweep_$2.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$2.log" \
    --start-file "$OUT/shm_start_$2.txt" \
    --games-dir "$1/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_$2.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}

# BLOCK:PILOT-SRV-BEGIN
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/srv_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$GTREE/rl/search_server.py" \
    > "$OUT/srv_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 $SRV_WAIT_TRIES); do
    grep -q 'search model loaded' "$OUT/srv_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/srv_s${seat}.log" || {
    echo "ABORT: patched server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/srv_s${seat}.log" || {
    echo "ABORT: patched server seat $seat loaded the wrong model" >&2; exit 1; }
done
# BLOCK:PILOT-SRV-END

# --- trees (one per games block) ---------------------------------
for blk in s1a s1b s2a s2b; do
  tree="/tmp/r10pilot_gm_${blk}"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s3_thr.php" "$tree/search.php"
  expect_hash "$tree/search.php" \
      4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49 \
      "installed search_s3_thr.php ($tree)" || exit 1
  start_sweeper "$tree" "gm_${blk}"
done

# --- the games (4 blocks concurrent) ------------------------------
# BLOCK:PILOT-GAMES-BEGIN
PIDS="" FAIL=0
for spec in "s1a 1 25001-25025" "s1b 1 25026-25050" \
            "s2a 2 25001-25025" "s2b 2 25026-25050"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3
  (
    tree="/tmp/r10pilot_gm_${blk}"
    logdir="$OUT/games_${blk}_log"
    mkdir -p "$logdir/snaps"
    GATE_GAME_IDS_FILE="$OUT/games_${blk}_ids.txt" \
      TCG_CLEAN_CHILDREN=1 \
      TEACHER_SNAP_DIR="$logdir/snaps" \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
        --seat "$seat" --arm teacher --seeds "$seeds" \
        --deck "$tree/$DECK_REL" --timeout $GAME_TIMEOUT \
        --out "$OUT/games_${blk}.jsonl" \
        --logdir "$logdir" \
        > "$OUT/games_${blk}.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a games block failed" >&2; exit 1; }
# BLOCK:PILOT-GAMES-END
for blk in s1a s1b s2a s2b; do touch "$OUT/shm_sweep_gm_${blk}.stop"; done

# --- registry merge BEFORE analysis -------------------------------
$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag r10_step1_pilot \
  --ids "$OUT/games_s1a_ids.txt" --ids "$OUT/games_s1b_ids.txt" \
  --ids "$OUT/games_s2a_ids.txt" --ids "$OUT/games_s2b_ids.txt" \
  --vault /home/joe/tcg/registry-vault \
  > "$OUT/registry_merge.txt" 2>&1 || exit 1

# --- games report (tuple audit + walls + class tallies) ------------
$PY "$CODE_DIR/pilot_games_report.py" --out-dir "$OUT" \
  --settings "$CODE_DIR/settings_pilot.json" \
  --json-out "$OUT/games_report.json" \
  > "$OUT/games_report.txt" 2>&1 || {
    echo "ABORT: games report failed (tuple audit?)" >&2
    cat "$OUT/games_report.txt" >&2; exit 1; }

# =====================================================================
# L3: every captured overturn, W=50 CRN, production server,
# sec.14 label engine (search_s2.php), seed family
# 570055001 + shard x 10^8.
# =====================================================================
L3=$ROOT_OUT/l3
mkdir -p "$L3"

STREAM_ARGS=""
STAT_ARGS=""
for blk in s1a s1b s2a s2b; do
  STREAM_ARGS="$STREAM_ARGS --stream $OUT/games_${blk}_log/snaps=$OUT/games_${blk}_log/snaps/teacher_snap_index.jsonl"
  STAT_ARGS="$STAT_ARGS --stats $OUT/games_${blk}_log/search_stats.jsonl"
done
$PY "$CODE_DIR/build_pilot_jobs.py" $STREAM_ARGS $STAT_ARGS \
  --settings "$CODE_DIR/settings_pilot.json" \
  --out "$L3/jobs_all.jsonl" --shard-prefix "$L3/jobs_shard" \
  --report "$L3/jobs_report.json" --nshard $NSHARD || exit 1

$PY - "$L3" "$NSHARD" <<'PYEOF' || exit 1
import json, os, sys
out, nshard = sys.argv[1], int(sys.argv[2])
for s in range(nshard):
    src = f"{out}/jobs_shard{s}.jsonl"
    jobs = [json.loads(l) for l in open(src) if l.strip()]
    for p in (1, 2):
        sel = [j for j in jobs if int(j["player"]) == p]
        with open(f"{out}/jobs_shard{s}_p{p}.jsonl", "w") as f:
            for j in sel:
                assert os.path.isdir(j["snap_dir"]), \
                    f"snap dir missing: {j['snap_dir']}"
                f.write(json.dumps(j, allow_nan=False) + "\n")
        print(f"shard {s} player {p}: {len(sel)} jobs")
PYEOF

# BLOCK:PILOT-LABEL-SRV-BEGIN
for seat in 1 2; do
  TCG_POLICY_SOCK="$L3/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$PROD" > "$L3/prod_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 $SRV_WAIT_TRIES); do
    grep -q 'search model loaded' "$L3/prod_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$L3/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$L3/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat loaded the wrong model" >&2; exit 1; }
done
# BLOCK:PILOT-LABEL-SRV-END

for s in 0 1 2 3; do
  tree="/tmp/r10pilot_l3_tree_$s"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  cp "$CODE_DIR/s2_label_main.php" "$tree/"
  expect_hash "$tree/search.php" \
      1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8 \
      "installed search_s2.php (label tree $s)" || exit 1
  start_sweeper "$tree" "l3_$s"
done

# BLOCK:PILOT-LABEL-BEGIN
PIDS="" FAIL=0
for s in 0 1 2 3; do
  (
    tree="/tmp/r10pilot_l3_tree_$s"
    for p in 1 2; do
      : > "$L3/labels_shard${s}_p$p.jsonl"
      (cd "$tree" && MEAS_JOBS="$L3/jobs_shard${s}_p$p.jsonl" \
         MEAS_OUT="$L3/labels_shard${s}_p$p.jsonl" \
         EVAL_STATS="$L3/label_stats_shard${s}_p$p.jsonl" \
         MEAS_SEED=$((LABEL_BASE + s * 100000000)) \
         TCG_POLICY_SOCK="$L3/prod_s$p.sock" \
         EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
         EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
         EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
         php s2_label_main.php \
           "$tree/$DECK_REL" "$tree/$DECK_REL" \
           --policy-search --games 1 \
           > "$L3/label_shard${s}_p$p.err" 2>&1) || exit 1
    done
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: an L3 label shard failed" >&2; exit 1; }
# BLOCK:PILOT-LABEL-END
for s in 0 1 2 3; do touch "$OUT/shm_sweep_l3_$s.stop"; done
cat "$L3"/labels_shard*_p*.jsonl > "$L3/labels_all.jsonl"

# --- the read ---------------------------------------------------------
$PY "$CODE_DIR/pilot_read.py" --jobs "$L3/jobs_all.jsonl" \
  --labels "$L3/labels_all.jsonl" \
  --games-rows "$OUT/games_s1a.jsonl" "$OUT/games_s1b.jsonl" \
    "$OUT/games_s2a.jsonl" "$OUT/games_s2b.jsonl" \
  --games-report "$OUT/games_report.json" \
  --settings "$CODE_DIR/settings_pilot.json" \
  --json-out "$ROOT_OUT/pilot_read.json" \
  > "$ROOT_OUT/pilot_read.txt" 2>&1 || {
    echo "ABORT: pilot read failed" >&2
    cat "$ROOT_OUT/pilot_read.txt" >&2; exit 1; }
cat "$ROOT_OUT/pilot_read.txt"

# --- manifest ---------------------------------------------------------
$PY - "$ROOT_OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
man = {"stage": "round10-step1-pilot",
       "games_report": json.load(open(out + "/games/games_report.json")),
       "jobs": json.load(open(out + "/l3/jobs_report.json")),
       "read": json.load(open(out + "/pilot_read.json")),
       "labels_rows": rows(out + "/l3/labels_all.jsonl"),
       "rows": {os.path.basename(p): rows(p) for p in sorted(
           glob.glob(out + "/games/games_*.jsonl") +
           glob.glob(out + "/l3/jobs_*.jsonl") +
           glob.glob(out + "/l3/labels_*.jsonl"))},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/games/games_*.jsonl") +
           glob.glob(out + "/games/games_report.json") +
           glob.glob(out + "/l3/jobs_*.jsonl") +
           glob.glob(out + "/l3/labels_*.jsonl") +
           glob.glob(out + "/pilot_read.json") +
           glob.glob(out + "/games/games_*_log/search_stats.jsonl") +
           glob.glob(out + "/games/games_*_log/snaps/"
                     "teacher_snap_index.jsonl"))}}
json.dump(man, open(out + "/pilot_manifest.json", "w"), indent=1)
print("pilot manifest written")
PYEOF
echo "STEP 1 PILOT COMPLETE - $ROOT_OUT/pilot_manifest.json"
