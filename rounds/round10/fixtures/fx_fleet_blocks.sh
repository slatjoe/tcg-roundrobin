#!/usr/bin/env bash
# Step 2+3 fleet runner block fixtures (the
# fx_pilot_blocks.sh / Stage 3 form): verbatim block
# extraction from the DEPLOYED runners, run against
# stubs and the REAL published attempt-2 manifest.
#
# - inventory: every registered section present in
#   both runners;
# - PREGATE-GATE (run_fleet_games.sh): passes on the
#   real published attempt-2 manifest under the
#   fleet's pins; refuses on verdict mutation, build
#   sha mutation, tuple mismatch (env), and a missing
#   manifest;
# - FREESPACE (both runners): Stage 3 test seams --
#   ample space proceeds; short aborts; the straddle
#   between x1.0 and x1.25 aborts;
# - RAW-RERUN: exactly one rerun spawns for a planted
#   raw-timeout pair (stub driver records the call and
#   completes the rerun row; the block reuses the raw
#   tree + server, Stage 3 form), zero when none time
#   out;
# - TS-DRIVERS / RS-DRIVERS composed environment: a
#   stub $PY records argv + env per block -- teacher
#   blocks carry TEACHER_TUPLE_JSON (== the tuple the
#   runner's SETREAD builds), TEACHER_SNAP_DIR per
#   block (the pilot's logdir/snaps layout),
#   GATE_GAME_IDS_FILE, TCG_CLEAN_CHILDREN=1,
#   --timeout 8031, the settings' seed strings; raw
#   blocks carry the tuple but NO TEACHER_SNAP_DIR.
#   Negative: with the tuple export emptied, the
#   recorded tuple is empty (the check detects it).
#   (In the RS extraction copy only, the raw tree's
#   search.php expected hash is rewritten to the
#   stub tree's hash -- the assertion's presence is
#   what is under test here; the hash VALUE is pinned
#   by fx_fleet_pins and by the runner itself.)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
R10=$(dirname "$HERE")
STEP2="$R10/code/step2"
GAMES="$STEP2/run_fleet_games.sh"
L3="$STEP2/run_fleet_l3.sh"
SETTINGS="$STEP2/settings_fleet.json"
MANIFEST="$R10/data/step1/pregate_attempt2/pregate_manifest.json"
TMP=$(mktemp -d)
FAILURES=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAILURES=$((FAILURES+1)); }
check() { if [ "$2" = 0 ]; then pass "$1"; else fail "$1"; fi }

extract() { # extract <file> <tag> <out>
  awk -v tag="$2" '
    index($0, "===== " tag) {inb=1}
    inb && /^##### =====/ && !index($0, "===== " tag) \
      && seen {exit}
    inb {print; seen=1}
  ' "$1" > "$3"
  [ -s "$3" ]
}
nth() { sed -n "${2}p" "$1"; }

TUPLE_JSON=$(python3 - "$SETTINGS" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
tt = s["teacher_tuple"]
canon = {k: tt[k] for k in ("deadline_s", "hooks",
                            "horizon", "horizon_value",
                            "k", "margin", "name")}
print(json.dumps(canon, sort_keys=True))
PYEOF
)
THR_SHA=4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49

# ================= inventory =================
for tag in PINFN SETREAD TUPLE-BUILD PREGATE-GATE \
    FREESPACE TS-SRV TS-DRIVERS WAIT-T RS-SRV \
    RS-DRIVERS WAIT-R RAW-RERUN GRES READ.G MANIFEST; do
  grep -q "===== $tag" "$GAMES"
  check "games runner has section $tag" $?
done
for tag in PINFN SETREAD FREESPACE JOBS LS-SPLIT \
    LS-SRV LS-TREES LS-DRIVERS WAIT-L READ.F MANIFEST; do
  grep -q "===== $tag" "$L3"
  check "l3 runner has section $tag" $?
done
grep -q 'cp "$CODE_DIR/search_s3_thr.php" "$tree/search.php"' \
  "$GAMES"
check "games runner installs the threshold build in teacher trees" $?
grep -q '8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61' \
  "$GAMES"
check "games runner asserts the raw trees keep the fleet search.php" $?
grep -qF 'MEAS_SEED=$((LABEL_BASE + s * 100000000))' "$L3"
check "l3 runner derives MEAS_SEED from LABEL_BASE + shard x 10^8" $?

