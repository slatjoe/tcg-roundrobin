#!/usr/bin/env bash
# Round-10 Step 2+3 COMBINED FLEET, L3 phase
# (step2-fleet-package.md; claude-reply-26cc773 sec.3):
# the Step 2 CO-READ's labels. L3 (W=50 CRN, tuple
# L3-W50+H) on ALL overturns the threshold teacher
# captured in the FLEET's teacher arm, labeled on the
# sec.14 engine (search_s2.php) with the PRODUCTION
# server, under the fresh label family
# MEAS_SEED = 1100055001 + shard x 10^8 (4 shards,
# enforced cap 512 jobs/shard -- disjointness proven
# by enumeration in fixtures/fx_fleet_seeds.py). The
# jobs file is written by build_fleet_jobs.py in
# strict JSON (allow_nan=False) at the source (the
# Oct 29 sec.14.6 ruling (b) form). Jobs/split/server/
# label blocks mirror the Step 1 pilot runner's
# proven forms (run_pilot.sh PILOT-LABEL-SRV /
# PILOT-LABEL) with fleet substitutions. Ends with
# fleet_read.py in FULL mode: the primary recomputed
# identically (deterministic bootstrap) + the co-read
# + the Step 2 gate decision + the attribution line.
#
# Requires the games phase's outputs (fleet_read.json,
# games_report.json, pairing.json) -- aborts otherwise;
# the primary-only read must exist first. Single-shot:
# refuses if the L3 outputs exist.
set -u
SIM=/home/joe/tcg/tcg-sim
CODE_DIR="${STEP2_CODE_DIR:-/home/joe/tcg/round10_code/step2}"
GAMES_OUT="${FLEET_OUT:-/home/joe/tcg/r10fleet_out}"
OUT="${FLEET_L3_OUT:-/home/joe/tcg/r10fleet_out/l3}"
GTREE="${GTREE:-/tmp/gravytree}"
CKPT="$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt"
PROD="$SIM/rl/search_server.py"
PY=/home/joe/tcg/rl-env/bin/python
LABEL_BASE=1100055001
NSHARD=4
export TCG_CLEAN_CHILDREN=1

expect_hash() { # expect_hash <path> <sha256>
  local got
  got=$(sha256sum "$1" 2>/dev/null | cut -d' ' -f1)
  if [ "$got" != "$2" ]; then
    echo "ABORT: hash mismatch on $1: got $got want $2" >&2
    exit 1
  fi
}

[ -f "$GAMES_OUT/fleet_read.json" ] || {
  echo "ABORT: games-phase fleet_read.json missing -- " \
    "run_fleet_games.sh must complete first" >&2; exit 1; }
[ -f "$GAMES_OUT/games_report.json" ] || {
  echo "ABORT: games_report.json missing" >&2; exit 1; }
[ -f "$GAMES_OUT/pairing.json" ] || {
  echo "ABORT: pairing.json missing" >&2; exit 1; }
[ -f "$OUT/l3_manifest.json" ] \
  && { echo "ABORT: fleet L3 outputs exist" >&2; exit 1; }
mkdir -p "$OUT"

##### ===== PINFN :: pinned inputs (fail loud) =====
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359
expect_hash "$CODE_DIR/search_s3_thr.php" \
  4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49
expect_hash "$CODE_DIR/search_s3.php" \
  87779e8ec96935776ce35d94ae350647d8f4174c8a17ed572b1bd4887b9a7ba7
expect_hash "$CODE_DIR/search_s2.php" \
  1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8
expect_hash "$CODE_DIR/s2_label_main.php" \
  1c1dfd9f9349e8db815f23e31637dee558a9ec36e09179142f71748a6bce72aa
expect_hash "$CODE_DIR/s1_eval_main.php" \
  0cb9d3c73114d5c6e54e93dd2dc122f20bd06ea8d8968fc4e703e8191b41e853
expect_hash "$CODE_DIR/build_fleet_jobs.py" \
  c7601341302fdf43f2e6708ff2d8bd5ef5417d1c2edee9dbe45dac1ca6e3695f
expect_hash "$CODE_DIR/fleet_games_report.py" \
  62ca60b5bc289944d1a6d7e66f0567e4ffac895f0f6e9b9a876207615f4fe578
