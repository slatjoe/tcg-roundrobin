#!/bin/bash
# Round-7 GRAVY K3 PRE-GATE - implements followup-k1-k3-fix sec.3
# EXACTLY (ghost vs raw, the seat-1 determinism check, the standing
# seat-crossed raw control R16), on the built Gravy tree with the
# pinned launch-copy driver (fleet-alignment registration sec.1),
# revised per claude-reply-ad1d7c6 sec.5 (this file supersedes the
# sec.8 draft, sha256 19cb3c13...; the four sec.5 changes are
# marked [sec.5.1]..[sec.5.4] below).
#
# *** REVIEW-GATED - DO NOT RUN ***
# This runner is submitted as reviewed code for the containment
# package. It launches only on Claude's approval of that package
# at its sha AND Joe's go in chat.
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
# [sec.5.1] The determinism read is PARSED, never grepped:
# parse_r3_pair.py checks the table's every column (exactly 10
# data rows; verdict IDENTICAL, within-row hits 0, outcome equal
# True, modes/seat/assert True). Any deviation stops the pre-gate.
# The same parser is run over the ghost tables and its output
# recorded; the ghost read's disposition (including the K5 class)
# belongs to the launch record, which uses this same parser.
#
# Containment [sec.5.2 + reply sec.2(C)]: the ghost arms are 20
# teacher-machinery games (~3,560 segments at the original
# probe's leak rate - the whole headroom), and the arms run one
# after another, so both registered mechanisms run:
#   * the (C) production sweeper (shm_sweep.py, pinned below)
#     runs LIVE for the run's whole duration, one pass per 60 s,
#     from the post-sweep run-start listing; and
#   * the standing G8 sweep (gate_ipcs_cleanup.sh) runs at the
#     start (PREGATE_SWEEP=1, REQUIRED - the run aborts without
#     it) and again after ghost_s1 and after ghost_s2; between
#     arms no driver is running, and the G8 guard (play_game /
#     paired_driver) lets the servers stay up.
# Before every arm the run aborts if the segment count is above
# 2,800. All listings are kept in $OUT.
#
# [sec.5.3] The ghost arms' driver environment carries
# TCG_CLEAN_CHILDREN=1, as the fleet's teacher arms do (the
# driver cleans the children that do not wipe themselves - the
# timeout-killed and Throwable classes - after each completed
# teacher-family game). The K3 invocation text omitted it; the
# reply registers it. Raw arms are unchanged.
#
# [sec.5.4] The registry step registers GAME IDS ONLY. The driver
# sets TEACHER_SNAP_DIR only for the capture arm
# (paired_driver.py:248-250) and this runner does not set it, so
# neither the ghost arms nor the raw arms produce a snapshot
# index: there are no ghost snapshots to quarantine. Every
# driver call's exit code is checked; a non-zero exit stops the
# pre-gate.
#
# Pins (fleet-alignment sec.1.4 + follow-up K2 + the containment
# package): search.php, featurize.php and rl/search_server.py
# (K2), paired_driver.py (the Gravy launch copy: TCG_MAX_TURNS=87,
# parameter 87 / trigger 62, decisions 3000), gate_raw_retry.py
# (unchanged), the C4-selected checkpoint itself, and the three
# runner-side tools deployed at the tree root by the launch
# manifest (gate_ipcs_cleanup.sh, shm_sweep.py, parse_r3_pair.py).
# The guard runs before any server starts or any output is made;
# a wrong tree aborts the launch.
#
# Inputs (environment):
#   GATE_TIMEOUT  REQUIRED - the extended probe's restated value
#                 is 3,870 s (extended-probe.md sec.6); supplied
#                 by the launch manifest; no value is inherited.
#   GRAVY_MODEL   REQUIRED - the C4-selected checkpoint, from the
#                 launch manifest; no default.
#   PREGATE_SWEEP REQUIRED =1 - the start-of-run G8 sweep is
#                 containment, not an option (sec.5.2).
#   GATE_TREE     default /tmp/gravytree
#   GATE_OUT      default /tmp/ggate (pregate outputs are
#                 pregate_* - no clash with the fleet's gate_c*)
#
# Outputs in $OUT: pregate_ghost_s{1,2}.jsonl (+ .manifest.json),
# pregate_raw_s{1,2}.jsonl, pregate_raw2_s1.jsonl, per-run logdirs
# (traces), the three r3_pair read files plus their parse records,
# server logs, the G8 sweep evidence files, the (C) sweeper's log,
# ipcs records, the production server hash before/after, and the
# registry merge record. Registry: backup to the vault first,
# then register_gate_ids.py merges every pregate game id
# eval-only.
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=${GATE_TREE:-/tmp/gravytree}
MODEL=${GRAVY_MODEL:?GRAVY_MODEL must be set from the launch manifest (C4-selected checkpoint)}
DECK=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
OUT=${GATE_OUT:-/tmp/ggate}
TIMEOUT=${GATE_TIMEOUT:?GATE_TIMEOUT must be set from the launch manifest (extended probe: 3870)}
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
expect_hash "$TREE/gate_ipcs_cleanup.sh" \
  338183e255acfa1b8ec23fd73511e55e291b8af64686ddaf84e7ba1779e3162e \
  "gate_ipcs_cleanup.sh (standing G8 sweep, round-3 committed copy)"
