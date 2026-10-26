# Round 9 — Stage 1 REPORT (calibration: bounds grid on the 240-state panel)

**SELECTION: CALIBRATED SETTING — `H8k-180+H`** (hooks
8,000, deadline 180 s, horizon at turn 62 with outcome −1,
k = 25, margin 1.5 — the tuple pinned in
`code/settings_stage1.json`). Per-state completion
**1.0000** (240/240 states), mean per-decision wall
**26.5486 s** — the cheapest of the five qualifying +H
settings under the registered rule (cheapest mean wall,
ties by p95 then max). All five +H settings qualified; the
control B0 completed 84/240 states (0.3500). Every figure
below was recomputed independently from the raw rows and
agrees with the analyzer exactly (§6). Stage 1 measures
completion and cost; it licenses no edge claim.

## 1. Provenance

- Design `8dddf387`, approved in direction with D1–D6
  settled (`c76f6856`); Stage 0 POSITIVE (`16f02e2e`,
  ruling `8dce0fac`) with the tie value settled for round
  9 (draw = 0 primary; horizon-ended worlds score −1).
- Stage 1 package `edddf5ed` → Claude's code review,
  changes requested (`claude-reply-edddf5e`: completion
  is the **per-state** rate; B0 is the **control**,
  excluded from selection; the runner's B0 stop
  condition) → fix pass `86de3be1` → **CONFIRMED**
  (`claude-reply-86de3be`, committed `6a874c4b`): Stage 1
  may launch on Joe's go at launched sha == `86de3be1`.
- **Launch attempt 1** — 2026-10-26 07:21:43 EDT,
  `PHASE=all` at `86de3be1` (repo HEAD `6a874c4b`,
  rounds-only difference), Joe's go 07:19 EDT. Record:
  `stage1-launch.md` (committed `2bf7639f`, including the
  abort record). Pre-flight restored the registry's live
  path byte-for-byte from the vault snapshot (sha256
  `28b5acfa…`, 6,241 games); capture played the 40 games
  (seeds 21001–21040), the registry merged to **6,281**
  (post-merge sha256 `902682fc…`, `registry_merge_b1.txt`),
  and the panel built: **240 contested states over 31
  games** (`panel_jobs.jsonl` sha256 `64fac6ce…`). The
  runner then **died entering eval**: line 343's stray
  `pid` token left `PIDS` unset and `set -u` aborted the
  shell at the first shard spawn; B0's shard 0 ran
  orphaned and was stopped ~07:27 EDT. No setting
  completed; no measurement was affected.
- **Launch fix** `a13cabc5` — the single token removed
  (reverting it reproduces the launched runner
  byte-for-byte), plus `fx_shard_supervision.sh`, which
  executes the supervision block verbatim and fails on
  the pre-fix text with the launch's exact errors.
  **CONFIRMED** (`claude-reply-a13cabc`) with §2 relaunch
  conditions: reuse the capture and panel (`PHASE=eval`,
  then `PHASE=analyze`; never `PHASE=all`); manifest
  records for the panel hash, the unchanged registry, a
  stray-process listing, the G8 sweep, and the stale-B0
  inventory.
- **Relaunch** — 2026-10-26 07:49:24 EDT, `PHASE=eval`
  at launched sha `a13cabc5` (HEAD `2ffd9638`, rounds-only
  difference), Joe's go 07:46 EDT. Record:
  `stage1-relaunch.md` (committed `9510eb7e`); manifest
  `stage1_relaunch_manifest.json` (sha256 `f462a248…`).
  All §2 records were taken (no stray processes; SHM
  188 → 0; registry unchanged at `902682fc…` / 6,281;
  panel hash equal; the orphan's stale B0 outputs
  inventoried, then truncated by the runner per shard as
  designed). Supervision was watched through the B0 gate:
  all four shards for both players, log error scan 0/0/0,
  **B0 gate PASSED** ~09:20 EDT. Eval completed the same
  day (last setting's files at 12:46 EDT); `PHASE=analyze`
  was run after completion (`stage1_analyze_run.log`).

## 2. Eval outcome — integrity per setting

Every setting evaluated the full panel under its pinned
tuple at the fleet's 4-way contention (eval seed base
885001 + shard × 10⁸). The analyzer's own audits (tuple
audit on every row, world-count guard, stat/world
cross-checks, draw-marker agreement) abort on any failure;
it produced a report, so all passed.

