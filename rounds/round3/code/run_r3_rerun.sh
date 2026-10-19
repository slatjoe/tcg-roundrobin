#!/bin/bash
# Round-3 RERUN script (Claude R12-R16). This exact file is what runs
# if the rerun package is approved at its sha and Joe gives the go.
# Same layout as run_r3.sh: raw + ghost at BOTH seats; shadow +
# capture at seat 1; seeds 1-18,20 (seed 19 hangs in every arm;
# reported, not scored - registration still open).
#
# Differences from run_r3.sh, per the rerun fixes:
#  - The script starts BOTH policy servers itself: one per seat, each
#    with TCG_LEARNER_SEAT matching its seat and its own socket, from
#    the tree's patched rl/search_server.py. It waits for each
#    server's own "listening on" line before running arms, and REAPS
#    both servers on exit (trap) - no server outlives the run.
#  - Arms are pointed at their seat's socket, so the driver's ping
#    records server_seat == arm seat on every row.
#  - ipcs -m | wc -l is recorded before and after EACH arm into
#    /tmp/r3x_ipcs.txt (shared-memory growth is a reported read).
#  - Outputs use the r3x_ prefix; the launch's r3_ files are the
#    record of the void run and are not overwritten.
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=/tmp/reruntree
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
SEEDS=1-18,20
IPCS_FILE=/tmp/r3x_ipcs.txt
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

rm -f /tmp/r3_s1.sock /tmp/r3_s2.sock
start_server 1 /tmp/r3_s1.sock /tmp/r3x_server_s1.log || exit 1
start_server 2 /tmp/r3_s2.sock /tmp/r3x_server_s2.log || exit 1
grep -h "search model loaded" /tmp/r3x_server_s1.log /tmp/r3x_server_s2.log

echo "ipcs before run: $(ipcs -m | wc -l)" >> $IPCS_FILE
for seat in 1 2; do
  for arm in raw ghost; do
    echo "before ${arm}_s${seat}: $(ipcs -m | wc -l)" >> $IPCS_FILE
    $PY paired_driver.py --tree $TREE --sock /tmp/r3_s${seat}.sock \
      --seat $seat --arm $arm --seeds $SEEDS \
      --out /tmp/r3x_${arm}_s${seat}.jsonl \
      --logdir /tmp/r3x_${arm}_s${seat}_log
    echo "after ${arm}_s${seat}: $(ipcs -m | wc -l)" >> $IPCS_FILE
  done
done
for arm in shadow capture; do
  echo "before ${arm}_s1: $(ipcs -m | wc -l)" >> $IPCS_FILE
  $PY paired_driver.py --tree $TREE --sock /tmp/r3_s1.sock --seat 1 \
    --arm $arm --seeds $SEEDS \
    --out /tmp/r3x_${arm}_s1.jsonl \
    --logdir /tmp/r3x_${arm}_s1_log
  echo "after ${arm}_s1: $(ipcs -m | wc -l)" >> $IPCS_FILE
done
echo "ipcs after run: $(ipcs -m | wc -l)" >> $IPCS_FILE
echo R3-RERUN-DONE
