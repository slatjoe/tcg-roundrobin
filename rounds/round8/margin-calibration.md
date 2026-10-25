# Round 8 — option-2 margin calibration: NO QUALIFIER — the line closes

**Decision frame:** Joe chose option 2 (2026-10-25 19:09 EDT) from `claude-reply-0140eab.md` §2, where the whole protocol below was registered before anything was computed.
**Outcome in one line:** the calibration ran on the W=100 check's existing labels only — no new labels, no games — and **no margin in the grid reaches V1-ov ≥ 0.60 on the selection half H1** (best: 0.571 at m = 3.0, on 7 A-overturns). Under the registration, with no H1 qualifier the verification half is never invoked and **the distillation line closes (option 3)**. The built-in fixture passed exactly first: the recomputation reproduces the check's shipped decisions on all 1,091 label rows and its full-set reads (66, 29/66, 442/478) to the count.

## 1. Inputs and fields

- Run A labels: box `/tmp/distill_wcheck/labels_w100_a.jsonl`, sha256 `d0e298ff46be2f4360658373378712046e7e9ed915473a19f9f5c545c870476e` (545 rows); run B labels `labels_w100_b.jsonl`, sha256 `a6038f643eb8a763bb2665551457cd4fa9856bd7851ebb5ac300e8062f0c8ec0` (546 rows); thin A `ebfe5713a91cd9c258da783c5901597bca8ad7016b7cb35c0d6cbb65fbe4db95` (2 rows), thin B `cbbe7e3d5afc5e4cb3d4f3e3dce9f37beaa6b9a5df58cd72569416eeb68049f0` (1 row). All hashes re-verified on the box and on the local copies before computing.
- **The labels carry everything the calibration needs — nothing was improvised from raw rows.** Fields used per state per run: `candidates` (the selected set), `prior_pick`, per-candidate finished-world `means`, and the pair stats `paired_n` / `mean_diff` / `se_diff`. Two schema facts make the recomputation exact:
  - The reducer computes paired stats **only for the best-mean candidate** ("best"), and stores them on the row whenever best ≠ prior and the paired count is ≥ 20 — including rows whose test did not fire at 1.5 (the `no_overturn_tested` rows). Where best == prior, or paired_n < 20, the stats are null and no margin can fire — the reducer's own rule.
  - "best" is not a stored field when the test did not fire; `calibrate_margin.py` recovers it with the reducer's own scan (ascending over `candidates`, strict >, starting from the prior's mean, over the row's stored `means`). The fixture in §3 proves the recovery empirically on every row.
- The decision at margin m (everything else in the registered rule unchanged): **overturn(m) iff best ≠ prior AND paired_n ≥ 20 AND mean_diff > m · se_diff**; the pick at m is best on an overturn, the prior otherwise. V1 counting mirrors `pilot_report.py`'s V1 block (and `run_w_check.sh`'s read), parameterized by m; Wilson intervals are `pilot_report.wilson`, imported, as the check's reader imported it.

## 2. Population and split

