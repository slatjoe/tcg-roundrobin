# Round 8 — Distillation: design for review

**Parent:** 939f65e0 (round 7 closed; Claude's independent recomputation, every figure exact).
**Status:** DESIGN FOR REVIEW. Nothing is built, generated, or launched. Approval of this design leads to a build package (code, hash-pinned, per the measurement-build approval rule); any run then needs Joe's explicit go in chat.
**Direction:** Joe, 2026-10-25 ("Distillation — draft the design for Claude"), following the recommendation that the cost line is next.

## 1. The mandate this answers

From the round-6 closure (`rounds/round6/claude-reply-3e2f6f1.md`), the measurement arc's second line:

> "Cost. The teacher plays at about 370 s per game against about 4 s for raw v15. Distilling the teacher's overturns into the policy is the natural route: train on overturn labels, with the next training run carrying the (b) featurizer correction. That turns a +0.2 search-time gain into a cheap policy, and it is also where the opponent-pool ceiling (every available opponent is under 10% dose) can start to lift."

And the aim, from the transfer design's stated consequence (`rounds/round7/transfer-package.md`), now live because the transfer did not convert as built: the distillation line is **re-aimed per-hero** — this round distills on the **Fai lineage**, where the teacher's edge is proven (+0.2525 vs heuristic; +0.2050 vs BC3 at 5.3% dose, both leak-audited). A hero-conditioned or hero-blind policy remains a later registration.

**The claim this round will support, if it converts:** a raw policy, trained on the teacher's decisions and served at raw-policy speed (~4 s/game), retains a registered fraction of the teacher's paired edge over v15 — measured fresh, paired, and audited, under the same discipline as the gate that produced the teacher's number.

## 2. The two changes, and only two

Against the Fai lineage's last training run, this run changes exactly:

1. **The training signal** — teacher labels (§5) join the run.
2. **The featurizer** — the (b) correction debuts (§4): deck counts read from the getter **view**, as every other zone already is, instead of from the store.

Everything else — architecture, deck (`decks/nats2026_ashlyn_fai_60.txt`), vocab, teacher configuration, KL/spot/heartbeat discipline where it applies — is carried over unchanged and hash-pinned in the build package. One-variable discipline is relaxed only where the mandate itself bundles the two changes, and §7's gate is designed so the bundle's combined effect is the measured quantity; isolating the featurizer's share is explicitly **not** a claim of this round (its behavioral weight on the current lineage measured nil at play: pick-flip 0/163).

## 3. Scope

- In scope: Fai mirror; the v15 lineage (`rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt`, sha256 `0400539d…`); the teacher exactly as gated (k=25, top-3 + prior ≥ 0.10 cap 4, continuation value, overturn at 1.5 paired SE, ≥20 finished worlds).
- Out of scope: Gravy (round 7 closed; a Gravy-search round is a separate registration), any hero-conditioned policy, any change to the teacher's configuration, any use of pre-fix label files (§5.4).

## 4. The featurizer correction

- **The change:** in `featurize.php`, the deck-count features read `SimV1_DeckCards` (the store); the correction reads them from the same getter view the other zones use. The build package carries the exact diff and the new hash pin. The load-bearing store:=view checkpoint sync is **not** touched (round-6 finding: removing it would break the bridge).
- **Where it applies:** the distillation run's training featurization **and** the distilled policy's serving featurization — training and serving change together, which is the round-6 ruling's whole point.
- **Gate arrangement (decision D1, proposed):** each arm is served by its **native** featurizer — the distilled policy by the corrected build, v15 by the build it was trained under. Serving v15 through the corrected featurizer would hand the control arm a train/serve mismatch the round-6 closure explicitly warned against; the pairing (seeds, seats) is unaffected, and featurization is part of each policy's definition. The alternative — both arms on the corrected build — is named and rejected on that reasoning. Claude's call if he reads it differently.

## 5. The label corpus

### 5.1 What a label is

At a **contested decision** (the teacher's registered contest rule), the label is the **teacher's pick** under its registered configuration, recorded with the featurized state (corrected featurizer), the prior pick, the candidate set, `n_worlds`, `mean_diff`, and `se_diff`. Overturns are the headline signal, but contested decisions where the teacher **confirms** the prior are also recorded — a distilled policy needs the teacher's judgment on the states where it agrees, or the corpus teaches it to overturn everywhere. Weighting (overturns upweighted?) is Q3 for Claude.

### 5.2 Two ways to generate it

- **Option A — the teacher plays.** Teacher-vs-heuristic and teacher-vs-BC3 games, labels recorded live at every contested decision. Labels sit on the teacher's own trajectory distribution. Cost driver: the teacher's Fai game time, **372.1 s/game** (gate measure) — a 1,000-game corpus is ~103 box-hours before parallelism.
- **Option B — the teacher labels the student's trajectories.** Cheap raw-policy games (v15 vs heuristic, v15 vs BC3, v15 mirror; ~4 s/game) are recorded with their decision states; the teacher's decision procedure is then run at each contested state from the recorded state, L3-machinery style (fresh determinized worlds from the root state, registered server rules for label work). Labels sit on the distribution the distilled policy will actually visit — the states where v15's own play leads, which are the states the distilled policy inherits. Cost driver: per-state teacher decisions, not whole teacher games.

**Recommendation: Option B as the primary corpus**, with Option A games as an optional supplement if Claude wants teacher-trajectory coverage. B is cheaper by roughly the ratio of contested decisions to full games, it reuses the label machinery whose outputs the audits already know how to check, and its state distribution is the right one for distillation. The build package must carry a **measured pilot** (20 label jobs, timed, tail reported) before any full corpus run is sized — the round-7 planning lesson (an 8-game probe underestimated the fleet's mean by ~2× and its tail worse) applies to every estimate in this round.

### 5.3 Corpus size (proposal, Claude to set)

Fai fleets give the scale: 10,869 contested decisions in the gate fleet, 10,648 in the O fleet, with non-thin overturn rates of 12–16%. A corpus target of **~10,000 contested labels** (≈ one fleet's worth, expected ~1,200–1,600 overturns) from fresh raw-policy games is proposed as the starting size, with the pilot's per-label cost deciding whether that is a day or a week of box time.

### 5.4 Exclusions

- **No pre-fix label material.** The `/tmp/harvest/labels*` files from the determinization era (Phase 2b and leaf-tranche labels) are VOID and are not inputs. The corpus is generated fresh, under the fixed code and the corrected featurizer, and hash-pinned in the build manifest.
- **Registry discipline, stated the right way round:** corpus games are training inputs by design and are listed in the manifest; the **gate** fleet's games are evaluation-only, join the do-not-train registry (currently 6,161 games, sha256 `fc46f835…`) before analysis, and their seed range is excluded from every corpus and training input.

## 6. Training

- **Initialization (decision D2, proposed):** from **v15** — the policy whose decisions the teacher corrected. Initializing from the BC3 anchor (`78e2950c…`) would throw away the PPO run the teacher was measured against. Claude's call.
- **Stage T1 — supervised distillation:** a behavior-cloning pass over the corpus (the BC trainer lineage that produced BC3, fed records in its shape), student = v15's architecture and vocab, featurization = corrected build throughout. KL-to-v15 regularization or a prior-agreement term, if any, is Claude's design choice (Q4).
- **Stage T2 — PPO polish (separable; Q5):** a `trainer_v4.py`-shape PPO run from the T1 checkpoint, carrying the corrected featurizer end-to-end, KL budget 0.125, spot gates and heartbeat as registered for stage 3 of round 7, and the halt-at-budget launch-copy fix (round 7 found the trainer sailing through its budget at lr ~1e-12; any PPO launch copy in this round halts at budget). Whether T2 belongs in this round or waits on T1's gate read is Claude's call; the design prices them separately so the round can stop after T1 with a complete result.
- **Checkpoint selection:** by a registered rule, not spot-gate impression — formal-gate form (round 7's C4 pattern) on a validation seed range disjoint from the gate fleet's, candidates in version order, first passer selected, ≤ 4 gates.

## 7. Evaluation — the distillation gate

- **Form:** the Fai gate's, verbatim in structure. Paired, fresh seeds **9001–9200** (checked against every range used to date: fleets 1001–1200 / 2001–2200, probes 3000s, controls 4001–4014, smokes 5001–5010 / 7001–7002, census 6001–6040, ghost 8501–8510, Gravy fleet 8001–8200, Gravy census 8801–8820), both seats, Fai mirror vs the heuristic, 800 games, draw-scored primary (engine caps at 0.5, per the standing instrument), fallbacks = 0, registry merge before analysis.
- **Arms:** distilled policy (corrected featurizer) vs **raw v15** (native featurizer) — the direct paired measure of what distillation bought, at equal (raw) speed.
- **Co-reports:** the distilled policy's absolute score vs the heuristic beside v15's 0.4500 (gate fleet) — the retention read against the teacher's +0.2525; per-seat splits; the distilled-vs-v15 decision-divergence rate (how often the student actually departs from v15 — the round-7 fleet taught us to report whether the arm under test *acted* differently at all).
- **Proposed bands (Claude to set):** paired Δ (distilled − v15) ≥ **+0.10** with CI lower bound > 0 → **distillation converts** (≥ ~40% of the teacher's edge retained at ~1% of its cost). CI lower bound > 0 below +0.10 → **partial retention**, read with the divergence rate. CI including 0 → **does not convert**; the corpus and label definition, not the gate, are then the suspects, in that order.
- **Pre-gate:** the standing discipline on the new tree (determinism, ghost/trace equality where a search arm is involved — here neither arm searches, so the pre-gate reduces to determinism + the R16-style control + server-hash and fallbacks verification; the build package states the exact form).
- **Audits:** L1-form leakage check on the distilled arm's divergence decisions (do its departures from v15 correlate with hidden information they cannot legally carry?). The L3 analog — fresh-world scoring of the positions where the distilled policy departs from v15 — is named as the impeachment instrument if the gate converts; whether it is required for the conversion read or follows it is Q6.

## 8. Costs (ranges, pilot-gated)

- **Corpus (Option B):** the pilot prices it. The build package reports the pilot's mean **and** p95 per label job, sizes the corpus from those, and states the wall-clock at the fleet's proven parallelism — no single-point estimates (round-7 lesson, recorded in `fleet-records.md` §3).
- **Training:** T1 is a supervised pass (GPU-hours, small next to any fleet). T2, if run, is priced from round 7's stage-3 actuals (399 versions / 68,436 games ≈ 7.4 h wall on this box).
- **Gate:** both arms at raw speed — the 800-game fleet is **hours**, not the teacher fleet's 37.5. The teacher's cost is paid once, in the corpus, at label granularity; that is the round's economic point.

## 9. Guards carried over, unchanged

Observation masking; the hidden-information canary (coverage form); local Talishar only, never public queues; (C) kernel-attribution containment for any teacher work on the production tree, with the pre-launch G8 sweep (the L-run conditions from the round-7 ruling apply to the corpus run); artifact citations by path + sha256 in every report; builder-run box spot-checks per Joe's standing rule, with the records-commit publication pattern (row + stat files to the repo) so the gate's read is independently recomputable, as round 7's was.

## 10. Open items this design surfaces

1. **The Gravy census diagnostic appears not to have run.** The build package registered it (round-5 census probe, unchanged, 20 plain Gravy bridge games, seeds 8801–8820) to be reported with the stage-3 report; the stage-3 report carries no census tally and no output directory survives on the box. Proposed: run it as a **report-only pre-step** of this round's build (minutes of compute; it tells the registration whether (b)'s store/view pattern on a second hero resembles Fai's ARS concentration). Not blocking for a Fai-lineage run; recorded here so it is not silently lost.
2. **The teacher-root census** remains open by registration "if the teacher path develops further." Distillation is the teacher path developing. Whether this round triggers it is Q7.

## 11. Questions for Claude

- **Q1.** Corpus: Option B primary (teacher labels raw-policy trajectories), Option A supplement — agreed, or A primary?
- **Q2.** D1 (per-arm native featurizers at the gate) and D2 (initialize from v15) — agreed?
- **Q3.** Label weighting: overturns upweighted, uniform over contested, or value-weighted by `mean_diff`?
- **Q4.** T1 form: plain behavior cloning, or cloning with a KL/agreement regularizer toward v15? Any value-head training from the labels' margins?
- **Q5.** T2 (PPO polish) in this round, priced separately, or does the round end at T1's gate?
- **Q6.** Bands as proposed in §7? And is the L3-analog audit required for a conversion read, or does it follow one?
- **Q7.** Does the teacher-root census attach to this round, and does the Gravy census diagnostic run as the §10.1 pre-step?

## 12. What this package is not

No code, no corpus, no training, no launch. On Claude's approval (with answers to §11), the builder returns a build package: the featurizer diff, the corpus generator and trainer configurations, the gate scripts — every file hash-pinned — for Claude's code approval and then Joe's go, in that order.
