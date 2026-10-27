#!/bin/bash
# Round-9 Stage 3 L3 (ruling sec.4.6): every overturn the
# calibrated teacher captured in the Stage 3 games, labeled
# at LABEL_W=50, CRN, against the PRODUCTION server, seed
# bases 50055001 + shard x 10^8, horizon 62 pinned -- the
# registered label tuple (settings_stage3.json label_tuple:
# L3-W50+H, carried over from Stage 2 unchanged).
# stage3_attr_analyze.py renders the ATTRIBUTION read
# (a co-report, not a gate: no PROCEED/STOP bands).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage 3
# package at its committed sha and Joe's explicit go, and
# only after run_stage3_games.sh has completed with its
# tuple audit OK (the games report AND the paired read are
# inputs here: the attribution ratio divides by the Stage 3
# fleet delta).
#
# Shape (the Stage 0/2 form): jobs built by build_s3_jobs.py
# from the 4 TEACHER blocks' snap indexes; 4 shards by game
# (sha256(game) mod 4); per shard a fleet-tree copy carrying
# search_s2.php (its label path IS the registered
# instrument) + s2_label_main.php; within a shard, jobs run
# in two sequential groups by root player against that
# seat's production server. Containment: hardened G8 sweep
# (g8_sweep2.sh) + one (C) sweeper per shard tree.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
GAMES_OUT=${STAGE3_OUT:-/home/joe/tcg/r9s3_out}/games
OUT=${STAGE3_OUT:-/home/joe/tcg/r9s3_out}/l3
GTREE=${GTREE_SRC:-/tmp/gravytree}
PROD=$SIM/rl/search_server.py
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
LABEL_BASE=50055001
NSHARD=4
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
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
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
  "search_s2.php (label path = the registered instrument)"
expect_hash "$CODE_DIR/s2_label_main.php" \
  c7a76af4fb59e8e6e0b69a6d06157efc44597b04238cdb3b2efe48350cdda888 \
  "s2_label_main.php (L3 driver)"
expect_hash "$CODE_DIR/build_s3_jobs.py" \
  fabecae5087d48c1eb2127e11ee750939d364c22b14e2d6b5d534a863fb2d498 \
  "build_s3_jobs.py"
expect_hash "$CODE_DIR/stage3_attr_analyze.py" \
  788cd28a5018d2786f67cd2b0a17c321598795bed9bc97e4b903dc837537fb21 \
  "stage3_attr_analyze.py"
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "stage0_report.py (taxonomy import)"
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 \
  "analyze_l3.py (bootstrap import)"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17 \
  "g8_sweep2.sh (hardened G8 sweep)"
expect_hash "$CODE_DIR/settings_stage3.json" \
  34337753835aae29e2fb9bf9c090cc2a2f64b7799d487210c093d48a1040ed2e \
  "settings_stage3.json"

