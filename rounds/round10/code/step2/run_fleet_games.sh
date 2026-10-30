#!/usr/bin/env bash
# Round-10 Step 2+3 COMBINED FLEET, games phase
# (step2-fleet-package.md; design claude-reply-26cc773
# sec.3). Fork of round 9's run_stage3_games.sh
# (db89f107...): same block structure, same guards,
# same raw-rerun and registry flow. The fleet: threshold
# teacher (the Step 1 build, search_s3_thr.php
# 4a1936fe..., tuple H8k-180+H from settings_fleet.json)
# vs RAW v10 (the Gravy anchor policy served raw --
# paired_driver_gravy.py --arm raw on the fleet tree's
# own search.php 8f6b35da..., the Stage 3 raw-arm
# configuration), Gravy mirror vs heuristic, instrument
# 87/62, seeds 26001-26061 x seats {1,2} x arms
# {teacher, raw} = 244 games, 122 pairs. GAME_TIMEOUT
# 8031 s = 3 x the pilot's observed max wall 2676.8 s,
# for BOTH arms (settings games.timeout_s). The raw
# phase runs AFTER the teacher phase completes, never
# concurrent (Stage 3 form).
#
# PRE-GATE (PREGATE-GATE below): NO fresh pre-gate run --
# the build + tuple are already covered by the Step 1
# pre-gate attempt 2's IDENTICAL (same build sha, same
# tuple). This runner MECHANICALLY refuses unless the
# attempt-2 pregate_manifest.json reads IDENTICAL under
# this run's pinned build sha + the tuple built from
# settings_fleet.json.
#
# Single-shot: refuses if the fleet outputs exist.
# Box paths mirror the pilot/stage3 runners.
set -u
SIM=/home/joe/tcg/tcg-sim
CODE_DIR="${STEP2_CODE_DIR:-/home/joe/tcg/round10_code/step2}"
OUT="${FLEET_OUT:-/home/joe/tcg/r10fleet_out}"
GTREE="${GTREE:-/tmp/gravytree}"
CKPT="$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt"
PY=/home/joe/tcg/rl-env/bin/python
export TCG_CLEAN_CHILDREN=1

expect_hash() { # expect_hash <path> <sha256>
  local got
  got=$(sha256sum "$1" 2>/dev/null | cut -d' ' -f1)
  if [ "$got" != "$2" ]; then
    echo "ABORT: hash mismatch on $1: got $got want $2" >&2
    exit 1
  fi
}

[ -f "$OUT/games_manifest.json" ] \
  && { echo "ABORT: fleet games outputs exist" >&2; exit 1; }
[ -f "$OUT/fleet_read.json" ] \
  && { echo "ABORT: fleet read exists" >&2; exit 1; }
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
  > "$OUT/deployed_code_hashes_games.txt" || exit 1
echo "pins OK; deployed code hashes recorded"

##### ===== SETREAD :: settings -> shell vars =====
eval "$($PY - "$CODE_DIR/settings_fleet.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
g = s["games"]
print("GAME_TIMEOUT=%d" % g["timeout_s"])
print("REGISTRY_TAG=%s" % g["registry_tag"])
print("DECK_NAME=%s" % s["deck"])
print("MAX_TURNS=%d" % s["instrument_max_turns"])
print("DRAW_TRIGGER=%d" % s["instrument_draw_trigger"])
tt = s["teacher_tuple"]
canon = {k: tt[k] for k in ("deadline_s", "hooks", "horizon",
                            "horizon_value", "k", "margin",
                            "name")}
# default separators: the attempt-2 pregate manifest
# recorded teacher_tuple_json in json.dumps' default
# spaced form, and PREGATE-GATE string-compares against
# it (fx_fleet_parity (b) pins this form).
print("TEACHER_TUPLE_JSON='%s'" % json.dumps(
    canon, sort_keys=True))
lt = s["label_tuple"]
canon_l = {k: lt[k] for k in ("deadline_s", "hooks",
                              "horizon", "horizon_value",
                              "k", "name")}
print("LABEL_TUPLE_JSON='%s'" % json.dumps(
    canon_l, sort_keys=True, separators=(",", ":")))
print("PG_MANIFEST=%s" % s["pregate"]["manifest_box_path"])
print("PG_THR_SHA=%s" % s["pregate"]["search_s3_thr_sha256"])
for b in g["blocks"]:
    print("BLOCK_%s_SEEDS=%s" % (b["tag"].upper(), b["seeds"]))
print("PAIRS_EXPECT=%d" % g["pairs"])
PYEOF
)" || { echo "ABORT: settings read failed" >&2; exit 1; }
export TEACHER_TUPLE_JSON
echo "settings: timeout=$GAME_TIMEOUT tag=$REGISTRY_TAG"

