#!/bin/bash
# fx_shard_supervision - the runner's eval shard-supervision
# block (code/run_stage1.sh lines 343-386: the PIDS spawn /
# wait / FAIL-check / cat region), extracted verbatim and
# executed against stubs. This suite exists because the
# Stage 1 launch of 2026-10-26 died in exactly this block:
# line 343 read
#     PIDS="" FAIL=0 pid
# The stray token `pid` makes bash parse both assignments
# as environment for a nonexistent command, so PIDS is
# never set in the shell; the first `PIDS="$PIDS $!"`
# (line 380) then kills the shell under `set -u`
# (unbound variable), orphaning shard 0. No earlier
# fixture executed this block: fx_b0_gate extracts the
# gate AFTER supervision, fx_s1_eval drives the PHP
# driver standalone, and `bash -n` passes (the defect is
# runtime-only; the line is syntactically valid).
#
# The region extracted starts at the PIDS line - AFTER
# tree setup (the tree copies, expect_hash calls and
# start_sweeper invocations above it are not supervision;
# the fixture pre-creates the four tree dirs the block
# hardcodes) - and ends at the stats cat line, the last
# line of supervision proper (the "setting done" echo
# and the B0GATE block after it are other suites' scope).
# The block is run under `bash -u`, the runner's own
# mode (run_stage1.sh line 80: set -u).
#
# Stubs: a fake `php` first on PATH appends one planted
# row to $MEAS_OUT / $EVAL_STATS per invocation (tagged
# with the shard/player jobs-file name); it can be told
# to fail for one shard/player (FX_PHP_FAIL_ON) or to
# sleep (FX_PHP_SLOW_ON / FX_PHP_SLOW_S). $OUT holds a
# planted jobs_<NAME>.jsonl whose games hash (the block's
# own splitter: sha256(game) % NSHARD) across >= 2 shards
# with both players present.
#
# Cases:
#   1  happy path: all shards spawn, the wait covers
#      every spawned pid (a 3 s-per-call slow shard's
#      rows are IN the concatenated output, and elapsed
#      time proves the block waited), FAIL stays 0,
#      exit 0, concatenated evals/stats == the per-shard
#      sums.
#   2  one shard's php exits 1: the block prints the
#      ABORT line and exits 1 BEFORE concatenating.
#   3  the same fixture against the PRE-FIX block text
#      (the one token re-added to a temp copy of the
#      extraction): the block dies with "PIDS: unbound
#      variable" - the launch failure, reproduced. This
#      case PASSES when the old text dies; it is the
#      before/after proof the hole is closed.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$FX/../code/run_stage1.sh"
WORK="$(mktemp -d)"
FAIL=0
check() { # name condition...
  local name=$1; shift
  if "$@"; then echo "PASS $name"; else echo "FAIL $name"; FAIL=1; fi
}

# --- the four tree dirs the block hardcodes -------------
TREES_CREATED=""
for s in 0 1 2 3; do
  d="/tmp/r9s1_tree_e${s}"
  if [ ! -d "$d" ]; then mkdir -p "$d" && TREES_CREATED="$TREES_CREATED $d"; fi
done
cleanup() {
  rm -rf "$WORK"
  for d in $TREES_CREATED; do rm -rf "$d"; done
}
trap cleanup EXIT

# --- stub php --------------------------------------------
mkdir -p "$WORK/bin"
cat > "$WORK/bin/php" <<'STUBEOF'
#!/bin/bash
# Stub for s1_eval_main.php: one planted row per call.
if [ -n "${FX_PHP_FAIL_ON:-}" ]; then
  case "$(basename "$MEAS_JOBS")" in
    *"$FX_PHP_FAIL_ON"*)
      echo "stub php: planted failure for $MEAS_JOBS" >&2
      exit 1 ;;
  esac
fi
if [ -n "${FX_PHP_SLOW_ON:-}" ]; then
  case "$(basename "$MEAS_JOBS")" in
    *"$FX_PHP_SLOW_ON"*) sleep "${FX_PHP_SLOW_S:-3}" ;;
  esac
