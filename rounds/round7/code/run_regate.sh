#!/bin/bash
# Round-7 stage 2 (part 2): the anchor gate - the two registered
# rl/eval.py invocations of build-package.md sec.4, run sequentially.
set -u
export TCG_MAX_DECISIONS=3000
cd /home/joe/tcg/tcg-sim
PY=/home/joe/tcg/rl-env/bin/python
G60=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
echo "=== anchor gate A (learner deck a) $(date) ==="
$PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
  --games 200 --deck-a $G60 --deck-b $G60 --learner-deck a \
  --workdir gravy_bc/anchor_regate_a --sock /tmp/gravy_regate_a.sock \
  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
echo "gate_a_exit=$?"
echo "=== anchor gate B (learner deck b) $(date) ==="
$PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
  --games 200 --deck-a $G60 --deck-b $G60 --learner-deck b \
  --workdir gravy_bc/anchor_regate_b --sock /tmp/gravy_regate_b.sock \
  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
echo "gate_b_exit=$?"
echo "=== gate runs complete $(date) ==="
