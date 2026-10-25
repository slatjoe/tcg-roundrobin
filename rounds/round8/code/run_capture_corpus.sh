#!/bin/bash
# Round-8 CAPTURE stage - the distillation corpus's raw games
# (build-package sec.2; claude-reply-926f6c3 sec.1, Option B).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's approval of the round-8 build package
# at its committed sha, a passed pilot read, and Joe's go in chat
# (the corpus is round 8's second go-gate).
#
# What runs: plain v15 games through the driver's CAPTURE arm
# (paired_driver.py --arm capture: TEACHER_MODE=1 +
# TEACHER_CAPTURE=1; search.php snapshots every contested
# decision, plays the prior pick, never rolls out - the arm's own
# manifest asserts exactly that). The learner is v15 in both
# seats (one stream per seat); the opponent is the server-routed
# other seat:
#   heur   - the heuristic (server default)
#   bc3    - BC3 via TCG_OPP_MIX=ckptpath:<bc3>:1.0
#   mirror - v15 itself via TCG_OPP_MIX=ckptpath:<v15>:1.0
# The driver has no opponent flag by design - opponent identity
# is a server property (the O fleet's routing), set here.
#
# Seed plan (corpus range 10001-10400, 400 games, fresh and
# disjoint from every registered range):
#   heur   s1 10001-10080   s2 10081-10160    (160)
#   bc3    s1 10161-10220   s2 10221-10280    (120)
#   mirror s1 10281-10340   s2 10341-10400    (120)
#
# The corpus tree is built HERE from the native tree +
# patch_capture_uncontested.py (the uncontested-snapshot
# extension the T1 KL term needs; the two gate trees are never
# touched). Its featurize.php stays NATIVE: capture states are
# the gated teacher's states. The corrected featurization of
# every state happens later, offline, in the T1 data builder.
# The capture-patch product is ASSERTED at its known hash
# (044ca8ec..., verified on a throwaway copy at build time),
# not merely recorded.
#
# PILOT_CAPTURE=1 (the round-8 pilot's first phase, fix
# package): run ONLY the heur seat-1 stream restricted to seeds
# 10001-10020 - the pilot labels those games' contested states
# (V1). The full corpus run (no PILOT_CAPTURE) later re-runs all
# six streams including those 20 games; capture is deterministic
# at raw speed, so the re-run reproduces the same snapshots and
# overwrites the pilot subset's rows.
#
# Outputs under $OUT (default /home/joe/tcg/distill_corpus - the
# durable disk, NOT tmpfs: snapshots run ~260 KB each and the
# corpus holds tens of thousands; round 7's stage-1 /tmp fill is
# the standing lesson):
#   <matchup>_s<seat>.jsonl (+ .manifest.json)   driver rows
#   <matchup>_s<seat>_log/                       stats, traces,
#                                               snaps/ (+ index)
#   <matchup>_s<seat>_game_ids.txt              G9-style ids
#   corpus_manifest.json                        tree hashes,
#                                               counts, ids
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
NATIVE=${NATIVE_TREE:-/tmp/distilltree_native}
CTREE=${CORPUS_TREE:-/tmp/distilltree_corpus}
V15=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
BC3=$SIM/bc3_out/bc3_policy.pt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
OUT=${CORPUS_OUT:-/home/joe/tcg/distill_corpus}
DECK=$CTREE/decks/nats2026_ashlyn_fai_60.txt
mkdir -p "$OUT"

