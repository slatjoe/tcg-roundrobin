#!/bin/bash
# Round-3 GATE fleet (Claude G1/G6/G8 registration, timeout ruling).
#
# Design: teacher (TEACHER_MODE=1, plain - the measured artifact:
# k=25, top-3 + any prior >= 0.10 cap 4, continuation va, overturn
# at 1.5 paired SE, R17 root state) vs raw v15, PAIRED seeds, both
# against the heuristic, BOTH seats. 200 fresh seeds 1001-1200 x 2
# seats = 400 (seed, seat) units = 800 games.
#
# Layout: FOUR chunks (c1 1001-1050, c2 1051-1100, c3 1101-1150,
# c4 1151-1200). Within each chunk every seed runs at BOTH seats
# and both arms (balanced by construction). Chunk workers run in
# PARALLEL; each writes its own row files, manifests, stat files,
# traces, snapshots and game-id file (the G9 registry source).
#
# Servers: ONE patched server per seat for the whole fleet (R12
# pattern - distinct sockets, seat env), started by this script,
# readiness from the servers' own "listening on" lines, REAPED on
# exit (trap). The driver pings each server and stamps its
# self-reported seat on every row (seat_ok).
#
# Fleet timeout 700s per game (timeout ruling 4: 3x the p99 of the
# rerun's 38 ghost game times - p99 233.1s nearest-rank -> 699.3s,
# registered as 700s; see the gate package). The pre-launch
# concurrency probe (4 teacher games at once, seeds 3003-3006)
# measured a slowest game of 295.3s under fleet-like contention, so
# the launch runs with GATE_TIMEOUT=886 (3x 295.3, probe-set; see
# builder-response-8d13b0f.md). Raw-arm wall timeouts
# get ONE re-run via gate_raw_retry.py (ruling 3); teacher
# timeouts stand and are scored by the analysis (ruling 2).
#
# Teacher arms run with:
#   TEACHER_SNAP_DIR=<chunk-seat snaps>   (G4 overturn snapshots)
#   TCG_CLEAN_CHILDREN=1                 (G8 per-game child cleanup)
#   GATE_GAME_IDS_FILE=<chunk ids file>  (G9 registry source)
# Both arms run with traces ON (G3).
#
# Shared memory (G8): ipcs -m | wc -l is recorded before/after EACH
# chunk into gate_ipcs.txt, and the production server's sha256 is
# recorded before the fleet and after it into gate_prod_hash.txt
# (launch conditions 1-2 carried over: the tree's built hashes are
# the gate package's; the wrapper that launches this script checks
# them - see the package's launch conditions).
#
# Outputs under $GATE_OUT (default /tmp/gate_r4):
#   gate_<chunk>_teacher_s<seat>.jsonl (+ .manifest.json)
#   gate_<chunk>_raw_s<seat>.jsonl     (+ .manifest.json)
#   gate_<chunk>_<arm>_s<seat>_log/    (search_stats, trace/)
#   gate_<chunk>_teacher_s<seat>_snaps/ (overturn snapshots+index)
#   gate_<chunk>_game_ids.txt
#   gate_ipcs.txt, gate_prod_hash.txt, gate_server_s{1,2}.log
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=${GATE_TREE:-/tmp/gatetree_r4}
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
OUT=${GATE_OUT:-/tmp/gate_r4}
TIMEOUT=${GATE_TIMEOUT:-700}
PROD_SERVER=/home/joe/tcg/tcg-sim/rl/search_server.py
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
rm -f /tmp/gate_s1.sock /tmp/gate_s2.sock
start_server 1 /tmp/gate_s1.sock $OUT/gate_server_s1.log || exit 1
start_server 2 /tmp/gate_s2.sock $OUT/gate_server_s2.log || exit 1
grep -h "search model loaded" $OUT/gate_server_s1.log $OUT/gate_server_s2.log

chunk_worker() {
  local chunk=$1 seeds=$2
  echo "before chunk $chunk: $(ipcs -m | wc -l)" \
    > $OUT/gate_ipcs_${chunk}.txt
  for seat in 1 2; do
    TEACHER_SNAP_DIR=$OUT/gate_${chunk}_teacher_s${seat}_snaps \
    TCG_CLEAN_CHILDREN=1 \
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/gate_s${seat}.sock \
        --seat $seat --arm teacher --seeds $seeds --timeout $TIMEOUT \
        --out $OUT/gate_${chunk}_teacher_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_teacher_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/gate_s${seat}.sock \
        --seat $seat --arm raw --seeds $seeds --timeout $TIMEOUT \
        --out $OUT/gate_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_raw_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/gate_${chunk}_game_ids.txt \
      $PY gate_raw_retry.py --tree $TREE --sock /tmp/gate_s${seat}.sock \
        --seat $seat --timeout $TIMEOUT \
        --rows $OUT/gate_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/gate_${chunk}_raw_s${seat}_log
  done
  echo "after chunk $chunk: $(ipcs -m | wc -l)" \
    >> $OUT/gate_ipcs_${chunk}.txt
}

CHUNK_PIDS=""
chunk_worker c1 1001-1050 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c2 1051-1100 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c3 1101-1150 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c4 1151-1200 & CHUNK_PIDS="$CHUNK_PIDS $!"
# Wait on the chunk workers ONLY. A bare `wait` here would also wait
# on the two server processes (background children of this shell that
# never exit on their own), hanging the script forever after the
# chunks finish - found by the pre-launch concurrency probe.
wait $CHUNK_PIDS

# Reap the per-seat servers explicitly now that the chunks are done,
# before the closing bookkeeping (the EXIT trap stays as a backstop).
for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null

cat $OUT/gate_ipcs_c1.txt $OUT/gate_ipcs_c2.txt \
    $OUT/gate_ipcs_c3.txt $OUT/gate_ipcs_c4.txt > $OUT/gate_ipcs.txt
echo "production server after: $(sha256sum $PROD_SERVER)" \
  >> $OUT/gate_prod_hash.txt
echo "ipcs after fleet: $(ipcs -m | wc -l)" >> $OUT/gate_ipcs.txt
echo GATE-FLEET-DONE
