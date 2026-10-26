# Round 9 — Stage 0 report

**Run:** L3 audit of the round-7 fleet's 118 overturn decisions
(88 games), LABEL_W=50, CRN, production server, two passes —
primary (byte-pristine driver) and the D7 horizon co-report
pass (LABEL_HORIZON=62). Launched 2026-10-25 at commit
**5646e695** on Joe's banked go; completed the same evening.
All figures below are from the run's own report files and from
the builder's verified recomputation on the published label
rows (data/stage0/, with MANIFEST.md). Stage 0 measures the
CONDITIONAL quality of the fleet teacher's overturns; with the
fleet Δ at +0.0075 it is not a share-of-Δ impeachment, and
nothing here re-opens the round-7 ruling.

## Headline

**Stage 0 is POSITIVE in both passes, and NOT
instrument-limited.** On the worlds both picks finished, the
teacher's overturned picks outscore the prior's picks by a
mean paired difference of **+0.0800** (primary) and
**+0.0701** (horizon) over the 118 jobs, both CIs clear of
zero; at the fleet's 0.295 overturns/game
that is +0.0236 / +0.0207 expected win-probability per game
from overturn quality alone. The primary pass's pooled
unfinished share is 12.12% — under the registered 20%
instrument ceiling — and a positive read stands regardless
under the registered condition. The D6 trigger (a Stage-0
null that is NOT instrument-limited) does not arise.

## 1. Primary read (primary pass)

Scorer: analyze_l3_deploy.py (the fleet's own scorer,
DELTA=+0.0075), imported by stage0_report.py and cross-checked
against its standalone run: **AGREE (1e-9)**.

| quantity | value |
|---|---:|
| jobs scored | 118 of 118 (missing 0) |
| mean paired diff | **+0.0800** |
| CI (game-clustered bootstrap) | [+0.0444, +0.1206] |
| frac jobs better / tied / worse | 0.6102 / 0.1186 / 0.2712 |
| per-game gain (× 118/400 = 0.295) | **+0.0236** |

The scorer's own registered line (claude-reply-94b9449 sec.4,
DELTA = +0.0075, half-Δ = 0.00375): "READ: converts; per-game
gain from overturn quality alone covers at least half of
Delta."

## 2. Instrument validity — registered condition (D)

Taxonomy as fixed in the report fix (a00dad50): non-termination
errors (abort, timeout, any unlisted class) count as
unfinished; the four determinization refusal classes are
excluded from every share and tallied separately. **No refusal
rows occurred in either pass.**

Primary pass, per candidate (5,900 rows each):

| candidate | finished | unfinished | refusal | share unfinished |
|---|---:|---:|---:|---:|
| teacher pick | 5,202 | 698 | 0 | 0.1183 |
| prior pick | 5,168 | 732 | 0 | 0.1241 |
| **pooled** | 10,370 | 1,430 | 0 | **0.1212** |

Error classes, pooled: **abort 1,430** [unfinished]; nothing
else. (The scorer's integrity block counts these same 1,430 as
error_rows; its separate "unfinished" counter is 0 because
every unfinished world here arrived as an abort error rather
than a finished==0 row.)

Paired-n (finished worlds shared by both candidates, per job):
min 26, p25 37.0, median 40.0, mean 40.35, p75 43.75, max 50;
buckets: n=50 → 8 jobs, 40–49 → 62, 20–39 → 48, 1–19 → 0.

Sensitivity read (unfinished worlds priced as draws, 0.5;
pairs dropped only on a refusal — none): 118 jobs over 5,900
worlds; mean paired diff **+0.0773**, CI [+0.0418, +0.1167],
per-game gain +0.0228. The read barely moves when the
unfinished worlds are priced in as draws.

**Determination:** pooled unfinished share 0.1212 ≤ 0.2000,
**so the instrument-limited clause is not engaged**; and the
primary read is positive (mean > 0, CI lower > 0), so under
the registered condition (claude-reply-8dddf38 sec.1) **the
read stands regardless of the unfinished share. Stage 0 is
NOT instrument-limited.**

