#!/bin/bash
# Round-10 Step 0 fixture: verbatim-extraction tests
# for run_probe.sh's control blocks (the standing
# rule: every runner block that spawns/waits gets one).
#
# Each block is extracted VERBATIM from the staged
# runner (between its # BLOCK:NAME-BEGIN / END
# markers) and executed in a stub environment:
#   * $PY is a dispatcher stub: "-" (heredoc snippets)
#     runs REAL python3 (the block's own splitter /
#     assertion snippets execute for real); the
#     capture driver writes its real output shapes
#     (rows file, manifest with assert_ok, game ids);
#     anything else exits 0.
#   * $PHP is a stub that consumes MEAS_JOBS and
#     writes dummy rows to MEAS_OUT / EVAL_STATS,
#     logging every call; FX_FAIL=1 makes shard-2
#     invocations exit 1 (the wait/FAIL path).
#   * CODE_DIR holds the REAL search_s3.php /
#     search_s2.php files (data for the blocks'
#     expect_hash assertions -- the PHP under test
#     never runs on this machine) plus stubs.
#   * start_sweeper is a recording stub; GTREE is a
#     tiny real tree.
# Assertions: block exit codes, spawned-call counts
# (driver x2, php x8 per shard phase), streams.txt
# contents, server-load markers, and the failure
# paths (FREESPACE abort on a stubbed tiny df; EVAL
# abort when a shard fails).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$HERE/../code/run_probe.sh"
SB="$(mktemp -d /tmp/fx_probe_blocks.XXXXXX)"
trap 'rm -rf "$SB"' EXIT
mkdir -p "$SB/out" "$SB/code" "$SB/gtree/decks" \
         "$SB/gtree/vendor/talishar/Games"
echo deck > "$SB/gtree/decks/nats2026_eriksen_gravy_60.txt"
cp "$HERE/../code/search_s3.php" "$SB/code/search_s3.php"
cp "$HERE/../code/search_s2.php" "$SB/code/search_s2.php"
CALLS="$SB/calls.log"; : > "$CALLS"

cat > "$SB/pystub" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
calls = os.environ["FX_CALLS"]
if len(sys.argv) > 1 and sys.argv[1] == "-":
    os.execvp("python3", ["python3", "-"] + sys.argv[2:])
with open(calls, "a") as f:
    f.write("PY " + " ".join(sys.argv[1:]) + "\n")
if len(sys.argv) > 1 and sys.argv[1].endswith("search_server.py"):
    print("search model loaded: ckpt_v10.pt")
    print("deployed ckpt_v10 sha ok")
    sys.exit(0)
if len(sys.argv) > 1 and sys.argv[1].endswith("paired_driver_gravy.py"):
    args = sys.argv[2:]
    out = args[args.index("--out") + 1]
    with open(out, "w") as f:
        f.write('{"game": "2400100001"}\n')
    with open(out + ".manifest.json", "w") as f:
        json.dump({"assert_ok": True, "arm": "capture",
                   "seat": 1, "assertions": ["stub"]}, f)
    ids = os.environ.get("GATE_GAME_IDS_FILE")
    if ids:
        with open(ids, "a") as f:
            f.write("2400100001\n")
    sys.exit(0)
sys.exit(0)
EOF
chmod +x "$SB/pystub"

cat > "$SB/phpstub" <<'EOF'
#!/bin/bash
echo "PHP jobs=$MEAS_JOBS" >> "$FX_CALLS"
if [ "${FX_FAIL:-0}" = "1" ]; then
  case "$MEAS_JOBS" in *shard2*) exit 1;; esac
fi
n=0
[ -f "$MEAS_JOBS" ] && n=$(grep -c . "$MEAS_JOBS" || true)
i=0
while [ "$i" -lt "$n" ]; do
  echo '{"snap":"stub","cand":0,"world":0}' >> "$MEAS_OUT"
  i=$((i+1))
