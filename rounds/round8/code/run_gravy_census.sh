#!/bin/bash
# Round 5 item (b) CENSUS DIAGNOSTIC at the round-7 hero -
# Talishar Gravy Bones, mirror, 20 bridge games. Round-8 package
# sec.7 (the round-7 build package's registered census
# diagnostic, claude-reply-eb950c5 sec.2, carried into round 8 by
# claude-reply-926f6c3 sec.6 after the round-7 report missed it).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Script written for the record; runs on Joe's go as the round-8
# pre-step (it is report-only and independent of the pilot /
# corpus / gate go-gates).
#
# This is the round-5 census design replayed at the new hero:
# probe-patched scratch tree (census probe only - the store:=view
# sync ships in search.php and is NOT touched), featurization
# counted at every bridge featurization via GetDeck /
# SimV1_DeckCards. The bridge model is the hero-transfer arm's
# raw policy (gravy PPO v10, C4-selected - the model whose live
# play is being censused). NOT a transfer re-measurement: no
# teacher, no gate machinery, no verdict machinery attaches -
# the tally is reported with no registration on it (the reply's
# form). The 20 games are eval-only and are registered into the
# do-not-train registry afterward (merge_registry.py, tag
# gravy_census_diag_eval) - post-hoc registration of an
# instrument that was never training data, the round-5 census
# precedent.
#
# Guards: search.php == 6cd6f980... (the round-5 census build),
# patched featurize.php == b2fa1ffe... (the round-5 probe
# product), production server == 81ef2cdb... (the ruling's
# production-server condition). Seeds 8801-8810 (seat 1),
# 8811-8820 (seat 2) - fresh, disjoint from every registered
# range (pilot gate 7001-7200, gravy chunks 8001-8200, round-8
# gate 9001-9200, corpus 10001-10400, pre-gate 11001-11010).
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
SRC=${CENSUS_SRC_TREE:-/tmp/gatetree_r4}
TREE=/tmp/gravycensus
OUT=${GRAVY_CENSUS_OUT:-/tmp/gravy_census_diag}
MODEL=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
PROD=$SIM/rl/search_server.py
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
DECK=decks/nats2026_eriksen_gravy_60.txt
mkdir -p "$OUT/census"

expect_hash() {
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
expect_hash "$MODEL" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "gravy PPO v10 (bridge model)"
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"

rm -rf "$TREE"
cp -r "$SRC" "$TREE"
find "$TREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
$PY "$CODE_DIR/patch_census_probe.py" "$TREE" || exit 1
expect_hash "$TREE/search.php" \
  6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a \
  "census-tree search.php (the checkpoint sync ships here)"
expect_hash "$TREE/featurize.php" \
  b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a \
  "census-tree featurize.php (round-5 probe product)"

SRV_PIDS=""
cleanup() { for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done; }
trap cleanup EXIT

run_seat() { # seat seeds
  local seat=$1 seeds=$2 sock slog srvpid i
  sock="$OUT/census_s${seat}.sock"
  slog="$OUT/census_s${seat}_server.log"
  TCG_POLICY_SOCK="$sock" TCG_LEARNER_SEAT=$seat SEARCH_MODEL="$MODEL" \
    setsid nohup $PY "$PROD" > "$slog" 2>&1 < /dev/null &
  srvpid=$!
  SRV_PIDS="$SRV_PIDS $srvpid"
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$slog" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$slog" || {
    echo "ABORT: census server seat $seat did not load" >&2; return 1; }
  CENSUS_LOG="$OUT/census/census_s${seat}.log" \
  GATE_GAME_IDS_FILE="$OUT/census_game_ids_s${seat}.txt" \
    $PY "$TREE/paired_driver.py" --tree "$TREE" --sock "$sock" \
      --seat "$seat" --arm raw --seeds "$seeds" --timeout 300 \
      --deck "$TREE/$DECK" \
      --out "$OUT/census_s${seat}.jsonl" \
      --logdir "$OUT/census_s${seat}_log" || return 1
  kill "$srvpid" 2>/dev/null
}

run_seat 1 8801-8810 || exit 1
run_seat 2 8811-8820 || exit 1
$PY "$CODE_DIR/tally_census.py" \
  "$OUT/census/census_s1.log" "$OUT/census/census_s2.log" \
  > "$OUT/tally.txt" || exit 1
cat "$OUT/tally.txt"
echo "CENSUS DIAGNOSTIC COMPLETE - register the 20 games with:"
echo "  merge_registry.py --tag gravy_census_diag_eval \\"
echo "    --ids $OUT/census_game_ids_s1.txt --ids $OUT/census_game_ids_s2.txt"
