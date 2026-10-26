# Claude — ruling on round-9 Stage 0

**Reviewed commit:** 16f02e2eed6724ad1d0e0ff26ae049fdf36f05e4 (HEAD verified after checkout; clean tree; equal to `origin/main`). The launch commit 5646e695 was verified at launch: its only code change is the one pin line, and the runner hashes to `4f5f8183…`. The committed `claude-reply-a00dad5.md` hashes to `599b764e…ab64c5d`, the value I gave Joe.
**Package:** `rounds/round9/stage0-report.md` and `rounds/round9/data/stage0/`. All 11 files listed in `MANIFEST.md` hash to their stated values.

**Ruling: Stage 0 reads POSITIVE, valid and not instrument-limited.** The round-7 teacher's overturns were good where it searched, which makes **coverage** the binding problem. **Stage 1 proceeds on the bounds grid with the horizon (D7); D6 is not triggered.** One design change for Stage 1 follows from the competition rules Joe confirmed: **a draw is worth 0** (§3).

## 1. Recomputed independently from the published rows

I wrote my own scorer from `jobs_all*.jsonl` and `labels_*.jsonl`, without `analyze_l3`, `stage0_report.py` or `tie_as_loss.py`:
- world score (outcome + 1) / 2
- pairing over worlds both candidates finished
- the per-job mean
- the mean over jobs
- a bootstrap clustered by game
- refusal classes excluded, every other error unfinished

| Read | Report | Recomputed here |
|---|---|---|
| Primary: mean paired diff | +0.0800 [+0.0444, +0.1206] | **+0.0800** [+0.0437, +0.1219] (my RNG) |
| Primary: per-game gain (× 118/400) | +0.0236 | **+0.0236** |
| Primary: draw-sensitivity | +0.0773 | **+0.0773** |
| Primary: pooled unfinished | 12.12% | **12.12%** |
| Horizon: mean, per game | +0.0701, +0.0207 | **+0.0701, +0.0207** |
| Horizon: sensitivity, unfinished | +0.0702, 0.02% | **+0.0702, 0.02%** |
| Tie-as-loss, primary | identical to the standard read | **+0.0800 (identical)** |
| Tie-as-loss, horizon | +0.0712, +0.0210 | **+0.0712, +0.0210** |

Everything matches. The intervals differ only in the fourth decimal, from bootstrap seeding. **Valid:** unfinished at 12.1% is under the 20% ceiling. As registered, a positive read stands either way.

## 2. What it means

- **Per overturn, the Gravy teacher is nearly as good as on Fai:** +0.080 here, against Fai's +0.097 and O's +0.091.
- **Per game, it delivered about a tenth as much:** +0.024 against about +0.22, because it fired **0.295 times per game against Fai's 2.29**.

The round-7 null came from **how rarely the search ran and fired, not from what it did when it fired.** That's the coverage hypothesis, now with direct evidence, and it's what Stage 1 is built to address.

**The horizon result matters for Stage 1.** With the turn-62 draw in the rollouts, label-world non-termination fell from **12.1% to 0.02%**, while the per-overturn edge stayed essentially the same (+0.070 against +0.080). The horizon removes the non-terminating worlds without changing the edge, so it's the strongest single candidate for the completion lever. Settings with the horizon and the old bounds may already clear the completion bar. That's the cheapest outcome, and the selection rule would pick it.

## 3. The tie value: settled for round 9 onward

Joe confirmed that **in competition a draw scores 0 match points, the same as a loss** (Tournament Rules and Policy, Appendix D, confirmed current by a competitive player), and that **the round clock applies to each game.** So the competitive objective is win = 1, draw = loss = 0. That's not a parameter to tune. **Registered for Stage 1 onward:**
- **The search's horizon value:** a rollout still running at the turn-62 trigger scores as a **loss for the root player** (outcome −1), not a draw (0). The same goes for any natural drawn rollout (winner 0). In D7's terms, the horizon outcome is −1. This is a run-pinned parameter, like the horizon itself.
- **Every read** (Stage 1's overturn co-reports, Stage 2's L3 and Stage 3's gate) is primary under **draw = 0**, with the 0.5 reading **co-reported** for continuity with rounds 7–9.
- **Stage 0's tie-as-loss read is already in hand:** +0.0800 primary and +0.0712 horizon. The conclusion is unchanged.

**The deadline itself stays at turn 62 for Stage 1.** Joe is building a turn-versus-time curve for 55-minute Classic Constructed games (each game is clocked; at time the turn finishes, one more turn is played, then it's a draw). If that curve supports a different or random deadline, it becomes **its own instrument registration**, applied to later stages and to any training. Stage 1 doesn't wait for it.

## 4. What the Stage 1 package carries

1. **Capture:** 40 raw-v10 games vs the heuristic on seeds 21001–21040, extending in blocks of 10 if needed; a panel of 240 contested states, at most 8 per game.
2. **The grid,** per D4 and D7: **B0** (old bounds, no horizon, control), **B0+H**, and **{8,000 / 16,000 hooks} × {180 / 360 s}**, all **with the horizon at outcome −1**. k = 25, and the margin doesn't move.
3. **The selection:** the cheapest setting by mean per-decision wall (ties broken by p95, then max) with **all-candidate completion ≥ 95%**, meaning every selected candidate has ≥ 20 finished worlds. Prior-only thin-prior is co-reported against the fleet's 31.7%. **NO CALIBRATED SETTING** if none qualifies.
4. **Faithful settings** (§4(C), clause 8): hooks, deadline, horizon and horizon value as env-read, run-pinned parameters, recorded on every row, aborting on mismatch. The evaluator runs **each setting's own deadline** at **the fleet's contention** (4 concurrent). B0 runs first and prices the rest.
5. **Containment and registry** as standing, the publication pattern, and status-only interim notices.
6. **Before Stage 2's live games (not in Stage 1):** the ghost pre-gate on the new teacher build.

**Scope:** this reply accepts Stage 0 (POSITIVE, valid), confirms D6 is not triggered, settles the tie value at draw = 0 from Stage 1 onward, and specifies the Stage 1 package. It approves no build and no run.
