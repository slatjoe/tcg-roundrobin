# Round 10 — Step 0 probe: FINAL REPORT (2026-10-29)

**Question (registered):** of the two candidate teacher improvements — margin 1.5 → 1.25, or the uncontested threshold 0.97 lowered so currently-unsearched states get searched — which, if either, is buildable, judged by predicted per-game gain whose game-clustered one-sided 95% lower bound exceeds 0, on the **cap-aligned** scoring (§14)?

**Answer: the threshold lever is buildable; the margin lever is not. The registered recommendation is the threshold build.** The hold rule does not fire. Detail below; the interpretation addendum (§5) bounds what the headline gain number means, and binds how any Step 1 package may be sized.

## 1. How the read was produced

Capture: 90 raw-v10 games, Gravy mirror vs the heuristic, seeds 24001–24090, instrument 87/62; 5,253 snapshots (2,167 contested, 3,086 uncontested sampled EVERY=2, Horvitz–Thompson weight 2); full k=25 offline eval of every snapshot; 646 jobs labeled at W=50/CRN in the run's first pass. Attempt 3 (2026-10-28) aborted in analyze on the `Infinity` serialization defect (§6); the **recovery** (2026-10-29, once, approved d17a4540, launched 3ef1815a) re-ran the read path with the §14 cap-aligned scoring registered as primary: eval completeness CLEAN (missing 0), the in-run rescoring reproduced the published reclassification byte-for-byte, the 10 dropped jobs were labeled under supplementary seed family A (970,055,001) and the 69 cap-aligned newly-qualifying jobs under family B (470,055,001), and the merged label set is 71,500 rows over 715 jobs. The recovery then crashed at the influence step (`NameError`, §6); the **completion** (once, confirmed fdfe37af, Joe's standing go) computed the influence prints and the recovery manifest offline from the published outputs. Run record: `step0-probe-recovery-run.md`; outputs: `data/step0/` (attempt 3), `data/step0_capalign/` (the reclassification), `data/step0_recovery/` (the recovery + completion).

## 2. The registered read (cap-aligned primary)