| setting | world rows | stat rows | fallbacks | unfinished worlds (class) |
|---|---:|---:|---:|---|
| B0 (control) | 17,025 | 240 | 0 | 3,566 (abort) |
| B0+H | 17,025 | 240 | 0 | 3 (abort) |
| H8k-180+H | 17,025 | 240 | 0 | 3 (abort) |
| H8k-360+H | 17,025 | 240 | 0 | 3 (abort) |
| H16k-180+H | 17,025 | 240 | 0 | 3 (abort) |
| H16k-360+H | 17,025 | 240 | 0 | 3 (abort) |

17,025 = 681 candidate evaluations × 25 worlds; 681 =
the panel's selected candidates (2–4 per state). B0's
counts equal the registered counts exactly — the
confirmation's §2.3 assertion: the aborted attempt's
orphan rows did not mix in (`evals_B0.jsonl` sha256
`c0be1d29…`, §7 of the MANIFEST). The +H unfinished
worlds are 3 of 17,025 per setting (pooled finished
share 0.999824), all hook-budget aborts; B0, without the
horizon, leaves 3,566 of 17,025 worlds unfinished (pooled
0.790543).

## 3. The selection table

Completion is the **per-state rate** — panel states where
**every** selected candidate reached the validity floor
(≥ 20 of 25 worlds finished) — against the registered
bar 0.95. Candidate-level rate and pooled finished share
are diagnostics only. Walls are per-decision seconds from
the stat rows. Overturn co-reports are over non-thin
states under both registered valuations (draw = 0 is the
primary; 0.5 co-reported), the margin fixed at 1.5 paired
SE. All values below are the independent audit's (§6);
the analyzer's are identical.

| setting | states completing | completion | cand-level (diag) | pooled (diag) | thin-prior | wall mean | wall p95 | wall max | wall total | overturn draw = 0 | overturn 0.5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 (control) | 84/240 | 0.3500 | 0.5609 (382/681) | 0.7905 | 0.4708 (113/240) | 57.6010 | 96.7318 | 149.688 | 13,824.248 | 0.0315 (4/127) | 0.0315 (4/127) |
| B0+H | 240/240 | 1.0000 | 1.0000 (681/681) | 0.9998 | 0.0000 | 26.5662 | 46.8774 | 55.838 | 6,375.881 | 0.0917 (22/240) | 0.1250 (30/240) |
| **H8k-180+H** | 240/240 | **1.0000** | 1.0000 | 0.9998 | 0.0000 | **26.5486** | 46.8204 | 56.382 | 6,371.672 | 0.0917 (22/240) | 0.1250 (30/240) |
| H8k-360+H | 240/240 | 1.0000 | 1.0000 | 0.9998 | 0.0000 | 26.5719 | 46.9121 | 56.272 | 6,377.249 | 0.0917 (22/240) | 0.1250 (30/240) |
| H16k-180+H | 240/240 | 1.0000 | 1.0000 | 0.9998 | 0.0000 | 26.5909 | 47.3717 | 55.424 | 6,381.807 | 0.0917 (22/240) | 0.1250 (30/240) |
| H16k-360+H | 240/240 | 1.0000 | 1.0000 | 0.9998 | 0.0000 | 26.6267 | 46.9219 | 55.703 | 6,390.417 | 0.0917 (22/240) | 0.1250 (30/240) |

**Selection:** all five +H settings qualify (completion
1.0000 ≥ 0.95). Sorted by (mean wall, p95, max), the
first is **H8k-180+H** at mean 26.5486 s — 0.0175 s under
the runner-up B0+H (26.5662 s); no tie-break was needed.
The five qualifiers' mean walls span 26.5486–26.6267 s
(a 0.3% band): on this panel they are indistinguishable
in cost and identical in completion, so the registered
rule — not a measured gap — is what names the winner.
That is the selection the rule produces, recorded as
such.

## 4. B0 — the control read

B0 is the fleet teacher as it ran in round 7 (4,000
hooks, 180 s, no horizon, legacy draw price), read in
full and never selectable:

- **Completion 0.3500** — at the fleet's bounds, 156 of
  240 panel states hold at least one candidate that
  never reaches the floor. This is the round-7 confound,
  measured on a fresh panel.
