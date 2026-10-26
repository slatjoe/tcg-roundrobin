# Round-9 Stage 0 fixtures

Synthetic job/label sets with hand-computed expectations, run
against the package's own code (`code/stage0_report.py`, the
deployment scorer, and the runner's pin guard extracted verbatim
from `code/run_stage0_l3.sh`), plus one box build test of the D7
horizon (FX7). Run locally with:

```
python3 fixtures/run_fixtures.py
```

(exit 0 iff every check passes; FX7 is a box build test, run
separately — its script and log are described below.)

## FX1 — primary read, all finished

2 games × 2 jobs, W=4, every world finished. gA jobs: teacher
outcomes +1 (score 1.0), prior 0 (score 0.5) → per-job diff +0.5.
gB jobs: teacher 0, prior +1 → diff −0.5.
By hand: mean diff 0; frac_pos = frac_neg = 0.5; unfinished shares
0; paired-n = 4 for every job; sensitivity = primary = 0; verdict
not instrument-limited.

## FX2 — unfinished accounting + draw sensitivity

1 game, 2 jobs, W=4.
Job 1 — teacher: finished(+1), finished(+1), unfinished,
unfinished; prior: finished(0), finished(0), finished(0),
unfinished. Primary shared finished worlds: w0, w1 → diff +0.5,
paired-n 2. Sensitivity worlds (both candidates non-error):
w0 +0.5, w1 +0.5, w2 (teacher draw 0.5 vs prior finished 0 → 0.5)
0.0, w3 (0.5 vs 0.5) 0.0 → sensitivity diff +0.25.
Job 2 — teacher all finished(−1), prior all finished(+1) → diff
−1.0 in both reads, paired-n 4.
By hand: primary mean (−0.25); sensitivity mean (−0.375);
unfinished shares: teacher 2/8 = 0.25, prior 1/8 = 0.125, pooled
3/16 = 0.1875 ≤ 0.20 → verdict NOT instrument-limited; paired-n
min 2, max 4, median 3.

## FX3 / FX3b — the instrument-limited line

FX3: 1 game, 2 jobs, planted primary diffs 0, pooled unfinished
10/16 = 0.625 > 0.20 → the report must print INSTRUMENT-LIMITED.
FX3b: same zero diffs, pooled unfinished 2/16 = 0.125 → the
verdict must NOT be instrument-limited. (FX3b job 1: teacher one
unfinished world; job 2: prior one unfinished world; all finished
outcomes 0.)

## FX4 — a positive read stands

1 game, 2 jobs; wherever both candidates finish, teacher +1 vs
prior −1 → per-job primary diff +1.0; single game ⇒ the
cluster bootstrap is degenerate, CI [1.0, 1.0]. Pooled unfinished
6/16 = 0.375 > 0.20, but the read is positive → verdict POSITIVE,
stands; NOT instrument-limited.

## FX5 — pin-format guard (round-8 W-check lesson)

The runner's `expect_hash` is extracted verbatim from
`code/run_stage0_l3.sh` (between the PINFN markers) and exercised:
a 62-char pin aborts on the format guard; a 64-char wrong-value
pin aborts on mismatch; the correct pin passes.

## FX6 — scorer self-test + the O3 substitution

`analyze_l3_deploy.py --self-test` must print its stock PASS, and
the deployment copy must read DELTA = 0.0075 with TEACHER_GAMES =
400 (the full substitution diff is
`fixtures/analyze_l3_deploy_diff.txt`).

## Recorded results — local fixtures (2026-10-25)

```
PASS: FX1 mean_diff == 0 got 0.0
PASS: FX1 frac_pos == frac_neg == 0.5
PASS: FX1 shares all 0
PASS: FX1 paired-n all 4
PASS: FX1 sensitivity == 0
PASS: FX1 verdict not instrument-limited
PASS: FX2 primary mean == -0.25 got -0.25
PASS: FX2 sensitivity mean == -0.375 got -0.375
PASS: FX2 shares 0.25 / 0.125 / 0.1875 got 0.25/0.125/0.1875
PASS: FX2 paired-n min 2 max 4 median 3
PASS: FX2 verdict not instrument-limited (0.1875 <= 0.20)
PASS: FX3 primary mean == 0
PASS: FX3 pooled share == 0.625 got 0.625
PASS: FX3 verdict INSTRUMENT-LIMITED
PASS: FX3b pooled share == 0.125 got 0.125
PASS: FX3b verdict NOT instrument-limited
PASS: FX4 primary mean == +1.0, CI degenerate [1, 1] got 1.0 [1.0, 1.0]
PASS: FX4 pooled share == 0.375 got 0.375
PASS: FX4 verdict POSITIVE stands, not instrument-limited
PASS: FX5 62-char pin aborts on format rc=1
PASS: FX5 wrong-value pin aborts on mismatch rc=1
PASS: FX5 correct pin passes rc=0
PASS: FX6 scorer self-test passes SELF-TEST PASS: aggregation, pairing, score conversion, cluster bootstrap all reproduce planted values
PASS: FX6 deploy DELTA == 0.0075, TEACHER_GAMES == 400
FIXTURES: ALL PASS
```

