# Claude — review of the Step 2+3 games-runner rebuild (package §19)

**Reviewed commit:** baf16e7fc96a01de54c56849d34ab656786ad040 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-5ea3a72.md` hashes to `f3f4ff8a…11965232`, the value I gave Joe.

**Verdict: the fork is right, but CHANGES REQUESTED before the re-smoke.**
- Both rulings asked are **approved** (§2).
- **A ninth defect** of the same class (§3) is added to this pass.
- The pass **must close the class, not the instance**: every Python invocation in both runners is checked against its real argparse, and the smoke runs through the merge.
- Stopping at the failed smoke without patching was exactly right.

## 1. What checks out

- **The fork.**
  - TS-SRV is token-identical to the pilot's `PILOT-SRV` block: per-seat `TCG_POLICY_SOCK`, `TCG_LEARNER_SEAT=$seat`, `SEARCH_MODEL`, `TCG_OPP_MIX`, the tree's patched server, and `search model loaded` readiness.
  - TS-DRIVERS carries `--tree --sock --seat --arm --seeds --deck --timeout --out --logdir`, `TCG_CLEAN_CHILDREN=1`, one sweeper per tree, and `TEACHER_TUPLE_JSON` exported.
  - The raw blocks mirror these.
- **The reference server.** `ref_patched_search_server.py` hashes to `ab85fa1b…`, equal to round 3's published copy.
- **The smoke proved the spawn side at runtime:** both servers loaded `ckpt_v10` on per-seat sockets with learner seats 1 and 2.
- **Fixtures, run here:** **the fleet suite has 186 checks, ALL PASS.**

## 2. The two rulings

1. **The smoke repair is approved,** with one condition and a seed ruling.
   - **The repair:** `seeds=${3:-}` in every driver loop that the SMOKE switch can empty (teacher, raw, and the rerun loop if it shares the pattern).
   - **Fixture:** extract each loop verbatim and run it under `set -u` with SMOKE's emptied lists and a stub driver. It must skip the emptied specs and run the populated ones. That's the test that would have caught this.
   - **Seed 27001: retire it.** Merge game id 776023215 into the registry under the smoke tag (it's do-not-train regardless), and re-smoke on a **fresh** seed proven against the completed record (for example 27002). Smoke seeds are cheap, and a retired seed is never ambiguous later.
2. **The merge argv correction is approved:** the pilot's form, `--registry … --tag … --ids <file>` per ids file, plus `--vault` as the pilot passes it.

## 3. A ninth defect, the same class: `shm_sweep.py --once`

- Both runners call `$PY "$CODE_DIR/shm_sweep.py" --once` (games line 238, L3 line 162).
- The pinned `shm_sweep.py`'s argparse has **no `--once`** and **requires** `--log --start-file --games-dir --stop-file`. Each call exits 2.
- Both sites end in `|| echo "note: shm sweep nonzero"`, so the failure is **swallowed**: the pre-spawn sweep has never actually run. G8 did the segment cleanup the launch record credits.
- **It's harmless in effect, but it's a call that can't work, hidden by a tolerance.**
- **Required:** remove the two lines (G8 is the pre-spawn cleanup), or replace them with a valid invocation. **No `|| echo note` on any invocation whose failure would mean the step didn't happen.**

## 4. Required: close the class

1. **An argparse contract over every Python call site.** A fixture that **enumerates by grep** every `$PY "$CODE_DIR/<file>.py" …` invocation in `run_fleet_games.sh` and `run_fleet_l3.sh`:
   - currently, the games runner's driver ×3, `shm_sweep` ×3, `fleet_games_report` ×2, `merge_registry` and `fleet_read`;
   - and the L3 runner's `shm_sweep` ×2, `build_fleet_jobs` and `fleet_read`.
   - For each site, extract the argv verbatim, with variables substituted by placeholders, and parse it under **that file's real argparse**: build its parser and call `parse_args`, executing nothing else.
   - A site added later without a contract entry fails the fixture.
   - **Negative cases:** the old `--once` and the old bare-files merge form must both fail.
2. **The smoke runs through the merge.**
   - SMOKE currently exits before GRES, so it would never have exercised the merge that defect 8 sits in.
   - The smoke continues through the games report (pairing-only, or with a smoke expected-pairs value), and the **registry merge under the smoke tag**, and stops before the read.
   - That makes the merge argv's first runtime proof the smoke, not the fleet.
3. **The doc records defects 8 and 9** beside 1–7, along with the class fix.

## 5. Then

- The pass comes back for a confirmation check.
- **The re-smoke runs on Joe's go:** a fresh seed, both seats, both arms, through the merge.
- **If it passes, the fleet launches under the same go,** from a clean output directory, with the single-shot guards untouched. If it fails, it stops and returns to review.

**Scope:** this accepts the fork at baf16e7f, approves the two §19 repairs as specified, and adds §3–§4. No smoke or fleet run is approved until the confirmation check.
