#!/bin/bash
# Round-7 GRAVY GATE fleet — run_gate.sh (round-3 Fai gate) with the
# registered substitutions only:
#   * tree     /tmp/gravytree — built from /tmp/otree per follow-up
#              K2 (claude-reply-dd4cb2f sec.3): the ABORT-PATCHED
#              build, search.php 8f6b35da...; the runner pins the
#              tree's hashes itself (see the guard block below)
#   * model    $GRAVY_MODEL — the C4-selected stage-3 checkpoint;
#              REQUIRED from the launch manifest, no default, so the
#              runner can never silently use a stale path
#   * deck     decks/nats2026_eriksen_gravy_60.txt, passed explicitly
#              to paired_driver.py and gate_raw_retry.py (their
#              built-in default is the Fai deck)
#   * seeds    c1 8001-8050, c2 8051-8100, c3 8101-8150, c4 8151-8200
#              (200 paired seeds x both seats x both arms = 800 games)
#   * timeout  $GATE_TIMEOUT — REQUIRED, set from the Gravy contention
#              probe (registered formula: max(700, 3 x slowest of the
#              4 concurrent probe games)); no Fai number is inherited
#   * out      /tmp/ggate (file names inside keep the gate_ form the
#              registry script parses)
#
# REVIEW-GATED: do not run until the round-7 build package AND the
# K1-K5 follow-up are approved at their committed shas AND Joe gives
# the go in chat. This script verifies the tree's built hashes
# against the follow-up's sec.K2 list before anything starts
# (follow-up K2 tree guard, below).
#
# Everything else is the Fai gate's structure verbatim: one patched
# server per seat for the whole fleet (seat env, distinct sockets,
# readiness from the servers' own "listening on" lines, reaped on
# exit); the driver pings each server and stamps its self-reported
# seat on every row; teacher arms run with TEACHER_SNAP_DIR,
# TCG_CLEAN_CHILDREN=1, GATE_GAME_IDS_FILE; both arms with traces ON;
# raw-arm wall timeouts get ONE re-run via gate_raw_retry.py; teacher
# timeouts stand and are scored by the analysis; ipcs recorded
# before/after each chunk and the production server's sha256 before
# and after the fleet.
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=${GATE_TREE:-/tmp/gravytree}
MODEL=${GRAVY_MODEL:?GRAVY_MODEL must be set from the launch manifest (C4-selected checkpoint)}
DECK=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
OUT=${GATE_OUT:-/tmp/ggate}
TIMEOUT=${GATE_TIMEOUT:?GATE_TIMEOUT must be set from the Gravy contention probe}
PROD_SERVER=/home/joe/tcg/tcg-sim/rl/search_server.py

# Follow-up K2 tree guard: the Gravy tree is the abort-patched
# build (copied from /tmp/otree). Pin its three hashes here so a
# stale or wrong tree aborts the launch before any server starts
# or any output is created.
expect_hash() {
  # $1 = path, $2 = expected sha256, $3 = label
  local got
  got=$(sha256sum "$1" 2>/dev/null | cut -d' ' -f1)
  [ "$got" = "$2" ] || {
    echo "ABORT: $3 hash mismatch: $1 = ${got:-missing}, want $2" >&2
    exit 1; }
}
expect_hash "$TREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "search.php (abort-patched build, follow-up K2)"
expect_hash "$TREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "featurize.php"
expect_hash "$TREE/rl/search_server.py" \
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c \
  "patched search server"

mkdir -p $OUT
cd $TREE

SRV_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
}
trap cleanup EXIT

start_server() {
  # $1 = seat, $2 = sock, $3 = log
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
    $PY rl/search_server.py > $3 2>&1 &
  SRV_PIDS="$SRV_PIDS $!"
  for i in $(seq 1 60); do
    grep -q "listening on $2" $3 2>/dev/null && return 0
    sleep 2
  done
  echo "SERVER FAILED TO START (seat $1): $3" >&2
  return 1
}

echo "production server before: $(sha256sum $PROD_SERVER)" \
  > $OUT/gate_prod_hash.txt
rm -f /tmp/ggate_s1.sock /tmp/ggate_s2.sock
start_server 1 /tmp/ggate_s1.sock $OUT/gate_server_s1.log || exit 1
start_server 2 /tmp/ggate_s2.sock $OUT/gate_server_s2.log || exit 1
grep -h "search model loaded" $OUT/gate_server_s1.log $OUT/gate_server_s2.log

chunk_worker() {
  local chunk=$1 seeds=$2
  echo "before chunk $chunk: $(ipcs -m | wc -l)" \
    > $OUT/gate_ipcs_${chunk}.txt
  for seat in 1 2; do
    TEACHER_SNAP_DIR=$OUT/gate_${chunk}_teacher_s${seat}_snaps \
    TCG_CLEAN_CHILDREN=1 \
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s${seat}.sock \
        --seat $seat --arm teacher --seeds $seeds --timeout $TIMEOUT \
        --deck $DECK \
        --out $OUT/gate_${chunk}_teacher_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_teacher_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s${seat}.sock \
        --seat $seat --arm raw --seeds $seeds --timeout $TIMEOUT \
        --deck $DECK \
        --out $OUT/gate_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_raw_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY gate_raw_retry.py --tree $TREE --sock /tmp/ggate_s${seat}.sock \
        --seat $seat --timeout $TIMEOUT --deck $DECK \
        --rows $OUT/gate_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_raw_s${seat}_log
  done
  echo "after chunk $chunk: $(ipcs -m | wc -l)" \
    >> $OUT/gate_ipcs_${chunk}.txt
}

CHUNK_PIDS=""
chunk_worker c1 8001-8050 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c2 8051-8100 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c3 8101-8150 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c4 8151-8200 & CHUNK_PIDS="$CHUNK_PIDS $!"
# Wait on the chunk workers ONLY (a bare wait would also wait on the
# two server processes and hang forever — the Fai gate's lesson).
wait $CHUNK_PIDS

for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null

cat $OUT/gate_ipcs_c1.txt $OUT/gate_ipcs_c2.txt \
    $OUT/gate_ipcs_c3.txt $OUT/gate_ipcs_c4.txt > $OUT/gate_ipcs.txt
echo "production server after: $(sha256sum $PROD_SERVER)" \
  >> $OUT/gate_prod_hash.txt
echo "ipcs after fleet: $(ipcs -m | wc -l)" >> $OUT/gate_ipcs.txt
echo GRAVY-GATE-FLEET-DONE
