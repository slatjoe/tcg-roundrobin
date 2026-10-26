#!/bin/bash
# Round-9 Stage 1 - calibration (design sec.4 as settled by
# claude-reply-16f02e2 sec.4): fresh capture, a 240-state
# contested panel, and the six-setting bounds grid evaluated
# offline at fleet contention, read by the registered
# selection rule.
#
# *** REVIEW-GATED - DO NOT RUN ***
# Launches only on Claude's code review of this Stage-1
# package at its committed sha and Joe's explicit go for
# Stage 1. The ghost pre-gate (ruling sec.4.6) is a Stage-2
# prerequisite, NOT part of this runner.
#
# Shape:
#   * CAPTURE: 40 raw-v10 games vs the heuristic, Gravy
#     mirror, instrument 87/62, seeds 21001-21040 (seat 1:
#     21001-21020, seat 2: 21021-21040) in per-stream copies
#     of the fleet tree (search.php 8f6b35da...), capture arm
#     (snapshot every contested decision, prior pick played,
#     no rollouts - the round-8 capture pattern). The paired
#     driver's own per-arm assertions must pass or the run
#     aborts. Extension blocks (BLOCK=2,3,...) add 10 games
#     each (5 per seat, seeds 21041+) and re-enter at the
#     panel phase; the driver skips seeds already played.
#   * REGISTRY: every capture game id is merged into the
#     do-not-train registry (tag r9s1_capture) before the
#     panel is built - registry discipline as standing.
#   * PANEL: build_panel.py over the capture streams in run
#     order: the first 240 contested snapshots, at most 8
#     per game. A shortfall exits 3 - the registered
#     response is another capture block, never a quiet
#     short panel.
#   * EVAL: each panel state is evaluated under ALL SIX
#     settings of settings_stage1.json, in file order - B0
#     (the fleet control) FIRST, pricing the rest. Per
#     setting: per-shard copies of the fleet tree with
#     search.php replaced by the clause-8 parameterized
#     build (code/search_s1.php; diff in the package
#     fixtures) and s1_eval_main.php as the driver. The full
#     setting tuple is env-pinned AND stamped into every
#     job copy; the driver aborts on any mismatch before
#     evaluating (clause 8, first placement). STOP
#     CONDITION (ruling sec.4.4): B0 is the smoke -- if
#     B0's pass aborts, or B0's rows fail any analyzer
#     integrity check (the B0 gate at the end of B0's
#     iteration, below), the runner stops BEFORE the +H
#     settings rather than continuing in file order.
#     Worlds W=25
#     per candidate, pair "va", production server, 4 shards
#     by game = the fleet's 4-way contention; each setting
#     runs its own deadline (the build's per-candidate
#     parent deadline IS the setting's deadline_s). Eval
#     seed bases 885001 + shard x 10^8 (settings constants).
#   * ANALYZE: stage1_analyze.py audits every row's tuple
#     stamp against settings_stage1.json (clause 8, second
#     placement) and reads completion (PER-STATE, the
#     selection metric: a state completes iff every
#     selected candidate reaches the validity floor; the
#     candidate-level rate and the pooled finished share
#     are diagnostics only), thin-prior beside the fleet's
#     31.7%, per-decision wall mean/p95/max, and the
#     overturn co-reports under both draw valuations
#     (draw = 0 primary per ruling sec.3; 0.5 co-reported).
#     Selection: cheapest qualifier (mean wall; ties p95,
#     then max) among the +H settings at per-state
#     completion >= 0.95 -- B0 is the control: read and
#     reported, never selected -- else NO CALIBRATED
#     SETTING and the round stops.
#   * Containment: pre-launch G8 sweep, then one (C)
#     kernel-attribution sweeper per tree, as standing.
#
# Phases (env PHASE): capture | panel | eval | analyze |
# all (default). SETTINGS=<name> restricts the eval phase
# to one setting (its stats/rows are still complete-panel).
# Outputs in $OUT: cap_* stream files + manifests,
# panel_jobs.jsonl + panel_report.json, jobs_<setting>.jsonl,
# evals_<setting>.jsonl, stats_<setting>.jsonl,
# stage1_report.{txt,json}, deployed_code_hashes.txt,
# stage1_manifest.json, streams.txt.
set -u
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CODE_DIR=${CODE_DIR:-/home/joe/tcg/round9_code}
OUT=${STAGE1_OUT:-/home/joe/tcg/r9s1_out}
GTREE=${GTREE_SRC:-/tmp/gravytree}
REG=${REGISTRY:-/home/joe/tcg/registry-vault/do_not_train_registry.json}
VAULT=/home/joe/tcg/registry-vault
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
NSHARD=4
PHASE=${PHASE:-all}
BLOCK=${BLOCK:-1}
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
$PY - "$REG" <<'PYEOF' || exit 1
import json, sys
try:
    reg = json.load(open(sys.argv[1]))
    n = int(reg["n_games"])
