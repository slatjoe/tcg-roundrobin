# Claude — code review of the round-10 Step 0 probe package

**Reviewed commit:** 402c92ff136f456cf1c05df91faa60eed28364e7 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-9b04ad1.md` hashes to `faf6aa44…276414b2`, the value I gave Joe. The nine reused files are byte-identical to their round-9 originals: `s1_eval_main` `73ed2482…`, `s2_label_main` `c7a76af4…`, `search_s2` `85490e8e…`, the driver, merge, report, `analyze_l3`, `g8_sweep2` and `shm_sweep`.

**Verdict: CHANGES REQUESTED.** There's one blocking defect: **the threshold lever's predicted gain is undercounted by the sampling factor** (§2.1). There's also one small required print (§2.2). F2–F7 are ruled in §3. The design is right: one hook, an offline eval of every snapshot, and a decision rule that's allowed to say no.

## 1. Checks

**Deliverable A** reproduces my §1–§3 tables, and the two flags are fair:
- **F3:** my band table joined jobs to statistics by first key match. The snap pairing is the pairing of record. The (2.5, 3.5] edges read +0.062 for Stage 2 and +0.072 for Stage 3 under it, and no conclusion moves. Future tables pair by snap.
- **F4:** my CIs came from my own resampler (B = 3,000, Python `random` seed 3), not the round-9 helper. That explains the 0.003 miss. Recorded.

**The hook.**
- `search_s3_diff.txt` is a single insertion in the uncontested branch.
- It's **inert unless both `TEACHER_CAPTURE` and `TEACHER_CAPTURE_UNCONTESTED` are set**, and it leaves the stat row, the return and the played pick stock.
- It shares the snap counter, so names stay unique, and writes the contested arm's index shape.
- `gen_search_s3.py --check` regenerates it byte-identically.

**The eval and the labels.**
- One eval at k = 25 serves all three margins, since z doesn't depend on the margin.
- Labels use fresh seeds from a disjoint family, so the would-fire selection's winner's curse doesn't enter the labeled edge.

**Seeds:** the capture block 24001–24090 and the label and eval bases are proven by enumeration in `fx_seed_clearance.py`.

**Fixtures, run here** on a scratch copy: **45 checks, ALL PASS**, with the PASS lines identical to `fx_r10_outputs.txt`.

## 2. Blocking

### 2.1 Uncontested gain must be weighted by the sampling factor

The hook snapshots **every 2nd** eligible uncontested decision. But `probe_label_analyze.per_game_gain()` sums each capture game's labeled diffs at weight 1 over the sampled states. So the uncontested per-game gain, its CI and the threshold's "lower bound" in `probe_report.py` estimate **half** the lever's gain at EVERY = 2.

The report already multiplies the *cost* side by `uncontested_every` (lines 139–142). The gain side has to match. As written, the decision rule compares a full-population margin gain against a half-population threshold gain.

**Required:**
- Weight each uncontested job's diff by `capture.uncontested_every` (Horvitz–Thompson; systematic sampling is unbiased for sums) inside the per-game sum, so the bootstrap runs over the weighted per-game totals. Contested-band jobs are unsampled and keep weight 1.
- Print the weight on the CLASS line.
- **Fixture:** a writer→reader round trip at EVERY = 2. The per-game uncontested gain must equal 2× the unweighted sum, with the CI scaled accordingly, and a contested-band population must be unchanged. Plant it in the hook's real index shape.

### 2.2 Print an offline-eval calibration line before the recommendation

The probe trusts offline k = 25 evals to stand in for live search. Print, before the recommendation:
- the probe's **contested** would-fire rate at 1.5, per contested state and per game;
- beside it, Stage 1's panel (22/240 = 0.092 per state, also on raw-policy capture states) and the live rates (0.069 for Stage 2, 0.065 for Stage 3 per state).

If the per-state rate falls outside [0.04, 0.13], the report says "offline eval does not reproduce the search's firing behavior" above the recommendation. That's a print and a flag, not a gate. It's the check that the instrument measuring the uncontested population is behaving on the population we already know.

## 3. Rulings on the flags

- **F1 (λ = 0, C2 out):** recorded.
- **F2, the class (a) margin: 1.5, as proposed.** A threshold build changes one thing, the threshold, at the current margin, so its gain is the z > 1.5 class.
  - **Also label the uncontested superset at z > 1.0.** It's a few dozen jobs at most, about 90 s each.
  - Report the (1.0, 1.5] uncontested jobs as a **diagnostic only**, excluded from the threshold gain.
  - With that, the jobs phase needs no ruling before labels: it prints the counts and proceeds.
- **F3, F4:** as in §1.
- **F5 (round-8 families vs Stage 3, value-disjoint):** noted for the record. No action.
- **F6, the size: registered as proposed.**
  - 90 capture games, EVERY = 2 (about 3,100 uncontested and 2,140 contested states).
  - **No k = 10 screen.** The bias argument is right: the screen's loss sits exactly on the headline estimand.
  - Label base 70,055,001 + shard × 10⁸ with the 256-job shard cap, eval base 30,055,001.
  - **The extension rule as written:** fewer than 5 class-(a) jobs means the edge read is uninformative, and the review may order a 10-game block before labels.
- **F7, the hook:** accepted. It's capture-only machinery. Any threshold *build* in Step 1 is a separate change with its own diff, pre-gate and review.
- **The decision rule: registered as written.** Buildable iff the gain's lower bound > 0. Prefer the higher lower bound, and on overlapping CIs prefer the cheaper lever (the margin). NO BUILD is an allowed outcome.
  - **Add one informational print per lever:** the **predicted Step 2 power** against my registered two-sample bar, using its predicted gain and an SE scaled from Stage 3's 0.0090; and the **Step 2 and fleet price** at its per-game cost (503 s against about 1,846 s).
  - At 90 games the gain CIs will be wide, so Joe should see what a "buildable" lever would cost to confirm before he says go.

## 4. Cost

About 43 box-hours, roughly 11–12 h of wall time. That's accepted against what it decides.

**Scope:** §2.1 (weighting and its fixture) and §2.2 (the calibration print), with the §3 additions (the z > 1.0 superset labels and the per-lever power and price prints), come back in one commit for a confirmation check. The probe then runs on Joe's go with launched sha == approved sha. No run is approved yet.