expect_hash "$CODE_DIR/fleet_read.py" \
  7370b989c36d1bac70673d4a3e16da35c6f39eb1daa425af3bb80df9d811cfdc
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17
expect_hash "$CODE_DIR/settings_fleet.json" \
  1a8de29007a9e4f5c0e0e2ab500306b2967c0cc468e9f6ed26ebc640f088faa4
expect_hash "$PROD" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4
expect_hash "$GTREE/decks/nats2026_eriksen_gravy_60.txt" \
  b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed
expect_hash "$GTREE/search.php" \
  8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61
expect_hash "$CKPT" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3

{ for f in analyze_l3.py build_fleet_jobs.py \
    fleet_games_report.py fleet_read.py g8_sweep2.sh \
    merge_registry.py paired_driver_gravy.py \
    s1_eval_main.php s2_label_main.php search_s2.php \
    search_s3.php search_s3_thr.php settings_fleet.json \
    shm_sweep.py stage0_report.py run_fleet_games.sh \
    run_fleet_l3.sh; do
    sha256sum "$CODE_DIR/$f"
  done; sha256sum "$0"; } \
  > "$OUT/deployed_code_hashes_l3.txt" || exit 1
echo "pins OK; deployed code hashes recorded"

##### ===== SETREAD :: settings -> shell vars =====
eval "$($PY - "$CODE_DIR/settings_fleet.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
lt = s["label_tuple"]
canon = {k: lt[k] for k in ("deadline_s", "hooks",
                            "horizon", "horizon_value",
                            "k", "name")}
print("LABEL_TUPLE_JSON='%s'" % json.dumps(
    canon, sort_keys=True, separators=(",", ":")))
lab = s["label"]
print("LABEL_SETTING_NAME=%s" % lab["tuple"]["name"])
print("LABEL_HOOKS=%d" % lab["tuple"]["hooks"])
print("LABEL_DEADLINE_S=%d" % lab["tuple"]["deadline_s"])
print("LABEL_HORIZON=%d" % lab["tuple"]["horizon"])
print("LABEL_HORIZON_VALUE=%d" % lab["tuple"]["horizon_value"])
print("LABEL_K=%d" % lab["tuple"]["k"])
print("LABEL_SEED_BASE=%d" % lab["seed_base"])
print("LABEL_SHARDS=%d" % lab["shards"])
print("DECK_REL=decks/%s" % s["deck"])
PYEOF
)" || { echo "ABORT: settings read failed" >&2; exit 1; }
[ "$LABEL_BASE" = "$LABEL_SEED_BASE" ] || {
  echo "ABORT: LABEL_BASE $LABEL_BASE != settings " \
    "label.seed_base $LABEL_SEED_BASE" >&2; exit 1; }
[ "$NSHARD" = "$LABEL_SHARDS" ] || {
  echo "ABORT: NSHARD $NSHARD != settings label.shards" >&2
  exit 1; }
echo "label tuple: $LABEL_TUPLE_JSON base=$LABEL_BASE"

##### ===== FREESPACE :: 4 label trees + headroom =====
PER_TREE=$(du -sb "$GTREE" | cut -f1)
NTREES=4
REQUIRED=$((PER_TREE * NTREES))
AVAILABLE=$(df --output=avail -B1 /tmp | tail -1 | tr -d ' ')
REQ_OVR="${FLEET_REQ_PER_TREE_OVERRIDE:-}"
AVL_OVR="${FLEET_DF_AVAIL_OVERRIDE:-}"
[ -n "$REQ_OVR" ] && REQUIRED=$((REQ_OVR * NTREES))
[ -n "$AVL_OVR" ] && AVAILABLE=$AVL_OVR
echo "freespace: per-tree $PER_TREE B x $NTREES trees = " \
  "required $REQUIRED B; available $AVAILABLE B"
if [ $((AVAILABLE * 4)) -lt $((REQUIRED * 5)) ]; then
  echo "ABORT: /tmp free space below required x 1.25" >&2
  exit 1
fi

##### ===== G8 :: containment sweep before spawn =====
G8LOG="$OUT/g8_prespawn_l3.log"
bash "$CODE_DIR/g8_sweep2.sh" "$G8LOG" || {
  echo "ABORT: G8 containment tripped before spawn" >&2
  cat "$G8LOG" >&2; exit 1; }

