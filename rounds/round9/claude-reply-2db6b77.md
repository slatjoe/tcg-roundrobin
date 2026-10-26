# Claude — code review of the round-9 Stage 0 launch package

**Reviewed commit:** 2db6b77f1651b9811c361708da09ab52da4c7e9b (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-8dddf38.md` hashes to `df0cf16c…dbb8ea`, the value I gave Joe.
**Package:** `rounds/round9/stage0-launch-package.md`, `rounds/round9/code/`, `rounds/round9/fixtures/`.

**Verdict: CHANGES REQUESTED, one blocking item.** The (D) reporting excludes **error rows** from the unfinished share and from the draw-sensitivity read. On Gravy, the error rows (hook-budget `abort`s) **are** the non-terminating worlds, so as built the registered 20% condition can't see the population it exists for (§2). Everything else is accepted, and so are the five §9 asks except the sensitivity-pairing exclusion.

## 1. Accepted

**The code.** Every file hashes to the §3 table.
- `analyze_l3.py` is **byte-identical** to round 4's (`16017ffa…`).
- The deployment copy differs by the one line, DELTA 0.2525 → 0.0075.
- `meas_label_main.php` is the registered `3109176b…`.

**The pin audit (my standing check):** all 21 hex literals in `run_stage0_l3.sh` are exactly 64 characters, and every distinct pin traces to a file in the package or to a registered value. `ParseGamestate.php` `0e88dd58…` is a new box-side pin, first registered in this package, and accepted.

**The §4 determination:** accepted. Error rows carry no turn, so whether a dead world crossed 62 is unrecoverable offline, and the in-child horizon with a second pass is the forced route. The patch is four hunks inside `SimLabel_*`, and Decide is untouched.

**The horizon semantics:** accepted as built.
- **The precedence rule:** a world that ended keeps its own outcome, and the horizon prices only worlds still running at absolute `currentTurn ≥ 62`, as a draw (`outcome 0`, `finished 1`). That's the instrument's own rule: a real game decided before turn 62 is decided, and one still running at the trigger is a draw.
- **The pin:** `off` or a non-negative integer, jobs must match it (exit 2), and every row is stamped.

**FX7 is strong evidence:** the OFF construction reproduces the primary field for field on 300 worlds, and ON finishes 300/300, with the 28 horizon draws being exactly the 28 OFF error tuples (all of which had crossed turn 62).

**Also accepted:**
- **The seed family** 875001 + shard × 10⁸.
- **Clauses 8–9:** the per-setting parameterization goes to the Stage 1 package and the ghost pre-gate before Stage 2's live games. Owed there, not waived.

## 2. Blocking: error rows must count as unfinished (except refusals)

`stage0_report.py` counts `unfinished` only as non-error rows with `finished = 0`, the guard and stuck exits. Error rows "never enter a share", and the sensitivity read drops any world where either candidate errored. **FX7 shows why that's wrong:** the OFF run had **272 finished, 0 unfinished and 28 errors**, and all 28 errors were hook-budget deaths of worlds already past turn 62. Under the current definition, that job set's unfinished share is **0%**, and its sensitivity read equals the primary, though 9.3% of its worlds never ended. In the fleet, 37,038 candidate aborts were recorded. **The 20% condition would almost never fire.**

The error classes split into two kinds, which must be treated differently:
- **Non-termination: `abort` (the hook budget), `timeout` (the candidate deadline), and any error not in the refusal list below.** The world was sampled and played, and it didn't end within bounds. These **are unfinished**: they count in the unfinished share, and the sensitivity read prices them as draws (0.5).
- **Determinization refusals: `canary_hook_failed`, `det_persist_failed`, `det_verify_failed`, `det_verify_hook_failed`.** The world was never validly constructed (the round-8 canary note). These stay **excluded** from both reads and are tallied separately, as now.

**Required:**
- `stage0_report.py` gets an explicit refusal-class list (with the unlisted-error default as non-termination) and the per-class tallies printed.
- The unfinished share's denominator is all rows minus refusals.
- The sensitivity pairing keeps a world unless either side is a refusal.
- **A fixture on FX7's own rows:** the OFF set must read unfinished **28/300 = 9.3%**, and its sensitivity read must differ from the primary where those 28 fall.
- The primary read is the stock scorer's and doesn't change.

## 3. Two small additions (non-blocking, in the same commit)

1. **World-count guard:** neither driver pins W on jobs (`r9_label_main.php` defaults `LABEL_W` to 25 if unset). The runner sets 50 for both passes. Have `stage0_report.py` assert **50 rows per (job, candidate)** in each pass, and abort otherwise.
2. **The horizon pass's own residue:** report its error and unfinished tallies by class. Expect about 0 aborts, since the horizon should end those worlds first, but a world can still cross 62 and exhaust its hooks within one drive step, and below-62 guard or stuck exits remain unfinished under the horizon too. Print them, so the co-report's completeness is shown, not assumed.

## 4. Rulings on §9

- **The §4 determination and the in-child route:** accepted.
- **The horizon precedence rule:** accepted.
- **The sensitivity pairing's exclusion of error worlds:** **rejected** for non-termination errors, accepted for refusals (§2).
- **The horizon seed family:** accepted.
- **Clauses 8–9 scoped to Stages 1 and 2:** accepted.

**Scope:** this review approves the package except `stage0_report.py`, which comes back with the §2 fix and fixture and the §3 additions, for a confirmation check. Stage 0 then launches on Joe's go. No run is approved yet.
