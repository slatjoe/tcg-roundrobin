#!/bin/bash
# Round-10 Step 0 probe runner (claude-reply-9b04ad1
# sec.3 + sec.6). Phases (env PHASE): capture | eval |
# jobs | label | analyze | all. Modeled on
# run_stage1.sh (capture/eval phases, b0b08c55...) and
# run_stage3_l3.sh (label phase, 2588d595...): same
# pin discipline (expect_hash on every deployed file,
# machine-copied literals), the same free-space
# pre-flight form (round-9 Stage 3: per-tree bytes x
# trees, 1.25 headroom, abort BEFORE any copy), the
# hardened G8 sweep (g8_sweep2.sh), one (C) sweeper
# per live tree, production policy servers, and a
# manifest at the end of each phase.
#
# What runs where:
#   capture: 2 seat streams of paired_driver_gravy.py
#     --arm capture in trees carrying search_s3.php
#     (the uncontested hook build) as search.php;
#     TEACHER_CAPTURE + TEACHER_CAPTURE_UNCONTESTED
#     set ONLY here. Raw v10 plays; no picks applied.
#     Capture game ids merge into the do-not-train
#     registry (tag r10_probe_capture).
#   eval: build_probe_eval_jobs.py over both streams'
#     indexes, then s1_eval_main.php (byte-identical
#     round-9 driver) at the probe eval tuple in 4
#     shard trees carrying search_s3.php (hook envs
#     UNSET -- inert) as search.php, then
#     probe_eval_analyze.py. MEAS_SEED = eval base
#     30055001 + shard x 10^8.
#   jobs: build_probe_jobs.py (shard-cap abort is
#     the label seed family's range bound).
#   label: s2_label_main.php (byte-identical) in 4
#     shard trees carrying STOCK search_s2.php --
#     the labels run the registered round-9 machinery
#     byte for byte. MEAS_SEED = label base 70055001
#     + shard x 10^8.
#   analyze: probe_label_analyze.py + probe_report.py.
#
# STAGE3_OUT-style env: PROBE_OUT (default
# /home/joe/tcg/r10probe_out). Nothing in this runner
# touches the live teacher or any fleet.
set -u
CODE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT=${PROBE_OUT:-/home/joe/tcg/r10probe_out}
PHASE=${PHASE:-all}
BLOCK=${BLOCK:-1}
GTREE=${GTREE:-/home/joe/tcg/gravytree}
REG=${REG:-/home/joe/tcg/registry-vault/do_not_train_registry.json}
VAULT=${VAULT:-/home/joe/tcg/registry-vault}
PY=${PY:-/home/joe/tcg/rl-env/bin/python}
PHP=${PHP:-php}
CKPT=${CKPT:-/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt}
PROD=${PROD:-/home/joe/tcg/tcg-sim/rl/search_server.py}
DECK_REL="decks/nats2026_eriksen_gravy_60.txt"
SETTINGS="$CODE_DIR/settings_probe.json"
SRV_WAIT_TRIES=${SRV_WAIT_TRIES:-120}
mkdir -p "$OUT"

expect_hash() {
  local got
  got=$(sha256sum "$1" | cut -d' ' -f1)
  if [ "$got" != "$2" ]; then
    echo "ABORT: $3: sha256 $got != expected $2" >&2
    return 1
  fi
}

# --- pins ------------------------------------------------------------
expect_hash "$CODE_DIR/search_s3.php" \
  8f7be190044f4c9eee192ca206d60215b98d0bd4029febdb8da0d9cb8b0a213d \
  "probe search_s3.php" || exit 1
expect_hash "$CODE_DIR/s1_eval_main.php" \
  73ed24822baaaa9cc8ceebe4f9e082320932cc6e64b5e5f8e3f74b81764cae5a \
  "probe s1_eval_main.php (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/s2_label_main.php" \
  c7a76af4fb59e8e6e0b69a6d06157efc44597b04238cdb3b2efe48350cdda888 \
  "probe s2_label_main.php (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "probe paired_driver_gravy.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "probe merge_registry.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/search_s2.php" \
  85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
  "probe search_s2.php (round-9 byte-identical; label trees)" || exit 1
