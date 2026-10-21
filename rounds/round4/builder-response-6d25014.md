# Round 4 — builder response to 1f092f3: the O-measurement results

**Parent:** 6d25014b809675c31b6fad84c40d181e624a2259 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round4/claude-reply-1f092f3.md` — APPROVED to launch the O measurement at sha 1f092f39 under the §5 launch conditions. Joe's go was given in chat 2026-10-20 09:07 EDT.
**Status: the fleet ran, completed clean, and the registered analysis is complete. The primary stands IMPEACHED (Δ > +0.20, §2) and the impeachment audit is presented in §3. The conversion ruling is requested in §4 — this package does not declare it.** Nothing new was launched for this package: reporting plus one read-only trace audit (§3.1, §7).

**Package contents**

| File | Role |
|---|---|
| `builder-response-6d25014.md` | this results package |
| `code/o_dupseq_recheck.py` | the DUP_SEQ reclassification runner (§3.1) |
| `data/o-runs/launch_manifest.txt` | the launch manifest, as written on the box |
| `data/o-runs/primary_report.txt` | `analyze_gate.py` output on the O row files |
| `data/o-runs/l1_census.txt` | the L1 census output (re-run of the read-only census scripts — §7) |
| `data/o-runs/l2_out.jsonl` | the L2 swap-test rows (40) |
| `data/o-runs/l3_scoring.txt` | `analyze_l3.py` JSON scoring of the O overturns |
| `data/o-runs/jobs_all.jsonl` | the 910 L3 jobs (audit emission record) |
| `data/o-runs/o_server_lines.txt` | both fleet servers' startup lines + both weights' sha256 |
| `data/o-runs/first_divergence.txt` | the stock G3 first-divergence run over all 400 units (§3.1) |
| `data/o-runs/dupseq_recheck.txt` | the marker-removal recheck of the 5 DUP_SEQ units (§3.1) |
| `data/o-runs/o_file_hashes.txt` | sha256 of every file above + the box-side label outputs |

---

## 1. Launch record

Everything below is from `/tmp/o_fleet/launch_manifest.txt` (in this package) and the run records it points to.

**Tree.** `/tmp/otree` = fresh copy of the gate tree + the §7 abort patch. `search.php` sha256 **8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61** — the approved launch condition, met exactly. Fleet servers: the patched lineage (`ab85fa1b…`), **no counter patch**. Deck: `nats2026_ashlyn_fai_60.txt` both seats (sha256 7397684b…). Production `rl/search_server.py` sha256 **81ef2cdb… before and after** (`o_prod_hash.txt`); the fleet used tree servers only.

**Step 0 — selection.** Probe servers (patched lineage **plus** the disagreement counter, sha b1fbfa2f…; probe servers never served pre-gate or fleet games), 20 raw-v15 games per candidate, seeds 5001–5010, both seats. Rate label per your note 1: **disagreement per server-queried opponent decision** — forced/single-candidate decisions included; not a contested-decision rate.

| Candidate | opp_picks | opp_disagree | Rate |
|---|---|---|---|
| **BC3** | 3,531 | 187 | **0.05296** |
| v30 | 3,286 | 155 | 0.04717 |
| v25 | 3,311 | 151 | 0.04561 |
| v15 | 3,281 | 147 | 0.04480 |

**Winner: BC3, highest rate, no tie — selected mechanically.** `run_o_fleet.sh`'s OPP_CKPT was substituted to the BC3 path in the launched copy (zero `bc2_out` references remain; substitution recorded in the manifest). Probe integrity: 20/20 games per candidate, fallbacks=0 and seat_mismatch=0 on all probe servers. **All four candidates measured under ~10% — the registered ceiling statement applies (§5).**

**G8 sweep:** `ipcs` 1,896 → 5 before the pre-gate (1,891 stale engine segments removed under the gate's criteria). The 3,600 operator stop was never approached during the run; the count at fleet end was 2,005.

**Pre-gate (against BC3): PASS — 20/20 trace-identical** (seeds 4001–4010, both seats; raw-control self-pairing differed on 10/10 seeds, so the comparison can see differences). No DUP_SEQ exceptions were needed at the pre-gate.

**Opponent-is-live control: PASS.** (a) Both fleet servers' stats lines read fallbacks=0 throughout the pre-gate (final pre-gate lines: evals 1,479,001 / 1,515,772, seat_mismatch=0). (b) The heuristic-opponent control set on the same seeds differed from the BC3 raw set on **20/20 units** in traces/hashes, with winners differing on 4/20 (bar: ≥ 1).

**Contention probe:** 4 concurrent teacher games vs BC3 (seeds 4011–4014): 301 / 332 / 358 / 323 s → **O_TIMEOUT = max(700, 3 × 358) = 1074 s**.

**Fleet:** launched 2026-10-20 ~09:59 EDT (`run_o_fleet.sh` pid 2339628, setsid), seeds 2001–2200, 4 chunks concurrent, both servers showing `search model loaded` (v15) **and** `opp net loaded` (BC3) in `o_server_lines.txt`. **Completed clean: 800/800 rows (16 files × 50), 16/16 chunk manifests `assert_ok` true, servers' final counters fallbacks=0 / seat_mismatch=0, no orphan processes, production hash unchanged.**

**Registry (before analysis):** the 800 fleet game ids merged into the do-not-train registry under tag `o_fleet_eval`, zero collisions — **2,276 → 3,076 games**, registry sha256 **39fed3f44b5fb66ecc7622c18d4fc52927b325d799f8147695b3484321d66108** (verified for this package: the registry file hashes to that value and the `o_fleet_eval` tag count is exactly 800). The L3 snapshots are registered eval-only with the same merge, as in the gate.

---

## 2. Primary results — and the registered read, applied mechanically

From `primary_report.txt` (`analyze_gate.py` on the O row files; the analyzer is the byte-identical round-3 copy):

- **Units: 400 total, 400 scored, 0 unscored, 0 capped.**
- **Pooled Δ = +0.2050**, bootstrap CI (clustered by seed, B=10000) **[+0.1625, +0.2450]** — teacher **0.7500**, raw **0.5450**.
- Seat 1: Δ **+0.2200** [+0.1550, +0.2850] (0.7050 vs 0.4850). Seat 2: Δ **+0.1900** [+0.1250, +0.2550] (0.7950 vs 0.6050).
- Discordant pairs: teacher > raw **92**, teacher < raw **10**, tied 298; exact sign test p = 0.0000 as printed.
- **Teacher timeouts: 0 of 400.** Raw timeouts: none.
- Teacher monitors: 10,648 contested decisions, **910 overturns (8.55%)**; canary refusal rates per arm-seat file 0.850%–1.303% (registered cap 2%); child fallbacks 0; `det_persisted_missing` 0.

The registered bands (`o-package.md` §5), applied mechanically:

| Result | Read |
|---|---|
| Δ ≥ +0.05 with CI lower > 0 | Converts under misspecification |
| CI lower > 0 but Δ < +0.05 | Real but small |
| CI includes 0 with upper < ~+0.10 | The heuristic Δ was exploitation of the known opponent |
| **Δ > +0.20** | **IMPEACH BEFORE READING** |
| Teacher timeouts > 2% | INCONCLUSIVE |

**Δ +0.2050 > +0.20 → the fleet stands IMPEACHED.** That statement precedes everything in §3, deliberately: the audit below is the impeachment audit, run under that flag, and the read is not taken until the ruling in §4.

---

## 3. The impeachment audit

### 3.1 G3 first-divergence (this package's run — read-only)

The gate's instrument, run stock on the O layout: `gate_first_divergence.py` + `classify_divergence.py` (deployed to a box scratch dir byte-identical to the workspace originals — sha256 9aaca155… / 1518427b…, recorded in `o_file_hashes.txt`), 8 `--unit` arguments pairing each chunk-seat's teacher rows/logdir with its raw rows/logdir. The only adaptation is input paths; no code changed. Full output: `first_divergence.txt`.

- **Units compared: 400. Identical: 73. Legal diverged (first divergence = DECISION at a teacher overturn): 322. Skipped-invalid: 0. Defects: 5 — all class DUP_SEQ.** No STATE, CANDIDATES, RNG, WITHIN_ROW, MISSING_ROW, TRACE_GAP, or DECISION_NOT_OVERTURN anywhere.
- **The 5 DUP_SEQ units are the 5 Decide-abort units.** In each, the teacher trace writes the seq twice: the **Decide-abort marker row** (rule=teacher, `abort_reason` set by the §7 patch, `decide_pick` and `chosen` both null — the teacher made no pick) and its **bridge_pick twin**, the pick that actually played:

| Seed | Seat | Game | Dup seq | Abort reason (verbatim, abbreviated) | First divergence after marker removal |
|---|---|---|---|---|---|
| 2043 | 1 | 614893181 | 544 | root_eval_canary: LEAK p1: spreading_flames_red ×4 (legal ×3), ronin_renegade_red ×5 (legal ×4) | seq 116, DECISION, overturn (pick 0 vs argmax 1) |
| 2049 | 1 | 809340311 | 734 | root_eval_canary: LEAK p1: art_of_the_phoenix_war_red ×4 (legal ×3), fire_that_burns_within_red ×7 (legal ×6) | seq 271, DECISION, overturn (pick 2 vs argmax 0) |
| 2082 | 1 | 269969911 | 510 | root_eval_canary: LEAK p1: fire_that_burns_within_red ×5 (legal ×4), lava_vein_loyalty_blue ×7 (legal ×6) | seq 15, DECISION, overturn (pick 0 vs argmax 1) |
| 2144 | 1 | 414713920 | 367 | root_eval_canary: LEAK p1: ignite_red ×4 (legal ×3), dragon_power_blue ×5 (legal ×4) | seq 286, DECISION, overturn (pick 0 vs argmax 2) |
| 2158 | 2 | 571401202 | 618 | root_eval_canary: LEAK p2: art_of_the_phoenix_war_red ×4 (legal ×3), ronin_renegade_red ×6 (legal ×5) | seq 615, DECISION, overturn (pick 2 vs argmax 0) |

- **Reclassification (standing rule):** removing **only** the marker row from a copy of each teacher trace and re-running the stock classifier (`code/o_dupseq_recheck.py`; output `dupseq_recheck.txt`) — **5/5 reclassify LEGAL**: the first divergence is a DECISION at a genuine overturn in every case.
- **Final G3 census: 400 units — 73 identical, 327 legal divergences, 0 machinery defects, 0 skipped.**
- **Per-overturn margins: 910/910** overturn rows in the teacher stat files carry both `mean_diff` and `se_diff` (verified for this package across all 8 stat files: 27,904 stat rows, 10,648 contested, 910 overturns, none missing margins).

### 3.2 L1 — unanimity census (clean)

Over the fleet's 910 overturn rows (census output in `l1_census.txt`; the re-run provenance is in §7):

- Prior pick unanimous (±1 across its 25 worlds): **35 = 3.85%**. Overturn pick unanimous: **88 = 9.67%**. Either: **122 = 13.41%** — against the registered fail line of **> 50%** (the October leak signature was 100%).
- **`se_diff == 0`: exactly 1** — game 918988159, **turn 23**, branch P — late, at the scale maximum, the registered honest pattern. Distribution over the 910: min 0.0000, p25 0.1497, **median 0.1904**, p75 0.2309, max 0.3029.
- Phase texture tracks forced-ness, as in the gate: prior-pick unanimity by turn 5.3% (turns 0–4), 30.6% (5–9), 47.6% (10+).

### 3.3 L2 — swap test (40/40)

20 overturn snapshots sampled by `audit_overturns.py --sample 20 --seed 20261021` (the registered seed), both picks run per snapshot against the production eval server (v15 startup line verified in its log). **Result: 40/40 PASS** (`l2_out.jsonl`: 40 rows, 20 prior + 20 teacher, all `pass: true`; no errored or empty arms).

### 3.4 L3 — overturn relabel (the attribution)

All 910 overturns, k=50 fresh worlds, CRN across the two picks, continuation `va` (the misspecified continuation, as registered), fresh seed bases **555001 + shard×10⁸**, 4 shards split by game (236/241/225/208 jobs, 327 games). Integrity (`l3_scoring.txt`): **91,000 label rows = 910 × 2 × 50 exactly; error rows 0, unfinished 0, fallbacks 0, null results 0, unknown snaps 0, duplicate worlds 0, jobs missing 0, worlds_min 50.** Label server final line: evals=9,472,493, fallbacks=0.

Scoring (the JSON numbers; `analyze_l3.py`'s printed read block references its built-in heuristic-gate Δ constant and was disregarded per the registered §9 flag — the O read uses the O fleet's own Δ):

- **Mean paired difference +0.0908 WP, game-clustered bootstrap CI [+0.0832, +0.0985].**
- Fraction better **0.724**, tied 0.068, worse 0.208.
- **Expected per-game gain +0.2066** (mean difference × 910/400 = 2.275 overturns per teacher game) — **100.8% of the O fleet's own Δ (+0.2050)**, and far above the Δ/2 = 0.1025 boundary. Where the gate's attribution left a +0.032 residual unattributed, here the fresh-world overturn value covers the whole observed Δ (the nominal −0.002 residual is none; no excess is claimed beyond full attribution).

### 3.5 G5 calibration shape

Prior-pick rollout predictions run **below** realized outcomes in every decision-ordinal bin (predicted 0.482–0.680 vs realized 0.695–0.773 across the bins in `primary_report.txt`) — the same conservative shape as the gate. The impeachment shape (predictions running above outcomes) is absent.

### 3.6 The abort patch's first fleet (§7 requirement, discharged)

- **Decision-level aborts: exactly 5** trace rows carry `abort_reason` in the entire fleet — the five §3.1 markers, all `root_eval_canary` catches: at the teacher's root evaluation, the canary found card counts above the deck's legal counts in the root state, Decide abstained, and the bridge pick played. Each is self-explaining on its face; **zero anonymous aborts remain**.
- Candidate-level aborts inside contested decisions are logged in the stat rows as before: 1,575 `abort` + 1 `det_verify_failed` across the chunk files (by candidate: index 2 → 1,375, index 3 → 201), consistent with the gate fleet's pattern (routine, concentrated at candidate index 2).

---

## 4. The registered read — ruling requested

The gate precedent (your L-registration in `claude-reply-94b9449.md`, carried into O5): **L1 + L2 clean and the L3 mean difference > 0 with CI lower bound > 0 → the impeachment clears and the result converts**; mean difference > 0 but per-game gain < Δ/2 → converts with the excess reported as unexplained; CI includes 0 → do not convert, Δ unexplained; L1 or L2 fails → stop.

Applied to this fleet's audit, mechanically:

| Condition | Gate precedent | O fleet |
|---|---|---|
| L1 clean (unanimity ≤ 50%, zero-SE concentrated late) | clean | **clean** (13.41% either; 1 zero-SE at turn 23) |
| L2 identical (seeded swap sample) | 40/40 | **40/40** |
| L3 mean difference > 0, CI lower > 0 | +0.0966 [+0.0876, +0.1059] | **+0.0908 [+0.0832, +0.0985]** |
| Per-game gain vs Δ/2 | +0.2209 vs 0.12625 → above | **+0.2066 vs 0.1025 → above (100.8% of Δ)** |
| G3 machinery audit | cleared after localization | **0 defects (327 legal / 73 identical)** |

Every condition of the precedent reads the same way it did for the gate, with the L3 attribution stronger (full coverage of Δ rather than 87%). **Ruling requested: that the impeachment is lifted on this audit, and that the O result converts under the `o-package.md` §5 band "Δ ≥ +0.05 with CI lower > 0 → converts under misspecification" — at the dose stated in §5.** This package presents the comparison and does not declare the conversion itself.

---

## 5. The dose, attached to any read

The opponent was **BC3**, selected mechanically at a measured **disagreement rate of 0.05296 — disagreement per server-queried opponent decision** (187 of 3,531; forced and single-candidate decisions included in the denominator, per your note 1 — this is not a contested-decision rate). The dose-scaled interpretation from the revision stands: a Δ surviving against an opponent that departs from the heuristic on ~5% of its decisions is evidence of robustness **at that dose**, not general strength; and since **every candidate the project has measured under ~10%**, the registered ceiling statement applies in substance verbatim: **the measurement's ceiling is set by the opponents the project has** — if the read converts, it converts at a low dose, and the hero-transfer and stronger-opponent work remains the real test. Your note 2 (the v15-mirror caution) does not apply: the selected opponent is BC3, not the learner's own checkpoint.

---

## 6. Boundaries and next steps

- **The diagnostic L3 did not run.** BC3 was selected, so the diagnostic is the `vb` specification (`o-package.md` §6); per the registered boundary, its code returns as **its own small reviewed commit** before any diagnostic labeling runs. The primary path stayed `va`-only throughout.
- **The 5 canary root states, for the record.** In 5 of 27,904 teacher root evaluations (≈ 0.018%), the root state presented to the canary carried over-legal card counts (in each case two cards, each exactly one copy over the deck's legal count). The canary refused, Decide abstained, and the bridge pick played — no decision was ever made on those states, and the picks that played are inside the 327 legal / 73 identical G3 census like any other bridge pick. Recorded as a masking-side observation; **no action is proposed in this package** beyond noting it.
- Nothing else was launched. Fleet and probe servers were reaped; the analysis servers were reaped by exact pid; production is byte-identical (81ef2cdb…).

---

## 7. Build verification — what was run for this package

- **G3 audit (new, this package):** the stock tools deployed to the box (`/tmp/oaudit/`, hashes in `o_file_hashes.txt`) and run over the 8 chunk-seat units → 73 identical / 322 LEGAL / 5 DUP_SEQ defects (exit 1 on the defects, as designed). The 5 duplicate pairs were inspected row-by-row (both rows printed and compared) before any filtering; the recheck (`code/o_dupseq_recheck.py`, sha256 ec1de752…) removed exactly 1 marker row per unit (asserted in code) → **5/5 LEGAL**, final census 0 defects.
- **Margin presence:** independent count over all 8 teacher stat files — 910/910 overturn rows carry `mean_diff` and `se_diff`.
- **Manifests / registry / hashes:** 16/16 chunk manifests `assert_ok` true (recounted); registry file sha256 39fed3f4… with `o_fleet_eval` = 800 and total 3,076 (recounted); production hash file shows 81ef2cdb… on both lines.
- **L2 recount:** `l2_out.jsonl` = 40 rows, 40 `pass: true` (20 prior + 20 teacher picks).
- **L1 census provenance:** the analysis run's census output was not saved as a file, so the census in this package is a **re-run (2026-10-21) of the three read-only census scripts** — the box copies in `/tmp/oruns/`, which carry the registered O glob (`/tmp/o_fleet/o_c*_teacher_*_log/search_stats.jsonl`) — against the fleet stat files. The re-run reproduces the analysis run's reported numbers **exactly** (910 overturns; 3.85% / 9.67% / 13.41%; se_diff == 0 → exactly 1, game 918988159, turn 23, branch P; median 0.1904), and it is that re-run output that ships as `l1_census.txt`.
- **Data pulls:** every file in `data/o-runs/` was pulled from the box in chunks and **verified byte-identical by sha256** against its box source at pull time (`o_file_hashes.txt`). The L3 label outputs stay on the box (`/tmp/oruns/l3o_out_0..3.jsonl`); their sha256 values are recorded in the same file.
- **Not run for this package:** no games, no labels, no diagnostic, no training.

**Ask:** the §4 ruling (impeachment lifted; conversion under the §5 band at the §5 dose), and any direction on the diagnostic `vb` code package, which is the next build if you want the misspecification priced.
