#!/bin/bash
# Round-7 GRAVY K3 PRE-GATE - implements followup-k1-k3-fix sec.3
# EXACTLY (ghost vs raw, the seat-1 determinism check, the standing
# seat-crossed raw control R16), on the built Gravy tree with the
# pinned launch-copy driver (fleet-alignment registration sec.1).
#
# *** REVIEW-GATED - DO NOT RUN ***
# This runner is submitted as reviewed code for the sec.8 package
# (claude-reply-51f35d9 sec.5/O5). It launches only on Claude's
# approval of the sec.8 package at its sha AND Joe's go in chat.
# It also carries an OPEN dependency: the O1 per-game SHMOP
# containment mechanism does not exist - the rollout children's
# segment keys are NOT recoverable from any record (launch-
# package.md sec.1). The O1 surface this runner carries is the
# standing pre-launch G8 sweep (guarded, below) and ipcs records
# at start and end. Running teacher games before Claude rules on
# the O1 alternatives risks the SHM ceiling (4,096 kernel limit,
# 3,600 operator stop) partway through the pre-gate.
#
# Registered form (followup-k1-k3-fix sec.3): 20 units - seeds
# 8501-8510 x both seats - ghost arm (paired_driver.py --arm ghost;
# TEACHER_MODE=1 + TEACHER_GHOST=1 in the driver) against raw arm
# (--arm raw, the plain bridge) on the tree's per-seat servers.
# Pass = per unit r3_pair.py verdict IDENTICAL with within-row
# hits = 0, outcome equal, modes ok, seat ok, assert ok - read
# through r3_pair.py / classify_divergence.py, never the gamelog
# sha alone. Any non-IDENTICAL unit stops the fleet; the sole
# exception is the K5 pick-null abort-marker class (followup K5),
# disposed of by the K5 reclassification procedure at read time.
# (a) Determinism: a second raw run at seat 1 on the same server
#     must pair IDENTICAL on all 10 units, and is read BEFORE the
#     ghost comparison - a failure stops the pre-gate there.
# (b) Standing raw control (R16): the pre-gate's own raw runs
#     across seats must differ on >= 1 seed of 10.
#
# Pins (fleet-alignment sec.1.4 + follow-up K2): search.php,
# featurize.php and rl/search_server.py (K2), paired_driver.py
# (the Gravy launch copy: TCG_MAX_TURNS=87, parameter 87 /
# trigger 62, decisions 3000) and gate_raw_retry.py (unchanged).
# The guard runs before any server starts or any output is made;
# a wrong tree aborts the launch.
#
# Inputs (environment):
#   GATE_TIMEOUT  REQUIRED - from the contention probe, as
#                 restated by the extended probe if it runs
#                 (fleet-alignment sec.3); no value is inherited.
#   GRAVY_MODEL   REQUIRED - the C4-selected checkpoint, from the
#                 launch manifest; no default.
#   GATE_TREE     default /tmp/gravytree
#   GATE_OUT      default /tmp/ggate (pregate outputs are
#                 pregate_* - no clash with the fleet's gate_c*)
#   PREGATE_SWEEP if =1, run the standing G8 sweep before the
#                 servers start: refuse while any search server /
#                 driver process is alive, save the full listing
#                 to $OUT/pregate_ipcs_presweep.txt, remove only
#                 nattch == 0 segments, one ipcrm -m per segment
#                 from the saved listing.
#
# Outputs in $OUT: pregate_ghost_s{1,2}.jsonl (+ .manifest.json),
# pregate_raw_s{1,2}.jsonl, pregate_raw2_s1.jsonl, per-run logdirs
# (traces + snaps), the three r3_pair read files, server logs,
# ipcs records, the production server hash before/after, and the
# registry merge record. Registry: backup to the vault first,
# then register_gate_ids.py merges every pregate game id and the
# ghost arms' snapshot ids eval-only.
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=${GATE_TREE:-/tmp/gravytree}
MODEL=${GRAVY_MODEL:?GRAVY_MODEL must be set from the launch manifest (C4-selected checkpoint)}
DECK=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
OUT=${GATE_OUT:-/tmp/ggate}
TIMEOUT=${GATE_TIMEOUT:?GATE_TIMEOUT must be set from the Gravy contention probe}
PROD_SERVER=/home/joe/tcg/tcg-sim/rl/search_server.py
REGISTRY=/tmp/harvest/do_not_train_registry.json
VAULT=/home/joe/tcg/registry-vault
SEEDS=8501-8510