except Exception as e:
    print(f"ABORT: registry {sys.argv[1]} unreadable: {e}")
    sys.exit(1)
if n < 6241:
    print(f"ABORT: registry has {n} games < the recorded 6241 - "
          "wrong file or a regressed registry")
    sys.exit(1)
print(f"registry pre-check: n_games={n}")
PYEOF
expect_hash "$SIM/rl/search_server.py" \
  81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4 \
  "production server"
expect_hash "$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt" \
  44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3 \
  "Gravy ckpt_v10"
expect_hash "$CODE_DIR/shm_sweep.py" \
  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
  "shm_sweep.py ((C) containment)"
expect_hash "$CODE_DIR/settings_stage1.json" \
  de7e09d36f4c0f6c51baff80c9b984f58c480fb079f667a2d2836b0067514459 \
  "settings_stage1.json (registered settings)"
expect_hash "$CODE_DIR/search_s1.php" \
  1fcacaa3eb35d06e33a13b4f53a7b901279cf48eb34bdea14539c86e770ecd52 \
  "search_s1.php (clause-8 evaluator build)"
expect_hash "$CODE_DIR/s1_eval_main.php" \
  73ed24822baaaa9cc8ceebe4f9e082320932cc6e64b5e5f8e3f74b81764cae5a \
  "s1_eval_main.php (evaluator driver)"
expect_hash "$CODE_DIR/paired_driver_gravy.py" \
  3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 \
  "paired_driver_gravy.py (capture driver)"
expect_hash "$CODE_DIR/build_panel.py" \
  8f22d84546e0f0775b5c538c1e356fda622632a30731be4e335eaa30807db576 \
  "build_panel.py (panel builder)"
expect_hash "$CODE_DIR/stage1_analyze.py" \
  384676138d3fb57ca26fa66b2ead31420a2d6589618b4ebe6494b927d319e381 \
  "stage1_analyze.py (analyzer)"
