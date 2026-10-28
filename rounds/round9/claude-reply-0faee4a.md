# Claude — ruling on the round-9 Stage 3 report

**Reviewed commit:** 0faee4a6fa31a0334bed69f0fca793b448a7b8e0 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch record at ec5407da.
- **Launched sha:** 3cb82748, which differs from the approved fdd68d64 only under `rounds/`, as the conditions allow.
- **The deployed hashes** listed in `deployed_code_hashes_games.txt` match the confirmed package.
- **The launch irregularities are accepted as recorded.** The free-space refusal is the pre-flight working as built. The missing execute bit was met by running the runner through `bash`, which changes nothing about what ran. The cleanup was verify-then-delete over closed rounds' scratch trees.
- **My last reply:** the committed `claude-reply-fdd68d6.md` hashes to `b7e2de20…37b32bd`, the value I gave Joe.

**Ruling: DOES NOT CONVERT stands.** I recomputed it (§1). The verdict sits on the band's edge, and §2 says plainly what that does and doesn't mean. Round 9 closes on its registered chain (§3), and one question is left open (§4).

## 1. Recomputed from the raw rows

My own code, using neither `stage3_games_report.py` nor `stage3_analyze.py`.

**The games.** 800 rows, 0 invalid, 400 pairs.

| Read | Δ | Seed-clustered CI (B = 10,000, rng 20261027) |
|---|---|---|
| **Primary (draw = 0)** | **+0.0475** | **[0.0000, 0.0950]** |
| Draw = 0.5 | +0.0300 | [−0.0138, +0.0725] |
| Life-differential | +0.0200 | [−0.0275, +0.0700] |
| Seat 1 | +0.0750 | [0.0000, 0.1500] |
| Seat 2 | +0.0200 | [−0.0400, +0.0800] |

All match the report to the fourth decimal.

**Life at the cap.** Teacher 174 wins, 82 capped draws, and ahead in 37 of its capped games. Raw 155 wins, 96 capped draws, and ahead in 48 of its capped games.

**The live rates.**
- 37,100 stat lines = 37,092 teacher rows + **8 R14 canary records**.
- 9,538 contested decisions, 0 thin-prior.
- **622 overturns**, 1.555 per game. They match the 622 jobs one-for-one.

**The L3 attribution.**
- The labels decompress to the manifest's raw sha256 `66e16f51…`: 62,200 rows, 8 aborts.
- Primary **+0.0417 [0.0311, 0.0526]**. Draw = 0.5 gives +0.0390, life-differential +0.0381.
- **Per-game gain** = 0.0417 × 1.555 = **+0.0648**.

## 2. What the verdict means

**The band is exact, and the verdict is what it says.** CONVERTS needs a lower bound **> 0**, and the registered bootstrap's lower bound is **0.0000**. That's not rounding: the pair diffs are whole numbers over 400, so the bootstrap means fall on a grid of 0.0025, and the 2.5th percentile lands on 0.

**It isn't an artifact of the registered rng seed.**
- I re-ran the bootstrap under 40 other seeds. The lower bound fell at −0.0025, 0 or +0.0025, and above 0 in only **2 of 40**.
- Two tests that don't resample agree: the seed-clustered z is **1.92**. Of the 97 pairs whose results differ, the teacher was better in 58 and raw in 39 (two-sided sign test **p = 0.067**).
- Re-reading with a different seed or test until it crosses would be exactly the move the registration exists to prevent. **The registered read stands.**

**So, plainly:**
- The paired estimate is positive, and the teacher won 19 more games than raw over the same 400 seeds and seats.
- At the registered precision, a null is not excluded.
- That is neither "the teacher doesn't help" nor "the teacher converts".

**My precision pricing was wrong, and it shaped this outcome.**
- In my Stage 2 ruling (§4.4) I priced Stage 3's half-width at **about 0.024** from round 7's paired rows. The realized half-width is **0.0475**, double.
- **Why:** round 7's old teacher overturned rarely, so most pairs replayed identical games and their diffs were near zero. The calibrated teacher overturns 1.56 times a game, and **only 101 of 400 pairs have identical gamelogs.** The pairs decorrelate, and the variance roughly quadruples.
- I should have priced from a teacher that actually fires.
- **The consequence:** at the true Δ this fleet estimated (+0.0475), a 400-pair fleet had **about 49% power** to clear the band. The fleet was sized for an effect twice the size it could resolve. That's my miss, not the builder's.

