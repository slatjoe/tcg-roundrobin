#!/bin/bash
# Round-9 Stage 0 - L3 on the round-7 fleet's 118 overturn decisions
# (design sec.3, as approved with additions in
# claude-reply-8dddf38), plus the D7 horizon co-report pass.
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage-0 package at
# its committed sha and Joe's explicit go for Stage 0.
#
# Shape:
#   * Population: the vaulted fleet L3 jobs (118 jobs, 88 games) -
#     no games are played and the registry is untouched; label
#     worlds are fresh seeds in the 855001 family.
#   * PRIMARY pass: the registered instrument, byte for byte -
#     meas_label_main.php (3109176b...) in a per-shard copy of the
#     fleet tree (search.php 8f6b35da...), LABEL_W=50, pair "va",
#     seed bases 855001 + shard x 10^8, against the PRODUCTION
#     server (81ef2cdb...) serving ckpt_v10.pt, one server per
#     seat (the label path's eval is per root-player seat).
#   * HORIZON pass (D7 co-report): the same 118 jobs in a per-shard
#     horizon tree - search.php carrying ONLY the run-pinned
#     horizon block (code/search_horizon.php, diff in the package
#     fixtures) - driven by r9_label_main.php with LABEL_HORIZON=62
#     pinned and every job stamped "horizon": 62. A world still
#     running at absolute currentTurn >= 62 ends finished, as a
#     draw - the score the game instrument itself assigns. Fresh
#     worlds: seed bases 875001 + shard x 10^8.
#   * Sharding: 4 shards by game (shard = sha256(game) mod 4), so
#     a game's jobs share a shard file; within a shard, jobs run
#     in two sequential groups by root player against that seat's
#     server. ji (the per-job seed index) is the index within the
#     group file the labeler is given, as in rounds 3/6/8.
#   * Job copies: the vaulted file is never modified. Shard copies
#     rewrite snap_dir to the absolute fleet snapshot root
#     ($SNAP_ROOT/<rel>) - a prefix substitution on copies,
#     asserted per job (the directory must exist).
#   * Scoring: analyze_l3_deploy.py (the O3 copy: stock scorer,
#     DELTA = 0.0075, TEACHER_GAMES = 400) on each pass, then
#     stage0_report.py for the (D) reporting (unfinished shares,
#     paired-n distribution, draw sensitivity, the registered
#     instrument-limited condition), cross-checked against the
#     scorer's standalone output.
#   * Containment: pre-launch G8 sweep, then one (C)
#     kernel-attribution sweeper per label tree, as in round 8.
# Outputs in $OUT: shard job files, per-group label files,
# labels_{primary,horizon}.jsonl, score_*_stdout.txt,
# report_{primary,horizon}.{txt,json}, deployed_code_hashes.txt,
# stage0_manifest.json.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
OUT=${STAGE0_OUT:-/tmp/r9s0_out}
GTREE=${GTREE_SRC:-/tmp/gravytree}
SNAP_ROOT=${SNAP_ROOT:-/tmp/ggate}
JOBS_SRC=/home/joe/tcg/registry-vault/jobs_all_gravy_fleet_l3.jsonl
PROD=$SIM/rl/search_server.py
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
HORIZON=62
NSHARD=4
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
expect_hash "$JOBS_SRC" \
  5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b \
  "vaulted L3 jobs file"
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$CKPT" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "Gravy ckpt_v10"
expect_hash "$CODE_DIR/meas_label_main.php" \
  3109176bb7137bc89b0645b8185f83c5722268c03028ca692642699cf7730b33 \
  "meas_label_main.php (registered labeler)"
expect_hash "$CODE_DIR/r9_label_main.php" \
  2463fc29c5333839971a0b22244b3b642d9ff68994f8942214d15b8eb6ca76a1 \
  "r9_label_main.php (horizon driver)"
expect_hash "$CODE_DIR/search_horizon.php" \
  6d63f5c37be840324bc847a454157a2688677354e952886980e4601f023d04a7 \
  "search_horizon.php (D7 horizon tree build)"
expect_hash "$CODE_DIR/analyze_l3_deploy.py" \
  3919bbb80db29eec91c87e6f640e6eb689fa8324865fb450a69292843008dd72 \
  "analyze_l3_deploy.py (O3 scorer)"
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "stage0_report.py ((D) reporting)"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$GTREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
  "fleet tree search.php"
expect_hash "$GTREE/featurize.php" \
  f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
  "fleet tree featurize.php"
expect_hash "$GTREE/play_game.php" \
  4ac2d62ddf64c8e8b6dfb64fac59beb639cb697026aaeb4b968fd91aa707f1d8 \
  "fleet tree play_game.php"
