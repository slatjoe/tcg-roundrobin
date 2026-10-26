# Round 9 — Stage 0 report fix (claude-reply-2db6b77 sec.2 + sec.3)

**Parent package:** 2db6b77f (Stage 0 launch package); **review:**
bf71c09a. **Status:** REVIEW-GATED — nothing here runs a
measurement. The fix is to code/stage0_report.py (plus fixture
scaffolding); the primary read is the stock scorer's output and
does not change, and the report's cross-check against the
scorer's standalone run is untouched code.

## 1. The sec.2 change set (blocking)

The old report treated every error row as one undifferentiated
class: counted apart, never in a share, and dropped from the
sensitivity read. On Gravy that excluded exactly the worlds
Stage 0 exists to inspect — FX7's OFF set read 0% unfinished
with 28 of 300 worlds dead. The fix:

- An explicit REFUSAL-class list in stage0_report.py
  (REFUSAL_CLASSES), verbatim:
    canary_hook_failed
    det_persist_failed
    det_verify_failed
    det_verify_hook_failed
  These are determinization refusals: excluded from both the
  unfinished share and the sensitivity read, tallied separately
  by class.
- EVERY other error class — abort, timeout, and any unlisted
  string (the unlisted default is NON-TERMINATION) — counts as
  UNFINISHED: it enters the unfinished share with denominator =
  all rows minus refusals, and is priced as a draw (0.5) in the
  sensitivity read. A row with no usable result is unfinished
  under the pseudo-class null_result.
- The sensitivity pairing keeps a world unless either side's
  row is a refusal (was: unless either side carried any error).
- Per-class error tallies are printed in the report, for each
  pass the report is invoked on (primary and horizon alike —
  sec.3.2's residue requirement is met by the same section).
- Code hunks: docstring (taxonomy + guard); REFUSAL_CLASSES and
  classify() added; the aggregation loop's "error" kind replaced
  by classify() with per-role class tallies; sensitivity skip
  condition changed from any-error to refusal; print sections
  gain refusal counts and the ERROR TALLIES BY CLASS block; JSON
  gains error_classes. Primary aggregation, summarize and the
  1e-9 cross-check: untouched.

## 2. The sec.3 additions

1. World-count guard: the report asserts exactly 50 rows per
   (job, candidate) over the pass's label files and aborts
   (exit 2, naming pass, job, candidate and the actual count)
   otherwise — neither label driver pins W on its jobs, so a
   truncated label file can no longer shrink the paired n
   silently. The guard runs before the scorer aggregation.
   One implementation detail, disclosed for the confirmation
   check (sec.3 below): the expected count is a parameter,
   --expect-rows, DEFAULTING to 50; the Stage 0 runner passes
   no override, so the registered run asserts exactly 50 as
   specified.
2. The horizon pass's own residue: the per-class tallies and
   unfinished accounting print for every pass invocation,
   including the horizon pass (exercised synthetically by
   fixture FX-R3 under --pass-name horizon).

## 3. The disclosed deviation: the guard meets the synthetic suite

The launch package's synthetic fixtures (FX1-FX6) build
4-world-per-candidate sets, so the sec.3.1 guard as literally
specified (assert 50) aborts every synthetic case before any
check runs. Rather than rebuild the registered suite at W=50
(several of its planted proportions — e.g. FX2's 2-of-4
unfinished — have no integer form at 50, so its hand-computed
expectations would all move), the guard takes --expect-rows
with default 50 and fixtures/run_fixtures.py passes 4
explicitly (a one-line harness change). The production path is
unchanged: no override anywhere in run_stage0_l3.sh, the
default is 50, and FX-R5 proves the guard fires at the default
on a 49-row candidate. Flagged here for the confirmation check
to rule on; if the reviewer prefers the literal form, the
parameter comes out and the suite is rebuilt instead.

Also verified at execution, closing a question the staging pass
left open: no FX1-FX6 case builds error rows (rows_for defines
an ('e',) -> {"error": "abort"} spec but no case uses it), so
the sec.2 taxonomy changes NO original FX expectation — the
suite's unfinished worlds are finished==0 rows throughout.

## 4. Fixtures — verbatim results (execution pass, 2026-10-25)

- FX1-FX6 (fixtures/run_fixtures.py): **FIXTURES: ALL PASS** —
  every original expectation, unchanged.
- fx_report_fix.py (new): FX-R1 refusal / FX-R2 timeout /
  FX-R3 unlisted class / FX-R4 denominator / FX-R5 guard —
  **FX-REPORT-FIX: ALL PASS**.
- fx7_rows_check.py (new) on FX7's own OFF rows, fetched from
  the box's durable build-test artifacts (/tmp/r9s0_fx7/:
  jobsBoff_p1+p2 merged, labelsBoff.jsonl; independent count of
  the fetched rows before the check: 272 finished, 28 errors,
  all abort — the FX7 record exactly; nothing was regenerated):
  **FX7-ROWS: ALL PASS**, and the report block itself reads:

```
  teacher rows 150: finished 134, unfinished 16, refusal 0; share 0.1067
  prior   rows 150: finished 138, unfinished 12, refusal 0; share 0.0800
  pooled : finished 272, unfinished 28, refusal 0; share 0.0933
  abort                      28  [unfinished]
  SENSITIVITY ... jobs 3 over 150 worlds; mean paired diff 0.0333
  PRIMARY ... mean paired diff 0.0324
```

  The pooled unfinished share is the review's required
  28/300 = 9.3% (was 0% under the old definition, on the same
  rows), and the sensitivity read now differs from the primary
  where the 28 fall. (The 3-job primary/sensitivity means are
  build-test mechanics on a fixture set, not a measurement.)

## 5. Clause-list delta

Against the launch package's clause list: the sec.1 (D)
reporting clause was marked DONE for the old taxonomy; as
amended by sec.2 it remains DONE in its corrected form. Two
clauses are added by the review and are DONE by this fix: the
sec.2 error taxonomy (refusal list, non-termination default,
sensitivity pairing rule, per-class tallies) and the sec.3
additions (world-count guard; horizon-pass residue). Clauses 8
(sec.4(C) parameterization) and 9 (ghost pre-gate) are
unaffected and remain NOT DONE by scope, owed with the Stage 1
/ pre-Stage 2 packages.

## 6. Hashes

- code/stage0_report.py: 5019d94e… -> 5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf
- fixtures/fx_report_fix.py (new): 8db0d1ac51f7b817acd76484b033e0ab87c57886a5156f7c1e65925a6240b33b
- fixtures/fx7_rows_check.py (new): 58d1fa1fab24aebf4e3715552922bf723260c6a06db243b95f114003f1766899
- fixtures/run_fixtures.py: cf. launch package -> 0eaa2348aafb403350476c636485036e7a01c356509ba0a78edb635a27af99d7 (the one-line --expect-rows harness change, sec.3)
- fixtures/README.md: appended the report-fix section.

## 7. The ask

Confirmation check on this file only: stage0_report.py as
amended (sec.2 taxonomy + sec.3 additions), the fixtures, and
the sec.3 deviation. On confirmation, Stage 0 launches on Joe's
go — which Joe has already given (2026-10-25 20:29 EDT, banked
against this confirmation): the launch manifest will record
the approved sha and the go together.
