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
  85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
  "recovery search_s2.php (round-9 byte-identical; label tree)" || exit 1
expect_hash "$CODE_DIR/probe_label_analyze.py" \
  60935aec0b75873584a73950d5b9921ea3ef93bdac80cc97f857177fdc687bfc \
  "recovery probe_label_analyze.py" || exit 1
expect_hash "$CODE_DIR/probe_report.py" \
  82856c6f59cdd910f9d2f771b43da4a8b865f72c326499b2a6eb7c6603d1a81a \
  "recovery probe_report.py" || exit 1
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
         eval_jobs_report.json eval_summary.json; do
  [ -f "$OUT/$f" ] || {
    echo "ABORT: recovery input $OUT/$f is missing" >&2; exit 1; }
done
for f in jobs_supp.jsonl labels_supp.jsonl \
         labels_merged.jsonl recovery_manifest.json; do
  [ ! -e "$OUT/$f" ] || {
    echo "ABORT: recovery output $OUT/$f already exists -- the recovery is single-shot" >&2; exit 1; }
done

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
  85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa \
  "recovery tree search.php (stock search_s2)" || exit 1
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

# --- merge + the registered analyze phase -------------------------------
cat "$OUT/labels_all.jsonl" "$OUT/labels_supp.jsonl" \
  > "$OUT/labels_merged.jsonl"
$PY "$CODE_DIR/probe_label_analyze.py" \
  --jobs "$OUT/jobs_all.jsonl" --labels "$OUT/labels_merged.jsonl" \
  --capture-games "$OUT/eval_jobs_report.json" \
  --settings "$SETTINGS" \
  --json-out "$OUT/label_read.json" \
  > "$OUT/label_read.txt" || exit 1
$PY "$CODE_DIR/probe_report.py" \
  --eval-summary "$OUT/eval_summary.json" \
  --eval-jobs-report "$OUT/eval_jobs_report.json" \
  --label-read "$OUT/label_read.json" \
  --settings "$SETTINGS" \
  --json-out "$OUT/probe_report.json" \
  > "$OUT/probe_report.txt" || exit 1

# --- recovery manifest ----------------------------------------------------
$PY - "$OUT" "$SUPP_SEED" <<'PYEOF' || exit 1
import hashlib, json, os, sys
out, seed = sys.argv[1], int(sys.argv[2])
names = ["jobs_all.jsonl", "labels_all.jsonl",
         "jobs_supp.jsonl", "labels_supp.jsonl",
         "label_stats_supp.jsonl", "labels_merged.jsonl",
         "label_read.json", "probe_report.json"]
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