# The remaining deployed files (second fix pass,
# claude-reply-af9e9f8 sec.2.2): every file in the
# deploy list below carries an expect_hash site --
# fx_pin_guards.py enumerates the list and asserts
# the coverage, with a negative case.
expect_hash "$CODE_DIR/build_probe_eval_jobs.py" \
  94030b488d96ef137bdf215e78974714c9054f1550225a302aa6d5976f3891c3 \
  "probe build_probe_eval_jobs.py" || exit 1
expect_hash "$CODE_DIR/probe_eval_analyze.py" \
  7c4d9f691af7681777c62bcb9b8c3bbf1b103f1de7b74912f14afc65ef017f90 \
  "probe probe_eval_analyze.py" || exit 1
expect_hash "$CODE_DIR/build_probe_jobs.py" \
  c08d8c8238918e3e65340be85b743d4ce68d0493b3e4c98d206c2e229fe868ae \
  "probe build_probe_jobs.py" || exit 1
expect_hash "$CODE_DIR/probe_label_analyze.py" \
  60935aec0b75873584a73950d5b9921ea3ef93bdac80cc97f857177fdc687bfc \
  "probe probe_label_analyze.py" || exit 1
expect_hash "$CODE_DIR/probe_report.py" \
  82856c6f59cdd910f9d2f771b43da4a8b865f72c326499b2a6eb7c6603d1a81a \
  "probe probe_report.py" || exit 1
expect_hash "$CODE_DIR/settings_probe.json" \
  5af0c715442e8d7208e89da9f197dfc458a55aef22182b551f64d7f3eedca2bb \
  "probe settings_probe.json (decision rule + bar)" || exit 1
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "probe stage0_report.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 \
  "probe analyze_l3.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17 \
  "probe g8_sweep2.sh (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "probe shm_sweep.py (round-9 byte-identical)" || exit 1
# The trees below install search_s3.php (capture/eval)
# or stock search_s2.php (labels) AS search.php; the
# per-tree expect_hash calls at install time are the
# operative assertions (the round-9 form).

: > "$OUT/deployed_code_hashes.txt"
for f in search_s3.php search_s2.php s1_eval_main.php \
         s2_label_main.php \
         paired_driver_gravy.py merge_registry.py \
         build_probe_eval_jobs.py probe_eval_analyze.py \
         build_probe_jobs.py probe_label_analyze.py \
         probe_report.py settings_probe.json \
         stage0_report.py analyze_l3.py g8_sweep2.sh \
         shm_sweep.py; do
  sha256sum "$CODE_DIR/$f" >> "$OUT/deployed_code_hashes.txt"
done

# --- free-space pre-flight (tree phases only) -------------------------
# BLOCK:FREESPACE-BEGIN
case "$PHASE" in
  capture|eval|label|all)
    PER_TREE=$(du -sb "$GTREE" | cut -f1)
    NTREES=10
    REQUIRED=$((PER_TREE * NTREES))
    AVAILABLE=$(df -B1 /tmp | tail -1 | awk '{print $4}')
    echo "free-space pre-flight: required_bytes=$REQUIRED (per-tree $PER_TREE x $NTREES trees) available_bytes=$AVAILABLE headroom_factor=1.25"
    if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
      echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$REQUIRED x 1.25" >&2
      exit 1
    fi
    ;;
esac
# BLOCK:FREESPACE-END

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

