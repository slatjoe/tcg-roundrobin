# Round 10, Step 0 — the offline probe package

**Stage:** round10-step0-probe · **Status:** PACKAGE FOR
REVIEW. This package approves no build and no run
(claude-reply-9b04ad1 close). It contains (A) the
standing-item reproduction of the direction review's
§1–§3 tables from the published round-9 rows, with
committed code, and (B) the Step 0 probe the review's
§3 specifies, designed against the round-9 machinery
as it actually exists in the repo, with its size,
cost, report shape, and decision rule registered
below for the review to amend or register as written.
**Amended in place by the FIX PASS of 2026-10-28
(§9) on claude-reply-402c92f (CHANGES REQUESTED):
§3.3 and §5 below were rewritten where the ruling
changed the text; §8 F2 is marked ruled.**

**Scope, as ruled.** Round 10 prices two levers and
only two: the fire margin (1.5 → 1.25) and the 0.97
uncontested threshold. Candidate-set widening is
dropped (review §1: it changes the candidate set in
2% of contested states). **C2 (horizon life-pricing)
is OUT of round 10: Joe ruled 2026-10-28 — λ = 0
accepted, per the review's recommendation (§4: under
the draw = 0 read a capped game is worth a loss
regardless of life, so any α > 0 trades win
probability for worthless life-leads; the coherent
alternative, v = (1−λ)(−1) + λ·L with the read using
the same λ, would be a separate future registration
if it is ever wanted, not part of this round).** The
probe itself is unchanged by the ruling: it prices
the margin and threshold levers only.

Instruments as everywhere in this project: max-turns
87 / draw trigger 62, stated together. Mirror: Gravy
Bones, both seats, deck
`nats2026_eriksen_gravy_60.txt` (b8b41390…), policy
raw v10 (ckpt_v10.pt, 44f1e5d7…) served by the
production build (81ef2cdb…), Talishar snapshot
3da4648.

---

## 1. Deliverable A — reproduction of the review's §1–§3

Code: `code/reproduce_r9_tables.py` (this round's
code dir). It reads ONLY the published rows under
`rounds/round9/data/stage2/` and `.../stage3/`
(driver rows, `search_stats_*`, `snap_index_*`,
`jobs_shard*`, `labels_shard*`) and imports two
round-9 helpers by pinned hash: `classify` from
`stage0_report.py` (5c7e5393…) and
`cluster_bootstrap` from `analyze_l3.py` (16017ffa…,
B = 10,000, seed 20261020). Constructions, each
stated before the numbers:

- **z** per contested statistic: `mean_diff /
  se_diff` from the same stat row; `se_diff = 0` with
  `mean_diff > 0` gives z = +∞ (such rows exist —
  constant paired diffs; the live rule
  `mean_diff > margin · se_diff` fires at any margin).
- **Fires at margin m:** contested stat rows with
  z > m, over teacher games (200 / 400). Sanity:
  fires@1.5 equals the logged overturn count exactly
  in both stages (353 / 622) — the logged rule and
  the recomputed z agree on every row.
- **Per-job L3 diff:** `stage3_attr_analyze.run_read`'s
  primary construction (score 1.0 iff outcome > 0,
  shared finished non-refusal worlds only). Overall
  edges recompute to the published +0.0621 (S2) /
  +0.0417 (S3) before any banding.
- **Job ↔ statistic pairing:** two pairings computed
  (this turns out to matter — see §1.2):
  (i) the **snap join** — the job's `snap` into
  `snap_index` (the index row Decide wrote in the
  same block that copied the snapshot the job
  labels); (ii) the **first-match stat join** — the
  job's key (game, player, branch, turn, prior_pick,
  pick) to the first stat row in stream order
  carrying it. An order-aware stat join (n-th job at
  a key ↔ n-th stat row at that key) agrees with the
  snap join on **353/353 (S2) and 622/622 (S3) jobs**.
- **Prior bands:** top prior from the stat row's
  `priors` array (every contested row in both
  published streams carries one, thin and
  no-contrast rows included — that is the §3
  denominator).

### 1.1 Results

| figure | Claude | mine | verdict |
|---|---|---|---|
| S2 fires/game @1.5 / 1.25 / 1.0 | 1.765 / 3.200 / 3.590 | 1.765 / 3.200 / 3.590 | MATCH (exact, all three) |
| S3 fires/game @1.5 / 1.25 / 1.0 | 1.555 / 2.720 / 3.080 | 1.555 / 2.720 / 3.080 | MATCH (exact, all three) |
| S2 band n (1.5,2] / (2,2.5] / (2.5,3.5] / >3.5 | 187 / 94 / 50 / 22 | 187 / 94 / 50 / 22 (first-match); 188 / 94 / 49 / 22 (snap) | MATCH under first-match pairing |
| S3 band n | 328 / 191 / 84 / 19 | 328 / 191 / 84 / 19 (first-match); 326 / 192 / 85 / 19 (snap) | MATCH under first-match pairing |
| S2 band edges | +0.020 / +0.029 / +0.060 / +0.566 | identical to 3 dp under first-match | MATCH |
| S3 band edges | +0.016 / +0.032 / +0.075 / +0.430 | identical to 3 dp under first-match | MATCH |
| Band CIs (8) | as printed in the review | 7 of 8 within ±0.0025 under first-match (narrow bands: normal approx; wide bands: cluster bootstrap) | MATCH except S3 >3.5 — see §1.3 |
| S2 non-tail edge / tail share / tail rate | +0.0286 / 57% / 0.110 | +0.0287 / 0.567 / 0.1100 | MATCH |
| S3 non-tail edge / tail share / tail rate | +0.0295 / 32% / 0.048 | +0.0295 / 0.314 / 0.0475 | MATCH |
| S3 uncontested per game | 68.9 | 68.89 (27,554 rows / 400) | MATCH |
| Uncontested with ncand ≤ 1 | "none" | 0 rows in both stages | MATCH |
| Tail rate [0.85,0.97), S3 / S2 | 0.0038 / 0.0060 | 0.0038 (7/1851) / 0.0060 (6/999) | MATCH |
| Tail rate [0.5,0.7), S3 | 0.0018 | 0.0018 (7/3957) | MATCH |

Full per-figure output (every band under both
pairings, both CI methods, the mis-paired jobs by
snap, the remaining prior bands) is staged at
`fixtures/fx_repro_output.txt` and regenerates from
the script; the fixture suite re-runs the script and
compares its summary line.

The full prior-band table (mine, all contested rows
as denominators) — S3: [0, 0.5) 0.0005 (1/2099),
[0.5, 0.7) 0.0018, [0.7, 0.85) 0.0025 (4/1631),
[0.85, 0.97) 0.0038; S2: 0.0055 (6/1095), 0.0033,
0.0034, 0.0060. The review's ordering claim — the
tail rate does not thin with confidence; the
[0.85, 0.97) band is the highest — holds in both
stages on these denominators.

### 1.2 The pairing finding (flag F3)

Five jobs sit at repeated decision keys — two
overturns in the same game, branch, and turn (snap
pairs like `272983764_t1/_t2`). A plain key join
pairs each such job with the FIRST stat row at its
key; the review's band counts and edges reproduce
**exactly** under that pairing, so it is the
pairing the review's table was computed with. The
snapshot pairing (confirmed independently by the
order-aware stat join, 975/975 jobs) is the pairing
of record: the snap index row and the snapshot were
written by the same Decide block that produced the
statistic. Under the snap pairing the band table
differs only where a mis-paired job crosses a band
edge. The corrected cells:

| band | stage | Claude (first-match) | snap pairing |
|---|---|---|---|
| (2.5, 3.5] edge | S2 | +0.060 (n 50) | **+0.062 (n 49)** |
| (2.5, 3.5] edge | S3 | +0.075 (n 84) | **+0.072 (n 85)** |
| (1.5, 2.0] n | S2 / S3 | 187 / 328 | 188 / 326 |
| (2.0, 2.5] edge | S3 | +0.032 | +0.033 (n 192) |

Mis-paired jobs (snap z vs first-match z), from the
script output: S2 `272983764_t2` (3.674 vs 5.099),
`748346653_t2` (1.549 vs 3.361); S3 `505941231_t2`
(2.009 vs 1.693), `460903542_t3` (2.450 vs 2.138),
`739674724_t2` (2.753 vs 2.000). No conclusion in
the review moves: the non-tail edges, tail shares,
and tail rates are pairing-invariant (the tail set
is identical under both pairings in both stages),
and the (1.25, 1.5] band price is computed from
stat rows, not jobs. The probe's own analyzers pair
by snap throughout (as the round-9 label analyzers
already do).

### 1.3 The one figure not reproduced (flag F4)

