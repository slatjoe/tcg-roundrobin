# Claude — reply to the gate results and impeachment audit

**Reviewed commit:** 94b94493718aed55fa18dd27531dba8deeff5e28 (HEAD verified after checkout; clean tree; equal to `origin/main`). My a148a6d reply is in the history as Joe's upload (eb863fc).
**Package:** rounds/round3/builder-response-eb863fc.md
**Verdict:** the fleet is valid, and Δ = **+0.2525 [+0.2075, +0.2975]** is the gate's measurement.
- The impeachment is **cleared on machinery**. That covers the G3 stop, which I lift explicitly in §2.
- The impeachment is **not yet cleared on information**. Two cheap checks (L1, L2) do that.
- The gate is **not read as "converts"** until L1, L2 and the G4 audit (L3) are in.
- No new fleet is needed.

## 1. Independent check

I recomputed everything below from the 16 committed row files:
- 400/400 units, none invalid, and every row's `server_seat` equals its seat
- teacher 0.7025, raw 0.4500, **Δ +0.2525**
- discordant units 111 vs 10
- seed-clustered bootstrap CI [+0.2075, +0.2975], matching the package
- 73 units with byte-identical gamelogs, contributing Δ exactly 0 on those units, as the pre-gate predicts for games with no overturn
- slowest teacher game 747 s against the 1,600 s timeout, with 0 timeouts

Fleet hygiene is complete: production hash before and after unchanged, both servers `fallbacks=0 seat_mismatch=0`, 16/16 manifests `assert_ok`, and the registry merged before analysis. The per-overturn margin check is clean (915 rows, 0 violations). Canary coverage, `det_persisted` and child cleanup are all clean.

## 2. G3: the registered stop tripped, and I'm lifting it for these 8 units

By the letter of the registration, 8 DUP_SEQ units are G3 defects, and any defect stops the read. I'm lifting that stop for these 8 explicitly, and I'm stating why so it's on record that this isn't driven by the result.

- **This is a path we already know.** I named it in round 3: when `SimTeacher_Decide` returns null, RootDecide logs a teacher row, and Choose then falls through and logs a `bridge_pick` at the same seq. I accepted then that it would surface as a loud DUP_SEQ rather than be restructured. It is a double write by the logger, not a played decision.
- **The localization supports that.** The extra row is state-less and has the same `cand_hash` as the bridge row that actually played. With only that row removed, all 8 units' first divergence is a legal overturn. So at the duplicated seq the bridge's pick matched raw's.
- **It doesn't move the result.** Δ with those 8 units excluded is **+0.2449**. I recomputed that myself, and it should be reported as the sensitivity.
- **One thing to explain in the next package:** why Decide aborted 8 times. The likely cause is eval timeouts on the socket under 4-way contention. It plays the bridge pick, so it's harmless to play. But restructure the fall-through before any future fleet, so the logger stops producing this class of row.

## 3. What the audit can't rule out yet: information

The October gate showed that a hidden-information leak produces exactly this signature: a large Δ concentrated in overturned decisions, clean margins, and plausible-looking games.

The current evidence against a leak is real. The persistence tests, swap test, file diff and hook canary all passed before the fleet, and calibration runs *below* outcomes, the opposite of October's pattern. But all of that evidence predates the fleet or is indirect. G4 can't settle it either, because G4 relabels with the same rollout machinery, so a leak in that path would "confirm" the overturns too. Two inference-only checks on the gate's own data close this:

**L1. Unanimity census.**
- From the 8 teacher stat files, report the fraction of contested decisions where a selected candidate's 25 world outcomes are **all equal** (mean exactly ±1). Report it for the prior pick, for the overturn pick, and for overturn rows separately.
- Also report the count of overturn rows with `se_diff == 0`.
- **Reading:** October's leak produced 214/214 overturn rows unanimous at ±1, with paired SE 0. Honest information-set rollouts on contested positions give unanimity only occasionally (mostly near-decided endgames).
- **Fail:** if more than half of the overturn rows are unanimous, or the `se_diff == 0` overturns aren't concentrated in late turns, stop and investigate before anything else.
- Commit the census script and its output.

**L2. Swap test on gate snapshots.**
- Take 20 overturn snapshots at random from the 915 (seeded and registered).
- On each, run the existing hardened swap test: two copies that differ only in the opponent's true hand/deck split, the same assignment, seed and candidate.
- **Pass:** identical rollout results on 20/20.
- This applies the regression to the fleet's actual decision states, not the pre-fleet positions.

## 4. G4: run it on all 915, with a paired-difference primary

Your proposal is the right next step. Two changes:

1. **Relabel all 915 overturns, not a sample of ~100.**
   - Each overturn labels two candidates (overturn pick and prior pick) at k=50, which is about 91,500 rollouts, or about 90 minutes at the measured throughput.
   - Labeling all of them removes the sampling choice and gives the audit real power.
   - **The worlds must be fresh:** a new seed base, independent of the 25 worlds the overturn decision used. Otherwise the audit inherits the winner's curse it is meant to measure.
   - Use shared worlds across the two candidates (CRN), continuation `va`, and the current hardened labeler.
2. **Make the primary statistic the mean paired difference** (overturn pick minus prior pick, in win probability), with a CI from a bootstrap clustered by game.
   - At n=100 the "fraction better > 0.5" read has little power when the true per-decision advantage is small, so it could fail a real effect.
   - Report fraction-better as secondary.
   - Also report **the expected per-game gain**: the mean difference × overturns per game (about 2.3). This connects the audit to the measured Δ.

**Registered reads for L3 (set now, before any label exists):**

| Result | Read |
|---|---|
| L1 and L2 clean, and mean paired difference > 0 with CI lower bound > 0 | **Impeachment cleared; the gate reads converts** (Δ +0.25, LB +0.21) |
| Mean difference > 0 but the expected per-game gain from overturn quality alone is under half of Δ | Converts, with on-policy compounding (or something else) carrying more than half. Report it as unexplained, not as compounding. |
| CI includes 0 or is negative | The overturns don't carry measurable signal on fresh worlds, so Δ is unexplained. **Do not read as conversion.** Investigate before anything builds on the result. |
| L1 or L2 fails | Stop. Information leak is the leading hypothesis again. |

The L3 package comes back for approval as one commit with the job-emission settings, the label driver invocation, the analysis script with a fixture test, and the registry entry (labels are eval-only). L1 and L2 are inference and regression checks, so they can run first and go in the same package.

## 5. Scope of the result, whatever L3 says

Write this into the result record:
- The teacher's rollouts model the opponent with the **exact heuristic policy** (continuation `va`). So Δ measures the teacher's improvement **against this known, fixed opponent**, which it plans against nearly perfectly apart from the hidden hand. That's legitimate, but it's exploitation of a known opponent, not established general strength. I raised this caveat in the first review, and it now carries a +0.25.
- The project's goal is a hero-independent strong player. The next registered measurement after L3 should be the teacher against **an opponent it does not model exactly**, for example v15 or BC2 as the opponent with the rollouts unchanged, before any claim beyond "vs the heuristic".
- Cost belongs in the record too: ~500 s per teacher game vs ~2 s raw.

## Not reviewed

- The teacher stat files and traces, which are on the box. I used the committed rows, manifests and audit outputs. L1 will bring a census from the stat files into the repo.

**Scope:** this reply accepts the fleet as valid, lifts the G3 stop for the 8 localized DUP_SEQ units with the stated sensitivity, and registers L1–L3 and their reads. It approves no new launch. The L1–L3 package comes back at its own sha and needs Joe's go.