expect_hash "$GTREE/vendor/talishar/ParseGamestate.php" \
  0e88dd584c5c1e4df5ca491d16d5a8c742f85f34efad52b3e51a547cc6acb782 \
  "fleet tree ParseGamestate.php"
expect_hash "$GTREE/meas_label_main.php" \
  3109176bb7137bc89b0645b8185f83c5722268c03028ca692642699cf7730b33 \
  "fleet tree meas_label_main.php"
expect_hash "$GTREE/$DECK_REL" \
  b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed \
  "fleet tree Gravy deck"
{
  echo "jobs_src $JOBS_SRC 5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b"
  echo "prod_server $PROD 81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4"
  echo "ckpt_v10 $CKPT 44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3"
  sha256sum "$CODE_DIR"/*.php "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
} > "$OUT/deployed_code_hashes.txt"

# --- shard job files (copies; vaulted original untouched) -------
$PY - "$JOBS_SRC" "$OUT" "$SNAP_ROOT" "$NSHARD" "$HORIZON" <<'PYEOF' || exit 1
import hashlib, json, os, sys
src, out, snap_root, nshard, horizon = (sys.argv[1], sys.argv[2],
                                        sys.argv[3], int(sys.argv[4]),
                                        int(sys.argv[5]))
jobs = [json.loads(l) for l in open(src) if l.strip()]
assert len(jobs) == 118, f"expected 118 jobs, got {len(jobs)}"
shards = {s: [] for s in range(nshard)}
for j in jobs:
    s = int(hashlib.sha256(str(j["game"]).encode()).hexdigest(), 16) % nshard
    shards[s].append(j)

def emit(path, rows, stamp_horizon):
    with open(path, "w") as f:
        for j in rows:
            c = dict(j)
            c["snap_dir"] = snap_root + "/" + j["snap_dir"]
            assert os.path.isdir(c["snap_dir"]), \
                f"snap dir missing: {c['snap_dir']}"
            if stamp_horizon is not None:
                c["horizon"] = stamp_horizon
            f.write(json.dumps(c) + "\n")

for s, rows in shards.items():
    emit(f"{out}/jobs_shard{s}.jsonl", rows, None)
    emit(f"{out}/jobs_h_shard{s}.jsonl", rows, horizon)
    print(f"shard {s}: {len(rows)} jobs")
emit(out + "/jobs_all.jsonl", jobs, None)
emit(out + "/jobs_all_h.jsonl", jobs, horizon)
print(f"total {len(jobs)} jobs; snap dirs asserted present")
PYEOF

# --- containment: G8 pre-launch sweep -----------------------------
bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1

# --- production servers (one per seat) ----------------------------
SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$PROD" > "$OUT/prod_s${seat}.log" 2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 60); do
    grep -q 'search model loaded' "$OUT/prod_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat did not load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat loaded the wrong model" >&2; exit 1; }
done

# --- one pass (tag p = primary, h = horizon) ----------------------
run_pass() { # tag driver seedbase horizon_env
  local tag=$1 driver=$2 seedbase=$3 hz_env=$4
  local s p tree
  for s in 0 1 2 3; do
    tree="/tmp/r9s0_tree_${tag}$s"
    rm -rf "$tree"
    cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    if [ "$tag" = "h" ]; then
      cp "$CODE_DIR/search_horizon.php" "$tree/search.php"
      cp "$CODE_DIR/r9_label_main.php" "$tree/"
      expect_hash "$tree/search.php" \
        6d63f5c37be840324bc847a454157a2688677354e952886980e4601f023d04a7 \
        "horizon tree $s search.php" || return 1
    else
      cp "$CODE_DIR/meas_label_main.php" "$tree/"
      expect_hash "$tree/search.php" \
        8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61 \
        "primary tree $s search.php" || return 1
    fi
    expect_hash "$tree/featurize.php" \
      f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
      "tree $tag$s featurize.php" || return 1
    ipcs -m > "$OUT/ipcs_${tag}_shard$s.txt"
    awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_${tag}_shard$s.txt" \
      > "$OUT/shm_start_${tag}$s.txt"
    rm -f "$OUT/shm_sweep_${tag}$s.stop"
    $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_${tag}$s.log" \
      --start-file "$OUT/shm_start_${tag}$s.txt" \
      --games-dir "$tree/vendor/talishar/Games" \
      --interval 60 --stop-file "$OUT/shm_sweep_${tag}$s.stop" &
    SWEEP_PIDS="$SWEEP_PIDS $!"
  done
  local PIDS="" FAIL=0 pid
  for s in 0 1 2 3; do
    (
      tree="/tmp/r9s0_tree_${tag}$s"
      jf="$OUT/jobs_shard$s.jsonl"
      [ "$tag" = "h" ] && jf="$OUT/jobs_h_shard$s.jsonl"
      for p in 1 2; do
        $PY - "$OUT" "$tag" "$s" "$p" "$jf" <<'PYEOF'
import json, sys
out, tag, s, p, jf = sys.argv[1], sys.argv[2], sys.argv[3], \
    int(sys.argv[4]), sys.argv[5]
jobs = [json.loads(l) for l in open(jf) if l.strip()]
sel = [j for j in jobs if int(j["player"]) == p]
with open(f"{out}/jobs_{tag}_shard{s}_p{p}.jsonl", "w") as f:
    for j in sel:
        f.write(json.dumps(j) + "\n")
print(f"pass {tag} shard {s} player {p}: {len(sel)} jobs")
PYEOF
        : > "$OUT/labels_${tag}_shard${s}_p$p.jsonl"
        (cd "$tree" && MEAS_JOBS="$OUT/jobs_${tag}_shard${s}_p$p.jsonl" \
           MEAS_OUT="$OUT/labels_${tag}_shard${s}_p$p.jsonl" \
           MEAS_SEED=$((seedbase + s * 100000000)) \
           LABEL_W=50 LABEL_HORIZON="$hz_env" \
           TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
           php "$driver" \
             "$tree/$DECK_REL" "$tree/$DECK_REL" \
             --policy-search --games 1 \
             > "$OUT/label_${tag}_shard${s}_p$p.err" 2>&1) || exit 1
      done
      touch "$OUT/shm_sweep_${tag}$s.stop"
    ) &
    PIDS="$PIDS $!"
  done
  for pid in $PIDS; do wait "$pid" || FAIL=1; done
  [ "$FAIL" = 0 ] || { echo "ABORT: a $tag-pass label shard failed" >&2; return 1; }
  cat "$OUT"/labels_${tag}_shard*_p*.jsonl > "$OUT/labels_${tag}.jsonl"
}

run_pass p meas_label_main.php 855001 off || exit 1
run_pass h r9_label_main.php 875001 "$HORIZON" || exit 1
mv "$OUT/labels_p.jsonl" "$OUT/labels_primary.jsonl"
mv "$OUT/labels_h.jsonl" "$OUT/labels_horizon.jsonl"

# --- scoring + (D) reporting --------------------------------------
$PY "$CODE_DIR/analyze_l3_deploy.py" --jobs "$OUT/jobs_all.jsonl" \
  --labels "$OUT/labels_primary.jsonl" \
  > "$OUT/score_primary_stdout.txt" || exit 1
$PY "$CODE_DIR/stage0_report.py" --jobs "$OUT/jobs_all.jsonl" \
  --labels "$OUT/labels_primary.jsonl" --pass-name primary \
  --scorer-json "$OUT/score_primary_stdout.txt" \
  --json-out "$OUT/report_primary.json" \
  > "$OUT/report_primary.txt" || exit 1
$PY "$CODE_DIR/analyze_l3_deploy.py" --jobs "$OUT/jobs_all_h.jsonl" \
  --labels "$OUT/labels_horizon.jsonl" \
  > "$OUT/score_horizon_stdout.txt" || exit 1
$PY "$CODE_DIR/stage0_report.py" --jobs "$OUT/jobs_all_h.jsonl" \
  --labels "$OUT/labels_horizon.jsonl" --pass-name horizon \
  --scorer-json "$OUT/score_horizon_stdout.txt" \
  --json-out "$OUT/report_horizon.json" \
  > "$OUT/report_horizon.txt" || exit 1

# --- manifest -------------------------------------------------------
$PY - "$OUT" <<'PYEOF'
import glob, hashlib, json, os, sys
out = sys.argv[1]

def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def rows(p):
    return sum(1 for l in open(p) if l.strip())

man = {"out": out,
       "labels_primary_rows": rows(out + "/labels_primary.jsonl"),
       "labels_horizon_rows": rows(out + "/labels_horizon.jsonl"),
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/labels_*.jsonl") +
           glob.glob(out + "/report_*.json") +
           glob.glob(out + "/score_*_stdout.txt") +
           glob.glob(out + "/jobs_*.jsonl"))},
       "report_primary": json.load(open(out + "/report_primary.json")),
       "report_horizon": json.load(open(out + "/report_horizon.json"))}
json.dump(man, open(out + "/stage0_manifest.json", "w"), indent=1)
print(json.dumps({k: man[k] for k in
                  ("labels_primary_rows", "labels_horizon_rows")}))
PYEOF
echo "STAGE 0 COMPLETE - $OUT/stage0_manifest.json"