**Stage 3, band >3.5, CI.** Review: [0.303, 0.553].
Mine, on the identical 19 jobs under either pairing:
cluster bootstrap (round-9 helper, seed 20261020)
[0.306, 0.555]; normal approximation [0.299, 0.560].
The point estimate reproduces (+0.429 vs +0.430);
the interval misses by 0.003 / 0.002 — consistent
with bootstrap Monte Carlo under a different seed
(the review does not record one), not with a
different job set or construction. Flagged, not
forced: every other CI in the table reproduces
within ±0.0025 under the first-match pairing.

---

## 2. Machinery findings — what exists, what is missing

Read from the staged round-9 code (pins in §7).

**Contested capture exists and is the probe's
chassis.** `search_s2.php`'s DecideInner, under
`TEACHER_CAPTURE`, snapshots EVERY contested
decision (game-dir copy to
`$TEACHER_SNAP_DIR/<game>_t<hcount>/` + an index row
carrying `cands`, the featurizer `state`, `priors`,
`prior_pick`, `selected`), plays the prior pick, and
never rolls out. Stage 1 ran exactly this arm; the
capture games are raw-policy games whose snapshots
Stage 1's panel and Stage 2's overturn jobs were
built from.

**The live path leaves a complete statistic.** Every
contested decision's stat row carries the candidate
means, `priors`, the pick, `overturn`, and
`mean_diff` / `se_diff` (null when there is no
contrast or fewer than 20 paired worlds) — which is
why Deliverable A could be computed from stat rows
alone.

**Uncontested decisions leave NO evaluable record.**
At the uncontested branch (`ncand ≤ 1` or top prior
≥ 0.97), DecideInner writes a stat row with the
setting, branch, player, turn, `ncand`, `prior_pick`,
`pick`, and ms — **no snapshot, no state, no priors
array**. There is nothing in any published stream an
offline eval could run on for these decisions. This
is the one machinery gap the probe has, and §3's
capture hook is the smallest change that closes it:
the priors and candidate records are in scope at
that point in the function, and the snapshot/index
primitives the contested arm uses
(`SimSearch_CopyDir`, `SimFeat_BuildState`) sit in
the same function, twenty lines below.

**The offline eval already exists.** `s1_eval_main.php`
(73ed2482…, reused byte-identical) re-enters a
snapshot at its root decision, runs the full search
machinery (determinize–fork–rollout) over the job's
`selected` candidates at W = k worlds per candidate,
and emits priced-outcome world rows; it aborts any
job whose `setting` stamp mismatches the run pins,
field by field. Stage 1 measured it at the exact
tuple the probe needs.

**The label machinery already exists.**
`s2_label_main.php` (1c1dfd9f… — the round-9
driver, reused; its jobs loader changed in §12)
labels a snapshot's two candidates at W = 50 with
CRN; Stage 3's attribution read is the construction
the probe's label analyzer mirrors.

---

## 3. The probe as designed

All parameters live in `code/settings_probe.json`
(single source; the runner's literals are
fixture-checked against it).

### 3.1 Capture — 90 fresh games

- **Seed block 24001–24090** (seat 1: 24001–24045,
  seat 2: 24046–24090), extensions in 10-game blocks
  from 24091. Checked disjoint from every used
  block: 1001–1200, 2001–2200, 8001–8200,
  10001–10400, 21001–21040 plus the Stage 1
  extension range to 21100, 22001–22100,
  23001–23200; the reserved 9001–9200 stays
  untouched (fixture-enumerated, §6).
- **Build:** `search_s3.php` = `search_s2.php`
  (85490e8e…) + ONE inserted block (the hook below),
  generated by `fixtures/gen_search_s3.py`; the diff
  is staged at `fixtures/search_s3_diff.txt` (77
  lines, insertion only) and the fixture suite
  asserts byte-identical regeneration.
- **The hook** (in the uncontested branch, before
  the stat-row write; inert unless `TEACHER_CAPTURE`
  AND `TEACHER_CAPTURE_UNCONTESTED` are set — the
  runner sets them only in the capture phase): for
  decisions with `ncand ≥ 2` and top prior ≥ 0.97,
  snapshot the game dir and append an index row in
  the contested arm's exact shape (same snap
  counter, same index file), plus `uncontested: 1`,
  `top_prior`, and `selected` = the candidate set
  the search would use (top-3 by prior, then any
  prior ≥ 0.10 up to 4 — with top ≥ 0.97 the tail
  sums to ≤ 0.03, so the second loop provably adds
  nothing; the code runs the rule, not the shortcut).
- **Sampling rule:** per game, systematic — every
  2nd eligible uncontested decision
  (`TEACHER_CAPTURE_UNCONTESTED_EVERY=2`, settings).
  Expected yield: 68.9 decisions/game × 90 games /
  2 ≈ **3,100 uncontested states**. At the review's
  speculated tail rate of 0.001–0.002/state that is
  3–6 expected tail fires — enough to price the
  lever within roughly a factor of two, which is
  what a Step 1 choice needs; §5 registers the
  extension rule if the realized would-fire count
  is too small to label a class.
- Contested states are captured by the stock arm,
  unsampled: ≈ 23.8/game × 90 ≈ **2,140 states**.
- Capture game ids merge into the do-not-train
  registry under tag `r10_probe_capture` (the
  runner does this in the capture phase, Stage 1
  form). Raw v10 plays; the teacher applies no
  picks (capture mode: snapshot and play the prior
  pick, exactly Stage 1).

### 3.2 Offline eval — every snapshot, k = 25, no screen

Each captured snapshot (both classes) becomes an
eval job (`build_probe_eval_jobs.py` — all rows, no
panel cap: the estimands are rates, and a cap would
censor the denominators). The byte-identical
`s1_eval_main.php` runs at the probe eval tuple
{hooks 8000, deadline 180 s, horizon 62,
horizon_value −1, **k = 25**} — the calibrated
search, nothing else. `probe_eval_analyze.py`
recomputes Decide's own statistic from the world
rows (winner-0 worlds priced −1, per-candidate
finished worlds, prior-pick ≥ 20-world floor,
paired diffs over shared worlds, ≥ 20 required,
z = mean_diff/se_diff with the se = 0 → +∞ rule)
and records per state: class, prior band, top
prior, search pick vs prior pick, mean_diff,
se_diff, z, would-fire at 1.5 / 1.25 / 1.0,
finished/unfinished/refusal diagnostics per
candidate, and the eval wall. **One eval serves all
three margins because z is margin-independent** —
the margin question is read off the z's, not
re-run.

**No k = 10 screen.** The review contemplates one
(§3: "a screen the builder may use"). The probe
does not, and the reason is the estimand: for
uncontested states the tail rate IS the number the
probe exists to measure. A k = 10 screen with a
z₁₀ floor at 1.0 keeps a true z₂₅ = 3.5 state with
probability ≈ Φ((3.5·√(10/25) − 1.0)/√(1 − 10/25))
= Φ(1.57) ≈ 94%, at z₂₅ = 4 ≈ 97% — a 3–6% downward
bias concentrated exactly at the tail boundary,
correctable only by modeling the joint (z₁₀, z₂₅)
distribution the probe is trying not to assume.
The saving is real (≈ 60% of eval cost) and the
bias is small, but it sits on the headline number;
the package prices the unscreened probe (§4) and
registers the screened variant as the fallback if
the review prefers the cheaper, slightly biased
read: screen at z₁₀ ≥ 1.0, full k = 25 re-eval
above it, and report the tail rate as a lower bound
with the Φ-correction printed beside it.

### 3.3 Labeling — three classes (F2 ruled; amended in place by the fix pass)

L3 at the registered configuration (W = 50, CRN,
pair `va`, horizon 62, draw = 0 read) via
`s2_label_main.php` (the round-9 driver; §12
changes its jobs loader), on:

- **(a) uncontested would-fires** — states whose
  eval statistic fires the CURRENT rule (z > 1.5),
  i.e. what a threshold build gains under today's
  decision rule;
- **(a-diag) the uncontested SUPERSET below the
  class-(a) margin** — states with z in (1.0, 1.5]
  (fix pass, review §3/F2). Labeled and reported
  (counts, edge) as a DIAGNOSTIC class only:
  excluded from the threshold per-game gain and
  from the decision rule (the label analyzer emits
  no gain for it, so nothing downstream can fold
  it in); and
- **(b) contested would-fires in (1.25, 1.5]** —
  the fires margin 1.25 adds.

**F2 — RULED (claude-reply-402c92f §3): class (a)'s
margin is 1.5**, as this package proposed — a
threshold build changes one thing, the threshold,
at the current margin, so its gain is the z > 1.5
class; the z > 1.0 superset is labeled alongside it
as the diagnostic above. Expected job counts under
each definition, from the Stage 3 z-distribution
ratios applied to the probe's expected uncontested
would-fire counts (the probe measures the base
rate; the ratios are the contested population's:
fires@1.25/fires@1.5 = 1.75, fires@1.0/fires@1.5 =
1.98):

