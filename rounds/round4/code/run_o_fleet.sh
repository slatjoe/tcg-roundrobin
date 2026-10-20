#!/bin/bash
# Round-4 O-FLEET (Claude O1-O8 registration, claude-reply-38dd581
# sec.5): teacher vs raw v15, paired seeds, both seats, against an
# opponent the teacher's rollouts do NOT model.
#
# Design (O1): teacher = exactly the gate artifact (TEACHER_MODE=1
# plain: k=25, top-3 + any prior >= 0.10 cap 4, continuation va,
# overturn at 1.5 paired SE, R17 root state) vs raw v15, PAIRED
# seeds, BOTH seats, against BC2 served through the patched
# server's TCG_OPP_MIX ckptpath: path (O2). The teacher's rollouts
# are UNCHANGED: inside rollout children the opponent seat is
# played by the in-process v1 heuristic (SimLabel_V1Argmax) and
# eval requests are answered by the learner model only, so the
# teacher plans against the heuristic while the live opponent is
# BC2 - the misspecification is the measurement. The v15-mirror
# secondary is NOT registered (BC2 only, decided at registration).
#
# Layout: FOUR chunks (c1 2001-2050, c2 2051-2100, c3 2101-2150,
# c4 2151-2200). Within each chunk every seed runs at BOTH seats
# and both arms (balanced by construction): 200 seeds x 2 seats =
# 400 (seed, seat) units = 800 games. Chunk workers run in
# PARALLEL; each writes its own row files, manifests, stat files,
# traces, snapshots and game-id file (the registry source, merged
# before any analysis - O7).
#
# Servers: ONE patched server per seat for the whole fleet (R12
# pattern - distinct sockets, seat env), started by this script
# with TCG_OPP_MIX=ckptpath:<BC2>:1.0, readiness from the servers'
# own "listening on" lines, REAPED on exit (trap). O2 manifest:
# BOTH models' startup lines ("search model loaded" + "opp net
# loaded") from BOTH server logs are captured into
# o_server_lines.txt, and the BC2 weights sha256 is recorded next
# to them, before the first chunk starts. The driver pings each
# server and stamps its self-reported seat on every row (seat_ok).
#
# Timeout: O_TIMEOUT (default 700 placeholder). The LAUNCH value
# is set by the O4 formula - max(700, 3x the slowest game of the
# launch-phase 4-way concurrent teacher probe under BC2-opponent
# contention), exactly as the gate's 1600s was probe-set. Raw-arm
# wall timeouts get ONE re-run via gate_raw_retry.py, REUSED
# unchanged from the gate build (the retry re-runs rows against
# the same per-seat sockets; the opponent lives in the server's
# env, so no opponent-aware retry change exists to make). Teacher
# timeouts stand and are scored by the analysis (gate timeout
# ruling 2, carried by O5's "same bands").
#
# Teacher arms run with:
#   TEACHER_SNAP_DIR=<chunk-seat snaps>   (L3 overturn snapshots)
#   TCG_CLEAN_CHILDREN=1                  (per-game child cleanup)
#   GATE_GAME_IDS_FILE=<chunk ids file>   (paired_driver's env
#     name for the registry id source - the driver's interface,
#     kept verbatim; the FILES are o_-named)
# Both arms run with traces ON (L1/L2/G3-style audits are standard
# parts of the O analysis, O5).
#
# Shared memory (O7): ipcs -m | wc -l recorded before/after EACH
# chunk into o_ipcs.txt; the 3,600 operator stop applies (the
# operator watches the count during the run; a stopped fleet is
# INCONCLUSIVE, not partially readable). A G8 sweep precedes the
# launch (launch-phase step, not this script's job). The
# production server's sha256 is recorded before/after into
# o_prod_hash.txt. The tree's search.php at launch must be the
# gate build PLUS patch_decide_abort_log.py (expected sha256
# 8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61,
# scratch-verified in the O package); the wrapper that launches
# this script checks the tree hashes, as with the gate.
#
# Outputs under $O_OUT (default /tmp/o_fleet):
#   o_<chunk>_teacher_s<seat>.jsonl (+ .manifest.json)
#   o_<chunk>_raw_s<seat>.jsonl     (+ .manifest.json)
#   o_<chunk>_<arm>_s<seat>_log/    (search_stats, trace/)
#   o_<chunk>_teacher_s<seat>_snaps/ (overturn snapshots+index)
#   o_<chunk>_game_ids.txt
#   o_ipcs.txt, o_prod_hash.txt, o_server_s{1,2}.log,
#   o_server_lines.txt (O2 startup-line + weights-sha manifest)
set -u
PY=/home/joe/tcg/rl-env/bin/python
TREE=${O_TREE:-/tmp/otree_r1}
MODEL=/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt
OPP_CKPT=/home/joe/tcg/tcg-sim/bc2_out/bc_policy.pt
OUT=${O_OUT:-/tmp/o_fleet}
TIMEOUT=${O_TIMEOUT:-700}
PROD_SERVER=/home/joe/tcg/tcg-sim/rl/search_server.py
mkdir -p $OUT
cd $TREE

