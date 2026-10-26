# Claude — code review of the round-9 Stage 2 launch package

**Reviewed commit:** a0599d4562c522b3635accf1b147c90a7dc03b23 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-d7b92fd.md` hashes to `c969b4cf…6f8b600f`, the value I gave Joe. Every code file hashes to the package's §6 table.

**Verdict: CHANGES REQUESTED, two small blocking items** (§2). Both are about what the read rests on: the games runner doesn't mechanically check the pre-gate, and the live overturn rate mixes timed-out games into its numerator. Everything else is accepted, and F1–F5 are ruled in §3.

## 1. Checks

**The build.**
- `fixtures/search_s2_diff.txt` applied to `search_s1.php` (`1fcacaa3…`) regenerates `search_s2.php` byte-identically (`85490e8e…`).
- I read the whole diff:
  - The tuple is validated before any eval, and malformed input throws.
  - Unpinned, it falls back to the legacy constants.
  - `$K`, the per-candidate deadline and the margin read the tuple.
  - The children get `horizon` and `hookBudget` through cfg. `SimLabel_RunRollout` reads both (lines 1537 and 1546), so the existing guards now follow the live tuple.
  - A drawn world is priced at `horizon_value` before it enters `$outcomes`. The −1 therefore applies to the means, to the best-candidate selection and to the paired differences behind the 1.5 SE test. That is the whole of what ruling §3.1 asked.
  - The life fields are written only when `horizonApplied` is set, and that implies winner 0.
  - Every DecideInner row and the wrapper's exception row carry `setting`.
  - Nothing else changed.

**The timeout, recomputed from the published rows.**

| Source | Rows | Mean | p95 | Max |
|---|---|---|---|---|
| `stats_H8k-180+H.jsonl`, per-decision wall (s) | 240 | 26.5486 | 46.820 | **56.382** |
| `stats_B0+H.jsonl`, per-decision wall (s) | 240 | 26.5662 | 46.877 | 55.838 |
| Round-7 fleet stats, contested decisions per game | 9,429 over 400 games | 23.5725 | 39 | **57** |

- 56.382 × 57 = 3,213.8, giving **3,214 s**. Accepted. Using the observed maxima is the right choice for a validity bound.
- The per-candidate deadline (180 s × up to 4 candidates) means this isn't a hard ceiling. Teacher timeouts are reported, and §2.2 keeps them out of the rate.

**Cost.**
- The mean-price figure, 26.5486 × 23.5725 = 625.9 s per game, gives 34.8 box-hours. That confirms my 35.
- The tail price is 101.4 box-hours serial, about 25 h of wall time at 4 blocks. Accepted.

**The fixtures, run here** on a scratch copy (PHP 8.3.6 with pcntl):
- **all 7 suites PASS, 109 checks**, and the PASS lines are identical to `fx_s2_outputs.txt`.
- `fx_s2_live` loads the real `code/search_s2.php`, so the flip, the hook-guard check in both directions and the stamps are proven on the live Decide path.

**The pin audit.**
- The three runners carry 45 literals, all exactly 64 hex characters, with 20 unique values.
- 16 match files in the repo.
- The other four trace to registered values: ParseGamestate `0e88dd58…`, ckpt_v10 `44f1e5d7…`, the fleet `search.php` `8f6b35da…` and the deck `b8b41390…`. All four appear in `run_stage1.sh`, the design or the launch manifests.
- Every literal is checked against the file it's labeled for.

**The read.**
- `stage2_analyze.py` scores the primary as win = 1 and draw = loss = 0, in score units.
- The 0.5 and life-differential reads are co-reported, with a tied life total priced at 0.
- A job's diff is the mean over shared finished, non-refused worlds. Jobs are weighted equally, and the CI is the stock cluster bootstrap.
- Per-game gain uses the live rate, and the bands and tripwires are as registered.

**Hygiene.** The three-name form is absent from every runner, no `.pyc` is tracked, and I left no cache in the clone.

## 2. Blocking

1. **The pre-gate has to gate the games mechanically.**
   - **The problem:** `run_stage2_games.sh` never looks at the pre-gate. "Gated on IDENTICAL" is currently a header comment plus the run order. The pre-gate runner exits non-zero on failure, but nothing stops the games runner from being started anyway.
   - **The fix:** before the servers spawn, the games runner reads `$STAGE2_OUT/pregate/pregate_manifest.json` and aborts unless all three hold:
     - the check output's verdict is `IDENTICAL`;
     - the manifest records the `search_s2.php` sha256, and it equals this run's `85490e8e…`;
     - the manifest records the `TEACHER_TUPLE_JSON` it ran under, and it equals the one built here.
   - The pre-gate manifest therefore has to start recording those two values.
   - **Fixture:** a planted-manifest case for each of pass, absent, NOT IDENTICAL, hash mismatch and tuple mismatch.
2. **Live overturns per game must come from completed games only.**
   - **The problem:** `stage2_games_report.py` counts overturns over **every** stat row, timed-out and invalid games included, then divides by **completed** games. An overturn in a game that timed out inflates the per-game gain the bands use.
   - **The fix:** restrict the contested, thin-prior and overturn tallies behind the band rate to stat rows whose `game` is a completed driver row's `gamename`.
   - Co-report the all-rows rate beside it.
   - The overturns from timed-out games stay in L3. They're valid decisions, and the per-decision audit should label them, but they don't enter the per-game rate.
   - **Fixture:** extend `fx_stage2_games_report.py` with a stat-row overturn in the timed-out game, and show it's excluded from `overturns_per_game` and present in the co-report.

## 3. Rulings on the flags

- **F1, horizon value in outcome units: accepted.** −1 in outcome units is a loss, and it's consistent with Stage 1's stamps. The settings comment states the mapping (score = (outcome + 1)/2), and the flip fixture's comparison arm (0.0, which equals 0.5 in score units) is correctly labeled.
- **F2, live life totals as tallies: accepted.** The life-differential read is computed where it's registered, from per-world L3 rows. The live `horizon_life` tallies are a diagnostic, and per-world live capture isn't needed.
- **F3, natural draws priced at the horizon value: accepted, and it's the right convention.** A natural draw also scores 0 match points, so pricing only horizon draws at −1 would be inconsistent. `n_draws` and `n_horizon` both land on the row, so the split stays auditable.
- **F4, pre-gate seeds 8501–8510: accepted.** The pre-gate is an action-identity regression, not a performance measurement, so reusing the standard block is correct. **Co-report, not required:** if the published round-7 pre-gate raw rows cover the same seeds, show raw seat-1 gamelog equality against them. It's a free cross-round check that the tree is the same.
- **F5, L3 children at 8000 hooks and 180 s: accepted.**
  - L3 audits the calibrated teacher, so its children should run under the teacher's bounds.
  - Under the horizon the bounds are inert. The largest Stage 1 hook count was 1,781, and per-candidate walls run well under 180 s even at W = 50.
  - Any deadline or hook abort would surface in the unfinished tallies, which are already reported.
  - The unparameterized label default stays proven separately.

## 4. Notes (non-blocking)

- **Outcome co-reports.** The games report's points use draw = 0.5, which is right for the fleet comparison (216.0). Print the draw = 0 points (W only) on the same line, since that's the settled tie value.
- **L3 coverage.** `stage2_analyze.py` should print the jobs that produced no shared finished world beside `jobs`, so the coverage of the overturn population is visible next to the read.

**Scope:** the two §2 items (pre-gate gate with manifest fields, and the completed-games rate), each with its fixture, come back in one commit for a confirmation check. Stage 2 then runs on Joe's go with launched sha == approved sha, pre-gate first. No run is approved yet.