##### ===== JOBS :: fleet jobs build (strict) =====
STREAM_ARGS=""
STAT_ARGS=""
for blk in t1a t1b t2a t2b; do
  STREAM_ARGS="$STREAM_ARGS --stream $GAMES_OUT/games_${blk}_log/snaps=$GAMES_OUT/games_${blk}_log/snaps/teacher_snap_index.jsonl"
  STAT_ARGS="$STAT_ARGS --stats $GAMES_OUT/games_${blk}_log/search_stats.jsonl"
done
$PY "$CODE_DIR/build_fleet_jobs.py" $STREAM_ARGS $STAT_ARGS \
  --settings "$CODE_DIR/settings_fleet.json" \
  --out "$OUT/jobs_all.jsonl" \
  --shard-prefix "$OUT/jobs_shard" \
  --report "$OUT/jobs_report.json" --nshard $NSHARD \
  > "$OUT/jobs_build.log" 2>&1 || {
  echo "ABORT: fleet jobs build failed (see jobs_build.log)" >&2
  tail -5 "$OUT/jobs_build.log" >&2; exit 1; }
cat "$OUT/jobs_build.log"

##### ===== LS-SPLIT :: per-shard player split =====
$PY - "$OUT" "$NSHARD" <<'PYEOF' || { echo "ABORT: player split failed" >&2; exit 1; }
import json, os, sys
out, nshard = sys.argv[1], int(sys.argv[2])
for s in range(nshard):
    src = os.path.join(out, "jobs_shard%d.jsonl" % s)
    jobs = [json.loads(l) for l in open(src) if l.strip()]
    for p in (1, 2):
        sel = [j for j in jobs if int(j["player"]) == p]
        with open(os.path.join(
                out, "jobs_shard%d_p%d.jsonl" % (s, p)),
                "w") as f:
            for j in sel:
                assert os.path.isdir(j["snap_dir"]), \
                    "snap dir missing: %s" % j["snap_dir"]
                f.write(json.dumps(j, allow_nan=False) + "\n")
        print("shard %d player %d: %d jobs" % (s, p, len(sel)))
PYEOF
echo "player split done"

##### ===== LS-SRV :: production servers x2 seats =====
SRV_PIDS=""
for seat in 1 2; do
  TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" \
    TCG_LEARNER_SEAT=$seat SEARCH_MODEL="$CKPT" \
    TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$PROD" > "$OUT/prod_s${seat}.log" \
      2>&1 < /dev/null &
  SRV_PIDS="$SRV_PIDS $!"
done
for seat in 1 2; do
  for i in $(seq 1 120); do
    grep -q 'search model loaded' "$OUT/prod_s${seat}.log" \
      2>/dev/null && break
    sleep 1
  done
  grep -q 'search model loaded' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat did not " \
      "load" >&2; exit 1; }
  grep -q 'ckpt_v10' "$OUT/prod_s${seat}.log" || {
    echo "ABORT: production server seat $seat loaded " \
      "the wrong model" >&2; exit 1; }
done
echo "production servers ready"

