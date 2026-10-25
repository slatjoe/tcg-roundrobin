# Round 7 — Stage-5 gate fleet report

**Parent:** 8816c66b (fleet-launch manifest, verified at `refs/heads/main` before launch). **Launched sha (approved build):** a6d8442291f6d53aefcdf58daf1c8860d0ed0731. **Launch manifest:** `fleet-launch.md` (the 8816c66b commit). **Joe's go:** 2026-10-23 ~07:01 EDT. This report answers the fleet-alignment registration (51f35d9c, accepted) and the launch manifest's report requirements; every decisive artifact is cited by path and sha256 (§11).

## 0. Verdict

**The fleet does not convert. The teacher played raw v10 to parity on Gravy Bones: paired Δ = +0.0075, bootstrap CI [−0.0138, +0.0288] — the registered band read is PROJECTION OVERSTATED (CI includes 0, upper bound < +0.10).**

- Primary: teacher **216.0** points − raw **213.0** points over 400 pairs (teacher 173W/86D/141L = 0.5400; raw 163W/100D/137L = 0.5325). Conversion (Δ ≥ +0.05 with CI lower > 0) fails on both terms; the +0.15 transfer band is not approached; the +0.20 impeachment band is not triggered. Discordant pairs 19/17 with 364 tied; exact sign test p = 0.8679.
- The seat split is exact parity twice: seat 1 Δ +0.0075 [−0.0200, +0.0350], seat 2 Δ +0.0075 [−0.0225, +0.0400].
- **Timeout stop NOT fired:** 7 teacher timeouts of 400 games = **1.75%**, under the >2% INCONCLUSIVE line. The 7 timed-out games are scored as teacher losses in the primary; dropping their pairs gives Δ +0.0165 [−0.0038, +0.0370] — the read does not change (§4).
- Audits that ran from the fleet outputs are clean: **L1** shows no leak signature (§7.1); **G3** records defects = 0 with every differing unit traced to a DECISION overturn (§7.2); canary refusal ≤ 0.134% on every arm-seat stream (cap 2%); fallbacks 0 everywhere.
- **L2 and L3 scoring were NOT produced.** Both require the registered post-gate L-run — a separate measurement launch on the production server that is not part of the fleet outputs and was not launched. The verbatim failures and what closing them requires are recorded in §7.3–7.4. No substitute numbers were computed.
- Dilution diagnostics (§6): **31.7%** of contested decisions fell back thin-prior (search never reached the 20-finished-world floor), and among the 6,441 non-thin contested decisions the overturn rate is **1.83%**, far below the 12–16% band the Fai fleets established. **A Gravy null must not be read as 'search doesn't help' when it may partly mean 'search couldn't run'.**
- Non-win co-report (registered, no band attaches): Δ **+0.0250** [+0.0025, +0.0500] under capped = 0 scoring (§3).
- The registry merge ran BEFORE any analysis, as registered: **5,031 → 6,161 games** (§8), and the analysis script's G9 registry gate passed against the merged registry.

## 1. Launch record

Launched **2026-10-23T07:03:36-04:00** under setsid (runner pid/pgid 943700) from `/tmp/gravytree`, env `GATE_TIMEOUT=3870`, `GRAVY_MODEL=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt`; outputs in `/tmp/ggate`; run log `/tmp/gfleet/fleet_run.log`. Pre-launch condition (§4 of the launch manifest) executed immediately before launch: standing G8 sweep took segments **30 → 0**, no game processes alive. A box-side watchdog (`/tmp/gfleet/watchdog.sh`, 600 s cadence) held the 3,600-segment stop for the unattended run; it never fired (in-run segment counts cycled in the low hundreds). The runner exited with all results home; the completion reading at **2026-10-24T20:32:59-04:00** records runner gone, 400 teacher + 400 raw results — wall clock ≈ **37 h 29 m**.