## 3. Horizon co-report (D7 pass)

Same 118 jobs, driver r9_label_main.php with LABEL_HORIZON=62:
a world reaching absolute currentTurn ≥ 62 ends outcome=0
(draw), finished=1. Seed bases 875001 + shard×10^8.

| quantity | value |
|---|---:|
| jobs scored | 118 of 118 (missing 0) |
| mean paired diff | **+0.0701** |
| CI | [+0.0361, +0.1088] |
| frac jobs better / tied / worse | 0.6441 / 0.0508 / 0.3051 |
| per-game gain | **+0.0207** |

Unfinished: teacher 1 abort, prior 1 abort, refusals 0;
**pooled share 0.0002** (2 of 11,800 rows). Paired-n: min 49,
median 50, mean 49.98 (116 jobs at n=50, 2 at 49). Sensitivity
read: +0.0702 [+0.0362, +0.1090], per-game +0.0207 — the
horizon leaves almost nothing unfinished, so the two reads
coincide. Determination as in sec.2: positive, stands;
not instrument-limited.

Residue tallies for this pass (report-fix sec.3.2): the only
error class present is abort ×2, reported above; refusals 0.
The scorer's integrity counter sums result.fallbacks over
non-error rows: 219 in this pass (7 in the primary pass).

## 4. Tie-as-loss co-reads (sec.3 registration)

Registered in claude-reply-a00dad5 sec.3 (recorded in
stage0-launch.md): a second version of each read, computed
offline from the published label rows, draws scored as losses
(world score 0 for winner == 0, finished or horizon == 1)
instead of 0.5. Report-only; decides nothing at Stage 0.

Method (code/tie_as_loss.py): identical population, pairing,
aggregation and game-clustered bootstrap as the registered
read (analyze_l3_deploy imported, unmodified); the only
change is the draw price. Draws are identified by the label
rows' winner field; a consistency check over every finished
row confirms winner == 0 iff outcome == 0 (violations: 0 in
both passes). Before producing any tie-as-loss figure, the
scorer recomputes the STANDARD read through the same code
path and asserts agreement with the box report to 1e-9 —
both passes pass. Fixture: fixtures/fx_tie_as_loss.py, three
planted jobs with hand-computed expectations in both modes
(12 checks): **ALL PASS**. Machine-readable outputs:
data/stage0/tie_as_loss_primary.json / tie_as_loss_horizon.json.

**Primary pass — the tie-as-loss read is identical to the
standard read: +0.0800 [+0.0444, +0.1206], per-game +0.0236.**
Reason, from the rows: the primary pass contains **zero drawn
finished worlds** — all 10,370 finished rows have outcome ±1
(5,195 wins / 5,175 losses for the deciding side). In this
pass the worlds that would have drawn are precisely the ones
that never finished (the 1,430 aborts). Re-pricing draws
moves nothing because there are no finished draws to re-price.

**Horizon pass — tie-as-loss: +0.0712 [+0.0358, +0.1113],
per-game +0.0210** (standard: +0.0701 [+0.0361, +0.1088],
+0.0207). Frac jobs better/tied/worse moves 0.6441/0.0508/
0.3051 → 0.6017/0.1356/0.2627. The pass holds 1,448 drawn
finished rows, **every one of them horizon-ended**
(horizon == 1, winner == 0 — no exceptions); 1,447 sit in the
paired population (717 teacher-pick worlds, 730 prior-pick
worlds; one drawn row sits opposite an aborted world). The
prior pick draws slightly more often than the teacher pick,
so pricing draws as losses nudges the read UP by +0.0011:
under tie-as-loss the overturns look marginally better, not
worse. What the horizon itself is worth is visible by
comparing passes: it converts the primary pass's 12.12%
unfinished into finished drawn worlds, at a small cost to
the mean (+0.0800 → +0.0701 standard) because those worlds
enter the read priced 0.5 instead of being excluded.

