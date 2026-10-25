#!/bin/bash
# Round-8 GATE fleet - the distillation conversion measurement
# (build-package sec.5; design sec.6/7 as ruled in
# claude-reply-926f6c3 sec.5).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's approval of the round-8 build package
# at its committed sha, a passed pre-gate, and Joe's go for the
# gate stage. The gate is round 8's last go-gate.
#
# Shape: paired, two-tree (D1). ONE fleet, two arms, both raw:
#   raw arm       - v15 served by the NATIVE tree
#                   (featurize f81193e0...), v15's native build;
#   distilled arm - the T1 checkpoint served by the CORRECTED
#                   tree (featurize 3dcf32c9...), its native
#                   build.
# Serving runs through each tree's OWN rl/search_server.py (the
# round-7 anchor re-gate precedent: the distilled checkpoint is
# a NEW artifact whose serving is validated by the pre-gate's
# determinism runs, so no production-server substitution).
# Seeds 9001-9200 x2 seats x2 arms = 800 games, Fai mirror deck,
# vs heuristic. Chunks c1 9001-9050, c2 9051-9100, c3 9101-9150,
# c4 9151-9200, run sequentially; per chunk, per seat, both arms'
# servers run side by side (four servers), then both driver runs
# run concurrently (the round-7 pattern).
#
# GATE_TIMEOUT is a REQUIRED input set at launch from the
# pre-gate/pilot tail behavior (the round-7 timeout-lessons
# rule: never inherit a number sized on another population): the
# fleet refuses to start without it.
#
# Containment: pre-launch G8 sweep; per-chunk ipcs records;
# (C) sweepers watch each tree's Games dir.
# Registry: BEFORE analysis, the fleet's game ids merge into the
# do-not-train registry (merge_registry.py, tag
# distill_gate_eval, vault copy), and the merged registry's
# sha256 is printed for the analysis's DISTILL_REGISTRY_SHA256
# assertion - the analysis does not run on an unmerged fleet.
#
# Required env: GATE_TIMEOUT, DISTILL_CKPT (the T1 checkpoint).
# Optional env: DISTILL_OUT (default /tmp/distill_gate).
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
NATIVE=/tmp/distilltree_native
CORR=/tmp/distilltree_corrected
V15=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
OUT=${DISTILL_OUT:-/tmp/distill_gate}
REG=/tmp/harvest/do_not_train_registry.json
VAULT=/home/joe/tcg/registry-vault
DECK_NAME=decks/nats2026_ashlyn_fai_60.txt
mkdir -p "$OUT"
: "${GATE_TIMEOUT:?ABORT: GATE_TIMEOUT must be set at launch from the pre-gate/pilot tail}"
: "${DISTILL_CKPT:?ABORT: DISTILL_CKPT (the T1 checkpoint) must be set}"