| class (a) defined at | expected jobs (if @1.5 rate is 0.002/state) | if 0.005/state |
|---|---|---|
| z > 1.5 (ruled) | ≈ 6 | ≈ 16 |
| z > 1.25 | ≈ 11 | ≈ 27 |
| z > 1.0 (the labeled superset) | ≈ 12 | ≈ 31 |

Class (b) is definition-independent: ≈ 1.165
fires/game (Stage 3) × 90 ≈ **105 jobs**; the
planned label total with the superset is ≤ 160
jobs (settings `label.planned_jobs_total_max`).
The jobs builder takes the margins from settings
(`label.uncontested_margin`,
`label.uncontested_diag_margin`), prints the
realized counts under all three definitions in its
report, and proceeds — with F2 ruled and the
superset in the job set, the jobs phase needs no
ruling before labels.

**Label seeds: base 70,055,001 + shard × 10⁸**,
4 shards, per-shard cap **256 jobs** enforced by an
abort in `build_probe_jobs.py` (span at the cap:
27,036,278; family top 97,091,279 < 10⁸; base
clears the Stage 3 family's span top 69,091,039).
Fix pass: the planned counts are enlarged for the
superset (planned total ≤ 160, planned per-shard
≤ 256 == the cap itself, settings), so the
enumeration in `fx_seed_clearance.py` — which runs
at the cap — is the re-proof at the enlarged
counts: no planned population can exceed the
enumerated one in any shard (§9).
**Eval seeds: base 30,055,001 + shard × 10⁸**
(value-disjoint from every prior family on the
shared lattice). Both proven by enumeration at the
planned counts in `fixtures/fx_seed_clearance.py`
(§6), including the round-8 families at their
recorded 547 jobs, W ≤ 100, over-approximated
across all shard-offset variants. **Flag F5:** the
round-8 families were never range-checked against
the Stage 3 family when Stage 3 was registered
(their span tops at recorded counts, ≈ 58.5M, in
fact clear the Stage 3 base 50,055,001's span
bottom only if shard offsets don't collide — the
enumeration in this package's fixture checks
VALUES, and finds no collision; the historical
registration gap is noted for the record, not
repaired here).

---

## 4. Size and cost (the probe's own price)

| piece | basis | box time | wall |
|---|---|---|---|
| Capture, 90 games | policy-speed games + snapshots (Stage 1 capture form; no rollouts run in capture mode) | ≈ 1–2 h incl. snapshot copying | ≈ 1–2 h (2 seat streams sequential per stream) |
| Offline eval, ≈ 5,240 states | Stage 1 measured H8k-180+H wall 26.5 s/state at fleet contention; the probe's own stats file re-measures it | ≈ 38.6 box-h | ≈ 9.6 h at 4 shard processes |
| Labeling, ≈ 110–140 jobs | Stage 3 L3 measured: 622 jobs, 62,200 rows, ≈ 1 h 57 m at 8 processes ≈ 90 process-s/job | ≈ 3.0 box-h | ≈ 25 min at 8 processes (4 shards × 2) |
| **Total** | | **≈ 43 box-h** | **≈ 11–12 h** |

Extension arithmetic (if the review wants more
uncontested states): each +10 capture games adds
≈ 344 uncontested (sampled) + ≈ 238 contested
states ≈ +4.3 eval box-h (≈ +1.1 h wall) and
≈ +12 band jobs. Doubling the uncontested sample
(EVERY=1 on the same 90 games) adds ≈ 3,100 states
≈ +22.8 eval box-h — the expensive direction is
states, not games.

For scale against the levers being priced: the
margin lever's predicted gain (review §1 arithmetic,
Stage 3 z's) is ≈ +0.012/game at zero added search
cost; the threshold lever's speculation is
+0.03–0.06/game at ≈ +1,343 s per teacher game
(68.9 searches × 19.5 s — the probe's report
recomputes this from its own measured populations:
smoke-tested at 68.89 decisions/game → 1,846 s/game,
3.67× the current 503 s, matching the review's
≈ 3.6×). The probe costs about what 300 fleet
teacher games cost, to decide whether a 950-pair
fleet (≈ 130+ box-h of teacher games) should be
built at all, and with which single change.

---

## 5. Report shape and decision rule (registered)

`probe_report.py` emits, from the three analyzer
outputs (items 1 and 3 amended in place by the fix
pass — the calibration block is new, the threshold
gain is now sampling-weighted, and the
informational Step 2 prints are new):

0. **Calibration (fix pass, review §2.2):** the
   probe's contested would-fire rate at margin 1.5,
   per contested state and per game, printed beside
   Stage 1's panel (22/240 = 0.092 per state) and
   the live rates (0.069 Stage 2, 0.065 Stage 3 per
   state). If the per-state rate falls outside
   [0.04, 0.13], the report prints "offline eval
   does not reproduce the search's firing behavior"
   above the recommendation. A print and a flag,
   not a gate — the decision rule below is
   unchanged.
1. **Tail rate per state and labeled edge, by prior
   band** — bands [0, 0.5), [0.5, 0.7), [0.7, 0.85),
   [0.85, 0.97), **[0.97, 1]** (the uncontested
   population), from the eval z's (rates) and the
   labels (edges). The (1.0, 1.5] uncontested
   DIAGNOSTIC class is reported here too — counts
   and edge, never a gain.
2. **The (1.25, 1.5] band:** fires/game (eval),
   labeled edge and per-game gain (labels).
3. **Per lever:** predicted per-game gain =
   the label read's game-clustered per-game gain
   (summed diffs per capture game over ALL 90
   capture games, zero-fire games included — the
   review §5 Step 2 form, applied at probe scale),
   with CI and lower bound; **the uncontested
   class's diffs are weighted by
   `capture.uncontested_every` (Horvitz–Thompson)
   inside the per-game sum** (fix pass, review
   §2.1 — the unweighted form undercounted the
   threshold gain by the sampling factor);
   predicted teacher-game cost: margin — 503 s (no
   added searches; fires rise to the probe-measured
   1.25 rate); threshold — 503 + (uncontested
   decisions/game × 19.5 s), with the probe's own
   offline seconds/state printed as a cross-check.
   **Informational, per lever (fix pass, review
   §3; power formula corrected in the second fix
   pass, §10):** the predicted Step 2 power
   against the registered two-sample bar — PASS
   iff (gain_new − 0.0649)/√(SE_new² + 0.0090²)
   ≥ 1.645. The lever's predicted gain is an
   INCREMENT (the added fires only), so the power
   is Φ(z − 1.645) with z = inc/√(SE_new² +
   0.0090²) and SE_new = √(0.0090² +
   se_inc,400²): Stage 3's base SE plus the
   increment's SE (read off its CI) scaled from
   the probe's 90 games to 400 by the √n rule,
   under the stated approximation that the
   build's base gain is Stage 3's. And the
   Step 2 + fleet teacher-arm prices at the
   lever's per-game cost. Printed so a
   "buildable" lever's confirmation price is
   visible before any go.
4. **Recommendation** under the registered rule
   (settings `report.decision_rule`): a lever is
   BUILDABLE iff its predicted gain's one-sided 95%
   lower bound — taken as the game-clustered
   two-sided CI's lower bound, the conservative
   stand-in, and labeled as such in the analyzer —
   exceeds 0. Exactly one buildable → recommend it.
   Both → the higher lower bound, unless the bounds
   lie within each other's CIs, in which case the
   cheaper lever (margin). **Neither → recommend NO
   Step 1 build.** The probe is allowed to say no.

**Extension rule (registered here):** if class (a)
realizes fewer than 5 jobs, the uncontested edge
read is reported as uninformative (counts and z's
only) and the threshold recommendation falls back
to the tail-rate arithmetic alone, stated as such —
or the review orders an extension block (10 games,
§4 arithmetic) before labels run. The jobs phase
prints the realized class counts before any label
box time is spent, so this decision is cheap.

---

## 6. Fixtures

`fixtures/run_fx_r10.sh` — **ALL PASS (126 checks;
45 at the original package, +12 in the fix pass
(§9), +29 in the second fix pass (§10), +13 in
the third fix pass (§11), +10 in the fourth fix
pass (§12), +17 in the fifth fix pass (§13))**,
transcript staged at
`fixtures/fx_r10_outputs.txt`:

- `fx_pin_guards.py` — every hash literal in
  `run_probe.sh` is 64-hex AND equals the staged
  file's sha256 (machine-checked); seed literals
  equal settings; capture seed strings equal
  settings. Second fix pass (§10): the deploy
  list is parsed from the runner's
  deployed-hashes recording loop and every
  deployed file is asserted to carry an
  expect_hash site equal to its staged sha256; a
  negative case runs the guard against a
  temporary pin-stripped copy of the runner and
  asserts it fails on the coverage check.
- `gen_search_s3.py --check` — search_s3.php
  regenerates byte-identically from the pinned
  search_s2.php; the diff is the single hook block.
- `fx_probe_blocks.sh` — verbatim extraction and
  stub execution of the runner's FREESPACE (pass +
  abort cases), SRV, CAPTURE, EVAL, and LABEL blocks,
  including the FAIL-flag abort paths when a shard
  process fails.
