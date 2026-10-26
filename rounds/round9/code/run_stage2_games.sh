#!/bin/bash
# Round-9 Stage 2 GAMES (design sec.5; ruling sec.3.4): 200
# live calibrated-teacher games vs the heuristic, Gravy
# mirror, seeds 22001-22100 x both seats, instrument 87/62.
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage 2
# package at its committed sha, a PASSED ghost pre-gate
# (run_stage2_pregate.sh, IDENTICAL), and Joe's explicit
# go for Stage 2. The pre-gate is enforced mechanically
# below (PREGATE-GATE block, review sec.2.1): no manifest
# recording IDENTICAL under this run's build pin and
# tuple, no run.
#
# The teacher build is code/search_s2.php installed into
# per-block copies of the fleet tree; the run tuple is
# pinned by TEACHER_TUPLE_JSON, built here from
# settings_stage2.json (teacher_tuple: H8k-180+H -- hooks
# 8000, deadline 180 s, horizon 62 at horizon_value -1,
# k 25, margin 1.5). Every teacher stat row carries the
# tuple stamp; stage2_games_report.py audits every stamp
# against the settings file before any rate is believed.
#
# Form: 4 blocks in parallel -- s1a seeds 22001-22050 seat
# 1, s1b 22051-22100 seat 1, s2a 22001-22050 seat 2, s2b
# 22051-22100 seat 2 -- each its own tree copy, snap dir,
# game-ids file, and (C) sweeper, over the tree's patched
# servers (one per seat). Every overturn is captured with
# its snapshot (TEACHER_SNAP_DIR, set per block). The game
# timeout is the DERIVED 3,214 s (settings_stage2.json
# games.timeout_derivation: per-decision wall max 56.382 s
# x contested-per-game max 57). Teacher timeouts are
# reported by stage2_games_report.py; there is no paired
# arm in Stage 2. Game ids merge into the registry (tag
# round9-stage2) BEFORE analysis, per the registration.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
OUT=${STAGE2_OUT:-/home/joe/tcg/r9s2_out}/games
GTREE=${GTREE_SRC:-/tmp/gravytree}
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
REG=/home/joe/tcg/registry-vault/do_not_train_registry.json
GAME_TIMEOUT=3214
SRV_WAIT_TRIES=${SRV_WAIT_TRIES:-60}
mkdir -p "$OUT"