expect_hash "$TREE/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) production sweeper, containment package)"
expect_hash "$TREE/parse_r3_pair.py" \
  ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1 \
  "parse_r3_pair.py (determinism/ghost table parser, containment package)"

mkdir -p $OUT
cd $TREE

echo "ipcs before pregate: $(ipcs -m | wc -l)" > $OUT/pregate_ipcs.txt
ipcs -m > $OUT/pregate_ipcs_start.txt

# [sec.5.2] The start-of-run G8 sweep is REQUIRED. The standing
# script refuses while play_game / paired_driver processes are
# alive and removes only nattch == 0 segments, from a saved
# listing; its evidence files land beside the prefix.
if [ "${PREGATE_SWEEP:-}" != "1" ]; then
  echo "ABORT: PREGATE_SWEEP=1 is required (start-of-run" \
    "containment is not optional, claude-reply-ad1d7c6 sec.5.2)" >&2
  exit 1
fi
bash gate_ipcs_cleanup.sh $OUT/pregate_ipcs_startsweep || {
  echo "PREGATE STOP: the start-of-run G8 sweep failed" >&2
  exit 1; }
echo "ipcs after start sweep: $(ipcs -m | wc -l)" \
  >> $OUT/pregate_ipcs.txt

# (C) live containment for the run's duration: the run-start
# listing is taken AFTER the start sweep, so rule (4) excludes
# exactly what the run did not create. The sweeper is stopped
# after the last read, before the closing listings.
ipcs -m > $OUT/pregate_ipcs_runstart.txt
awk '$1 ~ /^0x/ {print $2}' $OUT/pregate_ipcs_runstart.txt \
  > $OUT/pregate_shm_start.txt
rm -f $OUT/pregate_shm_sweep.stop
$PY shm_sweep.py --log $OUT/pregate_shm_sweep.log \
  --start-file $OUT/pregate_shm_start.txt \
  --games-dir $TREE/vendor/talishar/Games \
  --interval 60 --stop-file $OUT/pregate_shm_sweep.stop &
SWEEP_PID=$!

SRV_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
  kill $SWEEP_PID 2>/dev/null
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

check_headroom() {
  # $1 = the arm about to run. [sec.5.2]: abort above 2,800.
  local n
  n=$(ipcs -m | awk '$1 ~ /^0x/ {n++} END {print n+0}')
  echo "ipcs before $1: $n" >> $OUT/pregate_ipcs.txt
  if [ "$n" -gt 2800 ]; then
    echo "PREGATE STOP: ipcs count $n above 2,800 before $1" >&2
    exit 1
  fi
}

IDS=$OUT/pregate_game_ids.txt
run_arm() {
  # $1 = seat, $2 = arm, $3 = out name (no .jsonl)
  # [sec.5.4]: every driver call's exit code is checked.
  local rc
  check_headroom "$3"
  if [ "$2" = "ghost" ]; then
    # [sec.5.3]: TCG_CLEAN_CHILDREN=1 on the ghost arms only.
    TCG_CLEAN_CHILDREN=1 GATE_GAME_IDS_FILE=$IDS \
      $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s$1.sock \
        --seat $1 --arm $2 --seeds $SEEDS --timeout $TIMEOUT \
        --deck $DECK \
        --out $OUT/$3.jsonl \
        --logdir $OUT/${3}_log
  else
    GATE_GAME_IDS_FILE=$IDS \
      $PY paired_driver.py --tree $TREE --sock /tmp/ggate_s$1.sock \
        --seat $1 --arm $2 --seeds $SEEDS --timeout $TIMEOUT \
        --deck $DECK \
        --out $OUT/$3.jsonl \
        --logdir $OUT/${3}_log
  fi
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "PREGATE STOP: driver ($2 seat $1) exited $rc" >&2
    exit 1
  fi
}
run_arm 1 ghost pregate_ghost_s1
# [sec.5.2]: the standing G8 sweep after ghost_s1 (servers stay
# up; the G8 guard covers only play_game / paired_driver).
bash gate_ipcs_cleanup.sh $OUT/pregate_ipcs_post_ghost_s1 || {
  echo "PREGATE STOP: G8 sweep failed after ghost_s1" >&2
  exit 1; }