expect_hash() {
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
expect_hash "$NATIVE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "native featurize.php"
expect_hash "$V15" \
  0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"
expect_hash "$BC3" \
  78e2950c1628e8546d4a1faf7e335caebbdce3f1f1a9284a4377846018eb7bb9 "BC3"

# --- corpus tree -------------------------------------------------
rm -rf "$CTREE"
cp -r "$NATIVE" "$CTREE"
find "$CTREE" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
$PY "$CODE_DIR/patch_capture_uncontested.py" "$CTREE" || exit 1
expect_hash "$CTREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "corpus featurize.php (must stay native)"
expect_hash "$CTREE/search.php" \
  044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d \
  "corpus search.php (capture-patch product, asserted)"
CORPUS_SEARCH_SHA=$(sha256sum "$CTREE/search.php" | awk '{print $1}')
echo "corpus tree search.php (patched, asserted): $CORPUS_SEARCH_SHA"

SRV_PIDS=""
cleanup() { for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done; }
trap cleanup EXIT

run_stream() { # matchup seat seeds oppmix
  local matchup=$1 seat=$2 seeds=$3 oppmix=$4
  local sock="$OUT/cap_${matchup}_s${seat}.sock"
  local slog="$OUT/cap_${matchup}_s${seat}_server.log"
  TCG_POLICY_SOCK="$sock" TCG_LEARNER_SEAT="$seat" SEARCH_MODEL="$V15" \
    TCG_OPP_MIX="$oppmix" \
    setsid nohup $PY "$CTREE/rl/search_server.py" > "$slog" 2>&1 < /dev/null &
  local srvpid=$!
  SRV_PIDS="$SRV_PIDS $srvpid"
  local i
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$slog" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$slog" || {
    echo "ABORT: capture server ${matchup}/s${seat} did not load" >&2
    return 1; }
  local logdir="$OUT/${matchup}_s${seat}_log"
  TEACHER_CAPTURE_UNCONTESTED=1 TCG_CLEAN_CHILDREN=1 \
  GATE_GAME_IDS_FILE="$OUT/${matchup}_s${seat}_game_ids.txt" \
    $PY "$CTREE/paired_driver.py" --tree "$CTREE" --sock "$sock" \
      --seat "$seat" --arm capture --seeds "$seeds" --timeout 600 \
      --out "$OUT/${matchup}_s${seat}.jsonl" \
      --logdir "$logdir" --deck "$DECK" || return 1
  kill "$srvpid" 2>/dev/null
  # The capture arm's own manifest is the arm verification: it
  # asserts snapshot rows carry capture=1, pick == prior, no
  # rollout fields, and no rollouts anywhere in the arm.
  $PY - "$OUT/${matchup}_s${seat}.jsonl.manifest.json" <<'PYEOF' || return 1
import json, sys
m = json.load(open(sys.argv[1]))
assert m["assert_ok"] is True, f"capture manifest assert_ok != True: {m['checks']}"
print("capture manifest OK:", m["assertions"]["capture_rows"], "capture rows")
PYEOF
}

if [ "${PILOT_CAPTURE:-0}" = "1" ]; then
  run_stream heur 1 10001-10020 "heuristic:1.0" || exit 1
else
  run_stream heur   1 10001-10080 "heuristic:1.0" || exit 1
  run_stream heur   2 10081-10160 "heuristic:1.0" || exit 1
  run_stream bc3    1 10161-10220 "ckptpath:$BC3:1.0" || exit 1
  run_stream bc3    2 10221-10280 "ckptpath:$BC3:1.0" || exit 1
  run_stream mirror 1 10281-10340 "ckptpath:$V15:1.0" || exit 1
  run_stream mirror 2 10341-10400 "ckptpath:$V15:1.0" || exit 1
fi

$PY - "$OUT" "$CORPUS_SEARCH_SHA" "${PILOT_CAPTURE:-0}" <<'PYEOF'
import glob, json, sys
out, search_sha = sys.argv[1], sys.argv[2]
man = {"corpus_search_sha256": search_sha,
       "pilot_subset": sys.argv[3] == "1", "streams": {}}
tot_c = tot_u = 0
for idx in sorted(glob.glob(out + "/*_log/snaps/teacher_snap_index.jsonl")):
    stream = idx.split("/")[-3]
    rows = [json.loads(l) for l in open(idx) if l.strip()]
    c = sum(1 for r in rows if not r.get("uncontested"))
    u = sum(1 for r in rows if r.get("uncontested"))
    man["streams"][stream] = {"snapshots": len(rows),
                              "contested": c, "uncontested": u}
    tot_c += c; tot_u += u
man["totals"] = {"contested": tot_c, "uncontested": tot_u}
ids = []
for f in sorted(glob.glob(out + "/*_game_ids.txt")):
    ids += [l.strip() for l in open(f) if l.strip()]
man["game_ids_file_count"] = len(ids)
man["unique_game_ids"] = len(set(ids))
json.dump(man, open(out + "/corpus_manifest.json", "w"), indent=1)
print(json.dumps(man["totals"]), "games:", man["unique_game_ids"])
PYEOF
echo "CAPTURE COMPLETE - $OUT/corpus_manifest.json"
