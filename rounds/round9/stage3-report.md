# Round 9 — Stage 3 REPORT (paired calibrated teacher vs raw v10)

**VERDICT: DOES NOT CONVERT** — the analyzer's own word,
from the games runner's read on 2026-10-27 (see §2).
PRIMARY (draw = 0): mean paired diff **+0.0475**,
seed-clustered CI **[0.0000, 0.0950]** over 400 scored
pairs. Reading against the registered bands: CONVERTS
requires CI lower > 0 — the lower bound is 0.0000, so
the interval includes 0 and the band verdict is **DOES
NOT CONVERT**, as printed. It is not HARMS (the CI
upper bound 0.0950 is not below 0), and it is not
INCONCLUSIVE (teacher timeouts 0/400 and pairs out of
the primary 0/400 — both rates 0.0000 against the 0.02
lines). Full precision (`stage3_read.json`): mean diff
0.0475, CI [0.0, 0.095].

The attribution co-report (§4) is a valuation of the
teacher's overturns under the L3 rollout continuation,
not a second gate: its per-game gain (+0.0649) is
positive with a CI excluding 0, but the attribution
ratio against the fleet Δ is printed as **unstable
(Δ CI includes 0)** under the §4 guard — the game-level
verdict above is the one that stands.

## 1. Provenance

- Design `8dddf387` (approved in direction `c76f6856`);
  Stage 0 POSITIVE (`16f02e2e`, ruling `8dce0fac`); the
  tie value settled for round 9 (draw = 0 primary;
  horizon-ended worlds score −1); Stage 1 calibrated the
  setting **H8k-180+H** (report `d7b92fdf`; Claude's
  ruling `508d8c4a`); Stage 2 PROCEED (`d593faf2`,
  ruling `7e3fffbf`) — the L3 valuation Stage 3 exists
  to test at game level (Stage 2: L3 primary +0.0621
  [0.0440, 0.0809], per-game gain +0.1096 at 1.7650
  overturns/game).
- Stage 3 package `c924b19a` → Claude's code review,
  changes requested (`a8b62100`) → fix pass `fdd68d64`
  → **CONFIRMED** (`3cb82748`): launch on Joe's go at
  launched sha == `fdd68d64` (rounds-only difference).
