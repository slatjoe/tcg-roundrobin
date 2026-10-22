# Claude — confirmation check on the stage-3 implementing commit

**Reviewed commit:** 3a37f758f53ff976f6f3e96e3fb843f719c22ea1 (HEAD verified after checkout; clean tree; equal to `origin/main`). Its parent c0ec3f1 adds only my reply. The committed `claude-reply-b876b3f.md` hashes to `15d6f608…a7d3375d51`, the value I gave Joe.
**Package:** `rounds/round7/stage3-alignment-final.md`, plus `code/patch_trainer_launch.py`, `code/gravy_ppo_launch.sh` and `code/run_formal_gate.sh`.
**Verdict:** **CONFIRMED. Stage 3 is approved on this sha, and `GRAVY_STAGE2_CLEARED` may be set.** Four run-time conditions apply to the formal gates (§3). None of them changes a file. Joe's per-stage go is still required.

## 1. The checks in my b876b3f §5

| Item | Required | Found |
|---|---|---|
| `patch_trainer_launch.py` | sha256 `8826e399…6ee36cd27` | **`8826e39975bad516ed23af3d9257a202ba4374b420d40c532c8db466ee36cd27`** ✓. The diff adds changes 4–5 exactly as drafted: six anchored replacements, five for the spot gate and one for the tally, plus the docstring. |
| Launch copy | `a48c4abc…`, from pristine `8fd52d82…` | Re-produced in scratch on the box (§V). I can't run it here because the pristine trainer isn't in the repo. The launcher's guard pins `a48c4abc`. |
| `gravy_ppo_launch.sh` | guard change only, no worker-cap line | **The diff is the three guard occurrences only:** the header comment, the grep pattern and the abort message. The workers invocation is unchanged. There is no `TCG_MAX_TURNS`/`TCG_MAX_DECISIONS` line. New sha256 `53d20b82…4715210` ✓ |
| `run_formal_gate.sh` | §4 form, full text, sha256 | sha256 **`421934d8…8249c461`** ✓. Its text is reviewed in §2. |
| Amended sections | §3.3(a) withdrawn, residual stated, rollout capped-share report, 8×50 form, partial rule, interval wording, R\* | All present: §3.3, §4.1–§4.4 and §4.2 of the final document ✓ |
| Registry merge | 373 ids, expected 4,168 | Recorded in §7: ids cross-checked against the workdirs, backup taken first, 0 collisions, **4,168 games**, `5547cf2b…`, vault refreshed. I take this from the record, since the registry is on the box. ✓ |

## 2. The formal-gate script

**What I ran.** I extracted the pooling tail and ran it here on the re-gate's two half summaries. It reproduces every reported figure:
- draw-score **0.51213 [0.46709, 0.55717]**, var 0.19594
- non-win score 0.40431
- capped share 0.21563, Wilson [0.17681, 0.26028]
- the partial block's worst case **0.47500**

**What's right in it:**
- **The invocations:** eight `eval.py` calls of 50 games, four per deck half, each with its own workdir and socket.
- **The caps:** `--max-turns 87` on every call, and `TCG_MAX_DECISIONS=3000` exported.
- **`eval.py` is untouched.** Each call's exit code and wall time are logged.
- **The interval:** the normal approximation on the score mean is used for the draw-score, and Wilson only for the capped share.
- **The stall diagnostic** is labelled report-only.
- **R\* = 190/371.** The pass test compares against the exact counted value instead of the rounded 0.51213. That's accepted: the two differ by 6 × 10⁻⁷, and the exact value is the honest one.
- **Partial runs are caught.** Any summary error, including a missing summary, triggers the partial block and the "do not read" line. That's conservative, and correct.

## 3. Run-time conditions for the formal gates (no file changes)

1. **Fresh workdirs.** The script runs `mkdir -p` and doesn't refuse an existing `$BASE`. So **each gate gets a new tag, and the gate report shows that `gravy_bc/formal_gate/<tag>` did not exist before the run.** A reused directory voids the gate.
2. **The interval half of the invariance test.** In a partial gate, the tail prints the draw-score at the extreme completions, but **not the interval's lower bound** there. The gate report computes it at both extremes and reads (ii) as follows:
   - **Pass holds under every completion** iff the all-heuristic-wins completion gives a point estimate ≥ R\* *and* a lower bound > R\* − 0.05.
   - **Fail holds under every completion** iff the all-candidate-wins completion gives either a point estimate < R\* or a lower bound ≤ R\* − 0.05.
   - **Otherwise, top up.**

   **The extremes are enough.** I checked over a grid of counted states near the threshold (wins 150–230, draws 40–120, every split of the uncounted games into wins, losses and draws). The lower bound was always lowest at the all-losses completion and highest at the all-wins completion, with 0 exceptions.
3. **Top-ups** use the script's exact `eval.py` command form, in 50-game invocations under a **new** tag (for example `<tag>_top1`). They follow condition 1, and their command lines and summaries go in the gate report. They are pooled with the original gate's counted games, and every id is registered.
4. **Server logs.** The fallbacks = 0 check now covers **all eight** invocation logs, plus any top-up logs. The gate report lists each one.

## 4. Note on §10: what a capped episode pays

`assign_episode_rewards` pays a capped episode **−1.0**, the same as a loss. That corrects reason 1 in my b876b3f §3.3. Training doesn't *reward* stalling: it penalizes capped episodes as losses. So the "cheap stalling" argument was wrong as stated, and I withdraw it.

**The withdrawal of the worker caps still stands**, on reasons 2 and 3, plus one the −1.0 makes sharper. With rollouts capped at 62, every decided game that would have ended after turn 62 would be trained as a **loss**, along with the pass-forever games. That would push PPO toward ending games early, which the gate never asked for.

The heartbeat scores capped games 0.5 while training pays −1.0. That split is deliberate: the alarm measures the instrument's notion of a draw, and the reward is the training signal as approved at ba4e9c97. It's stated in §10 and carried in the stage-3 report.

## Not reviewed

These are on the box, and I took them from §V and §7:
- the scratch re-production of `a48c4abc`
- the registry merge and the vault copies
- the `assign_episode_rewards` source lines

**Scope:** this confirmation approves **stage 3 on sha 3a37f758f53ff976f6f3e96e3fb843f719c22ea1**, under the registration of record (`stage3-alignment-final.md`) and the run-time conditions in §3, with the rest of the ba4e9c97 stack unchanged. **`GRAVY_STAGE2_CLEARED` may now be set.** The launch manifest records R\* = 0.51213, the registry at 4,168 / `5547cf2b…`, and the patch and launch-copy hashes. Joe's per-stage go is required. Approval certifies the build as written, not the run as executed.
