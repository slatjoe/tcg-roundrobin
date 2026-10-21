# Claude — reply to the round-7 build package

**Reviewed commit:** dd4cb2fe55abea6a3da0596c97acff7f7500aeb1 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-3c46619.md` hashes to `48f403b7…437ff820`, the value I gave Joe. Joe's ratification note (0ff9b16) records both flags as I ratified them.
**Package:** rounds/round7/build-package.md
**Verdict:** a split approval, which the stage-gated protocol allows:
- **Stages 0–2 are APPROVED to launch on this sha**, with Joe's go: the vocab, the corpora with the pass-1 DAgger, re-featurization, the anchor and the anchor gate with its 0.40 stop.
- **Stage 3 onward is NOT yet approved.** Five corrections (K1–K5, §3) need one small follow-up commit, reviewed before stage 3 starts. Stages 1–2 take about 7 h, so this costs no wall time if the builder drafts it while the corpora generate.

What I checked:
- the package and all six code files
- the trainer patch's replacement list: sha-asserted base, each anchor required exactly once, the full diff printed
- the corpus driver's game-count checks
- the gate runner: required `GRAVY_MODEL` and `GATE_TIMEOUT` with no defaults, explicit deck, chunk-pid wait
- the ratification note

I can't run the box-side tests; I'm relying on the §9 evidence as reported.

## 1. The four focus items

**Stage-0 evidence: accepted.** The assertion was shown in **both directions**: the unextended vocab fails, naming `nullrune_hood` → EMPTY at all three positions, and the extended vocab passes 37/37 and 34/34. That proves the test can fail as well as pass. The append-only check was confirmed by an independent diff (`moved = {}`). This is the loud version of the silent fallback, done properly.

**The trainer patch: accepted, and two good catches.**
- **`DECK_FAI` as a module constant.** An unpatched Gravy run's spot gates would have evaluated a Gravy policy *playing the Fai deck*, a silent wrong measurement inside the run's main behavioral gate. Repointing the constant at both use sites is correct.
- **No suite off-switch.** Mapping `--suite none` to an empty suite reduces acceptance to the KL budget, and it was logic-tested (`(0,0,{})`, `True`).
- **The base is protected.** The patch refuses an unreviewed base by hash and prints its full diff on every application.

**The DAgger resolution (§3): accepted.** This is a correct, evidence-backed build-level correction to my own design text. The generation server's driver loads through the v1-generation pair, so a v3 pass-1 clone couldn't drive the batch. A v1-generation pass-1 clone trained on batches 1+2 is the faithful analog of Fai's bc-v1-driven DAgger. The labels stay the heuristic's argmax either way, so the driver only selects which states get visited, which is the DAgger mechanism itself. The `BCWHEELS` reasoning (the pin follows the driver's training pair) is right.

**The abort-patch decision (§6): reversed. Carry the patch** (K2 below).

## 2. Stages 0–2: launch conditions

- Exactly the registered invocations.
- The stage-1 completion check is **game counts** from `games_w*.jsonl` (2,400 / 750 / 1,500), never a DONE file.
- The pass-1 clone is never gated and never served beyond the DAgger batch.
- The anchor gate is 400 seat-balanced games through `rl/eval.py`. **Each workdir's server log must show the anchor loaded with fallbacks = 0, or the gate is void.** Its games are registered eval-only before anything else reads them.
- **The 0.40 stop is hard.** Below it, the pipeline returns a package, and `GRAVY_STAGE2_CLEARED` stays unset.
- The stage-1 manifest carries the **Flag 1 amendment text** to my round-6 closure, as the template has it.

## 3. Required before stage 3 (one follow-up commit)

**K1. Build a Gravy KL probe set; don't use the Fai one.**
- The divergence budget measures how far a candidate's policy has moved from the anchor. Measured on 27,000 **Fai** states, it measures drift where the Gravy policy never plays.
- This isn't the same as Flag 2. The suite is a judgment instrument with Fai-strategy answers. The probe is a *recipe*: fixed states, reference log-probs, a subsample seed. Applying the same recipe to the hero under test is the faithful transfer, and reusing Fai states is the deviation.
- **Required:** state the Fai probe's construction recipe as it was built (source games, state count, subsample size and seed), and apply it verbatim to the **Gravy heuristic mirror corpus** (`mirror_self`, which exists after stage 1). Commit the build script and the resulting file hash. Its role stays exactly as before.
- For the record, the budget never bound in the Fai run (0.0119 of 0.125), so the practical stakes are modest. That's a reason to make the instrument right cheaply, not a reason to leave it wrong.

**K2. The Gravy tree carries the abort-logging patch** (`search.php` = `8f6b35da…`, the O tree's build).
- My round-4 reply registered, under §3, that "**for any future fleet**, Decide must catch its own exceptions and log the abort reason at the marker". The §6 decision contradicts a standing registration.
- The patch changes no pick, margin, selection or validity logic, and it is fleet-proven: the O fleet ran on it.
- A **new hero** is where new abort classes are likeliest, which is exactly where self-explaining markers pay off. Comparability with the Fai gate isn't at risk, since the difference is logging only.
- Build `/tmp/gravytree` from `/tmp/otree`, and update §6's hash list. The stage-3 census diagnostic doesn't load `search.php` in bridge mode, so its guard can stay as written.

**K3. The pre-gate is the wrong test as written.** §7 describes it as "raw arm, Gravy tree vs the plain bridge". The registered pre-gate (rounds 3 and 4) is **ghost vs raw**: the full teacher machinery with its pick forced to the prior's, against the plain bridge, on the same seeds. It checks that the machinery itself doesn't perturb play. A raw-vs-raw comparison across trees tests something else.
- **Required:** 20 units (8501–8510 × both seats), **ghost arm vs raw arm** on the Gravy tree, against the fleet's per-seat servers, with trace-level equality.
- Run the **raw self-pairing control** alongside it, so the comparison is shown able to see differences.
- Any non-IDENTICAL unit stops the fleet. The only exception is the marker DUP_SEQ class in K5.

**K4. Stop (e) is mis-defined.** "Predicted-vs-actual empty in two or more of the top bins" is not the registered pattern. The calibration void pattern I registered (8d13b0f and onward) is the October signature:
- the **prior-pick rollout prediction climbs with decision ordinal and runs *ahead of* realized outcomes**
- honest runs sit at or below outcomes, as both the Fai gate and the O fleet did

Restate (e) that way.

**K5. State the DUP_SEQ rule precisely.** "DUP_SEQ-class rows are legal game differences" overstates the precedent. The registered rule:
- a DUP_SEQ is a **defect unless** its extra row is the pick-null teacher marker (with `abort_reason`, under K2)
- **and** removing only that marker row makes the stock classifier reclassify the unit as LEGAL
- any other DUP_SEQ is a G3 defect

## 4. Accepted as drafted

- **C1:** the stops restated, with the "~5%" rule explicitly struck.
- **C2:** L2 correctly specified, with its seed registered.
- **C3:** "no detectable conversion" wording, and the normalized co-reports with the Fai references computed (0.4591, +1.0599).
- **C4:** the selection protocol exactly as corrected (≥ anchor read, Wilson lower bound > anchor − 0.05, at most 4, first passer).
- **C5:** the scope stated.
- The census diagnostic on fresh seeds.
- Striking the opponent-is-live check and the dose for a heuristic opponent.
- The registry-before-analysis order, the per-stage manifests, and the ETAs.

## Not reviewed

- The box-side outputs of §9 beyond their reported values.
- The 3b invocation's historical form, which you correctly label a reconstruction.

**Scope:** this approval is valid only for sha dd4cb2fe55abea6a3da0596c97acff7f7500aeb1, for **stages 0–2 only**, under the conditions in §2, and requires Joe's go. Stage 3 and later return as a follow-up commit carrying K1–K5, reviewed at its sha. Approval certifies the build as written, not the run as executed.
