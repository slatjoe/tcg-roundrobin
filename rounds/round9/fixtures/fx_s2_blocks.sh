#!/bin/bash
# fx_s2_blocks - verbatim-extraction fixtures for EVERY
# spawn/wait block in the three Stage 2 runners (Claude's
# standing rule, a13cabc5 confirmation; the fx_b0_gate /
# fx_shard_supervision pattern). For each runner:
#   * the block inventory between "# BLOCK:<id>-BEGIN" and
#     "# BLOCK:<id>-END" markers must equal the expected
#     table below -- a spawn/wait block added without a
#     fixture fails here;
#   * no runner (nor this fixture's targets) may contain
#     the three-name assignment form `FAIL=0 pid` whose
#     top-level transplant killed the first Stage 1 launch
#     (see the package doc's fixture section);
#   * each extracted block is EXECUTED verbatim in a sandbox
#     with stubbed externals: server blocks must reach their
#     loaded-grep against a stub server AND abort against a
#     silent one; sweeper blocks must capture one PID per
#     tree; driver/shard blocks must run every worker and
#     FAIL when any worker fails.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
CODE="$FX/../code"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAIL=0
FX_STUB_MARKERS="$WORK/markers.txt"
FX_STUB_TAGFILE="$WORK/tag"
export FX_STUB_MARKERS FX_STUB_TAGFILE
note() { echo "$1"; }
bad() { echo "FAIL $1"; FAIL=1; }

# ---- stub python: behavior by argv --------------------------
mkdir -p "$WORK/stub"
cat > "$WORK/stub/py" <<'STUBEOF'
#!/bin/bash
# Stub for $PY. Server mode: print the load lines to stdout
# (the block redirects them to the log it greps). Sweeper
# mode: exit 0 at once. Driver mode: write a marker + row,
# exit per FX_STUB_FAIL_<TAG>.
for a in "$@"; do
  case "$a" in
    *search_server.py)
      [ -n "${FX_STUB_SILENT:-}" ] || {
        echo "search model loaded (/x/ckpt_v10.pt)"
        echo "ckpt_v10 served"; }
      exit 0;;
    *shm_sweep.py)
      echo "sweeper $$" >> "$FX_STUB_MARKERS"
      exit 0;;
    *paired_driver_gravy.py|*s2_label_main.php)
      tag=$(basename "$FX_STUB_TAGFILE")
      echo "worker $*" >> "$FX_STUB_MARKERS"
      # recover the block tag from the --out / MEAS_OUT arg
      for b in "$@"; do case "$b" in
        *games_*.jsonl) tag=$(basename "$b" .jsonl);;
        *pg_ghost_*.jsonl) tag=$(basename "$b" .jsonl);;
        *labels_shard*) tag=$(basename "$b" .jsonl);;
      esac; done
      eval "fv=\${FX_STUB_FAIL_$tag:-}"
      [ -n "$fv" ] && exit 1
      exit 0;;
    -)
      cat > /dev/null; exit 0;;
    *)
      exit 0;;
  esac
done
exit 0
STUBEOF
chmod +x "$WORK/stub/py"
# stub php for the L3 block's bare `php s2_label_main.php`:
# the worker tag comes from MEAS_OUT, as the runner sets it.
mkdir -p "$WORK/stubbin"
cat > "$WORK/stubbin/php" <<'STUBEOF'
#!/bin/bash
tag=$(basename "${MEAS_OUT:-none}" .jsonl)
echo "worker php $tag" >> "$FX_STUB_MARKERS"
eval "fv=\${FX_STUB_FAIL_$tag:-}"
[ -n "$fv" ] && exit 1
exit 0
STUBEOF
chmod +x "$WORK/stubbin/php"
# the L3 block cds into its shard trees; create them (and
# remove them again at the end).
for s in 0 1 2 3; do mkdir -p "/tmp/r9s2_l3_tree_$s"; done
sleep() { :; }   # sandbox: the wait loops spin on greps, not clocks
export -f sleep 2>/dev/null || true

extract() { # runner blockid -> file
  awk "/# BLOCK:$2-BEGIN/{f=1;next} /# BLOCK:$2-END/{f=0} f" "$1" > "$3"
  [ -s "$3" ]
}

run_block() { # name runner blockid extra_env...
  local name=$1 runner=$2 blk=$3; shift 3
  local bf="$WORK/blk_$blk.sh"
  extract "$runner" "$blk" "$bf" || { bad "$name extraction empty"; return; }
  : > "$FX_STUB_MARKERS"
  ( export PY="$WORK/stub/py" OUT="$WORK/out_$blk" CODE_DIR="$CODE" \
      SIM="$WORK/sim" GTREE="$WORK/gtree" CKPT="/x/ckpt_v10.pt" \
      PROD="$WORK/search_server.py" LABEL_BASE=955001 NSHARD=4 \
      GAME_TIMEOUT=3214 SRV_WAIT_TRIES=3 \
      PATH="$WORK/stubbin:$PATH" \
      FX_STUB_MARKERS FX_STUB_TAGFILE="$WORK/tag" "$@"
    mkdir -p "$OUT"
    # blocks reference per-block loop vars (seat/blk/s/spec)
    # and paths only; run the extracted text verbatim.
    bash "$bf" )
}

