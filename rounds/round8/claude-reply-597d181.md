# Claude — ruling on the round-8 pilot

**Reviewed commit:** 597d181f72b830398889a92af7c9c34126824156 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-8f834d2.md` hashes to `b3ab7925…9de1d450db`, the value I gave Joe.
**Package:** `pilot-report-final.md`, `report-fix.md`, `registry-normalization-record.md`, and the inputs under `rounds/round8/data/pilot/`. `MANIFEST.sha256` verifies, with every file OK.

**Ruling:**
- **The pilot PASSES as a validity test.** The offline labeler is consistent with the gated teacher (§1).
- **But the pilot's most important finding is about the labels, not the labeler.** At k = 25 the teacher's overturns are **about 80% irreproducible**, and a student trained on them, then played by argmax, will rarely depart from v15 (§2).
- **I recommend amending the label width before the corpus,** and I set out the alternative. **The choice is Joe's** (§3).

## 1. The reads, recomputed from the published inputs

| Read | Report | Recomputed here |
|---|---|---|
| V1-ov: P(B same overturn \| A overturned) | 5/30 = 0.167 [0.073, 0.336] | **5/30**, same interval |
| V1-conf | 501/517 = 0.969 | **501/517** |
| V2: P(labeler = live pick \| live overturned), thin | 22/100 = 0.220 [0.150, 0.311], thin 0 | **22/100**, same interval, thin 0 |
| V2 against V1-ov | p = 0.528 | consistent |
| Label time per job: mean / p95 / max | 4.3 / 8.6 / 52.6 s | **4.32 / 8.63 / 52.63 s** (n = 1,194) |

**On V1/V2, as registered:** V2 (0.22) and V1-ov (0.17) are statistically indistinguishable, which is what identity predicts. Two independent checks support the read:
- the **mechanism z-check**: mean −0.01, sd 0.86, 3 of 96 beyond 2, which is N(0,1)-like
- **direction**: on the 100 live overturns, the labeler's fresh means favor the live pick over the prior in **71 cases against 13** (16 ties)

**The labeler is the gated teacher's procedure.** The registered deadline difference is moot, with 0 batches past 180 s and 0 killed. The teacher-root census found 0 disagreements in 647 featurizations, which is consistent with post-sync roots, with the registered caveat. **The registry normalization record** is complete: 20 ids, the old object values, the string tags, the hashes and the vault copies. Accepted.

## 2. The finding that matters: the labels are mostly noise at the threshold

**When run A overturns, run B, with fresh worlds on the same state, makes the same overturn only 17% of the time.** The signal underneath is real, though:
- on A's overturns, B's means still favor A's pick by **+0.112** on average, with 18 of 30 positive
- on live overturns, fresh means favor the live pick by **+0.184**, against the live measured **+0.426**

That's a winner's curse. The overturned move is usually genuinely better, by about 40% of what the selecting run measured. But the 1.5 × SE test at 25 worlds has so little power that whether it fires at a given state is close to a coin flip weighted about 1 in 5.

**What that does to distillation as designed.** A cross-entropy target on a single k = 25 label teaches the student the teacher's *firing probability*. At a state where the better move fires about 20% of the time, the student learns about 0.2 for it and **plays the prior by argmax**. Add the KL anchor, and the predictable outcome is a student close to v15: a small divergence rate and Δ ≈ 0. The live teacher earned +0.25 from its *realized* draws, about 1 in 5 per state, on every state it visited. A deterministic student can't reproduce that by imitating single draws.

This was knowable only from the pilot. My Q3 answer (uniform cross-entropy on the teacher's pick) assumed labels reproducible enough to imitate. **They aren't, at k = 25.**

## 3. The decision (Joe's): two options

**Option 1, recommended: widen the labeler before the corpus.**
- Register **W = 100 worlds per candidate**, with the decision rule otherwise unchanged (the same candidate set, pair va, the 20-world floor, and 1.5 × SE). At 4× the worlds the SE halves, the test's power on the measured advantage rises sharply, and the labels become reproducible.
- **Cost,** from the pilot's own timings: about 17 s per job, so 10,000 labels is about **48 box-hours serial, roughly 12 h on the 4 label trees.** It's still the teacher's cost paid once, at label granularity.
- **Before the corpus, a V1 check at W = 100:** relabel the pilot's 547 capture states twice at W = 100, about 1.3 h on 4 trees with no games. **Register the threshold now: V1-ov ≥ 0.50.** If it's met, the corpus runs at W = 100. If not, it's reported and stopped for decision. (V2 isn't repeated. It established that the machinery is the teacher's, and W is a parameter of that machinery.)
- **What changes in the claim:** the student distills a **wider-search version of the gated teacher**, not the k = 25 teacher itself. The gate, bands and arms are unchanged. The +0.2525 stays as the historical reference, not a ceiling. Keep the impeachment bound at +0.25 as a sanity check. A distilled raw policy beating the k = 25 teacher's edge would still need auditing before it's read.
- **Implementation:** a `W` parameter in `distill_label_main.php` (pinned, aborting on anything else, as it does now for 25) and `label_reduce.py` reading W from the rows. That comes back as a small code commit for confirmation.

**Option 2: run the registered design unchanged.** The corpus is about 3 h on 4 trees, then T1 and the gate. It's a valid test of exactly what was registered, and cheap. **But the pilot predicts its result,** a near-v15 student and a likely DOES NOT CONVERT. If that's what comes back, widening the labels afterward would be an amendment made after seeing gate data, which is weaker method than making it now on label-validity evidence alone.

**I recommend Option 1.** The evidence for it comes from the labeler's own reproducibility, not from any gate outcome. It's the cleanest point in the round to change course.

## 4. On the record: a second set of invented interim figures

The report flags an interim notice, delivered mid-run, that carried figures that never existed: V2 "0.9200 flagged", a census of "1647/4", and a 14:28 completion time. The operator voided it against the primary files, and the builder re-verified every headline from the box. **The figures I recomputed from the published inputs match the final report, not the interim notice.** The discipline held: primary files over interim accounts, and publication for independent recomputation.

This is the second occurrence (the first was round 7's extended probe). A fabricated "V2 0.92 flagged" could have driven a wrong decision if anyone had acted on it. **From here on, interim notices carry status and artifact paths only, never figures.** Figures appear only in committed reports built from primary files.

## 5. Still owed

- **The option-(a) one-capture-per-seed declaration**, in the corpus launch manifest. The pilot capture of seeds 10001–10020 is kept. Under Option 1, its run-A labels at W = 25 are **superseded**, and those states are relabeled at W = 100 along with the rest of the corpus.
- **The sign-test fix**, before the gate.
- **The resume guard** against an `$OUT` that already holds `equiv_*` files (be2fae4 §2).

**Scope:** this reply rules the pilot a pass as a labeler-validity test, records its label-reproducibility finding, and puts the W decision to Joe with a recommendation. **It approves no corpus run.** Under Option 1, the W = 100 code commit and its V1 check come first. Under Option 2, the corpus launches on Joe's go with the §5 items in place.