##### ===== TUPLE-BUILD :: pinned teacher tuple =====
[ -n "${TEACHER_TUPLE_JSON:-}" ] || {
  echo "ABORT: TEACHER_TUPLE_JSON empty" >&2; exit 1; }
echo "teacher tuple: $TEACHER_TUPLE_JSON"

##### ===== PREGATE-GATE :: attempt-2 IDENTICAL =====
$PY - "$PG_MANIFEST" "$PG_THR_SHA" <<'PYEOF' || {
import json, os, sys
man_p, thr_sha = sys.argv[1], sys.argv[2]
if not os.path.exists(man_p):
    print("PREGATE-GATE: attempt-2 manifest absent: %s"
          % man_p)
    sys.exit(1)
man = json.load(open(man_p))
if man.get("verdict") != "IDENTICAL":
    print("PREGATE-GATE: attempt-2 verdict is %r, not "
          "IDENTICAL" % (man.get("verdict"),))
    sys.exit(1)
if man.get("search_s3_thr_sha256") != thr_sha:
    print("PREGATE-GATE: manifest build sha %s != fleet "
          "pin %s" % (man.get("search_s3_thr_sha256"),
                      thr_sha))
    sys.exit(1)
if man.get("teacher_tuple_json") != os.environ.get(
        "TEACHER_TUPLE_JSON"):
    print("PREGATE-GATE: manifest tuple != fleet tuple")
    sys.exit(1)
print("PREGATE-GATE ok: attempt 2 IDENTICAL under the "
      "fleet's build sha + tuple")
PYEOF
  echo "ABORT: PREGATE-GATE refused the fleet launch" >&2
  exit 1; }

##### ===== FREESPACE :: 8 trees + 25% headroom =====
PER_TREE=$(du -sb "$GTREE" | cut -f1)
NTREES=8
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
G8LOG="$OUT/g8_prespawn_games.log"
bash "$CODE_DIR/g8_sweep2.sh" "$G8LOG" || {
  echo "ABORT: G8 containment tripped before spawn" >&2
  cat "$G8LOG" >&2; exit 1; }
$PY "$CODE_DIR/shm_sweep.py" --once \
  > "$OUT/shm_prespawn_games.log" 2>&1 \
  || echo "note: shm sweep nonzero (see log)"

##### ===== TS-SRV :: teacher servers (patched) =====
for port in 18241 18242; do
  ( cd "$SIM" && TCG_POLICY_SEARCH=1 \
    TCG_POLICY_SEARCH_CKPT="$CKPT" \
    TCG_POLICY_SEARCH_DEVICE=cuda \
    TCG_SEARCH_SERVER=patched \
    SEARCH_MODEL="$CKPT" \
    $PY rl/search_server.py --socket /tmp/pol_$port.sock \
      --port $port > "$OUT/srv_$port.log" 2>&1 ) &
done
sleep 20
for port in 18241 18242; do
  grep -q '"ready": true' "$OUT/srv_$port.log" || {
    echo "ABORT: teacher server $port not ready" >&2
    tail -5 "$OUT/srv_$port.log" >&2; exit 1; }
done
echo "teacher servers ready"

##### ===== TS-SWEEP :: SHM sweeper alongside =====
( while :; do
    $PY "$CODE_DIR/shm_sweep.py" --once \
      >> "$OUT/shm_sweep_games.log" 2>&1
    sleep 120
  done ) &
SWEEP_PID=$!
echo "shm sweeper pid $SWEEP_PID"

##### ===== TS-DRIVERS :: teacher blocks x4 =====
PIDS_T=()
for spec in "t1a 1 $BLOCK_T1A_SEEDS 18241" \
            "t1b 1 $BLOCK_T1B_SEEDS 18241" \
            "t2a 2 $BLOCK_T2A_SEEDS 18242" \
            "t2b 2 $BLOCK_T2B_SEEDS 18242"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3; port=$4
  tree=/tmp/r10fleet_gm_$blk
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  cp "$CODE_DIR/search_s3_thr.php" "$tree/search.php"
  [ "$(sha256sum < "$tree/search.php" | cut -d' ' -f1)" \
    = "4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49" ] || {
    echo "ABORT: teacher tree $blk search.php hash" >&2
    exit 1; }
  mkdir -p "$OUT/games_${blk}_log" "$OUT/games_${blk}_log/snaps"
  GATE_GAME_IDS_FILE="$OUT/games_${blk}_ids.txt" \
  TEACHER_TUPLE_JSON="$TEACHER_TUPLE_JSON" \
  TEACHER_SNAP_DIR="$OUT/games_${blk}_log/snaps" \
  $PY "$CODE_DIR/paired_driver_gravy.py" \
    --arm teacher --seat "$seat" --seeds "$seeds" \
    --tree "$tree" --sock "/tmp/pol_$port.sock" \
    --out "$OUT/games_${blk}.jsonl" \
    --logdir "$OUT/games_${blk}_log" \
    --max-turns "$MAX_TURNS" \
    --cap-trigger "$DRAW_TRIGGER" \
    --timeout "$GAME_TIMEOUT" \
    > "$OUT/driver_${blk}.log" 2>&1 &
  PIDS_T+=($!)
