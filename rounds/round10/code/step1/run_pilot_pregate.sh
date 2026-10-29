#!/bin/bash
# Round-10 Step 1 pilot GHOST PRE-GATE (step1-pilot-
# package.md sec.5; claude-reply-243b9d8 sec.3.1:
# pre-gate as standard).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of the Step 1
# pilot package at its committed sha and Joe's explicit
# go. run_pilot.sh must not run before this pre-gate
# passes: pregate_check_pilot.py prints IDENTICAL and
# this runner exits 0 only then. The manifest records
# the verdict, the search_s3_thr.php sha256 and the
# exact TEACHER_TUPLE_JSON this pre-gate ran under, so
# run_pilot.sh's PREGATE-GATE block can gate on them
# mechanically.
#
# Arms (paired_driver_gravy.py, Gravy mirror, 87/62,
# seeds 13001-13010): raw seat 1, raw seat 1 rerun, raw
# seat 2 (pristine tree); ghost seat 1 + seat 2 under
# the sec.14 build (search_s3.php); ghost seat 1 +
# seat 2 under the threshold-lifted build
# (search_s3_thr.php). The played pick is the prior's
# in both ghost builds, so the played games must be
# action-identical; the checker reads the divergence
# at the decision level, where identity is required
# on the contested class and divergence is expected
# (and counted) only on newly-contested rows.
# Registry merge of the pre-gate game ids (tag
# r10_step1_pilot_pregate) only on a passed pre-gate.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round10_code/step1}
PGROOT=${PILOT_OUT:-/home/joe/tcg/r10pilot_out}/pregate
# ATTEMPT-RESOLUTION-BEGIN
# Re-run mechanics (fix pass 2, 2026-10-29): attempt 1
# ran in the FLAT layout directly under $PGROOT and
# stays untouched there as the record. Every later
# attempt runs in $PGROOT/attempt<N>, N = one more
# than the highest attempt present (the flat attempt-1
# layout counts as attempt 1 when its check artifact
# is present). PREGATE_ATTEMPT pins N explicitly.
if [ -n "${PREGATE_ATTEMPT:-}" ]; then
  ATTEMPT=$PREGATE_ATTEMPT
else
  ATTEMPT=1
  [ -f "$PGROOT/pregate_check.txt" ] && ATTEMPT=2
  for d in "$PGROOT"/attempt[0-9]*; do
    [ -d "$d" ] || continue
    n=${d##*attempt}
    case "$n" in *[!0-9]*|"") continue ;; esac
    [ "$n" -ge "$ATTEMPT" ] && ATTEMPT=$((n + 1))
  done
fi
OUT=$PGROOT/attempt$ATTEMPT
echo "pre-gate attempt $ATTEMPT -> $OUT"
# ATTEMPT-RESOLUTION-END
GTREE=${GTREE_SRC:-/tmp/gravytree}
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
REG=/home/joe/tcg/registry-vault/do_not_train_registry.json
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

[ ! -f "$OUT/pregate_manifest.json" ] || {
  echo "ABORT: single-shot: pregate_manifest.json already exists in $OUT" >&2; exit 1; }

# --- pre-flight pins ---------------------------------------------
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
expect_hash "$CODE_DIR/search_s3.php" \
  87779e8ec96935776ce35d94ae350647d8f4174c8a17ed572b1bd4887b9a7ba7 \
  "search_s3.php (sec.14 build, pre-gate baseline)"
expect_hash "$CODE_DIR/search_s3_thr.php" \
  4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49 \
  "search_s3_thr.php (threshold-lifted build)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py"
expect_hash "$CODE_DIR/pregate_check_pilot.py" \
  260e0797560c7a0ad8055069833f044bb5bef8594f79a4517227f007140f4299 \
  "pregate_check_pilot.py"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py"
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
for f in search_s3.php search_s3_thr.php \
         paired_driver_gravy.py pregate_check_pilot.py \
         merge_registry.py shm_sweep.py g8_sweep2.sh \
         settings_pilot.json; do
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

