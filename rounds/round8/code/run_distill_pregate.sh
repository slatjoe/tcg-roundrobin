#!/bin/bash
# Round-8 PRE-GATE for the distillation gate (build-package
# sec.5): per-tree determinism (the review's D2 control),
# fallbacks = 0, and the report-only FEATURIZER-ONLY CONTROL
# (claude-reply-926f6c3 sec.5(3)): v15 raw on the corrected tree
# vs v15 raw on the native tree, paired on the pre-gate seeds.
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's approval of the round-8 build package
# at its committed sha and Joe's go for the gate stage (after the
# T1 checkpoint exists - the corrected tree's serving is what this
# pre-gate certifies alongside the native tree's).
#
# Shape (the round-7 pre-gate pattern, two trees):
#   * per tree: hash pins asserted at start (search.php, the
#     tree's featurize.php, the tree server, the driver, the
#     deck, v15);
#   * per tree: the raw arm (v15, both seats, seeds 11001-11010,
#     vs heuristic) run TWICE -> determinism read from the
#     driver's own rows by pregate_compare.py (never eyeballed);
#   * fallbacks = 0 verified from server logs AND driver rows
#     (connect_failed = 0);
#   * the seat-crossed control (R16 form) is read by the compare
#     script from the same rows.
# Pre-gate seeds 11001-11010 are fresh and disjoint from every
# registered range and from the gate (9001-9200) and corpus
# (10001-10400) ranges.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
V15=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
OUT=${PREGATE_OUT:-/tmp/distill_pregate}
mkdir -p "$OUT"
SRV_PIDS=""
cleanup() { for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done; }
trap cleanup EXIT

expect_hash() {
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
tree_pins() { # tree featurize_sha label
  expect_hash "$1/search.php" \
    6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a \
    "$3 search.php"
  expect_hash "$1/featurize.php" "$2" "$3 featurize.php"
  expect_hash "$1/rl/search_server.py" \
    ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c \
    "$3 tree server"
  expect_hash "$1/paired_driver.py" \
    1e312629c9ebe30e97e0480c1f9d5530e82eba3c1a9511b3a929bc6f2d92471d \
    "$3 paired_driver.py"
  expect_hash "$V15" \
    0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"
}
NATIVE=/tmp/distilltree_native
CORR=/tmp/distilltree_corrected
tree_pins "$NATIVE" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 native
tree_pins "$CORR" \
  3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a corrected

run_tree() { # tree tag runno
  local tree=$1 tag=$2 runno=$3 seat sock slog srvpid i
  for seat in 1 2; do
    sock="$OUT/${tag}_s${seat}.sock"
    slog="$OUT/${tag}_s${seat}_server.log"
    TCG_POLICY_SOCK="$sock" TCG_LEARNER_SEAT=$seat SEARCH_MODEL="$V15" \
      setsid nohup $PY "$tree/rl/search_server.py" \
      > "$slog" 2>&1 < /dev/null &
    srvpid=$!
    SRV_PIDS="$SRV_PIDS $srvpid"
    for i in $(seq 1 30); do
      grep -q 'search model loaded' "$slog" 2>/dev/null && break
      sleep 1
    done
    grep -q 'search model loaded' "$slog" || {
      echo "ABORT: $tag seat $seat server did not load" >&2; return 1; }
    GATE_GAME_IDS_FILE="$OUT/${tag}_r${runno}_s${seat}_game_ids.txt" \
      $PY "$tree/paired_driver.py" --tree "$tree" --sock "$sock" \
        --seat "$seat" --arm raw --seeds 11001-11010 --timeout 300 \
        --deck "$tree/decks/nats2026_ashlyn_fai_60.txt" \
        --out "$OUT/${tag}_r${runno}_s${seat}.jsonl" \
        --logdir "$OUT/${tag}_r${runno}_s${seat}_log" || return 1
    kill "$srvpid" 2>/dev/null
  done
  cat "$OUT/${tag}_r${runno}_s1.jsonl" "$OUT/${tag}_r${runno}_s2.jsonl" \
    > "$OUT/${tag}_r${runno}.jsonl"
  grep -c 'fallback' "$OUT/${tag}_s1_server.log" "$OUT/${tag}_s2_server.log" \
    > "$OUT/${tag}_r${runno}_fallback_counts.txt" || true
}

ipcs -m > "$OUT/ipcs_before.txt"
run_tree "$NATIVE" native 1 || exit 1
run_tree "$NATIVE" native 2 || exit 1
run_tree "$CORR" corr 1 || exit 1
run_tree "$CORR" corr 2 || exit 1
$PY "$CODE_DIR/pregate_compare.py" \
  --native-run1 "$OUT/native_r1.jsonl" --native-run2 "$OUT/native_r2.jsonl" \
  --corr-run1 "$OUT/corr_r1.jsonl" --corr-run2 "$OUT/corr_r2.jsonl" \
  --out "$OUT/pregate_report.json" || exit 1
echo "PRE-GATE COMPLETE - $OUT/pregate_report.json"
echo "fallbacks (must total 0) + driver connect_failed rows: verify in"
echo "  $OUT/*_fallback_counts.txt and the manifests before the gate."
