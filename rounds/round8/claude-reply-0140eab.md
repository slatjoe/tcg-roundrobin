# Claude — on the W = 100 V1 check (STOP)

**Reviewed commit:** 0140eab25bd4dcc21cd24c842c974bf39f8bd1ca (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-af89615.md` hashes to `5b1ab7e4…2f2f5ceb2`, the value I gave Joe.
**Package:** `rounds/round8/wcheck-report.md`.

**Read: STOP stands.** V1-ov is 29/66 = **0.439** [0.326, 0.559], against the registered **≥ 0.50**, so the corpus does not launch at W = 100 under the registered rule. I don't recommend overriding the bar (§2, option 1). **I recommend option 2:** a stricter overturn margin, calibrated on the double labels already paid for and verified on a held-out half, with no new labels or games. If it fails, **option 3: close the distillation line on this finding.** The choice is Joe's (§3).

## 1. What the check shows

Widening from 25 to 100 worlds roughly **tripled reproducibility** (0.167 → 0.439) and **doubled the overturn rate** (5.5% → 12.1%, 66/545). The second is consistent with the pilot's finding: many states carry a real but small advantage that a more powerful test detects more often. Across the 544 double-labeled states:
- **29 overturns reproduce** (5.3% of states)
- 37 fire in A only, about 39 in B only
- V1-conf is 0.925

So at W = 100 there's now a substantial core of states whose overturn fires reliably, mixed with a fringe of near-threshold coin flips. **The builder's closing note is right:** what has failed at both widths is the *label definition*, the binary 1.5 × SE threshold, not the labeler.

**Also from the report:**
- **Finished worlds:** 2 of 3,195 candidate entries fall short, both whole-batch failures. No deadline kills. Accepted.
- **Error reasons:** 600 `canary_hook_failed` in A and 300 `det_persist_failed` in B, all as whole 100-world batches. Before any corpus run, identify the affected states and confirm these are the known determinization-refusal classes (excluded worlds), **not** canary detections of a hidden-information read. It's cheap to check from the raw rows, and it matters because "canary" is in the name.
- **Cost: 45.8 s/job mean (p95 90.6).** That's **10.6× the W = 25 cost for 4× the worlds**, with 100 concurrent children per candidate. My "about 17 s" in 597d181 was a linear extrapolation and wrong, as was the smoke-based 1.3–1.5 h. At W = 100 the corpus is about **32 h wall at the mean, about 63 h at p95**, on 4 trees.
- **SHM** closed at 0.

## 2. The options

**Option 1: proceed at W = 100 anyway.** There's a real argument for it. A cross-entropy student learns each state's firing frequency q, and argmax deviates where q > 0.5. V1-ov ≈ 0.44 implies a meaningful share of states with high q, and those are the strongest-advantage states, where the gain is. **But it means overriding a threshold registered in advance precisely to make this call.** At 32 to 63 h of box time, I don't recommend spending it against our own bar.

**Option 2 (recommended): calibrate a stricter margin on the data already paid for.** The noise is in the threshold, and the existing two W = 100 runs contain everything needed to see how reproducibility trades against overturn rate as the margin rises. **Register now, before anything is computed:**
- **The grid:** overturn iff paired n ≥ 20 and `mean_diff > m · se_diff`, for m ∈ {1.5, 2.0, 2.5, 3.0}. Everything else in the decision rule is unchanged.
- **The split:** the 544 states divided into halves H1 and H2 by a seeded random split (seed 20261025), **by game**.
- **The selection, on H1 only:** the **smallest m** in the grid with V1-ov(m) ≥ **0.60** on H1. The bar is higher than 0.50 to leave room for selection shrinkage.
- **The verification, on H2 only:** V1-ov(m*) ≥ **0.50**, with its Wilson interval. If it's met, the corpus runs at W = 100 with margin m*. If no m qualifies on H1, or H2 misses, **the line closes** (option 3).
- **Report-only, per m on both halves:** the overturn rate, V1-conf, and the mean advantage of the overturned pick under the *other* run's means (the winner's-curse read), so we can see what stricter labels give up.
- **Cost:** none. It's a recomputation from the existing raw rows, with paired per-world outcomes.
- **What changes in the claim:** the student distills a **more conservative** version of the gated teacher, at W = 100 and margin m*. It overturns only where the evidence is strong, which is the population an argmax student can actually learn. The gate, arms and bands are unchanged.
- **A new label-rule constant:** `label_reduce.py` gains `margin` (pinned, recorded on every label, abort on mismatch), as W did.

**Option 3: close the distillation line.** The finding stands as a round-8 result in its own right: **at the registered decision rule, the teacher's overturn labels are not reproducible enough to distill by argmax imitation at affordable width.** At k = 25, 17% of overturns reproduce; at W = 100, 44%, at about 10× the label cost. That's worth recording either way, and it bears on how any future teacher-to-policy transfer should be built, for example with value-based targets rather than thresholded picks. A design like that would be a new registration, not an amendment.

## 3. What I need either way

- **Publish the W-check data** under `rounds/round8/data/wcheck/`: both runs' labels and thin rows, and the **raw rows gzipped**, since option 2 needs per-world outcomes. Include the job files and hashes. I'll recompute V1-ov 29/66 and V1-conf 442/478, and under option 2 I'll verify the calibration myself from the same files.
- **The canary explanation** from §1, before any corpus.
- **Still owed** for the corpus commit, if one happens: the one-capture-per-seed declaration (with all pilot-state labels at the final rule), the guard in the remaining runners, and the sign-test fix before the gate.

**Scope:** this reply confirms the registered STOP and lays out three options with my recommendation (option 2, falling back to option 3). It approves no corpus run. Under option 2, the calibration is a computation on existing files: its code and the H1/H2 results come back for my review before anything launches. **The decision is Joe's.**
