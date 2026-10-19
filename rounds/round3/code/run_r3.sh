#!/bin/bash
# Round-3 launch script (Claude round-3 reply, R1/R7). This exact file
# is what runs if the package is approved and Joe gives the go.
# Arms: raw + ghost at BOTH seats; shadow + capture at seat 1.
# Seeds 1-18,20 (seed 19 hangs in every arm; reported, not scored -
# its registration is issue #1 ask 4, still open).
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=/tmp/tracetree
SOCK=/tmp/tcg_policy.sock
SEEDS=1-18,20
cd $TREE
for seat in 1 2; do
  for arm in raw ghost; do
    $PY paired_driver.py --tree $TREE --sock $SOCK --seat $seat \
      --arm $arm --seeds $SEEDS \
      --out /tmp/r3_${arm}_s${seat}.jsonl \
      --logdir /tmp/r3_${arm}_s${seat}_log
  done
done
for arm in shadow capture; do
  $PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 \
    --arm $arm --seeds $SEEDS \
    --out /tmp/r3_${arm}_s1.jsonl \
    --logdir /tmp/r3_${arm}_s1_log
done
echo R3-LAUNCH-DONE
