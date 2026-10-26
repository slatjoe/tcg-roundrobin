#!/bin/bash
# Round-9 Stage 2 GHOST PRE-GATE (design sec.5; ruling
# sec.3.3; clause 9 of claude-reply-16f02e2): the new live
# teacher build (code/search_s2.php) at the registered tuple
# must be ACTION-IDENTICAL to raw v10 through the standard
# instruments, read under K6 (claude-reply-1ab9903 sec.2).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage 2
# package at its committed sha and Joe's explicit go. The
# games runner (run_stage2_games.sh) must not run before
# this pre-gate passes: pregate_check.py prints IDENTICAL
# and this runner exits 0 only then.
#
# Arms (paired_driver_gravy.py, Gravy mirror, instrument
# 87/62): raw seat 1 (seeds 8501-8510, the round-7 pre-gate
# block), raw seat 1 rerun (determinism), raw seat 2 (R16
# seat-crossed control) -- all in a pristine fleet-tree copy;
# ghost seat 1 + seat 2 (TEACHER_GHOST, tuple pinned via
# TEACHER_TUPLE_JSON from settings_stage2.json) in tree
# copies carrying search_s2.php. Servers: the tree's patched
# rl/search_server.py (ab85fa1b...), one per seat, ckpt_v10.
# Containment: G8 pre-launch sweep + one (C) sweeper per
# ghost tree. The run's game ids are merged into the
# registry (tag round9-stage2) when the check passes.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
OUT=${STAGE2_OUT:-/home/joe/tcg/r9s2_out}/pregate
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
expect_hash "$CODE_DIR/search_s2.php" \
  85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
  "search_s2.php (Stage 2 live teacher build)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py"
expect_hash "$CODE_DIR/pregate_check.py" \
  bc5327d380dfe73308ac2ce737e527a568c0de42a8f80f82d8775f481290496a \
  "pregate_check.py"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/settings_stage2.json" \
  2a1634ccbe67cf2f16993a1e38fc4df6005c492cb9dd769d59c9b3c19cd72f50 \
  "settings_stage2.json"

