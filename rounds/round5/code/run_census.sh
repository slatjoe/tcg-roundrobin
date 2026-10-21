#!/bin/bash
# run_census.sh - round-5 (b) census runner.
#
# REVIEW-GATED: do not run until the round-5 census package is
# approved at its committed sha AND Joe gives the go in chat.
# Building the census tree (package sec.8) is:
#   cp -r /tmp/otree /tmp/censustree
#   python3 patch_census_probe.py /tmp/censustree
#   (verify featurize.php == b2fa1ffe..., search.php == 8f6b35da...)
#
# The census: 40 plain bridge games in the census tree - seeds
# 6001-6020 with learner seat 1, seeds 6021-6040 with learner
# seat 2 - v15 through the bridge against the production server's
# heuristic route for the other seat, mirror Fai 60 deck. Per
# seat: start the PRODUCTION server build (seat-stamped), run
# the tree's paired_driver.py raw arm with CENSUS_LOG set, stop
# the server by its recorded pid. Sanity gates: the server's
# loaded line must appear before games start, and the census log
# must be non-empty after the seat's games, else the run aborts.
set -u
TREE=${CENSUS_TREE:-/tmp/censustree}
DECK=$TREE/decks/nats2026_ashlyn_fai_60.txt
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
PROD=/home/joe/tcg/tcg-sim/rl/search_server.py
PY=/home/joe/tcg/rl-env/bin/python
OUT=${CENSUS_OUT:-/tmp/census}
mkdir -p "$OUT"

# Tree identity guards (package sec.5): the census tree's
# search.php is the O build untouched; featurize.php is the O
# build plus the probe patch and nothing else.
grep -q '^8f6b35da' <(sha256sum "$TREE/search.php") || {
  echo "ABORT: $TREE/search.php is not the O build (8f6b35da...)"; exit 1; }
grep -q '^b2fa1ffe' <(sha256sum "$TREE/featurize.php") || {
  echo "ABORT: $TREE/featurize.php is not the probe build (b2fa1ffe...)"; exit 1; }
sha256sum "$PROD" > "$OUT/prod_server_hash_before.txt"

run_seat () {
  local seat=$1 seeds=$2
  local sock=$OUT/census_s$seat.sock log=$OUT/server_s$seat.log
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
  CENSUS_LOG=$OUT/census_s$seat.jsonl python3 "$TREE/paired_driver.py" \
    --tree "$TREE" --sock "$sock" --seat "$seat" --arm raw \
    --seeds "$seeds" --out "$OUT/rows_s$seat.jsonl" \
    --logdir "$OUT/log_s$seat" --deck "$DECK"
  local rc=$?
  kill "$pid" 2>/dev/null
  [ -s "$OUT/census_s$seat.jsonl" ] || {
    echo "ABORT: census log empty for seat $seat"; return 1; }
  return $rc
}

run_seat 1 "6001-6020" || exit 1
run_seat 2 "6021-6040" || exit 1

sha256sum "$PROD" > "$OUT/prod_server_hash_after.txt"
wc -l "$OUT"/census_s*.jsonl "$OUT"/rows_s*.jsonl
echo "CENSUS RUN COMPLETE - analysis is a separate registered step (package sec.6)"