done
echo '{"snap":"stub","wall_ms":1000}' >> "$EVAL_STATS"
exit 0
EOF
chmod +x "$SB/phpstub"

extract() {  # $1 = block name, $2 = dest
  awk "/# BLOCK:$1-BEGIN/,/# BLOCK:$1-END/" "$RUNNER" > "$2"
  grep -q "BLOCK:$1-END" "$2" || {
    echo "FAIL fx_probe_blocks: block $1 not extractable"; exit 1; }
}

HARNESS_COMMON='
set -u
OUT="'"$SB"'/out"
CODE_DIR="'"$SB"'/code"
GTREE="'"$SB"'/gtree"
PY="'"$SB"'/pystub"
PHP="'"$SB"'/phpstub"
PROD="/stub/search_server.py"
CKPT="/stub/ckpt_v10.pt"
DECK_REL="decks/nats2026_eriksen_gravy_60.txt"
SRV_WAIT_TRIES=5
SRV_PIDS=""; SWEEP_PIDS=""
export FX_CALLS="'"$CALLS"'"
start_sweeper() { echo "SWEEPER $2" >> "$FX_CALLS"; }
cleanup() { :; }
'
# expect_hash, verbatim from the runner
sed -n '/^expect_hash() {/,/^}/p' "$RUNNER" > "$SB/expect_hash.inc"
grep -q 'sha256sum' "$SB/expect_hash.inc" || {
  echo "FAIL fx_probe_blocks: expect_hash not extractable"; exit 1; }

FAILN=0
note() { if [ "$1" = 0 ]; then echo "PASS $2"; else
  echo "FAIL $2"; FAILN=$((FAILN+1)); fi; }

# ---- FREESPACE: pass case -------------------------------------------
extract FREESPACE "$SB/blk_freespace.sh"
{ echo "$HARNESS_COMMON"; echo 'PHASE=capture';
  cat "$SB/blk_freespace.sh"; echo 'echo BLOCK_RC=$?';
} > "$SB/run_fs.sh"
bash "$SB/run_fs.sh" > "$SB/fs.out" 2>&1
grep -q 'free-space pre-flight: required_bytes=' "$SB/fs.out"
note $? "fx blocks FREESPACE pass case prints the pre-flight line"
# ---- FREESPACE: abort case (stub df reports 1 byte free) ------------
mkdir -p "$SB/stubbin"
printf '#!/bin/sh\necho "Filesystem 1B-blocks Used Available Use%% Mounted on"\necho "tmpfs 100 99 1 99%% /tmp"\n' \
  > "$SB/stubbin/df"; chmod +x "$SB/stubbin/df"
PATH="$SB/stubbin:$PATH" bash "$SB/run_fs.sh" > "$SB/fs2.out" 2>&1
rc=$?
[ $rc -ne 0 ] && grep -q 'ABORT: free-space pre-flight' "$SB/fs2.out"
note $? "fx blocks FREESPACE abort case exits non-zero with ABORT"

# ---- SRV -------------------------------------------------------------
extract SRV "$SB/blk_srv.sh"
{ echo "$HARNESS_COMMON"; cat "$SB/expect_hash.inc";
  cat "$SB/blk_srv.sh"; echo 'start_servers'; echo 'echo SRV_OK';
} > "$SB/run_srv.sh"
bash "$SB/run_srv.sh" > "$SB/srv.out" 2>&1
rc=$?
[ $rc -eq 0 ] && grep -q SRV_OK "$SB/srv.out" \
  && grep -q 'search model loaded' "$SB/out/prod_s1.log" \
  && grep -q 'search model loaded' "$SB/out/prod_s2.log"
note $? "fx blocks SRV starts both servers and verifies loads"

