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
`s2_label_main.php` (c7a76af4…, reused byte-identical)
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
pair `va`, horizon 62, draw = 0 read) via the
byte-identical `s2_label_main.php`, on:

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

`fixtures/run_fx_r10.sh` — **ALL PASS (86 checks;
45 at the original package, +12 in the fix pass
(§9), +29 in the second fix pass (§10))**,
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
`reproduce_r9_tables.py`.

**Byte-identical reuse from round 9** (`code/`,
hash-verified copies of the round-9 files):
`s1_eval_main.php` (73ed2482), `s2_label_main.php`
(c7a76af4), `paired_driver_gravy.py` (3389b1b9),
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