Design, as registered: teacher vs raw `ckpt_v10.pt`, paired on seeds **8001–8200**, both seats, Gravy mirror (deck `nats2026_eriksen_gravy_60.txt`, sha256 `b8b41390…`) against the heuristic, 4 chunks × 100 pairs = 800 games. Turn-cap instrument: parameter 87 / trigger 62. Draw-scored primary (engine caps score 0.5); teacher wall-clock timeout = teacher loss (primary), pair dropped in the sensitivity table; raw timeout would score 0.5 after one re-run (none occurred).

Pins (verified at launch; full record in `fleet-launch.md`):

| File | sha256 |
|---|---|
| `run_gravy_gate.sh` (fleet runner) | `0ffe635b7fe81fdb41325cc55f27d1af09f3909fb4f70a65522d9655d5e453a2` |
| `paired_driver.py` (Gravy launch copy, cap 87) | `0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae` |
| `gate_raw_retry.py` | `c3fb227e…` |
| `search.php` (K2) | `8f6b35da…` |
| `featurize.php` | `f81193e0…` |
| `rl/search_server.py` (patched, tree copy) | `ab85fa1b…` |
| `shm_sweep.py` ((C) sweeper, fail-safe build) | `98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33` |
| checkpoint `ckpt_v10.pt` | `44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3` |

Both servers loaded `ckpt_v10.pt` on cuda at launch; fallbacks stayed 0 for the entire run (§5).

## 2. Primary result

From the registered analysis (`analyze_gate_gravy.py`, pin `d468468e…`, run unedited; box output `/tmp/ggate/primary_report.txt`, §11), quoted:

```
units total: 400 | scored: 400 | unscored: 0
capped games among scored units: 105 (scored 0.5 per ruling)

pooled      : n=400 units, 200 seeds | teacher 0.5400 - raw 0.5325 = delta +0.0075 | bootstrap CI (clustered by seed, B=10000) [-0.0138, +0.0288]
seat 1      : n=200 units, 200 seeds | teacher 0.5475 - raw 0.5400 = delta +0.0075 | bootstrap CI (clustered by seed, B=10000) [-0.0200, +0.0350]
seat 2      : n=200 units, 200 seeds | teacher 0.5325 - raw 0.5250 = delta +0.0075 | bootstrap CI (clustered by seed, B=10000) [-0.0225, +0.0400]

DISCORDANT: teacher>raw 19 | teacher<raw 17 | tied 364 | exact sign test (two-sided) p = 0.8679
READ (pooled): PROJECTION OVERSTATED (CI includes 0, upper < +0.10)
```

