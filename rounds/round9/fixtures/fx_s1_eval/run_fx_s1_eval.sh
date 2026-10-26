#!/bin/bash
# fx_s1_eval - clause-8 first placement: s1_eval_main.php's
# run pins, job/tuple matching, abort-on-mismatch, and row/stat
# stamping, exercised against a stub play_game.php (the fixture
# dir is the CWD so the driver's include resolves to the stub).
# PHP=${PHP:-php} - any PHP >= 8 CLI.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
DRIVER="$FX/../../code/s1_eval_main.php"
PHP=${PHP:-php}
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAIL=0
note() { echo "$1"; }
expect_abort() { # name jobsfile extra_env...
  local name=$1 jobs=$2; shift 2
  rm -f "$WORK/out.jsonl" "$WORK/stats.jsonl"
  (cd "$FX" && env MEAS_JOBS="$jobs" MEAS_OUT="$WORK/out.jsonl" \
     EVAL_STATS="$WORK/stats.jsonl" MEAS_SEED=885001 \
     TCG_POLICY_SOCK=/dev/null FX_CFG_LOG="$WORK/cfg.jsonl" \
     EVAL_SETTING_NAME=B0+H EVAL_HOOKS=4000 EVAL_DEADLINE_S=180 \
     LABEL_HORIZON=62 EVAL_HORIZON_VALUE=-1 EVAL_K=25 "$@" \
     $PHP "$DRIVER" deck deck --policy-search --games 1 \
     > "$WORK/$name.stdout" 2> "$WORK/$name.stderr")
  local rc=$?
  if [ $rc -eq 2 ] && grep -q "ABORT:" "$WORK/$name.stderr" \
     && [ ! -e "$WORK/out.jsonl" ]; then
    note "PASS $name (exit 2, ABORT logged, no rows written)"
  else
    note "FAIL $name (exit $rc; stderr: $(head -2 "$WORK/$name.stderr"))"
    FAIL=1
  fi
}

# --- happy path -------------------------------------------------
rm -f "$WORK/out.jsonl" "$WORK/stats.jsonl" "$WORK/cfg.jsonl"
(cd "$FX" && env MEAS_JOBS="$FX/jobs_ok.jsonl" \
   MEAS_OUT="$WORK/out.jsonl" EVAL_STATS="$WORK/stats.jsonl" \
   MEAS_SEED=885001 TCG_POLICY_SOCK=/dev/null \
   FX_CFG_LOG="$WORK/cfg.jsonl" \
   EVAL_SETTING_NAME=B0+H EVAL_HOOKS=4000 EVAL_DEADLINE_S=180 \
   LABEL_HORIZON=62 EVAL_HORIZON_VALUE=-1 EVAL_K=25 \
   $PHP "$DRIVER" deck deck --policy-search --games 1 \
   > "$WORK/ok.stdout" 2> "$WORK/ok.stderr")
rc=$?
if [ $rc -eq 0 ] && grep -q "S1-EVAL-DONE" "$WORK/ok.stderr"; then
  note "PASS happy path (exit 0, S1-EVAL-DONE)"
else
  note "FAIL happy path (exit $rc; stderr: $(head -3 "$WORK/ok.stderr"))"
  FAIL=1
fi
if [ -e "$WORK/out.jsonl" ]; then
  python3 "$FX/check_fx_s1_eval.py" "$WORK/out.jsonl" \
    "$WORK/stats.jsonl" "$WORK/cfg.jsonl" || FAIL=1
fi

# --- mismatch cases: each must abort before evaluating ---------
expect_abort bad_hooks "$FX/jobs_badhooks.jsonl"
expect_abort missing_setting "$FX/jobs_nosetting.jsonl"
expect_abort bad_horizon_value "$FX/jobs_ok.jsonl" \
  EVAL_HORIZON_VALUE=banana
expect_abort bad_hook_pin "$FX/jobs_ok.jsonl" EVAL_HOOKS=0x1000

echo "FX-S1-EVAL: $([ $FAIL -eq 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
