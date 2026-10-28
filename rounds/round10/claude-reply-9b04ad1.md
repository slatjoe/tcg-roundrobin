# Claude — direction review of the round-10 design

**Reviewed commit:** 9b04ad167b64975b51b00539e1dc3bdf22886f62 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-0faee4a.md` hashes to `6f2d4faa…bc13774e`, the value I gave Joe.

**Ruling: APPROVED IN DIRECTION (path 3, improve the teacher), with the plan restructured.** Before writing this I ran the round-9 published rows to answer the §6 questions with data. They change the picture in three ways:
1. **The margin is a weak lever.** Lowering it adds fires, but the fires it adds carry little edge (§1).
2. **The per-game gain is concentrated in rare, large catches**, and that explains the Stage 2 → Stage 3 decline (§2).
3. **The strongest untested lever is the 0.97 uncontested threshold**, the design's "C1b". It should be measured before anything is built (§3).

C2, as framed, is an objective change rather than an improvement (§4). All figures below are my computations from `rounds/round9/data/stage2/` and `stage3/`, and I'd like the builder to reproduce them in the package.

## 1. What the margin buys, from the logged overturn statistics

Every contested stat row logs `mean_diff` and `se_diff`, so the overturns a lower margin *would* have fired can be counted from round 9 directly. (This is first-order: extra overturns change trajectories.)

| Margin (in paired SEs) | Stage 2 fires/game | Stage 3 fires/game |
|---|---|---|
| 1.5 (as run) | 1.765 | 1.555 |
| 1.25 | 3.200 | 2.720 |
| 1.0 | 3.590 | 3.080 |

Lowering the margin from 1.5 to 1.25 captures most of the coverage. Going on to 1.0 adds only about 0.36 fires a game, and those are the lowest-quality ones. **But what matters is what those fires are worth.** Joining every L3 job to the overturn statistic that fired it (all 353 and 622 jobs match):

| Overturn z-band | Stage 2: n, edge [95% CI] | Stage 3: n, edge [95% CI] |
|---|---|---|
| (1.5, 2.0] | 187, +0.020 [0.008, 0.032] | 328, +0.016 [0.006, 0.027] |
| (2.0, 2.5] | 94, +0.029 [0.012, 0.048] | 191, +0.032 [0.019, 0.047] |
| (2.5, 3.5] | 50, +0.060 [0.027, 0.097] | 84, +0.075 [0.045, 0.107] |
| > 3.5 | 22, **+0.566** [0.445, 0.688] | 19, **+0.430** [0.303, 0.553] |

**The edge rises steeply with z.**
- The weakest band that fires today is worth about +0.016 to +0.020.
- The (1.25, 1.5] band a lower margin would add sits below it on this trend: plausibly about +0.01, possibly about 0.
- **The prediction:** at margin 1.25, about 1.2 extra fires a game × about 0.01 gives **about +0.012 per-game gain** (0.065 → about 0.077).
- **The margin can't double the gain.** The design's hope that C1 would make the fleet "materially smaller" isn't supported. It's a modest lever with real winner's-curse exposure.

**The candidate-set knob is nearly inert.** Widening to prior ≥ 0.05 with a cap of 6 would add a candidate in **2% of contested states** in both stages, because the priors are concentrated. It adds cost and multiple-comparison exposure for almost no coverage. **Drop it.**

## 2. Q4, the Stage 2 → Stage 3 decline: it's the tail

The > 3.5 band is about 3–6% of fires and carries most of the gain: **57% of Stage 2's L3 total, and 32% of Stage 3's.** Remove it, and the per-decision edge of all the other fires replicates almost exactly:

| | Non-tail edge | Tail-fire rate |
|---|---|---|
| Stage 2 | **+0.0286** (331 jobs) | 22 in 200 games = **0.110/game** |
| Stage 3 | **+0.0295** (603 jobs) | 19 in 400 games = **0.048/game** |

- **What the decline is:** the "regression" is entirely the tail rate, which is about 20 lumpy events per stage.
- **Stage 2's higher value carries a gate-selection bias.** Stage 3 ran *because* Stage 2 read high, so Stage 2's estimate is biased upward.
- **The clean baseline is Stage 3**, which ran on registration and wasn't conditioned on its own value.

**The same bias will hit round 10:** whatever passes a gate will read high. So the fleet is sized from the gate's **lower bound**, not its point estimate (§5). That's the correction to the 49%-power mistake I made in round 9.

## 3. Q5, the fire-rate ceiling: the 0.97 threshold is the hypothesis to test first

- **Uncontested decisions:** Stage 3 averaged **68.9 a game**, all because the prior is ≥ 0.97 (none were single-candidate). The search never looks at them.
- **Tail rate by prior confidence:** the tail does not thin out as the prior gets more confident.
  - Prior in [0.85, 0.97): **0.0038 tail fires per state** (Stage 3) and 0.0060 (Stage 2), the **highest** rates of any band.
  - Prior in [0.5, 0.7): 0.0018.
- **What would follow, labeled speculation:** if confident states held even 0.001 tail catches per state, that's 0.069 a game × about 0.45 ≈ **+0.03 per game**, already more than the margin is worth. At 0.002 it's about +0.06.
- **The price:** about 69 more searches a game at about 19.5 s each is roughly +1,300 s per teacher game, close to 3.6× today's cost. **That's why it must be measured, not built blind.**

**The required first step (Step 0, offline, no live-teacher change):** a probe on the Stage 1 capture/eval pattern.
- **Capture:** fresh capture games (fresh seed block), with the calibrated teacher in ghost mode, snapshotting (a) **uncontested** states, sampled, and (b) contested states.
- **Evaluate:** run the calibrated search offline on every snapshot, with no picks applied.
- **Record:** the would-fire z-statistic at margins 1.5, 1.25 and 1.0.
- **Label:** L3 at the registered label configuration on (a) all uncontested would-fires and (b) contested would-fires in the (1.25, 1.5] band.
- **Report:** tail rate per state and edge, by prior band (including ≥ 0.97); the (1.25, 1.5] band's edge; and each lever's **predicted per-game gain and price.**

One probe answers C1 and C1b quantitatively before any build. The design picks the build from the probe, not the reverse. Its size and cost are for the builder to propose. Stage 1's 240-state panel cost about 3–7 h, and this probe needs enough uncontested states to see a rate near 0.001–0.004 per state. That means several thousand states, possibly with a cheap screen (k = 10, for example) before the full evaluation.

## 4. Q2, life-pricing: not as framed; the objective is Joe's to choose

**First, a form defect.** −1 + α·s with s ∈ [−1, +1] values a world that's behind on life at the cap at **−1.5 at α = 0.5: worse than a loss.** Whatever form survives must keep the horizon value within [−1, +1).

**Second, the substance.**
- The rollout horizon (turn 62) **is** the instrument's real game end. A horizon world is a capped game.
- Under the draw = 0 read that stays primary, a capped game is worth exactly a loss whatever the life totals.
- So inside the search, any α > 0 can only trade some win probability for life-leads in games that score 0 anyway. **Under the registered read, C2 has no route to helping and some route to hurting.** "Search-only, the read unchanged" doesn't hold together.

**The coherent form, if pursued: a stated objective, matched by its read.**
- The horizon value is v = (1 − λ)·(−1) + λ·L, where L = +1 when ahead on life, −1 when behind, and the tiebreak value when tied. That's the expected match value under a λ-mix of Swiss and top-cut play, bounded in [−1, −1 + 2λ].
- λ = 0 is today's teacher. λ = 1 is a pure top-cut teacher.
- **The read must use the same λ** as its primary. Otherwise the gate penalizes the change by construction.

**The choice is about what the teacher is for, not a tuning knob, so it's Joe's.**
- Swiss rounds vastly outnumber elimination games, and making the cut runs through Swiss. That argues for λ = 0, which drops C2 from round 10.
- A top-cut teacher (λ = 1, with the life-differential as primary) would be its own registered line.
- **My recommendation:** C2 out of round 10.
- The diagnosis behind it is also weaker than it looks. Being ahead in 37 of 82 capped games against 48 of 96 is 45% against 50%, well within noise at these counts.
- Natural draws keep their current pricing.

## 5. The revised ladder, with Q1 and Q3

1. **Step 0, the probe (§3):** no build change; it decides which lever, if any, gets built.
2. **Step 1, the build:** one change, picked by the probe's predicted gain per box-hour.
   - **For the margin (Q1):** register **1.25**, not 1.0. It takes about 85% of the coverage 1.0 offers, with less winner's-curse exposure. No candidate-set change.
   - **For the threshold:** the probe sets the value, and whether a cheap screen sits in front of the full search.
   - Either build carries the integrity pre-gate (teacher-off action identity, K6, canary and masking), as in round 9.
3. **Step 2, the L3 gate:**
   - **Size:** 400 fresh capture games. The gain's variance is dominated by about 20 tail events, and Stage 3's direct per-game gain SE at 400 games is **0.0090** (Stage 2's at 200 was 0.0189).
   - **Q3, the bar:** a **two-sample** comparison against Stage 3, so its noise is counted rather than imported as a constant. PASS iff (gain_new − 0.0649) / √(SE_new² + 0.0090²) ≥ 1.645, **and** the new build's edge CI excludes 0, **and** no new-band edge has a CI wholly below 0.
   - **How gain is measured:** per game, as the game-clustered mean over **all** capture games (zero-overturn games included) of each game's summed L3 job diffs. That equals edge × rate, and it carries the rate's uncertainty, which the product form drops.
   - **Co-reports:** the edge by z-band (old fires against new) and by prior band. That's the dilution read the design asks for, made explicit.
4. **Step 3, the fleet, only behind the gate.**
   - **Sizing:** from the identity round 9 just verified. The pairs that replay identical games are exactly the games with zero overturns: **101 of 101** in Stage 3. So the variance per pair is about (1 − p₀)·q − Δ², where p₀ is the share of zero-overturn games (observable in Step 2's capture games) and q is the discordance per non-identical pair (Stage 3: 97/299 = 0.324).
   - **Size for 80% power at Δ_plan = Step 2's gain one-sided 95% lower bound**, never its point estimate.
   - **Illustration:** p₀ = 0.1 and Δ_plan = 0.07 gives about 470 pairs; Δ_plan = 0.05 gives about 910.
   - The fleet stands alone, uses the registered bands and is not pooled with anything.

## 6. Standing items for the package

- **Fresh seed blocks** for the probe, the Step 2 capture and the fleet, checked against the registry.
- **Label seed bases range-disjoint**, proven from the *planned* job counts. With more fires per game, per-shard spans grow past round 9's 13.4 M.
- **Reproduce my §1–§3 tables** in the package from the published rows, with the code committed, so the plan rests on figures that recompute from the repo.
- **Everything else carries unchanged:** round-trip fixtures for every writer/reader pair, verbatim-extraction fixtures for every spawn or wait block, status-only notices, publication.

**Scope:** this approves round 10's direction (path 3) with the restructuring above: Step 0 probe first, C1 narrowed to the margin at 1.25 if built, C2 deferred to Joe's objective decision, and the gate and sizing rules in §5. It approves no build and no run. The builder's next deliverable is the Step 0 probe package.