- **Thin-prior 0.4708** (113/240 states whose prior
  candidate does not complete) beside the fleet's
  **0.3170** — printed as the registered comparability
  check, not an identity (different population:
  raw-trajectory roots vs the fleet teacher's own
  trajectory).
- **Cost:** mean wall 57.6010 s per decision — 2.17×
  the selected setting's — spent largely on worlds that
  never finish.
- **Overturn co-report:** 4/127 non-thin states
  (0.0315) under both valuations.

## 5. What the grid says

- **The horizon is the completion lever.** Adding the
  turn-62 horizon — at B0's own hooks and deadline
  (B0+H) — takes completion from 0.3500 to 1.0000,
  thin-prior from 0.4708 to 0.0000, and *halves* the mean
  wall (57.60 → 26.57 s): bounded worlds finish instead
  of consuming the budget. This is the direct-evidence
  version of Stage 0's read (its horizon pass cut pooled
  unfinished from 12.12% to 0.02% with the edge intact).
- **Hooks and deadline move nothing on this panel.**
  From 4,000 → 16,000 hooks and 180 → 360 s (all with
  the horizon), completion, thin-prior, pooled share and
  the overturn co-reports are identical, and mean walls
  stay inside a 0.3% band. The residual unfinished
  worlds are 3 per setting at every budget. The bar is
  cleared by the cheapest completion-equivalent
  configurations; nothing in this panel rewards the
  larger budgets.
- **The valuation moves overturns, not completion.**
  Under draw = 0 the +H settings overturn on 22/240
  non-thin states; at 0.5, on 30/240 — 8 states flip
  with the price of a drawn world, as registered for
  co-reporting. These are reads of the decision rule on
  panel states, not edge measurements; Stage 2 is where
  the calibrated teacher plays games.

## 6. Independent audit

`audit_stage1.py` (published in `data/stage1/` with its
output `audit_stage1.json`) was written from the
registered definitions — not from the analyzer's code —
and recomputed, for **each** setting, from the raw
rows (`evals_<setting>.jsonl` + `stats_<setting>.jsonl`
on the box):

- (a) row counts: 17,025 world rows / 240 stat rows —
  exact for all six settings;
- (b) per-state completion (finished worlds counted
  from the world rows themselves), plus the
  candidate-level rate, pooled finished share and
  thin-prior rate;
- (c) mean / p95 / max / total per-decision wall from
  the stat rows;
- (d) the overturn co-reports under both valuations
  (the decide rule as specified in the launch package
  §2), and the stat `cand_finished` cross-check against
  the world rows (0 mismatches in 681 × 6 candidate
  tallies).

**Result: full agreement on every check for all six
settings** (counts exact; floats within 1e-9), including
the error tallies (B0 abort 3,566; +H abort 3 each). The
audit's own selection sort, run on its recomputed
values, also returns H8k-180+H. No disagreement was
found anywhere; had any appeared, it — not this report —
would have been the deliverable.

## 7. Publication

`rounds/round9/data/stage1/` (see its `MANIFEST.md`):
the six settings' stat files and job copies,
`panel_jobs.jsonl` + `panel_report.json`, the launch and
relaunch manifests and logs, the B0 gate report, the
analyze run log, the analyzer's `stage1_report.txt` /
`.json`, the runner's `stage1_manifest.json`, and the
audit script + output. The six world-row files
(273,689,565 bytes raw) are published in the same
directory gzip-compressed as `evals_<setting>.jsonl.gz`
(~8.2 MB total), each decompressing to exactly the raw
bytes hashed in the MANIFEST (and in
`stage1_manifest.json`); every figure above traces to a
file hashed there.

## 8. Registered consequence

A calibrated setting exists, so round 9 proceeds:
**Stage 2 fields the teacher at H8k-180+H** — 8,000
hooks, 180 s deadline, horizon at turn 62 scoring −1,
k = 25, margin 1.5 — under Stage 2's own registration
(200 fresh games, seeds 22001–22100, label bases
955001 + shard × 10⁸; the ghost pre-gate, clause 9,
re-proves the new build against raw v10 before any live
game; the live Decide path carries the horizon value
per the confirmation's carry-forward, and both players'
life totals are recorded on horizon-ended worlds per
the rules-note ruling). The NO CALIBRATED SETTING stop
does not arise. D6 does not arise either: it was
conditioned on a Stage-0 null that is not
instrument-limited, and Stage 0 was positive; Stage 1's
outcome gives it no new trigger.