expect_hash() {
  # $1 = path, $2 = expected sha256, $3 = label
  local got
  got=$(sha256sum "$1" 2>/dev/null | cut -d' ' -f1)
  [ "$got" = "$2" ] || {
    echo "ABORT: $3 hash mismatch: $1 = ${got:-missing}, want $2" >&2
    exit 1; }
}
expect_hash "$TREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "search.php (abort-patched build, follow-up K2)"
expect_hash "$TREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "featurize.php"
expect_hash "$TREE/rl/search_server.py" \
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c \
  "patched search server"
expect_hash "$TREE/paired_driver.py" \
  0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae \
  "paired_driver.py (Gravy launch copy, fleet-alignment registration: TCG_MAX_TURNS=87, trigger 62)"
expect_hash "$TREE/gate_raw_retry.py" \
  c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93 \
  "gate_raw_retry.py (unchanged stock copy; caps live in the driver)"
expect_hash "$MODEL" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "C4-selected checkpoint (stage-3 report sec.5)"

mkdir -p $OUT
cd $TREE

echo "ipcs before pregate: $(ipcs -m | wc -l)" > $OUT/pregate_ipcs.txt
ipcs -m > $OUT/pregate_ipcs_start.txt

# Standing G8 sweep (optional, guarded): only before any server
# of this run exists, only with nothing else alive, only
# nattch == 0 segments from a saved listing.
if [ "${PREGATE_SWEEP:-0}" = "1" ]; then
  if pgrep -f "search_server.py|paired_driver.py|play_game.php" \
       > /dev/null; then
    echo "ABORT: sweep refused - game processes are running" >&2
    exit 1
  fi
  ipcs -m > $OUT/pregate_ipcs_presweep.txt
  awk '$1 ~ /^0x/ && $6 == 0 {print $2}' \
    $OUT/pregate_ipcs_presweep.txt | while read -r id; do
      ipcrm -m "$id" 2>/dev/null
    done
  ipcs -m > $OUT/pregate_ipcs_postsweep.txt
  echo "ipcs after sweep: $(ipcs -m | wc -l)" >> $OUT/pregate_ipcs.txt
fi

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
  > $OUT/pregate_prod_hash.txt
rm -f /tmp/ggate_s1.sock /tmp/ggate_s2.sock
start_server 1 /tmp/ggate_s1.sock $OUT/pregate_server_s1.log || exit 1
start_server 2 /tmp/ggate_s2.sock $OUT/pregate_server_s2.log || exit 1
grep -h "search model loaded" $OUT/pregate_server_s1.log \
  $OUT/pregate_server_s2.log

IDS=$OUT/pregate_game_ids.txt
run_arm() {
  # $1 = seat, $2 = arm, $3 = out name (no .jsonl)
  GATE_GAME_IDS_FILE=$IDS \
    $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s$1.sock \
      --seat $1 --arm $2 --seeds $SEEDS --timeout $TIMEOUT \
      --deck $DECK \
      --out $OUT/$3.jsonl \
      --logdir $OUT/${3}_log
}
run_arm 1 ghost pregate_ghost_s1
run_arm 2 ghost pregate_ghost_s2
run_arm 1 raw   pregate_raw_s1
run_arm 2 raw   pregate_raw_s2
# (a) determinism: second raw run, seat 1, same server.
GATE_GAME_IDS_FILE=$IDS \
  $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s1.sock \
    --seat 1 --arm raw --seeds $SEEDS --timeout $TIMEOUT \
    --deck $DECK \
    --out $OUT/pregate_raw2_s1.jsonl \
    --logdir $OUT/pregate_raw2_s1_log