{
  echo "stage round9-stage2-pregate"
  sha256sum "$CODE_DIR"/settings_stage2.json "$CODE_DIR"/*.php \
    "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
  echo "registry $REG (recorded in the manifest, pre/post)"
} > "$OUT/deployed_code_hashes.txt"

# --- the run tuple, from the settings file (one source) -----
TEACHER_TUPLE_JSON=$($PY - "$CODE_DIR/settings_stage2.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps(s["teacher_tuple"]))
PYEOF
) || exit 1
export TEACHER_TUPLE_JSON

# --- containment: G8 pre-launch sweep -------------------------
bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

# BLOCK:PS-SRV-BEGIN
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
# BLOCK:PS-SRV-END

# --- trees ------------------------------------------------------
RAW_TREE=/tmp/r9s2_pg_raw
rm -rf "$RAW_TREE"; cp -r "$GTREE" "$RAW_TREE"
find "$RAW_TREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
expect_hash "$RAW_TREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "pristine tree search.php (raw v10)" || exit 1
for seat in 1 2; do
  tree="/tmp/r9s2_pg_ghost_s${seat}"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  expect_hash "$tree/search.php" \
      85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
      "installed search_s2.php ($tree)" || exit 1
done

# BLOCK:PS-SWEEP-BEGIN
for seat in 1 2; do
  tree="/tmp/r9s2_pg_ghost_s${seat}"
  ipcs -m > "$OUT/ipcs_pg_s${seat}.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_pg_s${seat}.txt" \
    > "$OUT/shm_start_pg_s${seat}.txt"
  rm -f "$OUT/shm_sweep_pg_s${seat}.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_pg_s${seat}.log" \
    --start-file "$OUT/shm_start_pg_s${seat}.txt" \
    --games-dir "$tree/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_pg_s${seat}.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
done
# BLOCK:PS-SWEEP-END

# --- raw arms (foreground, sequential; raw is fast) -------------
for run in "raw_s1 1" "raw2_s1 1" "raw_s2 2"; do
  set -- $run; tag=$1; seat=$2
  GATE_GAME_IDS_FILE="$OUT/pg_${tag}_ids.txt" \
    $PY "$CODE_DIR/paired_driver_gravy.py" \
      --tree "$RAW_TREE" --sock "$OUT/srv_s${seat}.sock" \
      --seat "$seat" --arm raw --seeds 8501-8510 \
      --deck "$RAW_TREE/$DECK_REL" \
      --out "$OUT/pg_${tag}.jsonl" \
      --logdir "$OUT/pg_${tag}_log" \
      > "$OUT/pg_${tag}.stdout" 2>&1 || exit 1
done

# --- ghost arms (concurrent, one per seat) ------------------------
# BLOCK:PS-GHOST-BEGIN
PIDS="" FAIL=0
for seat in 1 2; do
  (
    tree="/tmp/r9s2_pg_ghost_s${seat}"
    GATE_GAME_IDS_FILE="$OUT/pg_ghost_s${seat}_ids.txt" \
      TCG_CLEAN_CHILDREN=1 \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
        --seat "$seat" --arm ghost --seeds 8501-8510 \
        --deck "$tree/$DECK_REL" \
        --out "$OUT/pg_ghost_s${seat}.jsonl" \
        --logdir "$OUT/pg_ghost_s${seat}_log" \
        > "$OUT/pg_ghost_s${seat}.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a ghost arm failed" >&2; exit 1; }
# BLOCK:PS-GHOST-END
for seat in 1 2; do touch "$OUT/shm_sweep_pg_s${seat}.stop"; done

# --- the verdict ---------------------------------------------------
$PY "$CODE_DIR/pregate_check.py" \
  --rows raw_s1="$OUT/pg_raw_s1.jsonl" \
  --rows raw2_s1="$OUT/pg_raw2_s1.jsonl" \
  --rows raw_s2="$OUT/pg_raw_s2.jsonl" \
  --rows ghost_s1="$OUT/pg_ghost_s1.jsonl" \
  --rows ghost_s2="$OUT/pg_ghost_s2.jsonl" \
  --manifest ghost_s1="$OUT/pg_ghost_s1.jsonl.manifest.json" \
  --manifest ghost_s2="$OUT/pg_ghost_s2.jsonl.manifest.json" \
  --stats ghost_s1="$OUT/pg_ghost_s1_log/search_stats.jsonl" \
  --stats ghost_s2="$OUT/pg_ghost_s2_log/search_stats.jsonl" \
  > "$OUT/pregate_check.txt" 2>&1 || {
    echo "ABORT: pre-gate NOT IDENTICAL (see $OUT/pregate_check.txt)" >&2
    exit 1; }

# --- registry merge (only for a passed pre-gate) -------------------
cat "$OUT"/pg_*_ids.txt > "$OUT/pg_all_ids.txt"
$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag round9-stage2 --ids "$OUT/pg_all_ids.txt" \
  --vault /home/joe/tcg/registry-vault \
  > "$OUT/registry_merge.txt" 2>&1 || exit 1

# --- manifest -------------------------------------------------------
$PY - "$OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
man = {"stage": "round9-stage2-pregate",
       "check": open(out + "/pregate_check.txt").read(),
       "rows": {os.path.basename(p): rows(p) for p in
                sorted(glob.glob(out + "/pg_*.jsonl"))},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/pg_*.jsonl") +
           glob.glob(out + "/pg_*.jsonl.manifest.json") +
           glob.glob(out + "/pregate_check.txt"))}}
json.dump(man, open(out + "/pregate_manifest.json", "w"), indent=1)
print("pregate manifest written")
PYEOF
echo "STAGE 2 PRE-GATE COMPLETE - $OUT/pregate_manifest.json"
