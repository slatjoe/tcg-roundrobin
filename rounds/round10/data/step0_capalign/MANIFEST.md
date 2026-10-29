# data/step0_capalign — the §14 cap-aligned eval rescoring

Computed 2026-10-29 by `code/capalign_eval.py` from the
PUBLISHED attempt-3 files in `data/step0/` only (the
fixture rule: fixtures and rescoring read only what's
published in the repo). Inputs: `eval_jobs.jsonl`,
`evals_all.jsonl.gz` (381,625 world rows),
`eval_states.jsonl`, `eval_summary.json`,
`jobs_all.jsonl`, `code/settings_probe.json`.

The registered cap-aligned rule (§14;
claude-reply-28c2065 §3.2): a finished world is
DECISIVE only if it ended by turn 61 — the live
instrument's cap trigger is currentTurn 62, and
play_game.php scores the game a draw the moment
currentTurn reaches 62. Every other finished world
prices as a horizon draw (−1 in the eval's paired
statistic). The statistic is probe_eval_analyze.py's,
mirrored; before any cap-aligned number was emitted,
the as-run recomputation reproduced every published
eval state (status, search pick, paired count, z) and
the attempt-3 job set (snaps and classes) exactly —
the script aborts on any mismatch.

Headline results (full detail in
capalign_reclassification.txt):

- would-fire @1.5: 448 → 424; @1.25: 697 → 673;
  @1.0: 799 → 780.
- Classes: uncontested 329 → 305, uncontested_diag
  235 → 230, contested_band 82 → 94.
- 86 attempt-3 label jobs DROP OUT (their states no
  longer qualify cap-aligned) — excluded from the
  cap-aligned read and listed in the recovery
  manifest. Of game 540261752's ten jobs: t64
  (cap-aligned z 13.27) and t65 (z 6.0) stay
  uncontested; t66 falls to z = 1.0; t67–t73 lose
  their contrast entirely (all their search-pick
  wins were recorded after turn 61).
- 69 states NEWLY QUALIFY (8 uncontested, 32
  uncontested_diag, 29 contested_band) and need
  supplementary labeling — supplementary_jobs.jsonl,
  built exactly as build_probe_jobs builds jobs,
  labeled by the recovery under the fresh seed
  family based at 470,055,001.
- 39 attempt-3 jobs keep a class but change it
  (regrouped by the cap-aligned read).

All files are strict JSON (no bare Infinity/NaN
tokens; a non-finite z is the 999.0 sentinel with a
z_nonfinite flag — the fix-pass-4 discipline).

| file | bytes | sha256 | rows |
|---|---|---|---|
| capalign_states.jsonl | 3527148 | 47126ff8e924d6d2a1d799d1994957c1bc6357d9e2aa81fd6e5228b9aa0431c7 | 5253 states |
| capalign_summary.json | 4602 | 5f0ee7a41b88af2da86a483eca4f43bf57ef71e07855e96f60a3a0943a3a4352 | — |
| capalign_classes.json | 132364 | 10b5e0af822c24d7d779ec49e2ab44027171d5017c56a0f6a26c50eda98e8ce9 | 5253 snaps |
| capalign_reclassification.json | 38161 | 109243673413bce7509d9c584878e19ae443543f45dc298e36eb178fc9b92295 | — |
| capalign_reclassification.txt | 21581 | 5dfc8d36ca63f6a69fde2262bbea6fba618f1e2ee635c02a9281b7b7db3b94da | — |
| supplementary_jobs.jsonl | 71011 | 2145529daaf6feb9f493eee7ea6b3ab9538b0e8fccca934cac468895ef321436 | 69 jobs |
| supplementary_jobs_report.json | 618 | 6ad534f57ea46e646cac6f28913a643e93005d5467f12c0735619ffe1d077e63 | — |