## FX7 — horizon OFF-equivalence + ON mechanics (box build test)

Three real jobs from the vaulted file (first B, first P, first ARS
branch jobs, distinct games), W=50, seed base 855001, production
servers serving ckpt_v10:

- run A: pristine fleet tree + pristine `meas_label_main.php`;
- run B-off: horizon tree (`code/search_horizon.php`) + r9 driver,
  LABEL_HORIZON=off, jobs stamped `"horizon": 0`;
- run B-on: same tree/driver, LABEL_HORIZON=62, jobs stamped 62;
- negative: pin 62 against jobs stamped 0 must abort (exit 2)
  before labeling — the (C) pinned-parameter mismatch rule.

OFF-equivalence compares the full (snap, cand, world, result)
tuples of A vs B-off — they must be identical. ON mechanics: every
row stamped `"horizon": 62`; every result marked `"horizon": 1`
has finished = 1 and outcome 0.0; the ON finished count is at
least the OFF finished count. Build test only: three jobs say
nothing about the Stage 0 read.

Results (box, 2026-10-25; jobs: B `359158031_t2` player 1,
P `190554034_t1` player 1, ARS `308484385_t1` player 2; 300
worlds per run; servers serving ckpt_v10, load-verified):

- Run A and run B-off agree on **every field of every world**
  except the horizon build's own result marker: B-off's
  non-error results carry `"horizon": 0`, a key the pristine
  build does not emit. The 272 non-error tuples differ only in
  that key; the 28 error tuples are identical, and the error
  *set* is the same 28 (snap, cand, world) tuples in both runs.
  Winner, outcome, finished, turns, hooks, fallbacks and
  child_state match 300/300. OFF reproduces the primary
  construction.
- Run B-on: 300 finished / 0 unfinished / 0 error (OFF: 272 /
  0 / 28). The 28 `"horizon": 1` worlds are **exactly** the 28
  tuples that are error rows under OFF — each had crossed the
  trigger before dying on the hook budget (exit turns 62–227);
  every marked world has finished = 1 and outcome 0.0; every row
  is stamped `"horizon": 62`; the 272 unmarked worlds match run
  A on all scoring fields.
- Negative test: pin 62 against jobs stamped 0 aborted with
  exit 2 before labeling ("ABORT: job for snap 359158031_t2
  carries horizon 0 != LABEL_HORIZON pin 62").

Side observation: the build test ran no (C) sweepers; the box's
shared-memory segment count went 3 → 62 across the test (dead
label children leave segments, the standing Talishar behavior
the sweeper exists to attribute). The real runner runs one
sweeper per label tree.

## Report-fix fixtures (claude-reply-2db6b77 sec.2/sec.3)

The review's error-taxonomy fix is exercised by two additions:

- `fx_report_fix.py` — synthetic cases FX-R1..FX-R5 with
  hand-computed expectations: a refusal-class case
  (canary_hook_failed: excluded from shares and sensitivity,
  tallied [REFUSAL]); a timeout case (counted unfinished,
  priced 0.5 in the sensitivity read: 0.9000 against the
  finished-pairs primary); an unlisted-class case
  (segfault_in_child: the default is non-termination, identical
  treatment to timeout, run under the horizon pass name so the
  per-pass tallies of sec.3.2 are exercised); a denominator case
  (refusals leave the share denominator: 10/(30+10) = 0.2500);
  and the sec.3.1 world-count guard failing on a 49-row
  candidate (exit 2, guard line naming the count).
- `fx7_rows_check.py` — the fixed report run on FX7's own OFF
  rows. Expectations from the FX7 record (272 finished, 28 abort
  errors, all past turn 62): pooled unfinished 28/300 = 0.0933,
  refusals 0, abort tallied [unfinished], and a sensitivity read
  that differs from the primary where the 28 fall.

FX1-FX6 regression note: the sec.2 change moves an expectation
only where a case's rows carry error classes. Verified at the
fix's execution pass: no FX1-FX6 case builds error rows (the
rows_for helper defines an ('e',) -> {"error": "abort"} spec but
no case uses it; the cases' unfinished worlds are finished==0
rows), so all original FX1-FX6 expectations stand unchanged and
the regression reads ALL PASS. The one interaction the fix did
have with the suite is the sec.3.1 guard: the synthetic cases
use 4 worlds per candidate, so the guard takes an
--expect-rows parameter (default 50, the registered width; the
runner passes no override) and run_fixtures.py passes 4
explicitly. See stage0-report-fix.md sec.3 for the disclosure.
- `fx_tie_as_loss.py` — fixture for code/tie_as_loss.py (the
  sec.3 tie-as-loss co-read). Three planted jobs over two
  games with hand-computed expectations in both modes:
  standard mean 0.625/3 vs tie-as-loss 0.5/3, per-job diffs
  (+0.375/+0.25/0.0 -> +0.5/+0.5/-0.5), 3 paired drawn worlds
  per candidate role, and the population rules exercised
  (error row, finished==0 row, unpaired world and a duplicate
  world all excluded or counted exactly as the registered
  scorer counts them). Standalone: run it directly; exit 0
  iff all 12 checks pass. Result at the Stage 0 build:
  ALL PASS.