SRV_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
}
trap cleanup EXIT

start_server() {
  # $1 = seat, $2 = sock, $3 = log
  TCG_POLICY_SOCK=$2 TCG_LEARNER_SEAT=$1 SEARCH_MODEL=$MODEL \
  TCG_OPP_MIX=ckptpath:$OPP_CKPT:1.0 \
    $PY rl/search_server.py > $3 2>&1 &
  SRV_PIDS="$SRV_PIDS $!"
  for i in $(seq 1 60); do
    grep -q "listening on $2" $3 2>/dev/null && return 0
    sleep 2
  done
  echo "SERVER FAILED TO START (seat $1): $3" >&2
  return 1
}

echo "production server before: $(sha256sum $PROD_SERVER)" \
  > $OUT/o_prod_hash.txt
rm -f /tmp/o_s1.sock /tmp/o_s2.sock
start_server 1 /tmp/o_s1.sock $OUT/o_server_s1.log || exit 1
start_server 2 /tmp/o_s2.sock $OUT/o_server_s2.log || exit 1
# O2 manifest: BOTH models' startup lines from BOTH servers, plus
# the opponent weights sha, captured before any game runs. If the
# opp line is absent the launch wrapper must stop the fleet: the
# opponent would silently be the heuristic.
{
  echo "== learner model (both servers) =="
  grep -h "search model loaded" $OUT/o_server_s1.log $OUT/o_server_s2.log
  echo "== opponent model (both servers) =="
  grep -h "opp net loaded" $OUT/o_server_s1.log $OUT/o_server_s2.log
  echo "== opponent weights =="
  sha256sum $OPP_CKPT
  echo "== learner weights =="
  sha256sum $MODEL
} > $OUT/o_server_lines.txt
grep -q "opp net loaded" $OUT/o_server_lines.txt || {
  echo "OPPONENT MODEL NOT LOADED - see o_server_lines.txt" >&2
  exit 1
}

chunk_worker() {
  local chunk=$1 seeds=$2
  echo "before chunk $chunk: $(ipcs -m | wc -l)" \
    > $OUT/o_ipcs_${chunk}.txt
  for seat in 1 2; do
    TEACHER_SNAP_DIR=$OUT/o_${chunk}_teacher_s${seat}_snaps \
    TCG_CLEAN_CHILDREN=1 \
    GATE_GAME_IDS_FILE=$OUT/o_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/o_s${seat}.sock \
        --seat $seat --arm teacher --seeds $seeds --timeout $TIMEOUT \
        --out $OUT/o_${chunk}_teacher_s${seat}.jsonl \
        --logdir $OUT/o_${chunk}_teacher_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/o_${chunk}_game_ids.txt \
      $PY paired_driver.py --tree $TREE --sock /tmp/o_s${seat}.sock \
        --seat $seat --arm raw --seeds $seeds --timeout $TIMEOUT \
        --out $OUT/o_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/o_${chunk}_raw_s${seat}_log
    GATE_GAME_IDS_FILE=$OUT/o_${chunk}_game_ids.txt \
      $PY gate_raw_retry.py --tree $TREE --sock /tmp/o_s${seat}.sock \
        --seat $seat --timeout $TIMEOUT \
        --rows $OUT/o_${chunk}_raw_s${seat}.jsonl \
        --logdir $OUT/o_${chunk}_raw_s${seat}_log
  done
  echo "after chunk $chunk: $(ipcs -m | wc -l)" \
    >> $OUT/o_ipcs_${chunk}.txt
}

CHUNK_PIDS=""
chunk_worker c1 2001-2050 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c2 2051-2100 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c3 2101-2150 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c4 2151-2200 & CHUNK_PIDS="$CHUNK_PIDS $!"
# Wait on the chunk workers ONLY. A bare `wait` here would also
# wait on the two server processes (background children of this
# shell that never exit on their own), hanging the script forever
# after the chunks finish - the gate fleet's run_gate.sh fix,
# carried verbatim.
wait $CHUNK_PIDS

# Reap the per-seat servers explicitly now that the chunks are
# done, before the closing bookkeeping (the EXIT trap stays as a
# backstop).
for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null

cat $OUT/o_ipcs_c1.txt $OUT/o_ipcs_c2.txt \
    $OUT/o_ipcs_c3.txt $OUT/o_ipcs_c4.txt > $OUT/o_ipcs.txt
echo "production server after: $(sha256sum $PROD_SERVER)" \
  >> $OUT/o_prod_hash.txt
echo "ipcs after fleet: $(ipcs -m | wc -l)" >> $OUT/o_ipcs.txt
echo O-FLEET-DONE
