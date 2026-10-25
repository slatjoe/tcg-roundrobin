# Claude — transfer ruling on the stage-5 Gravy gate fleet

**Reviewed commit:** 9fb0e9856d8bc971713887cdf10a8c168b5192cc (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch manifest `fleet-launch.md` (8816c66). The committed `claude-reply-1ab9903.md` hashes to `ae64a008…f727340cd2be`, the value I gave Joe.
**Package:** `fleet-report.md`, `fleet-analysis.json`, `fleet-diagnostics.json`, `fleet-registry-merge.json` and `fleet-spotchecks.txt`.

**Ruling:**
- **The Gravy transfer does not convert. The registered read, PROJECTION OVERSTATED, stands as the round-7 result.** It is valid: no stop fired, including two stops the report didn't rule on explicitly, which I settle in §2.
- **What it means** (§3): the Fai pipeline, replicated faithfully on Gravy, produced a teacher that is nearly the raw policy. It is not a teacher that searched well and found nothing. The fleet can't say which of those Gravy search would be if it actually ran, so the result is a finding about this teacher configuration on Gravy, not about search on Gravy.
- **The L-run:** **L2 is closed as moot.** **L3 is not run in round 7.** It's the right first measurement for any later Gravy search work, and only then (§4).
- **Round 7 closes on this ruling**, with two records items to finish (§5).

## 1. The primary, checked

I checked the analysis output in `fleet-analysis.json` against the report's counts:
- **Teacher:** 173 W, 86 D, 141 L → 216/400 = 0.5400
- **Raw:** 163 W, 100 D, 137 L → 213/400 = 0.5325
- **Δ = +3.0/400 = +0.0075**

The normal approximation from the reported Σd² = 18.0 gives [−0.0133, +0.0283]. That agrees with the cluster bootstrap's [−0.0138, +0.0288], and the read is the same under both.

**The drop-sensitivity is consistent:**
- (3.0 + 3.5) / 393 = +0.0165
- so raw scored 3.5 on the 7 pairs where the teacher timed out

The non-win co-report is 173 − 163 wins, giving +0.0250, and it's arithmetically right.

**The bands, as registered:**
- conversion fails on both terms
- the CI includes 0 and its upper bound is below +0.10
- impeachment (+0.20) is not triggered

The seat split (+0.0075 each) and the chunks (−0.015 to +0.030) show nothing carrying the result.

**The co-report is not a result.** The teacher decided 14 more games than raw (86 draws against 100), and most of those became wins. That's a hint that search sometimes breaks Gravy's pass-forever stalls. But the co-report was registered with no band attached, and the primary governs. I'm recording the hint as an observation for later work, not as evidence of transfer.

## 2. The stops

These the report settles, and I agree:
- **Teacher timeouts:** 7/400 = 1.75%, so the >2% stop doesn't fire. The rule applies to the final count, so the interim reading of 2.05% at 341 games doesn't count.
- **Canary refusals:** at most 0.134% per stream.
- **Fallbacks:** 0.
- **DUP_SEQ:** none. G3 records defects = 0 with every differing unit at a DECISION overturn, and a DUP_SEQ outside K5 would have shown up as a defect.
- **SHM:** the watchdog never fired, and in-run counts stayed between about 70 and 260.

**Two the report didn't rule on, settled here from its own data:**
- **Stop (e), the calibration void pattern** (K4: prediction *climbing with ordinal and running ahead of* realized). **Not fired.** In G5, the prediction sits **below** realized in bins 1 through 21–40, by 0.01–0.04, and it falls rather than climbs over that range. That's the honest shape the Fai and O fleets showed. Only the 41+ bin reads ahead (0.8025 against 0.7840), on n = 81. That gap is well inside the realized rate's ±0.09 interval, and it's a jump in the small subpopulation of games that run past 40 decisions, not a climb.
- **Stop (a), overturn rows failing their own margin.** The report gives the `se_diff` distribution but doesn't state the check. **Required in the records commit (§5):** count overturn rows with `mean_diff ≤ 1.5 × se_diff` (expected 0), from the stat files. The two rows with `se_diff = 0` pass only if their `mean_diff > 0`. Report their `mean_diff` values. An exactly-zero paired SE with a positive mean means every paired world favored the overturn, a decisive position, which is benign at 2 of 118. The L1 read of no leak signature stands.

## 3. What the null means

**The teacher barely deviated from raw:**
- 305 of 400 units are byte-identical games
- 118 overturns in about 37,000 teacher decisions, roughly 0.3 per game
- the overturn rate is **1.83% even among non-thin contested decisions**, against Fai's 12–16%

So a Δ of about 0 was close to forced. There was very little teacher in the teacher arm.

**There are two channels, and both are in the record:**
1. **The search often didn't run.** 31.7% of contested decisions fell back thin-prior, and the eight streams logged about 37,000 rollout aborts, roughly 4 per contested decision. Gravy rollouts hit the 4,000-hook budget and the 180 s deadlines that were sized on Fai's short games.
2. **When it did run, it rarely cleared the bar.** About 23 finished worlds per candidate, on long, high-variance games, makes the 1.5 × paired-SE margin hard to clear.

It's also possible that v10's prior already sits where search would go.

**The registered sentence applies in full:** a Gravy null must not be read as "search doesn't help" when it may partly mean "search couldn't run". **The ruling, precisely:** the round-7 question was whether the Fai pipeline transfers to a second hero. **As built, it does not:** the teacher configuration doesn't carry over to Gravy-length games. Whether a Gravy-calibrated search would help is not answered, and round 7 should not be cited as answering it.

**On scope, the report's own caveats are accepted as written:**
- v10 is a non-inferiority selection, so this is parity against v10, not against a strong policy
- the fleet tests pipeline transfer, not a hero-independent policy
- the teacher's cost profile (1,263 s/game mean) is recorded for the distillation line

## 4. The L-run

**L2 (the swap control): closed as moot.** L2 exists to impeach a *positive* result that a hidden-information leak could have inflated. There's no positive to impeach, and L1 is clean. Running it buys nothing for this ruling.

**L3 (fresh-world attribution of the 118 overturns): not run in round 7.**
- **Its question isn't this ruling's.** It asks: when the Gravy teacher does overturn, is it right on fresh worlds? The answer can't change a null primary.
- **It is the right first measurement for a later round, if Joe opens one aimed at Gravy search** (search budgets and bounds calibrated to Gravy). Here's why:
  - if the 118 overturns are positive on average, the problem is coverage, and more budget is the lever
  - if they're noise, the overturn bar or the rollout variance is the problem
- At LABEL_W = 50 over 118 jobs, the pooled per-overturn difference would have a standard error of roughly ±0.01, enough to tell those apart.
- **The jobs file is built** (`jobs_all.jsonl`, `5fe5c0d8…`). Keep it in the vault.

**If it's ever run, the L-run needs its own registration.** It runs the rollout machinery on the **production tree**, so it leaks SHM exactly as the fleet did. That means (C) containment there, pointed at that tree's `Games/` directory, plus the standard pre-launch G8 sweep, a timeout set for Gravy-length worlds, and the measurement-build approval rule.

**My recommendation to Joe:** don't spend the L-run's box time to close round 7. Spend it only as the opening step of a Gravy-search round, if you want one.

## 5. To close round 7: one records commit

1. **Stop (a), stated** as in §2: the count of overturn rows failing their own margin, and the two `se_diff = 0` rows' `mean_diff` values.
2. **Independent verification without Joe at a terminal.** Joe's standing change (the builder runs all box checks) is his call, and the commands with raw outputs in `fleet-spotchecks.txt` are the right form under it. But after the probe's discarded monitoring account, builder-run checks aren't independent of the builder's session.

   The way to get independence back without asking Joe to type anything: **commit the fleet's 16 row files** (800 rows, small) and **the pre-gate's two ghost `search_stats.jsonl` files**. Add the eight fleet stat files too, compressed, if they're under about 25 MB together. Each file's hash should match §11 and the pre-gate report.

   I'll then recompute the primary Δ, the timeout rate, the overturn and thin-prior counts, and the K6 line (`496 133 0 0`) myself, from the repo. If any of them disagrees with the report, the ruling reopens. The repo is public. These files carry seeds, game ids and outcomes, and nothing secret, but Joe should confirm he's content to publish them.
3. **The planning lesson, recorded for future timeouts:** the fleet ran **37.5 h against an 18 h estimate**. The teacher's mean of 1,263 s/game was about twice the probe's mean, and close to the probe's *maximum*. The 3,870 s timeout held, but at an interim 2.05% it came within a few games of INCONCLUSIVE. An 8-game probe underestimates both the mean and the tail. Any future teacher fleet should derive its timeout from a larger sample, or from a tail quantile with margin.

**Registry:** 5,031 → **6,161**, `fc46f835…`. 1,130 ids, including the timeout-spawned games, 0 collisions, and the G9 gate passed. Accepted. **The 227 closing segments** are rule-3 parents, inside the expected ceiling of about 800. The next launch's G8 sweep clears them.

## Not reviewed

These are on the box. I took them from the report and the committed JSON:
- the row and stat files, until they're committed (§5.2)
- the sweeper log
- the server logs
- the registry file

**Scope:** this reply rules the round-7 transfer question on the registered primary: **it does not convert, read PROJECTION OVERSTATED, valid.** It records what the null does and doesn't mean (§3), closes L2 as moot and defers L3 to any future Gravy-search round (§4), and asks for one records commit to close the round (§5). No launch is approved or pending.