## 5. Provenance and integrity

- Authorization: design approval c76f6856; launch package
  2db6b77f; code review bf71c09a; report fix a00dad50;
  confirmation 71c91f14 (pin remedy pre-authorized in its
  sec.2); Joe's go 2026-10-25 20:29 EDT. Launched sha
  **5646e695** (differs from the approved chain only by the
  one pin line plus round9 notes, as the confirmation's
  extension specifies).
- Times (EDT, 2026-10-25; the runner log carries no
  timestamps — these are the OUT artifacts' own): first run
  artifacts 20:45; primary label files complete 21:18:05;
  horizon label files complete 21:36:46; stage0_manifest.json
  written 21:36:48, run complete.
- Jobs: the vault file /home/joe/tcg/registry-vault/
  jobs_all_gravy_fleet_l3.jsonl, sha256
  5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b
  — 118 jobs over 88 games (verified from the published job
  files). Runner-assembled copies: jobs_all.jsonl
  (117792c5…), jobs_all_h.jsonl (cf8b6bc7…, adds "horizon": 62).
- Server: production /home/joe/tcg/tcg-sim/rl/search_server.py,
  sha256 81ef2cdb… (the label path's server, per the R12
  placement), serving ckpt_v10 (44f1e5d7…).
- Deployed code (deployed_code_hashes.txt, all hash-verified
  pre-launch): run_stage0_l3.sh 4f5f8183…, stage0_report.py
  5c7e5393…, analyze_l3_deploy.py 3919bbb8…,
  meas_label_main.php 3109176b…, r9_label_main.php 2463fc29…,
  search_horizon.php 6d63f5c3…, shm_sweep.py 98027a8b….
- Parameters: LABEL_W=50 both passes; primary seed bases
  855001 + shard×10^8; horizon seed bases 875001 +
  shard×10^8; LABEL_HORIZON=62 (horizon pass only). Pre-launch
  G8 sweep cleared SHM segments 62 → 0.
- Row counts: 11,800 label rows per pass = 118 jobs × 2
  candidates × 50 worlds; the report's world-count guard
  (exactly 50 per (job, candidate)) passed both passes.
  Integrity per pass (scorer): error rows 1,430 / 2;
  null results 0; unknown snaps 0; duplicate worlds 0;
  jobs missing 0.
- Builder verification: the transferred label/report files'
  sha256 match the runner's stage0_manifest.json exactly
  (see data/stage0/MANIFEST.md); a local re-run of the
  deployed stage0_report.py on the transferred rows
  reproduces both box report JSONs **exactly** (every field,
  including both bootstrap CIs); the tie-as-loss scorer's
  standard mode agrees with the box reports to 1e-9 in both
  passes before its co-read is read.

## 6. What this settles, and what it leaves open

Settled: the fleet teacher's overturns were GOOD decisions
under fresh W=50 CRN evaluation — the round-7 null is not
explained by bad overturns, and Stage 0 cannot trigger CLOSE
(positive, not instrument-limited). Per the registered Stage
0 outcome implications, the round proceeds to Stage 1 (the
calibration: whether a Gravy-bounded search makes the
teacher worth its cost at fleet scale), with no D6 k=50
question to put (that trigger required a non-instrument-
limited null). The tie-value input for Stage 1's design is
now on the table with numbers attached: at the horizon, draws
are ~12% of paired worlds (1,447/11,796) and the choice
between 0.5 and 0 moves this read by +0.0011 — Joe and the
builder settle it before Stage 1 is designed, as registered.

Open, untouched by Stage 0 by design: whether calibrated
bounds change the teacher's LIVE overturn rate or quality
(Stage 2's question), and the parked stalemate item — though
the horizon pass is suggestive context for it: 1,448 of
11,798 finished horizon worlds (12.3%) ended only because the
instrument called them draws at turn 62.
