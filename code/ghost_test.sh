#!/bin/bash
# Pre-gate ghost test (Claude round 2): ghost teacher (full machinery,
# pick forced to the prior's) must be ACTION-IDENTICAL to raw v15 on
# the same seeds - verified by gamelog sha per seed. Raw-repeat arm
# controls for engine determinism. Any mismatch stops the line.
# Server must already be up on $SOCK (seat 1) with SEARCH_MODEL set.
PY=/home/joe/tcg/rl-env/bin/python
TREE=/tmp/gatetree
SOCK=/tmp/tcg_policy.sock
cd $TREE
$PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 --arm raw \
  --seeds 1-20 --out /tmp/ghost_raw.jsonl --logdir /tmp/ghost_raw_log
$PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 --arm ghost \
  --seeds 1-20 --out /tmp/ghost_ghost.jsonl --logdir /tmp/ghost_ghost_log
$PY paired_driver.py --tree $TREE --sock $SOCK --seat 1 --arm raw \
  --seeds 1-20 --out /tmp/ghost_raw2.jsonl --logdir /tmp/ghost_raw2_log
echo GHOST-TEST-DONE
