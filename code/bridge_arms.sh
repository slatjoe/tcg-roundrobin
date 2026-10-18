#!/bin/bash
# Corrected ghost test, bridge arms: plain v15 (no search root) on
# the ghost seeds, twice - repeat determinism control + the true
# baseline for the (already completed) ghost arm rows.
# Waits for the search-arm repeat (raw3) to clear the server first.
PY=/home/joe/tcg/rl-env/bin/python
TREE=/tmp/gatetree
SOCK=/tmp/tcg_policy.sock
while pgrep -f "ghost_raw3" > /dev/null; do sleep 20; done
cd $TREE
$PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 --arm raw \
  --seeds 1-18,20 --out /tmp/ghost_bridge.jsonl --logdir /tmp/ghost_bridge_log
$PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 --arm raw \
  --seeds 1-18,20 --out /tmp/ghost_bridge2.jsonl --logdir /tmp/ghost_bridge2_log
echo BRIDGE-ARMS-DONE
