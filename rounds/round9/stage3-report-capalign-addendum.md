# Round 9 — Stage 2 / Stage 3 reports: CAP-ALIGNED CO-REPORT ADDENDUM

**Dated 2026-10-29.** This is a new addendum file. The
original reports (`stage2-report.md`, `stage3-report.md`)
and their read JSONs are untouched, and no verdict in
them changes: Stage 2's PROCEED stands, Stage 3's DOES
NOT CONVERT stands — the fleet verdict was read from the
real games, not from these labels. What follows is the
§14 co-report Claude's reply of 2026-10-29
(`rounds/round10/claude-reply-28c2065.md` §2, §3.3) called
for: the two L3 primaries recomputed under the
cap-aligned rule and printed beside the originals.

## The rule

The horizon worlds in the round-9 label fleets did not
stop at the registered trigger. The rollout loop checked
the horizon once per outer iteration — after up to 20
`PuzzleFinishStep()` calls — so horizon worlds exited at
a median of turn 93 (max 268) instead of at turn 62, and
some worlds were recorded decisive after the trigger.
The live instrument cannot produce either: its cap
trigger is currentTurn 62 and it scores the game a draw
the moment currentTurn reaches 62, so **turn 61 is the
last decisive turn** (play_game.php checks its cap after
each finish step). The cap-aligned rule prices the
recorded rows the way the live game would have:
**a world scores 1.0 only if it won and ended by turn
61; every other finished world scores 0** under the
registered draw = 0 primary. Mechanism evidence and the
engine fix are in the round-10 package doc §14.

## The recomputation

`code/capalign_l3.py`, run on the published
`data/stage2/` and `data/stage3/` label rows, read
construction mirroring `stage3_attr_analyze.run_read`
exactly, bootstrap `analyze_l3.cluster_bootstrap` at
its defaults (10,000 reps, seed 20261020). Full output:
`stage3-capalign-addendum.json` (sha256 3db4987c…).

Verification first: the as-run recomputation reproduces
both published primaries **exactly** — point estimates
and job counts, and the CIs bit-for-bit under the repo's
bootstrap defaults (Stage 2 +0.0621 [0.0440, 0.0809],
353 jobs; Stage 3 +0.0417 [0.0311, 0.0527], 622 jobs).

## Results

| read | as-run (published) | cap-aligned (this addendum) | Claude §2 |
|---|---|---|---|
| Stage 2 L3 primary | +0.0621 [0.0440, 0.0809] | **+0.0565 [0.0400, 0.0739]** | +0.0565 [0.0406, 0.0737] |
| Stage 2 per-game gain | +0.1096 | +0.0997 | — |
| Stage 3 L3 primary | +0.0417 [0.0311, 0.0527] | **+0.0417 [0.0314, 0.0527]** | +0.0417 [0.0320, 0.0527] |
| Stage 3 per-game gain | +0.0649 | +0.0649 | — |

Point estimates agree with Claude's recomputation at
the precision he quoted (Stage 2 cap-aligned mean
0.056506; Stage 3 0.041747 — at full precision the
Stage 3 cap-aligned mean sits 0.00003 *above* its
as-run value: the repricing removed post-cap wins from
both candidates and the two effects nearly cancel).
The CI differences against Claude's figures (at most
0.0006, on one bound of each interval) are bootstrap
draw: his recomputation used his own bootstrap, while
this addendum uses the repo's seeded defaults — the
same defaults that reproduce the published CIs
bit-for-bit, which is the stated basis for preferring
them here. No interval changes sides of 0 under either
draw, and no conclusion moves: **the per-decision edge
is positive and replicated under the aligned rule at
both stages, at roughly nine-tenths (Stage 2) and
full (Stage 3) of its as-run size.**

## The overshoot, on this addendum's counting basis

Basis: every finished world in both candidates of
every job, deduplicated as the analyzers dedupe
(35,296 Stage 2 worlds; 62,192 Stage 3). Decisive
worlds ending after turn 61: Stage 2 591 of 15,800
decisive (3.7%); Stage 3 589 of 26,010 (2.3%).
Horizon-flagged worlds' end turns: median 93, max 268,
both stages — Claude's §2 medians and maxima exactly.
(Claude's §2 counts of decisive worlds ending after
turn 63 — 532 and 676 — were computed on a counting
basis his reply does not state; on this addendum's
basis those counts are 327 and 349. The point
estimates, which are the registered comparison, agree
exactly; the tail counts differ by basis, and this
addendum does not paper over that.)
