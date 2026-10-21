#!/bin/bash
# gravy_corpus_driver.sh — round-7 STAGE 1: Gravy corpora generation.
#
# REVIEW-GATED: do not run until the round-7 build package is approved
# at its committed sha AND Joe gives the go in chat.
#
# The BC3 corpus recipe (design sec.4.1), regenerated fresh on the
# Gravy deck with the design's registered two-pass deviation:
#
#   batch 1 mirror_self : heuristic Gravy mirror, 6 workers x 400
#                         = 2,400 games (target ~920k records)
#   batch 2 cross_self  : heuristic Gravy (seat A) vs Fai (seat B),
#                         6 x 125 = 750 games (target ~284k records)
#   pass-1 clone        : bc_train.py (root v1-generation pair) on
#                         batches 1+2 only -> gravy_bc/pass1_out/
#                         bc_policy.pt. SCAFFOLDING: never gated,
#                         never the raw arm. (The generation server
#                         policy_server.py loads its driver through
#                         bc_train.BCPolicy + bc_features — the v1-
#                         generation pair — so the DAgger driver is a
#                         v1-format clone, exactly the role bc v1
#                         played for Fai. See build-package.md sec.3.)
#   batch 3 mirror_bc   : DAgger — pass-1 clone drives the Gravy
#                         mirror, heuristic (v1-argmax) labels,
#                         6 x 250 = 1,500 games (target ~563k records)
#
# Completion is read from per-batch game/record counts (games_w*.jsonl
# rows and traj_w*.jsonl lines), NEVER from a DONE file (Oct-15
# lesson). A batch whose game count is short aborts the driver.
set -u
SIM=/home/joe/tcg/tcg-sim
G60=$SIM/decks/nats2026_eriksen_gravy_60.txt
F60=$SIM/decks/nats2026_ashlyn_fai_60.txt
ROOT=$SIM/gravy_bc
DATA=$ROOT/data
PY=/home/joe/tcg/rl-env/bin/python
mkdir -p "$DATA"

count_games() { cat "$1"/games_w*.jsonl 2>/dev/null | wc -l; }
count_recs()  { cat "$1"/traj_w*.jsonl 2>/dev/null | wc -l; }

check_batch() {  # $1 = batch dir, $2 = expected games
  local g r
  g=$(count_games "$1"); r=$(count_recs "$1")
  echo "batch $1: games=$g (want $2) records=$r"
  [ "$g" -eq "$2" ] || { echo "ABORT: batch $1 short on games" >&2; exit 1; }
}

echo "=== batch 1 mirror_self $(date) ==="
bash "$SIM/bc2_gen.sh" 6 400 "$G60" "$G60" "$DATA/mirror_self"
check_batch "$DATA/mirror_self" 2400

echo "=== batch 2 cross_self $(date) ==="
bash "$SIM/bc2_gen.sh" 6 125 "$G60" "$F60" "$DATA/cross_self"
check_batch "$DATA/cross_self" 750

echo "=== pass-1 clone (v1 pair, scaffolding) $(date) ==="
mkdir -p "$ROOT/pass1_data"
ln -sfn "$DATA/mirror_self" "$ROOT/pass1_data/mirror_self"
ln -sfn "$DATA/cross_self"  "$ROOT/pass1_data/cross_self"
"$PY" "$SIM/bc_train.py" --data "$ROOT/pass1_data" \
  --out "$ROOT/pass1_out" > "$ROOT/pass1_train.log" 2>&1
[ -f "$ROOT/pass1_out/bc_policy.pt" ] || {
  echo "ABORT: pass-1 clone missing (see $ROOT/pass1_train.log)" >&2; exit 1; }
echo "pass-1 clone: $ROOT/pass1_out/bc_policy.pt"

echo "=== batch 3 mirror_bc (DAgger, pass-1 driven) $(date) ==="
# BCWHEELS left unset: worker copies take the sim-root bc_train.py +
# bc_features.py — the same pair that trained the pass-1 clone.
bash "$SIM/bc2_gen.sh" 6 250 "$G60" "$G60" "$DATA/mirror_bc" \
  "$ROOT/pass1_out/bc_policy.pt"
check_batch "$DATA/mirror_bc" 1500

echo "=== stage 1 corpus complete $(date) ==="
echo "total records: $(count_recs "$DATA/mirror_self") + "
echo "               $(count_recs "$DATA/cross_self") + "
echo "               $(count_recs "$DATA/mirror_bc")"
