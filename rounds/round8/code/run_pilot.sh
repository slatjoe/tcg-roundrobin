#!/bin/bash
# Round-8 PILOT - the label-validity + cost pilot, as corrected
# by claude-reply-a076148 sec.3-4 (fix package).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on the reviewer's approval of this fix package at
# its committed sha AND Joe's go in chat (the pilot is the first
# of round 8's go-gates; the corpus stays gated on the reviewer's
# read of the pilot's numbers).
#
# Phases, in order:
#   0. Guards: native-tree pins (incl. r3_pair.py), production
#      server pin, v15 pin, deployed code present.
#   1. Containment: pre-launch G8 sweep, then the (C) sweeper
#      alongside the label work, pointed at the native tree's
#      Games dir (teacher/label roots run there - the round-7
#      L-run conditions).
#   2. PILOT CAPTURE: run_capture_corpus.sh with PILOT_CAPTURE=1
#      captures the first 20 corpus games (seeds 10001-10020,
#      heur seat 1) into the corpus dir. These games ARE the
#      corpus's first 20; the full corpus run later re-runs all
#      400. The full 400-game corpus does NOT run in the pilot.
#   3. CAPTURE EQUIVALENCE CHECK (reply sec.4.2): the corpus
#      tree's capture arm (with the uncontested patch active)
#      vs raw v15 on the native tree, 10 seeds per seat
#      (12001-12010, fresh) vs the heuristic, compared through
#      r3_pair.py with the round-7 strict parser
#      (parse_r3_pair.py): both seats must read IDENTICAL. A
#      parse failure STOPS the pilot - it would mean capture +
#      the patch changes play, so the corpus is not v15's state
#      distribution.
#   4. Jobs: pilot_prep.py v1 (every contested state of the 20
#      capture games, ~540) and v2 (100 gate-fleet overturn
#      snapshots from the PRESERVED copy on durable disk,
#      stratified across the 8 streams).
#   5. Labels: production servers (v15, both seats). V1 states
#      labeled TWICE (run A DISTILL_SEED 555001, run B 777001);
#      V2 states once (555001). All runs in DISTILL_SPLIT_CANDS
#      mode (per-candidate batches, same world seeds - the
#      deadline accounting's instrument). Runs split by root
#      player against that seat's server; ONE label process in
#      the native tree at a time.
#   6. Reads: pilot_times.py aggregates the per-candidate
#      timings; pilot_report.py prints COST (mean/p95/max over
#      the ~1,200 jobs + the corpus estimate computed from
#      them), V1-ov, V1-conf, V2, the V2-vs-V1-ov test, the
#      mechanism z-scores, the deadline accounting, thin counts.
#   7. Teacher-root census (report-only): the census-probe tree
#      featurizes the pilot's label roots (V1 + V2 job roots)
#      with CENSUS_LOG set; tally_census.py tallies. Parsed-root
#      caveat as registered (build-package sec.3).
# Nothing here passes or fails itself, except the phase-3
# equivalence check, which stops the pilot on failure. The
# report goes to Claude and Joe; the corpus runs only after
# Claude's pilot review and Joe's go.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
NATIVE=${NATIVE_TREE:-/tmp/distilltree_native}
CTREE=${CORPUS_TREE:-/tmp/distilltree_corpus}
PROBE_TREE=${PROBE_TREE:-/tmp/distilltree_censusprobe}
PROD=$SIM/rl/search_server.py
MODEL=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
DECK=$NATIVE/decks/nats2026_ashlyn_fai_60.txt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
CORPUS=${CORPUS_OUT:-/home/joe/tcg/distill_corpus}
PRESERVE=${V2_PRESERVE:-/home/joe/tcg/gate_r4_v2_preserve}
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
expect_hash "$NATIVE/r3_pair.py" \
  13f95ebe09fbbe5d8cd123c7aca4642c4944de03af2c9e847f689660e96869da \
  "native r3_pair.py"
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$MODEL" \
  0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"
