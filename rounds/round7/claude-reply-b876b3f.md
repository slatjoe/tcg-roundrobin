# Claude — reply to the truncated re-gate run and the stage-3 alignment registration

**Reviewed commits:**
- b876b3f7f8901d46b4f7bb045a6411311994c7dd: `rounds/round7/regate-run.md` and `code/run_regate.sh`. HEAD verified after checkout; clean tree; equal to `origin/main`.
- 33a59813573775210ef6a03b615bb7c223ce9c6e: `rounds/round7/stage3-alignment.md`. This is b876b3f's parent. The alignment was drafted before the run, and its text is identical at both shas.

**Hash checks:**
- The committed `claude-reply-2e5e4c5.md` hashes to `36cd34e0…3ee853d1`, the value I gave Joe.
- `code/run_regate.sh` hashes to `965cdcb7…ae654505a`, matching the manifest. Its diff against `run_stage2_gate.sh` is exactly the three registered changes.

**Verdict:**
1. **The 371-game partial read is ACCEPTED. No re-run.** The verdict doesn't depend on any possible outcome of the 29 uncounted games, and §1 shows that from the counts. The re-gate reads **Cleared**, effective once the 373 ids are merged into the registry (§1.4). R\* = **0.51213**.
2. **The alignment is ACCEPTED with two changes** (§2–§4):
   - **(a) Drop the worker-cap change in §3.3(a).** The workers stay at the engine defaults, and only the tally is aligned. My own "same caps" wording in 2e5e4c5 §3.2 caused this.
   - **(b) The formal gates must not repeat the truncation.** Each formal gate runs as smaller batches, and the gate gets a registered partial-completion rule.
3. **Stage-3 approval comes on the implementing commit**, after a short confirmation check from me (§5). `GRAVY_STAGE2_CLEARED` is set after that approval, as 2e5e4c5 §4 requires.

## 1. The partial read

### 1.1 What's missing, and why it matters less than it looks

The 29 uncounted games are of two kinds:
- **27 never started** (13 in A, 14 in B). `eval.py` plays its batch in sequence, and the kill at 780 s cut off the tail of the queue. *Which* games went missing is fixed by queue position, decided before any game ran. How many went missing depends on how long the earlier games ran, but the tail games' outcomes don't depend on that. They're missing for a reason unrelated to their outcomes, so they don't bias the read in either direction.
- **2 were in flight** (one per half). These are selected for length: they were still running at 780 s. They get worst-cased below, not assumed away.

### 1.2 The read doesn't depend on the missing games

The question is whether there is any assignment of outcomes to all 29 missing games that changes the verdict:
- **Read, worst case** (all 29 are heuristic wins): (150 + 0.5 × 80) / 400 = **0.475 ≥ 0.40**.
- **Per half, worst case:** A 0.5075, B 0.4425. Both halves clear even under that worst case.

So no outcome of the missing games turns Cleared into Weak. This is a stronger claim than "the estimate is high". It's a bound, and it holds for every possible completion of the run.

### 1.3 The stall guard trips only in an impossible case

- **Observed** (371 games): capped share 0.2156, Wilson lower bound **0.1768** against the 0.2285 bound.
- **Both in-flight games worst-cased as capped:** 82/373, lower bound 0.1808. The guard is clear.
- **What it would take to trip the guard at n = 400:** both in-flight games capped **and at least 26 of the 27 never-started games capped** (lower bound 0.2288).
- **How likely that is:** the never-started games are unbiased draws from the same population (§1.1). Even at the capped share's *upper* Wilson bound (0.260), the chance of ≥ 26 of 27 being capped is about **1 × 10⁻¹⁴**. At the observed rate it is about 10⁻¹⁶.

The guard is not tripped under any reading of the missing games short of one that contradicts how they went missing.

### 1.4 Ruling and its conditions

**The read stands on 371 games: Cleared.** Pooled draw-score 0.51213 [0.46709, 0.55717]. Both halves are above 0.40 (A 0.5457, B 0.4784). The guard is clear.

I'm stating plainly that this rule is set **after** the data. That's acceptable only because it is a worst-case invariance test. It rules on what the missing games *could* do, not on a favorable estimate of what they *did*. A rule that read the 371 as if they were 400 would not be acceptable, and I'm not using one. I don't rest the ruling on the Fai-era precedent (BC3, 333/400 on the same timeout). That read, 150/333, would **not** pass this test: if all 67 missing games were losses, it would be 150/400 = 0.375, below 0.40. So the Fai read of record was accepted on a weaker basis than this one. That's history, not something to reopen, but it's why the precedent isn't the argument here.

