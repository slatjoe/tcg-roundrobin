#!/bin/bash
# Round-8 PILOT - the label-validity + cost pilot
# (build-package sec.3; claude-reply-926f6c3 sec.1, sec.8.3).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's approval of the round-8 build package
# at its committed sha AND Joe's go in chat (the pilot is the
# first of round 8's four go-gates).
#
# What it does, in order:
#   0. Guards: native-tree pins, production-server pin, v15 pin,
#      deployed code hashes logged.
#   1. Pre-launch G8 sweep of stale segments (evidence files in
#      $OUT), then the (C) kernel-attribution sweeper alongside
#      the label work, pointed at the native tree's Games dir
#      (the labeler runs teacher roots there against the
#      production server - the round-7 L-run conditions).
#   2. pilot_prep.py: 20 jobs sampled from the Fai gate fleet's
#      surviving overturn snapshots, "selected" joined from the
#      fleet's stat rows (join asserted per row).
#   3. Production servers (seat 1 + seat 2, v15). Label runs:
#      run A (DISTILL_SEED 555001) and run B (777001) - the same
#      20 jobs under two different world-seed bases. Jobs are
#      split by root player; each (run, player) group is ONE
#      distill_label_main.php invocation in the native tree
#      against that seat's production server (one label process
#      per tree at a time - SimLabel_RunForSnapshot's scratch
#      discipline). Per-job timings come from the main's own
#      stderr lines.
#   4. label_reduce.py on both runs; pilot_report.py assembles
#      the timing read (mean + p95), V1, V2, thin counts.
#   5. Teacher-root census (report-only): a scratch tree (native
#      + the round-5 census probe, unchanged) featurizes the 20
#      pilot roots via featurize_snapshot.php with CENSUS_LOG
#      set; tally_census.py (round 5, unchanged) tallies by
#      direction and branch.
# Nothing here passes or fails itself: the report goes to Claude
# and Joe, and the corpus run is gated on their read plus Joe's
# go.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
NATIVE=${NATIVE_TREE:-/tmp/distilltree_native}
PROBE_TREE=${PROBE_TREE:-/tmp/distilltree_censusprobe}
PROD=/home/joe/tcg/tcg-sim/rl/search_server.py
MODEL=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
DECK=$NATIVE/decks/nats2026_ashlyn_fai_60.txt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
OUT=${PILOT_OUT:-/tmp/distill_pilot}
mkdir -p "$OUT"

