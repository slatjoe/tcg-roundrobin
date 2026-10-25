# Claude — reply to the round-8 distillation design

**Reviewed commit:** 926f6c315639365fbdd574767cd549da0df72546 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-26290bb.md` hashes to `b176064e…31165b4d1`, the value I gave Joe.
**Package:** `rounds/round8/distillation-design.md`.

**Verdict: the design is APPROVED IN DIRECTION, with the answers below and four additions.** The four additions:
- a label-validity test for the offline labeler (§1)
- **no game-based checkpoint selection** (§4)
- a **featurizer-only control** in the pre-gate (§5)
- **an L2-form swap test** in place of the L1-form check (§6)

The build package comes back for code review; nothing runs before then.

The aim is right: per-hero, on the Fai lineage, where the teacher's edge is proven and leak-audited. So is the scope: two changes, bundled as the round-6 ruling bundled them, with the bundle's combined effect as the measured quantity.

## 1. Q1, the corpus: Option B, agreed, with a label-validity test

B is right. Its states are the ones the student will actually visit, and the per-state cost is far below a teacher game. A rough prior for the pilot to confirm or overturn: the Fai gate's 10,869 contested decisions over 400 teacher games at 372 s/game is about 14 s of teacher time per contested decision. So about 10,000 labels is roughly 40 box-hours serial, about 10 h at the fleet's 4-way parallelism. That's a day, not a week. **The pilot, with its mean and p95, decides.** Option A isn't needed as a supplement.

**Name the existing machinery.** Capturing contested states from v15's play is the driver's **`capture` arm**:
- `TEACHER_CAPTURE=1`
- pick = prior
- no rollouts
- snapshots at contested decisions

The build package uses that arm, rather than a new recorder, unless it shows why not.

**The labeler must be shown to *be* the registered teacher.** A label is the teacher's decision procedure run offline from a snapshot:
- k = 25
- the registered candidate rule
- pair-va continuation
- R17 bridge state at the root
- overturn at > 1.5 paired SE on ≥ 20 finished worlds

That isn't the live `Decide` path. Rollouts are stochastic, so exact reproduction is impossible. The test is consistency:
- **(V1) Self-consistency:** label a fixed set of snapshots twice, under different world seeds, and report the agreement rate on overturns and on confirmations.
- **(V2) Live-consistency:** label snapshots that have a *live* teacher decision on record. The Fai gate fleet's teacher snapshots are the natural set, if they survive. The labeler's agreement with the live pick must be statistically indistinguishable from its own self-agreement (V1).

V2 falling short of V1 means the offline labeler isn't the gated teacher, and the corpus would distill something else. It's cheap, it runs inside the pilot, and it **must pass before the full corpus run**.

**Thin labels:** a label whose search falls under the 20-finished-worlds floor is **excluded and counted**, never labelled with the prior. (Fai's thin rate was 0, so expect it to be near 0.)

**Corpus seeds:** a fresh registered range, disjoint from every range listed in §7 and from the validation and gate ranges. Corpus games are training inputs by design and are listed in the manifest. The design already states the registry discipline the right way round.

## 2. Q2, D1 and D2: both agreed

- **D1:** each arm on its native featurizer. Featurization is part of each policy's definition. §5's control makes the choice measurable rather than argued.
- **D2:** initialize from v15.

**A consequence to carry into T1's loss:** any KL-to-v15 term (§3) evaluates v15's distribution through **v15's native featurizer**, and the student's through the corrected one. Otherwise the regularizer quietly reintroduces the mismatch D1 avoids.

## 3. Q3 and Q4, the training objective

**Q3, the weighting: uniform over contested labels, with no upweighting and no value weighting.** The objective is "imitate the teacher on the teacher's contested states", and the unbiased form of that is uniform. About 87% of labels will be confirmations, and those are what keep the student from overturning everywhere. A single overturn weight, or a weighting by `mean_diff`, is a free knob over a noisy quantity (`mean_diff` and `se_diff` are themselves estimates, and the selection on them is what made each row a label). Leave it out of the primary design.

**Q4, the T1 form: cloning plus a KL anchor, and no value-head training.**
- **Loss** = cross-entropy to the teacher's pick on contested states, plus **β · KL(v15 ‖ student) on the same corpus games' uncontested states.** Those are the states the teacher left to v15, so the student should stay where v15 is. Register **β = 1**.
- **No value-head training from the label margins.** Rollout means sit on a different scale, and play doesn't use the value head. Leave it as v15 had it. If a T2 is ever run, it re-learns the value head.
- **A held-out split** of about 10% of corpus **games**, split by game, not by state, is reserved for §4's stopping rule.

## 4. Q5 and checkpoint selection

**Q5: the round ends at T1's gate. T2 is not in round 8.** PPO polish after distillation confounds what distillation bought, and the KL budget would have to be anchored to something new. If T1 converts, T2 is its own registration later, and that's where the halt-at-budget fix lands.

**Selection: no game-based selection. Exactly one checkpoint enters the gate.** Round 7 showed the cost of choosing on noisy game reads: v10's 0.610 spot read regressed to 0.5225 at its formal gate. So T1 runs a **registered fixed schedule** with **early stopping on held-out cross-entropy** (the minimum, with patience stated in advance). The checkpoint at that minimum is the gate arm. With no validation games and no formal-gate selection, there's no winner's curse in the gate's read.

## 5. The gate, and the featurizer-only control

**The form is as proposed:**
- Fai gate structure
- paired seeds 9001–9200, both seats, versus the heuristic
- 800 games, draw-scored
- fallbacks = 0
- registry merge before analysis
- per-seat splits, the absolute score beside v15's 0.4500, and **the divergence rate**

The divergence rate is the round-7 lesson, applied well.

**The pre-gate (neither arm searches):**
- determinism, with each arm's re-run IDENTICAL on its own tree
- the R16-style seat control
- server and featurizer hash pins **per tree**
- fallbacks

**Add one featurizer-only control, report-only:** **v15 on the corrected tree against v15 on its native tree**, paired on the pre-gate's seeds. This re-measures the round-6 "behavior-nil" claim (pick-flip 0/163) on this instrument. If the games are identical, D1 against its alternative is moot, and the gate's Δ is attributable to the labels alone. If they diverge, the report states how much, and the bundle reading stays as designed. It costs minutes at raw speed.

**The bands (Q6, first part), registered:**
- **Converts:** Δ ≥ +0.10 with CI lower bound > 0. That's about 40% of the teacher's +0.2525 retained.
- **Partial retention:** lower bound > 0, Δ < +0.10, read alongside the divergence rate.
- **Does not convert:** the CI includes 0. The suspects are, in order, the label definition (V1 and V2 are on record) and then the corpus.
- **New: impeach before reading if Δ > +0.25.** A distilled raw policy beating the edge of the teacher it learned from is implausible enough to require audit first.

## 6. Q6, second part: the right impeachment instrument

**The L1-form check doesn't fit.** L1 is a census of the search's rollout statistics, and a raw policy has none. What can carry hidden information into a raw policy is its **features at serving time**. The instrument that tests exactly that is **L2's form, the hidden-card swap**: on registered snapshots, swap the opponent's hidden cards and check the policy's pick is invariant.

**Required for a conversion read:** an L2-form swap test on the **distilled policy**, with **v15 as control**, in the registered 20-snapshot × both-picks shape. Use states drawn from the gate's divergence decisions, the places where the student departs from v15. Both must pass invariance. At raw speed it's cheap.

The observation-masking canary stands alongside it. **The L3 analog** (fresh-world scoring of the divergence positions) **follows a conversion as attribution. It isn't required for the read.**

## 7. Q7, the censuses

- **The teacher-root census: yes, attach it, report-only, on the pilot's label jobs.** The labeler runs teacher roots, so this is the teacher path developing. The pilot's roots are the cheapest place to look.
- **The Gravy census: run it as the report-only pre-step, as proposed.** And a correction for the record: it was registered for the stage-3 report, and **I reviewed that report without noticing it was missing.** That's my miss, as well as the build's. It doesn't bear on a Fai run. Run it once (20 plain Gravy bridge games, seeds 8801–8820, the round-5 probe unchanged), report it, and register the games.

## 8. What the build package carries

1. **The featurizer diff** and its new pin. **Two trees** (native and corrected) and their hash lists.
2. **The capture-run configuration** (the `capture` arm, with the corpus seed range) and **the labeler**. Include the labeler's code and how it invokes the registered teacher procedure from a snapshot, with its hashes.
3. **The pilot:** 20 label jobs, timed, mean and p95, **V1 and V2 with their agreement rates**, the thin-label count, and the teacher-root census. It's sized and reported before the full corpus is approved.
4. **The T1 trainer configuration:**
   - cross-entropy plus β · KL with β = 1, KL computed through v15's native featurizer
   - no value-head training
   - the fixed schedule, the held-out-by-game split, and the early-stopping rule
5. **The gate scripts:** two-tree pairing; pre-gate with determinism, R16, the featurizer-only control, pins and fallbacks; analysis with the bands of §5, the divergence rate, the absolute score, and the L2-form swap on both arms. Plus the records-commit publication pattern.
6. **Containment:** the (C) sweeper and the pre-launch G8 sweep for any teacher work on the production tree, per the round-7 L-run conditions. Timeouts from the pilot's tail, not its mean.
7. **The Gravy census** as the report-only pre-step.

**Scope:** this reply approves the round-8 design in direction and answers Q1–Q7 as above. It approves no code and no run. The build package comes back for code review at its sha. Then the pilot, the corpus, the training and the gate each need Joe's go, with the corpus run approved only after the pilot's V1/V2 and cost reads.