{
  echo "stage round9-stage3-l3 label_base $LABEL_BASE"
  sha256sum "$CODE_DIR"/settings_stage3.json "$CODE_DIR"/*.php \
    "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
} > "$OUT/deployed_code_hashes.txt"

# BLOCK:FREESPACE-BEGIN
# Free-space pre-flight (homework b): the runner copies the
# fleet tree once per shard; a full /tmp mid-run kills games
# silently, so measure the source tree FRESH here and demand
# 1.25x headroom over N_TREES copies BEFORE the first copy.
# Fixture seams (test-only; production leaves both unset):
# S3_REQ_PER_TREE_OVERRIDE replaces the du measurement and
# S3_DF_AVAIL_OVERRIDE replaces the df measurement, so
# fx_s3_blocks can extract this block verbatim and drive
# both branches. Integer arithmetic only: abort when
# AVAILABLE * 4 < REQUIRED * 5 (available < required x 1.25).
REQ_PER_TREE=${S3_REQ_PER_TREE_OVERRIDE:-$(du -sb "$GTREE" | awk '{print $1}')}
N_TREES=4
REQUIRED=$((REQ_PER_TREE * N_TREES))
AVAILABLE=${S3_DF_AVAIL_OVERRIDE:-$(df -B1 --output=avail "$GTREE" | tail -1 | tr -d ' ')}
echo "free-space pre-flight: required_bytes=$REQUIRED (per-tree $REQ_PER_TREE x $N_TREES trees) available_bytes=$AVAILABLE headroom_factor=1.25"
if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
  echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$REQUIRED x 1.25" >&2
  exit 1
fi
# BLOCK:FREESPACE-END

[ -f "$GAMES_OUT/games_report.json" ] || {
  echo "ABORT: games report missing (games phase incomplete)" >&2
  exit 1; }
[ -f "$GAMES_OUT/stage3_read.json" ] || {
  echo "ABORT: stage3 paired read missing (games phase incomplete)" >&2
  exit 1; }

# --- jobs: every captured overturn, sharded by game ----------------
STREAM_ARGS=""
for blk in t1a t1b t2a t2b; do
  STREAM_ARGS="$STREAM_ARGS --stream $GAMES_OUT/games_${blk}_log/snaps=$GAMES_OUT/games_${blk}_log/snaps/teacher_snap_index.jsonl"
done
$PY "$CODE_DIR/build_s3_jobs.py" $STREAM_ARGS \
  --settings "$CODE_DIR/settings_stage3.json" \
  --out "$OUT/jobs_all.jsonl" --shard-prefix "$OUT/jobs_shard" \
  --report "$OUT/jobs_report.json" --nshard $NSHARD || exit 1

# --- shard job copies: absolute snap dirs asserted ------------------
$PY - "$OUT" "$NSHARD" <<'PYEOF' || exit 1
import json, os, sys
out, nshard = sys.argv[1], int(sys.argv[2])
for s in range(nshard):
    src = f"{out}/jobs_shard{s}.jsonl"
    jobs = [json.loads(l) for l in open(src) if l.strip()]
    for p in (1, 2):
        sel = [j for j in jobs if int(j["player"]) == p]
        with open(f"{out}/jobs_shard{s}_p{p}.jsonl", "w") as f:
            for j in sel:
                assert os.path.isdir(j["snap_dir"]), \
                    f"snap dir missing: {j['snap_dir']}"
                f.write(json.dumps(j) + "\n")
        print(f"shard {s} player {p}: {len(sel)} jobs")
PYEOF

# --- containment: G8 pre-launch sweep -------------------------------
bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8" || exit 1

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

# BLOCK:LS-SRV-BEGIN
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$PROD" > "$OUT/prod_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 $SRV_WAIT_TRIES); do
    grep -q 'search model loaded' "$OUT/prod_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat loaded the wrong model" >&2; exit 1; }
done
# BLOCK:LS-SRV-END

# --- trees (one per shard) -------------------------------------------
for s in 0 1 2 3; do
  tree="/tmp/r9s3_l3_tree_$s"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  cp "$CODE_DIR/s2_label_main.php" "$tree/"
  expect_hash "$tree/search.php" \
      85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
      "installed search_s2.php (shard tree $s)" || exit 1
done

# BLOCK:LS-SWEEP-BEGIN
for s in 0 1 2 3; do
  tree="/tmp/r9s3_l3_tree_$s"
  ipcs -m > "$OUT/ipcs_l3_shard$s.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_l3_shard$s.txt" \
    > "$OUT/shm_start_l3$s.txt"
  rm -f "$OUT/shm_sweep_l3$s.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_l3$s.log" \
    --start-file "$OUT/shm_start_l3$s.txt" \
    --games-dir "$tree/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_l3$s.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
done
# BLOCK:LS-SWEEP-END

# BLOCK:LS-SHARD-BEGIN
PIDS="" FAIL=0
for s in 0 1 2 3; do
  (
    tree="/tmp/r9s3_l3_tree_$s"
    for p in 1 2; do
      : > "$OUT/labels_shard${s}_p$p.jsonl"
      (cd "$tree" && MEAS_JOBS="$OUT/jobs_shard${s}_p$p.jsonl" \
         MEAS_OUT="$OUT/labels_shard${s}_p$p.jsonl" \
         EVAL_STATS="$OUT/label_stats_shard${s}_p$p.jsonl" \
         MEAS_SEED=$((LABEL_BASE + s * 100000000)) \
         TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
         EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
         EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
         EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
         php s2_label_main.php \
           "$tree/$DECK_REL" "$tree/$DECK_REL" \
           --policy-search --games 1 \
           > "$OUT/label_shard${s}_p$p.err" 2>&1) || exit 1
    done
  ) &
  PIDS="$PIDS $!"
done
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: an L3 label shard failed" >&2; exit 1; }
# BLOCK:LS-SHARD-END
for s in 0 1 2 3; do touch "$OUT/shm_sweep_l3$s.stop"; done
cat "$OUT"/labels_shard*_p*.jsonl > "$OUT/labels_all.jsonl"

# --- the read ---------------------------------------------------------
$PY "$CODE_DIR/stage3_attr_analyze.py" --jobs "$OUT/jobs_all.jsonl" \
  --labels "$OUT/labels_all.jsonl" \
  --games-report "$GAMES_OUT/games_report.json" \
  --stage3-read "$GAMES_OUT/stage3_read.json" \
  --settings "$CODE_DIR/settings_stage3.json" \
  --json-out "$OUT/attr_read.json" \
  > "$OUT/attr_read.txt" 2>&1 || {
    echo "ABORT: stage3 attribution analyzer failed" >&2
    cat "$OUT/attr_read.txt" >&2; exit 1; }
cat "$OUT/attr_read.txt"

# --- manifest ---------------------------------------------------------
$PY - "$OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def rows(p):
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0
man = {"stage": "round9-stage3-l3",
       "read": json.load(open(out + "/attr_read.json")),
       "jobs": json.load(open(out + "/jobs_report.json")),
       "labels_rows": rows(out + "/labels_all.jsonl"),
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/labels_*.jsonl") +
           glob.glob(out + "/jobs_*.jsonl") +
           glob.glob(out + "/attr_read.json"))}}
json.dump(man, open(out + "/l3_manifest.json", "w"), indent=1)
print("l3 manifest written")
PYEOF
echo "STAGE 3 L3 COMPLETE - $OUT/l3_manifest.json"