declare -A EXPECT=(
  [run_stage2_pregate.sh]="PS-SRV PS-SWEEP PS-GHOST"
  [run_stage2_games.sh]="GS-SRV GS-SWEEP GS-DRIVERS"
  [run_stage2_l3.sh]="LS-SRV LS-SWEEP LS-SHARD"
)
for runner in run_stage2_pregate.sh run_stage2_games.sh run_stage2_l3.sh; do
  if grep -n "FAIL=0 pid" "$CODE/$runner" > /dev/null; then
    bad "$runner contains the lethal three-name form"
  else
    note "PASS $runner: no three-name assignment form"
  fi
  got=$(grep -o "# BLOCK:[A-Z-]*-BEGIN" "$CODE/$runner" \
        | sed 's/# BLOCK://; s/-BEGIN//' | sort | tr '\n' ' ')
  want=$(echo "${EXPECT[$runner]}" | tr ' ' '\n' | sort | tr '\n' ' ')
  if [ "$got" = "$want" ]; then
    note "PASS $runner block inventory: $got"
  else
    bad "$runner block inventory: got [$got] want [$want]"
  fi
done

# ---- server blocks: loaded stub passes, silent stub aborts --
for pair in "run_stage2_pregate.sh PS-SRV" "run_stage2_games.sh GS-SRV" "run_stage2_l3.sh LS-SRV"; do
  set -- $pair
  if run_block "$2-ok" "$CODE/$1" "$2" > "$WORK/$2_ok.log" 2>&1; then
    note "PASS $2: stub server loads -> block completes"
  else
    bad "$2: stub server loads -> block failed"; sed -n 1,3p "$WORK/$2_ok.log"
  fi
  if FX_STUB_SILENT=1 run_block "$2-silent" "$CODE/$1" "$2" > "$WORK/$2_silent.log" 2>&1; then
    bad "$2: silent server -> block should have aborted"
  else
    note "PASS $2: silent server -> block aborts"
  fi
done

# ---- sweeper blocks: one PID per tree ------------------------
# (sweepers are fire-and-forget daemons by design -- the block
# does not wait for them -- so poll the marker file briefly
# for the count instead of reading it the instant the block
# returns.)
for pair in "run_stage2_pregate.sh PS-SWEEP 2" "run_stage2_games.sh GS-SWEEP 4" "run_stage2_l3.sh LS-SWEEP 4"; do
  set -- $pair
  run_block "$2" "$CODE/$1" "$2" > "$WORK/$2.log" 2>&1
  n=0
  for i in $(seq 1 100); do
    n=$(grep -c sweeper "$FX_STUB_MARKERS" 2>/dev/null || echo 0)
    [ "$n" -ge "$3" ] && break
    python3 -c "import time; time.sleep(0.05)"
  done
  if [ "$n" = "$3" ]; then
    note "PASS $2: $3 sweepers spawned"
  else
    bad "$2: sweeper spawn count (got $n, want $3)"
    sed -n 1,3p "$WORK/$2.log"
  fi
done

# ---- driver / shard blocks: all workers run; a failure fails -
run_workers() { # name runner blockid nworkers failtag
  local name=$1 runner=$2 blk=$3 n=$4 ftag=$5
  if run_block "$name" "$runner" "$blk" > "$WORK/$blk.log" 2>&1 \
     && [ "$(grep -c worker "$FX_STUB_MARKERS")" = "$n" ]; then
    note "PASS $name: $n workers ran, block completes"
  else
    bad "$name: happy path"; sed -n 1,3p "$WORK/$blk.log"
  fi
  if [ -n "$ftag" ]; then
    if FX_STUB_FAIL_$ftag=1 run_block "$name-fail" "$runner" "$blk" \
         > "$WORK/${blk}_fail.log" 2>&1; then
      bad "$name: a failing worker must fail the block"
    else
      note "PASS $name: a failing worker fails the block"
    fi
  fi
}
# env var indirection for the fail tag (bash dynamic names)
run_workers_env() { # name runner blockid n failvar
  local name=$1 runner=$2 blk=$3 n=$4 fvar=$5
  if run_block "$name" "$runner" "$blk" > "$WORK/$blk.log" 2>&1 \
     && [ "$(grep -c worker "$FX_STUB_MARKERS")" = "$n" ]; then
    note "PASS $name: $n workers ran, block completes"
  else
    bad "$name: happy path"; sed -n 1,3p "$WORK/$blk.log"
  fi
  if env "$fvar=1" run_block "$name-fail" "$runner" "$blk" \
       > "$WORK/${blk}_fail.log" 2>&1; then
    bad "$name: a failing worker must fail the block"
  else
    note "PASS $name: a failing worker fails the block"
  fi
}
run_workers_env "PS-GHOST" "$CODE/run_stage2_pregate.sh" PS-GHOST 2 FX_STUB_FAIL_pg_ghost_s1
run_workers_env "GS-DRIVERS" "$CODE/run_stage2_games.sh" GS-DRIVERS 4 FX_STUB_FAIL_games_s1a
run_workers_env "LS-SHARD" "$CODE/run_stage2_l3.sh" LS-SHARD 8 FX_STUB_FAIL_labels_shard0_p1

rmdir /tmp/r9s2_l3_tree_0 /tmp/r9s2_l3_tree_1 \
      /tmp/r9s2_l3_tree_2 /tmp/r9s2_l3_tree_3 2>/dev/null
echo "FX-S2-BLOCKS: $([ $FAIL = 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
