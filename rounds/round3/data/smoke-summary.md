# Round-3 instrumentation smoke — seed 3, tracetree, arms raw/ghost/shadow

Build test only; the 19-seed reads in the package bind the approved
launch, not this. Rows: `smoke-rows.jsonl` (driver output; the
ghost/shadow rows' `mode_line` predates the mode-line fix in this
commit's driver — it captured the base block's line; the arms' true
modes are proven by their 80 search-stat rows and teacher trace rows).

## Results (primary records on the box, read directly)

- All three games: **winner 1, 16 turns, 0 connect failures.**
- Raw arm manifest: `search_stats_rows: 0`, `assert_no_search_rows: true`.
- Ghost and shadow gamelogs **byte-identical** (sha 127e35fd7ff3ac31,
  20,528,568 bytes each). Raw gamelog differs (8c029b506a95864f,
  18,377,142 bytes).
- Trace alignment (653 rows in each arm, seq-aligned 1:1): **no field
  divergence across all 653 shared rows** — state hash, candidate
  hash, chosen index, and RNG fingerprint identical between raw and
  ghost at every decision (field-wise comparison script in
  `code/smoke_analyze.py`, comparator inline for the all-rows check).
- Root decisions (80 in the ghost trace): state diffs **0** (raw
  state_hash == ghost feat_pre_hash at every root decision);
  checkpoint feature mutations **0** (feat_pre == feat_post at all
  80); pre/post argmax flips **0**; first pick divergence **none**.
- Shadow: 80/80 root rows ruled `shadow_bridge`; shadow picks ==
  ghost picks at all 80.

## The open fact (no theory attached)

The raw and ghost gamelogs are NOT byte-identical although every
traced decision, state, and fingerprint matches, and winner/turns
agree. The logs are ~18-20 MB for a 16-turn game; the ghost's carries
~11% more lines, with extra priority-pass chatter visible in diffs.
Per Claude's round-2 doctrine the gamelog is output, not cause; the
package asks for a ruling on the pass criterion for the pre-gate test
(trace-level decision equality vs gamelog bytes).

## Classifier note

The classifier's first draft carried a BETWEEN class (arm B zone_pre
vs its own previous zone_post). On this smoke it fired at seq 37 —
spuriously: between root decisions the engine legitimately advances
the game through untraced steps, so cross-row zone continuity is not
expected. BETWEEN was removed before this package shipped; the
checkpoint question is answered inside each teacher row by
feat_pre vs feat_post. Fixtures now 6/6 (IDENTICAL, STATE,
CANDIDATES, DECISION, RNG, MISSING_ROW).
