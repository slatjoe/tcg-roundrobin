# Claude — reply to the re-specified gate registration

**Reviewed commit:** 2e5e4c5dd15c6aa55b5f1ab662e79de20117bbbc (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-143968a.md` hashes to `cfcabe65…4c3dd0be`, the value I gave Joe.
**Package:** rounds/round7/respecified-gate-registration.md
**Verdict:**
- **The re-gate is APPROVED to run on this sha**, under the conditions in §2. Joe's go is still required.
- The registration is complete as specified in my 143968a §4.
- **But its "Cleared" branch has a gap I didn't catch in 143968a: stage 3's internal gates still use the old instrument.** A cleared re-gate therefore **clears stage 2 only**. Stage 3 needs a short instrument-alignment registration before it launches (§3).

## 1. Completeness against 143968a §4

- **Caps: complete.**
  - `--max-turns 87` on both calls, with the parameter and the 62 trigger both stated.
  - `TCG_MAX_DECISIONS=3000` exported, with the inheritance path re-verified line by line: the copies at :154 and :183, neither overriding the variable, read at `play_game.php:344`.
  - The no-margin note on the decision cap is right.
- **Summary-based draw scoring: complete, and verified the right way.**
  - The per-half summaries already carry `games`, `wins`, `capped_games` and `cap_reasons`.
  - The identity decided = games − capped reproduces the stage-2 composition exactly (112 = 59 + 53, 288 capped).
  - So no per-game capture or code change is needed.
  - Draw-score is (wins + 0.5 × capped) / games, with the non-win score co-reported per half and pooled.
- **Stall guard: complete.** It uses the pooled capped share at n = 400, all reasons. The Wilson95 lower bound is checked against 0.2285. A trip is a stall finding at any read.
- **Validity conditions: complete.**
  - the anchor unchanged and hash-linked (`1e6e3906…48eac288`)
  - fresh workdirs
  - `fallbacks = 0` in both server logs, or the run is void
  - **0 id collisions** against the merged registry, as a condition of the read, with the registry state pinned (`ae7b04b9…`, 3,795 games, vault copy identical)
  - registration under `gravy_anchor_regate_eval` before use
  - the manifest contents listed
- **R4 table and wall-time estimate:** carried.

## 2. Launch conditions for the re-gate

1. **The script.** `run_regate.sh` isn't in the repo. It's fully determined by text: build-package §4's two `eval.py` invocations, plus `--max-turns 87`, `TCG_MAX_DECISIONS=3000` and fresh workdir and socket names. So I'll accept it without a code review, **provided the run manifest carries its full text and sha256 together with its diff against `run_stage2_gate.sh`**, and that diff shows exactly those three changes. Any other difference voids the run.
2. **The read is on the point estimate**, as the original stop was ("reads below 0.40"). Report an interval beside it, computed from the three-category counts (anchor wins, heuristic wins, draws), treating the read as the mean of per-game scores in {1, 0, 0.5}. State the method. The interval doesn't change the read.
3. **Report the decided split** (anchor wins against heuristic wins among decided games) and the capped share **per half**, as well as pooled.

## 3. The gap: stage 3 still measures with the old instrument

The registration says that on **Cleared**, "stage 3 proceeds under its existing approval (ba4e9c97)". It can't do that as written. Stage 3's own gates are built on the Fai-era instrument:

- **Spot gates:** `trainer_v4`'s `run_spot_gate` calls `rl/eval.py` with no `--max-turns`, so the default 60 parameter and 35 trigger apply, and capped games count as non-wins. Measured that way, the anchor read 0.1475. A policy at the anchor's level would read about 0.15 at every spot gate, far under the 0.30 floor, and **PPO would halt at its first spot gate** on the instrument artifact the calibration just identified.
- **The heartbeat (trailing-150 floor 0.30):** this is computed from rollout-worker games under whatever caps `run_workers.sh` passes. Those caps, and how capped games score in the heartbeat, are unstated.
- **C4 formal gates:** these are "the §4 protocol", which is the old instrument. Their thresholds are relative to "the stage-2 anchor's gate read", and after a clear that read becomes the *re-gate's* draw-score, on a different instrument.

**Required before stage 3 (a short registration, its own commit, reviewed):**
1. **Spot gates** on the re-specified instrument: `--max-turns 87`, `TCG_MAX_DECISIONS=3000`, draw-scored. That's a change to `patch_trainer_launch.py`'s launch copy (the `run_spot_gate` call and its read). Show the diff and a logic test.
2. **Heartbeat:** state the workers' caps from `run_workers.sh` / the worker environment, and how capped games enter the trailing-150 rate. Bring both onto the same caps and draw-scoring, or show from the code that they already match.
3. **C4 formal gates** on the re-specified instrument, with draw-scoring. The thresholds are relative to the **re-gate's** pooled draw-score: pass iff the point estimate ≥ that read **and** the lower bound > that read − 0.05.
4. **The floors stay at 0.30** (R3), now read on a draw-scored instrument where the heuristic's self-play is 0.5, which is the same footing they had on Fai.
5. Everything else in ba4e9c97 stands. The **stall guard** should also be reported at each formal gate as a diagnostic (the policy's capped share against the mirror's H′ upper bound). Report-only, not a gate.

None of this depends on the re-gate's result, so it can be drafted and reviewed while the re-gate runs or before it. It touches only the instrument, never the policy or the thresholds' levels.

## 4. Amendment to §4 of the registration (the three-way read)

- **Cleared:** draw-score ≥ 0.40 and the guard not tripped. **Stage 2 is cleared.** `GRAVY_STAGE2_CLEARED` is set **only once the §3 alignment registration is also approved**. Stage 3 then proceeds under ba4e9c97 as amended by that registration, with Joe's per-stage go.
- **Stall** and **Weak:** unchanged.

**Scope:** this approval is valid only for sha 2e5e4c5dd15c6aa55b5f1ab662e79de20117bbbc, for the 400-game re-gate under the conditions in §2, and requires Joe's go. Stage 3 additionally requires the §3 alignment registration. Approval certifies the build as written, not the run as executed.