# (a) read FIRST: raw seat 1 against its own re-run. Anything
# short of IDENTICAL on all 10 units stops the pre-gate before
# the ghost comparison is read.
$PY r3_pair.py \
  raw=$OUT/pregate_raw_s1.jsonl,$OUT/pregate_raw_s1_log \
  raw=$OUT/pregate_raw2_s1.jsonl,$OUT/pregate_raw2_s1_log \
  > $OUT/pregate_pair_determinism.txt 2>&1
DET_OK=$(grep -c "IDENTICAL" $OUT/pregate_pair_determinism.txt || true)
if [ "$DET_OK" -lt 10 ]; then
  echo "PREGATE STOP: determinism check not IDENTICAL on 10/10" \
    "units - see $OUT/pregate_pair_determinism.txt" >&2
  exit 1
fi

# (b) standing raw control (R16): the pre-gate's own raw runs,
# across seats - must differ on >= 1 seed.
$PY r3_pair.py --raw-control \
  $OUT/pregate_raw_s1.jsonl $OUT/pregate_raw_s2.jsonl \
  > $OUT/pregate_raw_control.txt 2>&1
grep -q "RAW-CONTROL: PASS" $OUT/pregate_raw_control.txt || {
  echo "PREGATE STOP: raw control FAIL - see" \
    "$OUT/pregate_raw_control.txt" >&2
  exit 1; }

# Ghost vs raw, per seat, through the standard instruments. The
# read itself is evaluated in the launch package (the K5 marker
# exception is a read-time disposition, not a runner decision);
# the tables are the runner's output.
for seat in 1 2; do
  $PY r3_pair.py \
    ghost=$OUT/pregate_ghost_s${seat}.jsonl,$OUT/pregate_ghost_s${seat}_log \
    raw=$OUT/pregate_raw_s${seat}.jsonl,$OUT/pregate_raw_s${seat}_log \
    > $OUT/pregate_pair_ghost_s${seat}.txt 2>&1
done

# Server evidence: the selected checkpoint loaded on both
# servers, and no nonzero fallback count anywhere.
grep -h "search model loaded" $OUT/pregate_server_s1.log \
  $OUT/pregate_server_s2.log > $OUT/pregate_server_loads.txt
if grep -hE "fallbacks=[1-9]" $OUT/pregate_server_s1.log \
     $OUT/pregate_server_s2.log > /dev/null; then
  echo "PREGATE STOP: nonzero fallbacks in a server log" >&2
  exit 1
fi

for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null
SRV_PIDS=""

echo "production server after: $(sha256sum $PROD_SERVER)" \
  >> $OUT/pregate_prod_hash.txt
ipcs -m > $OUT/pregate_ipcs_end.txt
echo "ipcs after pregate: $(ipcs -m | wc -l)" >> $OUT/pregate_ipcs.txt

# Registry: backup first, then every pregate game id and the
# ghost arms' snapshot ids go in eval-only (existing entries are
# never modified by the tool; collisions are reported by it).
# Ids files carry no c<digit> token, so the tool's chunk fallback
# applies: games land under gate:gate, snapshots gate_snap:gate.
TS=$(date +%Y%m%d-%H%M%S)
cp $REGISTRY $VAULT/do_not_train_registry.bak-${TS}-pregate.json
$PY register_gate_ids.py --registry $REGISTRY \
  --ids $IDS \
  --snap-index $OUT/pregate_ghost_s1_log/snaps/teacher_snap_index.jsonl \
               $OUT/pregate_ghost_s2_log/snaps/teacher_snap_index.jsonl \
  > $OUT/pregate_registry_merge.txt 2>&1
cp $REGISTRY $VAULT/do_not_train_registry-${TS}-pregate.json
echo "registry after pregate: $(sha256sum $REGISTRY)" \
  >> $OUT/pregate_registry_merge.txt

echo GRAVY-PREGATE-DONE