expect_hash() {
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
expect_hash "$NATIVE/search.php" \
  6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a "native search.php"
expect_hash "$CORR/search.php" \
  6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a "corrected search.php"
expect_hash "$NATIVE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 "native featurize.php"
expect_hash "$CORR/featurize.php" \
  3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a "corrected featurize.php"
expect_hash "$V15" \
  0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"
echo "distilled ckpt sha256: $(sha256sum "$DISTILL_CKPT" | awk '{print $1}')"

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1

start_server() { # tree sock model seat logfile
  TCG_POLICY_SOCK="$2" TCG_LEARNER_SEAT="$4" SEARCH_MODEL="$3" \
    setsid nohup $PY "$1/rl/search_server.py" > "$5" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
}
wait_server() {
  local i
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$1" 2>/dev/null && return 0
    sleep 1
  done
  echo "ABORT: server $1 did not load" >&2; return 1
}
start_sweeper() { # tag gamesdir
  ipcs -m > "$OUT/ipcs_$1.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$1.txt" > "$OUT/shm_$1.txt"
  rm -f "$OUT/shm_$1.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$1.log" \
    --start-file "$OUT/shm_$1.txt" --games-dir "$2" \
    --interval 60 --stop-file "$OUT/shm_$1.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}

RAW_RETRY_POLICY=$(cat <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
pending = [r["seed"] for r in rows
           if (not r.get("keep_game_dir") and not r.get("gamelog_sha256"))]
old = {r["seed"]: r for r in rows}
out = []
seen = set()
for path in sys.argv[2:]:
    for l in open(path):
        if not l.strip():
            continue
        r = json.loads(l)
        s = r["seed"]
        if s in pending and s not in seen and (
                r.get("keep_game_dir") or r.get("gamelog_sha256")):
            out.append(r); seen.add(s)
ok = len(seen) == len(pending)
with open(sys.argv[1], "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
    for r in out:
        f.write(json.dumps(r) + "\n")
print(f"raw_retry: {len(seen)}/{len(pending)} timeouts recovered")
sys.exit(0 if ok else 1)
EOF
)

run_chunk() {
  local chunk=$1 lo=$2 hi=$3 seat
  ipcs -m > "$OUT/ipcs_${chunk}.txt"
  for seat in 1 2; do
    start_server "$NATIVE" "$OUT/raw_${chunk}_s${seat}.sock" "$V15" \
      "$seat" "$OUT/raw_${chunk}_s${seat}_server.log"
    start_server "$CORR" "$OUT/dist_${chunk}_s${seat}.sock" "$DISTILL_CKPT" \
      "$seat" "$OUT/dist_${chunk}_s${seat}_server.log"
    wait_server "$OUT/raw_${chunk}_s${seat}_server.log" || return 1
    wait_server "$OUT/dist_${chunk}_s${seat}_server.log" || return 1
  done
  (
    GATE_GAME_IDS_FILE="$OUT/raw_${chunk}_s1_game_ids.txt" \
      $PY "$NATIVE/paired_driver.py" --tree "$NATIVE" \
        --sock "$OUT/raw_${chunk}_s1.sock" --seat 1 --arm raw \
        --seeds "$lo-$hi" --timeout "$GATE_TIMEOUT" \
        --deck "$NATIVE/$DECK_NAME" \
        --out "$OUT/raw_${chunk}_s1.jsonl" \
        --logdir "$OUT/raw_${chunk}_s1_log"
  ) & local p_raw1=$!
  (
    GATE_GAME_IDS_FILE="$OUT/raw_${chunk}_s2_game_ids.txt" \
      $PY "$NATIVE/paired_driver.py" --tree "$NATIVE" \
        --sock "$OUT/raw_${chunk}_s2.sock" --seat 2 --arm raw \
        --seeds "$lo-$hi" --timeout "$GATE_TIMEOUT" \
        --deck "$NATIVE/$DECK_NAME" \
        --out "$OUT/raw_${chunk}_s2.jsonl" \
        --logdir "$OUT/raw_${chunk}_s2_log"
  ) & local p_raw2=$!
  (
    GATE_GAME_IDS_FILE="$OUT/dist_${chunk}_s1_game_ids.txt" \
      $PY "$CORR/paired_driver.py" --tree "$CORR" \
        --sock "$OUT/dist_${chunk}_s1.sock" --seat 1 --arm raw \
        --seeds "$lo-$hi" --timeout "$GATE_TIMEOUT" \
        --deck "$CORR/$DECK_NAME" \
        --out "$OUT/dist_${chunk}_s1.jsonl" \
        --logdir "$OUT/dist_${chunk}_s1_log"
  ) & local p_dist1=$!
  (
    GATE_GAME_IDS_FILE="$OUT/dist_${chunk}_s2_game_ids.txt" \
      $PY "$CORR/paired_driver.py" --tree "$CORR" \
        --sock "$OUT/dist_${chunk}_s2.sock" --seat 2 --arm raw \
        --seeds "$lo-$hi" --timeout "$GATE_TIMEOUT" \
        --deck "$CORR/$DECK_NAME" \
        --out "$OUT/dist_${chunk}_s2.jsonl" \
        --logdir "$OUT/dist_${chunk}_s2_log"
  ) & local p_dist2=$!
  local rc=0
  wait $p_raw1 || rc=1
  wait $p_raw2 || rc=1
  wait $p_dist1 || rc=1
  wait $p_dist2 || rc=1
  [ "$rc" = 0 ] || return 1
  # Timeout recovery (the round-7 gate_raw_retry pattern): a raw
  # timeout leaves no record but the bare result row; re-run
  # those seeds once (the retry replays the identical game) and
  # splice the full record in.
  local arm tree tag
  for arm in raw dist; do
    for seat in 1 2; do
      if [ "$arm" = raw ]; then tree=$NATIVE; else tree=$CORR; fi
      tag=${arm}_${chunk}_s${seat}
      GATE_GAME_IDS_FILE="$OUT/${tag}_retry_game_ids.txt" \
      KEEP_GAME_ON_TIMEOUT=1 \
        $PY "$tree/paired_driver.py" --tree "$tree" \
          --sock "$OUT/${tag}.sock" --seat "$seat" --arm raw \
          --arm2 retry --timeout "$GATE_TIMEOUT" \
          --deck "$tree/$DECK_NAME" \
          --out "$OUT/${tag}_retry.jsonl" \
          --logdir "$OUT/${tag}_retry_log" \
          --base-rows "$OUT/${tag}.jsonl" || return 1
      $PY -c "$RAW_RETRY_POLICY" "$OUT/${tag}.jsonl" \
        "$OUT/${tag}_retry.jsonl" || return 1
    done
  done
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  SRV_PIDS=""
}

start_sweeper native "$NATIVE/vendor/talishar/Games"
start_sweeper corr "$CORR/vendor/talishar/Games"
run_chunk c1 9001 9050 || exit 1
run_chunk c2 9051 9100 || exit 1
run_chunk c3 9101 9150 || exit 1
run_chunk c4 9151 9200 || exit 1
touch "$OUT/shm_native.stop" "$OUT/shm_corr.stop"

$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag distill_gate_eval --vault "$VAULT" \
  --ids "$OUT/raw_c1_s1_game_ids.txt" --ids "$OUT/raw_c1_s2_game_ids.txt" \
  --ids "$OUT/raw_c2_s1_game_ids.txt" --ids "$OUT/raw_c2_s2_game_ids.txt" \
  --ids "$OUT/raw_c3_s1_game_ids.txt" --ids "$OUT/raw_c3_s2_game_ids.txt" \
  --ids "$OUT/raw_c4_s1_game_ids.txt" --ids "$OUT/raw_c4_s2_game_ids.txt" \
  --ids "$OUT/dist_c1_s1_game_ids.txt" --ids "$OUT/dist_c1_s2_game_ids.txt" \
  --ids "$OUT/dist_c2_s1_game_ids.txt" --ids "$OUT/dist_c2_s2_game_ids.txt" \
  --ids "$OUT/dist_c3_s1_game_ids.txt" --ids "$OUT/dist_c3_s2_game_ids.txt" \
  --ids "$OUT/dist_c4_s1_game_ids.txt" --ids "$OUT/dist_c4_s2_game_ids.txt" \
  > "$OUT/registry_merge.txt" || exit 1
cat "$OUT/registry_merge.txt"
echo "FLEET COMPLETE - analysis runs next with"
echo "  DISTILL_REGISTRY_SHA256=<the sha printed above>"
echo "  $PY analyze_distill_gate.py --fleet $OUT --arm-names raw dist"