done
echo "teacher drivers: ${PIDS_T[*]}"

##### ===== WAIT-T :: teacher phase completes =====
TFAIL=0
for p in "${PIDS_T[@]}"; do wait "$p" || TFAIL=1; done
[ "$TFAIL" = 0 ] || echo "note: a teacher driver exited nonzero"
kill "$SWEEP_PID" 2>/dev/null
pkill -f 'rl/search_server.py --socket /tmp/pol_1824' \
  2>/dev/null
sleep 2
echo "teacher phase done"

##### ===== RS-SRV :: raw servers (raw form) =====
for port in 18251 18252; do
  ( cd "$SIM" && TCG_POLICY_SEARCH_DEVICE=cuda \
    SEARCH_MODEL="$CKPT" \
    $PY rl/search_server.py --socket /tmp/pol_$port.sock \
      --port $port > "$OUT/srv_$port.log" 2>&1 ) &
done
sleep 20
for port in 18251 18252; do
  grep -q '"ready": true' "$OUT/srv_$port.log" || {
    echo "ABORT: raw server $port not ready" >&2
    tail -5 "$OUT/srv_$port.log" >&2; exit 1; }
done
echo "raw servers ready"
sleep 60   # TS-SWEEP tail (Stage 3 form)

##### ===== RS-DRIVERS :: raw blocks x4 =====
PIDS_R=()
for spec in "r1a 1 $BLOCK_R1A_SEEDS 18251" \
            "r1b 1 $BLOCK_R1B_SEEDS 18251" \
            "r2a 2 $BLOCK_R2A_SEEDS 18252" \
            "r2b 2 $BLOCK_R2B_SEEDS 18252"; do
  set -- $spec; blk=$1; seat=$2; seeds=$3; port=$4
  tree=/tmp/r10fleet_gm_$blk
  rm -rf "$tree"; cp -r "$GTREE" "$tree"
  [ "$(sha256sum < "$tree/search.php" | cut -d' ' -f1)" \
    = "8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61" ] || {
    echo "ABORT: raw tree $blk search.php is not the " \
      "fleet tree's own" >&2; exit 1; }
  mkdir -p "$OUT/games_${blk}_log"
  GATE_GAME_IDS_FILE="$OUT/games_${blk}_ids.txt" \
  TEACHER_TUPLE_JSON="$TEACHER_TUPLE_JSON" \
  $PY "$CODE_DIR/paired_driver_gravy.py" \
    --arm raw --seat "$seat" --seeds "$seeds" \
    --tree "$tree" --sock "/tmp/pol_$port.sock" \
    --out "$OUT/games_${blk}.jsonl" \
    --logdir "$OUT/games_${blk}_log" \
    --max-turns "$MAX_TURNS" \
    --cap-trigger "$DRAW_TRIGGER" \
    --timeout "$GAME_TIMEOUT" \
    > "$OUT/driver_${blk}.log" 2>&1 &
  PIDS_R+=($!)
done
echo "raw drivers: ${PIDS_R[*]}"

##### ===== WAIT-R :: raw phase completes =====
RFAIL=0
for p in "${PIDS_R[@]}"; do wait "$p" || RFAIL=1; done
[ "$RFAIL" = 0 ] || echo "note: a raw driver exited nonzero"
echo "raw phase done (servers stay up for the rerun pass)"

##### ===== RAW-RERUN :: one rerun per raw timeout =====
# Stage 3 form: the selector reads the DRAFT pairing's
# raw rows (invalid == "timeout"); reruns reuse the
# raw trees and the still-running raw servers.
$PY "$CODE_DIR/fleet_games_report.py" --out-dir "$OUT" \
  --settings "$CODE_DIR/settings_fleet.json" \
  --json-out "$OUT/games_report_draft.json" --pairing-only \
  > "$OUT/games_report_draft.log" 2>&1 || {
  echo "ABORT: draft pairing failed" >&2; exit 1; }
