#!/bin/bash
# Stage 3 fixture suite aggregator: runs every fx_s3_* /
# fx_stage3_* suite and reports one line per suite.
# PHP=${PHP:-php} (PHP >= 8 CLI with pcntl; the VM's
# user-space php8.3 or the box PHP both qualify).
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
run fx_s3_blocks bash "$FX/fx_s3_blocks.sh"
run fx_g8_sweep2 bash "$FX/fx_g8_sweep2.sh"
run fx_stage3_games_report python3 "$FX/fx_stage3_games_report.py"
run fx_stage3_analyze python3 "$FX/fx_stage3_analyze.py"
run fx_s3_registry python3 "$FX/fx_s3_registry.py"
run fx_s3_l3_roundtrip bash "$FX/fx_s3_l3_roundtrip/run_fx_s3_l3.sh"
echo "FX-S3 SUITE: $([ $FAIL = 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
