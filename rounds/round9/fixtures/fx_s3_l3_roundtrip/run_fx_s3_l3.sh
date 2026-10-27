#!/bin/bash
# fx_s3_l3_roundtrip - the REAL s2_label_main.php at the
# Stage 3 seed base (MEAS_SEED=1055001) and the Stage 3
# settings' label_tuple pins, against the cand-parity stub
# play_game.php in this dir; then the genuine rows feed the
# REAL stage3_attr_analyze.py (see check script). Mirrors
# fixtures/fx_s2_label/run_fx_s2_label.sh.
# PHP=${PHP:-php} - any PHP >= 8 CLI.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
DRIVER="$FX/../../code/s2_label_main.php"
PHP=${PHP:-php}
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAIL=0
run_env() {
  (cd "$FX" && env MEAS_JOBS="$1" MEAS_OUT="$2" \
     EVAL_STATS="$3" MEAS_SEED=1055001 \
     TCG_POLICY_SOCK=/dev/null FX_CFG_LOG="$WORK/cfg.jsonl" \
     EVAL_SETTING_NAME=L3-W50+H EVAL_HOOKS=8000 \
     EVAL_DEADLINE_S=180 LABEL_HORIZON=62 \
     EVAL_HORIZON_VALUE=-1 EVAL_K=50 \
     $PHP "$DRIVER" deck deck --policy-search --games 1 \
     > "$4" 2> "$5")
  return $?
}
run_env "$FX/jobs_ok.jsonl" "$WORK/out.jsonl" "$WORK/stats.jsonl" \
        "$WORK/ok.stdout" "$WORK/ok.stderr"
rc=$?
if [ $rc -eq 0 ] && grep -q "S2-LABEL-DONE" "$WORK/ok.stderr"; then
  echo "PASS happy path (exit 0, S2-LABEL-DONE, MEAS_SEED=1055001)"
else
  echo "FAIL happy path (exit $rc; stderr: $(head -3 "$WORK/ok.stderr"))"
  FAIL=1
fi
for name in badk nosetting; do
  run_env "$FX/jobs_${name}.jsonl" "$WORK/${name}.out.jsonl" \
          "$WORK/${name}.stats.jsonl" "$WORK/${name}.stdout" \
          "$WORK/${name}.stderr"
  rc=$?
  if [ $rc -eq 2 ]; then
    echo "PASS $name abort exit code 2"
  else
    echo "FAIL $name abort exit code (got $rc)"
    FAIL=1
  fi
done
python3 "$FX/check_fx_s3_l3.py" "$WORK" || FAIL=1
exit $FAIL
