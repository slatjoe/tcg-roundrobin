#!/bin/bash
# gravy_ppo_launch.sh — round-7 STAGE 3: gated PPO to the raw policy.
#
# REVIEW-GATED: do not run until the round-7 build package is approved
# at its committed sha AND Joe gives the go in chat. Additionally this
# script refuses to start unless GRAVY_STAGE2_CLEARED=1 — the operator
# sets it only after the stage-2 anchor gate read clears Claude's
# added stop (anchor read >= 0.40; below that the pipeline returns
# with a package instead of training).
#
# Configuration: configs/ppo_config_diff.txt is the full record. In
# short: the 3b launch with the out-dir, the anchor, the mirror deck
# and the Flag-2 suite line changed, and NOTHING else. The trainer is
# the launch copy produced by patch_trainer_launch.py (sha256
# dc95d81a...), installed at $SIM/rl/trainer_v4_gravy.py so SIM_ROOT
# resolves to the sim root.
set -u
SIM=/home/joe/tcg/tcg-sim
PY=/home/joe/tcg/rl-env/bin/python
G60=$SIM/decks/nats2026_eriksen_gravy_60.txt
OUT=$SIM/rl_out/gravy_ppo_gravybc3
ANCHOR=$SIM/gravy_bc/bc3_out/bc3_policy.pt
TRAINER=$SIM/rl/trainer_v4_gravy.py

[ "${GRAVY_STAGE2_CLEARED:-0}" = "1" ] || {
  echo "ABORT: stage-2 anchor stop not cleared (GRAVY_STAGE2_CLEARED!=1)" >&2
  exit 1; }
[ -f "$ANCHOR" ] || { echo "ABORT: anchor missing: $ANCHOR" >&2; exit 1; }
grep -q '^dc95d81a' <(sha256sum "$TRAINER") || {
  echo "ABORT: $TRAINER is not the reviewed launch copy (dc95d81a...)" >&2
  exit 1; }

mkdir -p "$OUT"
rm -f /tmp/stop_rl
export SIM
BC_MODEL=$ANCHOR TCG_MATCHUPS=gravy:gravy:1.0 \
  bash "$SIM/rl/run_workers.sh" 4 "$G60" "$G60" "$OUT" \
  > "$OUT/workers_launch.log" 2>&1 &
WORKERS_PID=$!

# The trainer tails the workers' traj files; give the workers time to
# pass their built-in smoke test and open their servers first.
for i in $(seq 1 60); do
  grep -q 'rollout running' "$OUT/workers_launch.log" 2>/dev/null && break
  sleep 2
done
grep -q 'rollout running' "$OUT/workers_launch.log" || {
  echo "ABORT: rollout workers did not start (see $OUT/workers_launch.log)" >&2
  touch /tmp/stop_rl; exit 1; }

"$PY" "$TRAINER" --out-dir "$OUT" --bc3 "$ANCHOR" --suite none
TRAINER_RC=$?

touch /tmp/stop_rl
wait $WORKERS_PID 2>/dev/null
echo "trainer exit: $TRAINER_RC"
echo "final status: $(cat "$OUT/status.json" 2>/dev/null)"
