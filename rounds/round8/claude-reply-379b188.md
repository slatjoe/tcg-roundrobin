# Claude — on the margin calibration: CLOSE

**Reviewed commit:** 379b188ce925a04c1506026210295f4763ff69ad (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-0140eab.md` hashes to `0857782f…af14`, the value I gave Joe.
**Package:** `rounds/round8/margin-calibration.md`, `code/calibrate_margin.py`, the `label_reduce.py` margin pin, and `fixtures/calibration_fixture.txt`.

**Read: CLOSE stands.** The calibration was run as registered. No margin reaches the H1 bar, so the verification on H2 correctly wasn't invoked. **The distillation line closes on the registered finding (option 3).** Round 8 closes once the publication commit is in and my recomputation agrees (§3).

## 1. The calibration, as registered

- **The construction is right.** It recomputes each run's decision at margin m from the stored paired statistics (`paired_n`, `mean_diff`, `se_diff` of best against prior). Best is the argmax of the means whatever m is, so raising m only tightens the overturn test, and nothing else in the rule moves. **The fixture shows it:** at m = 1.5 it reproduces the shipped decision on all 1,091 label rows, plus the check's own reads: 66 A-overturns, V1-ov 29/66, V1-conf 442/478.
- **The split:** 544 states, 20 games, seed 20261025, by game. H1 is 10 games and 284 states; H2 is 10 games and 260 states.
- **H1 selection** (bar ≥ 0.60): m = 1.5 → 16/36 (0.444), 2.0 → 9/23 (0.391), 2.5 → 7/13 (0.538), 3.0 → 4/7 (0.571). **No qualifier.**

## 2. What it shows

**Tightening the margin trades population for precision, and the two curves don't meet the registered terms:**

| m | A overturns | V1-ov | Advantage of the overturned pick in the other run |
|---|---|---|---|
| 1.5 | 66 | 0.439 | +0.153 |
| 2.0 | 36 | 0.389 | +0.212 |
| 2.5 | 21 | 0.571 | +0.294 |
| 3.0 | 11 | 0.545 | +0.425 |

(Full set, report-only.)

**The overturns that survive a stricter margin are genuinely better moves:** the other run's advantage rises steadily, from +0.15 to +0.43. But reproducibility only plateaus at about 0.55, and the population falls six-fold. At m = 3.0, 11 overturns in 545 states, about 2%, would leave a 10,000-label corpus with roughly 200 overturn examples, and even those reproduce only about half the time. There's no margin at which an argmax student would get a learnable, reproducible signal of useful size.

## 3. Still owed, to close round 8

- **The publication commit:** under `rounds/round8/data/wcheck/`, both runs' labels and thin rows, the job files, and the raw rows gzipped, with hashes. I'll recompute V1-ov 29/66, V1-conf 442/478, and **the whole calibration table** (both halves and the full set) from the published files, independently of `calibrate_margin.py`. If anything disagrees, the reading reopens.
- **The canary explanation:** the 600 `canary_hook_failed` worlds in run A (6 whole batches) and the 300 `det_persist_failed` in B. Name the states, and show from the label path's code that these are determinization refusals that exclude worlds, not canary detections of a hidden-information read. With the line closed this no longer gates a corpus, but it's an integrity question about the label machinery and needs answering.
- **The margin pin** in `label_reduce.py` is accepted as built (fixture-proven, negative tests aborting). It's moot for round 8. **The sign-test fix** and the runner guards lapse with the line, unless a later round reuses those scripts. If one does, they become preconditions there.

## Round 8: the record of result (pending §3)

- **The question:** can the Fai teacher's paired edge (+0.25 over v15) be distilled into a raw policy that plays at raw speed?
- **The answer: not by imitating the teacher's decisions.**
  - The offline labeler is the teacher's procedure (V2 ≈ V1, the mechanism check is N(0,1)-like, no deadline effects).
  - But the teacher's overturns are mostly irreproducible: **17% at k = 25, 44% at W = 100** (at about 10× the label cost), and at most about 55% under a stricter margin, by which point the overturns have dwindled to about 2% of states.
  - The signal is real: fresh worlds favor the overturned move 71 to 13 on live overturns, and the advantage survives selection at every margin. **But it lives in small, noisy advantages that a thresholded label can't carry to a deterministic student.**
- **Never measured:** a distilled policy's actual play. No corpus, training or gate ran, by registered decision, before any gate data existed.
- **For any future attempt:** the evidence points to **value-based targets** (training on the candidates' estimated advantages rather than on thresholded picks), or to stochastic serving. Either would be a new design and registration, not an amendment to this one.
- **Also from this round:**
  - the (b) featurizer pattern (ARS-concentrated, view > store) is replicated on Gravy
  - capture is proven action-identical to raw v15
  - the label machinery is validated against the live teacher
  - interim figures were caught twice by the primary-file discipline

**Scope:** this reply accepts the calibration and the CLOSE, and states round 8's result, pending the §3 publication and my recomputation. No launch is approved or pending.
