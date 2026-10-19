#!/bin/bash
# G10 smoke runner (disclosed build test for the gate package):
# seed 1001 at seat 1 and seat 2, teacher + raw, on the gate tree
# (/tmp/gatetree_r4), per-seat patched servers, fleet conditions
# (timeout 700, traces on, TEACHER_SNAP_DIR + TCG_CLEAN_CHILDREN=1
# + GATE_GAME_IDS_FILE on teacher arms). NOT the gate fleet.
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=/tmp/gatetree_r4
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
OUT=/tmp/gate_smoke
mkdir -p $OUT
cd $TREE

SRV_PIDS=""
cleanup() { for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done; }
trap cleanup EXIT

start_server() {
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
    $PY rl/search_server.py > $3 2>&1 &
  SRV_PIDS="$SRV_PIDS $!"
  for i in $(seq 1 60); do
    grep -q "listening on $2" $3 2>/dev/null && return 0
    sleep 2
  done
  echo "SERVER FAILED TO START (seat $1)" >&2
  return 1
}

echo "ipcs before smoke: $(ipcs -m | wc -l)" > $OUT/smoke_ipcs.txt
rm -f /tmp/gate_s1.sock /tmp/gate_s2.sock
start_server 1 /tmp/gate_s1.sock $OUT/server_s1.log || exit 1
start_server 2 /tmp/gate_s2.sock $OUT/server_s2.log || exit 1
grep -h "listening on" $OUT/server_s1.log $OUT/server_s2.log

for seat in 1 2; do
  TEACHER_SNAP_DIR=$OUT/c1_teacher_s${seat}_snaps \
  TCG_CLEAN_CHILDREN=1 \
  GATE_GAME_IDS_FILE=$OUT/gate_c1_game_ids.txt \
    $PY paired_driver.py --tree $TREE --sock /tmp/gate_s${seat}.sock \
      --seat $seat --arm teacher --seeds 1001 --timeout 700 \
      --out $OUT/gate_c1_teacher_s${seat}.jsonl \
      --logdir $OUT/gate_c1_teacher_s${seat}_log
  echo "ipcs after teacher s${seat}: $(ipcs -m | wc -l)" >> $OUT/smoke_ipcs.txt
  GATE_GAME_IDS_FILE=$OUT/gate_c1_game_ids.txt \
    $PY paired_driver.py --tree $TREE --sock /tmp/gate_s${seat}.sock \
      --seat $seat --arm raw --seeds 1001 --timeout 700 \
      --out $OUT/gate_c1_raw_s${seat}.jsonl \
      --logdir $OUT/gate_c1_raw_s${seat}_log
  echo "ipcs after raw s${seat}: $(ipcs -m | wc -l)" >> $OUT/smoke_ipcs.txt
done
echo SMOKE-RUN-DONE
