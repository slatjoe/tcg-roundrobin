#!/bin/bash
# Round-10 Step 0 probe: SUPPLEMENTARY LABEL RECOVERY
# (fix pass 4, package doc sec.12). NOT a re-run of
# run_probe.sh -- a registered addendum to attempt 3,
# executed once, from attempt 3's preserved outputs.
#
# What happened: 10 jobs of the 646 in jobs_all.jsonl
# (snaps 540261752_t64..t73, game 540261752, class
# uncontested, shard 0 / player 2) carried z =
# Infinity as a bare token (invalid JSON, the
# pre-fix writer's output). The pre-fix
# s2_label_main.php loader dropped those lines
# silently; their worlds never ran; the analyze
# phase's world-count guard aborted on the first of
# them. Everything else in the run is intact.
#
# Fix pass 5 (package doc sec.13,
# claude-reply-9dae0e2 sec.2.2-2.3) adds two steps:
#   0. BEFORE anything else, the eval-completeness
#      assertion (eval_completeness.py) runs on the
#      box's eval_jobs.jsonl + evals_all.jsonl: the
#      eval phase used the same silent loader, and a
#      nonzero missing count aborts this recovery
#      before any extraction, merge or analysis;
#   4b. AFTER the report, the registered influence
#      read (probe_influence.py) runs over the
#      merged labels and writes probe_influence.txt
#      / .json beside the report; the recovery
#      manifest carries its file hashes and any
#      "buildable, single-game dependent" hold lines.
#
# Sec.14 amendment (package doc sec.14,
# claude-reply-28c2065 sec.3.1-3.4), which SUPERSEDES
# step 4 / 4b below where they conflict:
#   0b. After the completeness gate, the CAP-ALIGNED
#       eval rescoring (capalign_eval.py) runs on
#       the box's eval files and writes
#       $OUT/capalign/: per-state cap-aligned
#       classes, the reclassification (drop-outs /
#       newly qualifying), and the supplementary
#       job set for the newly qualifying states.
#       (The same outputs are published in the repo
#       at data/step0_capalign/, computed there from
#       the published rows; the recovery recomputes
#       them from the run's own files and the read
#       consumes the in-run copies.)
#   2b. The newly qualifying states (69 in the
#       published rescoring) are labeled in a second
#       invocation in the same tree under a FRESH
#       seed family: MEAS_SEED = 470055001 (the
#       label lattice at shard index 4; span at 69
#       jobs tops at 478,390,718 -- disjoint from
#       every family incl. the 970,055,001 family's
#       500 values; fx_seed_clearance enumerates).
#   4'. The analyze phase is the sec.14 read:
#       probe_label_analyze.py computes BOTH
#       scorings over the merged set (jobs_merged =
#       the 646 attempt-3 jobs + the supplementary
#       set; labels_merged = attempt-3 labels + the
#       10 + the newly qualifying), CAP-ALIGNED as
#       the registered primary with jobs grouped by
#       their cap-aligned classes -- dropped-out
#       jobs are excluded from the cap-aligned read
#       and listed in the manifest; probe_report.py
#       decides on the cap-aligned summary and
#       prints the as-run report as a labeled
#       co-report; probe_influence.py runs its LOGO
#       and hold rule on the cap-aligned read.
#       The 10-job extraction, supplementary
#       labeling and merge stay as ONE step
#       (sec.3.4): all labels merge before any read.
#   Disclosure (also in the manifest): the
#   supplementary labels (the 10 + the newly
#   qualifying) run under the sec.14-FIXED search
#   file (1c964160...) installed in the label tree,
#   while attempt 3's 636 jobs ran the as-built
#   bytes. Under cap-aligned scoring the two are
#   commensurable -- the fixed engine's worlds are
#   cap-aligned by construction (decisive only by
#   turn 61, horizon flagged at the trigger) -- and
#   the as-run co-report is labeled accordingly.
#
# This script:
#   1. extracts exactly those 10 jobs from
#      jobs_all.jsonl (Python's json is the one
#      reader in the chain that accepts the bare
#      token, so the rows are recovered whole) and
#      rewrites them in the FIXED writer's shape
#      (z = 999.0 sentinel + "z_nonfinite": true)
#      as jobs_supp.jsonl;
#   2. labels ONLY them, with the fixed loader, at
#      the registered label tuple, in one label
#      tree, under a FRESH seed family:
#      MEAS_SEED = 970055001 (the label family's
#      base lattice at shard index 9 -- no such
#      shard exists; the enumeration in sec.12
#      shows the family's 500 seed values interval-
#      disjoint from every realized and planned
#      family, the eval family's worst planned span
#      topping out 308,554,590 below the base);
#   3. asserts the fixed loader's own jobs=10 line
#      and exactly 50 rows per (snap, candidate)
#      BEFORE merging;
#   4. merges labels_all.jsonl + labels_supp.jsonl
#      into labels_merged.jsonl and runs the
#      registered analyze phase (probe_label_
#      analyze.py + probe_report.py) over the
#      merged set, writing label_read.* and
#      probe_report.* in OUT (superseding the
#      aborted analyze; the abort line is preserved
#      in the published data/step0/label_read.txt);
#   5. writes recovery_manifest.json (input/output
#      hashes, seed base, the 10 snaps, the
#      disclosure text the probe report carries).
#
# Refuses to run if its outputs already exist (the
# recovery is single-shot) or if any input is
# missing. Same pin discipline, free-space form, G8
# sweep and (C) sweeper as run_probe.sh.
#
# Env: PROBE_OUT (default /home/joe/tcg/r10probe_out),
# GTREE (the canonical source tree; the launches
# pass /tmp/gravytree), PHP, PY -- as run_probe.sh.
set -u
CODE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT=${PROBE_OUT:-/home/joe/tcg/r10probe_out}
GTREE=${GTREE:-/home/joe/tcg/gravytree}
PY=${PY:-/home/joe/tcg/rl-env/bin/python}
PHP=${PHP:-php}
CKPT=${CKPT:-/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt}
PROD=${PROD:-/home/joe/tcg/tcg-sim/rl/search_server.py}
SETTINGS="$CODE_DIR/settings_probe.json"
SRV_WAIT_TRIES=${SRV_WAIT_TRIES:-120}
SUPP_SEED=970055001
SUPP_SEED_B=470055001
mkdir -p "$OUT"