# ================= PREGATE-GATE =================
extract "$GAMES" PREGATE-GATE "$TMP/gate.sh"
check "PREGATE-GATE block extracted" $?
run_gate() { # run_gate <manifest> <tuple-env>
  PG_MANIFEST="$1" PG_THR_SHA="$THR_SHA" \
  TEACHER_TUPLE_JSON="$2" PY=python3 \
    bash "$TMP/gate.sh" > "$TMP/gate.out" 2>&1
  echo $?
}
rc=$(run_gate "$MANIFEST" "$TUPLE_JSON")
{ [ "$rc" = 0 ] && grep -q "PREGATE-GATE ok" "$TMP/gate.out"; }
check "PREGATE-GATE passes on the real attempt-2 manifest" $?
python3 - "$MANIFEST" "$TMP/man_verdict.json" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1])); m["verdict"] = "NOT IDENTICAL"
json.dump(m, open(sys.argv[2], "w"))
PYEOF
rc=$(run_gate "$TMP/man_verdict.json" "$TUPLE_JSON")
[ "$rc" != 0 ]
check "PREGATE-GATE refuses a non-IDENTICAL verdict" $?
python3 - "$MANIFEST" "$TMP/man_sha.json" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1]))
m["search_s3_thr_sha256"] = "0" * 64
json.dump(m, open(sys.argv[2], "w"))
PYEOF
rc=$(run_gate "$TMP/man_sha.json" "$TUPLE_JSON")
[ "$rc" != 0 ]
check "PREGATE-GATE refuses a build-sha mismatch" $?
rc=$(run_gate "$MANIFEST" '{"deadline_s": 1}')
[ "$rc" != 0 ]
check "PREGATE-GATE refuses a tuple mismatch" $?
rc=$(run_gate "$TMP/no_such_manifest.json" "$TUPLE_JSON")
[ "$rc" != 0 ]
check "PREGATE-GATE refuses a missing manifest" $?

# ================= FREESPACE =================
for spec in "run_fleet_games.sh 8" "run_fleet_l3.sh 4"; do
  set -- $spec; runner=$1; ntrees=$2
  extract "$STEP2/$runner" FREESPACE "$TMP/fs_$runner.sh"
  mkdir -p "$TMP/gtree"
  run_fs() {
    GTREE="$TMP/gtree" FLEET_REQ_PER_TREE_OVERRIDE="$1" \
    FLEET_DF_AVAIL_OVERRIDE="$2" \
      bash "$TMP/fs_$runner.sh" > "$TMP/fs.out" 2>&1
    echo $?
  }
  rc=$(run_fs 1000 100000000)
  { [ "$rc" = 0 ] && grep -q "required 8000 B\|required 4000 B" "$TMP/fs.out"; }
  check "FREESPACE $runner: ample space proceeds (sizes printed)" $?
  if [ "$ntrees" = 8 ]; then short=5000; else short=4000; fi
  rc=$(run_fs 1000 $short)
  [ "$rc" != 0 ]
  check "FREESPACE $runner: short space aborts" $?
  if [ "$ntrees" = 8 ]; then straddle=9000; else straddle=4500; fi
  rc=$(run_fs 1000 $straddle)
  [ "$rc" != 0 ]
  check "FREESPACE $runner: straddle (x1.0 ok, x1.25 short) aborts" $?
done

# ================= RAW-RERUN =================
mkdir -p "$TMP/stubbin" "$TMP/rec"
cat > "$TMP/stubbin/sleep" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
cat > "$TMP/pystub.sh" <<'EOF'
#!/usr/bin/env bash
# stub $PY: emulates the production server (ready
# line on stdout) and the paired driver (records the
# invocation; for a driver call, appends a completed
# raw row to --out). The games-report invocation and
# the heredoc spec-reader run the REAL python -- the
# writer under test is never stubbed.
case "$*" in
  *fleet_games_report.py*) exec python3 "$@" ;;
  -*) exec python3 "$@" ;;
  *search_server.py*)
    echo '{"ready": true}'
    echo x >> "$STUB_REC_DIR/servers"
    exit 0 ;;
  *paired_driver_gravy.py*)
    echo "$@" >> "$STUB_REC_DIR/drivers"
    out=""; seeds=""; seat=""
    prev=""
    for a in "$@"; do
      case "$prev" in
        --out) out="$a" ;;
        --seeds) seeds="$a" ;;
        --seat) seat="$a" ;;
      esac
      prev="$a"
    done
    python3 - "$out" "$seeds" "$seat" <<'PYEOF'
import json, sys
out, seed, seat = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
row = {"seed": seed, "seat": seat, "gamename": "777777777",
       "winner": seat, "capped": False, "draw": False,
       "p1life": 40, "p2life": 0, "turns": 30,
       "decisions": 90, "secs": 3.0, "arm": "raw",
       "gamelog_sha": "0" * 64}
with open(out, "a") as f:
    f.write(json.dumps(row) + "\n")
PYEOF
    exit 0 ;;
