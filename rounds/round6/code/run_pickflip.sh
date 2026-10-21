#!/bin/bash
# run_pickflip.sh - round-6 pick-flip runner.
#
# REVIEW-GATED: do not run until the round-6 pick-flip package is
# approved at its committed sha AND Joe gives the go in chat.
# Building the flip tree (package sec.8):
#   cp -r /tmp/otree /tmp/fliptree
#   python3 patch_pickflip_probe.py /tmp/fliptree
#   (verify policy_server.php == c00befa9..., featurize.php ==
#    f81193e0... unchanged, search.php == 8f6b35da...)
#
# The measurement (claude-reply-f7e4534 sec.3): the census's own
# 40 plain bridge games - seeds 6001-6020 with learner seat 1,
# seeds 6021-6040 with learner seat 2 - v15 through the bridge
# against the production server, mirror Fai 60 deck, with
# FLIP_LOG set so every ARS featurization is dual-evaluated
# (current state vs view-consistent variant) and logged. Play
# continues on the current state's pick; the run must replay the
# census games identically (reconciliation: package sec.5).
# Per seat: start the PRODUCTION server build (seat-stamped),
# run the tree's paired_driver.py raw arm, stop the server by
# its recorded pid. Sanity gates: the server's loaded line must
# appear before games start (its startup line, learner seat
# included, is quoted in the results - the hand seat check), and
# the flip log must be non-empty after the seat's games, else
# the run aborts. Segment counts are recorded in-script.
set -u
TREE=${PICKFLIP_TREE:-/tmp/fliptree}
DECK=$TREE/decks/nats2026_ashlyn_fai_60.txt
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
PROD=/home/joe/tcg/tcg-sim/rl/search_server.py
PY=/home/joe/tcg/rl-env/bin/python
OUT=${PICKFLIP_OUT:-/tmp/pickflip}
mkdir -p "$OUT"

# Tree identity guards (package sec.5): the flip tree's
# search.php and featurize.php are the O builds untouched;
# policy_server.php is the O build plus the pick-flip probe
# patch and nothing else.
grep -q '^8f6b35da' <(sha256sum "$TREE/search.php") || {
  echo "ABORT: $TREE/search.php is not the O build (8f6b35da...)"; exit 1; }
grep -q '^f81193e0' <(sha256sum "$TREE/featurize.php") || {
  echo "ABORT: $TREE/featurize.php is not the O build (f81193e0...)"; exit 1; }
grep -q '^c00befa9' <(sha256sum "$TREE/policy_server.php") || {
  echo "ABORT: $TREE/policy_server.php is not the probe build (c00befa9...)"; exit 1; }
sha256sum "$PROD" > "$OUT/prod_server_hash_before.txt"
ipcs -m | wc -l > "$OUT/segments_start.txt"

run_seat () {
  local seat=$1 seeds=$2
  local sock=$OUT/flip_s$seat.sock log=$OUT/server_s$seat.log
  TCG_POLICY_SOCK=$sock TCG_LEARNER_SEAT=$seat SEARCH_MODEL=$MODEL \
    setsid nohup $PY $PROD > "$log" 2>&1 < /dev/null &
  local pid=$!
  echo "$pid" > "$OUT/server_s$seat.pid"
  local i
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$log" || {
    echo "ABORT: production server for seat $seat did not load"; kill "$pid" 2>/dev/null; return 1; }
  FLIP_LOG=$OUT/flip_s$seat.jsonl python3 "$TREE/paired_driver.py" \
    --tree "$TREE" --sock "$sock" --seat "$seat" --arm raw \
    --seeds "$seeds" --out "$OUT/rows_s$seat.jsonl" \
    --logdir "$OUT/log_s$seat" --deck "$DECK"
  local rc=$?
  kill "$pid" 2>/dev/null
  [ -s "$OUT/flip_s$seat.jsonl" ] || {
    echo "ABORT: flip log empty for seat $seat"; return 1; }
  return $rc
}

run_seat 1 "6001-6020" || exit 1
run_seat 2 "6021-6040" || exit 1

sha256sum "$PROD" > "$OUT/prod_server_hash_after.txt"
ipcs -m | wc -l > "$OUT/segments_end.txt"
wc -l "$OUT"/flip_s*.jsonl "$OUT"/rows_s*.jsonl
echo "PICK-FLIP RUN COMPLETE - tally is a separate registered step (package sec.6)"