# ---- CAPTURE ----------------------------------------------------------
extract CAPTURE "$SB/blk_capture.sh"
{ echo "$HARNESS_COMMON"; cat "$SB/expect_hash.inc";
  echo 'BLOCK=1'; echo 'S1SEEDS="24001-24045"';
  echo 'S2SEEDS="24046-24090"';
  cat "$SB/blk_capture.sh"; echo 'echo CAPTURE_OK';
} > "$SB/run_cap.sh"
: > "$CALLS"
bash "$SB/run_cap.sh" > "$SB/cap.out" 2>&1
rc=$?
ndrivers=$(grep -c 'paired_driver_gravy.py' "$CALLS" || true)
nstreams=$(grep -c 'snaps=' "$SB/out/streams.txt" || true)
[ $rc -eq 0 ] && grep -q CAPTURE_OK "$SB/cap.out" \
  && [ "$ndrivers" = 2 ] && [ "$nstreams" = 2 ] \
  && grep -q 'capture assertions OK' "$SB/cap.out"
note $? "fx blocks CAPTURE runs 2 seat drivers, manifest assert passes, 2 streams recorded"

# ---- EVAL -------------------------------------------------------------
extract EVAL "$SB/blk_eval.sh"
# the runner creates the shard trees immediately before
# the block (same phase, outside the block markers);
# the harness does the same so the block's cd succeeds
for s in 0 1 2 3; do mkdir -p "/tmp/r10probe_eval_tree_$s"; done
cat > "$SB/out/eval_jobs.jsonl" <<'EOF'
{"snap":"gA_t1","game":"gA","player":1}
{"snap":"gB_t1","game":"gB","player":2}
EOF
{ echo "$HARNESS_COMMON"; cat "$SB/blk_eval.sh";
  echo 'echo EVAL_OK';
} > "$SB/run_eval.sh"
: > "$CALLS"
bash "$SB/run_eval.sh" > "$SB/eval.out" 2>&1
rc=$?
nphp=$(grep -c '^PHP ' "$CALLS" || true)
[ $rc -eq 0 ] && grep -q EVAL_OK "$SB/eval.out" && [ "$nphp" = 8 ]
note $? "fx blocks EVAL spawns 8 shard processes and waits clean"
grep -q 'for pid in $PIDS; do wait' "$SB/blk_eval.sh"
note $? "fx blocks EVAL block carries the wait discipline verbatim"
# failure case: shard 2 php exits 1 -> block must abort
FX_FAIL=1 bash "$SB/run_eval.sh" > "$SB/eval2.out" 2>&1
rc=$?
[ $rc -ne 0 ] && grep -q 'ABORT: an eval shard failed' "$SB/eval2.out"
note $? "fx blocks EVAL failure case aborts via the FAIL flag"

# ---- LABEL ------------------------------------------------------------
extract LABEL "$SB/blk_label.sh"
for s in 0 1 2 3; do mkdir -p "/tmp/r10probe_l3_tree_$s"; done
for s in 0 1 2 3; do for p in 1 2; do
  echo '{"snap":"gA_t2","game":"gA","player":1}' \
    > "$SB/out/jobs_shard${s}_p$p.jsonl"
done; done
{ echo "$HARNESS_COMMON"; cat "$SB/blk_label.sh";
  echo 'echo LABEL_OK';
} > "$SB/run_label.sh"
: > "$CALLS"
bash "$SB/run_label.sh" > "$SB/label.out" 2>&1
rc=$?
nphp=$(grep -c '^PHP ' "$CALLS" || true)
[ $rc -eq 0 ] && grep -q LABEL_OK "$SB/label.out" && [ "$nphp" = 8 ]
note $? "fx blocks LABEL spawns 8 shard processes and waits clean"
FX_FAIL=1 bash "$SB/run_label.sh" > "$SB/label2.out" 2>&1
rc=$?
[ $rc -ne 0 ] && grep -q 'ABORT: a label shard failed' "$SB/label2.out"
note $? "fx blocks LABEL failure case aborts via the FAIL flag"

if [ "$FAILN" = 0 ]; then echo "fx_probe_blocks: ALL PASS";
else echo "fx_probe_blocks: $FAILN FAILURES"; fi
exit "$FAILN"