esac
exit 0
EOF
chmod +x "$TMP/stubbin/sleep" "$TMP/pystub.sh"
mkdir -p "$TMP/gtree2"
echo "stub tree search" > "$TMP/gtree2/search.php"

extract "$GAMES" RAW-RERUN "$TMP/rerun.sh"
# plant a games OUT with one raw-timeout pair
ROUT="$TMP/rout"; mkdir -p "$ROUT"
python3 - "$ROUT" "$SETTINGS" <<'PYEOF'
import json, os, sys
out, sp = sys.argv[1], sys.argv[2]
tt = dict(json.load(open(sp))["teacher_tuple"]); tt["pinned"] = 1
def drow(seed, seat, gn, winner, invalid=None):
    r = {"seed": seed, "seat": seat, "gamename": gn,
         "winner": winner, "capped": False, "draw": False,
         "p1life": 40, "p2life": 0, "turns": 30,
         "decisions": 90, "secs": 3.0, "arm": "x",
         "gamelog_sha": "0" * 64}
    if invalid: r["invalid"] = invalid
    return r
for blk in ("t1a","t1b","t2a","t2b","r1a","r1b","r2a","r2b"):
    rows = []
    if blk == "t1a":
        rows = [drow(26001, 1, "511111111", 1)]
    if blk == "r1a":
        rows = [drow(26001, 1, "611111111", 0, "timeout")]
    with open(os.path.join(out, "games_%s.jsonl" % blk), "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    logdir = os.path.join(out, "games_%s_log" % blk)
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "search_stats.jsonl"), "w") as f:
        if blk == "t1a":
            f.write(json.dumps({"game": "511111111",
                "teacher": 1, "setting": tt}) + "\n")
PYEOF
SIMD="$TMP/simd"; mkdir -p "$SIMD"
PATH="$TMP/stubbin:$PATH" OUT="$ROUT" CODE_DIR="$STEP2" \
  GTREE="$TMP/gtree2" \
  PY="$TMP/pystub.sh" SIM="$SIMD" STUB_REC_DIR="$TMP/rec" \
  GAME_TIMEOUT=8031 MAX_TURNS=87 DRAW_TRIGGER=62 \
  TEACHER_TUPLE_JSON="$TUPLE_JSON" \
  bash "$TMP/rerun.sh" > "$TMP/rerun.out" 2>&1
rc=$?
{ [ "$rc" = 0 ] && [ "$(grep -c paired_driver "$TMP/rec/drivers" 2>/dev/null)" = 1 ] \
  && grep -q -- "--seeds 26001" "$TMP/rec/drivers" \
  && [ -f "$ROUT/games_r1a_rerun.jsonl" ]; }