## Stage 1 fixtures (claude-reply-16f02e2 sec.4; clause 8)

Five suites, 66 PASS lines, ALL PASS locally 2026-10-26
(rerun in full after the `claude-reply-edddf5e` fix pass;
verbatim transcript: `fx_stage1_outputs.txt`). The PHP
suite ran on a user-space PHP 8.3.6 (deb extraction); the
box runs PHP 8.5.4 and every Stage 1 PHP file also lints
clean under 8.3.6.

- `fx_s1_eval/` — clause 8's first placement against the REAL
  `code/s1_eval_main.php`, driven through a stub `play_game.php`
  (synthetic `SimLabel_RunForSnapshot`). 20 PASS lines: the happy
  path stamps every world row and stat row with the full
  setting tuple; the stub's cfg log proves the pins reach the
  label machinery (hookBudget/deadlineS/horizon/W/pair from the
  env pins; seedBase 885001 + job index x 100003); stat
  accounting on a job with a drawn world and abort errors
  (22 finished = 21 decisive + 1 draw, errors {abort: 6});
  and four abort cases (job/pin hooks mismatch, missing job
  setting, malformed `EVAL_HORIZON_VALUE`, malformed
  `EVAL_HOOKS`) — each exits 2 with ABORT logged and NO rows
  written.
- `fx_stage1_analyze.py` — `code/stage1_analyze.py` on planted
  rows, 25 checks. The completion metric is PER-STATE (a
  state completes iff every selected candidate reaches the
  validity floor); the candidate-level rate and the pooled
  finished share are diagnostics. Scenario A: per-state
  0.75 vs candidate-level 0.875 vs pooled 0.97 — the
  setting must NOT qualify, and does not; the same states
  prove the valuation flip (challenger 15W/5 draws/5L vs
  prior 15W/10L: overturn at draw = 0.5, none at draw = 0,
  means 0.4 vs 0.2 exactly as planted) and the p95
  selection tie-break (P2 over P1 at equal mean 6.0).
  Scenario B proves the max tie-break (equal mean 8.0 and
  p95 20.0; max 23 beats 24). Scenario C: NO CALIBRATED
  SETTING at per-state 0.5, and a corrupted row tuple
  aborts the analyzer (exit 2). Scenario D is the
  review's divergence plant (`claude-reply-edddf5e`
  sec.1): a setting at candidate-level exactly 0.95 but
  per-state 0.90 does NOT qualify, its per-state-0.95
  twin does, and the cheaper non-qualifier is not
  selected. Scenario E (review sec.2): B0 completes
  every state and is the cheapest setting — it is read
  as the control and the selection skips it for the +H
  setting.
- `fx_b0_gate.sh` — the runner's B0 stop condition
  (`claude-reply-edddf5e` sec.4.4), 10 checks. The
  fixture extracts the B0GATE block from
  `code/run_stage1.sh` verbatim and executes it against
  planted B0 outputs: intact rows pass the gate (exit
  0, gate report written); a stat row corrupted against
  its world rows makes the analyzer abort inside the
  block and the block stops the run (exit 1, before the
  +H settings); a B0-only invocation and a +H iteration
  are no-ops.
- `fx_build_panel.py` — `code/build_panel.py`, 5 checks:
  first-N-in-capture-order with the per-game cap respected;
  the cap binding before a shortfall (exit 3, report marked
  incomplete); a capture row without `selected` aborts
  (exit 2); a duplicated snap aborts (exit 2).
- `fx_merge_registry.py` — `code/merge_registry.py`,
  6 checks: clean merge with backup + vault copy and the
  printed sha256 equal to the merged file's; same-tag
  re-merge is a no-op; a retag conflict aborts (exit 1)
  leaving the registry byte-identical.