expect_hash "$CODE_DIR/merge_registry.py" \
  13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe \
  "merge_registry.py (registry merge)"
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
expect_hash "$GTREE/$DECK_REL" \
  b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed \
  "fleet tree Gravy deck"
{
  sha256sum "$CODE_DIR"/settings_stage1.json "$CODE_DIR"/*.php \
    "$CODE_DIR"/*.py "$CODE_DIR"/*.sh 2>/dev/null
  echo "registry $REG (recorded in the manifest, pre/post)"
} > "$OUT/deployed_code_hashes.txt"

SRV_PIDS=""
SWEEP_PIDS=""
cleanup() {
  for pid in $SRV_PIDS; do kill "$pid" 2>/dev/null; done
  for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
}
trap cleanup EXIT

start_servers() {
  local seat i
  for seat in 1 2; do
    TCG_POLICY_SOCK="$OUT/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
      SEARCH_MODEL="$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt" \
      TCG_OPP_MIX="heuristic:1.0" \
      setsid nohup $PY "$SIM/rl/search_server.py" \
      > "$OUT/prod_s${seat}.log" 2>&1 < /dev/null &
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
}

start_sweeper() { # tree tag
  ipcs -m > "$OUT/ipcs_$2.txt"
  awk '$1 ~ /^0x/ {print $2}' "$OUT/ipcs_$2.txt" > "$OUT/shm_start_$2.txt"
  rm -f "$OUT/shm_sweep_$2.stop"
  $PY "$CODE_DIR/shm_sweep.py" --log "$OUT/shm_sweep_$2.log" \
    --start-file "$OUT/shm_start_$2.txt" \
    --games-dir "$1/vendor/talishar/Games" \
    --interval 60 --stop-file "$OUT/shm_sweep_$2.stop" &
  SWEEP_PIDS="$SWEEP_PIDS $!"
}

# --- capture -------------------------------------------------------
if [ "$PHASE" = "capture" ] || [ "$PHASE" = "all" ]; then
  bash "$CODE_DIR/g8_sweep.sh" "$OUT/g8" || exit 1
  start_servers
  read S1SEEDS S2SEEDS <<< "$($PY - "$BLOCK" <<'PYEOF'
import sys
b = int(sys.argv[1])
if b == 1:
    print("21001-21020 21021-21040")
else:
    start = 21041 + (b - 2) * 10
    print(f"{start}-{start+4} {start+5}-{start+9}")
PYEOF
)"
  for seat in 1 2; do
    seeds=$S1SEEDS; [ "$seat" = 2 ] && seeds=$S2SEEDS
    tree="/tmp/r9s1_cap_s${seat}"
    rm -rf "$tree"; cp -r "$GTREE" "$tree"
    find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
    start_sweeper "$tree" "cap_s${seat}"
    logdir="$OUT/cap_s${seat}_b${BLOCK}_log"
    GATE_GAME_IDS_FILE="$OUT/cap_game_ids.txt" TCG_CLEAN_CHILDREN=1 \
      $PY "$CODE_DIR/paired_driver_gravy.py" \
        --tree "$tree" --sock "$OUT/prod_s${seat}.sock" \
        --seat "$seat" --arm capture --seeds "$seeds" \
        --deck "$tree/$DECK_REL" \
        --out "$OUT/cap_s${seat}_b${BLOCK}.jsonl" \
        --logdir "$logdir" \
        > "$OUT/cap_s${seat}_b${BLOCK}.stdout" 2>&1 || exit 1
    touch "$OUT/shm_sweep_cap_s${seat}.stop"
    $PY - "$OUT/cap_s${seat}_b${BLOCK}.jsonl.manifest.json" <<'PYEOF' || exit 1
import json, sys
man = json.load(open(sys.argv[1]))
assert man["assert_ok"], f"capture arm assertions FAILED: {man['checks']}"
print(f"capture assertions OK ({man['arm']} seat {man['seat']}): "
      f"{man['assertions']}")
PYEOF
    echo "$logdir/snaps=$logdir/snaps/teacher_snap_index.jsonl" \
      >> "$OUT/streams.txt"
  done
  $PY "$CODE_DIR/merge_registry.py" --registry "$REG" \
    --tag r9s1_capture --ids "$OUT/cap_game_ids.txt" \
    --vault "$VAULT" | tee "$OUT/registry_merge_b${BLOCK}.txt" || exit 1
  echo "CAPTURE BLOCK $BLOCK DONE"
fi

# --- panel ---------------------------------------------------------
if [ "$PHASE" = "panel" ] || [ "$PHASE" = "all" ]; then
  [ -s "$OUT/streams.txt" ] || {
    echo "ABORT: no capture streams recorded ($OUT/streams.txt)" >&2; exit 1; }
  SARGS=""
  while IFS= read -r line; do SARGS="$SARGS --stream $line"; done \
    < "$OUT/streams.txt"
  $PY "$CODE_DIR/build_panel.py" $SARGS \
    --panel-size 240 --per-game-cap 8 \
    --out "$OUT/panel_jobs.jsonl" --report "$OUT/panel_report.json"
  rc=$?
  if [ $rc -eq 3 ]; then
    echo "PANEL SHORTFALL: run another capture block " \
      "(BLOCK=$((BLOCK+1)) PHASE=capture), then PHASE=panel" >&2
    exit 3
  fi
  [ $rc -eq 0 ] || exit 1
  $PY - "$OUT/panel_jobs.jsonl" <<'PYEOF' || exit 1
import json, os, sys
jobs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
assert len(jobs) == 240, f"panel has {len(jobs)} jobs, expected 240"
for j in jobs:
    assert os.path.isdir(j["snap_dir"]), \
        f"snap dir missing: {j['snap_dir']}"
print(f"panel: 240 jobs; all snap dirs asserted present")
PYEOF
fi

# --- eval ------------------------------------------------------------
if [ "$PHASE" = "eval" ] || [ "$PHASE" = "all" ]; then
  [ -z "$SRV_PIDS" ] && start_servers
  SETLIST="$($PY - "$CODE_DIR/settings_stage1.json" "${SETTINGS:-all}" <<'PYEOF'
import json, sys
spec = json.load(open(sys.argv[1]))
want = sys.argv[2]
for s in spec["settings"]:
    if want == "all" or s["name"] == want:
        hz = "off" if int(s["horizon"]) == 0 else str(s["horizon"])
        print("%s %d %d %s %s %d" % (s["name"], s["hooks"],
              s["deadline_s"], hz, s["horizon_value"], s["k"]))
PYEOF
)"
  [ -n "$SETLIST" ] || { echo "ABORT: no such setting" >&2; exit 1; }
  NSETTINGS=$(printf '%s\n' "$SETLIST" | grep -c .)
  while read -r NAME HOOKS DEADLINE HZENV HVAL K; do
    # Retire the previous setting's sweepers before its trees
    # are recreated (their stop files were already touched;
    # this is the belt to that suspenders).
    for pid in $SWEEP_PIDS; do kill "$pid" 2>/dev/null; done
    SWEEP_PIDS=""
    # per-setting job copies: the panel + the setting tuple from
    # the SAME settings file the analyzer audits against.
    $PY - "$OUT/panel_jobs.jsonl" "$CODE_DIR/settings_stage1.json" \
          "$NAME" "$OUT/jobs_${NAME}.jsonl" <<'PYEOF' || exit 1
import json, os, sys
panel_path, spec_path, name, out_path = sys.argv[1:5]
spec = json.load(open(spec_path))
tuple_ = [s for s in spec["settings"] if s["name"] == name]
assert len(tuple_) == 1, f"setting {name} not unique in {spec_path}"
tuple_ = {k: tuple_[0][k] for k in
          ("name", "hooks", "deadline_s", "horizon",
           "horizon_value", "k")}
jobs = [json.loads(l) for l in open(panel_path) if l.strip()]
with open(out_path, "w") as f:
    for j in jobs:
        assert os.path.isdir(j["snap_dir"]), \
            f"snap dir missing: {j['snap_dir']}"
        c = dict(j); c["setting"] = tuple_
        f.write(json.dumps(c) + "\n")
print(f"setting {name}: {len(jobs)} job copies stamped "
      f"{json.dumps(tuple_)}")
PYEOF
    for s in 0 1 2 3; do
      tree="/tmp/r9s1_tree_e${s}"
      rm -rf "$tree"; cp -r "$GTREE" "$tree"
      find "$tree" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
      cp "$CODE_DIR/search_s1.php" "$tree/search.php"
      cp "$CODE_DIR/s1_eval_main.php" "$tree/"
      expect_hash "$tree/search.php" \
        1fcacaa3eb35d06e33a13b4f53a7b901279cf48eb34bdea14539c86e770ecd52 \
        "eval tree $s search.php (search_s1)" || exit 1
      expect_hash "$tree/featurize.php" \
        f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92 \
        "eval tree $s featurize.php" || exit 1
      start_sweeper "$tree" "e${s}"
    done
    PIDS="" FAIL=0
    for s in 0 1 2 3; do
      (
        tree="/tmp/r9s1_tree_e${s}"
        for p in 1 2; do
          $PY - "$OUT" "$NAME" "$s" "$p" "$NSHARD" <<'PYEOF'
import hashlib, json, sys
out, name, s, p, nshard = (sys.argv[1], sys.argv[2],
                          int(sys.argv[3]), int(sys.argv[4]),
                          int(sys.argv[5]))
jobs = [json.loads(l) for l in
        open(f"{out}/jobs_{name}.jsonl") if l.strip()]
sel = [j for j in jobs
       if int(hashlib.sha256(str(j["game"]).encode()).hexdigest(),
              16) % nshard == s and int(j["player"]) == p]
with open(f"{out}/jobs_{name}_shard{s}_p{p}.jsonl", "w") as f:
    for j in sel:
        f.write(json.dumps(j) + "\n")
print(f"setting {name} shard {s} player {p}: {len(sel)} jobs")
PYEOF
          : > "$OUT/evals_${NAME}_shard${s}_p$p.jsonl"
          : > "$OUT/stats_${NAME}_shard${s}_p$p.jsonl"
          (cd "$tree" && MEAS_JOBS="$OUT/jobs_${NAME}_shard${s}_p$p.jsonl" \
             MEAS_OUT="$OUT/evals_${NAME}_shard${s}_p$p.jsonl" \
             EVAL_STATS="$OUT/stats_${NAME}_shard${s}_p$p.jsonl" \
             MEAS_SEED=$((885001 + s * 100000000)) \
             EVAL_SETTING_NAME="$NAME" EVAL_HOOKS="$HOOKS" \
             EVAL_DEADLINE_S="$DEADLINE" LABEL_HORIZON="$HZENV" \
             EVAL_HORIZON_VALUE="$HVAL" EVAL_K="$K" \
             TCG_POLICY_SOCK="$OUT/prod_s$p.sock" \
             php s1_eval_main.php \
               "$tree/$DECK_REL" "$tree/$DECK_REL" \
               --policy-search --games 1 \
               > "$OUT/eval_${NAME}_shard${s}_p$p.err" 2>&1) || exit 1
        done
        touch "$OUT/shm_sweep_e${s}.stop"
      ) &
      PIDS="$PIDS $!"
    done
    for pid in $PIDS; do wait "$pid" || FAIL=1; done
    [ "$FAIL" = 0 ] || {
      echo "ABORT: an eval shard failed for setting $NAME" >&2; exit 1; }
    cat "$OUT"/evals_${NAME}_shard*_p*.jsonl > "$OUT/evals_${NAME}.jsonl"
    cat "$OUT"/stats_${NAME}_shard*_p*.jsonl > "$OUT/stats_${NAME}.jsonl"
    echo "setting $NAME done: $(wc -l < "$OUT/evals_${NAME}.jsonl") world rows, $(wc -l < "$OUT/stats_${NAME}.jsonl") stat rows"
    # B0GATE-BEGIN (ruling sec.4.4, as ruled in
    # claude-reply-edddf5e sec.4.4: B0 IS the smoke. A B0
    # eval abort already exited inside this iteration -
    # the "an eval shard failed" exit above. This gate is
    # the other half of the condition: if B0's rows fail
    # ANY analyzer integrity check, the run stops HERE,
    # before the +H settings, instead of continuing in
    # file order. It runs the analyzer over a B0-only
    # settings file and reads only its exit code (0 =
    # every audit passed; 2 = an integrity abort); the
    # subset report's selection verdict is meaningless -
    # B0 alone is the control - and is never read.
    # fixtures/fx_b0_gate.sh extracts and executes exactly
    # this block against planted B0 outputs.)
    if [ "$NAME" = "B0" ] && [ "$NSETTINGS" -gt 1 ]; then
      $PY - "$CODE_DIR/settings_stage1.json" \
            "$OUT/b0_gate_settings.json" <<'PYEOF' || exit 1
import json, sys
spec = json.load(open(sys.argv[1]))
spec["settings"] = [s for s in spec["settings"]
                    if s["name"] == "B0"]
assert len(spec["settings"]) == 1, "B0 not unique in settings"
json.dump(spec, open(sys.argv[2], "w"), indent=1)
print("B0 gate: B0-only settings file written")
PYEOF
      if $PY "$CODE_DIR/stage1_analyze.py" \
          --panel "$OUT/panel_jobs.jsonl" \
          --settings "$OUT/b0_gate_settings.json" \
          --evals-dir "$OUT" \
          --json-out "$OUT/b0_gate_report.json" \
          > "$OUT/b0_gate_report.txt" 2>&1; then
        echo "B0 gate PASSED: B0's rows pass every analyzer integrity check; continuing to the +H settings"
      else
        echo "ABORT: B0 failed the analyzer integrity gate (see $OUT/b0_gate_report.txt) - stopping BEFORE the +H settings (ruling sec.4.4)" >&2
        exit 1
      fi
    fi
    # B0GATE-END
  done <<< "$SETLIST"
fi

# --- analyze ---------------------------------------------------------
if [ "$PHASE" = "analyze" ] || [ "$PHASE" = "all" ]; then
  $PY "$CODE_DIR/stage1_analyze.py" --panel "$OUT/panel_jobs.jsonl" \
    --settings "$CODE_DIR/settings_stage1.json" --evals-dir "$OUT" \
    --json-out "$OUT/stage1_report.json" \
    > "$OUT/stage1_report.txt" || exit 1
  cat "$OUT/stage1_report.txt"
  $PY - "$OUT" "$REG" <<'PYEOF'
import glob, hashlib, json, os, sys
out, reg_path = sys.argv[1], sys.argv[2]

def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def rows(p):
    return sum(1 for l in open(p) if l.strip())

reg = json.load(open(reg_path))
man = {"out": out,
       "panel_rows": rows(out + "/panel_jobs.jsonl"),
       "registry_post": {"n_games": reg["n_games"],
                         "sha256": h(reg_path)},
       "sha256": {os.path.basename(p): h(p) for p in sorted(
           glob.glob(out + "/panel_*.json*") +
           glob.glob(out + "/evals_*.jsonl") +
           glob.glob(out + "/stats_*.jsonl") +
           glob.glob(out + "/stage1_report.*") +
           glob.glob(out + "/jobs_*.jsonl"))},
       "report": json.load(open(out + "/stage1_report.json"))}
json.dump(man, open(out + "/stage1_manifest.json", "w"), indent=1)
print(json.dumps(man["report"]["selection"]))
PYEOF
  echo "STAGE 1 COMPLETE - $OUT/stage1_manifest.json"
fi