RERUN_LIST=$($PY - "$OUT/pairing_draft.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
for p in d["pairs"]:
    r = p.get("raw") or {}
    row = r.get("row") or {}
    if row.get("invalid") == "timeout":
        blk = (r.get("file") or "").replace("games_", "") \
                                   .replace(".jsonl", "")
        print("%s %s %s" % (p["seed"], p["seat"], blk))
PYEOF
) || exit 1
PIDS="" FAIL=0
while read -r seed seat rblk; do
  [ -n "$seed" ] || continue
  (
    tree="/tmp/r10fleet_gm_${rblk}"
    logdir="$OUT/games_${rblk}_rerun_log"
    mkdir -p "$logdir"
    GATE_GAME_IDS_FILE="$OUT/games_${rblk}_rerun_ids.txt" \
    TEACHER_TUPLE_JSON="$TEACHER_TUPLE_JSON" \
    $PY "$CODE_DIR/paired_driver_gravy.py" \
      --arm raw --seat "$seat" --seeds "$seed" \
      --tree "$tree" --sock "/tmp/pol_$((18250 + seat)).sock" \
      --out "$OUT/games_${rblk}_rerun.jsonl" \
      --logdir "$logdir" \
      --max-turns "$MAX_TURNS" \
      --cap-trigger "$DRAW_TRIGGER" \
      --timeout "$GAME_TIMEOUT" \
      > "$OUT/games_${rblk}_rerun.stdout" 2>&1
  ) &
  PIDS="$PIDS $!"
done <<EOF_RERUN
$RERUN_LIST
EOF_RERUN
for pid in $PIDS; do wait "$pid" || FAIL=1; done
[ "$FAIL" = 0 ] || { echo "ABORT: a raw rerun failed" >&2; exit 1; }
if [ -n "$RERUN_LIST" ]; then
  echo "raw reruns done"
else
  echo "no raw timeouts; no reruns"
fi
pkill -f 'rl/search_server.py --socket /tmp/pol_1825' \
  2>/dev/null
sleep 2

##### ===== GRES :: report + registry merge =====
$PY "$CODE_DIR/fleet_games_report.py" --out-dir "$OUT" \
  --settings "$CODE_DIR/settings_fleet.json" \
  --json-out "$OUT/games_report.json" \
  > "$OUT/games_report.txt" 2>&1 || {
  echo "ABORT: games report failed" >&2
  tail -20 "$OUT/games_report.txt" >&2; exit 1; }
cat "$OUT/games_report.txt"
$PY "$CODE_DIR/merge_registry.py" \
  --tag "$REGISTRY_TAG" \
  "$OUT"/games_*_ids.txt \
  > "$OUT/registry_merge_games.log" 2>&1 || {
  echo "ABORT: registry merge failed" >&2; exit 1; }
tail -2 "$OUT/registry_merge_games.log"

##### ===== READ.G :: primary read (co-read pending) =====
$PY "$CODE_DIR/fleet_read.py" \
  --pairing "$OUT/pairing.json" \
  --games-report "$OUT/games_report.json" \
  --settings "$CODE_DIR/settings_fleet.json" \
  --primary-only \
  --json-out "$OUT/fleet_read.json" \
  > "$OUT/fleet_read.txt" 2>&1 || {
  echo "ABORT: fleet primary read failed" >&2
  tail -20 "$OUT/fleet_read.txt" >&2; exit 1; }
cat "$OUT/fleet_read.txt"

##### ===== MANIFEST :: games-phase manifest =====
$PY - "$OUT" "$CODE_DIR" <<'PYEOF'
import hashlib, json, os, sys
out, code = sys.argv[1], sys.argv[2]
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
names = ["games_t1a.jsonl", "games_t1b.jsonl",
         "games_t2a.jsonl", "games_t2b.jsonl",
         "games_r1a.jsonl", "games_r1b.jsonl",
         "games_r2a.jsonl", "games_r2b.jsonl",
         "games_report.json", "pairing.json",
         "fleet_read.json", "deployed_code_hashes_games.txt"]
files = {}
for n in names:
    p = os.path.join(out, n)
    if os.path.exists(p):
        files[n] = {"rows": rows(p), "sha256": sha(p)}
read = json.load(open(os.path.join(out, "fleet_read.json")))
man = {"stage": "round10-step2-fleet-games",
       "settings": os.path.join(code, "settings_fleet.json"),
       "primary_verdict": read.get("verdict"),
       "primary": read.get("primary"),
       "teacher_timeouts": read.get("teacher_timeouts"),
       "files": files}
with open(os.path.join(out, "games_manifest.json"),
          "w") as f:
    json.dump(man, f, indent=1)
print("games manifest written; primary verdict:",
      man["primary_verdict"])
PYEOF
echo "== fleet games phase done =="
