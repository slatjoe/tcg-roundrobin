# Claude — ruling on round-9 Stage 1 (calibration)

**Reviewed commit:** d7b92fdf5373ec86afc34b6f6e3179a4263aab91 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the relaunch record at 9510eb7. The committed `claude-reply-a13cabc.md` hashes to `233e45f3…46242848`, the value I gave Joe.
**Package:** `rounds/round9/stage1-report.md` and `rounds/round9/data/stage1/`.

**Ruling: CALIBRATED SETTING = H8k-180+H, as registered.** Stage 2 proceeds at that setting under its own registration (§3). One finding shapes how the result is read: **under the horizon, the bounds are inert, and the calibration *is* the horizon** (§2).

## 1. Recomputed from the raw rows

I wrote my own computation from `panel_jobs.jsonl`, `jobs_<setting>.jsonl`, `evals_<setting>.jsonl.gz` and `stats_<setting>.jsonl`, using neither `stage1_analyze.py` nor `audit_stage1.py`:
- per-state completion: every selected candidate has ≥ 20 finished worlds
- the candidate-level rate
- thin-prior
- the mean wall from `wall_ms`
- overturns by the registered rule under both valuations

| Setting | Per-state | Candidate | Thin-prior | Mean wall (s) | Overturns: draw = 0 / 0.5 |
|---|---|---|---|---|---|
| B0 (control) | 84/240 = **0.3500** | 0.5609 | **0.4708** | 57.6010 | 4 / 4 |
| B0+H | **1.0000** | 1.0000 | 0 | 26.5662 | 22 / 30 |
| **H8k-180+H** | **1.0000** | 1.0000 | 0 | **26.5486** | **22 / 30** |
| H8k-360+H | 1.0000 | 1.0000 | 0 | 26.5719 | 22 / 30 |
| H16k-180+H | 1.0000 | 1.0000 | 0 | 26.5909 | 22 / 30 |
| H16k-360+H | 1.0000 | 1.0000 | 0 | 26.6267 | 22 / 30 |

Everything agrees with the report. Selection over the five +H settings, by the cheapest mean wall, gives **H8k-180+H**. The control is correctly excluded.

## 2. The finding: the horizon is the calibration

**All five +H settings produced byte-identical world results.** I compared all 17,025 world rows of each against B0+H, excluding `child_state`, and found **0 differences**. The largest hook count of any B0+H world is **1,781** (p99 1,748), under half of even the old 4,000 budget. With the turn-62 horizon, no rollout comes near the hook budget or the deadline, so those bounds never bind. The selection between the five was decided by **wall-clock noise** (26.549 against 26.566 s, a 0.07% spread). It's correct by the registered rule, and behaviorally immaterial: H8k-180+H **is** B0+H with a hook budget twice what it ever uses.

**State the result accordingly:** on Gravy, the round-7 coverage failure (control thin-prior 47%, completion 35%) is closed entirely by **ending rollouts at the instrument's own draw trigger**. More hooks and longer deadlines contribute nothing. The horizon also **halves** the per-decision cost (57.6 → 26.5 s).

**Draw pricing matters for the fires.** 30 overturns at 0.5 against 22 at draw = 0: 8 of 30 fires exist only because a draw was priced at half a win. The live teacher will run at −1 (§3).

**Projection, labeled as extrapolation, not a claim:**
- **Overturns at draw = 0:** 22/240 = **9.2%** of contested decisions, against the fleet's 1.83% non-thin rate.
- **Contested decisions per game:** the fleet's 23.6, giving about **2.2 overturns per game**, close to Fai's 2.29.
- **Edge:** at Stage 0's per-overturn edge (+0.07 to +0.08), the per-game gain would be on the order of **+0.15**.

That's comfortably above Stage 2's +0.05 floor, and it's exactly what Stage 2 exists to test, not assume.

## 3. What the Stage 2 package carries

1. **The live teacher build:** `SimTeacher_DecideInner` and its rollout children get the same env-read, run-pinned tuple: hooks 8,000, deadline 180 s, horizon 62, horizon value −1, k = 25, margin 1.5. It's recorded on every stat row and aborts on mismatch. **The children's hook guards** (currently the label-path global, defaulting to 4,000) must read the live tuple. **The horizon value −1 must apply inside Decide's candidate means**, where it changes picks. Fixtures prove a planted draw-heavy candidate flips between the 0.5 and −1 valuations in the *live* path.
2. **Life totals at the horizon:** both players' life recorded on every world that ends at turn 62, in the live stat rows and in the L3 labels, so a life-differential price can be co-reported beside the registered −1.
3. **The ghost pre-gate** on the new build before any live game: action-identical to raw v10, read through the standard instruments, with K6 as registered. Thin-prior should now be about 0, so K6 should rarely apply.
4. **The games:** 200 calibrated-teacher games against the heuristic, Gravy mirror, seeds 22001–22100 × both seats, at the instrument (87/62), with every overturn captured. **The game timeout** is derived from a tail, not the mean: the Stage 1 per-decision wall distribution (report p95 and max) × the contested-decisions-per-game tail, with the derivation shown. Teacher timeouts are reported; there's no paired arm here.
5. **L3:** all overturns at LABEL_W = 50, CRN, with **horizon 62 and draw = 0 primary** (the selected setting carries the horizon, per 8dddf38 §3), 0.5 and life-differential co-reported, and the unfinished share and refusal tallies as in Stage 0. Label seed family 955001 + shard × 10⁸.
6. **The bands (D3, unchanged):**
   - **PROCEED** iff the game-clustered CI lower bound > 0 **and** the per-game gain ≥ +0.05, with per-game gain = mean difference × **live** overturns per game
   - **DOES NOT PROCEED** or **STOP** as registered
   - **the tripwire:** a per-game gain > +0.25 or a mean difference > +0.20 triggers the L1/L2-form checks before any read
7. **Co-reports:** the live thin-prior and overturn rates against the panel's (0 and 9.2%), and the games' draw-scored outcomes beside the fleet's.
8. **Standing:** containment, the registry merge before analysis, publication, status-only notices, pins format-asserted, and **verbatim-extraction fixtures for every runner block that spawns or waits.**

**Cost** (extrapolated): about 26.5 s × 23.6 contested decisions is about 10–11 min of teacher time per game, roughly half the fleet's 1,263 s, so 200 games is about **35 box-hours serial**, before contention. The package prices it from Stage 1's wall tail, not the mean.

**Scope:** this reply accepts Stage 1 (CALIBRATED SETTING H8k-180+H, recomputed and verified) with the finding that the horizon is the operative change, and specifies the Stage 2 package. It approves no build and no run.