expect_hash() {
  local got
  got=$(sha256sum "$1" | cut -d' ' -f1)
  if [ "$got" != "$2" ]; then
    echo "ABORT: $3: sha256 $got != expected $2" >&2
    return 1
  fi
}

# --- pins (the files this script executes) ---------------------------
expect_hash "$CODE_DIR/s2_label_main.php" \
  1c1dfd9f9349e8db815f23e31637dee558a9ec36e09179142f71748a6bce72aa \
  "recovery s2_label_main.php (round-9 + r10 fix-pass-4 loud loader)" || exit 1
expect_hash "$CODE_DIR/search_s2.php" \
  1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8 \
  "recovery search_s2.php (sec.14 horizon-aligned; label tree)" || exit 1
expect_hash "$CODE_DIR/probe_label_analyze.py" \
  131661e877bfd67b412b65609e74f69ad8ddfbf1dee50d5aa6fc8b19f896e927 \
  "recovery probe_label_analyze.py (sec.14: dual read -- cap-aligned primary via --capalign-classes, as-run co-report; fix-pass-5 module-level job_diffs/per_game_gain)" || exit 1
expect_hash "$CODE_DIR/eval_completeness.py" \
  4d7d38b7df523213251b0a37aa96667fe0419688db4733beb18cd1b11e24e0b6 \
  "recovery eval_completeness.py (fix pass 5)" || exit 1
