# Claude — reply to the round-7 hero-transfer design draft

**Reviewed commit:** 3c466195f831ea5dc2f039f0572626e2c3a13fc1 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-3e2f6f1.md` hashes to `12864693…161e48cf`, the value I gave Joe.
**Package:** rounds/round7/transfer-package.md
**Verdict:** the design is **approved as the basis for the build package**.
- **Both flags are ratified as recommended**, with one added stop on Flag 2 (§1). Joe's ratification is still needed for the record.
- Five corrections must land in the build package (§2). Two of them fix carried-over text that is wrong: a stop rule I withdrew in round 3, and a mis-described L2.
- Nothing launches on this sha.

This is a design review; there's no code to check. I read the package in full against the round-3/4 registrations it cites.

## 1. The two flags

**Flag 1, the (b) correction timing: ratified, Option A.** Train Gravy on the current featurizer, and let the correction debut in the distillation run.
- My closure said "the next training run". You're right that this is one. But B would confound the project's headline comparison: hero and featurizer would change together, and separating them would take a second ~11 h gate.
- A keeps the transfer test to one variable, and the measured weight of the correction on behavior is nil (0 flips in 163; shifts ≤ 0.0024).
- Train/serve consistency holds under A: Gravy is trained and served on the same featurization.
- The distillation run is the right place for the correction: it retrains the lineage where (b) was measured, and the effect can be isolated as that run's own variable. **Record the re-timing in the build manifest as an amendment to my round-6 closure, not as a silent change.**
- One addition: the census was Fai-only. Gravy has allies and tokens, so its store/view pattern may differ. After stage 3, run the round-5 census probe (unchanged) on 20 plain Gravy bridge games as a **report-only diagnostic**. It reuses existing, reviewed code, costs minutes, and tells the distillation registration whether (b) looks the same on a second hero.

**Flag 2, the canonical suite in PPO: ratified, option (a).** Run without the suite gate; the KL budget, spot gates and heartbeat stay.
- A suite mined from Fai positions can't judge a Gravy policy.
- Inserting a new, unvalidated Gravy suite as a *halting* gate inside the transfer test would add an untested instrument where it can do the most damage.
- The suite's own record (46/50 for a policy winning zero games) supports removing it.

**The added stop.** The behavioral floors (spot gate and heartbeat at 0.30) were set against a Fai anchor at 0.450, a margin of about 0.15. Gravy's heuristic baseline is unknown. **If the stage-2 anchor gate reads below 0.40, stop before PPO and return with a package.** Don't run PPO under floors tuned to a different hero's level. The draft already calls this a stage-2 finding. This makes it a stop, not a report.

## 2. Corrections for the build package

**C1. The standing stops carry a rule I withdrew.** §6 lists "a fleet overturn rate well above ~5% impeaches the margin rule". I withdrew that rule in my 8d13b0f reply: the rule's null false-overturn rate is 12–16%, so a rate alone can't impeach. The registered stops since then are:
- any G3 machinery defect
- **any overturn row failing its own logged margin** (`mean_diff > 1.5 × se_diff` on ≥ 20 shared worlds)
- teacher timeouts above 2% (inconclusive)
- canary refusals above 2% per arm-seat
- the calibration void pattern

The overturn rate is **reported against the 12–16% null band**, and **above 30%** triggers a sample review before Δ is read. Restate the stops exactly this way.

**C2. L2 is mis-described.** §4.5 calls L2 a "40-game trace-verified replay". L2 is the **hidden-card swap test**: 20 seeded overturn snapshots × both picks = 40 checks, with the opponent's hand[0] and deck[0] swapped and the rollout results compared. That's the check that bears on leakage, so the description has to be right. Register its sampling seed for the Gravy fleet.

**C3. The bands need two adjustments for a second hero.**
- **Wording.** "The projection overstated conversion" refers to the Fai §3 off-policy projection. Gravy has no projection. For Gravy, read that band as **"no detectable conversion"**.
- **Baseline.** Δ in raw win rate isn't directly comparable across heroes when the raw arms start at different levels: a raw arm at 0.30 has more headroom than one at 0.55. Keep the registered reads on Δ, as drafted. But **co-report the headroom-normalized gain, Δ / (1 − raw rate)**, for both heroes (Fai: 0.2525 / 0.55 ≈ 0.46), and the log-odds difference. Without them, a Gravy Δ of +0.15 against a raw arm at 0.30 would look like partial transfer when it may be the same relative gain. State in advance that the transfer bands read on Δ, and that the normalized figures are context only.

**C4. Checkpoint selection must be precise, with a cap.** "Passes a formal 400-game gate at the BC standard" needs a definition.
- **Proposed:** the formal gate's point estimate is at least the stage-2 anchor's own gate read, and its CI lower bound is above the anchor's read minus 0.05. That is the v15-over-BC3 pattern written down.
- Candidates are tested **in order (v5, v10, …), at most 4 formal gates**. The first to pass is the raw arm.
- If none of four passes, that's the "no checkpoint passing" finding.
- Every formal gate's games are registered eval-only.
- The cap matters because unlimited sequential gating would select on noise. The paired fleet on fresh seeds protects the teacher Δ, but the selection record should still be honest.

**C5. Name the scope of "transfer".** This tests whether the *pipeline* transfers (data, clone, PPO, teacher, gate on a second hero, producing a second hero-specific policy). It does **not** test a single hero-independent policy. State that in the registration, so that "transfers" isn't later read as more than it is. If the result transfers, the hero-blind or hero-conditioned policy is a later registration, where the distillation run is the natural place.

## 3. Accepted as drafted

- The inventory: no v3 Gravy checkpoint exists (the v2 format won't load), and the vocab covers 36/37.
- The **append-only vocab fix with a loud assertion**. The silent EMPTY fallback is exactly the kind of failure that should be made loud.
- Keeping the Phoenix Flame channel unchanged as a constant 0 for Gravy is the honest like-for-like.
- The audit headline: one hardcoded channel, one Fai instrument, one vocab gap.
- The **two-pass BC** as a registered, forced deviation.
- The corpus recipe, regenerated rather than reused.
- The PPO configuration diffed against 3b.
- The teacher left byte-identical.
- The fleet structure on 8001–8200, with pre-gate, opponent-is-live control, contention-probe timeout, G8 sweep, registry before analysis, and L1–L3 plus G3 as standard.
- The §7 build scope.

## Not reviewed

- Code and configurations, which come in the build package.
- The box-side evidence for the §9 claims, which I accept as stated pending the build package's hashes.

**Scope:** this reply ratifies Flags 1 and 2 (subject to Joe's ratification) with the §1 anchor stop, and registers C1–C5 for the build package. It approves no launch.
