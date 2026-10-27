#!/bin/bash
# Round-9 Stage 3 GAMES (ruling sec.4): the PAIRED fleet
# read -- calibrated teacher vs raw v10, same seed + same
# seat per pair; Gravy mirror vs heuristic; instrument
# 87/62; seeds 23001-23200 x seats {1,2} x arms {teacher,
# raw} = 800 games, 400 pairs.
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage 3
# package at its committed sha and Joe's explicit go.
# PRE-GATE: no new run -- the PREGATE-GATE block below
# reads the STAGE 2 pre-gate manifest and aborts unless it
# records IDENTICAL under this run's search_s2.php pin and
# the tuple built from settings_stage3.json (byte-identical
# reuse of the Stage 2 teacher tuple).
#
# Form: teacher phase first -- 4 blocks (t1a seeds
# 23001-23100 seat 1, t1b 23101-23200 seat 1, t2a seat 2
# low, t2b seat 2 high) over the tree's 2 patched servers,
# per-block tree copies with search_s2.php installed and
# hash-asserted, TEACHER_SNAP_DIR set (every overturn
# captured). Raw phase runs AFTER the teacher phase
# completes (never concurrent): the teacher servers are
# stopped and raw-phase servers started on the same sockets
# (RS-SRV); 4 raw blocks (r1a/r1b/r2a/r2b) mirror the
# teacher layout on trees WITHOUT search.php installed
# (the fleet tree's own search.php, hash-asserted). The
# raw arm is paired_driver_gravy.py --arm raw
# (--policy-server). GAME_TIMEOUT=3214 for both arms
# (settings_stage3.json games.timeout_derivation).
# A raw hang is NOT re-run inline: the RAW-RERUN section
# builds a draft pairing, then re-runs each timed-out raw
# (seed, seat) once into games_<rblk>_rerun.jsonl.
# Registry merge (tag round9-stage3) over ALL game-ids
# files BEFORE the games report; then the full games
# report (final pairing.json + games_report.json) and the
# paired analyzer (stage3_analyze.py -> stage3_read).
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
OUT=${STAGE3_OUT:-/home/joe/tcg/r9s3_out}/games
GTREE=${GTREE_SRC:-/tmp/gravytree}
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
REG=/home/joe/tcg/registry-vault/do_not_train_registry.json
GAME_TIMEOUT=${GAME_TIMEOUT:-3214}
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
  "search_s2.php (Stage 2 live teacher build, reused byte-identical)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py"
expect_hash "$CODE_DIR/stage3_games_report.py" \
  4f19306d6ca1000756bccc05867ab6558dd47c3055870a56ff9de5052940fe25 \
  "stage3_games_report.py"
expect_hash "$CODE_DIR/stage3_analyze.py" \
  e283a23711221c959aba138a8d9104893cebbcc78bb774b24b6d92bc908ff76e \
  "stage3_analyze.py"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  72b18b3402ca5132bcdd4d1c6ea1f9f6c8cc3fc9e3fea76472dc0a09e5293a86 \
  "g8_sweep2.sh (hardened G8 sweep)"
expect_hash "$CODE_DIR/settings_stage3.json" \
  b241515588b8152145bed2708432aa377ce4f054131fff150076e8998b5be912 \
  "settings_stage3.json"