start_sweeper() {
  # $1 = tree, $2 = tag
  ipcs -m > "$OUT/ipcs_$2.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$2.txt" > "$OUT/shm_start_$2.txt"
  rm -f "$OUT/shm_sweep_$2.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$2.log" \
    --start-file "$OUT/shm_start_$2.txt" \
    --games-dir "$1/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_$2.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}

# BLOCK:SRV-BEGIN
start_servers() {
  # idempotent within one invocation: a second phase
  # reuses the servers the first phase started (same
  # socket paths); across invocations the EXIT trap
  # has reaped them and the marker is stale-free
  # because the marker file lives in this run's
  # memory only (a shell variable, not a file).
  [ -n "${SERVERS_UP:-}" ] && return 0
  SERVERS_UP=1
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
}
# BLOCK:SRV-END

# --- capture ---------------------------------------------------------
if [ "$PHASE" = "capture" ] || [ "$PHASE" = "all" ]; then
  bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_capture" || exit 1
  start_servers
  read S1SEEDS S2SEEDS <<< "$($PY - "$BLOCK" <<'PYEOF'
import sys
b = int(sys.argv[1])
if b == 1:
    print("24001-24045 24046-24090")
else:
    start = 24091 + (b - 2) * 10
    print(f"{start}-{start+4} {start+5}-{start+9}")
PYEOF
)"
# BLOCK:CAPTURE-BEGIN
  for seat in 1 2; do
    seeds=$S1SEEDS; [ "$seat" = 2 ] && seeds=$S2SEEDS
    tree="/tmp/r10probe_cap_s${seat}"
    rm -rf "$tree"; cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    cp "$CODE_DIR/search_s3.php" "$tree/search.php"
    expect_hash "$tree/search.php" \
      8f7be190044f4c9eee192ca206d60215b98d0bd4029febdb8da0d9cb8b0a213d \
      "capture tree $seat search.php (search_s3)" || exit 1
    start_sweeper "$tree" "cap_s${seat}"
    logdir="$OUT/cap_s${seat}_b${BLOCK}_log"
    GATE_GAME_IDS_FILE="$OUT/cap_game_ids.txt" TCG_CLEAN_CHILDREN=1 \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/prod_s${seat}.sock" \
        --seat "$seat" --arm capture --seeds "$seeds" \
        --deck "$tree/$DECK_REL" \
        --out "$OUT/cap_s${seat}_b${BLOCK}.jsonl" \
        --logdir "$logdir" \
        > "$OUT/cap_s${seat}_b${BLOCK}.stdout" 2>&1 || exit 1
    touch "$OUT/shm_sweep_cap_s${seat}.stop"
    $PY - "$OUT/cap_s${seat}_b${BLOCK}.jsonl.manifest.json" <<'PYEOF' || exit 1
import json, sys
man = json.load(open(sys.argv[1]))
assert man["assert_ok"], f"capture arm assertions FAILED: {man['checks']}"
print(f"capture assertions OK ({man['arm']} seat {man['seat']}): "
      f"{man['assertions']}")
PYEOF
    echo "$logdir/snaps=$logdir/snaps/teacher_snap_index.jsonl" \
      >> "$OUT/streams.txt"
  done
# BLOCK:CAPTURE-END
  $PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
    --tag r10_probe_capture --ids "$OUT/cap_game_ids.txt" \
    --vault "$VAULT" | tee "$OUT/registry_merge_b${BLOCK}.txt" || exit 1
  echo "CAPTURE BLOCK $BLOCK DONE"
fi

# --- eval ------------------------------------------------------------
if [ "$PHASE" = "eval" ] || [ "$PHASE" = "all" ]; then
  [ -f "$OUT/streams.txt" ] || {
    echo "ABORT: no capture streams recorded ($OUT/streams.txt)" >&2; exit 1; }
  STREAM_ARGS=""
  while IFS= read -r line; do
    STREAM_ARGS="$STREAM_ARGS --stream $line"
  done < "$OUT/streams.txt"
  $PY "$CODE_DIR/build_probe_eval_jobs.py" $STREAM_ARGS \
    --settings "$SETTINGS" --out "$OUT/eval_jobs.jsonl" \
    --report "$OUT/eval_jobs_report.json" || exit 1
  bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_eval" || exit 1
  start_servers
  for s in 0 1 2 3; do
    tree="/tmp/r10probe_eval_tree_$s"
    rm -rf "$tree"; cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    cp "$CODE_DIR/search_s3.php" "$tree/search.php"
    cp "$CODE_DIR/s1_eval_main.php" "$tree/"
    expect_hash "$tree/search.php" \
      8f7be190044f4c9eee192ca206d60215b98d0bd4029febdb8da0d9cb8b0a213d \
      "eval tree $s search.php (search_s3, hook inert)" || exit 1
    start_sweeper "$tree" "eval_e$s"
  done
