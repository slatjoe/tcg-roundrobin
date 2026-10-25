# Round 8 — W=100 V1 check: RELAUNCHED and COMPLETE — threshold reads STOP

**Launch:** manifest `rounds/round8/wcheck-launch.md` (repo sha 08ea4bb7); approved amendment a9dd40e2; pin fix confirmed in `claude-reply-af89615.md` (repo commit 4d2444a4); Joe's Option-1 go recorded 2026-10-25 14:46 EDT.
**Outcome in one line:** the check **ran to completion** this time. The pilot's 547 V1 capture states were labeled twice at W=100 (run A at world-seed base 555001, run B at 777001), and the registered threshold reads **STOP — V1-ov 0.439 < 0.50**: at W=100 the teacher's overturns reproduce only ~44% of the time, so the corpus does not run at W=100 and the question returns for decision. No games were played. The first attempt's abort (62-char v15 pin literal, report at repo 0e4c285a) is superseded by this report.

## 1. Launch record

- **Deployed code, verified by sha256sum on the box BEFORE launch** (`/home/joe/tcg/round8_code/`, deployed from the staging tree): `distill_label_main.php` = `acf5f4bb3d8b0c7dbbdb3ba1dffa18aeebbde166c07f492ac74a70411e674cc4`; `label_reduce.py` = `25a5f4cc8ad2875e0d3233ae40e09c4ce2c4468befce71e46d575daf2e685399`; `run_w_check.sh` = `489bf8451b0976a4e0ccf023154a0885814067b2e01d4c0159eeb3b39fad425a` (the confirmed pin fix). The run's own `deployed_code_hashes.txt` (`/tmp/distill_wcheck/`, sha256 `2e9e8d004281dcd5e5cc84827c9186007abbdc63b3e4de1aed25660c4cc0c396`) records the same three hashes.
- **Stale OUT disposition:** `/tmp/distill_wcheck` from the aborted attempt was verified to contain exactly one file, `deployed_code_hashes.txt` (sha256 `ec24d9c8f56294c737b97248349d15035fee174eb9f3f3993127fadece00ae6d`, the abort's own code-hash record), and the directory was removed so the relaunch started clean. The aborted attempt's run log was preserved as `/tmp/r8_launch/wcheck_run_aborted1.log` (sha256 `3fb4b0571c8e70da4c72392763b3b8479772af2d8066c35018443e5ab79ae37e` — the same hash the aborted attempt recorded for its one-line log).
- **Source jobs:** `/tmp/distill_pilot_resume/v1_jobs.jsonl`, 547 lines, present pre-launch.
- **Launch:** `bash run_w_check.sh` from `/home/joe/tcg/round8_code`, setsid-detached, 2026-10-25 15:27 EDT; run log `/tmp/r8_launch/wcheck_run.log`, sha256 `437a80e3cd8a4569ffa4cf6b4e2c724ce8ea37d6fc694ca588d90071ef761576`. Pre-flight pins passed (the guard and the corrected literal did their work silently); G8 cleared the pre-existing segments 126 → 0; shards 137/137/137/136.
- **Phases (artifact timestamps):** run A labeling 15:27 → 17:11, run B 17:11 → 18:57, report written 18:57:48 EDT. **Total wall ≈ 3.5 h** — well over the 1.3–1.5 h planning estimate, which was extrapolated from the one-state smoke; §3 carries the measured per-job cost that replaces it. No runner processes remain.

## 2. The read — `wcheck_report.txt` verbatim

`/tmp/distill_wcheck/wcheck_report.txt`, sha256 `bdf91e5f44a3e7f3e8b01d676b24fe6a979d27657fee1db290fb421365f5b558` (`wcheck_report.json`, sha256 `79ced9ffc4b51b676a27f38b00388abae1104900fa9aa5d37fb0d6c35d82c05e`, carries the same reads in structured form; the reduce summaries in the run log read: pass A — 547 jobs, labels 545, thin 2, overturn 66, confirm 327, no_overturn_tested 152, no_rows 0, prior_not_selected 0; pass B — labels 546, thin 1, overturn 68, confirm 343, no_overturn_tested 135, no_rows 0, prior_not_selected 0):

```
ROUND-8 W=100 V1 CHECK (claude-reply-597d181 sec.3)

V1 AT W=100 (pilot capture states, 544 states labeled twice; A overturns 66, A confirmations 478):
  V1-ov  P(B same overturn | A overturned): 29/66 = 0.439 Wilson95 [0.326, 0.559]
  V1-conf P(B confirms | A confirmed): 442/478 = 0.925 Wilson95 [0.897, 0.945]

THIN (excluded, counted): w100a 2, w100b 1

COST (report-only): 1094 label job-runs timed; per-job secs: mean 45.8  p95 90.6  max 115.4

REGISTERED THRESHOLD: STOP - V1-ov below 0.50 (or undefined): reported for decision; the corpus does not run at W=100
```

Widening from 25 to 100 worlds moved V1-ov from the pilot's 0.167 to 0.439 — reproducibility roughly tripled, and the confirmation rate stayed high (0.925) — but the overturns still do not reproduce at the registered 0.50 line. Per the confirmation's scope, a STOP returns the question for decision; nothing about the corpus launches on this read.

## 3. Report-only additions (per `claude-reply-a9dd40e`, confirmed in `claude-reply-af89615`)

### (1) Finished worlds per candidate, and the raw rows' error reasons

From both runs' label files (`labels_w100_a.jsonl` sha256 `d0e298ff46be2f4360658373378712046e7e9ed915473a19f9f5c545c870476e`, `labels_w100_b.jsonl` sha256 `a6038f643eb8a763bb2665551457cd4fa9856bd7851ebb5ac300e8062f0c8ec0`): **3,195 candidate entries; minimum n_worlds 0; 2 entries below 100 (0.0626%), and the same 2 below 80 — both are exactly 0.** Every other candidate finished all 100 worlds. The thin files (`thin_w100_a.jsonl` `ebfe5713…`, `thin_w100_b.jsonl` `cbbe7e3d…`) hold the 3 excluded rows, every candidate at 0.

The raw rows reconcile exactly. Each run emitted **160,200 rows** (`raw_a_all.jsonl` sha256 `55deb993783ce65e2dcc0f01ebe4e0bcaf25c19c4521707ce7eb4e89569328d5`, `raw_b_all.jsonl` sha256 `2ec6ead74a27bb9eaeeaec32244051da6ff43ddd0629c3ff7889553b09799938`): run A = 159,500 finished + **700 error rows**; run B = 159,800 finished + **400 error rows**. The sums of `n_worlds` over labels+thin equal the finished counts exactly (159,500 / 159,800). Error reasons, counted over every row (an error row's `result` is exactly `{"error": <reason>}`):

| reason | run A | run B |
|---|---|---|
| `canary_hook_failed` | 600 | 0 |
| `det_persist_failed` | 0 | 300 |
| `abort` | 100 | 100 |
| **total error rows** | **700** | **400** |

Every error count is a whole number of 100-world candidate batches: 7 failed batches in A, 4 in B — matching the zero-finished candidate slots exactly (A: 6 slots in its 2 thin rows + 1 inside an emitted label; B: 3 in its 1 thin row + 1 inside an emitted label). **No row in either file carries an explicit deadline/timeout reason string**; the two `abort` batches (one per run) are the only candidates whose loss is not attributed to the canary or determinization persistence. No batch was partially thinned by the 300 s label deadline in any way the rows record — worlds were either all finished or the whole batch errored.

### (2) Cost at W=100

From the report (§2): 1,094 job-runs timed; per-job **mean 45.8 s, p95 90.6 s, max 115.4 s**. The corpus estimate at W=100, in the pilot report's convention (per 10,000 contested labels): **127.2 box-hours serial at the mean (251.7 at p95); on the 4 label trees, 31.8 h wall (62.9 h at p95)** — arithmetic: 45.8 s × 10,000 = 458,000 s; 90.6 s × 10,000 = 906,000 s. For scale against the registered corpus: the pilot's 20 games produced 547 contested states (~27 per game), so a 400-game corpus implies roughly 11,000 contested labels — the per-10,000 figures are the right order for it. The check itself consumed ≈ 13.9 serial box-hours (1,094 × 45.8 s) inside its 3.5 h wall.

### (3) Shared memory

Per-tree sweepers (8 logs in `/tmp/distill_wcheck/shm_sweep_{a,b}{0..3}.log`, 104–107 passes each). Pass-line accounting, summed over all passes and logs, with the per-pass identity `selected = deleted + failed` verified in each of the 8 logs: **selected 3,116 = deleted 839 + failed 2,277**. The sums count attempts, not distinct segments — a segment a pass could not yet delete (its owner still finishing) is re-selected and re-counted on later passes, which is what the large failed figures are; the final passes' failed lines sum to 3. Unattributed (the (C) fail-safe KEEP count) ended at 0 in seven logs and 2 in `shm_sweep_b2.log` (per-pass maximum across logs: 4). **Closing state: 0 segments** (`ipcs -m` after the run), and the run's own G8 had already cleared the 126 pre-existing segments to 0 before labeling started.

## 4. Disposition

The check is complete and its read is **STOP** under the registered threshold. Per the confirmation's scope this returns for decision: the corpus does not launch at W=100, and no part of the banked corpus go's conditions (check PASS + reviewer read) is met. What remains is a decision among the people reading this report — the labels, thin rows, raw rows, and sweep logs all remain in `/tmp/distill_wcheck` for independent recomputation.
