#!/bin/bash
# Round-8 LABEL stage - label the corpus's contested snapshots
# with the offline labeler (build-package sec.2;
# claude-reply-926f6c3 sec.1).
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's approval of the round-8 build package
# at its committed sha, a passed pilot read, and Joe's go for the
# corpus (the go covers capture + label as one corpus stage).
#
# Shape:
#   * Jobs are built from the capture streams' snap indexes -
#     CONTESTED rows only (uncontested snapshots feed the T1 KL
#     term directly and are never labeled).
#   * The labeler runs in NATIVE-tree copies (featurize
#     f81193e0... - the gated teacher's own featurization) against
#     the PRODUCTION server (81ef2cdb...; the label path's eval
#     requests are rejected by the patched tree server, R12).
#   * ONE label process per tree (SimLabel_RunForSnapshot wipes
#     the fixed Games/label_scratch/): jobs are sharded across
#     4 tree copies run in parallel, each copy hash-asserted.
#     Within a copy, jobs run in two sequential groups by root
#     player, each against that seat's production server.
#   * Containment: pre-launch G8 sweep, then one (C)
#     kernel-attribution sweeper per label tree for the run.
#   * World seeds: DISTILL_SEED 999001 + shard * 1000003; the
#     seed base of every job is recorded on its raw rows (labels
#     join back to them by snap for provenance).
# Outputs in $OUT: jobs.jsonl, raw_shard*.jsonl, labels.jsonl,
# thin.jsonl, label_manifest.json (counts + hashes).
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
NATIVE=${NATIVE_TREE:-/tmp/distilltree_native}
PROD=$SIM/rl/search_server.py
V15=$SIM/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round8_code}
CORPUS=${CORPUS_OUT:-/home/joe/tcg/distill_corpus}
OUT=${LABEL_OUT:-/home/joe/tcg/distill_corpus/labels}
NSHARD=4
mkdir -p "$OUT"

expect_hash() {
  local got
  got=$(sha256sum "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || { echo "ABORT: $3 hash $got != $2" >&2; exit 1; }
}
expect_hash "$NATIVE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "native featurize.php"
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$V15" \
  0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c "v15"

# --- jobs ---------------------------------------------------------
$PY - "$CORPUS" "$OUT" <<'PYEOF' || exit 1
import glob, json, sys
corpus, out = sys.argv[1], sys.argv[2]
jobs = []
for idx in sorted(glob.glob(corpus + "/*_log/snaps/teacher_snap_index.jsonl")):
    snaps_dir = idx.rsplit("/", 1)[0]
    for ln in open(idx):
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("uncontested"):
            continue
        jobs.append({"snap_dir": snaps_dir + "/" + r["snap"],
                     "snap": r["snap"], "game": r["game"],
                     "player": r["player"], "branch": r["branch"],
                     "turn": r["turn"], "cands": r["cands"],
                     "selected": r["selected"],
                     "prior_pick": r["prior_pick"]})
with open(out + "/jobs.jsonl", "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")
print(f"label jobs (contested snapshots): {len(jobs)}")
PYEOF

# --- containment ----------------------------------------------------
bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1

# --- production servers (one per seat) ------------------------------
SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$V15" \
    setsid nohup $PY "$PROD" > "$OUT/prod_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 30); do
    grep -q 'search model loaded' "$OUT/prod_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat did not load" >&2; exit 1; }
done

# --- shards ---------------------------------------------------------
for s in 0 1 2 3; do
  $PY - "$OUT" "$s" "$NSHARD" <<'PYEOF'
import json, sys
out, s, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
jobs = [json.loads(l) for l in open(out + "/jobs.jsonl") if l.strip()]
mine = [j for i, j in enumerate(jobs) if i % n == s]
with open(f"{out}/jobs_shard{s}.jsonl", "w") as f:
    for j in mine:
        f.write(json.dumps(j) + "\n")
print(f"shard {s}: {len(mine)} jobs")
PYEOF
done

run_shard() { # shard
  local s=$1
  local tree="/tmp/distilltree_label$s"
  rm -rf "$tree"
  cp -r "$NATIVE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cp "$CODE_DIR/distill_label_main.php" "$tree/"
  expect_hash "$tree/featurize.php" \
    f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
    "label tree $s featurize.php" || return 1
  ipcs -m > "$OUT/ipcs_shard$s.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_shard$s.txt" > "$OUT/shm_start$s.txt"
  rm -f "$OUT/shm_sweep$s.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep$s.log" \
    --start-file "$OUT/shm_start$s.txt" \
    --games-dir "$tree/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep$s.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
  local p
  for p in 1 2; do
    $PY - "$OUT" "$s" "$p" <<'PYEOF'
import json, sys
out, s, p = sys.argv[1], sys.argv[2], int(sys.argv[3])
jobs = [json.loads(l) for l in open(f"{out}/jobs_shard{s}.jsonl") if l.strip()]
sel = [j for j in jobs if int(j["player"]) == p]
with open(f"{out}/jobs_shard{s}_p{p}.jsonl", "w") as f:
    for j in sel:
        f.write(json.dumps(j) + "\n")
print(f"shard {s} player {p}: {len(sel)}")
PYEOF
    : > "$OUT/raw_shard${s}_p$p.jsonl"
    (cd "$tree" && DISTILL_JOBS="$OUT/jobs_shard${s}_p$p.jsonl" \
       DISTILL_OUT="$OUT/raw_shard${s}_p$p.jsonl" \
       DISTILL_SEED=$((999001 + s * 1000003)) \
       TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
       php distill_label_main.php \
         "$tree/decks/nats2026_ashlyn_fai_60.txt" \
         "$tree/decks/nats2026_ashlyn_fai_60.txt" \
         --policy-search --games 1 \
         > "$OUT/label_shard${s}_p$p.err" 2>&1) || return 1
  done
  touch "$OUT/shm_sweep$s.stop"
}
PIDS=""
for s in 0 1 2 3; do run_shard "$s" & PIDS="$PIDS $!"; done
FAIL=0
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a label shard failed" >&2; exit 1; }

cat "$OUT"/raw_shard*_p*.jsonl > "$OUT/raw_all.jsonl"
$PY "$CODE_DIR/label_reduce.py" --jobs "$OUT/jobs.jsonl" \
  --raw "$OUT/raw_all.jsonl" --out "$OUT/labels.jsonl" \
  --thin-out "$OUT/thin.jsonl" > "$OUT/reduce_counts.json" || exit 1
$PY - "$OUT" <<'PYEOF'
import hashlib, json, sys
out = sys.argv[1]
h = hashlib.sha256(open(out + "/labels.jsonl", "rb").read()).hexdigest()
man = {"labels_sha256": h,
       "labels": sum(1 for _ in open(out + "/labels.jsonl")),
       "thin": sum(1 for _ in open(out + "/thin.jsonl")),
       "reduce_counts": json.load(open(out + "/reduce_counts.json"))}
json.dump(man, open(out + "/label_manifest.json", "w"), indent=1)
print(json.dumps(man))
PYEOF
echo "LABEL STAGE COMPLETE - $OUT/label_manifest.json"
