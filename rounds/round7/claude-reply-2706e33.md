# Claude — reply to the round-7 stop package

**Reviewed commit:** 2706e337223caa3f165064af77649695d9f28a97 (HEAD verified after checkout; clean tree; equal to `origin/main`).
**Package:** rounds/round7/stop-package.md
**Verdict:** **The stop stands. The gate is valid.** Of the four paths in §6, **(d) is not legitimate**, and **(b) and (c) are not legitimate as proposed**. One step is legitimate now: **an instrument calibration (§3 below), with its decision rule registered here, before anyone looks at its numbers.** It doesn't touch the anchor, and nothing past it launches without a further registration and Joe's go.

## 1. Gate validity: accepted

- The arithmetic reproduces: 28/200 and 31/200, pooled 59/400 = 0.1475, Wilson95 [0.1161, 0.1856], to four decimals. Decided games 58 + 54 = 112, split 59–53. Registry 3,076 + 400 = 3,476.
- Server-log evidence meets the registered standard: the anchor loaded as learner in both workdirs, `fallbacks=0` throughout, zero hits on `fallbacks=[1-9]`.
- Registry registration before use, verified by diff against the backup, with all 400 ids tagged and 0 collisions: accepted.
- The halt state is correct: no flag, no PPO dir, no stage-4 tree, no probe. **Stage-3+ approval (ba4e9c97) does not carry over to anything in this reply.**

**Stage 0–2 evidence: accepted.** Corpus counts are exact, record totals sum, and the train/val split sums to the re-featurize total. **The symlink deviation is accepted retroactively.** It was mechanical, disclosed in the manifest at the time, and the verification (18 symlinks, unmodified corpus dirs, line counts summing to the consumed total) is the right kind. The 10h31m wall-clock miss is noted as an estimate miss, not a defect.

## 2. The cap diagnostic: good evidence, two corrections to the reasoning

The composition is the most useful thing in the package: **288/400 turn-capped, decided split 59–53.** Two places where the package's inferences go further than the evidence:

**(i) The decided split doesn't show parity, and it doesn't rule out mechanism 3.** 59/112 = 0.527, Wilson95 [0.435, 0.617]. That is *consistent with* parity, not a measurement of it. More importantly, under a binding cap the decided games are a **selected subset**: the games that happened to finish early. "The entire distance between the decided split and the registered read is the 288 capped games" is true by arithmetic. It isn't evidence about who would have won those 288 games. The heuristic could win most of them if they ran to completion. Mechanism 3 stays open.

**(ii) The decided split doesn't discriminate mechanism 1 (clone stall) from mechanism 2 (cap structure) either.** A heuristic-vs-heuristic Gravy mirror under the same cap could produce the same composition. The discriminator for 1 vs 2 is **the instrument's behavior on the teacher itself**, and the package has the pieces to read most of it without new games (§3).

**One figure needs reconciling.** The gate's mean turns (33.2 / 33.4) with 72% of games at the turn cap puts the cap at **no more than ~46 turns** in the reported units: mean = 0.72·T + 0.28·d with d ≤ T. Round 3 registered the engine turn cap at **60**. Either `rl/eval.py` runs a lower cap than the engine default, or the mean-turns field counts a different unit than the cap. **The package never states the eval protocol's turn cap.** It's the single most important number in §5, and it has to be stated, from the code, with its unit.

## 3. The ruling on §6

**The deciding fact.** The 0.40 line was drawn against Fai's 0.450 (150/333). The repo's Fai-era records show the engine caps essentially never binding on Fai: round 3's launch summary records `capped = 0`, and round 4's gate records 0 capped of 400. If the eval protocol also caps Gravy's *heuristic* mirror heavily, then the 0.40 line is measuring Gravy's game length, not the anchor's play. The stop's own rationale ("don't import another hero's level") would then apply to the instrument as much as to the floors. If the protocol barely caps the heuristic mirror, the anchor genuinely stalls, and the stop is the finding. **That question is answerable from the teacher alone, without the anchor, which is what makes it legitimate to ask after seeing the anchor's number.**

**(d): not legitimate.** It sets the floors from the read the stop was built to catch. And if the cap dominates the read, floors set from it would be cap-dominated too: the spot gates and heartbeat would be reading game length, not behavior. That is re-registering around the result.

**(b) as proposed: not legitimate.** A Gravy cap or a decided-games form chosen *now* is chosen with the anchor's 0.1475 and its 59–53 in view. A re-specified gate can become legitimate, but only through the calibration below, with the cap set from teacher data under a rule fixed in advance.

**(c): not now.** No recipe change can be "aimed at the stall" until a stall is established, and right now it isn't distinguished from the instrument. If the calibration lands in the low band below, (c) may come back as its own registration.

**(a) is always available.** Joe can take it now, and the stop closes the question for this hero.

**Registered: the instrument calibration (call it §6(e)).** Steps 1–2 are analysis only, from existing records:

1. **State the eval protocol's turn cap**, value and unit, from `rl/eval.py` and the sim config it launches. Reconcile it with the gate's 33.2 / 33.4 mean turns. Report the gate's mean turns split by decided vs capped.
2. **Fai anchor's cap composition** from its gate records (the 150/333): capped count, cap reasons, decided split. If those records don't survive, say so; don't reconstruct.
3. **H = the capped share of a heuristic-vs-heuristic Gravy mirror under the eval protocol.** If the cap units match the driver's `turns` field, H can be read off mirror_self's 2,400 rows: the share of games whose turn count exceeds the eval cap, counting already-capped rows as capped. If the units don't match, or the driver's engine differs from the eval engine in a way that matters, H needs a **400-game seat-balanced heuristic-vs-heuristic run through `rl/eval.py`**. That is a registered run: if `eval.py` needs any code change to seat the heuristic as learner, the change comes back for review first.

**Decision rule, fixed now:**
- **H ≤ 0.10:** the instrument isn't what failed the anchor. The stop stands as the finding, path (a). A stall-aimed recipe (path c) may be proposed later as a separate registration.
- **H ≥ 0.40:** the protocol doesn't measure Gravy play at this cap, and the 0.40 line isn't meaningful on it. A re-specified gate may come back as a registration, under these terms:
  - its turn cap is set from the **heuristic mirror's** decided-game length distribution (the 99th percentile), never from the anchor's games;
  - capped games score as non-wins, as now;
  - the 0.40 line is kept unchanged;
  - the floors stay at 0.30.
- **0.10 < H < 0.40:** report the numbers and stop. No pre-set rule; it comes back to me and Joe.

## 4. Open items

1. **The 72 deleted `/tmp/eval_v*` dirs vs the 320 loose eval-only games.** §7 still carries 320 unregistered eval-only games as a standing loose end. Confirm that their ids are recoverable from records outside the deleted dirs (committed data or persistent workdirs). If any of the 320 ids lived only in a deleted workdir, say which, so the loose end is restated as partly unrecoverable rather than open.
2. **Registry durability.** The registry backup sits on `/tmp/harvest`, a 20G tmpfs that filled once this run. State where the live registry lives. If it's on tmpfs, a reboot erases the do-not-train record, so copy both it and the backup to persistent storage and record the hashes.
3. **Anchor hash linkage.** Confirm that the stage-2 manifest records the same sha256 for `bc3_policy.pt` that §2 gives (`1e6e3906…48eac288`).

**Joe:** the stop needs no action to stand. If you want the calibration, steps 1–2 are reading only. Step 3's run, if it's needed, needs your go at the sha where it comes back.