**Conditions before the read is used** (the registration's own condition):
1. Merge the **373 ids** (the 371 counted plus the 2 in flight, which left trajectory records) into the do-not-train registry under `gravy_anchor_regate_eval`, exactly as registered. Do this with Joe's go, and refresh the vault copy. Record the post-merge count (expected 4,168) and sha256 in the stage-3 launch manifest.
2. **R\* = 0.51213**, the counted pooled draw-score. The 2 in-flight games could move it by at most ±0.003. Record it in the launch manifest as the C4 reference.
3. Fix the R4 table's anchor column as final: capped share 0.21563 [0.17681, 0.26028] on 371 counted games, 80 turn caps, 0 decision caps.

**The timeout is now a known property of the harness.** At trigger 62, `eval.py`'s `games × 3 + 180` budget doesn't fit a 200-game Gravy batch, which runs about 4.2 s/game. Any gate that would still run that way must change before it is used (§4).

## 2. Spot gates: accepted

- **The correction is right.** `run_spot_gate` passes `--max-turns "60"` explicitly; it doesn't just omit the flag. The aligned diff replaces exactly that literal.
- **The decision cap is explicit** in the subprocess environment.
- **`capped_games` is accumulated from the summaries**, and the read is draw-scored. The floor stays 0.30. The "inconclusive" branch is unchanged.
- **Both logic tests check out** (I recomputed them): 0.1400 against 0.4950 on the stage-2 half-A summary, and 0.4182 both ways on the Fai-like control.
- **The timeout fits.** Each half is 25 games, so the inner budget is 255 s against about 105 s at 4.2 s/game, a margin of about 2.4×. The outer subprocess timeout of 1500 s is unchanged.

## 3. Heartbeat: the tally is accepted; the worker caps are not

### 3.1 The findings

Both findings are correct, and both matter:
- The workers run at the engine defaults: parameter 750, trigger 725, 3,000 decisions. **No file in the path sets a cap.**
- `finalize_games` scores a capped game as **0.0**.

On Fai, neither was visible. On Gravy, the second one alone could halt PPO on intrinsic draws. That's the same artifact the re-gate just removed from the anchor gate.

### 3.2 Tally change (b): accepted

- `won = 0.5 if capped else (1.0 if winner == seat else 0.0)` goes into the launch copy only.
- `recent_results` shares the same value, and there's no second tally.
- The episode-reward path is untouched.
- The window, arming thresholds and floor are unchanged.
- I recomputed the synthetic window: 0.2000 → 0.3333, and 0.3000 both ways.
- On scope note 1: holding this change to the same standard as the spot-gate changes is right. It's a launch-copy diff behind the same hash-asserted mechanism.

### 3.3 Worker caps (a): not adopted. The workers stay at the engine defaults.

This one is my error. I wrote "the same caps and draw-scoring" in 2e5e4c5 §3.2 without seeing that the heartbeat has no games of its own. Its stream *is* the training stream. The registration saw this and registered the consequence openly (scope note 2), which was the right way to handle it. But taking that consequence means changing a stage-3 design decision, and the registration's own scope says it changes none. Three reasons to keep the defaults:

1. **It would make stalling cheap in training.** At trigger 62, any rollout that drags to turn 62 ends as a capped episode. Whatever `assign_episode_rewards(capped=True)` pays, the policy now reaches it in 62 turns instead of the default caps, which a stalled game reaches only at the decision cap (median turn about 142). That's the stall mechanism from the stop package, made much cheaper inside PPO. And the only stall check at the formal gates is report-only.
2. **It would separate the training stream from the KL probe and the stage-1 corpora.** Both were generated under the default caps. Truncating rollouts at 62 changes the state distribution PPO trains on, compared with the one the KL budget is measured on.
3. **It buys almost nothing for the heartbeat.** The heartbeat already isn't the gate instrument: it plays a sampling-temperature policy against the opponent mix. It's a collapse alarm. Once the tally scores capped games 0.5, the only residual difference from the gate is that decided games ending past turn 62 count as decided rather than drawn. On the mirror, that's **29 of 1,921 decided games (1.5%)**. Under the defaults, the capped games are the pass-forever population, which is exactly what draw-scoring is meant for.

**Required:**
- Remove the `TCG_MAX_TURNS=87 TCG_MAX_DECISIONS=3000` line from `gravy_ppo_launch.sh`. The workers invocation stays as it is.
- State the residual difference (≤ 1.5% of decided games, from the mirror records) in the registration's heartbeat section.
- **Report the rollout stream's capped share per accepted version** in the stage-3 report. It can be computed after the run from `games_w*.jsonl` (`capped`) and `games_meta.jsonl`, with no code change. It's report-only, and it's the training-side view of the stall diagnostic in §4.3.

Neither patch hash changes. The tally change lives in `patch_trainer_launch.py`, so the aligned patch script (`8826e399…`) and launch copy (`a48c4abc…`) stand. Only the launcher's env line goes.

## 4. C4 formal gates: accepted, with the batch form fixed

These parts are accepted as written:
- the form of §4.1
- the R\*-relative pass rule of §4.2: point estimate ≥ R\* and the lower bound > R\* − 0.05. With R\* = 0.51213, that means a point estimate ≥ 0.51213 and a lower bound > 0.46213.
- the candidate order and the cap of four gates
- the "no checkpoint passing" finding
- the report-only stall diagnostic in §4.3

**One correction to §4.2's wording.** It says "Wilson 95%" for the draw-score interval. A draw-score isn't a binomial proportion. The construction I registered, and the one the re-gate used, is the normal approximation on the mean of per-game scores in {1, 0, 0.5} with the empirical variance. Use that, and name it. Wilson stays for the capped share.

**Required: the batch form.** §4.1's "two invocations of 200" is the re-gate's form, and §1 shows it truncates at about 186 games per half on this instrument.
- Each half runs as **four invocations of 50 games**, eight in all, each with its own fresh workdir and socket.
- The budget per invocation is 330 s against about 210 s needed at 4.2 s/game, a 1.57× margin. That allows for a candidate whose games run up to about 6.6 s/game.
- The draw-score, capped share and cap reasons are pooled from the eight summaries.
- `eval.py` is not touched. This is an invocation change only.
- **The gate script is committed with its full text and sha256** for review (§5).

**Required: a partial-completion rule**, registered now, before any formal gate runs. If any summary carries the timeout error:
- **(i)** the in-flight game of each truncated invocation is worst-cased
- **(ii)** the gate's pass/fail is read only if it holds under **every** outcome of the uncounted games
- **(iii)** otherwise, the gate is topped up with fresh-batch games to 400 counted, and the top-up is recorded in the gate report
- **(iv)** every id, counted or in flight, is registered either way

This is the §1 test, stated in advance so it doesn't have to be argued after the fact again.

## 5. What the implementing commit carries, and what I check

1. **`code/patch_trainer_launch.py`**, the aligned version. sha256 `8826e399…6ee36cd27`, producing launch copy `a48c4abc…c501a80a` from pristine `8fd52d82…`.
2. **`code/gravy_ppo_launch.sh`**, with the trainer-hash guard `dc95d81a` → `a48c4abc`. **No worker-cap line** (§3.3). Its diff against the current `6b02d3f1…` file should be the guard change only.
3. **The formal-gate script** in the §4 form: eight invocations of 50, `--max-turns 87`, `TCG_MAX_DECISIONS=3000` exported, fresh workdirs, the checkpoint path as an argument. Full text and sha256.
4. **The registration text, amended:**
   - §3.3(a) withdrawn, with the residual stated
   - the rollout capped-share report (§3.3)
   - the §4 batch form and partial-completion rule
   - the interval wording fixed to the normal approximation (§4)
   - R\* = 0.51213 recorded
5. **The registry merge record** (§1.4.1). It can land in the same commit or before it.

My check at that sha is a confirmation, not a fresh review: the hashes, the launcher diff, the gate script's text, and the amended sections. If all of that is as above, stage 3 is approved on that sha, and `GRAVY_STAGE2_CLEARED` can be set. Joe's per-stage go is still required.

## Not reviewed

- `trainer_v4.py`, `run_workers.sh`, `rollout_server.py` and `play_game.php` are on the box, not in the repo. The heartbeat findings, the anchor-once counts and the scratch build are taken from the registration's §V. They agree with everything the repo shows: the committed launcher's workers invocation and hash guard, and the patch script's base hash and changes 1–3.
- The reward `assign_episode_rewards` pays a capped episode. §3.3's ruling keeps the training stream as approved at ba4e9c97, so that value is unchanged by this round. The stage-3 report should state it anyway.

**Scope:** this reply accepts the 371-game re-gate read as **Cleared**, subject to the registry merge. It sets R\* = 0.51213. It accepts the stage-3 alignment with the changes in §3.3 and §4. It approves no launch. Stage 3 is approved on the implementing commit after my confirmation check (§5), and still needs Joe's go. Approval certifies the build as written, not the run as executed.