fi
printf '{"stub":"php","jobs":"%s"}\n' "$(basename "$MEAS_JOBS")" \
  >> "$MEAS_OUT"
printf '{"stub":"php","jobs":"%s"}\n' "$(basename "$MEAS_JOBS")" \
  >> "$EVAL_STATS"
exit 0
STUBEOF
chmod +x "$WORK/bin/php"

# --- extract the runner's own supervision block ----------
START=$(grep -n '^    PIDS="" FAIL=0$' "$RUNNER" | cut -d: -f1)
END=$(grep -n 'cat "\$OUT"/stats_' "$RUNNER" | head -1 | cut -d: -f1)
[ -n "$START" ] && [ -n "$END" ] && [ "$END" -gt "$START" ] \
  || { echo "FAIL extraction (block anchors not found)"; exit 1; }
sed -n "${START},${END}p" "$RUNNER" > "$WORK/block.sh"
echo "extracted runner lines $START-$END"
head -1 "$WORK/block.sh" | grep -qx '    PIDS="" FAIL=0'
check "extraction starts at the PIDS init line" test $? -eq 0
tail -1 "$WORK/block.sh" | grep -q 'stats_${NAME}.jsonl'
check "extraction ends at the stats cat line" test $? -eq 0
[ "$(wc -l < "$WORK/block.sh")" -eq $((END - START + 1)) ]
check "extraction is the full $((END - START + 1))-line region" test $? -eq 0
grep -q 'PIDS="$PIDS $!"' "$WORK/block.sh" \
  && grep -q 'wait "$pid"' "$WORK/block.sh" \
  && grep -q 'ABORT: an eval shard failed' "$WORK/block.sh" \
  && grep -q 'evals_${NAME}_shard' "$WORK/block.sh"
check "extraction carries spawn/wait/FAIL-check/cat verbatim" test $? -eq 0
grep -q 'B0GATE\|start_sweeper\|expect_hash' "$WORK/block.sh"
check "extraction excludes tree setup and the B0 gate" test $? -eq 1

# --- the pre-fix block: the one token re-added ------------
sed 's/^    PIDS="" FAIL=0$/    PIDS="" FAIL=0 pid/' \
  "$WORK/block.sh" > "$WORK/block_old.sh"
grep -qx '    PIDS="" FAIL=0 pid' "$WORK/block_old.sh"
check "pre-fix block reconstructed (stray token restored)" test $? -eq 0

# --- plant jobs: games hashing across >= 2 shards --------
plant_jobs() { # outdir
  python3 - "$1" <<'PYEOF'
import hashlib, json, sys
out = sys.argv[1]
games, i = [], 0
def shard(g):
    return int(hashlib.sha256(str(g).encode()).hexdigest(), 16) % 4
while len({shard(g) for g in games}) < 3 and i < 200:
    games.append(f"fxg{i}"); i += 1
assert len({shard(g) for g in games}) >= 2, "games cover < 2 shards"
jobs = [{"game": g, "player": p, "snap_dir": "/fx/" + g,
         "snap": g + "_t1", "branch": "P", "turn": 7}
        for g in games for p in (1, 2)]
with open(out + "/jobs_FXSET.jsonl", "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")
print(f"planted {len(jobs)} jobs over {len(games)} games, "
      f"shards {sorted({shard(g) for g in games})}")
PYEOF
}

run_block() { # blockfile outdir -> stdout+stderr; rc in $?
  ( env PATH="$WORK/bin:$PATH" PY=python3 OUT="$1" NAME=FXSET \
      NSHARD=4 HOOKS=4000 DEADLINE=180 HZENV=off HVAL=0 K=25 \
      DECK_REL=decks/fx_deck.txt \
      FX_PHP_FAIL_ON="${FX_PHP_FAIL_ON:-}" \
      FX_PHP_SLOW_ON="${FX_PHP_SLOW_ON:-}" \
      FX_PHP_SLOW_S="${FX_PHP_SLOW_S:-3}" \
      bash -u "$2" ) 2>&1
}

