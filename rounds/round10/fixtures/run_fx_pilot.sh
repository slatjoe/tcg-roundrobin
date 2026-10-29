#!/bin/bash
# Round-10 Step 1 pilot fixture suite driver.
# Fixtures:
#   gen_search_s3_thr.py  -- the build regenerates
#                            byte-identically from the
#                            sec.14 file; the diff is
#                            exactly the one-token
#                            threshold change.
#   fx_pilot_pins.py      -- deploy-list pin guard
#                            for both runners +
#                            settings-literal checks +
#                            the negative case.
#   fx_pilot_seeds.py     -- seed-family clearance
#                            by enumeration (labels at
#                            the cap vs every prior
#                            family; capture + pregate
#                            seed blocks).
#   fx_pilot_python.py    -- writer->reader round
#                            trips on real shapes
#                            (jobs builder pairing +
#                            classes, games report
#                            walls/audit, the read's
#                            gain/LOGO/sizing by hand).
#   fx_pilot_pregate.py   -- the pre-gate checker's
#                            exact form on synthetic
#                            records (identity, the
#                            expected newly-contested
#                            divergence, two failure
#                            shapes).
#   fx_pilot_loader.py    -- strict job files + loud
#                            loaders in both shipped
#                            PHP job readers (the s1
#                            block verbatim under php).
#   fx_pilot_env.py       -- the composed-environment
#                            contract for the games
#                            runner (BLOCK:PILOT-GAMES
#                            verbatim in a stub
#                            harness; negative case).
#   fx_pilot_parity.py    -- tuple-builder parity
#                            between the runners;
#                            pregate manifest
#                            writer/reader key parity;
#                            driver flag parity.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FAILED=0
run() {
  echo "===== $1 ====="
  shift
  "$@" || FAILED=$((FAILED+1))
  echo
}
run gen_search_s3_thr.py python3 "$HERE/gen_search_s3_thr.py"
run fx_pilot_pins.py python3 "$HERE/fx_pilot_pins.py"
run fx_pilot_seeds.py python3 "$HERE/fx_pilot_seeds.py"
run fx_pilot_python.py python3 "$HERE/fx_pilot_python.py"
run fx_pilot_pregate.py python3 "$HERE/fx_pilot_pregate.py"
run fx_pilot_loader.py python3 "$HERE/fx_pilot_loader.py"
run fx_pilot_env.py python3 "$HERE/fx_pilot_env.py"
run fx_pilot_parity.py python3 "$HERE/fx_pilot_parity.py"
echo "===== bash -n (both runners; never run) ====="
bash -n "$HERE/../code/step1/run_pilot.sh" \
  && bash -n "$HERE/../code/step1/run_pilot_pregate.sh" \
  && echo "PASS bash -n both runners" || FAILED=$((FAILED+1))
echo
if [ "$FAILED" = 0 ]; then echo "run_fx_pilot: ALL FIXTURES PASS";
else echo "run_fx_pilot: $FAILED FIXTURE(S) FAILED"; fi
exit "$FAILED"