expect_hash() { # path sha label
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
expect_hash "$NATIVE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "native featurize.php"
expect_hash "$NATIVE/search.php" \
  6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a \
  "native search.php"
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$MODEL" \
  0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"
for f in distill_label_main.php featurize_snapshot.php \
         label_reduce.py pilot_prep.py pilot_report.py pilot_times.py \
         patch_census_probe.py tally_census.py shm_sweep.py \
         g8_sweep.sh; do
  [ -f "$CODE_DIR/$f" ] || { echo "ABORT: $CODE_DIR/$f missing" >&2; exit 1; }
done
sha256sum "$CODE_DIR"/* > "$OUT/deployed_code_hashes.txt"

# Deploy the labeler + featurizer into the native tree root (the
# label mains' bootstrap pattern: tools live at the tree root).
cp "$CODE_DIR/distill_label_main.php" "$NATIVE/"
cp "$CODE_DIR/featurize_snapshot.php" "$NATIVE/"

# --- containment: pre-launch G8 + (C) sweeper -------------------
ipcs -m > "$OUT/ipcs_before.txt"
bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1
ipcs -m > "$OUT/ipcs_run_start.txt"
awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_run_start.txt" > "$OUT/shm_start.txt"
rm -f "$OUT/shm_sweep.stop"
$PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep.log" \
  --start-file "$OUT/shm_start.txt" \
  --games-dir "$NATIVE/vendor/talishar/Games" \
  --interval 60 --stop-file "$OUT/shm_sweep.stop" &
SWEEP_PID=$!

SRV_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  touch "$OUT/shm_sweep.stop" 2>/dev/null
  kill "$SWEEP_PID" 2>/dev/null
}
trap cleanup EXIT

start_prod_server() { # seat sock log
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
    setsid nohup $PY "$PROD" > "$3" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$3" 2>/dev/null && return 0
    sleep 1
  done
  echo "ABORT: production server (seat $1) did not load" >&2
  return 1
}
start_prod_server 1 "$OUT/prod_s1.sock" "$OUT/prod_s1.log" || exit 1
start_prod_server 2 "$OUT/prod_s2.sock" "$OUT/prod_s2.log" || exit 1
sha256sum "$PROD" > "$OUT/prod_server_hash.txt"

# --- jobs --------------------------------------------------------
$PY "$CODE_DIR/pilot_prep.py" --out "$OUT" || exit 1

split_jobs() { # jobs player outfile
  $PY - "$1" "$2" "$3" <<'PYEOF'
import json, sys
jobs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
sel = [j for j in jobs if int(j["player"]) == int(sys.argv[2])]
with open(sys.argv[3], "w") as f:
    for j in sel:
        f.write(json.dumps(j) + "\n")
print(f"player {sys.argv[2]} jobs: {len(sel)}")
PYEOF
}

run_labels() { # run seed
  local run=$1 seed=$2 p sock
  : > "$OUT/label_${run}.err"
  for p in 1 2; do
    split_jobs "$OUT/pilot_jobs.jsonl" "$p" "$OUT/jobs_${run}_p$p.jsonl" || exit 1
    : > "$OUT/raw_${run}_p$p.jsonl"
    sock="$OUT/prod_s$p.sock"
    (cd "$NATIVE" && DISTILL_JOBS="$OUT/jobs_${run}_p$p.jsonl" \
       DISTILL_OUT="$OUT/raw_${run}_p$p.jsonl" DISTILL_SEED="$seed" \
       TCG_POLICY_SOCK="$sock" \
       php distill_label_main.php "$DECK" "$DECK" \
         --policy-search --games 1 >> "$OUT/label_${run}.err" 2>&1) || exit 1
  done
  cat "$OUT"/raw_${run}_p*.jsonl > "$OUT/raw_${run}.jsonl"
  $PY "$CODE_DIR/label_reduce.py" --jobs "$OUT/pilot_jobs.jsonl" \
    --raw "$OUT/raw_${run}.jsonl" --out "$OUT/labels_${run}.jsonl" \
    --thin-out "$OUT/thin_${run}.jsonl" > "$OUT/reduce_${run}.json" || exit 1
}
run_labels a 555001
run_labels b 777001
$PY "$CODE_DIR/pilot_times.py" "$OUT" "$OUT/label_a.err" "$OUT/label_b.err" \
  || exit 1
$PY "$CODE_DIR/pilot_report.py" --out "$OUT" > "$OUT/pilot_report.txt" || exit 1

# --- teacher-root census (report-only) ---------------------------
rm -rf "$PROBE_TREE"
cp -r "$NATIVE" "$PROBE_TREE"
find "$PROBE_TREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
$PY "$CODE_DIR/patch_census_probe.py" "$PROBE_TREE" || exit 1
expect_hash "$PROBE_TREE/featurize.php" \
  b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a \
  "census-probe featurize (teacher-root census tree)"
cp "$CODE_DIR/featurize_snapshot.php" "$PROBE_TREE/"
(cd "$PROBE_TREE" && CENSUS_LOG="$OUT/root_census.jsonl" \
   FEAT_JOBS="$OUT/pilot_jobs.jsonl" FEAT_OUT="$OUT/root_census_states.jsonl" \
   php featurize_snapshot.php "$DECK" "$DECK" \
     --policy-search --games 1 > "$OUT/root_census.err" 2>&1) || exit 1
$PY "$CODE_DIR/tally_census.py" "$OUT/root_census.jsonl" \
  > "$OUT/root_census_tally.txt" || exit 1

touch "$OUT/shm_sweep.stop"
sleep 2
ipcs -m > "$OUT/ipcs_after.txt"
echo "PILOT COMPLETE - reads in $OUT/pilot_report.txt and" \
     "$OUT/root_census_tally.txt; the corpus gate is a human read" \
     "of those files plus Joe's go"