From `data/step0_recovery/probe_report.txt` (the run's own report):

- **Margin 1.25** (class contested_band, 94 jobs): labeled edge +0.0072 [−0.0063, +0.0205]; predicted per-game gain **+0.0076, lower bound −0.0067** → **NOT buildable**.
- **Threshold 0.97** (class uncontested, 305 jobs): labeled edge over the full class **+0.0698 [+0.0342, +0.1136]**; predicted per-game gain **+0.4734, lower bound +0.2080** → **BUILDABLE**.
- Tail structure: uncontested tail edge (eval z > 3.5) **+0.4838 [+0.3260, +0.6050]** over 21 jobs; tail rate per state by prior band — [0.85, 0.97): 0.0092 (4/437); [0.97, 1.01): 0.0068 (21/3,086). Diagnostic class (1.0, 1.5], never in the decision: edge +0.0172 [+0.0035, +0.0323] over 230 jobs.
- **Calibration:** probe contested would-fire rate @1.5 = 0.0549/state (119/2,167; 1.3222/game) — inside the registered flag band [0.04, 0.13] against the Stage 1 panel (0.0917) and live rates (0.069 / 0.065); **no flag** — the offline eval reproduces the search's firing behavior.
- Registered cost prints: threshold teacher game ≈ 1,840 s (3.66× the current teacher; +1,337 s/game of added search at 19.5 s/search over 68.58 uncontested decisions/game); margin adds no searches (503 s/game). The Step 2 outlook prints (power 0.142 margin / 1.000 threshold) are the registered formula's output; §5 rules the threshold's 1.000 not credible as a sizing input.
- **RECOMMENDATION (registered rule), as printed by the run:** "threshold 0.97 — only the threshold's gain lower bound exceeds 0."

## 3. As-run co-report (labeled; not the decision basis)

Same eval and label rows under the pre-alignment scoring: margin per-game gain +0.0062 (lower bound −0.0089), threshold +0.5418 (lower bound +0.2231); the as-run recommendation under the rule is also threshold 0.97. The two scorings agree on the recommendation; the cap-aligned read governs.

## 4. Influence prints (verbatim, from the completion)

The registered influence read — state inspection of game 540261752 with the by-61/after-61 split, leave-one-game-out per lever, and the hold-rule determination — produced by the completion step (`data/step0_recovery/probe_influence.txt`, sha256 d0df2c50…):

```
=== ROUND-10 STEP 0 PROBE -- INFLUENCE READ (claude-reply-9dae0e2 sec.2.3) ===

-- (a) state inspection: game 540261752 (10 recovered jobs: 540261752_t64, 540261752_t65, 540261752_t66, 540261752_t67, 540261752_t68, 540261752_t69, 540261752_t70, 540261752_t71, 540261752_t72, 540261752_t73)
  driver row: seat 2, seed 24070, winner 0, draw True, capped True (cap_reason turns), turns 63, p1life 19, p2life 8
  540261752_t64 turn 45: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 22 wins by turn 61 (stand cap-aligned), 3 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t65 turn 47: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 15 wins by turn 61 (stand cap-aligned), 10 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t66 turn 49: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 1 wins by turn 61 (stand cap-aligned), 24 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t67 turn 51: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t68 turn 53: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t69 turn 55: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t70 turn 57: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t71 turn 59: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 24 horizon draws priced -1, 1 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t72 turn 61: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 25 horizon draws priced -1, 0 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)
  540261752_t73 turn 63: prior pick 0 (chum_friendly_first_mate_yellow) vs search pick 9 (prismatic_leyline_yellow); top prior 1.0000
    cand 0: finished 25, unfinished 0, refusal 0, error rows 0 (pick: prior)
    cand 7: finished 25, unfinished 0, refusal 0, error rows 0
    cand 9: finished 25, unfinished 0, refusal 0, error rows 0 (pick: search)
    prior pick's 25 worlds: 24 horizon draws priced -1, 1 outright losses, 0 other; eval cand_diag agrees: yes
    search pick's 25 worlds: 0 wins by turn 61 (stand cap-aligned), 25 wins after turn 61 (post-cap; horizon draws under the aligned rule)

-- (b) leave-one-game-out, per lever (CAP-ALIGNED scoring and classes, sec.14; 86 drop-out jobs excluded)
  margin (class contested_band, weight 1): full gain 0.0076 (lower bound -0.0067); LOGO range [0.0052, 0.0103]; largest single-game share 0.3235 (game 221917095); with 221917095 excluded: gain 0.0052, lower bound -0.0083; weakest exclusion: game 221917095 (lower bound -0.0083)
  threshold (class uncontested, weight 2): full gain 0.4734 (lower bound 0.2080); LOGO range [0.3259, 0.4863]; largest single-game share 0.3192 (game 635852068); with 635852068 excluded: gain 0.3259, lower bound 0.1753; weakest exclusion: game 635852068 (lower bound 0.1753)

-- (c) hold rule (sec.2.3, evaluated on the cap-aligned numbers, sec.14)
  margin: hold rule not triggered -- not buildable (report lower bound -0.0067)
  threshold: hold rule not triggered -- lower bound stays > 0 under every single-game exclusion (weakest 0.1753)
```

**Hold determination:** the hold rule does **not** fire for either lever. For the threshold lever, the weakest single-game exclusion — game 635852068, the largest carrier at 31.92% of the gain — still leaves a lower bound of **+0.1753 > 0** (gain +0.3259 with it excluded). The manifest records `single_game_dependent: []` and `influence_hold_lines: []`. The recommendation therefore stands as the rule produced it, without the "buildable, single-game dependent" qualification.

## 5. Interpretation addendum (labeled; Claude's §3 of claude-reply-416872f, recorded in package §15.6)

The recommendation in §2 is the registered rule's output and stands as such. **But +0.4734 per game is not a prediction of what a threshold teacher would gain in games, and must not be used as one.** It is the probe's estimand taken outside its range of validity (reproduced exactly from the published rows: 305 jobs, cap-aligned diffs, weight 2, over 90 games):

1. It is an additive sum over the **raw policy's trajectory** — about 6.8 weighted fires a game, each valued as if independent. The interval's upper end (0.86) is more than the base win rate leaves room for; per-decision edges do not add into win probability that way.
2. Repeated presentations of one mistake are counted every time they recur: on the raw trajectory an un-fixed stall re-presents turn after turn, while a teacher that fixes it once changes the trajectory and the later repeats never happen. The 305 jobs are **276 distinct** (game, prior card, teacher card) choices; game 635852068 alone carries 18 jobs summing to 6.80, about a third of the whole gain (the LOGO in §4 independently identifies the same game as the largest carrier).
3. Bounding illustrations — **not registered reads**: as registered 0.4734; each distinct choice counted once ≈ 0.27; only the best single fix per game ≈ 0.13. All remain above Stage 3's whole-teacher per-game gain (0.0649): the lever's signal is real; the size is not 0.47.
4. Round 9's per-game gain was a different estimand — fires on the teacher's **own** trajectory, conditioned on its earlier fixes. The Step 2 gate as registered measures exactly that again (capture games played by the threshold teacher); that is the right estimand for the lever's real value.

**Binding consequences for Step 1:** no Step 2 or fleet sizing from +0.47; the printed power 1.000 is not credible input; sizing uses round-9-style live-trajectory numbers or a conservative bound stated as such. Step 2 prices at ≈1,840 s per teacher game — about 205 box-hours for 400 games, roughly 51 hours of wall time. Per Joe's decision (2026-10-29), the Step 1 package is drafted **pilot-first**: a smaller live pilot of the threshold teacher to measure its realized fire rate and on-trajectory gain before the full gate is committed to.

## 6. Disclosures

- **The `Infinity` defect (attempt 3):** 10 jobs in one game carried eval z = +Infinity; Python's bare-token JSON silently dropped them in the labeler's loader (the analyzer's world-count guard was the first component to treat the absence as an error). The 636 surviving jobs' labels stand (§12 analysis: seed-family uniqueness + CRN pairing kept under the compressed bases). The fixed writer emits a 999.0 sentinel + `z_nonfinite` and serializes `allow_nan=False`; the fixed loader aborts loudly. Standing rule (Claude, §14.6 ruling): any jobs file a PHP process reads is written strict at the source.
- **The horizon defect (§14):** as-built rollout worlds overshot the instrument's turn-62 trigger (median end ~93–96, max ~268) because the horizon check ran once per outer iteration over up to 20 finish steps, and a trigger-crossing win stood as decisive. The round-10 engine copies check after each finish step and force a horizon draw on a hit, mirroring the live cap (decisive only at final turns ≤ 61). All probe reads in this report are on the cap-aligned scoring; round 9's conclusions stand under the same alignment (addendum published: Stage 2 L3 +0.0565, Stage 3 L3 +0.0417).
- **Supplementary labels under the fixed engine** (the 79 recovery jobs) vs the 636 under as-built bytes: ruled commensurable (below turn 62 the engines step identically; cap-aligned rescoring of an as-built world gives exactly the fixed engine's classification).
- **Capture rows `unpinned` by design:** the capture arm never invokes the search; stat rows carry no tuple pin because there is nothing to pin (`settings_probe.json`'s `capture.teacher_tuple` is descriptive of the build). Eval and label rows carry their delivered pins.
- **The influence crash:** the recovery's influence step died on an uninitialized accumulator (`logo_by_lever`) that no fixture had ever exercised through `main()`; the completion ran the repaired file (one initialization line; AST audit found no siblings) under argument parity with the registered invocation, verified by fixture. The recovery script on record is byte-identical to the script that executed (sha256 e9eea58c…).

## 7. What this closes and what it opens

Step 0 is complete: both levers are priced on the registered rule, the recommendation is final (threshold 0.97; hold not triggered), and the margin lever is closed as not buildable at this registration. What opens, on review of this report: the **Step 1 package for the threshold build, drafted pilot-first** under §5's sizing terms — the build itself (the 0.97 threshold change on the §14-fixed engine), a live pilot measuring realized fire rate and on-trajectory gain, and only then the Step 2 L3 gate sized from the pilot's numbers.