{
  echo "stage round9-stage3-games timeout_s $GAME_TIMEOUT"
  sha256sum "$CODE_DIR"/settings_stage3.json "$CODE_DIR"/*.php \
    "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
  echo "registry $REG (recorded in the manifest, pre/post)"
} > "$OUT/deployed_code_hashes.txt"

TEACHER_TUPLE_JSON=$($PY - "$CODE_DIR/settings_stage3.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
print(json.dumps(s["teacher_tuple"]))
PYEOF
) || exit 1
export TEACHER_TUPLE_JSON

PREGATE_MANIFEST=${STAGE2_OUT:-/home/joe/tcg/r9s2_out}/pregate/pregate_manifest.json
PIN_SEARCH_S2_SHA256=85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa

# BLOCK:PREGATE-GATE-BEGIN
# Read/abort gate (Stage 2 review sec.2.1 form, ruling
# sec.4: NO new pre-gate run for Stage 3): this run proceeds
# only if the STAGE 2 pre-gate manifest records verdict
# IDENTICAL under THIS run's search_s2.php pin and the
# tuple THIS run builds from settings_stage3.json (the
# Stage 2 teacher tuple, byte-identical reuse). The tuple
# comparison is string equality against the manifest's
# recorded teacher_tuple_json; the canonical form is the
# runners' shared builder output (python json.dumps of the
# settings teacher_tuple, default separators, file key
# order). An absent or unreadable manifest aborts.
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
          "than this run builds from settings_stage3.json")
print("pre-gate gate: Stage 2 manifest IDENTICAL under this "
      "run's search_s2.php pin and tuple - proceeding")
PYEOF
# BLOCK:PREGATE-GATE-END

# BLOCK:FREESPACE-BEGIN
# Free-space pre-flight (homework b): the runner copies the
# fleet tree once per block; a full /tmp mid-run kills games
# silently, so measure the source tree FRESH here and demand
# 1.25x headroom over N_TREES copies BEFORE the first copy.
# Fixture seams (test-only; production leaves both unset):
# S3_REQ_PER_TREE_OVERRIDE replaces the du measurement and
# S3_DF_AVAIL_OVERRIDE replaces the df measurement, so
# fx_s3_blocks can extract this block verbatim and drive
# both branches. Integer arithmetic only: abort when
# AVAILABLE * 4 < REQUIRED * 5 (available < required x 1.25).
REQ_PER_TREE=${S3_REQ_PER_TREE_OVERRIDE:-$(du -sb "$GTREE" | awk '{print $1}')}
N_TREES=8
REQUIRED=$((REQ_PER_TREE * N_TREES))
AVAILABLE=${S3_DF_AVAIL_OVERRIDE:-$(df -B1 --output=avail "$GTREE" | tail -1 | tr -d ' ')}
echo "free-space pre-flight: required_bytes=$REQUIRED (per-tree $REQ_PER_TREE x $N_TREES trees) available_bytes=$AVAILABLE headroom_factor=1.25"
if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
  echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$REQUIRED x 1.25" >&2
  exit 1
fi
# BLOCK:FREESPACE-END

# --- containment: G8 pre-launch sweep (hardened) ----------------
bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8" || exit 1

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

# BLOCK:TS-SRV-BEGIN
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
# BLOCK:TS-SRV-END

# --- teacher trees (one per block, search_s2 installed) ---------
for blk in t1a t1b t2a t2b; do
  tree="/tmp/r9s3_gm_${blk}"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  expect_hash "$tree/search.php" \
      85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
      "installed search_s2.php ($tree)" || exit 1
done

# BLOCK:TS-SWEEP-BEGIN
for blk in t1a t1b t2a t2b; do
  tree="/tmp/r9s3_gm_${blk}"
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
# BLOCK:TS-SWEEP-END

# --- the teacher games (4 blocks concurrent) ---------------------
# BLOCK:TS-DRIVERS-BEGIN
PIDS="" FAIL=0
for spec in "t1a 1 23001-23100" "t1b 1 23101-23200" \
            "t2a 2 23001-23100" "t2b 2 23101-23200"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3
  (
    tree="/tmp/r9s3_gm_${blk}"
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
[ "$FAIL" = 0 ] || { echo "ABORT: a teacher games block failed" >&2; exit 1; }
# BLOCK:TS-DRIVERS-END
for blk in t1a t1b t2a t2b; do touch "$OUT/shm_sweep_gm_${blk}.stop"; done
SWEEP_PIDS=""

# BLOCK:RS-SRV-BEGIN
# Raw phase servers: stop the teacher-phase servers first,
# then start raw-phase servers on the SAME sockets (the
# tree's 2 patched servers serve both phases, sequentially).
for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null || true; done
SRV_PIDS=""
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/srv_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$GTREE/rl/search_server.py" \
    > "$OUT/srv_raw_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 $SRV_WAIT_TRIES); do
    grep -q 'search model loaded' "$OUT/srv_raw_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/srv_raw_s${seat}.log" || {
    echo "ABORT: raw-phase server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/srv_raw_s${seat}.log" || {
    echo "ABORT: raw-phase server seat $seat loaded the wrong model" >&2; exit 1; }
done
# BLOCK:RS-SRV-END

# --- raw trees (NO search install: fleet search.php asserted) ---
for blk in r1a r1b r2a r2b; do
  tree="/tmp/r9s3_gm_${blk}"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  expect_hash "$tree/search.php" \
      8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
      "raw tree keeps fleet search.php ($tree)" || exit 1
done

# BLOCK:RS-SWEEP-BEGIN
for blk in r1a r1b r2a r2b; do
  tree="/tmp/r9s3_gm_${blk}"
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
# BLOCK:RS-SWEEP-END

# --- the raw games (4 blocks concurrent, AFTER teacher) ----------
# BLOCK:RS-DRIVERS-BEGIN
PIDS="" FAIL=0
for spec in "r1a 1 23001-23100" "r1b 1 23101-23200" \
            "r2a 2 23001-23100" "r2b 2 23101-23200"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3
  (
    tree="/tmp/r9s3_gm_${blk}"
    logdir="$OUT/games_${blk}_log"
    mkdir -p "$logdir"
    GATE_GAME_IDS_FILE="$OUT/games_${blk}_ids.txt" \
      TCG_CLEAN_CHILDREN=1 \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
        --seat "$seat" --arm raw --seeds "$seeds" \
        --deck "$tree/$DECK_REL" --timeout $GAME_TIMEOUT \
        --out "$OUT/games_${blk}.jsonl" \
        --logdir "$logdir" \
        > "$OUT/games_${blk}.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a raw games block failed" >&2; exit 1; }
# BLOCK:RS-DRIVERS-END
for blk in r1a r1b r2a r2b; do touch "$OUT/shm_sweep_gm_${blk}.stop"; done

# --- raw reruns: one re-run per timed-out raw (seed, seat) -------
# BLOCK:RAW-RERUN-BEGIN
$PY "$CODE_DIR/stage3_games_report.py" --pairing-only \
  --out-dir "$OUT" --settings "$CODE_DIR/settings_stage3.json" \
  > "$OUT/pairing_draft.txt" 2>&1 || {
    echo "ABORT: draft pairing for the rerun pass failed" >&2
    cat "$OUT/pairing_draft.txt" >&2; exit 1; }
RERUN_LIST=$($PY - "$OUT/pairing_draft.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
for p in d["pairs"]:
    r = p.get("raw") or {}
    row = r.get("row") or {}
    if row.get("invalid") == "timeout":
        blk = (r.get("file") or "").replace("games_", "") \
                                   .replace(".jsonl", "")
        print("%s %s %s" % (p["seed"], p["seat"], blk))
PYEOF
) || exit 1
PIDS="" FAIL=0
while read -r seed seat rblk; do
  [ -n "$seed" ] || continue
  (
    tree="/tmp/r9s3_gm_${rblk}"
    logdir="$OUT/games_${rblk}_rerun_log"
    mkdir -p "$logdir"
    GATE_GAME_IDS_FILE="$OUT/games_${rblk}_rerun_ids.txt" \
      TCG_CLEAN_CHILDREN=1 \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/srv_s${seat}.sock" \
        --seat "$seat" --arm raw --seeds "$seed" \
        --deck "$tree/$DECK_REL" --timeout $GAME_TIMEOUT \
        --out "$OUT/games_${rblk}_rerun.jsonl" \
        --logdir "$logdir" \
        > "$OUT/games_${rblk}_rerun.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done <<EOF_RERUN
$RERUN_LIST
EOF_RERUN
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a raw rerun failed" >&2; exit 1; }
# BLOCK:RAW-RERUN-END

# --- registry merge BEFORE analysis (ALL ids files) --------------
IDS_ARGS=""
for f in "$OUT"/games_*_ids.txt; do IDS_ARGS="$IDS_ARGS --ids $f"; done
$PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
  --tag round9-stage3 \
  $IDS_ARGS \
  --vault /home/joe/tcg/registry-vault \
  > "$OUT/registry_merge.txt" 2>&1 || exit 1

# --- games report, full mode (final pairing + tuple audit) -------
$PY "$CODE_DIR/stage3_games_report.py" --out-dir "$OUT" \
  --settings "$CODE_DIR/settings_stage3.json" \
  --json-out "$OUT/games_report.json" \
  > "$OUT/games_report.txt" 2>&1 || {
    echo "ABORT: games report failed (tuple audit?)" >&2
    cat "$OUT/games_report.txt" >&2; exit 1; }

# --- the paired read ----------------------------------------------
$PY "$CODE_DIR/stage3_analyze.py" --pairing "$OUT/pairing.json" \
  --games-report "$OUT/games_report.json" \
  --settings "$CODE_DIR/settings_stage3.json" \
  --json-out "$OUT/stage3_read.json" \
  > "$OUT/stage3_read.txt" 2>&1 || {
    echo "ABORT: stage3 analyzer failed" >&2
    cat "$OUT/stage3_read.txt" >&2; exit 1; }
cat "$OUT/stage3_read.txt"

# --- manifest -------------------------------------------------------
$PY - "$OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
man = {"stage": "round9-stage3-games",
       "pairing": json.load(open(out + "/pairing.json"))["counts"],
       "games_report": json.load(open(out + "/games_report.json")),
       "read": json.load(open(out + "/stage3_read.json")),
       "rows": {os.path.basename(p): rows(p) for p in
                sorted(glob.glob(out + "/games_*.jsonl"))},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/games_*.jsonl") +
           glob.glob(out + "/games_*.jsonl.manifest.json") +
           glob.glob(out + "/pairing.json") +
           glob.glob(out + "/games_report.json") +
           glob.glob(out + "/stage3_read.json") +
           glob.glob(out + "/stage3_read.txt") +
           glob.glob(out + "/games_*_log/search_stats.jsonl") +
           glob.glob(out + "/games_*_log/snaps/"
                     "teacher_snap_index.jsonl"))}}
json.dump(man, open(out + "/games_manifest.json", "w"), indent=1)
print("games manifest written")
PYEOF
echo "STAGE 3 GAMES COMPLETE - $OUT/games_manifest.json"
