#!/bin/bash
# fx_s2_live - the Stage 2 live-teacher build fixtures:
# the valuation flip through the REAL SimTeacher_Decide path,
# tuple pin/mismatch aborts, the hook guard reading the LIVE
# tuple, life-total recording, and the label-path default
# regression. Each case runs the harness main in its own
# process (the tuple is process-pinned) with the fixture dir
# as CWD (RunForSnapshot roots its Games/ at the CWD).
# PHP=${PHP:-php} - any PHP >= 8 CLI with pcntl.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
PHP=${PHP:-php}
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
CASES="flip0 flip1 unpinned pin_bad pin_bad_k hooks_live hooks_low label_default label_horizon"
for case in $CASES; do
  mkdir -p "$WORK/$case"
  (cd "$WORK/$case" && FX_SEARCH="$FX/../../code/search_s2.php" \
     FX_OUT="$WORK/$case/out.json" \
     $PHP "$FX/fx_s2_live_main.php" "$case" "$WORK/$case" \
       > "$WORK/$case/stdout.txt" 2> "$WORK/$case/stderr.txt")
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "FAIL harness case $case exited $rc"
    head -5 "$WORK/$case/stderr.txt"
    exit 1
  fi
done
python3 "$FX/check_fx_s2_live.py" "$WORK"