# --- case 1: happy path, with a slow shard ---------------
O1="$WORK/out1"; mkdir -p "$O1"; plant_jobs "$O1"
t0=$(date +%s)
out1=$(FX_PHP_SLOW_ON="shard3_" FX_PHP_SLOW_S=3 \
  run_block "$O1" "$WORK/block.sh"); rc1=$?
t1=$(date +%s)
[ $rc1 -eq 0 ]; check "case1 exit 0 (all shards supervised)" test $? -eq 0
[ "$(wc -l < "$O1/evals_FXSET.jsonl")" -eq 8 ]
check "case1 concatenated evals == 8 stub rows (4 shards x 2 players)" test $? -eq 0
[ "$(wc -l < "$O1/stats_FXSET.jsonl")" -eq 8 ]
check "case1 concatenated stats == 8 stub rows" test $? -eq 0
ntags=0
for s in 0 1 2 3; do for p in 1 2; do
  grep -q "shard${s}_p${p}" "$O1/evals_FXSET.jsonl" && ntags=$((ntags+1))
done; done
[ $ntags -eq 8 ]
check "case1 rows from EVERY shard present after the wait" test $? -eq 0
[ $((t1 - t0)) -ge 4 ]
check "case1 block waited for the slow shard (elapsed $((t1-t0))s >= 4s)" test $? -eq 0
python3 - "$O1" <<'PYEOF'
import glob, json, sys
rows = [json.loads(l) for p in glob.glob(sys.argv[1] + "/jobs_FXSET_shard*_p*.jsonl")
        for l in open(p) if l.strip()]
shards = {p.split("shard")[1][0] for p in glob.glob(sys.argv[1] + "/jobs_FXSET_shard*_p*.jsonl")
          if open(p).read().strip()}
assert len(shards) >= 2, f"job shards {shards}"
assert {r["player"] for r in rows} == {1, 2}
print(f"PASS case1 jobs split across {len(shards)} shards, both players")
PYEOF
[ $? -eq 0 ] || FAIL=1

# --- case 2: one shard's php fails ------------------------
O2="$WORK/out2"; mkdir -p "$O2"; plant_jobs "$O2"
out2=$(FX_PHP_FAIL_ON="shard1_p1" run_block "$O2" "$WORK/block.sh"); rc2=$?
[ $rc2 -eq 1 ]; check "case2 exit 1 (shard failure aborts the block)" test $? -eq 0
case "$out2" in *"ABORT: an eval shard failed for setting FXSET"*)
  echo "PASS case2 ABORT line names the failed setting" ;;
  *) echo "FAIL case2 output: $out2"; FAIL=1 ;; esac
[ ! -e "$O2/evals_FXSET.jsonl" ]
check "case2 no concatenation after a shard failure" test $? -eq 0

# --- case 3: the PRE-FIX block dies as the launch died ----
O3="$WORK/out3"; mkdir -p "$O3"; plant_jobs "$O3"
out3=$(run_block "$O3" "$WORK/block_old.sh"); rc3=$?
[ $rc3 -ne 0 ]; check "case3 PRE-FIX block exits non-zero" test $? -eq 0
case "$out3" in *"PIDS: unbound variable"*)
  echo "PASS case3 PRE-FIX block dies with 'PIDS: unbound variable' (the launch failure)" ;;
  *) echo "FAIL case3 output: $out3"; FAIL=1 ;; esac
case "$out3" in *"pid: command not found"*)
  echo "PASS case3 PRE-FIX block first reports the phantom 'pid' command" ;;
  *) echo "FAIL case3 output (no pid error): $out3"; FAIL=1 ;; esac
[ ! -e "$O3/evals_FXSET.jsonl" ]
check "case3 PRE-FIX block never reaches the concatenation" test $? -eq 0

echo "FX-SHARD-SUPERVISION: $([ $FAIL -eq 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
