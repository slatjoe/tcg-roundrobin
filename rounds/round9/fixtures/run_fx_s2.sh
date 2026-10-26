#!/bin/bash
# Stage 2 fixture suite aggregator: runs every fx_s2_* /
# fx_stage2_* / fx_build_s2_* / fx_pregate_* suite and
# reports one line per suite. PHP=${PHP:-php} (PHP >= 8 CLI
# with pcntl; on this project the box PHP 8.5 or the VM's
# user-space php8.3 both qualify).
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
PHP=${PHP:-php}
export PHP
FAIL=0
run() { # name cmd...
  local name=$1; shift
  echo "===== $name ====="
  if "$@"; then echo "SUITE $name: PASS"; else
    echo "SUITE $name: FAIL"; FAIL=1; fi
}
run fx_s2_live bash "$FX/fx_s2_live/run_fx_s2_live.sh"
run fx_s2_label bash "$FX/fx_s2_label/run_fx_s2_label.sh"
run fx_s2_blocks bash "$FX/fx_s2_blocks.sh"
run fx_build_s2_jobs python3 "$FX/fx_build_s2_jobs.py"
run fx_pregate_check python3 "$FX/fx_pregate_check.py"
run fx_stage2_games_report python3 "$FX/fx_stage2_games_report.py"
run fx_stage2_analyze python3 "$FX/fx_stage2_analyze.py"
echo "FX-S2 SUITE: $([ $FAIL = 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