##### ===== LS-TREES :: label trees + sweepers =====
SWEEP_PIDS=""
start_sweeper() {
  ipcs -m > "$OUT/ipcs_$2.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$2.txt" \
    > "$OUT/shm_start_$2.txt"
  rm -f "$OUT/shm_sweep_$2.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$2.log" \
    --start-file "$OUT/shm_start_$2.txt" \
    --games-dir "$1/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_$2.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}
for s in 0 1 2 3; do
  tree="/tmp/r10fleet_l3_tree_$s"
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  find "$tree" -name __pycache__ -type d -exec rm -rf {} + \
    2>/dev/null
  cp "$CODE_DIR/search_s2.php" "$tree/search.php"
  cp "$CODE_DIR/s2_label_main.php" "$tree/"
  [ "$(sha256sum < "$tree/search.php" | cut -d' ' -f1)" \
    = "1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8" ] || {
    echo "ABORT: label tree $s search.php hash" >&2; exit 1; }
  [ "$(sha256sum < "$tree/s2_label_main.php" | cut -d' ' -f1)" \
    = "1c1dfd9f9349e8db815f23e31637dee558a9ec36e09179142f71748a6bce72aa" ] || {
    echo "ABORT: label tree $s s2_label_main.php hash" >&2
    exit 1; }
  start_sweeper "$tree" "l3_$s"
done
echo "label trees ready"

##### ===== LS-DRIVERS :: label shards x4 =====
PIDS_L="" FAIL_L=0
for s in 0 1 2 3; do
  (
    tree="/tmp/r10fleet_l3_tree_$s"
    for p in 1 2; do
      : > "$OUT/labels_shard${s}_p$p.jsonl"
      (cd "$tree" && MEAS_JOBS="$OUT/jobs_shard${s}_p$p.jsonl" \
         MEAS_OUT="$OUT/labels_shard${s}_p$p.jsonl" \
         EVAL_STATS="$OUT/label_stats_shard${s}_p$p.jsonl" \
         MEAS_SEED=$((LABEL_BASE + s * 100000000)) \
         TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
         EVAL_SETTING_NAME="$LABEL_SETTING_NAME" \
         EVAL_HOOKS="$LABEL_HOOKS" \
         EVAL_DEADLINE_S="$LABEL_DEADLINE_S" \
         LABEL_HORIZON="$LABEL_HORIZON" \
         EVAL_HORIZON_VALUE="$LABEL_HORIZON_VALUE" \
         EVAL_K="$LABEL_K" \
         php s2_label_main.php \
           "$tree/$DECK_REL" "$tree/$DECK_REL" \
           --policy-search --games 1 \
           > "$OUT/label_shard${s}_p$p.err" 2>&1) || exit 1
    done
  ) &
  PIDS_L="$PIDS_L $!"
done
echo "label drivers: $PIDS_L"

##### ===== WAIT-L :: label phase completes =====
for pid in $PIDS_L; do wait "$pid" || FAIL_L=1; done
[ "$FAIL_L" = 0 ] || {
  echo "ABORT: an L3 label shard failed" >&2; exit 1; }
for s in 0 1 2 3; do touch "$OUT/shm_sweep_l3_$s.stop"; done
for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
sleep 2
cat "$OUT"/labels_shard*_p*.jsonl > "$OUT/labels_all.jsonl"
wc -l "$OUT/labels_all.jsonl"

##### ===== READ.F :: full read (primary + co-read) =====
$PY "$CODE_DIR/fleet_read.py" \
  --pairing "$GAMES_OUT/pairing.json" \
  --games-report "$GAMES_OUT/games_report.json" \
  --settings "$CODE_DIR/settings_fleet.json" \
  --jobs "$OUT/jobs_all.jsonl" \
  --labels "$OUT/labels_all.jsonl" \
  --games-rows "$GAMES_OUT/games_t1a.jsonl" \
    "$GAMES_OUT/games_t1b.jsonl" \
    "$GAMES_OUT/games_t2a.jsonl" \
    "$GAMES_OUT/games_t2b.jsonl" \
  --json-out "$GAMES_OUT/fleet_read.json" \
  > "$GAMES_OUT/fleet_read.txt" 2>&1 || {
  echo "ABORT: fleet full read failed" >&2
  tail -20 "$GAMES_OUT/fleet_read.txt" >&2; exit 1; }
cat "$GAMES_OUT/fleet_read.txt"

##### ===== MANIFEST :: L3-phase manifest =====
$PY - "$OUT" "$GAMES_OUT" <<'PYEOF'
import hashlib, json, os, sys
out, gout = sys.argv[1], sys.argv[2]
def rows(p):
    try:
        with open(p, "rb") as f:
            return sum(1 for l in f if l.strip())
    except OSError:
        return None
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
names = ["jobs_all.jsonl", "jobs_report.json",
         "labels_all.jsonl", "deployed_code_hashes_l3.txt"]
files = {}
for n in names:
    p = os.path.join(out, n)
    if os.path.exists(p):
        files[n] = {"rows": rows(p), "sha256": sha(p)}
read = json.load(open(os.path.join(gout, "fleet_read.json")))
man = {"stage": "round10-step2-fleet-l3",
       "primary_verdict": read.get("verdict"),
       "step2_gate": (read.get("coread") or {}).get("step2_gate"),
       "attribution": (read.get("coread") or {}).get("attribution"),
       "label_storage": "publication stores the label parts "
       "gzip-compressed (.jsonl.gz) with decompressed "
       "sha256s in the MANIFEST (pilot precedent, stated "
       "in settings label.storage)",
       "files": files}
with open(os.path.join(out, "l3_manifest.json"), "w") as f:
    json.dump(man, f, indent=1)
print("l3 manifest written; step2 gate:",
      (man["step2_gate"] or {}).get("PASS"))
PYEOF
echo "== fleet L3 phase done =="