- `fx_probe_python.py` — writer/reader round trips
  fed the writers' real output shapes: capture
  index → eval jobs (incl. both poison-row aborts);
  synthetic s1-eval rows → per-state statistics
  (z = +∞ on constant diffs; an independently
  computed z = √2 in the (1.25, 1.5] band; the
  thin-prior floor; tie → no contrast; **drawn
  worlds priced −1** — this case caught a real
  winner-field bug in the analyzer's first draft,
  fixed and now covered); states → label jobs
  (class assignment at both candidate margins, the
  shard-cap abort); label rows → the label read
  (per-world scoring, refusal worlds skipped, the
  exactly-50 world-count guard, per-game gain over
  a population including a zero-job game). Fix
  pass additions (§9): the sampling-weight round
  trip in the hook's real index shape (gain and CI
  scale by exactly the sampling factor; the
  contested band unchanged); the uncontested class
  boundaries (z = 1.0 / (1.0, 1.5] / z > 1.5); and
  the report prints (calibration in/out of band,
  the Step 2 power print against two by-hand
  cases — inc = 0 → Φ(−1.645) ≈ 0.05; inc = 0.03
  at se_inc,400 = 0.005 → SE_new 0.0103, z 2.194,
  power 0.708 (second fix pass, §10) — and both
  levers' price lines).
- `fx_seed_clearance.py` — the §3.3 enumeration.
- `fx_runner_env.py` — the capture environment
  contract (third fix pass, §11): BLOCK:CAPTURE is
  extracted verbatim from the runner and EXECUTED
  in the stub harness with an environment-recording
  stub driver; the composed runner → driver → game
  environment is asserted to carry both variables
  the search_s3.php uncontested hook gates on
  (the hook's gate line and the driver's arm lines
  are lifted verbatim from their own files); a
  negative case runs the same checks against a
  temporary runner copy with the
  TEACHER_CAPTURE_UNCONTESTED assignment removed
  and asserts the guard fails on exactly the two
  uncontested checks.
- `fx_label_loader.py` — the non-finite-z chain
  (fourth fix pass, §12): an inf-z state
  (mean_diff 2.0, se_diff 0.0) through the real
  job writer — strict JSON on every line of
  jobs_all and the shard files, the sentinel
  z = 999.0 + `z_nonfinite` on that job only, the
  report's count; the PHP loader's load block,
  lifted verbatim from `s2_label_main.php` and
  run under php8.3, loading the writer's file
  whole; the analyzer banding the sentinel job in
  class (a)'s z > 3.5 tail; and the negative
  case — attempt 3's real line 282 (the bare-
  Infinity t64 job, read from `data/step0/
  jobs_all.jsonl` at runtime) makes the loader
  abort at exit 2, naming the line.
- `fx_repro` — the Deliverable A script re-run; its
  summary line compared against the staged output.

`probe_report.py` is smoke-tested on synthetic
analyzer outputs (its real inputs are the
fixture-verified analyzers' JSON): populations,
cost arithmetic (68.89 × 19.5 s → 1,846 s, 3.67×),
and all four recommendation branches' inputs
exercised; the both-buildable tie branch produced
the registered tie-break line.

---

## 7. Files staged, reuse vs new

Under `rounds/round10/` (hashes are sha256, first 8):

**New code** (`code/`): `search_s3.php` (8f7be190,
generated — see below), `settings_probe.json`,
`build_probe_eval_jobs.py`, `probe_eval_analyze.py`,
`build_probe_jobs.py`, `probe_label_analyze.py`,
`probe_report.py`, `run_probe.sh`,
`run_probe_recovery.sh` (§12),
`reproduce_r9_tables.py`.

**Byte-identical reuse from round 9** (`code/`,
hash-verified copies of the round-9 files):
`s1_eval_main.php` (73ed2482), `s2_label_main.php`
(1c1dfd9f — the round-9 driver; its jobs loader
changed in §12, so this one is no longer
byte-identical), `paired_driver_gravy.py` (3389b1b9),
`merge_registry.py` (13a655e3), `search_s2.php`
(85490e8e — the label trees' build and the hook's
base), `stage0_report.py` (5c7e5393), `analyze_l3.py`
(16017ffa), `g8_sweep2.sh` (d49981ca), `shm_sweep.py`
(98027a8b).

**Derived:** `search_s3.php` from `search_s2.php`
by the single fixture-checked insertion
(`fixtures/gen_search_s3.py`,
`fixtures/search_s3_diff.txt`);
`build_probe_eval_jobs.py` forked from
`build_panel.py` (8f22d845) with the panel cap
removed and the uncontested class added;
`build_probe_jobs.py` / `probe_label_analyze.py`
forked in construction from `build_s3_jobs.py`
(fabecae5) / `stage3_attr_analyze.py` (788cd28a).

**Fixtures** (`fixtures/`): `run_fx_r10.sh`,
`fx_pin_guards.py`, `fx_probe_blocks.sh`,
`fx_probe_python.py`, `fx_seed_clearance.py`,
`fx_runner_env.py`, `fx_label_loader.py`,
`gen_search_s3.py`, `search_s3_diff.txt`,
`fx_repro_output.txt`, `fx_r10_outputs.txt`.

---

## 8. Flags for the review

- **F1 — RESOLVED (recorded, not asked):** λ = 0;
  C2 is out of round 10 (Joe, 2026-10-28, §scope
  above). No C2 build, no life-priced read, in this
  round.
- **F2 — RULED (claude-reply-402c92f §3):** the
  uncontested label class is defined at **1.5**, as
  proposed; the z > 1.0 superset is labeled as the
  (1.0, 1.5] diagnostic class (§3.3 as amended).
  The jobs builder prints realized counts under
  all three margins and proceeds without a ruling.
- **F3 — pairing (§1.2):** the review's §1 band
  table is computed under a first-match key join;
  under the snapshot pairing of record, two band
  edges read +0.062 / +0.072 instead of +0.060 /
  +0.075. No conclusion moves. Future tables should
  pair by snap (the round-9 label analyzers already
  do).
- **F4 — not reproduced (§1.3):** the Stage 3 >3.5
  band CI, off by 0.003/0.002, consistent with an
  unrecorded bootstrap seed.
- **F5 — seed history (§3.3):** the round-8 label
  families were never range-checked against the
  Stage 3 family at registration; this package's
  enumeration finds no value collision at recorded
  counts, and the probe's families are proven clear
  of all of them. Noted for the record.
- **F6 — probe size, for registration or
  replacement:** 90 capture games, uncontested
  sampling EVERY = 2 (≈ 3,100 states), NO k = 10
  screen (§3.2 gives the bias arithmetic and the
  screened fallback), label base 70,055,001 with
  the 256-job shard cap, eval base 30,055,001.
- **F7 — machinery, stated plainly:** the probe's
  only machinery gap was real — uncontested
  decisions left no evaluable record at all in the
  stock build. The hook in `search_s3.php` is the
  smallest change that closes it (one inserted
  block, inert outside the capture phase, diff
  staged). Everything else the review's §3 requires
  already existed and is reused byte-identical.
  One honest limitation: the hook snapshots the
  state the same way the contested arm does, so an
  uncontested snapshot costs the same disk per state
  as a contested one (≈ 90 games × (23.8 + 34.4)
  snapshot dirs in the capture streams) — the
  free-space pre-flight covers the trees; the
  capture streams' own disk is the box's data disk,
  and Stage 1's precedent (2,248 snapshots) is
  smaller than the probe's ≈ 5,240. Noted, not
  blocking.

---

*End of package. Nothing here launches anything:
the runner exists so the review can read the exact
blocks that would run, and the launch, if the
review registers the package and Joe directs it,
follows the standing pattern (fresh deployment by
hash into a new box code dir, deployed.sh manifest,
phase order capture → eval → jobs → label →
analyze, with the jobs-phase counts read before
label box time is spent).*

---

## 9. FIX PASS — 2026-10-28 (on claude-reply-402c92f, CHANGES REQUESTED)

The review's verdict: one blocking defect (§2.1),
one required print (§2.2), and the §3 additions
(the z > 1.0 superset labels; the per-lever
informational prints). This section is the dated
record; **§3.3, §5, §6 and §8 above were amended
IN PLACE** (rewritten where the ruling changed the
text), not merely annotated here.

- **§2.1 — SAMPLING WEIGHTS (blocking).**
  `probe_label_analyze.py`: each uncontested job's
  diff is weighted by `capture.uncontested_every`
  (Horvitz–Thompson) inside the per-game sum in
  `per_game_gain()`, so the bootstrap runs over the
  weighted per-game totals; contested-band jobs
  keep weight 1. The weight is printed on the CLASS
  line and recorded in the JSON gain object. (The
  report already scaled the cost side by the same
  factor; the gain side now matches.)
- **§2.2 — CALIBRATION PRINT (required).**
  `probe_report.py` prints, before the
  recommendation, the probe's contested would-fire
  rate at margin 1.5 per contested state and per
  game, beside Stage 1's panel (22/240 = 0.092 per
  state) and the live rates (0.069 Stage 2, 0.065
  Stage 3 per state); a per-state rate outside
  [0.04, 0.13] prints "offline eval does not
  reproduce the search's firing behavior" above the
  recommendation. Print + flag, not a gate; the
  recommendation logic is unchanged.