Cross-checks (independent recomputation from the row files, fleet-diagnostics.json §11): the normal-approximation CI from sumDiffSq 18.0 is [−0.0133, +0.0283] — same read, method difference only (the registered read is the script's cluster bootstrap). Per-chunk paired Δ, for the record:

| chunk | teacher pts | raw pts | Δ |
|---|---|---|---|
| c1 | 55.5 | 52.5 | +0.030 |
| c2 | 51.5 | 51.0 | +0.005 |
| c3 | 55.0 | 54.0 | +0.010 |
| c4 | 54.0 | 55.5 | −0.015 |
| **pooled** | **216.0** | **213.0** | **+0.0075** |

No chunk carries the pooled result; the largest single-chunk deviation (c1, +0.030 on 100 pairs) is inside chunk-level noise.

## 3. Non-win co-report

Registered co-report (fleet-alignment): identical scoring to the primary except an engine-capped game scores **0** for that arm instead of 0.5; no band read attaches. Quoted from the same analysis output:

```
pooled      : teacher 0.4325 - raw 0.4075 = delta +0.0250 | bootstrap CI [+0.0025, +0.0500]
seat 1      : teacher 0.4350 - raw 0.4150 = delta +0.0200 | bootstrap CI [-0.0100, +0.0500]
seat 2      : teacher 0.4300 - raw 0.4000 = delta +0.0300 | bootstrap CI [-0.0050, +0.0650]
```

Every draw in this fleet was a turn-cap draw (teacher 86 capped of 86 draws; raw 100 capped of 100 draws), so under non-win scoring both arms' draw points vanish and the co-report reduces to the win-count difference: teacher 173 wins vs raw 163 wins = +10 net wins over 400 pairs. It is recorded as the registered co-report and nothing more: the bands apply to the primary (§2), and the primary's draw price (0.5) is the registered one for this gate.

## 4. Teacher timeouts and drop-sensitivity

Seven teacher games hit the `GATE_TIMEOUT` of 3,870 s and were recorded by the driver as `invalid="timeout"` rows (no winner, no secs; each row carries the ids of games spawned during the attempt):

| stream | seed | seat | spawned game ids in the row |
|---|---|---|---|
| `gate_c1_teacher_s1.jsonl` | 8046 | 1 | 114 |
| `gate_c3_teacher_s1.jsonl` | 8135 | 1 | 70 |
| `gate_c3_teacher_s2.jsonl` | 8125 | 2 | 37 |
| `gate_c3_teacher_s2.jsonl` | 8131 | 2 | 59 |
| `gate_c4_teacher_s1.jsonl` | 8178 | 1 | 35 |
| `gate_c4_teacher_s1.jsonl` | 8184 | 1 | 51 |
| `gate_c4_teacher_s2.jsonl` | 8178 | 2 | 79 |

Final rate: **7 / 400 = 1.75%** — the >2% INCONCLUSIVE stop (timeout ruling 2) does not fire. (The rate sat above 2% at interim denominators — 7 of 341 = 2.05% at the 15:32 EDT reading on Oct 24 — and resolved below the line as the remaining games completed; the ruling applies to the fleet's final count.) All seven are scored as teacher losses in the primary. The script's sensitivity line, quoted:

```
SENSITIVITY (teacher-timeout pairs dropped): n=393 delta +0.0165 CI [-0.0038, +0.0370]
```

(Normal-approximation cross-check: Δ +0.01654 [−0.0035, +0.0366].) Dropping the timed-out pairs raises the point estimate by ~+0.009 and changes nothing else: the interval still straddles 0 and still excludes +0.05. There were no raw timeouts, no connect failures, and no other invalid rows: 400 units scored, 0 unscored.

## 5. Containment and server evidence

The (C) kernel-attribution sweeper ran live for the whole fleet (`/tmp/ggate/gate_shm_sweep.log`, 2,239 PASS + 2,239 DELETED lines): **selected 120,349 · deleted 120,349 · failed 0 · unattributed 24**. The 24 unattributed are the fail-safe working as registered: segments whose `ipcs -m -p` row lacked a cpid/lpid were KEPT and counted, never deleted (the ef34219 fix, confirmed at a6d84422). Closing segment count: **227**, recorded at the completion reading and confirmed by a post-run `ipcs` observation (2026-10-24 23:45 EDT) — all rule-3-kept parents (game directories present under the tree). The fleet-launch expectation was up to ~800 accumulated parents (≈1 per game); the observed residue is below that ceiling, and the 3,600 stop was never approached (in-run counts cycled between ~70 and ~260). The 227 remain on the box; a G8 sweep is the standing pre-launch condition for whatever runs next.

Servers: both search servers loaded `ckpt_v10.pt` on cuda; the latest `fallbacks=` value in each of `gate_server_s1.log` and `gate_server_s2.log` is **0**, and no fallback stop fired at any point in the run.

## 6. Stage-5 report-only diagnostics

Source: the eight teacher streams' `search_stats.jsonl` (37,133 stat rows: 37,120 teacher decision rows + 13 canary/missing rows). Contested decisions (rows with `contested == 1`, the rollout rows): **9,429**. Full per-stream detail in fleet-diagnostics.json (§11).

**(a) Overturns — per-candidate world counts.** 118 overturns. The stat rows carry no separate unfinished-worlds field; `n_worlds` records finished worlds per candidate and is present on all 118 overturn rows. Total finished worlds per overturned decision: min 44 / mean 67.5 / max 100 (sum 7,965). The picked candidate's finished worlds: mean 22.97 (sum 2,710); the prior pick's: mean 23.08 (sum 2,723). The failure side of those same rows: `errors` sums to 735, and across all contested rows the monitors record 37,038 candidate aborts (abort_reasons `{'abort': N}` per stream, §11 output file) — the volume the 180 s per-candidate deadlines cut off.

**(b) Thin-prior rate.** 2,988 contested decisions took the `thin_prior` fallback (the prior pick played because the search never reached the 20-finished-world floor): **2,988 / 9,429 = 31.7%** of contested decisions (8.05% of all 37,120 teacher decision rows). For scale: the pre-gate measured 26.8% on seeds 8501–8510; the Fai fleets measured 0 of ~21,500.

**(c) Overturn rate among non-thin contested decisions.** Non-thin contested decisions: 9,429 − 2,988 = 6,441. Overturns: **118** (every overturn is among the non-thin; cross-checked two ways — the `overturn` flag and `pick != prior_pick` agree at 118). Rate: **118 / 6,441 = 1.83%**, against the registered 12–16% null band established by the Fai fleets. Even where Gravy search ran to completion, it almost never found a reason to move off the prior that cleared the registered overturn bar (paired margin > 1.5 × paired SE).

**(d) Fallen-back share of contested decisions.** **2,988 / 9,429 = 31.7%** — identical to (b): every contested fallback in the fleet is `thin_prior`; no other fallback kind appears among contested rows.

**The registered sentence for this read:** A Gravy null must not be read as 'search doesn't help' when it may partly mean 'search couldn't run'. The two dilution channels are both in the record: nearly a third of contested decisions never got a completed search at all, and the completed searches overturned at 1.83% — an order of magnitude under the Fai band. Whether that is search failing to find value in Gravy's positions, the overturn bar being harder to clear in longer noisier games, or the v10 prior already sitting where search would go, is not separable from this fleet's outputs alone; §7.3 records the instrument (L3) that would attribute it, and it was not run.

**G5 calibration** (prior-pick rollout mean by decision ordinal, from the primary analysis output; predicted vs realized for the learner):

| bin | pred | realized | n |
|---|---|---|---|
| 1 | 0.5131 | 0.5496 | 393 |
| 2 | 0.5120 | 0.5496 | 393 |
| 3 | 0.5395 | 0.5497 | 392 |
| 4 | 0.5301 | 0.5499 | 391 |
| 5 | 0.5166 | 0.5491 | 387 |
| 6–10 | 0.5200 | 0.5467 | 1,894 |
| 11–20 | 0.4896 | 0.5226 | 3,161 |
| 21–40 | 0.4018 | 0.4231 | 2,016 |
| 41+ | 0.8025 | 0.7840 | 81 |

**Canary / coverage monitors** (per arm-seat stream, from the same output): root calls 4,448–5,039; canary refusals 0–6 per stream, refusal rate **0.000%–0.134%** (cap 2%); no branch above 5%; `child_fallbacks=0` and `det_persisted_missing=0` on all eight streams. Pooled monitor line: contested 9,429, overturns 118, overturn rate 1.25%.

## 7. Audits

### 7.1 L1 — leak/canary audit (ran, clean)

Deployment substitution O2, as registered: `l1_check.py` (pin `956923d0…`) copied to `/tmp/ggate/l1_check_deploy.py` (sha256 `10c7d91e7a07bf6f45aa223b547efb9f36bf7527c20b4dfe50b174934e878c48`) with exactly one line changed — the input glob `/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl` → `/tmp/ggate/gate_c*_teacher_*_log/search_stats.jsonl` (unified diff in fleet-analysis.json). Output (`/tmp/ggate/l1_output.txt`):

- contested 9,429; U1 (prior-pick unanimous) 3,504 (37.16%); any-candidate-unanimous 4,146 (43.97%); U2 3,772 (40.00%).
- Overturn rows 118; `se_diff` present on 118; **`se_diff == 0` on 2 (1.69%)**; distribution min 0.0000 / p25 0.1565 / median 0.1694 / p75 0.2253 / max 0.3204.

Read: no leak signature. The determinization defect this audit exists to catch presented as `se_diff` exactly 0 across the overturn population (paired worlds identical); here 98.3% of overturns carry healthy positive paired SEs in the same range the Fai audits recorded, and two rows at the distribution's floor do not resemble that pattern.

### 7.2 G3 — first-divergence audit (ran, clean)

Quoted from `/tmp/ggate/g3_output.txt`:

```
units identical=305 legal_diverged=88 skipped_invalid=7 defects=0
```

Every one of the 88 differing units has its first divergence at a DECISION overturn (a legal teacher pick differing from raw), none at a machinery defect; the 7 skipped_invalid units are the §4 timeout units.

### 7.3 L3 — fresh-world attribution (jobs built; scoring NOT PRODUCED)

The jobs build ran: `audit_overturns.py --sample 100000 --seed 20261023` produced **118 jobs from 118 snapshot-index entries** (`/tmp/ggate/jobs_all.jsonl`, sha256 `5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b`) — the fleet's full overturn population.

The scoring step cannot run: there are no label files. Deployment substitution O3 was applied as registered (`analyze_l3.py` pin `16017ffa…` → `/tmp/ggate/analyze_l3_deploy.py`, sha256 `3919bbb80db29eec91c87e6f640e6eb689fa8324865fb450a69292843008dd72`, one line: `DELTA = 0.2525` → `DELTA = 0.0075`; TEACHER_GAMES=400 unchanged), and the attempted command

```
analyze_l3_deploy.py --jobs /tmp/ggate/jobs_all.jsonl --labels /tmp/ggate/l3_out_0.jsonl
```

failed verbatim (exit 1):

```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/ggate/l3_out_0.jsonl'
```

Labels are produced by the separate post-gate L-run (`meas_label_main.php`, LABEL_W=50, production search server, seed bases 855001 + shard×10⁸ in the Fai pattern) — a measurement launch in its own right, subject to the measurement-build approval rule, and not part of the fleet outputs. It was not launched. **L3's mean paired diff, per-game gain, and share of Δ are therefore not producible for this fleet and are recorded as open, not estimated.**

### 7.4 L2 — swap control (NOT PRODUCED)

The registered L2 (20 seeded snapshots × both picks, production server, via the Gravy tree's `probe_swap20.php`, pin `400a9215…` in `/tmp/gravytree`) requires an L2 jobs file; none exists among the fleet outputs. The attempted run

```
cd /tmp/gravytree && SWAP_JOBS=/tmp/ggate/jobs_l2.jsonl SWAP_IDX=0 SWAP_OUT=/tmp/ggate/l2_out.jsonl timeout 120 php probe_swap20.php
```

exited 2 with output verbatim:

```
policy: v1 (deck-aware)
policy: search (seat 1 via /tmp/tcg_policy.sock)
no job at idx 0
```

Same disposition as L3: a separate post-gate run, not launched, recorded as open.

## 8. Registry merge

Executed before any analysis (the analysis script's G9 gate refuses to run otherwise, and passed). Merge record: `fleet-registry-merge.json` (§11); box note `/tmp/ggate/gate_registry_merge.txt`.

- Before: **5,031 games**, sha256 `71cacfb0bfc190f34b4c252e43d515236e65430bcc761a248d1f82e0c519cd5d`.
- Ids collected: **793** `gamename` ids from the scored rows (the 7 timeout rows carry no `gamename`) + **445** entries in the timeout rows' `timeout_new_games` lists (442 unique; 105 of them also appear among the row ids) = **1,130 unique ids, 0 already present**.
- Tag: **`gate:gate`** for all 1,130 — the pregate merge's convention (the registry's `gate:gate` count went 57 → 1,187; no separate tag exists for timeout-spawned ids).
- After: **6,161 games**, sha256 **`fc46f835cafefdca042457bc84b509af47e3f6ed28f63b453fde05261c225521`**.
- Spot verification: six sampled ids — a mix of row ids and timeout-only spawn ids (969608432, 214723822, 147742645, 127827778, 533437181, 970540730) — all present in the merged registry under `gate:gate`.
- Vault refreshed in the prior pattern: `/home/joe/tcg/registry-vault/do_not_train_registry.bak-20261024-234503-gatefleet-pre.json` (sha = before) and `do_not_train_registry-20261024-234503-gatefleet.json` (sha = after), both hash-verified after writing.
- Independent confirmation: the analysis run (§2) passed its G9 registry gate against this merged registry — all 793 row gamenames found.

## 9. Teacher-time accounting

From the row files (fleet-diagnostics.json): 393 scored teacher games carry `secs`; their sum is **496,324.7 s** (≈137.9 worker-hours across the 4 chunk workers), mean **1,262.9 s per game**, median 1,192.4 s. The 7 timeout rows carry no `secs` — each burned up to the 3,870 s GATE_TIMEOUT outside that sum. Fleet wall clock: 2026-10-23 07:03:36 → 2026-10-24 20:32:59 EDT ≈ 37 h 29 m for 800 games. Final teacher-timeout rate statement: **7 of 400 teacher games (1.75%) hit the wall-clock timeout; the >2% INCONCLUSIVE stop does not fire** (§4).

## 10. Builder spot-checks

Run on the box by the builder (standing rule, 2026-10-23); commands and raw outputs verbatim — full text in `fleet-spotchecks.txt` (§11). All three match this report.

**(1) The Δ line recomputed from the row files** (python pass over `/tmp/ggate/gate_c*.jsonl`; teacher timeout rows score 0.0; scored row preferred over a marker row for a duplicate key):

```
400 216.0 213.0 0.0075 18.0
```

**(2) The teacher-timeout rate from the row files:**

```
7 400 0.0175
```

**(3) The post-merge registry:**

```
fc46f835cafefdca042457bc84b509af47e3f6ed28f63b453fde05261c225521  /tmp/harvest/do_not_train_registry.json
6161
```

## 11. Artifact index (path · sha256)

Staged analysis record (this package):
- `rounds/round7/fleet-registry-merge.json` · `6c66903cee5e5e3474e60b5a32ad0545f5ad7ed3ec0e4bec74b672a0c864ab80`
- `rounds/round7/fleet-diagnostics.json` · `3d98560338600b2cdea78e1618f507ab3a8de2eaf372ca04db0cf55f216547a1`
- `rounds/round7/fleet-analysis.json` · `ff031f321832423306820cb80852b5ba80cfee1271a3e1cdea3aedfe552d24dd` (script pins, both deployment diffs, full component stdouts, verbatim L2/L3 failures, all input hashes)
- `rounds/round7/fleet-spotchecks.txt` · `1b3f254d01dba874d3a37f99f40925cb172fbad599f7423cf53c0c4e093ac2ff`

Analysis scripts (staging pins; all verified before running):
- `rounds/round7/code/analyze_gate_gravy.py` · `d468468eac58a8f192335886ccb54dca6d2d36d28682089b03dc036d825247db` (matches the fleet-alignment pin; transferred to the box and run unedited)
- stock `analyze_gate.py` · `a5e2086677a69c6055a47de433ada1dfbf29f37e49264af6d4dab0e824277a6e`
- `l1_check.py` · `956923d06733aa1e93343b44ae8f2ccdf9e1a21f458f26fdf4119689acae1be1`
- `analyze_l3.py` · `16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9`
- `gate_first_divergence.py` · `9aaca15536332c856b8d69e377d7662170e783ef8708f61a47ec69155b0c541d`
- `classify_divergence.py` · `1518427bd4904a581fd2158b702b0e58e902b2cf1c64371f40da51c6fc7b0533`
- `audit_overturns.py` · `20853c435901ef725adcc604c69ddaa56a1670cc9c3175608f1d490332e610bb`
- `probe_swap20.php` (staging / gravytree) · `6993ece4f84bf2aea3540635c5b1cd8b2f0c9a787c0ed42cf426d4a3f8160243` / `400a921567b8739c8d88387e12ef75d2fb42587a53c1d5762b2db200a0bc5c2c`

Deployment copies (box, `/tmp/ggate/`):
- `l1_check_deploy.py` (O2) · `10c7d91e7a07bf6f45aa223b547efb9f36bf7527c20b4dfe50b174934e878c48`
- `analyze_l3_deploy.py` (O3) · `3919bbb80db29eec91c87e6f640e6eb689fa8324865fb450a69292843008dd72`
- `jobs_all.jsonl` (L3 jobs build) · `5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b`

Analysis outputs (box, `/tmp/ggate/`; full hashes in fleet-analysis.json):
- `primary_report.txt` · `7d3caea1…`
- `l1_output.txt` · `6cfa716e…`
- `g3_output.txt` · `fdae6a01…`

Row files (`/tmp/ggate/`):
- `gate_c1_teacher_s1.jsonl` · `12cac321c0beaf4c28885ff5a8364e526ebb720a59cdae8c5c69e91c796a4750`
- `gate_c1_teacher_s2.jsonl` · `a23772af39f98d014c2afbd0663b938c07fd38096aba2f1c56391dbe3aa7b176`
- `gate_c1_raw_s1.jsonl` · `04531a69b81da80439b3b1d366eab7adf44a8f5a8e7bf0ffc4ae6dbe4b6563b3`
- `gate_c1_raw_s2.jsonl` · `78c215c3a23dc96bdb7da01638ec66fa675966e16fb13acadcbf8173e90c634d`
- `gate_c2_teacher_s1.jsonl` · `605224c546941e60f5dfb085f9cd6830d75810e16b77788aeb127ed25e5eb9b4`
- `gate_c2_teacher_s2.jsonl` · `de1ccc9e35a36acaf7b9d3d67ac30ed9cd100ecd3e77cf63493987756b83bf01`
- `gate_c2_raw_s1.jsonl` · `e755b23bab82205784f3a928b11f6b77a5cb11e895c26505f05ef03fc9c75eeb`
- `gate_c2_raw_s2.jsonl` · `ea545d62f6bf4c6ed24124807495250cf2939934b7901fe6e6fe56a592612ce7`
- `gate_c3_teacher_s1.jsonl` · `49252c7b84a5b0e7c81ff9aa552c6f8e85241681d376d82cfdfd51176d2f9b0f`
- `gate_c3_teacher_s2.jsonl` · `9cc99687a28e89b3acc48009b45d471869142b363cf33ca7561872c3d87b633b`
- `gate_c3_raw_s1.jsonl` · `12c06bf017efd578831dfb4f9d3dde7eb534916b3a333d2b74c5d58bbcd4e73d`
- `gate_c3_raw_s2.jsonl` · `04f1302c6e5696875bc3dbca9dfdc55a2ad8faf5c2344e486969ecb0f0303884`
- `gate_c4_teacher_s1.jsonl` · `1563a9f0b1585483afb4bbf3792c9bc88d3e66afca7ab378b99dc5c78b14ed5e`
- `gate_c4_teacher_s2.jsonl` · `e2232a5f936cc47557537078a6a3284d2c55f8b8004b25ce46e8a4435d5ba8fa`
- `gate_c4_raw_s1.jsonl` · `3a97b84b0bb2e6cf1589b98eabed58829e2314a8b48d45fb75ab0069a0a52e3b`
- `gate_c4_raw_s2.jsonl` · `725629dc909db06f6edb28a9bfc4075b264ed690327e03d110f95293a4b4c26d`

Stat files (`/tmp/ggate/`):
- `gate_c1_teacher_s1_log/search_stats.jsonl` · `01941349eca03770faf2efae2ad3d7ea94eb27e0712ed5a316921083b673abfa`
- `gate_c1_teacher_s2_log/search_stats.jsonl` · `16c918162a7b3148534a4fc1a019cf1957c1b18fd3cc5044456f910e0c341411`
- `gate_c2_teacher_s1_log/search_stats.jsonl` · `31fd9455164bac925adc95c5d43bf54796e095996feae83f81841948ce4351ba`
- `gate_c2_teacher_s2_log/search_stats.jsonl` · `35e67c52ee1b59eebbac99eb2c98c12bf6b8041723f51472278061ba03ade87f`
- `gate_c3_teacher_s1_log/search_stats.jsonl` · `a13177c688d6ffe01c1e45e23e57183405280ef3634b8ee9cdbd5fc0e7da5566`
- `gate_c3_teacher_s2_log/search_stats.jsonl` · `98253b37cfb7c26f38d06ae4151ad931e87b580d931d8b99d392f92ec9d8ffda`
- `gate_c4_teacher_s1_log/search_stats.jsonl` · `54214c82662ca8a72ced0bf195d0b7acc31a7f2a6f8e6d00f4612927428fd87d`
- `gate_c4_teacher_s2_log/search_stats.jsonl` · `89d3988f94e0d614f3f004b2726de4a4e5712fa91fde7c9ca23c1d979e4a63a4`

Servers, containment, registry:
- `gate_shm_sweep.log` · `df6f2b3dc7327137829592928f132dafa4a657fda6453bfe34cca6490f151978`
- `gate_server_s1.log` · `c362790869df2f1c77608246227950c51908d9853b3225b51e45884dcf214d8e`
- `gate_server_s2.log` · `73109d6aed03acc7bbc6ef76898199677bc83f46f098e8ebc167a343a33fc59f`
- `/tmp/harvest/do_not_train_registry.json` (after merge) · `fc46f835cafefdca042457bc84b509af47e3f6ed28f63b453fde05261c225521`
- `gate_registry_merge.txt` (box merge note; hash in fleet-registry-merge.json)

## 12. Open items — what this report does not settle

- **The transfer ruling is Claude's.** This report is the record: the primary fails conversion and the transfer band under the registered bands, with the dilution diagnostics of §6 attached. Whether the round-7 question closes here or continues is not this report's call.
- **L2 and L3 remain open** (§7.3–7.4). Closing them requires the registered post-gate L-run — a measurement launch needing the full plan and code approved by Claude and Joe's own go. Given Δ ≈ 0 and the §6 diagnostics, whether that attribution is worth its cost is part of the same ruling. The L3 jobs file (118 jobs, §11) is built and waiting if it is approved.
- **Stage-3's C4 remains a non-inferiority bar.** Nothing in stage 3 showed PPO improving on the Gravy anchor, and nothing here changes that: v10 is this fleet's raw arm by the registered first-passer selection, and the teacher's parity here is parity against v10, not against a demonstrated-strong policy.
- **Scope (C5):** this fleet tests pipeline transfer — a second hero-specific policy built by the Fai pipeline's faithful replication — not a single hero-independent policy. The read does not speak to the hero-independent question.
- **Cost/distillation is untouched.** The teacher's cost profile on Gravy (mean 1,262.9 s/game, 31.7% thin-prior, §6/§9) is recorded here as the distillation line's input, nothing more.
- The 227 closing segments (§5) remain on the box as rule-3-kept parents; the next launch's pre-launch G8 sweep clears them as registered.