run_arm 2 ghost pregate_ghost_s2
bash gate_ipcs_cleanup.sh $OUT/pregate_ipcs_post_ghost_s2 || {
  echo "PREGATE STOP: G8 sweep failed after ghost_s2" >&2
  exit 1; }
run_arm 1 raw   pregate_raw_s1
run_arm 2 raw   pregate_raw_s2
# (a) determinism: second raw run, seat 1, same server.
run_arm 1 raw   pregate_raw2_s1

# (a) read FIRST, [sec.5.1] parsed: raw seat 1 against its own
# re-run. Anything short of a full strict pass stops the
# pre-gate before the ghost comparison is read.
$PY r3_pair.py \
  raw=$OUT/pregate_raw_s1.jsonl,$OUT/pregate_raw_s1_log \
  raw=$OUT/pregate_raw2_s1.jsonl,$OUT/pregate_raw2_s1_log \
  > $OUT/pregate_pair_determinism.txt 2>&1
if ! $PY parse_r3_pair.py --expect-rows 10 \
     $OUT/pregate_pair_determinism.txt \
     > $OUT/pregate_pair_determinism.parse.txt 2>&1; then
  echo "PREGATE STOP: determinism read failed the strict parse" \
    "- see $OUT/pregate_pair_determinism.parse.txt" >&2
  exit 1
fi

# (b) standing raw control (R16): the pre-gate's own raw runs,
# across seats - must differ on >= 1 seed. The control's own
# verdict string is the tool's output (RAW-CONTROL: PASS).
$PY r3_pair.py --raw-control \
  $OUT/pregate_raw_s1.jsonl $OUT/pregate_raw_s2.jsonl \
  > $OUT/pregate_raw_control.txt 2>&1
grep -q "RAW-CONTROL: PASS" $OUT/pregate_raw_control.txt || {
  echo "PREGATE STOP: raw control FAIL - see" \
    "$OUT/pregate_raw_control.txt" >&2
  exit 1; }

# Ghost vs raw, per seat, through the standard instruments. The
# runner writes the tables and runs the same strict parser over
# them in record-only mode; the read's disposition (including
# the K5 marker exception) is made in the launch record with
# this parser - the runner itself does not stop on it.
for seat in 1 2; do
  $PY r3_pair.py \
    ghost=$OUT/pregate_ghost_s${seat}.jsonl,$OUT/pregate_ghost_s${seat}_log \
    raw=$OUT/pregate_raw_s${seat}.jsonl,$OUT/pregate_raw_s${seat}_log \
    > $OUT/pregate_pair_ghost_s${seat}.txt 2>&1
  $PY parse_r3_pair.py --expect-rows 10 \
    $OUT/pregate_pair_ghost_s${seat}.txt \
    > $OUT/pregate_pair_ghost_s${seat}.parse.txt 2>&1 || true
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

# Stop the (C) sweeper (it exits after its current pass), then
# the servers; the closing listings are post-containment.
touch $OUT/pregate_shm_sweep.stop
wait $SWEEP_PID 2>/dev/null

for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null
SRV_PIDS=""

echo "production server after: $(sha256sum $PROD_SERVER)" \
  >> $OUT/pregate_prod_hash.txt
ipcs -m > $OUT/pregate_ipcs_end.txt
echo "ipcs after pregate: $(ipcs -m | wc -l)" >> $OUT/pregate_ipcs.txt

# Registry: backup first, then every pregate game id goes in
# eval-only (existing entries are never modified by the tool;
# collisions are reported by it). [sec.5.4]: game ids only -
# neither arm produces a snapshot index under this runner (see
# the header). Ids files carry no c<digit> token, so the tool's
# chunk fallback applies: games land under gate:gate.
TS=$(date +%Y%m%d-%H%M%S)
cp $REGISTRY $VAULT/do_not_train_registry.bak-${TS}-pregate.json
$PY register_gate_ids.py --registry $REGISTRY \
  --ids $IDS \
  > $OUT/pregate_registry_merge.txt 2>&1
cp $REGISTRY $VAULT/do_not_train_registry-${TS}-pregate.json
echo "registry after pregate: $(sha256sum $REGISTRY)" \
  >> $OUT/pregate_registry_merge.txt

echo GRAVY-PREGATE-DONE