# BLOCK:EVAL-BEGIN
  PIDS="" FAIL=0
  for s in 0 1 2 3; do
    (
      tree="/tmp/r10probe_eval_tree_$s"
      for p in 1 2; do
        $PY - "$OUT" "$s" "$p" <<'PYEOF'
import hashlib, json, sys
out, s, p = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
jobs = [json.loads(l) for l in open(f"{out}/eval_jobs.jsonl")
        if l.strip()]
sel = [j for j in jobs
       if int(hashlib.sha256(str(j["game"]).encode()).hexdigest(),
              16) % 4 == s and int(j["player"]) == p]
with open(f"{out}/eval_jobs_shard{s}_p{p}.jsonl", "w") as f:
    for j in sel:
        f.write(json.dumps(j) + "\n")
print(f"eval shard {s} player {p}: {len(sel)} jobs")
PYEOF
        : > "$OUT/evals_shard${s}_p$p.jsonl"
        : > "$OUT/eval_stats_shard${s}_p$p.jsonl"
        (cd "$tree" && MEAS_JOBS="$OUT/eval_jobs_shard${s}_p$p.jsonl" \
           MEAS_OUT="$OUT/evals_shard${s}_p$p.jsonl" \
           EVAL_STATS="$OUT/eval_stats_shard${s}_p$p.jsonl" \
           MEAS_SEED=$((30055001 + s * 100000000)) \
           EVAL_SETTING_NAME="R10-EVAL-K25+H" EVAL_HOOKS=8000 \
           EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
           EVAL_HORIZON_VALUE=-1 EVAL_K=25 \
           TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
           $PHP s1_eval_main.php \
             "$tree/$DECK_REL" "$tree/$DECK_REL" \
             --policy-search --games 1 \
             > "$OUT/eval_shard${s}_p$p.err" 2>&1) || exit 1
      done
      touch "$OUT/shm_sweep_eval_e$s.stop"
    ) &
    PIDS="$PIDS $!"
  done
  for pid in $PIDS; do wait "$pid" || FAIL=1; done
  [ "$FAIL" = 0 ] || {
    echo "ABORT: an eval shard failed" >&2; exit 1; }
# BLOCK:EVAL-END
  cat "$OUT"/evals_shard*_p*.jsonl > "$OUT/evals_all.jsonl"
  cat "$OUT"/eval_stats_shard*_p*.jsonl > "$OUT/eval_stats_all.jsonl"
  $PY "$CODE_DIR/probe_eval_analyze.py" \
    --jobs "$OUT/eval_jobs.jsonl" --rows "$OUT/evals_all.jsonl" \
    --stats "$OUT/eval_stats_all.jsonl" \
    --jobs-report "$OUT/eval_jobs_report.json" \
    --settings "$SETTINGS" \
    --states-out "$OUT/eval_states.jsonl" \
    --json-out "$OUT/eval_summary.json" || exit 1
  echo "EVAL DONE"
fi

# --- label jobs --------------------------------------------------------
if [ "$PHASE" = "jobs" ] || [ "$PHASE" = "all" ]; then
  $PY "$CODE_DIR/build_probe_jobs.py" \
    --states "$OUT/eval_states.jsonl" \
    --eval-jobs "$OUT/eval_jobs.jsonl" \
    --settings "$SETTINGS" --out "$OUT/jobs_all.jsonl" \
    --shard-prefix "$OUT/jobs_shard" \
    --report "$OUT/jobs_report.json" || exit 1
  echo "JOBS DONE"
fi

# --- labels ------------------------------------------------------------
if [ "$PHASE" = "label" ] || [ "$PHASE" = "all" ]; then
  $PY - "$OUT" <<'PYEOF' || exit 1