for f in distill_label_main.php featurize_snapshot.php \
         label_reduce.py pilot_prep.py pilot_report.py \
         pilot_times.py run_capture_corpus.sh \
         patch_capture_uncontested.py patch_census_probe.py \
         tally_census.py parse_r3_pair.py shm_sweep.py \
         g8_sweep.sh; do
  [ -f "$CODE_DIR/$f" ] || { echo "ABORT: $CODE_DIR/$f missing" >&2; exit 1; }
done
sha256sum "$CODE_DIR"/* > "$OUT/deployed_code_hashes.txt"

# Deploy the labeler + featurizer into the native tree root (the
# label mains' bootstrap pattern: tools live at the tree root).
cp "$CODE_DIR/distill_label_main.php" "$NATIVE/"
cp "$CODE_DIR/featurize_snapshot.php" "$NATIVE/"

SRV_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  touch "$OUT/shm_sweep.stop" 2>/dev/null
}
trap cleanup EXIT

# --- phase 1: containment ---------------------------------------
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
SRV_PIDS="$SRV_PIDS $SWEEP_PID"

# --- phase 2: pilot capture (first 20 corpus games) -------------
PILOT_CAPTURE=1 CORPUS_OUT="$CORPUS" CODE_DIR="$CODE_DIR" \
  NATIVE_TREE="$NATIVE" CORPUS_TREE="$CTREE" \
  bash "$CODE_DIR/run_capture_corpus.sh" \
  > "$OUT/pilot_capture.log" 2>&1 || {
    echo "PILOT STOP: pilot capture failed - $OUT/pilot_capture.log" >&2
    exit 1; }
expect_hash "$CTREE/search.php" \
  044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d \
  "corpus search.php (capture-patch product)"

# --- phase 3: capture equivalence check ---------------------------
start_tree_server() { # seat sock log
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
    setsid nohup $PY "$NATIVE/rl/search_server.py" \
    > "$3" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
  local i
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$3" 2>/dev/null && return 0
    sleep 1
  done
  echo "ABORT: native tree server (seat $1) did not load" >&2
  return 1
}
for seat in 1 2; do
  start_tree_server $seat "$OUT/equiv_s${seat}.sock" \
    "$OUT/equiv_s${seat}_server.log" || exit 1
  TEACHER_CAPTURE_UNCONTESTED=1 TCG_CLEAN_CHILDREN=1 \
  GATE_GAME_IDS_FILE="$OUT/equiv_cap_s${seat}_game_ids.txt" \
    $PY "$CTREE/paired_driver.py" --tree "$CTREE" \
      --sock "$OUT/equiv_s${seat}.sock" --seat $seat --arm capture \
      --seeds 12001-12010 --timeout 300 --deck "$DECK" \
      --out "$OUT/equiv_cap_s${seat}.jsonl" \
      --logdir "$OUT/equiv_cap_s${seat}_log" || exit 1
  GATE_GAME_IDS_FILE="$OUT/equiv_raw_s${seat}_game_ids.txt" \
    $PY "$NATIVE/paired_driver.py" --tree "$NATIVE" \
      --sock "$OUT/equiv_s${seat}.sock" --seat $seat --arm raw \
      --seeds 12001-12010 --timeout 300 --deck "$DECK" \
      --out "$OUT/equiv_raw_s${seat}.jsonl" \
      --logdir "$OUT/equiv_raw_s${seat}_log" || exit 1
  (cd "$NATIVE" && $PY r3_pair.py \
     raw="$OUT/equiv_cap_s${seat}.jsonl,$OUT/equiv_cap_s${seat}_log" \
     raw="$OUT/equiv_raw_s${seat}.jsonl,$OUT/equiv_raw_s${seat}_log" \
     > "$OUT/equiv_pair_s${seat}.txt" 2>&1)
  if ! $PY "$CODE_DIR/parse_r3_pair.py" --expect-rows 10 \
       "$OUT/equiv_pair_s${seat}.txt" \
       > "$OUT/equiv_pair_s${seat}.parse.txt" 2>&1; then
    echo "PILOT STOP: capture equivalence FAILED seat $seat -" \
         "see $OUT/equiv_pair_s${seat}.parse.txt" >&2
    exit 1
  fi
  echo "capture equivalence seat $seat: IDENTICAL (strict parse)"
done

# --- phase 4: jobs --------------------------------------------------
$PY "$CODE_DIR/pilot_prep.py" --mode v1 --corpus "$CORPUS" \
  --out "$OUT" || exit 1
$PY "$CODE_DIR/pilot_prep.py" --mode v2 --preserve "$PRESERVE" \
  --out "$OUT" || exit 1

# --- phase 5: label runs ---------------------------------------------
start_prod_server() { # seat sock log
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
    setsid nohup $PY "$PROD" > "$3" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
  local i
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

run_labels() { # tag jobs seed
  local tag=$1 jobs=$2 seed=$3 p sock
  : > "$OUT/label_${tag}.err"
  rm -f "$OUT/timings_${tag}.jsonl"
  for p in 1 2; do
    split_jobs "$jobs" "$p" "$OUT/jobs_${tag}_p$p.jsonl" || exit 1
    : > "$OUT/raw_${tag}_p$p.jsonl"
    sock="$OUT/prod_s$p.sock"
    (cd "$NATIVE" && DISTILL_JOBS="$OUT/jobs_${tag}_p$p.jsonl" \
       DISTILL_OUT="$OUT/raw_${tag}_p$p.jsonl" DISTILL_SEED="$seed" \
       DISTILL_SPLIT_CANDS=1 \
       DISTILL_TIMINGS="$OUT/timings_${tag}.jsonl" \
       TCG_POLICY_SOCK="$sock" \
       php distill_label_main.php "$DECK" "$DECK" \
         --policy-search --games 1 >> "$OUT/label_${tag}.err" 2>&1) \
      || exit 1
  done
  cat "$OUT"/raw_${tag}_p*.jsonl > "$OUT/raw_${tag}.jsonl"
  $PY "$CODE_DIR/label_reduce.py" --jobs "$jobs" \
    --raw "$OUT/raw_${tag}.jsonl" --out "$OUT/labels_${tag}.jsonl" \
    --thin-out "$OUT/thin_${tag}.jsonl" \
    > "$OUT/reduce_${tag}.json" || exit 1
}
run_labels v1a "$OUT/v1_jobs.jsonl" 555001
run_labels v1b "$OUT/v1_jobs.jsonl" 777001
run_labels v2  "$OUT/v2_jobs.jsonl" 555001

# --- phase 6: reads ---------------------------------------------------
$PY "$CODE_DIR/pilot_times.py" "$OUT" \
  "v1a=$OUT/timings_v1a.jsonl" "v1b=$OUT/timings_v1b.jsonl" \
  "v2=$OUT/timings_v2.jsonl" || exit 1
$PY "$CODE_DIR/pilot_report.py" --out "$OUT" \
  > "$OUT/pilot_report.txt" || exit 1

# --- phase 7: teacher-root census (report-only) -----------------------
cat "$OUT/v1_jobs.jsonl" "$OUT/v2_jobs.jsonl" > "$OUT/census_jobs.jsonl"
rm -rf "$PROBE_TREE"
cp -r "$NATIVE" "$PROBE_TREE"
find "$PROBE_TREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
$PY "$CODE_DIR/patch_census_probe.py" "$PROBE_TREE" || exit 1
expect_hash "$PROBE_TREE/featurize.php" \
  b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a \
  "census-probe featurize (teacher-root census tree)"
cp "$CODE_DIR/featurize_snapshot.php" "$PROBE_TREE/"
(cd "$PROBE_TREE" && CENSUS_LOG="$OUT/root_census.jsonl" \
   FEAT_JOBS="$OUT/census_jobs.jsonl" \
   FEAT_OUT="$OUT/root_census_states.jsonl" \
   php featurize_snapshot.php "$DECK" "$DECK" \
     --policy-search --games 1 > "$OUT/root_census.err" 2>&1) || exit 1
$PY "$CODE_DIR/tally_census.py" "$OUT/root_census.jsonl" \
  > "$OUT/root_census_tally.txt" || exit 1

touch "$OUT/shm_sweep.stop"
sleep 2
ipcs -m > "$OUT/ipcs_after.txt"
echo "PILOT COMPLETE - reads in $OUT/pilot_report.txt and" \
     "$OUT/root_census_tally.txt; the corpus is gated on the" \
     "reviewer's read of the pilot plus Joe's go"