check "RAW-RERUN spawns exactly one rerun for the planted raw timeout" $?
# and with no timeouts: zero reruns
python3 - "$ROUT" <<'PYEOF'
import json, sys
p = sys.argv[1] + "/games_r1a.jsonl"
rows = [json.loads(l) for l in open(p)]
rows[0].pop("invalid", None); rows[0]["winner"] = 2
with open(p, "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
PYEOF
rm -f "$TMP/rec/drivers" "$ROUT/games_r1a_rerun.jsonl" \
  "$ROUT/pairing_draft.json" "$ROUT/games_report_draft.json"
PATH="$TMP/stubbin:$PATH" OUT="$ROUT" CODE_DIR="$STEP2" \
  GTREE="$TMP/gtree2" \
  PY="$TMP/pystub.sh" SIM="$SIMD" STUB_REC_DIR="$TMP/rec" \
  GAME_TIMEOUT=8031 MAX_TURNS=87 DRAW_TRIGGER=62 \
  TEACHER_TUPLE_JSON="$TUPLE_JSON" \
  bash "$TMP/rerun.sh" > "$TMP/rerun2.out" 2>&1
{ [ ! -f "$TMP/rec/drivers" ] \
  && grep -q "no raw timeouts" "$TMP/rerun2.out"; }
check "RAW-RERUN spawns zero reruns when no raw game times out" $?

# ================= composed env: TS/RS drivers =================
cat > "$TMP/envstub.sh" <<'EOF'
#!/usr/bin/env bash
# stub $PY for driver blocks: records argv + the env
# the composed-environment fixture asserts on.
rec="$STUB_REC_DIR/$(echo "$*" | grep -oE '\--arm [a-z]+' | tr ' ' '_')_$(echo "$*" | grep -oE '\--seeds [0-9-]+' | grep -oE '[0-9-]+').txt"
{
  echo "ARGV: $*"
  echo "TEACHER_TUPLE_JSON=${TEACHER_TUPLE_JSON-<absent>}"
  echo "TEACHER_SNAP_DIR=${TEACHER_SNAP_DIR-<absent>}"
  echo "GATE_GAME_IDS_FILE=${GATE_GAME_IDS_FILE-<absent>}"
  echo "TCG_CLEAN_CHILDREN=${TCG_CLEAN_CHILDREN-<absent>}"
} > "$rec"
exit 0
EOF
chmod +x "$TMP/envstub.sh"
mkdir -p "$TMP/rec2" "$TMP/gtree2" "$TMP/out2"
echo "stub tree search" > "$TMP/gtree2/search.php"
cp "$STEP2/search_s3_thr.php" "$TMP/gtree2/search_s3_thr.php"
STUBHASH=$(sha256sum "$TMP/gtree2/search.php" | cut -d' ' -f1)

extract "$GAMES" TS-DRIVERS "$TMP/ts.sh"
extract "$GAMES" RS-DRIVERS "$TMP/rs.sh"
sed -i "s/8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61/$STUBHASH/" "$TMP/rs.sh"

run_drivers_x() {
  OUT="$TMP/out2" CODE_DIR="$STEP2" GTREE="$TMP/gtree2" \
  PY="$TMP/envstub.sh" STUB_REC_DIR="$TMP/rec2" \
  GAME_TIMEOUT=8031 MAX_TURNS=87 DRAW_TRIGGER=62 \
  BLOCK_T1A_SEEDS=26001-26031 BLOCK_T1B_SEEDS=26032-26061 \
  BLOCK_T2A_SEEDS=26001-26031 BLOCK_T2B_SEEDS=26032-26061 \
  BLOCK_R1A_SEEDS=26001-26031 BLOCK_R1B_SEEDS=26032-26061 \
  BLOCK_R2A_SEEDS=26001-26031 BLOCK_R2B_SEEDS=26032-26061 \
  TEACHER_TUPLE_JSON="$2" TCG_CLEAN_CHILDREN=1 \
    bash "$1" > /dev/null 2>&1
  for i in $(seq 1 50); do
    [ "$(ls "$TMP/rec2" 2>/dev/null | wc -l)" -ge 4 ] && break
    sleep 0.1
  done
}
cp "$TMP/ts.sh" "$TMP/ts_block.sh"; cp "$TMP/rs.sh" "$TMP/rs_block.sh"
run_drivers_x "$TMP/ts_block.sh" "$TUPLE_JSON"
ok=0
for f in "$TMP/rec2"/--arm_teacher_*.txt; do
  grep -q "TEACHER_TUPLE_JSON=$TUPLE_JSON" "$f" || ok=1
  grep -q "TEACHER_SNAP_DIR=$TMP/out2/games_t.*_log/snaps" "$f" || ok=1
  grep -q -- "--timeout 8031" "$f" || ok=1
  grep -q "TCG_CLEAN_CHILDREN=1" "$f" || ok=1
  grep -q "GATE_GAME_IDS_FILE=$TMP/out2/games_t.*_ids.txt" "$f" || ok=1
done
[ "$(ls "$TMP/rec2" | wc -l)" = 4 ] || ok=1
check "TS-DRIVERS composed env: tuple, snap dirs, ids file, clean-children, timeout in all 4 teacher blocks" $ok
rm -rf "$TMP/rec2"; mkdir -p "$TMP/rec2"
run_drivers_x "$TMP/rs_block.sh" "$TUPLE_JSON"
ok=0
for f in "$TMP/rec2"/--arm_raw_*.txt; do
  grep -q "TEACHER_TUPLE_JSON=$TUPLE_JSON" "$f" || ok=1
  grep -q "TEACHER_SNAP_DIR=<absent>" "$f" || ok=1
  grep -q -- "--timeout 8031" "$f" || ok=1
done
[ "$(ls "$TMP/rec2" | wc -l)" = 4 ] || ok=1
check "RS-DRIVERS composed env: tuple present, TEACHER_SNAP_DIR absent, timeout in all 4 raw blocks" $ok
rm -rf "$TMP/rec2"; mkdir -p "$TMP/rec2"
run_drivers_x "$TMP/ts_block.sh" ""
empty_seen=0; canon_seen=0
for f in "$TMP/rec2"/*.txt; do
  grep -qx "TEACHER_TUPLE_JSON=" "$f" && empty_seen=1
  grep -q "TEACHER_TUPLE_JSON=$TUPLE_JSON" "$f" && canon_seen=1
done
{ [ "$empty_seen" = 1 ] && [ "$canon_seen" = 0 ]; }
check "negative: without the runner's tuple export the recorded tuple is empty (detected)" $?

echo "fx_fleet_blocks: $FAILURES failure(s)"
[ "$FAILURES" = 0 ]