expect_hash "$CODE_DIR/capalign_eval.py" \
  7a9d27891e9a2c83bafab5de0f2feb1da59a38c14fb406d726874a2ba1426999 \
  "recovery capalign_eval.py (sec.14: cap-aligned eval rescoring + reclassification + supplementary jobs)" || exit 1
expect_hash "$CODE_DIR/probe_influence.py" \
  83f4f1d1ed496cb95619e7c960626ca07e2896e15522e5b93a26154ad90275ab \
  "recovery probe_influence.py (sec.14: LOGO + hold on the cap-aligned read; by-61 inspection split)" || exit 1
expect_hash "$CODE_DIR/probe_report.py" \
  868be99240174e774d114d23283de2eb7c3be135deb854b9ecafa1bb2de4b28e \
  "recovery probe_report.py (sec.14: cap-aligned primary via --capalign-summary, as-run co-report)" || exit 1
expect_hash "$CODE_DIR/settings_probe.json" \
  5af0c715442e8d7208e89da9f197dfc458a55aef22182b551f64d7f3eedca2bb \
  "recovery settings_probe.json (decision rule + bar)" || exit 1
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "recovery stage0_report.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 \
  "recovery analyze_l3.py (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/g8_sweep2.sh" \
  d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17 \
  "recovery g8_sweep2.sh (round-9 byte-identical)" || exit 1
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "recovery shm_sweep.py (round-9 byte-identical)" || exit 1

# --- preconditions -----------------------------------------------------
for f in jobs_all.jsonl labels_all.jsonl \
         eval_jobs_report.json eval_summary.json \
         eval_jobs.jsonl evals_all.jsonl \
         eval_states.jsonl cap_s1_b1.jsonl \
         cap_s2_b1.jsonl; do
  [ -f "$OUT/$f" ] || {
    echo "ABORT: recovery input $OUT/$f is missing" >&2; exit 1; }
done
for f in jobs_supp.jsonl labels_supp.jsonl \
         labels_merged.jsonl recovery_manifest.json \
         eval_completeness.txt eval_completeness.json \
         probe_influence.txt probe_influence.json \
         jobs_suppB.jsonl labels_suppB.jsonl \
         label_stats_suppB.jsonl jobs_merged.jsonl \
         capalign; do
  [ ! -e "$OUT/$f" ] || {
    echo "ABORT: recovery output $OUT/$f already exists -- the recovery is single-shot" >&2; exit 1; }
done

# --- eval completeness assertion (fix pass 5, sec.2.2) ------------------
# The eval phase ran on the same silent loader as the
# label phase. Before anything is extracted, merged or
# analyzed, assert from the run's own files that every
# eval job produced world rows for every selected
# candidate. A nonzero missing count stops the
# recovery here and goes back to review.
$PY "$CODE_DIR/eval_completeness.py" \
  --eval-jobs "$OUT/eval_jobs.jsonl" \
  --evals "$OUT/evals_all.jsonl" \
  --json-out "$OUT/eval_completeness.json" \
  > "$OUT/eval_completeness.txt" || {
  echo "ABORT: eval completeness assertion failed -- the recovery stops before any extraction, merge or analysis (see eval_completeness.txt)" >&2; exit 1; }

# --- cap-aligned rescoring (sec.14, step 0b) -----------------------------
# Recompute the cap-aligned eval rescoring from the
# run's own files (the repo carries the same outputs
# at data/step0_capalign/, computed from the
# published rows; capalign_eval.py verifies its
# as-run mirror against the published states before
# emitting anything and aborts on a mismatch). The
# read below consumes THESE in-run copies: the class
# map, the states (cap-aligned z), the summary, and
# the supplementary job set for the newly qualifying
# states.
$PY "$CODE_DIR/capalign_eval.py" \
  --jobs "$OUT/eval_jobs.jsonl" \
  --rows "$OUT/evals_all.jsonl" \
  --states-published "$OUT/eval_states.jsonl" \
  --summary-published "$OUT/eval_summary.json" \
  --label-jobs "$OUT/jobs_all.jsonl" \
  --settings "$SETTINGS" \
  --out-dir "$OUT/capalign" \
  > "$OUT/capalign.txt" || {
  echo "ABORT: cap-aligned rescoring failed (see capalign.txt)" >&2; exit 1; }
cp "$OUT/capalign/supplementary_jobs.jsonl" \
   "$OUT/jobs_suppB.jsonl"

# --- free-space pre-flight (one tree) -----------------------------------
PER_TREE=$(du -sb "$GTREE" | cut -f1)
AVAILABLE=$(df -B1 /tmp | tail -1 | awk '{print $4}')
echo "free-space pre-flight: required_bytes=$PER_TREE (per-tree x 1 tree) available_bytes=$AVAILABLE headroom_factor=1.25"
if [ $((AVAILABLE * 4)) -lt $((PER_TREE * 5)) ]; then
  echo "ABORT: free-space pre-flight: available_bytes=$AVAILABLE < required_bytes=$PER_TREE x 1.25" >&2
  exit 1
fi

# --- extract the 10 dropped jobs, in the fixed writer's shape -----------
$PY - "$OUT" <<'PYEOF' || exit 1
import json, math, sys
out = sys.argv[1]
want = ["540261752_t%d" % t for t in range(64, 74)]
rows = [json.loads(l) for l in open(out + "/jobs_all.jsonl")
        if l.strip()]
sel = [j for j in rows if str(j["snap"]) in want]
assert len(sel) == 10, \
    "expected exactly the 10 registered jobs, found %d" % len(sel)
for j in sel:
    assert str(j["game"]) == "540261752", j["snap"]
    assert j["probe_band"] == "uncontested", j["snap"]
    assert not math.isfinite(j["z"]), j["snap"]
    # the fixed writer's shape (build_probe_jobs.py,
    # fix pass 4): finite sentinel + the flag.
    j["z"] = 999.0
    j["z_nonfinite"] = True
with open(out + "/jobs_supp.jsonl", "w") as f:
    for j in sel:
        f.write(json.dumps(j, allow_nan=False) + "\n")
print("recovery extraction: %d jobs -> jobs_supp.jsonl"
      % len(sel))
PYEOF

# --- servers + sweeper (run_probe.sh's machinery, verbatim form) --------
SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

start_sweeper() {
  # $1 = tree, $2 = tag
  ipcs -m > "$OUT/ipcs_$2.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$2.txt" > "$OUT/shm_start_$2.txt"
  rm -f "$OUT/shm_sweep_$2.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$2.log" \
    --start-file "$OUT/shm_start_$2.txt" \
    --games-dir "$1/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_$2.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}

start_servers() {
  for seat in 1 2; do
    TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
      SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
      setsid nohup $PY "$PROD" > "$OUT/prod_s${seat}.log" 2>&1 < /dev/null &
    SRV_PIDS="$SRV_PIDS $!"
  done
  for seat in 1 2; do
    for i in $(seq 1 $SRV_WAIT_TRIES); do
      grep -q 'search model loaded' "$OUT/prod_s${seat}.log" 2>/dev/null && break
      sleep 1
    done
    grep -q 'search model loaded' "$OUT/prod_s${seat}.log" || {
      echo "ABORT: production server seat $seat did not load" >&2; exit 1; }
    grep -q 'ckpt_v10' "$OUT/prod_s${seat}.log" || {
      echo "ABORT: production server seat $seat loaded the wrong model" >&2; exit 1; }
  done
}

bash "$CODE_DIR/g8_sweep2.sh" "$OUT/g8_recovery" || exit 1
start_servers
tree="/tmp/r10probe_rec_tree_0"
rm -rf "$tree"; cp -r "$GTREE" "$tree"
find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
cp "$CODE_DIR/search_s2.php" "$tree/search.php"
cp "$CODE_DIR/s2_label_main.php" "$tree/"
expect_hash "$tree/search.php" \
  1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8 \
  "recovery tree search.php (sec.14 search_s2)" || exit 1
start_sweeper "$tree" "rec"

# --- label ONLY the 10, under the fresh seed family ---------------------
DECK_REL="decks/nats2026_eriksen_gravy_60.txt"
: > "$OUT/labels_supp.jsonl"
: > "$OUT/label_stats_supp.jsonl"
(cd "$tree" && MEAS_JOBS="$OUT/jobs_supp.jsonl" \
   MEAS_OUT="$OUT/labels_supp.jsonl" \
   EVAL_STATS="$OUT/label_stats_supp.jsonl" \
   MEAS_SEED=$SUPP_SEED \
   TCG_POLICY_SOCK="$OUT/prod_s2.sock" \
   EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
   EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
   EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
   $PHP s2_label_main.php \
     "$tree/$DECK_REL" "$tree/$DECK_REL" \
     --policy-search --games 1 \
     > "$OUT/label_supp.err" 2>&1) || exit 1
touch "$OUT/shm_sweep_rec.stop"
grep -q "s2 label jobs=10 " "$OUT/label_supp.err" || {
  echo "ABORT: the supplementary loader did not load exactly 10 jobs (see label_supp.err)" >&2; exit 1; }
grep -q "S2-LABEL-DONE" "$OUT/label_supp.err" || {
  echo "ABORT: supplementary labeling did not complete (see label_supp.err)" >&2; exit 1; }

# --- world-count pre-check BEFORE merging -------------------------------
$PY - "$OUT" <<'PYEOF' || exit 1
import json, sys
from collections import Counter
out = sys.argv[1]
jobs = [json.loads(l) for l in open(out + "/jobs_supp.jsonl")
        if l.strip()]
rows = [json.loads(l) for l in open(out + "/labels_supp.jsonl")
        if l.strip()]
cnt = Counter((str(r["snap"]), int(r["cand"])) for r in rows)
for j in jobs:
    for cand in (int(j["teacher_pick"]), int(j["prior_pick"])):
        n = cnt.get((str(j["snap"]), cand), 0)
        assert n == 50, \
            "job %s candidate %d has %d rows, expected 50" \
            % (j["snap"], cand, n)
print("recovery world-count pre-check OK: %d jobs x 2 "
      "candidates x 50 worlds = %d rows"
      % (len(jobs), len(rows)))
PYEOF

# --- label the newly qualifying states (sec.14, step 2b) ------------------
# Same tree, same tuple, second invocation, fresh
# seed family (470,055,001). The job set is
# capalign_eval.py's supplementary_jobs.jsonl
# (copied to jobs_suppB.jsonl above); its count is
# read from the file, never assumed.
SUPPB_N=$($PY -c "import sys; print(sum(1 for l in open(sys.argv[1]) if l.strip()))" "$OUT/jobs_suppB.jsonl")
start_sweeper "$tree" "recB"
: > "$OUT/labels_suppB.jsonl"
: > "$OUT/label_stats_suppB.jsonl"
(cd "$tree" && MEAS_JOBS="$OUT/jobs_suppB.jsonl" \
   MEAS_OUT="$OUT/labels_suppB.jsonl" \
   EVAL_STATS="$OUT/label_stats_suppB.jsonl" \
   MEAS_SEED=$SUPP_SEED_B \
   TCG_POLICY_SOCK="$OUT/prod_s2.sock" \
   EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
   EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
   EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
   $PHP s2_label_main.php \
     "$tree/$DECK_REL" "$tree/$DECK_REL" \
     --policy-search --games 1 \
     > "$OUT/label_suppB.err" 2>&1) || exit 1
touch "$OUT/shm_sweep_recB.stop"
grep -q "s2 label jobs=$SUPPB_N " "$OUT/label_suppB.err" || {
  echo "ABORT: the supplementary-B loader did not load exactly $SUPPB_N jobs (see label_suppB.err)" >&2; exit 1; }
grep -q "S2-LABEL-DONE" "$OUT/label_suppB.err" || {
  echo "ABORT: supplementary-B labeling did not complete (see label_suppB.err)" >&2; exit 1; }
$PY - "$OUT" <<'PYEOF' || exit 1
import json, sys
from collections import Counter
out = sys.argv[1]
jobs = [json.loads(l) for l in open(out + "/jobs_suppB.jsonl")
        if l.strip()]
rows = [json.loads(l) for l in open(out + "/labels_suppB.jsonl")
        if l.strip()]
cnt = Counter((str(r["snap"]), int(r["cand"])) for r in rows)
for j in jobs:
    for cand in (int(j["teacher_pick"]), int(j["prior_pick"])):
        n = cnt.get((str(j["snap"]), cand), 0)
        assert n == 50, \
            "job %s candidate %d has %d rows, expected 50" \
            % (j["snap"], cand, n)
print("recovery-B world-count pre-check OK: %d jobs x 2 "
      "candidates x 50 worlds = %d rows"
      % (len(jobs), len(rows)))
PYEOF

# --- merge + the sec.14 read ----------------------------------------------
# jobs_merged: the 646 attempt-3 jobs VERBATIM (the
# ten keep their original bare-Infinity lines --
# Python readers accept them, probe_influence.py's
# inspection selects the ten by exactly that
# non-finite z, and the PHP loader never sees this
# file) + the supplementary set appended.
cat "$OUT/jobs_all.jsonl" "$OUT/jobs_suppB.jsonl" \
  > "$OUT/jobs_merged.jsonl"
cat "$OUT/labels_all.jsonl" "$OUT/labels_supp.jsonl" \
    "$OUT/labels_suppB.jsonl" \
  > "$OUT/labels_merged.jsonl"
$PY "$CODE_DIR/probe_label_analyze.py" \
  --jobs "$OUT/jobs_merged.jsonl" \
  --labels "$OUT/labels_merged.jsonl" \
  --capture-games "$OUT/eval_jobs_report.json" \
  --settings "$SETTINGS" \
  --capalign-classes "$OUT/capalign/capalign_classes.json" \
  --capalign-states "$OUT/capalign/capalign_states.jsonl" \
  --json-out "$OUT/label_read.json" \
  > "$OUT/label_read.txt" || exit 1
$PY "$CODE_DIR/probe_report.py" \
  --eval-summary "$OUT/eval_summary.json" \
  --eval-jobs-report "$OUT/eval_jobs_report.json" \
  --label-read "$OUT/label_read.json" \
  --settings "$SETTINGS" \
  --capalign-summary "$OUT/capalign/capalign_summary.json" \
  --json-out "$OUT/probe_report.json" \
  > "$OUT/probe_report.txt" || exit 1

# --- the registered influence read (fix pass 5, sec.2.3; sec.14: on the
# --- cap-aligned read) -----------------------------------------------------
$PY "$CODE_DIR/probe_influence.py" \
  --jobs "$OUT/jobs_merged.jsonl" \
  --labels "$OUT/labels_merged.jsonl" \
  --capture-games "$OUT/eval_jobs_report.json" \
  --settings "$SETTINGS" \
  --eval-jobs "$OUT/eval_jobs.jsonl" \
  --evals "$OUT/evals_all.jsonl" \
  --eval-states "$OUT/eval_states.jsonl" \
  --driver-rows "$OUT/cap_s1_b1.jsonl" \
    "$OUT/cap_s2_b1.jsonl" \
  --report-json "$OUT/probe_report.json" \
  --capalign-classes "$OUT/capalign/capalign_classes.json" \
  --json-out "$OUT/probe_influence.json" \
  > "$OUT/probe_influence.txt" || exit 1

# --- recovery manifest ----------------------------------------------------
$PY - "$OUT" "$SUPP_SEED" "$SUPP_SEED_B" <<'PYEOF' || exit 1
import hashlib, json, os, sys
out, seed = sys.argv[1], int(sys.argv[2])
seed_b = int(sys.argv[3])
names = ["jobs_all.jsonl", "labels_all.jsonl",
         "jobs_supp.jsonl", "labels_supp.jsonl",
         "label_stats_supp.jsonl", "labels_merged.jsonl",
         "label_read.json", "probe_report.json",
         "eval_completeness.json",
         "probe_influence.json", "probe_influence.txt",
         "jobs_suppB.jsonl", "labels_suppB.jsonl",
         "label_stats_suppB.jsonl", "jobs_merged.jsonl",
         "capalign/capalign_states.jsonl",
         "capalign/capalign_summary.json",
         "capalign/capalign_classes.json",
         "capalign/capalign_reclassification.json",
         "capalign/supplementary_jobs_report.json"]
infl = json.load(open(os.path.join(
    out, "probe_influence.json")))
recl = json.load(open(os.path.join(
    out, "capalign",
    "capalign_reclassification.json")))
lread = json.load(open(os.path.join(
    out, "label_read.json")))
supp_b = [json.loads(l)["snap"] for l in open(
    os.path.join(out, "jobs_suppB.jsonl")) if l.strip()]
man = {"supplementary_meas_seed": seed,
       "supplementary_jobs": ["540261752_t%d" % t
                              for t in range(64, 74)],
       "disclosure": (
           "10 of the 646 label jobs (snaps "
           "540261752_t64..t73) were labeled in a "
           "supplementary run after the pre-fix loader "
           "silently dropped their invalid-JSON lines "
           "(z = Infinity); their worlds ran under "
           "fresh seed family MEAS_SEED = 970055001. "
           "All other jobs labeled in the original "
           "run. See the package doc sec.12."),
       "eval_completeness": json.load(open(
           os.path.join(out,
                        "eval_completeness.json")))[
           "missing_states"],
       "influence_hold_lines": infl["hold_lines"],
       "single_game_dependent": [
           lever for lever, h in infl["hold"].items()
           if h["hold"]],
       "sec14": {
           "scoring": (
               "CAP-ALIGNED is the registered primary "
               "(package doc sec.14): a finished world "
               "is decisive only if it ended by turn "
               "61; the probe report's decision rule, "
               "the label read's primary gains and "
               "the influence read's LOGO and hold "
               "rule all run on the cap-aligned "
               "scoring. The as-run scoring is "
               "co-reported, labeled, in label_read "
               "and probe_report."),
           "supplementary_meas_seed_b": seed_b,
           "supplementary_jobs_b": supp_b,
           "supplementary_jobs_b_count": len(supp_b),
           "dropped_jobs": recl["dropouts"],
           "dropped_jobs_count":
               recl["dropout_count"],
           "capaligned_excluded_jobs":
               lread["capaligned"]["excluded_jobs"],
           "disclosure": (
               "The supplementary labels (the 10 "
               "recovered jobs and the newly "
               "qualifying set) ran under the sec.14-"
               "fixed search file (search_s2.php "
               "1c964160...) installed in the label "
               "tree; attempt 3's 636 jobs ran the "
               "as-built bytes. Under cap-aligned "
               "scoring the two are commensurable -- "
               "the fixed engine's worlds are "
               "cap-aligned by construction. The "
               "dropped-out jobs above were labeled "
               "(or recovered) and merged like every "
               "other job, then excluded from the "
               "cap-aligned read because their states "
               "no longer qualify under the aligned "
               "scoring; they remain in the as-run "
               "co-report's job set.")},
       "files": {}}
for fn in names:
    p = os.path.join(out, fn)
    man["files"][fn] = hashlib.sha256(
        open(p, "rb").read()).hexdigest()
with open(os.path.join(out, "recovery_manifest.json"),
          "w") as f:
    json.dump(man, f, indent=1)
print("recovery manifest written")
PYEOF
echo "RECOVERY DONE"