- Population: the **544 states labeled in both runs**. Accounting: A-only state `286996099_t19` is exactly thin-B's row; B-only states `286996099_t12`, `286996099_t16` are exactly thin-A's rows (all three in game 286996099, each a whole-batch determinization loss with 0 finished worlds — the check report's §3(1) population, not a labeling gap). A and B agree on `game`, `prior_pick` and `candidates` for all 544.
- Split (registered algorithm, implemented verbatim in the code so the reviewer can reproduce it from the published files): group by the label rows' `game` field (the game id embedded in the snapshot id — `state_id` starts with `game` on all 1,091 rows); sort the 20 unique game ids as strings; shuffle with `random.Random(20261025)`; first ⌈20/2⌉ = 10 games = H1, rest = H2.
  - **H1 (10 games, 284 states):** 846941112, 286996099, 882717405, 458087167, 423095452, 945603323, 220719073, 542398807, 140079940, 475002105.
  - **H2 (10 games, 260 states):** 218711839, 312432844, 852109890, 955924560, 169234412, 831144116, 324193875, 396512818, 566235298, 745681102.

## 3. The fixture (mandatory self-test, ran first)

`rounds/round8/fixtures/calibration_fixture.txt` (sha256 `b4a381c9a8408061f7199d11a4c8ff3c7863c0c7580e88e582505742dd1132e5`), verbatim:

```
CALIBRATION FIXTURE - m=1.5 reproduction of the W=100 check's shipped reads

run A: per-row decision agreement at m=1.5: 545/545
run B: per-row decision agreement at m=1.5: 546/546
full-set (544 states) at m=1.5: A overturns 66 (expected 66); V1-ov 29/66 (expected 29/66); V1-conf 442/478 (expected 442/478)
FIXTURE: PASS - the m=1.5 recomputation reproduces the check's reads exactly
```

The per-row agreement is the strong form of the test: it proves both the best-recovery scan and the parameterized decision reproduce the shipped (`overturn`, `teacher_pick`) on **every one of the 1,091 rows**, not just the aggregates.

## 4. The grid (report-only reads plus the registered selection/verification)

Winner's-curse reads are A→B: **primary** = over A's overturn-at-m states, the mean of B's per-candidate-mean advantage for A's overturned pick, `means_B[pick] − means_B[prior]` (the registered "mean advantage of the overturned pick under the other run's means"; no A-overturn state was missing a B mean at any m). **Secondary** = the mean of B's stored paired `mean_diff` over the A-overturn states where B's tested candidate is A's pick, with its coverage count.

### m = 1.5 (the registered rule — restated from the fixture population)

| set | A overturn | V1-ov | V1-conf | curse primary | curse secondary |
|---|---|---|---|---|---|
| full (544) | 66/544 = 0.121 [0.097, 0.151] | 29/66 = 0.439 [0.326, 0.559] | 442/478 = 0.925 [0.897, 0.945] | +0.153 (66) | +0.218 (45) |
| H1 (284) | 36/284 = 0.127 [0.093, 0.170] | 16/36 = 0.444 [0.295, 0.604] | 234/248 = 0.944 [0.907, 0.966] | +0.171 (36) | +0.244 (24) |
| H2 (260) | 30/260 = 0.115 [0.082, 0.160] | 13/30 = 0.433 [0.274, 0.608] | 208/230 = 0.904 [0.859, 0.936] | +0.131 (30) | +0.189 (21) |

### m = 2.0

| set | A overturn | V1-ov | V1-conf | curse primary | curse secondary |
|---|---|---|---|---|---|
| full (544) | 36/544 = 0.066 [0.048, 0.090] | 14/36 = 0.389 [0.248, 0.551] | 487/508 = 0.959 [0.938, 0.973] | +0.212 (36) | +0.286 (25) |
| H1 (284) | 23/284 = 0.081 [0.055, 0.119] | 9/23 = 0.391 [0.222, 0.592] | 253/261 = 0.969 [0.941, 0.984] | +0.236 (23) | +0.311 (16) |
| H2 (260) | 13/260 = 0.050 [0.029, 0.084] | 5/13 = 0.385 [0.177, 0.645] | 234/247 = 0.947 [0.912, 0.969] | +0.169 (13) | +0.242 (9) |

### m = 2.5

| set | A overturn | V1-ov | V1-conf | curse primary | curse secondary |
|---|---|---|---|---|---|
| full (544) | 21/544 = 0.039 [0.025, 0.058] | 12/21 = 0.571 [0.365, 0.755] | 515/523 = 0.985 [0.970, 0.992] | +0.294 (21) | +0.362 (17) |
| H1 (284) | 13/284 = 0.046 [0.027, 0.077] | 7/13 = 0.538 [0.291, 0.768] | 266/271 = 0.982 [0.958, 0.992] | +0.325 (13) | +0.420 (10) |
| H2 (260) | 8/260 = 0.031 [0.016, 0.060] | 5/8 = 0.625 [0.306, 0.863] | 249/252 = 0.988 [0.966, 0.996] | +0.245 (8) | +0.280 (7) |

### m = 3.0

| set | A overturn | V1-ov | V1-conf | curse primary | curse secondary |
|---|---|---|---|---|---|
| full (544) | 11/544 = 0.020 [0.011, 0.036] | 6/11 = 0.545 [0.280, 0.787] | 527/533 = 0.989 [0.976, 0.995] | +0.425 (11) | +0.474 (10) |
| H1 (284) | 7/284 = 0.025 [0.012, 0.050] | 4/7 = 0.571 [0.250, 0.842] | 273/277 = 0.986 [0.963, 0.994] | +0.451 (7) | +0.537 (6) |
| H2 (260) | 4/260 = 0.015 [0.006, 0.039] | 2/4 = 0.500 [0.150, 0.850] | 254/256 = 0.992 [0.972, 0.998] | +0.380 (4) | +0.380 (4) |

### Selection and verification

- Selection (H1 only, smallest m with V1-ov_H1(m) ≥ 0.60): H1 reads **0.444, 0.391, 0.538, 0.571** for m = 1.5, 2.0, 2.5, 3.0 — **no qualifier; m\* does not exist**, so the H2 verification is not invoked.
- **OUTCOME: CLOSE — no margin in the grid reaches V1-ov ≥ 0.60 on H1; the distillation line closes (option 3).**

What the grid shows, without softening the outcome: tightening the margin does buy real signal at the strict end — the surviving overturns keep more of their advantage under the other run's means (+0.153 → +0.425 full-set) and full-set reproducibility rises to ~0.55–0.57 — but the population collapses as it does (66 → 11 A-overturns), and on the selection half the reproducibility never crosses the registered bar; the closest approach (m = 3.0, H1) is 4 of 7 states. The trade the calibration was built to measure is real, and it does not reach the registered terms.

## 5. The `label_reduce.py` margin pin (staged with this note)

`rounds/round8/code/label_reduce.py`, sha256 `b6e66390430dfd69b101f835955c3836c4ca78dc4cee951385035d35c94c2906` (supersedes `25a5f4cc…`). The change set is only the pin, following the W pattern:

- `LABEL_MARGIN` env, validated as a positive finite number (`margin_pin()`), default **1.5**.
- Every job must carry `margin` numerically equal to the pin (bool / non-numeric / missing / unequal all abort), checked **before any raw row is read** — a mismatched job set never produces a partial reduce.
- Every emitted label row and thin row carries `margin`, as do the counts; the Decide comparison is now `mean_diff > MARGIN * se_diff`. At the default pin the arithmetic is the shipped arithmetic (float 1.5 == the literal 1.5).

**Fixture (on the box, `/tmp/margin_fx/`):** the first 200 jobs of `jobs_w100.jsonl` stamped `margin: 1.5` (`fx_jobs.jsonl`, `ccea43fbeb9f49216d241bdd34ff333ad10371a216a844482c5969ef0563dd68`), their 58,500 raw rows extracted from `raw_a_all.jsonl` in file order (`fx_raw.jsonl`, `db062e936864194f064dd0608deaffe6090c233b0a0d30c4a806b11a20b093f0`), reduced with the amended code at the default pin:

- Counts: 200 jobs → **198 labels, 2 thin** (confirm 119, no_overturn_tested 59, overturn 20, paired_thin 0; counts carry `"margin": 1.5`, `"W": 100`).
- **198/198 label rows match the corresponding shipped `labels_w100_a.jsonl` rows exactly on the decision fields (`teacher_pick`, `overturn`, `means`) — 0 mismatches**; the paired fields (`paired_n`, `mean_diff`, `se_diff`) also match on all 198 (report-only, beyond the required fields). `fx_labels.jsonl` sha256 `41a27471bb2b379b60fab9e47b31b55efbe5192ed36664a3f513cde4d42c66a2`.
- Thin agreement: the sample's thin rows are exactly the shipped thin-A snaps (`286996099_t12`, `286996099_t16`), each carrying margin 1.5 (`fx_thin.jsonl`, `779c9293c76755eb36fee48b1770ec30a6444b8bd548f96cae8d6e675d5ea7a9`).
- Negative tests, all aborting with exit 1 before reducing: jobs without `margin` (`ABORT: job for snap 286996099_t8 carries margin None != the LABEL_MARGIN pin 1.5 …`); `LABEL_MARGIN=2.0` against jobs stamped 1.5 (`… carries margin 1.5 != the LABEL_MARGIN pin 2.0 …`); `LABEL_MARGIN=abc` (`ABORT: LABEL_MARGIN 'abc' is not a number …`).

## 6. Artifacts

| artifact | sha256 / location |
|---|---|
| `rounds/round8/code/calibrate_margin.py` | `0d72295f8f2690acafa094bf154d3894dcf99b83c9c9b6b907600d54879baf85` |
| `rounds/round8/fixtures/calibration_fixture.txt` | `b4a381c9a8408061f7199d11a4c8ff3c7863c0c7580e88e582505742dd1132e5` |
| `rounds/round8/code/label_reduce.py` (amended) | `b6e66390430dfd69b101f835955c3836c4ca78dc4cee951385035d35c94c2906` |
| calibration results JSON (full machine-readable table) | `b0e50f13621fbd90417c213ae4270d3b2e6e4f27ea5398e5e4c85e463149df03` (work copy; every figure in it is in §4) |
| reducer fixture (box) | `/tmp/margin_fx/` — jobs / raw / labels / thin hashes in §5 |
| inputs (box) | `/tmp/distill_wcheck/` — label / thin hashes in §1; `wcheck_report.txt` `bdf91e5f44a3e7f3e8b01d676b24fe6a979d27657fee1db290fb421365f5b558` |

**Note on the close:** per `claude-reply-0140eab` §2, this calibration was the fork — pass and the corpus could be proposed at W=100 with margin m\*; fail and option 3 governs. It failed at the selection step, on the registered terms, with the fixture proving the computation is the shipped decision recomputed rather than a new one. The finding the line closes on: at the registered decision rule the teacher's overturn labels reproduce at 17% (k=25) and 44% (W=100); no stricter threshold in {1.5, 2.0, 2.5, 3.0} brings held-out-selection reproducibility to 0.60, and the surviving overturn counts at the strict end (7–13 per half) are too thin to verify at 0.50 with any room. The margin pin in §5 is staged anyway — it is part of the registered option-2 package, it is fixture-proven, and any future label rule (a new registration, e.g. value-based targets) inherits a reducer whose decision constant is pinned and recorded rather than literal.
