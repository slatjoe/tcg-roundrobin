# Round-3 pre-gate launch — results summary

**Launch:** `run_r3.sh` at approved repo sha
107ea5d35b86e80f384e5ef41a098681dc64ef30, authorized by Joe Slattery
in-chat 2026-10-18 ~22:05 EDT, started on the sim box ~22:08 EDT.
**Completion verified from primary records:** `/tmp/r3_launch.log`
contains `R3-LAUNCH-DONE`; all six driver row files have 19 rows
(seeds 1–18, 20; seed 19 excluded by design).

## Overall verdict: PRE-GATE DOES NOT PASS

- Two pairings are **FAIL-localized** on the classifier
  (raw vs ghost seat 2; ghost vs capture seat 1).
- All four pairings also carry **more than 2 canary-invalid seeds**,
  which under the registered reads makes a pairing **inconclusive**
  (>2 invalid seeds). The seat-1 classifier passes therefore do not
  count as pre-gate passes.
- No pairing is FAIL-outcome (no seed was IDENTICAL with unequal
  outcome fields), and there are no INVALID_MODE, MISSING_ROW,
  DUP_SEQ, `shadow_fallback_decide`, connect-failure, or timeout
  seeds (details below).

## Per-pairing verdicts (registered reads)

Classifier PASS per seed requires: classifier IDENTICAL,
within_row_hits = 0, outcome fields equal (winner, turns, decisions,
p1life, p2life, gamestate_norm_sha), modes ok, zero connect failures.

### (a) raw vs ghost, seat 1 — `pair-raw-ghost-s1.md`

- Classifier/outcome: **19/19 PASS** (all IDENTICAL, 0 within-row
  hits, outcome equal, modes ok).
- INVALID overlay: **8 canary-invalid seeds** — 1, 5, 7, 13, 15, 16,
  17, 20 (11 `fallback: "canary"` rows in the ghost arm's
  search_stats, mapped game → seed).
- **Verdict: INCONCLUSIVE** (classifier pass, >2 invalid seeds).

### (b) raw vs ghost, seat 2 — `pair-raw-ghost-s2.md`

- Classifier/outcome: **0/19 PASS — FAIL-localized on all 19 seeds**,
  every verdict DECISION, outcome equal = False on all 19.
- INVALID overlay: **7 canary-invalid seeds** — 1, 2, 6, 8, 12, 16,
  17 (16 canary rows in the ghost seat-2 search_stats).
- **Verdict: FAIL-localized** (and independently inconclusive by
  the invalid-seed rule).
- Localized divergences (class DECISION, rule `ghost_prior` in
  every case; a_chosen = 0 in every case):

  | seed | seq | branch | | seed | seq | branch |
  |---|---|---|---|---|---|---|
  | 1 | 77 | M | | 11 | 108 | B |
  | 2 | 208 | M | | 12 | 332 | M |
  | 3 | 241 | B | | 13 | 280 | B |
  | 4 | 147 | M | | 14 | 296 | B |
  | 5 | 190 | M | | 15 | 77 | M |
  | 6 | 141 | M | | 16 | 253 | M |
  | 7 | 97 | B | | 17 | 59 | B |
  | 8 | 11 | A | | 18 | 193 | B |
  | 9 | 4 | M | | 20 | 4 | M |
  | 10 | 203 | M | | | | |

- Within-row hit (in addition to the DECISION at seq 97):
  seed 7, seq 167, side B (ghost), branch ARS, pair `feat`,
  rule `ghost_prior`.

### (c) raw vs shadow, seat 1 — `pair-raw-shadow-s1.md`

- Classifier/outcome: **19/19 PASS** (all IDENTICAL, 0 within-row
  hits, outcome equal, modes ok).
- INVALID overlay: **8 canary-invalid seeds** — 1, 5, 7, 13, 15, 16,
  17, 20 (11 canary rows in the shadow arm's search_stats; same seed
  set as ghost seat 1).
- **Verdict: INCONCLUSIVE** (classifier pass, >2 invalid seeds).

### (d) ghost vs capture, seat 1 (ghost is the base) — `pair-ghost-capture-s1.md`

- Classifier/outcome: **4/19 IDENTICAL** (seeds 7, 13, 18, 20) and
  **15/19 FAIL-localized** (DECISION, outcome equal = False).
- INVALID overlay: **13 distinct canary-invalid seeds** —
  1, 3, 4, 5, 7, 8, 9, 12, 13, 15, 16, 17, 20 (ghost arm: 11 rows /
  seeds 1, 5, 7, 13, 15, 16, 17, 20; capture arm: 29 rows / seeds
  1, 3, 4, 5, 7, 8, 9, 12, 13, 15, 17, 20). After the overlay, only
  seed 18 remains a clean PASS in this pairing.
- **Verdict: FAIL-localized** (and independently inconclusive by
  the invalid-seed rule).
- Localized divergences (class DECISION, rule `teacher` in
  every case):

  | seed | seq | branch | | seed | seq | branch |
  |---|---|---|---|---|---|---|
  | 1 | 272 | B | | 10 | 292 | B |
  | 2 | 302 | B | | 11 | 3 | ARS |
  | 3 | 410 | M | | 12 | 77 | M |
  | 4 | 24 | M | | 14 | 270 | B |
  | 5 | 404 | B | | 15 | 283 | P |
  | 6 | 265 | B | | 16 | 244 | M |
  | 8 | 178 | M | | 17 | 91 | M |
  | 9 | 412 | B | | | | |

- Within-row hit (in addition to the DECISION at seq 3):
  seed 11, seq 455, side B (capture), branch ARS, pair `feat`,
  rule `teacher`.

## Other registered checks

- Modes: ok on every seed in every pairing (r3_pair `modes ok` =
  True throughout); zero INVALID_MODE seeds.
- Connect failures: 0 in all six driver row files
  (`connect_failed` sum = 0 per file).
- `shadow_fallback_decide` trace rows: **0** in all six arms
  (trace-row rule census per arm logdir on the box).
- MISSING_ROW / DUP_SEQ: none — every classifier verdict was
  IDENTICAL or DECISION.
- Timeouts / caps / stuck: none found — no timeout lines in the
  launch log or arm logdirs; `capped` = 0 and `stuck` = 0 in all
  six driver row files.
- Canary source: `search_stats.jsonl` in each arm logdir on the
  box (`/tmp/r3_<arm>_log/search_stats.jsonl`, not part of this
  package per the package list); counts above are
  `fallback: "canary"` rows mapped to seeds via the driver rows'
  gamename. Per-arm totals: ghost s1 11 rows / 8 games, ghost s2
  16 / 7, shadow s1 11 / 8, capture s1 29 / 12.

## Server log

- `/tmp/probe_server.log` (search server, pid recorded in
  `launch-manifest.json`): **server-log fallback count = 0.**
  All 2,164 lines in the log report `fallbacks=0` (final counter
  also `fallbacks=0`), and the log contains zero error / exception
  / traceback lines — so the count is 0 for the run window under
  any slicing of that log.

## Box state after the run

- `ipcs -m | wc -l` after completion: **2774**
  (launch-manifest recorded 2360 before the run).

## Files in this package

Four pairing tables (`pair-*.md`), the six driver row files
(`r3_*.jsonl`, 19 rows each), the six arm manifests
(`r3_*.jsonl.manifest.json`), `launch-manifest.json`, and this
summary. Local copies were sha256-verified against the box
originals before commit.