import json, sys
out = sys.argv[1]
for s in range(4):
    src = f"{out}/jobs_shard{s}.jsonl"
    rows = [json.loads(l) for l in open(src) if l.strip()]
    for p in (1, 2):
        sel = [j for j in rows if int(j["player"]) == p]
        with open(f"{out}/jobs_shard{s}_p{p}.jsonl", "w") as f:
            for j in sel:
                f.write(json.dumps(j) + "\n")
        print(f"label shard {s} player {p}: {len(sel)} jobs")
PYEOF
  bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_label" || exit 1
  start_servers
  for s in 0 1 2 3; do
    tree="/tmp/r10probe_l3_tree_$s"
    rm -rf "$tree"; cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    cp "$CODE_DIR/search_s2.php" "$tree/search.php"
    cp "$CODE_DIR/s2_label_main.php" "$tree/"
    expect_hash "$tree/search.php" \
      85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
      "label tree $s search.php (stock search_s2)" || exit 1
    start_sweeper "$tree" "l3_$s"
  done
# BLOCK:LABEL-BEGIN
  PIDS="" FAIL=0
  for s in 0 1 2 3; do
    (
      tree="/tmp/r10probe_l3_tree_$s"
      for p in 1 2; do
        : > "$OUT/labels_shard${s}_p$p.jsonl"
        (cd "$tree" && MEAS_JOBS="$OUT/jobs_shard${s}_p$p.jsonl" \
           MEAS_OUT="$OUT/labels_shard${s}_p$p.jsonl" \
           EVAL_STATS="$OUT/label_stats_shard${s}_p$p.jsonl" \
           MEAS_SEED=$((70055001 + s * 100000000)) \
           TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
           EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
           EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
           EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
           $PHP s2_label_main.php \
             "$tree/$DECK_REL" "$tree/$DECK_REL" \
             --policy-search --games 1 \
             > "$OUT/label_shard${s}_p$p.err" 2>&1) || exit 1
      done
      touch "$OUT/shm_sweep_l3_$s.stop"
    ) &
    PIDS="$PIDS $!"
  done
  for pid in $PIDS; do wait "$pid" || FAIL=1; done
  [ "$FAIL" = 0 ] || {
    echo "ABORT: a label shard failed" >&2; exit 1; }
# BLOCK:LABEL-END
  cat "$OUT"/labels_shard*_p*.jsonl > "$OUT/labels_all.jsonl"
  echo "LABEL DONE"
fi

# --- analyze -----------------------------------------------------------
if [ "$PHASE" = "analyze" ] || [ "$PHASE" = "all" ]; then
  $PY "$CODE_DIR/probe_label_analyze.py" \
    --jobs "$OUT/jobs_all.jsonl" --labels "$OUT/labels_all.jsonl" \
    --capture-games "$OUT/eval_jobs_report.json" \
    --settings "$SETTINGS" \
    --json-out "$OUT/label_read.json" \
    > "$OUT/label_read.txt" || exit 1
  $PY "$CODE_DIR/probe_report.py" \
    --eval-summary "$OUT/eval_summary.json" \
    --eval-jobs-report "$OUT/eval_jobs_report.json" \
    --label-read "$OUT/label_read.json" \
    --settings "$SETTINGS" \
    --json-out "$OUT/probe_report.json" \
    > "$OUT/probe_report.txt" || exit 1
  $PY - "$OUT" <<'PYEOF'
import hashlib, json, os, sys
out = sys.argv[1]
man = {}
for fn in sorted(os.listdir(out)):
    p = os.path.join(out, fn)
    if os.path.isfile(p):
        man[fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
with open(os.path.join(out, "probe_manifest.json"), "w") as f:
    json.dump({"files": man}, f, indent=1)
print("probe manifest written: %d files" % len(man))
PYEOF
  echo "ANALYZE DONE"
fi
echo "run_probe.sh PHASE=$PHASE BLOCK=$BLOCK complete"
