#!/usr/bin/env bash
# Round-10 Step 2+3 fleet fixture driver: runs the
# fleet suites and prints one PASS/FAIL line per
# check; the transcript is fx_fleet_outputs.txt
# (deterministic -- two runs byte-identical).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY=python3
FAIL=0
for suite in fx_fleet_seeds fx_fleet_sizing \
             fx_fleet_pins fx_fleet_parity \
             fx_fleet_read fx_fleet_anchor \
             fx_fleet_server_env fx_fleet_contract \
             fx_fleet_smoke_loops fx_fleet_argparse; do
  echo "===== $suite ====="
  $PY "$HERE/$suite.py" || FAIL=1
done
echo "===== fx_fleet_blocks ====="
bash "$HERE/fx_fleet_blocks.sh" || FAIL=1
echo "===== bash -n (all fleet shell files) ====="
for f in "$HERE/../code/step2/run_fleet_games.sh" \
         "$HERE/../code/step2/run_fleet_l3.sh" \
         "$HERE/../code/step2/g8_sweep2.sh" \
         "$HERE/fx_fleet_blocks.sh" \
         "$HERE/run_fx_fleet.sh"; do
  case "$f" in
    "$HERE/../"*) disp=${f#"$HERE/../"} ;;
    "$HERE/"*)    disp=fixtures/${f#"$HERE/"} ;;
    *)            disp=$f ;;
  esac
  if bash -n "$f"; then echo "PASS: bash -n $disp"; else
    echo "FAIL: bash -n $disp"; FAIL=1; fi
done
[ "$FAIL" = 0 ] && echo "ALL FLEET FIXTURES PASS" \
  || echo "FLEET FIXTURES FAILED"
exit $FAIL