# BLOCK:FREESPACE-BEGIN
PER_TREE=$(du -sb "$GTREE" | cut -f1)
NTREES=5
REQUIRED=$((PER_TREE * NTREES))
AVAILABLE=$(df -B1 /tmp | tail -1 | awk '{print $4}')
echo "free-space pre-flight: required_bytes=$REQUIRED (per-tree $PER_TREE x $NTREES trees) available_bytes=$AVAILABLE headroom_factor=1.25"
if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
  echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$REQUIRED x 1.25" >&2
  exit 1
fi
# BLOCK:FREESPACE-END

# --- containment: G8 pre-launch sweep -------------------------
bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_pregate" || exit 1

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

# BLOCK:PG-SRV-BEGIN
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
# BLOCK:PG-SRV-END

# --- trees ------------------------------------------------------
RAW_TREE=/tmp/r10pilot_pg_raw
rm -rf "$RAW_TREE"; cp -r "$GTREE" "$RAW_TREE"
find "$RAW_TREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
expect_hash "$RAW_TREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "pristine tree search.php (raw v10)" || exit 1
for build in 14 thr; do
  for seat in 1 2; do
    tree="/tmp/r10pilot_pg_ghost${build}_s${seat}"
    rm -rf "$tree"; cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    if [ "$build" = 14 ]; then
      cp "$CODE_DIR/search_s3.php" "$tree/search.php"
      expect_hash "$tree/search.php" \
        87779e8ec96935776ce35d94ae350647d8f4174c8a17ed572b1bd4887b9a7ba7 \
        "installed search_s3.php ($tree)" || exit 1
    else
      cp "$CODE_DIR/search_s3_thr.php" "$tree/search.php"
      expect_hash "$tree/search.php" \
        4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49 \
        "installed search_s3_thr.php ($tree)" || exit 1
    fi
    start_sweeper "$tree" "pg_ghost${build}_s${seat}"
  done
done

# --- raw arms (foreground, sequential; raw is fast) -------------
for run in "raw_s1 1" "raw2_s1 1" "raw_s2 2"; do
  set -- $run; tag=$1; seat=$2
  GATE_GAME_IDS_FILE="$OUT/pg_${tag}_ids.txt" \
    $PY "$CODE_DIR/paired_driver_gravy.py" \
      --tree "$RAW_TREE" --sock "$OUT/srv_s${seat}.sock" \
      --seat "$seat" --arm raw --seeds 13001-13010 \
      --deck "$RAW_TREE/$DECK_REL" \
      --out "$OUT/pg_${tag}.jsonl" \
      --logdir "$OUT/pg_${tag}_log" \
      > "$OUT/pg_${tag}.stdout" 2>&1 || exit 1
done

# --- ghost arms (concurrent) -------------------------------------
# Both ghost arms run at --timeout 7845, the pilot's
# registered GAME_TIMEOUT (fix pass 2): attempt 1's
# 1,200 s driver default was sized for the sec.14 arm
# and killed 5 + 3 thr games (the thr arm's max
# COMPLETED wall in attempt 1 was 1,153.3 s -- the
# default was below even that). 7,845 s is 6.8x that
# max, and keeps one timeout story across pre-gate
# and pilot. The sec.14 arm takes the same value:
# its games finish far below either bound, so the
# bound only ever bites on a hang.
# BLOCK:PG-GHOST-BEGIN
PIDS="" FAIL=0
for build in 14 thr; do
  for seat in 1 2; do
    (
      tree="/tmp/r10pilot_pg_ghost${build}_s${seat}"
      GATE_GAME_IDS_FILE="$OUT/pg_ghost${build}_s${seat}_ids.txt" \
        TCG_CLEAN_CHILDREN=1 \
        $PY "$CODE_DIR/paired_driver_gravy.py" \
          --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
          --seat "$seat" --arm ghost --seeds 13001-13010 \
          --deck "$tree/$DECK_REL" --timeout 7845 \
          --out "$OUT/pg_ghost${build}_s${seat}.jsonl" \
          --logdir "$OUT/pg_ghost${build}_s${seat}_log" \
          > "$OUT/pg_ghost${build}_s${seat}.stdout" 2>&1
    ) &
    PIDS="$PIDS $!"
  done
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a ghost arm failed" >&2; exit 1; }
# BLOCK:PG-GHOST-END
for build in 14 thr; do
  for seat in 1 2; do
    touch "$OUT/shm_sweep_pg_ghost${build}_s${seat}.stop"
  done