- **Launch** (record `ec5407da`, full record in
  `stage3-launch.md`): Joe's go 2026-10-27 08:01 EDT
  (with tracker, F-S3-3). **Attempt 1** (08:03:29 EDT)
  aborted at the runner's own free-space pre-flight
  AFTER the PREGATE-GATE passed (Stage 2's manifest
  IDENTICAL under this run's pin and tuple): required
  3,749,692,064 B (468,711,508 × 8 trees) against
  3,215,175,680 B available — nothing copied or
  spawned. Cleanup (verify-then-delete, four properties
  per tree) reclaimed 5,300,775,668 B from closed
  rounds' scratch trees; two candidates
  (`distill_wcheck`, `distill_pilot_resume`) were
  skipped — flat run-output directories, not tree
  copies. **Attempt 2** (08:09:25 EDT, pid 1346456;
  the first invocation died in setsid with Permission
  denied — the deployed runner has no execute bit —
  preserved as `games_launch2_execfail.log`, and the
  runner went in through `bash`): all seven
  first-minutes checks pass — gate, free-space
  (9,080,950,784 B available), G8 sweep clean
  (segments 15 → 0), both teacher servers on
  `ckpt_v10.pt` on cuda, 4 teacher drivers, stat rows
  flowing with 0 bad stamps, no ABORT.
- **Games:** teacher arm, seeds 23001–23200 × both
  seats under the pinned tuple, Gravy mirror vs the
  heuristic, instrument parameter 87 / draw trigger
  62; raw arm in its own phase (never concurrent
  with the teacher arm). Completed 2026-10-27
  22:20:49 EDT. **800/800 games completed** (100 per
  block × 8 blocks), **400/400 pairs scored**,
  invalids none on either arm, **teacher timeouts 0**,
  raw rerun rows 0; tuple audit OK over all 37,092
  teacher stat rows (0 bad rows, 0 malformed-pin
  aborts, every row stamped H8k-180+H); registry
  merge → **7,331 games** (sha256 `24156438…`).
- **L3 jobs:** 622 captured overturns over 299
  games (`jobs_all.jsonl` sha256 `e4c03f68…`;
  `jobs_report.json`; shard split 143/152/176/151).
  Labeling at LABEL_W=50, CRN, label tuple L3-W50+H
  (hooks 8000, deadline 180 s, horizon 62, horizon
  value −1, k 50), seed bases **50055001 +
  shard×10⁸** (the fix-pass base, range-disjoint from
  the Stage 0 / Stage 2 families). L3 launched
  2026-10-28 06:55:32 EDT; labeling completed and the
  attribution read ran 2026-10-28 08:52 EDT
  (`l3_manifest.json` written; no read aborts, no
  re-labeling, no games re-run).

## 2. The paired read

The analyzer's output, exactly as printed
(`stage3_read.txt`, sha256 `0bb140ec…`):

```
=== STAGE 3 PAIRED READ (teacher vs raw v10, same seed + seat) ===
RECONCILIATION: pairs attempted 400; teacher stat rows 37092 == games report; tuple audit ok; gamenames unique over 800 completed rows
R14 root-canary refusal records (fallback=canary, no teacher stamp): 8 — root decisions refused by the missing-card conservation check and played down the plain bridge; they write no teacher row
PRIMARY: pairs scored 400 of 400 attempted; mean paired diff 0.0475; seed-clustered CI [0.0000, 0.0950] (B=10000, rng 20261027)
CO-REPORT delta05 (draws 0.5; teacher timeout still 0): mean 0.0300; CI [-0.0138, 0.0725]
CO-REPORT delta_lifediff (life scores from p1life/p2life): mean 0.0200; CI [-0.0275, 0.0700]
CO-REPORT per-seat primary: seat 1 mean 0.0750 CI [0.0000, 0.1500] over 200 pairs; seat 2 mean 0.0200 CI [-0.0400, 0.0800] over 200 pairs
SENSITIVITY (drop teacher-timeout pairs): 0 pairs dropped; primary over 400 pairs = 0.0475
TEACHER TIMEOUTS: 0 of 400 teacher games (rate 0.0000; > 0.02 -> INCONCLUSIVE)
PAIRS OUT of the primary: dropped_raw_timeout 0, excluded 0 (total 0 of 400 attempted, rate 0.0000; > 0.02 -> INCONCLUSIVE)
BANDS: INCONCLUSIVE iff teacher timeout rate > 0.02 or (excluded + dropped) rate > 0.02; CONVERTS iff CI lower > 0; HARMS iff CI upper < 0; else DOES NOT CONVERT.
VERDICT: DOES NOT CONVERT
```

Reading against the registered bands (§4.4 of the
package): the CI [0.0000, 0.0950] includes 0, so the
band is **DOES NOT CONVERT**. The lower bound sits
exactly on 0 — the estimate is positive but the
registered precision does not exclude a null. No
impeachment machinery applies: the primary Δ
(0.0475) is below the +0.25 impeachment line, so the
analyzer's `impeachment` field is null, as printed.

Co-reports, as printed:

- **Draw = 0.5 read:** mean diff 0.0300, CI [−0.0138,
  0.0725] — the old tie price also includes 0.
- **Life-differential read:** mean diff 0.0200, CI
  [−0.0275, 0.0700] — the life-based pricing of
  capped games also includes 0. All three pricings
  agree in sign but none excludes 0.
- **Per-seat primary:** seat 1 mean 0.0750, CI
  [0.0000, 0.1500] over 200 pairs; seat 2 mean 0.0200,
  CI [−0.0400, 0.0800] over 200 pairs. Per-block
  primary means (from `stage3_read.json`): t1a 0.08,
  t1b 0.07, t2a 0.07, t2b −0.03.
- **Drop-teacher-timeout sensitivity:** 0 pairs
  dropped; primary over 400 pairs = 0.0475 —
  identical to the primary, because there were no
  teacher timeouts to drop.
- **Teacher timeouts:** **0 of 400** (rate 0.0000).
  **Pairs out of the primary: 0 of 400**
  (dropped_raw_timeout 0, excluded 0, rate 0.0000).
  Neither INCONCLUSIVE line is near.
- **Reconciliation:** 400 pairs attempted, 400
  scored; teacher stat rows 37,092 == the games
  report; tuple audit ok; gamenames unique over
  800 completed rows. The four published
  `search_stats_<blk>.jsonl` files total 37,100
  lines: 37,092 teacher stat rows + the 8 R14
  root-canary refusal records, named here as
  **canary_refusal_rows = 8** — the class Claude's
  ruling on Stage 2 required future reports to name
  instead of carrying as an unexplained difference.
- **Games outcomes (draw-scored, from the games
  report):** teacher 174W/82D/144L = 215.0 pts over
  400 games (0.5375/game; 174.0 pts at draw = 0, W
  only, 0.4350/game). Per-block at draw = 0.5:
  t1a 57.0, t1b 54.0, t2a 57.0, t2b 47.0. Per-seat:
  seat 1 111.0, seat 2 104.0. Teacher capped games'
  life tallies: ahead 37, behind 42, tied 3
  (life_score_sum 37). The teacher win rate at
  draw = 0 (0.435) sits near Stage 2's unpaired
  teacher figure (87/200 = 0.435) — the caution
  Claude registered in his Stage 2 ruling is not
  contradicted by this fleet.

## 3. Measured phase times (F-S3-1 discharged)

The package's raw-arm price was an estimate
(~1 h wall, flagged F-S3-1); both arms are now
measured. The games manifest records no phase
timestamps, so both walls below are taken from
filesystem evidence and stated as such: driver
stdout lines carry per-game seconds; block log
directories and driver files carry creation /
last-write times.

- **Teacher arm:** attempt-2 launch 2026-10-27
  08:09:25 EDT; the last teacher driver file
  closes 2026-10-27 22:14:17 EDT (t1b; the other
  teacher blocks close 21:12–21:36 EDT) — **≈
  14 h 05 min launch-to-last-teacher-row**, in
  line with the package's ~14 h price from Stage
  2's 503 s/game mean.
- **Raw arm:** the raw blocks' log directories are
  created 2026-10-27 ≈ 22:14 EDT (immediately after
  the teacher arm's last block) and the last raw
  driver file closes 22:20:47 EDT — **≈ 6.5 min
  for 400 games** (raw stdout lines show 2–5 s
  per game), far under the ≤ 1 h estimate. The
  raw arm is the whole reason the tracker total
  jumped 400 → 800 inside a single 10-minute
  poll gap: the entire arm fits in one interval.
- **Games total:** launch to the games manifest
  (22:20:49 EDT) ≈ **14 h 11 min**.
- **Attribution L3:** launched 2026-10-28
  06:55:32 EDT; `l3_manifest.json` written
  2026-10-28 08:52:02 EDT — **≈ 1 h 57 min**
  for 622 jobs × 100 worlds (62,200 label rows),
  inside the package's 2–3 h price.

## 4. The attribution (L3 on all teacher-arm overturns)

The attribution analyzer's output, exactly as
printed (`attr_read.txt`, sha256 `4016cfee…`):

```
=== STAGE 3 L3 ATTRIBUTION READ (primary: horizon 62, draw = 0) ===
PRIMARY (draw = 0): jobs 622; jobs_no_shared_worlds 0 (of 622 jobs); mean paired diff 0.0417; CI [0.0311, 0.0527]
  per-game gain 0.0649 (mean diff x LIVE overturns/game 1.5550 from 622 captured overturns over 400 completed teacher games)
ATTRIBUTION: per-game gain 0.0649 = L3 mean diff 0.0417 x live overturns/game 1.5550; per-game gain / fleet delta = unstable (Δ CI includes 0), fleet Δ 0.0475 CI [0.0000, 0.0950] (Fai gate references: 87% and 101%)
CO-REPORT coreport_draw05: mean diff 0.0390; CI [0.0294, 0.0491] over 622 jobs
CO-REPORT coreport_lifediff: mean diff 0.0381; CI [0.0282, 0.0484] over 622 jobs
UNFINISHED (refusals excluded from shares): pooled share 0.0001 (finished 62192, unfinished 8, refusals 0); fallbacks 14
  abort                       8  [unfinished]
CO-REPORT live rates vs the Stage 2 record: thin-prior 0.0000 (Stage 2 0.0000); overturn rate 0.0652 of contested (Stage 2 0.0694); overturns/game 1.5550 (Stage 2 1.7650)
CO-REPORT games outcomes (draw-scored): Stage 3 teacher 174W/82D/144L = 215.0000 pts over 400 games (0.5375/game)
ATTRIBUTION READ COMPLETE (co-report, not a gate: no PROCEED/STOP bands apply)
```

Reading: the L3 valuation of the calibrated
teacher's overturns is positive and excludes 0
(mean 0.0417, CI [0.0311, 0.0527]; full precision
in `attr_read.json`: 0.04171402…,
CI [0.03113472…, 0.05273119…]). At the LIVE
overturn rate — 622 captured overturns over 400
completed teacher games = **1.5550 overturns/game**
(games report: overturn rate 0.0652 of 9,538
contested rows; thin-prior 0.0000) — the per-game
gain is **+0.0649** (full precision
0.06486531…). The attribution ratio
**per-game gain ÷ Δ is printed as `unstable
(Δ CI includes 0)`** under the package's §4
guard: the JSON carries `ratio_to_delta: null`
and `ratio_note: "unstable (Δ CI includes 0)"`
with the fleet Δ and its CI beside it. The
guard exists for exactly this case — a positive
L3 valuation cannot be expressed as a share of a
fleet Δ whose interval includes 0, and no ratio
number is printed here. The Fai gate references
(87% for the gate, 101% for the O-measurement)
are printed by the analyzer as history, not as
this run's result.

The attribution tripwire is null (mean diff
0.0417 < +0.20, per-game gain 0.0649 < +0.25),
so no impeachment ordering applies and the read
stands as printed.

## 5. Integrity / audit

- **Games tuple audit:** 37,092 rows checked, 0
  bad, 0 malformed-pin aborts → OK; every row
  stamped with the H8k-180+H tuple
  (hooks 8000, deadline 180 s, horizon 62,
  horizon value −1, k 25, margin 1.5,
  `pinned: 1`).
- **Label tuple audit (fixed form):** 62,200
  rows, **0 bad** — every label row stamps
  exactly the six registered L3-W50+H fields
  (hooks 8000, deadline 180 s, horizon 62,
  horizon value −1, k 50), no `pinned` key.
  Label seed family 50055001 + shard × 10⁸ as
  registered.
- **Label rows:** 622 jobs × 100 rows/job
  (LABEL_W = 50 worlds × {teacher, prior}
  candidates) = **62,200 rows**, verified three
  ways: the shard files sum to 62,200 (8300 /
  6000 / 8300 / 6900 / 9100 / 8500 / 9100 / 6000
  across shard0_p1 … shard3_p2), `labels_all.jsonl`
  is 62,200 lines, and the analyzer's audit
  counts 62,200 rows; the decompressed stream
  hashes to `66e16f51…` on the box and on the
  transferred copy.
- **Unfinished / refusals (labels):** pooled
  unfinished share **0.0001** (finished 62,192;
  unfinished 8 — all class `abort`, teacher 3 /
  prior 5; refusals 0); fallbacks **14**.
- **Coverage:** `jobs_no_shared_worlds` **0 of
  622** — every job's two candidates share their
  worlds; no job rests on an unpaired comparison.
- **Games fallbacks:** `child_fallbacks` 0 in
  the games report.
- **Registry:** post-merge **7,331 games**
  (6,531 + 800), sha256
  `24156438ec0383aa56a2e0fd1748f1c91e93aa28762b903232347286adf973ed`.
- **ABORTs:** none in `games_launch2.log` or
  `l3_launch.log`. The single ABORT in
  `games_launch.log` is attempt 1's free-space
  pre-flight refusal, documented in §1 — the
  run's only abort, and it happened before any
  game or label existed.

## 6. Data

All run artifacts are published under
`rounds/round9/data/stage3/` with `MANIFEST.md`
(sha256 + row counts + one-line role per file;
the labels' raw identity listed there). The box
originals remain in `/home/joe/tcg/r9s3_out/`
(games + l3 + launch logs) and the registry in
`/home/joe/tcg/registry-vault/`.

Every figure in this report recomputes from the
repo alone: the primary, co-reports, per-seat
and per-block deltas, timeout and pairs-out
rates, and the verdict from `stage3_read.json` /
`.txt` + `pairing.json` + the driver rows; the
band rates and tuple audit from
`games_report.json` / `.txt` + the stat logs;
the attribution, live rates, and ratio guard
from `attr_read.json` / `.txt` +
`jobs_all.jsonl` + the label rows (gz, raw
identity in the manifest); the phase times from
the launch logs and the driver-file timestamps
noted in §3.
