# Claude — code review of the round-10 Step 1 pilot package

**Reviewed commit:** acc55a14f94526222df4e752906284560e5ee4fa (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-243b9d8.md` hashes to `8a3c8b01…57911a`, the value I gave Joe. The doc is `7573cd9e…`, and the package adds files only: no existing file is modified.

**Verdict: CHANGES REQUESTED, three small items** (§2). The build, the read's formulas, the sizing arithmetic, and the standing requirements are right (§1). Both flags are accepted (§3).

## 1. Checks

**The build.**
- `search_s3_thr_diff.txt` is one token, `$bp >= 0.97` → `$bp >= 1.01`, in the branch condition. That's unreachable for any multi-candidate decision, which is the faithful expression of "lifted".
- The only other `0.97` in the file is the probe's capture hook, now nested under `$ncand <= 1` and env-gated, so it's inert.
- The base file is the §14 `search_s3.php` (`87779e8e…`).
- The reused files in `code/step1/` are byte-identical to the round-10 copies: `search_s2`, `search_s3`, `s2_label_main` (the loud form), `stage0_report`, `analyze_l3`, `g8_sweep2`, `shm_sweep`, `merge_registry` and the driver.
- `s1_eval_main.php` differs only by the loud loader and its header note, as required.

**The runner.**
- It builds and exports `TEACHER_TUPLE_JSON` from settings, so the live teacher runs the pinned tuple, not the unpinned legacy one.
- It sets `TEACHER_SNAP_DIR` per block and leaves `TEACHER_CAPTURE` unset.
- It gates on the pre-gate manifest's verdict, build hash and tuple.
- The composed-env fixture executes the games block verbatim.

**The read.**
- Classes are assigned by the live stat row's top prior: below 0.97 is contested, otherwise newly contested.
- Per-game totals run over all 100 games, zeros included, with no weights.
- **The sizing:** n = ⌈100·SE²/((Δ/2.4866)² − 0.0090²)⌉, where 2.4866 = 1.645 + 0.8416. That's correct for the registered two-sample bar at 80% power, with the infinite case handled.

**Timeout:** 7,845 s = ⌈2143.2 × 3.66⌉, derived from the published Stage 2 rows. Accepted.

**Fixtures, run here:**
- **round-10 suite: 197 checks, ALL PASS.**
- **The pilot suite did not run clean here.** `fx_pilot_loader.py` hard-codes `~/workspace/tcg-sim/.tools/php83/usr/bin/php8.3` and crashes on any other host (129 PASS, then a FileNotFoundError). With the path pointed at this host's php, **131 checks, ALL PASS**. The remaining transcript differences are set-print ordering only (§2.3).

## 2. Required

### 2.1 The pre-gate seed block overlaps a used block, and the used-blocks list is incomplete

- `run_pilot_pregate.sh` plays **8601–8610**. **8601–8604 is round 7's contention probe** (`round7/build-package.md`, listed in round 9's D2 record).
- `fx_pilot_seeds.py` passes only because its `USED_GAME_BLOCKS` omits it. The list also omits: the 3000-series probes, 4001–4014, 5001–5010, 6001–6040, 7001–7002, 8501–8510, 8801–8820, 11001–11010 and 12001–12010.
- Reusing a block for an action-identity pre-gate is defensible, as round 9's F4 was. But the package **claims** disjointness, and the claim is false.

**Required:**
- Complete `USED_GAME_BLOCKS` from the record: round 9's D2 list plus every block used since. Cite the sources in the fixture's docstring.
- Move the pre-gate to a block the completed list proves fresh.

### 2.2 The STOP gate and Δ_plan must use one-sided 95% bounds, as registered

- The read takes `lb` and `ub` from `analyze_l3.cluster_bootstrap`, which returns the two-sided 95% interval: the 2.5th and 97.5th percentiles.
- **For Δ_plan,** the 2.5th percentile is more conservative than the one-sided 5th. That's the same stand-in the probe used, and acceptable.
- **For STOP, it errs the permissive way.** The 97.5th percentile sits above the registered one-sided 95% upper bound, so a pilot that should STOP may not.

**Required:**
- Compute the **5th and 95th percentiles from the same bootstrap replicates** (same B and seed). Use the 95th for STOP and the 5th for Δ_plan, and print the two-sided CI beside them.
- **Fixture:** planted totals where the 95th percentile is below 0.0849 but the 97.5th isn't must print STOP.

### 2.3 Portability and determinism of the suite

- **The php path:** resolve php as the round-10 suite does (`$PHP`, else `command -v php8.3`/`php`), and fail with a clear message, not a traceback, when none exists.
- **Determinism:** sort the sets printed in PASS lines (the gate-field set and the seed-block set), so the transcript reproduces byte-identically across hosts.

## 3. Rulings on the flags

1. **Seeds 25001–25050 × both seats = 100 games: accepted.** It's the project's paired layout, and it leaves the door open to a raw arm on the same seeds later.
2. **Label family 700,055,001 + shard × 10⁸ with a 512-per-shard cap: accepted.** The move off 570,055,001 is right, given the probe eval family's span. The enumeration of ranges and values against all ten prior families is the standard proof.

**Scope:** §2.1–§2.3 come back in one commit for a confirmation check. The pre-gate then runs first on Joe's go, and the pilot only after it reads IDENTICAL. No run is approved yet.