- **§3/F2 — SUPERSET LABELS.** `build_probe_jobs.py`
  emits a third class, `uncontested_diag` —
  uncontested states with z in (1.0, 1.5]
  (`label.uncontested_diag_margin`) — alongside
  class (a) at the ruled margin 1.5. The label
  analyzer reads it for counts and edge only and
  emits NO per-game gain for it; the report prints
  it as a diagnostic line. It is excluded from the
  threshold gain and from the decision rule. The
  jobs phase prints realized counts under margins
  1.5 / 1.25 / 1.0 and proceeds without a ruling.
  Seed clearance + the 256-job shard cap re-proven
  at the ENLARGED planned counts
  (`label.planned_jobs_total_max` 160,
  `planned_jobs_per_shard_max` 256 == the enforced
  cap): the `fx_seed_clearance.py` enumeration runs
  at the cap and now asserts the recorded plan sits
  at or under it, so no planned population exceeds
  the enumerated one; span top 97,091,279 and all
  disjointness results are unchanged.
- **§3 — INFORMATIONAL PRINTS.** `probe_report.py`,
  per lever: (i) the predicted Step 2 power against
  the registered two-sample bar (settings
  `report.step2_bar`: PASS iff (gain_new −
  0.0649)/√(SE_new² + 0.0090²) ≥ 1.645), computed
  from the lever's predicted gain with SE_new
  scaled from the probe's 90-game gain SE (read off
  its CI) to 400 games by the √n rule — the whole
  print labeled informational; and (ii) the Step 2
  (400 games) + fleet (per 100 pairs) teacher-arm
  prices at the lever's per-game cost (margin
  503 s; threshold 503 + uncontested/game × 19.5 s
  from the probe's measured populations).
- **Fixtures: 45 → 57 checks, ALL PASS**
  (transcript re-staged at
  `fixtures/fx_r10_outputs.txt`). New in
  `fx_probe_python.py`: the §2.1 writer→reader
  round trip at EVERY = 2 planted in the capture
  hook's real index shape (index → eval jobs →
  eval states → label jobs → label rows → the
  read; the per-game uncontested gain is exactly
  2× the unweighted sum, the CI scales by the same
  factor, a contested-band population in the same
  run is unchanged); class assignment at the z
  boundaries 1.0 / (1.0, 1.5] / > 1.5; the
  calibration print in both branches; the power
  print against an independently computed Φ value
  and both price lines. Two PRE-EXISTING checks had
  encoded the pre-fix behavior and were updated to
  the registered post-fix behavior: the §3 jobs
  check (a (1.0, 1.5] state is now one diagnostic
  job, not zero jobs) and the §4 label-read check
  (the uncontested per-game gain is now the
  weighted 0.5, not the unweighted 0.25). No other
  check changed.
- **Files changed by this pass:** `code/
  settings_probe.json`, `code/build_probe_jobs.py`,
  `code/probe_label_analyze.py`, `code/
  probe_report.py`, `fixtures/fx_probe_python.py`,
  `fixtures/fx_seed_clearance.py`, `fixtures/
  fx_r10_outputs.txt` (re-staged transcript), and
  this doc. Everything else — including the nine
  byte-identical round-9 reuse files, `search_s3.php`
  and its generator/diff, the runner, and the
  reproduction script and its staged output — is
  untouched.

---

## 10. SECOND FIX PASS (2026-10-28) — the confirmation check's two items

Claude's confirmation check on the fix pass
(`claude-reply-af9e9f8.md`) confirmed §9's §2.1
(weighting), §2.2 (calibration print) and the F2
class, and required two mechanical items. Both
are implemented here; nothing else changed.