done

# --- the verdict ---------------------------------------------------
$PY "$CODE_DIR/pregate_check_pilot.py" \
  --rows raw_s1="$OUT/pg_raw_s1.jsonl" \
  --rows raw2_s1="$OUT/pg_raw2_s1.jsonl" \
  --rows raw_s2="$OUT/pg_raw_s2.jsonl" \
  --rows ghost14_s1="$OUT/pg_ghost14_s1.jsonl" \
  --rows ghost14_s2="$OUT/pg_ghost14_s2.jsonl" \
  --rows ghostthr_s1="$OUT/pg_ghostthr_s1.jsonl" \
  --rows ghostthr_s2="$OUT/pg_ghostthr_s2.jsonl" \
  --manifest ghost14_s1="$OUT/pg_ghost14_s1.jsonl.manifest.json" \
  --manifest ghost14_s2="$OUT/pg_ghost14_s2.jsonl.manifest.json" \
  --manifest ghostthr_s1="$OUT/pg_ghostthr_s1.jsonl.manifest.json" \
  --manifest ghostthr_s2="$OUT/pg_ghostthr_s2.jsonl.manifest.json" \
  --stats ghost14_s1="$OUT/pg_ghost14_s1_log/search_stats.jsonl" \
  --stats ghost14_s2="$OUT/pg_ghost14_s2_log/search_stats.jsonl" \
  --stats ghostthr_s1="$OUT/pg_ghostthr_s1_log/search_stats.jsonl" \
  --stats ghostthr_s2="$OUT/pg_ghostthr_s2_log/search_stats.jsonl" \
  > "$OUT/pregate_check.txt" 2>&1 || {
    echo "ABORT: pre-gate NOT IDENTICAL (see $OUT/pregate_check.txt)" >&2
    exit 1; }

# --- registry merge (only for a passed pre-gate) -------------------
cat "$OUT"/pg_*_ids.txt > "$OUT/pg_all_ids.txt"
$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag r10_step1_pilot_pregate --ids "$OUT/pg_all_ids.txt" \
  --vault /home/joe/tcg/registry-vault \
  > "$OUT/registry_merge.txt" 2>&1 || exit 1

# --- manifest -------------------------------------------------------
# MANIFEST-WRITE-BEGIN
$PY - "$OUT" "$CODE_DIR/search_s3_thr.php" "$ATTEMPT" <<'PYEOF'
import glob, hashlib, json, os, sys
out, thr_path = sys.argv[1], sys.argv[2]
attempt = int(sys.argv[3])
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
check_txt = open(out + "/pregate_check.txt").read()
verdict = None
for _l in check_txt.splitlines():
    if _l.startswith("PREGATE: "):
        verdict = _l.split(":", 1)[1].strip()
man = {"stage": "round10-step1-pilot-pregate",
       "attempt": attempt,
       "verdict": verdict,
       "search_s3_thr_sha256": h(thr_path),
       "teacher_tuple_json": os.environ.get("TEACHER_TUPLE_JSON"),
       "check": check_txt,
       "rows": {os.path.basename(p): rows(p) for p in
                sorted(glob.glob(out + "/pg_*.jsonl"))},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/pg_*.jsonl") +
           glob.glob(out + "/pg_*.jsonl.manifest.json") +
           glob.glob(out + "/pregate_check.txt"))}}
json.dump(man, open(out + "/pregate_manifest.json", "w"), indent=1)
print("pregate manifest written")
PYEOF
# MANIFEST-WRITE-END
echo "PILOT PRE-GATE COMPLETE - $OUT/pregate_manifest.json"