# PINFN-BEGIN
expect_hash() {
  [[ "$2" =~ ^[0-9a-f]{64}$ ]] || {
    echo "ABORT: pin for $3 is not a 64-char sha256 (got ${#2} chars)" >&2; exit 1; }
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
# PINFN-END

# --- pre-flight pins ---------------------------------------------
expect_hash "$GTREE/rl/search_server.py" \
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c \
  "patched server (tree copy)"
expect_hash "$GTREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "fleet tree search.php (K2 source)"
expect_hash "$GTREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "fleet tree featurize.php"
expect_hash "$GTREE/play_game.php" \
  4ac2d62ddf64c8e8b6dfb64fac59beb639cb697026aaeb4b968fd91aa707f1d8 \
  "fleet tree play_game.php"
expect_hash "$GTREE/vendor/talishar/ParseGamestate.php" \
  0e88dd584c5c1e4df5ca491d16d5a8c742f85f34efad52b3e51a547cc6acb782 \
  "fleet tree ParseGamestate.php"
expect_hash "$GTREE/$DECK_REL" \
  b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed \
  "fleet tree Gravy deck"
expect_hash "$CKPT" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "Gravy ckpt_v10"
expect_hash "$CODE_DIR/search_s2.php" \
  85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
  "search_s2.php (Stage 2 live teacher build)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py"
expect_hash "$CODE_DIR/stage2_games_report.py" \
  62b5b319243df01211f928210dbbc6da216a48032b009b486f179ee9583ddfef \
  "stage2_games_report.py"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/settings_stage2.json" \
  2a1634ccbe67cf2f16993a1e38fc4df6005c492cb9dd769d59c9b3c19cd72f50 \
  "settings_stage2.json"

{
  echo "stage round9-stage2-games timeout_s $GAME_TIMEOUT"
  sha256sum "$CODE_DIR"/settings_stage2.json "$CODE_DIR"/*.php \
    "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
  echo "registry $REG (recorded in the manifest, pre/post)"
} > "$OUT/deployed_code_hashes.txt"

TEACHER_TUPLE_JSON=$($PY - "$CODE_DIR/settings_stage2.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps(s["teacher_tuple"]))
PYEOF
) || exit 1
export TEACHER_TUPLE_JSON

PREGATE_MANIFEST=${STAGE2_OUT:-/home/joe/tcg/r9s2_out}/pregate/pregate_manifest.json
PIN_SEARCH_S2_SHA256=85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa

# BLOCK:PREGATE-GATE-BEGIN
# Read/abort gate (review sec.2.1): this run proceeds only
# if the pre-gate manifest records verdict IDENTICAL under
# THIS run's search_s2.php pin and THIS run's tuple. The
# tuple comparison is string equality against the manifest's
# recorded teacher_tuple_json; the canonical form is the
# runners' shared builder output (python json.dumps of
# settings_stage2.json's teacher_tuple, default separators,
# file key order) -- both runners build it identically, and
# the pre-gate records the string it ran under verbatim.
[[ "$PIN_SEARCH_S2_SHA256" =~ ^[0-9a-f]{64}$ ]] || {
  echo "ABORT: pre-gate gate pin is not a 64-char sha256" >&2
  exit 1; }
$PY - "$PREGATE_MANIFEST" "$PIN_SEARCH_S2_SHA256" <<'PYEOF' || exit 1
import json, os, sys
man_p, want_sha = sys.argv[1], sys.argv[2]
want_tuple = os.environ.get("TEACHER_TUPLE_JSON", "")
def abort(why):
    sys.stderr.write("ABORT: pre-gate gate: %s\n" % why)
    sys.exit(1)
if not want_tuple:
    abort("TEACHER_TUPLE_JSON is unset in this run")
try:
    man = json.load(open(man_p))
except Exception as e:
    abort("pre-gate manifest absent or unreadable at %s (%s)"
          % (man_p, e))
if man.get("verdict") != "IDENTICAL":
    abort("pre-gate verdict is %r, not IDENTICAL"
          % (man.get("verdict"),))
if man.get("search_s2_sha256") != want_sha:
    abort("pre-gate ran under search_s2.php %s; this run "
          "pins %s" % (man.get("search_s2_sha256"), want_sha))
if man.get("teacher_tuple_json") != want_tuple:
    abort("pre-gate ran under a different TEACHER_TUPLE_JSON "
          "than this run builds from settings_stage2.json")
print("pre-gate gate: manifest IDENTICAL under this run's "
      "search_s2.php pin and tuple - proceeding")
PYEOF
# BLOCK:PREGATE-GATE-END

# --- containment: G8 pre-launch sweep -------------------------
bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

# BLOCK:GS-SRV-BEGIN
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/srv_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$GTREE/rl/search_server.py" \
    > "$OUT/srv_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 $SRV_WAIT_TRIES); do
    grep -q 'search model loaded' "$OUT/srv_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/srv_s${seat}.log" || {
    echo "ABORT: patched server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/srv_s${seat}.log" || {
    echo "ABORT: patched server seat $seat loaded the wrong model" >&2; exit 1; }
done
# BLOCK:GS-SRV-END

# --- trees (one per block) --------------------------------------
for blk in s1a s1b s2a s2b; do
  tree="/tmp/r9s2_gm_${blk}"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  expect_hash "$tree/search.php" \
      85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
      "installed search_s2.php ($tree)" || exit 1
done

# BLOCK:GS-SWEEP-BEGIN
for blk in s1a s1b s2a s2b; do
  tree="/tmp/r9s2_gm_${blk}"
  ipcs -m > "$OUT/ipcs_gm_${blk}.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_gm_${blk}.txt" \
    > "$OUT/shm_start_gm_${blk}.txt"
  rm -f "$OUT/shm_sweep_gm_${blk}.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_gm_${blk}.log" \
    --start-file "$OUT/shm_start_gm_${blk}.txt" \
    --games-dir "$tree/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_gm_${blk}.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
done
# BLOCK:GS-SWEEP-END

# --- the games (4 blocks concurrent) ------------------------------
# BLOCK:GS-DRIVERS-BEGIN
PIDS="" FAIL=0
for spec in "s1a 1 22001-22050" "s1b 1 22051-22100" \
            "s2a 2 22001-22050" "s2b 2 22051-22100"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3
  (
    tree="/tmp/r9s2_gm_${blk}"
    logdir="$OUT/games_${blk}_log"
    mkdir -p "$logdir/snaps"
    GATE_GAME_IDS_FILE="$OUT/games_${blk}_ids.txt" \
      TCG_CLEAN_CHILDREN=1 \
      TEACHER_SNAP_DIR="$logdir/snaps" \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
        --seat "$seat" --arm teacher --seeds "$seeds" \
        --deck "$tree/$DECK_REL" --timeout $GAME_TIMEOUT \
        --out "$OUT/games_${blk}.jsonl" \
        --logdir "$logdir" \
        > "$OUT/games_${blk}.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a games block failed" >&2; exit 1; }
# BLOCK:GS-DRIVERS-END
for blk in s1a s1b s2a s2b; do touch "$OUT/shm_sweep_gm_${blk}.stop"; done

# --- registry merge BEFORE analysis -------------------------------
$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag round9-stage2 \
  --ids "$OUT/games_s1a_ids.txt" --ids "$OUT/games_s1b_ids.txt" \
  --ids "$OUT/games_s2a_ids.txt" --ids "$OUT/games_s2b_ids.txt" \
  --vault /home/joe/tcg/registry-vault \
  > "$OUT/registry_merge.txt" 2>&1 || exit 1

# --- games report (tuple audit + rates + outcomes) ------------------
$PY "$CODE_DIR/stage2_games_report.py" --out-dir "$OUT" \
  --settings "$CODE_DIR/settings_stage2.json" \
  --json-out "$OUT/games_report.json" \
  > "$OUT/games_report.txt" 2>&1 || {
    echo "ABORT: games report failed (tuple audit?)" >&2
    cat "$OUT/games_report.txt" >&2; exit 1; }

# --- manifest ---------------------------------------------------------
$PY - "$OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
man = {"stage": "round9-stage2-games",
       "games_report": json.load(open(out + "/games_report.json")),
       "rows": {os.path.basename(p): rows(p) for p in
                sorted(glob.glob(out + "/games_*.jsonl"))},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/games_*.jsonl") +
           glob.glob(out + "/games_*.jsonl.manifest.json") +
           glob.glob(out + "/games_report.json") +
           glob.glob(out + "/games_*_log/search_stats.jsonl") +
           glob.glob(out + "/games_*_log/snaps/"
                     "teacher_snap_index.jsonl"))}}
json.dump(man, open(out + "/games_manifest.json", "w"), indent=1)
print("games manifest written")
PYEOF
echo "STAGE 2 GAMES COMPLETE - $OUT/games_manifest.json"