- **The power print's formula (his §2.1).** As
  first implemented (§9's informational prints),
  `probe_report.py`'s `outlook()` computed
  z = (gain − 0.0649)/√(SE² + 0.0090²) with the
  gain the lever's INCREMENT and SE the
  increment's own scaled SE — it compared an
  increment to a total, so any realistic lever
  printed near-zero power. (The P2 fixture
  matched an independent Φ evaluation of the
  same wrong formula, so it could not catch
  this.) Corrected to the registered form:
  SE_new = √(0.0090² + se_inc,400²) — Stage 3's
  base SE (`report.step2_bar.stage3_gain_se`)
  plus the increment's SE (off its CI) scaled
  from the probe's games to 400 by the √n rule —
  z = inc/√(SE_new² + 0.0090²), power =
  Φ(z − 1.645); the print line states the
  approximation (the build's base gain is taken
  as Stage 3's), and the settings' `step2_bar`
  note now spells the formula (no constant
  changed). §5 item 3's description of the print
  is corrected IN PLACE (this note records that
  it was); §9's informational-prints paragraph
  stands as the first pass's record and is
  superseded by this section. Fixtures: the old
  P2 is REPLACED by two by-hand cases driven
  through the report's `outlook()` code path
  with the contested band's gain object replaced
  — **P2a:** inc = 0 → z = 0, power =
  Φ(−1.645) = 0.04998, asserted ≈ 0.05 within
  0.002 (the bar's own α); **P2b:** inc = 0.03
  with the 90-game increment SE chosen so
  se_inc,400 = 0.005 exactly → SE_new = 0.010296
  (0.0103 to 4 dp), z = 2.1938 (2.194), power =
  0.7084 (0.708), each asserted within 0.002,
  SE_new at 4 dp, and the approximation line
  asserted present in the printed report.
- **The runner's pins (his §2.2).** The runner's
  header claimed expect_hash on every deployed
  file but asserted six; the other ten were only
  recorded in `deployed_code_hashes.txt`.
  `run_probe.sh` now carries machine-copied
  expect_hash literals for all ten:
  `build_probe_eval_jobs.py` (94030b48…),
  `probe_eval_analyze.py` (7c4d9f69…),
  `build_probe_jobs.py` (c08d8c82…),
  `probe_label_analyze.py` (60935aec…),
  `probe_report.py` (82856c6f… — pinned after
  the formula fix above was final),
  `settings_probe.json` (5af0c715…),
  `stage0_report.py` (5c7e5393…), `analyze_l3.py`
  (16017ffa…), `g8_sweep2.sh` (d49981ca…),
  `shm_sweep.py` (98027a8b…) — the last four
  equal their round-9 registered values.
  `fx_pin_guards.py` is EXTENDED: it parses the
  deploy list from the runner's own recording
  loop (the `for f in …; do` that writes
  `deployed_code_hashes.txt` — the list the
  runner deploys by, hence the parse source) and
  asserts every one of the 16 deployed files
  carries a header pin site whose literal equals
  the staged sha256; and a NEGATIVE case writes
  a temporary copy of the runner with the
  `probe_report.py` pin block removed and
  asserts the guard fails on exactly that
  coverage gap (the negative run's lines are
  prefix-labeled "[negative copy]" in the
  transcript).
- **Fixtures: 57 → 86 checks, ALL PASS**
  (transcript re-staged at
  `fixtures/fx_r10_outputs.txt`): +28 in
  `fx_pin_guards.py` (the 10 new per-site pin
  checks, the deploy-list parse, 16 coverage
  checks, the negative case) and P2 → P2a + P2b
  (+1 net) in `fx_probe_python.py`. §6's count
  and its pin-guard and power-print descriptions
  are also corrected in place; this note records
  those corrections.
- **Files changed by this pass:**
  `code/probe_report.py`, `code/settings_probe.json`
  (the `step2_bar` note only — no constant
  changed), `code/run_probe.sh`,
  `fixtures/fx_pin_guards.py`,
  `fixtures/fx_probe_python.py`,
  `fixtures/fx_r10_outputs.txt` (re-staged
  transcript), and this doc. Everything else is
  untouched.

---

## 11. THIRD FIX PASS (2026-10-28) — the capture environment defect (found live, attempt 2)

**The defect.** `search_s3.php`'s uncontested
capture hook gates on `getenv("TEACHER_CAPTURE") &&
getenv("TEACHER_CAPTURE_UNCONTESTED")` (line 1000).
The two variables reach the game process by
different channels: `TEACHER_CAPTURE` is set by
`paired_driver_gravy.py` itself (its capture arm),
but `TEACHER_CAPTURE_UNCONTESTED` had to arrive
through the runner — and `run_probe.sh` never set
it, anywhere. The hook's uncontested branch could
therefore never fire under the runner. No fixture
could see it: the hook fixtures set the env by
hand, and `fx_probe_blocks.sh` stubbed the driver
without inspecting the environment it was invoked
with. **Found live at the first-minutes
verification of launch attempt 2** (the capture
index filled with contested rows only); attempt 2
was killed as void. Attempt 1 never reached
capture (the free-space pre-flight abort), so the
defect was latent, not exercised, there.

**The fix (one variable, the identical channel).**
The runner's capture-phase driver invocation now
carries `TEACHER_CAPTURE_UNCONTESTED=1` in its env
prefix, alongside `GATE_GAME_IDS_FILE` /
`TCG_CLEAN_CHILDREN` — the same channel the runner
already uses to feed the driver, whose child env
is seeded `dict(os.environ)` and passed whole to
the game process (`env=env`). No other runner
behavior changes.

**The fixture (the gap class, not the instance).**
New `fixtures/fx_runner_env.py`: BLOCK:CAPTURE is
extracted VERBATIM from the runner and EXECUTED in
the stub harness with an environment-recording
stub driver; the driver's own arm lines
(`env = dict(os.environ)`; the capture arm's
`env["TEACHER_CAPTURE"] = "1"` +
`TEACHER_SNAP_DIR`; the spawn's `env=env`) and the
hook's gate line are lifted verbatim from their
own files, and the COMPOSED environment is
asserted to carry both gated variables. A NEGATIVE
case runs the same checks against a temporary
runner copy with the assignment removed: the guard
fails there, on exactly the two uncontested checks
(prefixed "[negative copy]" in the transcript).

**Env audit — every `getenv()` in `search_s3.php`
and in the two mains the runner drives**
(`s1_eval_main.php` / `s2_label_main.php`, whose
env sets are identical). "Channel" is how the
variable reaches the consuming process.

| Variable | Consumer | Set by / channel | State |
|---|---|---|---|
| TEACHER_CAPTURE | search_s3.php:1000,1086 (hook gates) | driver, capture arm (`env["TEACHER_CAPTURE"]="1"`) | SET |
| TEACHER_CAPTURE_UNCONTESTED | search_s3.php:1000 (hook gate) | runner, capture invocation env prefix | **WAS UNSET — the defect; fixed by this pass** |
| TEACHER_CAPTURE_UNCONTESTED_EVERY | search_s3.php:1026 (sampling) | nobody — code default 2 == settings `capture.uncontested_every` (2) | BY DEFAULT (registered value) |
| TEACHER_SNAP_DIR | search_s3.php:1032,1089 (snapshot dirs) | driver, capture arm (= logdir/snaps) | SET |
| TEACHER_MODE | search_s3.php:1371 (Decide entry) | driver, teacher-family arms incl. capture | SET |
| TEACHER_GHOST | search_s3.php:1250,1408 | driver, ghost arm only | correctly UNSET in capture |
| TEACHER_SHADOW | search_s3.php:1387 | driver, shadow arm only | correctly UNSET in capture |
| TEACHER_TUPLE_JSON | search_s3.php:858 (SimTeacher_Tuple) | NOBODY in the probe chain (round-9 games runner set it from settings_stage2.json) | **UNSET — FLAGGED, NOT FIXED by this pass; see below** |
| TCG_LEARNER_SEAT | search_s3.php:478,507 (eval payload) | driver (= seat) for capture games; runner for the policy servers | SET where consumed live; unset in eval/label processes, where the production server featurizes from `state["player"]` and ignores the field (round-9 identical) |
| TCG_SEARCH_LOG | search_s3.php:834 (stat writer; silent return if unset) | driver (= logdir) in capture | SET in capture; unset in eval/label, whose mains carry their own EVAL_STATS channel (round-9 identical) |
| SIM_ARS_DESC | search_s3.php:405 (arsenal desc variant in the checkpoint sync) | nobody, in any round | UNSET = stock behavior (the registered featurization) |
| LEAF_HARVEST_DIR | search_s3.php:558 (leaf harvest; returns if unset) | nobody | UNSET = harvest off (round-9 identical) |
| HARVEST_DIR | search_s3.php:1351 (Phase-2b root harvest; skipped if unset) | nobody | UNSET = harvest off (throwaway-tree tool) |
| ISMCTS_D / ISMCTS_S | search_s3.php:1289,1290 (RootDecide; defaults 10 / 12) | nobody, in any round | BY DEFAULT (registered stock values) |
| LABEL_DEBUG | search_s3.php:1687 (debug print) | nobody | UNSET = silent |
| MEAS_JOBS, MEAS_OUT, EVAL_STATS, MEAS_SEED | both mains (inputs/outputs/seed base; the mains ABORT if missing/malformed) | runner, eval AND label invocations (env prefix) | SET |
| EVAL_SETTING_NAME, EVAL_HOOKS, EVAL_DEADLINE_S, LABEL_HORIZON, EVAL_HORIZON_VALUE, EVAL_K | both mains (the pinned tuple; abort on any mismatch with the jobs' setting objects) | runner, eval invocation: R10-EVAL-K25+H (8000/180/62/−1/25); label invocation: L3-W50+H (8000/180/62/−1/50) | SET |
| TCG_POLICY_SOCK | both mains via play_game (policy server socket) | runner, eval AND label invocations | SET |
| LABEL_DRIVER | play_game.php (loaded by both mains) | the mains themselves (`putenv`) | SET (self) |

`search_s2.php` (the label trees' search.php)
carries the same getenv set minus the uncontested
trio; TEACHER_CAPTURE is unset there, so its
contested capture block is inert in label trees —
by design (labels do not snapshot).

**FLAGGED, NOT FIXED — TEACHER_TUPLE_JSON.**
`settings_probe.json` registers a capture
`teacher_tuple` (H8k-180+H: hooks 8000, deadline
180, horizon 62, value −1, k 25, margin 1.5), but
nothing in the runner → driver chain delivers it
as `TEACHER_TUPLE_JSON`, so `SimTeacher_Tuple()`
takes its absent-pin branch. Why this pass does
not treat it as a second instance of the defect,
and does not fix it: under TEACHER_CAPTURE the
Decide path returns the prior pick BEFORE the
first tuple-bound quantity is used (the
uncontested branch returns at the priors; the
contested capture block snapshots and returns —
the rollout loop, the only consumer of
hooks/deadline/horizon/k/margin, is never
entered; the driver's own capture assertions —
`capture_no_rollout_fields`, `no_rollouts_anywhere`
— prove no rollout ran). No trajectory, snapshot,
index row, or estimand in the probe depends on the
capture tuple; the eval and label paths pin their
tuples through the mains' EVAL_* env and the jobs'
setting objects, not through this variable. The
one real effect is a stamp: capture stat rows
carry `"setting": {"name": "unpinned", ...legacy
constants..., "pinned": 0}` instead of the
registered H8k-180+H name. No probe consumer reads
capture stat stamps (the driver assertions do not;
the analyzers audit the eval/label stamps, which
the mains stamp from their own pins). Recorded
here as an open flag for the reviewer: if the
stamp is wanted true to the settings file, the
remedy is one more prefix variable carrying the
settings' capture tuple JSON — a settings →
runner delivery of exactly the kind this pass
adds for the hook, but a separate ruling, not
folded into this one-variable fix.

- **Fixtures: 86 → 99 checks, ALL PASS**
  (transcript re-staged at
  `fixtures/fx_r10_outputs.txt`, byte-stable
  across two consecutive runs): +13 in the new
  `fx_runner_env.py` (12 contract checks + the
  negative-case line), and `run_fx_r10.sh` runs
  it. §6's count and fixture list are corrected
  in place above; this note records the
  corrections.
- **Files changed by this pass:**
  `code/run_probe.sh` (the one prefix variable),
  `fixtures/fx_runner_env.py` (new),
  `fixtures/run_fx_r10.sh` (registers it),
  `fixtures/fx_r10_outputs.txt` (re-staged
  transcript), and this doc. Everything else is
  untouched — in particular `search_s3.php`,
  the driver, and the nine reuse files are
  byte-identical.

---

## 12. FOURTH FIX PASS (2026-10-29) — the silent loader drop (found in attempt 3's analyze phase) and the supplementary recovery

**The defect.** Attempt 3 ran to the analyze
phase, which aborted on its world-count guard:

```
ABORT: world-count guard: job 540261752_t64 candidate 0 has 0 rows, expected exactly 50
```

(preserved in `data/step0/label_read.txt`). The
chain, each link verified in the published rows:

1. The offline eval emits `z = +inf` for a state
   whose paired candidate diffs are constant
   (se = 0) — a legitimate statistic (the
   analyzer's own fixture case A plants it).
2. `build_probe_jobs.py` serialized jobs with
   Python's `json.dumps`, which writes a
   non-finite float as the bare token `Infinity`
   — **invalid JSON**. Ten jobs carried it:
   `jobs_all.jsonl` lines 282–291, snaps
   `540261752_t64..t73`, all game 540261752, all
   class `uncontested` (evidence:
   `data/step0/jobs_all.jsonl`).
3. `s2_label_main.php`'s loader (the round-9
   block) json_decoded each line and kept only
   array results (`if (is_array($j)) $jobs[] =
   $j;`). PHP rejects the bare token, the decode
   returned null, and the line was **dropped
   without a trace** — no count, no warning. All
   ten sat in one invocation (shard 0, player 2:
   105 of its 115 lines loaded).
4. Their worlds never ran. The other 636 jobs
   labeled normally (`labels_all.jsonl` holds
   exactly 63,600 rows = 636 × 2 candidates × 50
   worlds), and the loss surfaced only here, two
   phases later, as the analyzer's guard abort.
   No report was produced.

**What the shift did and did not do.** The
labeler derives each job's seed base from its
index in the LOADED array, so the 105 loaded
jobs of that invocation labeled under bases
compressed by the missing indices. That does
not touch their labels' validity: a base only
has to be unique within the family and paired
across the job's two candidates (CRN), and both
hold — the used values are a subset of the
family's enumerated lattice positions, taken in
order. The 636 jobs' labels stand as labeled.
Only the 10 dropped jobs are missing, and they
never had seed bases at all.

**The fix — writer.** `build_probe_jobs.py`
never emits a non-finite float. A job whose z
is non-finite is written with the finite
sentinel **z = 999.0** and a `"z_nonfinite":
true` field (finite jobs omit the field). The
sentinel bands exactly where +inf banded: above
every class margin and above the analyzer's
`tail_z = 3.5`, so such a job lands in the
uncontested TAIL subset, as +inf did (fixture
N8 proves the banding through the real
analyzer). Second line of defense: every job
line is serialized once, up front, with
`allow_nan=False` — any other non-finite float
in any field aborts the build (exit 2) before
any file is written. The jobs report gains a
`z_nonfinite_jobs` count.

**The fix — loader.** The jobs-load block in
`s2_label_main.php` now counts non-empty lines
read vs jobs decoded and **aborts (exit 2) on
the first line that fails to decode, naming its
line number and file**, with a final count
assertion behind it. No silent drops, ever; the
change is confined to the load block plus a
header note — every other behavior of the
round-9 driver is unchanged. This makes
`s2_label_main.php` the first reuse file the
probe has had to change: it is no longer
byte-identical to round 9 (noted in place in
§2, §3.3 and §7). `settings_probe.json`'s
comment still calls the label machinery
byte-identical; that file is the run's pinned
parameter record and is NOT modified by this
pass — this section supersedes its comment on
the point.

**Pins.** Both changed code files are pinned
in `run_probe.sh`; both literals were updated
from `sha256sum` of the new staged files in
the same pass (machine-copied, the standing
rule): `s2_label_main.php` c7a76af4… →
**1c1dfd9f…** (its pin description updated to
name the change), `build_probe_jobs.py`
c08d8c82… → **f3882a9d…**. The pin-guard
fixture asserts both equalities on every suite
run — the suite failed on the stale writer pin
mid-pass, before the update, which is the
guard working.

**Fixtures: 99 → 109 checks, ALL PASS**
(transcript re-staged at
`fixtures/fx_r10_outputs.txt`, byte-identical
across two consecutive runs): +10 in the new
`fixtures/fx_label_loader.py` —

- N1–N4 (writer): an inf-z state (mean_diff
  2.0, se_diff 0.0 — the t64 shape) through the
  real writer: strict JSON on every line of
  `jobs_all` and the shard files (a
  `parse_constant`-raising parse), the sentinel
  + flag on that job only, the report's count.
- N5–N7 (loader): the load block lifted
  **verbatim** from `s2_label_main.php` (from
  `$jobs = [];` to the setting-audit loop, with
  the file's own `s1_abort`) and run under
  php8.3 — named as an extraction: the full
  driver needs the Talishar tree and a policy
  server. It loads the writer's file whole, the
  sentinel job present and flagged.
- N8 (analyzer): the sentinel job bands in
  class (a)'s TAIL (z > 3.5); a finite z = 2.0
  job bands in class only.
- N9–N10 (negative): a jobs file carrying
  attempt 3's **real line 282** (read from
  `data/step0/jobs_all.jsonl` at runtime) makes
  the loader ABORT at exit 2, naming line 2,
  and load nothing.

**The recovery (design, for review — nothing
has run).** `code/run_probe_recovery.sh` (new):
a single-shot addendum executed on the box from
attempt 3's preserved outputs, under this
section as its registration. It refuses to run
if any of its outputs already exists or any
input is missing. Steps:

1. **Extract** the 10 jobs from
   `jobs_all.jsonl` by snap (the registered set
   `540261752_t64..t73`). Python's json is the
   one reader in the chain that accepts the
   bare token, so the rows are recovered whole;
   the extraction asserts the set (exactly 10,
   game 540261752, class uncontested, z
   non-finite on each) and rewrites them in the
   fixed writer's shape (z = 999.0 +
   `z_nonfinite`) as `jobs_supp.jsonl`,
   serialized with `allow_nan=False`.
2. **Label only them** — one label tree, the
   fixed loader, the registered tuple
   (L3-W50+H), the player-2 policy socket (all
   10 are player 2) — under a **fresh seed
   family, MEAS_SEED = 970055001**. The script
   asserts the loader's own `s2 label jobs=10`
   line in the run log: the whole set loaded,
   proven by the loader that used to drop them.
3. **Seed disjointness.** The family is the
   label lattice at shard index 9
   (70,055,001 + 9×10⁸; no such shard exists).
   Its values are 970,055,001 + ji×100,003 +
   w×31,337 for ji ∈ [0, 9], w ∈ [0, 49] — 500
   values in the interval [970,055,001,
   972,490,541]. Every other family's span,
   bounded at PLANNED counts on its worst
   shard, tops out below it:

   | family | span top |
   |---|---|
   | probe eval (s3, 3300 states) | 661,500,411 |
   | probe labels (s3, cap 256) | 397,091,279 |
   | Stage 3 labels (s3, 176 jobs) | 369,091,039 |
   | round-8 (s3, 547 jobs, W ≤ 100) | 358,481,002 |
   | Stage 2 labels (s3, ≤353 jobs) | 337,691,570 |
   | Stage 0 (s3, span < 27,036,278) | < 327,891,279 |

   The supplementary interval clears the
   largest (the eval family's) by **308,554,590**
   — interval-disjoint from every family, hence
   value-disjoint, a stronger statement than
   the lattice-interleave argument the sibling
   families rely on. (The probe-label family's
   REALIZED span is smaller still: shard totals
   195/159/190/102 bound its tops at
   90,991,096 + s×10⁸.) The base is registered
   here and as a literal in the recovery script;
   `settings_probe.json` is unchanged — the
   recovery is an addendum to the run, not a
   re-registration of it.
4. **Pre-check, then merge.** Exactly 50 rows
   per (snap, candidate) for all 10 jobs is
   asserted before anything merges; then
   `labels_all.jsonl` + `labels_supp.jsonl` →
   `labels_merged.jsonl` (63,600 + 1,000 =
   64,600 rows, 646 jobs).
5. **Analyze + report** over the merged set —
   the registered analyze phase verbatim
   (`probe_label_analyze.py` →
   `label_read.json/.txt`,
   `probe_report.py` → `probe_report.json/.txt`,
   superseding the aborted attempt in OUT; the
   abort line stays in the published
   `data/step0/label_read.txt`), then
   `recovery_manifest.json` (input/output
   hashes, the seed base, the 10 snaps, the
   disclosure text).

**The disclosure the probe report and its data
MANIFEST will carry** (verbatim, also embedded
in `recovery_manifest.json`):

> 10 of the 646 label jobs (snaps
> 540261752_t64..t73) were labeled in a
> supplementary run after the pre-fix loader
> silently dropped their invalid-JSON lines
> (z = Infinity); their worlds ran under fresh
> seed family MEAS_SEED = 970055001. All other
> jobs labeled in the original run. See the
> package doc sec.12.

**In-place corrections by this pass** (the
§10/§11 practice): §2's loader hash and reuse
wording, §3.3's "byte-identical" wording, §6's
check count and fixture list, §7's file lists
(the §12 files added; the loader's hash
corrected) are corrected above; §§9–11 stand
as their passes' records, superseded on the
loader's hash where they quote it.

- **Files changed by this pass:**
  `code/build_probe_jobs.py` (the sentinel,
  strict serialization, the report count),
  `code/s2_label_main.php` (the loud loader +
  header note), `code/run_probe.sh` (the two
  pin literals, machine-copied; the loader
  pin's description and the header comment),
  `code/run_probe_recovery.sh` (new),
  `fixtures/fx_label_loader.py` (new),
  `fixtures/run_fx_r10.sh` (registers it),
  `fixtures/fx_r10_outputs.txt` (re-staged
  transcript), and this doc. Nothing else —
  in particular `settings_probe.json`,
  `search_s3.php`, `search_s2.php` and the
  remaining reuse files are byte-identical.

## 13. FIFTH FIX PASS (2026-10-29) — publish the evidence, check the eval, register the influence read

On `claude-reply-9dae0e2.md` (the fourth pass's
confirmation check: NOT YET — the fixes accepted in
substance, three items required before the recovery
runs). Joe approved the recovery execution on
2026-10-29; this pass is the remaining gate.

### 13.1 Attempt 3's evidence is published (the reply's §2.1)

The fixture suite must pass **from the repo alone** —
a fixture may read only what's published. At
9dae0e2c `data/step0/` did not exist, so
`fx_label_loader.py` N9/N10 (which plant attempt 3's
real bare-`Infinity` line) failed with
FileNotFoundError (107 of 109). Now published under
`data/step0/`, every file fetched from the box and
verified byte-identical against the box copy by
sha256, with `data/step0/MANIFEST.md` recording
sha256 + row counts for each:

- capture: both driver rows (45 + 45), both snap
  indexes (2,565 + 2,688);
- eval: `eval_jobs.jsonl` (5,253),
  `evals_all.jsonl.gz` (381,625 decompressed rows;
  raw 1,171,452,622 B, sha256 `14cfdd35…`; gz
  27,333,659 B), `eval_states.jsonl` (5,253),
  `eval_summary.json`;
- label jobs as the labeler consumed them:
  `jobs_all.jsonl` (646) and all eight
  `jobs_shard*_p*.jsonl` (row counts sum to 646;
  `jobs_shard0_p2.jsonl` is the 115-line shard the
  labeler loaded as 105);
- labels: `labels_all.jsonl.gz` (63,600
  decompressed rows), the aborted `label_read.txt`,
  and every `label_shard*_p*.err` (shard0_p2's
  line 3, `s2 label jobs=105`, is the silent
  drop's fingerprint);
- run records: `probe_launch_manifest.json`,
  `registry_merge_b1.txt`.

With the data in place the full suite passes from
the repo: **126 checks, ALL PASS** (see §13.4).

### 13.2 Eval completeness (the reply's §2.2)

The eval phase's loader (`s1_eval_main.php`) is the
same silent pattern, and `probe_eval_analyze.py`
has no jobs-to-states count guard — a dropped eval
job line would have vanished from every tail rate's
denominator. New `code/eval_completeness.py`
asserts, from the published files, that every eval
job produced world rows for every one of its
selected candidates, and prints the counts.

**As run on attempt 3's published data**
(`eval_jobs.jsonl` + `evals_all.jsonl.gz`):

```
eval job lines: 5253
eval rows: 381625
states with rows: 5253
states complete (every selected candidate at exactly k rows): 5253
missing states: 0
(job, candidate) row counts != k: 0
row split: finished 381587, unfinished 38, refusal 0 (error rows 38)
rows for unknown snaps: 0; rows for unselected candidates: 0
EVAL COMPLETENESS: CLEAN
```

The 38 unfinished rows are all error rows (none in
a refusal class). The eval denominators are whole:
no state vanished. **Recovery wiring:**
`run_probe_recovery.sh` now runs this assertion on
the box's `eval_jobs.jsonl` + `evals_all.jsonl`
immediately after its preconditions — before any
extraction, merge or analysis — and a nonzero exit
aborts the recovery and sends it back to review.
The loud loader for `s1_eval_main.php` itself is,
per the reply, deferred to the next package that
runs an eval; it is not needed now because the
count is clean. Fixtures
(`fixtures/fx_eval_completeness.py`, E1–E3): a
complete synthetic pair passes; the same pair with
one candidate's rows deleted is caught and the
state named; a candidate short by one row is a
named count anomaly.

### 13.3 The influence read (the reply's §2.3)

New `code/probe_influence.py`, wired into the
recovery to run **after** `probe_report.py`; its
outputs (`probe_influence.txt` / `.json`) land
beside the report in OUT, and the recovery manifest
now carries their hashes, the eval-completeness
missing count, and any hold lines. Three parts:

**(a) State inspection of game 540261752** — from
the published files: the driver row's outcome;
for each of the ten snaps (t64–t73): turn, prior
pick vs search pick (card ids), top prior, the
eval's per-candidate finished / unfinished / error
counts (computed from the eval rows in the eval
read's own taxonomy, cross-checked against its
published `cand_diag`), and the prior pick's 25
worlds split into horizon draws priced −1 vs
outright losses. **Classification rule, from the
rows' own fields:** a world is a horizon draw
priced −1 iff `result.horizon == 1` — such rows
record outcome 0 (a draw) and winner 0, and the
registered horizon value (−1) is what prices them
in the eval read (the eval analyzer substitutes
the horizon value whenever winner == 0); an
outright loss is a finished world with
outcome == −1 and `horizon == 0`. The rows
distinguish the two exactly: every `horizon == 1`
row in `evals_all` (67,557) carries outcome 0. For
the record, the inspection's inputs as sampled
during this pass: the capture game itself was a
capped draw (`winner 0, draw true, capped true`,
63 turns, p1life 19 / p2life 8); all ten snaps
read prior pick `chum_friendly_first_mate_yellow`
(cand 0) vs search pick
`prismatic_leyline_yellow` (cand 9) at top prior
1.0; the eval's per-candidate counts are 25/25
finished with zero unfinished and zero refusals in
all ten; and of the prior pick's 250 worlds, 248
are horizon draws priced −1 and 2 are outright
losses. The script recomputes all of this from the
files at recovery time; these sampled values are
what it will print if the files are as published.

**(b) Leave-one-game-out** for each lever's
per-game gain, computed with
`probe_label_analyze.py`'s **own** machinery:
`job_diffs` and `per_game_gain` were lifted from
`main()` to module level in this pass — a pure
refactor, proven equivalent before anything
depended on it (original vs refactored analyzer on
a synthetic three-class set: stdout and JSON
byte-identical) — and `probe_influence.py` imports
them. The weighting is reused, never reimplemented;
per-game totals are `per_game_gain`'s own
aggregation, asserted against its full read
(gain × n_games, tolerance 1e-9). The read prints,
per lever: the LOGO range over all 90 exclusions,
the largest single-game share of the gain and
which game holds it, and the gain + one-sided 95%
lower bound with that game excluded (plus the
weakest exclusion overall).

**(c) The hold rule** (process, not a change to
the decision rule): if a lever is buildable under
the registered rule (its `probe_report.json` gain
lower bound > 0) but its lower bound is ≤ 0 with
any single game excluded, the influence read
prints **"buildable, single-game dependent"** for
that lever — in `probe_influence.txt`, in its
JSON, and (carried by the recovery manifest)
alongside the report. Fixtures
(`fixtures/fx_probe_influence.py`, L1–L3): a
concentrated synthetic table (one game carrying
9.0 of a 9.7 total) is identified with share
9/9.7 ≈ 0.9278, LOGO range [0.7/9, 1.1], the
carrier's exclusion lower bound ≤ 0, and the hold
line fires on a buildable report; a diffuse table
(+0.5 per game, lower bound 0.5 under every
exclusion) and a non-buildable report both stay
silent.

The analyzer refactor changed
`probe_label_analyze.py`'s hash, so its
`expect_hash` literals in **both** `run_probe.sh`
and `run_probe_recovery.sh` were updated from
`sha256sum` of the refactored file (machine-copied,
as always). The recovery also gains pins for
`eval_completeness.py` and `probe_influence.py`,
refusal-list entries for their outputs, and the
eval-jobs / eval-rows / eval-states / driver-row
files as required inputs.

### 13.4 Suite state and files

**Fixtures: 109 → 126 checks, ALL PASS** (the two
new fixture files contribute E1–E3 and L1–L3, 17
checks), transcript re-staged at
`fixtures/fx_r10_outputs.txt` and byte-identical
across two consecutive runs on the finished tree.

**In-place corrections by this pass** (the
standing practice): §6's check count and
per-pass arithmetic are corrected above. Nothing
else in §§1–12 is altered; the recovery's §12
design stands, with the two steps this pass adds
(step 0 and step 4b in the script's header).

- **Files changed/added by this pass:**
  `data/step0/` (new: the published evidence +
  `MANIFEST.md`), `code/eval_completeness.py`
  (new), `code/probe_influence.py` (new),
  `code/probe_label_analyze.py` (the module-level
  lift; math unchanged, equivalence-proven),
  `code/run_probe.sh` (the analyzer pin literal),
  `code/run_probe_recovery.sh` (the completeness
  gate, the influence step, three new pins, the
  manifest additions, header + refusal list),
  `fixtures/fx_eval_completeness.py` (new),
  `fixtures/fx_probe_influence.py` (new),
  `fixtures/run_fx_r10.sh` (registers both),
  `fixtures/fx_r10_outputs.txt` (re-staged
  transcript), and this doc. `settings_probe.json`,
  `search_s3.php`, `search_s2.php`,
  `s2_label_main.php` and the remaining reuse
  files are byte-identical.