**The attribution:**
- Stage 3's own L3 per-game gain is **+0.065**, against a fleet Δ of **+0.0475 [0, 0.095]**. The two agree: the L3 figure sits inside the fleet interval.
- The ratio would be about 137%, but the §4 guard prints "unstable" correctly. With Δ's CI touching 0, there's no ratio to claim.
- **The overstatement my Stage 2 ruling flagged was real at the projection stage.** Stage 2's +0.11 per game came down to Stage 3's own +0.065: the L3 mean fell from 0.062 to 0.042, and live overturns from 1.77 to 1.56 per game. The game-level Δ is in the range that +0.065 predicts.

**The pricings and the seats:**
- **Draws:** the teacher had fewer capped draws (82 against 96). It converts some deadlocks into wins and some into losses.
- **Life-differential (+0.020):** this is the top-cut price, and it shows the smallest edge. At the cap the teacher was ahead in 37 of its 82 draws, raw in 48 of its 96. The teacher's remaining deadlocks are not ones it's winning on life.
- **Per seat:** seat 1 (+0.075) against seat 2 (+0.020), and block t2b (−0.03). The CIs overlap, so I make no seat claim.

## 3. What round 9 closes

Each question in design §1, answered against its registration:
1. **(i) Do the old teacher's overturns carry a per-decision edge? Yes.** Stage 0 was POSITIVE.
2. **(ii) What makes the search complete on Gravy? The turn-62 horizon, not the bounds.**
   - Stage 1 completion went 0.35 → 1.00 and per-decision cost halved.
   - Hooks and deadlines are inert.
   - Live play confirms it: thin-prior was 0 in 600 games, and unfinished worlds were about 0.01%.
3. **(iii) Does the calibrated search earn a per-decision edge over raw v10? Yes, replicated.**
   - Stage 2 L3: +0.062 [0.044, 0.081].
   - Stage 3 L3, on fresh seeds: +0.042 [0.031, 0.053].
4. **(iv) Does it convert at game level? Not shown at the registered precision.** DOES NOT CONVERT, Δ +0.0475 [0.0000, 0.0950].

**Round 9 closes here as registered.** Per design §5.2, resizing is a new registration, not an automatic extension. Stage 3's Δ is the round's game-level result and is not pooled with anything.

**Post-hoc only:** round 7's fleet re-scored at draw = 0 was +0.0254 [0.0025, 0.0509]. The two fleets point the same way, but **pooling them is not a registered read**, and I'm not making one.

## 4. What it leaves open: the decision is Joe's

The open question is narrow: **is a game-level edge of roughly +0.03 to +0.05 real?** Three paths, each a new registration with its own approval:

1. **Close the line here.** Record the per-decision edge as established, and game conversion as unresolved at about +0.05. No further cost.
2. **A confirmation fleet, sized correctly this time.**
   - **Size:** to resolve Δ ≈ +0.045 at about 80% power, the needed SE is about 0.016. From Stage 3's realized cluster SE (0.0247 at 400 pairs), that's **about 950 pairs (1,900 games)** on a fresh seed block.
   - **Cost:** the teacher arm is about 950 × 503 s ≈ **133 box-hours, roughly 33–35 h of wall time** at 4 blocks.
   - **The rule:** the new fleet stands alone and is **not pooled** with Stage 3. A borderline result followed by "more data until it crosses" is optional stopping.
   - Same build, same tuple, the same bands, and the pre-gate coverage carries over.
3. **Improve the teacher before measuring again.** The game-level edge is small partly because the teacher fires only about 1.5 times a game, and its capped deadlocks lose on life. Measuring a stronger teacher could be the better use of the box-hours.

**On the top cut:** the life-differential read (+0.020) is the smallest of the three. If elimination-round play is what matters, that's the read to watch in any next round, and it isn't one where the teacher is clearly ahead today.

**Scope:** this accepts the Stage 3 report (DOES NOT CONVERT, recomputed and verified) and closes round 9's registered chain. It approves no further build or run. Any of the §4 paths needs its own registration and Joe's go.
