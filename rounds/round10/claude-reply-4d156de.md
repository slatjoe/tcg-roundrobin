# Claude — confirmation check on the Step 2+3 fleet fix pass (package §20)

**Reviewed commit:** 4d156de8b5bc8d7d17ef28d3b46b1d62501356d4 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-baf16e7.md` hashes to `a6481cd9…99439639`, the value I gave Joe. The runners are games `2a2ab082…` and L3 `56a0688b…`.

**Verdict: CONFIRMED. On Joe's go, the re-smoke runs, and if it passes, the fleet launches under that same go**, with launched sha == 4d156de8 (or differing only under `rounds/`).

## Checks

- **The smoke repair.**
  - `seeds=${3:-}` in TS-DRIVERS (l.297) and RS-DRIVERS (l.374).
  - The RAW-RERUN exemption is reasoned and fixture-checked.
  - `fx_fleet_smoke_loops.py` runs both loops verbatim under `set -u`, and the reverted form reproduces the §19.4 abort.
- **Seed 27001: retired as ruled.** Game 776023215 is under `r10_step2_fleet_smoke`, and the registry went 7,641 → 7,642.
- **The re-smoke seed:** 27002, fresh, and named at all four SMOKE assignments, with a guard that 27001 appears in none.
- **Merge argv:** the pilot form (`--registry … --tag … --ids <file>` per file, `--vault`) at both the smoke and production sites.
- **Defect 9:** both `shm_sweep.py --once` lines are gone, with no `|| echo` left in either runner. The kept tolerances are each dispositioned in §20.4.
- **The class fix:** `fx_fleet_argparse.py` enumerates all 14 Python call sites, parses each verbatim argv under the target file's real argparse with hashes asserted, and fails both the old `--once` and the bare-files merge.
- **The smoke now runs through the merge.** It runs the games report (pairing-only, for the stated reason) and the registry merge under the smoke tag, then exits before the read. The production flow is unchanged.
- **Fixtures, run here** on a scratch copy: **the fleet suite has 239 checks, ALL PASS**, identical to the committed transcript.

**Item 8, closing the seed inside the package: that was the right call.** A seed edit after confirmation would have broken launched sha == confirmed sha. The precedent is fine: an open item that the next run would read belongs inside the reviewed commit.

## Launch conditions

1. **Joe's go.** The launch record states the launched sha and the deployed hashes, read back.
2. **The re-smoke:** `SMOKE=1`, seed 27002, both seats, both arms, through the games report and the smoke-tag merge.
   - **It passes iff:** both servers are loaded with learner seats 1 and 2; four valid driver rows with the specified seat and arm; the teacher rows stamped H8k-180+H; no teacher stat rows from raw; the report written; the merge completed with the registry count up by the smoke games.
   - **Any failure stops everything** and returns to review. No patch, no rerun.
3. **On a pass, the fleet** runs from a clean production output directory: gate → teacher phase → raw phase → reruns → report → merge → primary read, then `run_fleet_l3.sh`.
4. **Status-only interim notices**, and publication of `data/step2/` with the declared label storage.

**Scope:** this confirms the §20 fix pass and approves the re-smoke and, behind its pass, the combined paired fleet at sha 4d156de8b5bc8d7d17ef28d3b46b1d62501356d4, on Joe's go. Approval certifies the build as written, not the run as executed.
