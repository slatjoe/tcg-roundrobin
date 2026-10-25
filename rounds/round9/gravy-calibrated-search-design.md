# Round 9 — Gravy-calibrated search: design for review

**Parent:** 263e4953 (round 8 closed; round 7 closed and independently verified at 939f65e0).
**Status:** DESIGN FOR REVIEW. Nothing is built, run, or launched. Approval of this design leads to a build package (code, hash-pinned, per the measurement-build approval rule); any run then needs Joe's explicit go in chat, stage by stage.
**Direction:** Joe, 2026-10-25 19:40 EDT ("Take the road"), accepting the builder's verdict that the next fork is a Gravy-calibrated search round rather than a value-target distillation (the round-8 closure's future lines — value-based targets, stochastic serving — are separate registrations and are not this round; `rounds/round8/claude-reply-5556677.md`).

## 1. The question, stated as a confound to resolve

Round 7's fleet (`rounds/round7/fleet-report.md`) read **Δ +0.0075, bootstrap CI [−0.0138, +0.0288] — does not convert**. The ruling (`rounds/round7/claude-reply-9fb0e98.md`, verified at 26290bb / 939f65e0) scoped that null precisely: it is a finding about **this teacher configuration** on Gravy — bounds sized for Fai — not about search on Gravy. The confound is in the fleet's own numbers:

- The teacher ran with **Fai-sized bounds**: k=25 worlds per candidate, a **4,000-hook budget** per rollout, **180 s candidate deadlines**, a ≥20-finished-world validity floor, overturn at 1.5 paired SE (`search.php` sha256 `8f6b35da…`, fleet-alignment §4).
- Gravy's mirror is **bimodal**: ~21% of games do not terminate at any cap (intrinsic draw share H′ = 0.2117 [0.1958, 0.2285]; fleet capped share 0.21563); the corpus-capped median end-turn is **142**, mean 285.9. Fai games end long before any of these bounds can bind.
- Result: **thin-prior on 2,988 of 9,429 contested decisions = 31.7%** — the search never reached its own validity floor and the prior pick played unsearched. The Fai fleets measured thin-prior **0 of ~21,500**. A further 37,038 candidate aborts were recorded across contested rows. Where the search did complete, it rarely cleared the bar: non-thin overturn rate **118 / 6,441 = 1.83%**, against Fai's 12–16%.

So most contested Gravy decisions were never really searched, and the fleet's null cannot distinguish "search has no edge on Gravy" from "this search never ran." **Round 9 asks, in order: (i) do the old teacher's overturns — where it did fire — carry a real per-decision edge (Stage 0); (ii) what bounds make the search actually complete on Gravy states, and at what price (Stage 1); (iii) does a search calibrated to Gravy's horizons earn a per-decision edge over raw v10 (Stage 2); and only then (iv) whether that edge converts at game level (Stage 3).**

## 2. Scope and claim discipline

**Scope sentence:** round 9 tests a per-hero calibrated search on the Gravy PPO v10 lineage, mirror vs heuristic — a pipeline-transfer question, not a hero-independent policy.

- **Fixed throughout:** the policy (selected Gravy PPO checkpoint `ckpt_v10.pt`, sha256 `44f1e5d7…`; no retraining, no new checkpoint), the deck (mirror, `decks/nats2026_eriksen_gravy_60.txt`, sha256 `b8b41390…`), the opponent (the heuristic), the instrument (turn-cap parameter **87** / draw trigger **62**; capped games score as draws at 0.5), the candidate rule (top-3 priors + any prior ≥ 0.10, cap 4), the validity floor (≥20 finished worlds), the overturn rule (paired margin > 1.5 × paired SE), continuation `va`. **The only thing that moves in this round is the search's resource bounds** — that is what "calibrated" means here.
- **Claim discipline: no stage's read licenses the next stage's claim.** A Stage-0 edge does not imply a calibrated search has one; a Stage-1 completion rate does not imply an edge; a Stage-2 per-decision edge does not imply game-level conversion. Each stage's launch registration states its own claim, and each stage after Stage 0 launches only on the previous stage's read plus its own approval and Joe's go.
- **Out of scope:** any change to the policy or its training; value-based or stochastic teacher-to-policy lines (new registrations per the round-8 closure); the parked stalemate-breaking and clock/standings questions (the fleet's non-win co-report, +0.0250 [+0.0025, +0.0500], stays an observation, not a result, and is not a round-9 claim); any hero other than Gravy Bones; any opponent other than the heuristic.

## 3. Stage 0 — L3 on the round-7 fleet's overturn decisions

**This is the registered first measurement of any Gravy-search round** (`claude-reply-9fb0e98.md`: L3 was not run in round 7; the jobs file was kept; any future run needs its own registration — this section is that registration).

### 3.1 Population and instrument

- **Jobs file (verified on the box, 2026-10-25):** `/home/joe/tcg/registry-vault/jobs_all_gravy_fleet_l3.jsonl` — **118 rows, 79,408 bytes, sha256 `5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b`** (identical to the fleet report's build hash). Built by `audit_overturns.py --sample 100000 --seed 20261023` from the fleet's snapshot index — the fleet's **full** overturn population, not a sample.
- **Population:** 118 overturn decisions over **88 distinct fleet games**, both seats (player 1: 58 jobs, player 2: 60), branches P 63 / M 27 / B 15 / ARS 11 / D 2. Every job is a decision where the old (Fai-bounded) teacher overrode v10's prior pick and the fleet played the teacher's pick.
- **Instrument (as built in the round-7 package):** `meas_label_main.php` (sha256 `3109176b…`) at **LABEL_W = 50** fresh determinized worlds per candidate, worlds shared across the two candidates (CRN), continuation `va`, fresh label seed bases **855001 + shard × 10⁸**, 4 shards by game hash, on the **production server** (the patched server rejects the label path's seat-0 requests, R12 — label work uses the production server, standing rule). Scored by `analyze_l3.py` (sha256 `16017ffa…`) in a deployment copy with DELTA set to the fleet's measured Δ (**+0.0075**, replacing the Fai constant 0.2525) and TEACHER_GAMES = 400; the substitution diff and hash are recorded in the run record (the O3 pattern).
- **What L3 is (round-3/4 definition, unchanged):** for each job, fresh paired worlds — independent of the worlds the decision itself used, so the audit does not inherit the winner's curse — score the teacher's pick against the prior's pick. World score = (outcome + 1)/2 over finished worlds. **Primary: mean paired difference** (teacher pick − prior pick, win probability), CI from a bootstrap clustered by game. Secondary: fraction better / tied / worse. **Per-game gain = mean difference × overturns per teacher game.**

### 3.2 The read, and what each outcome implies

The denominator is fixed by the fleet: 118 overturns / 400 teacher games = **0.295 overturns per teacher game**, against Fai's 2.29. Stage 0 therefore measures the **conditional quality** of the old teacher's rare fires; its per-game gain will be small even if the conditional edge is Fai-sized, and with Δ ≈ 0 there is no meaningful "share of Δ" — Stage 0 is **not** an impeachment of the fleet (there is nothing to impeach) and must not be reported as one. Registered reads:

- **Mean diff > 0, CI lower > 0 (Fai-like magnitude, ~+0.09):** the overturns that fired were real. The fleet's failure was **coverage** — the search rarely ran and rarely fired — and Stage 1 proceeds as designed in §4: completion is the lever, and the grid stays bounds-only. (Reference magnitudes: Fai gate L3 **+0.0966 [+0.0876, +0.1059]**, per-game +0.2209 over 915 jobs; O-fleet L3 **+0.0908 [+0.0832, +0.0985]**, per-game +0.2066 over 910 jobs.)
- **Mean diff > 0 but CI includes 0, or mean diff ≈ 0:** at k=25 on Gravy-length, high-variance worlds, the fires that cleared 1.5 paired SE do not reproduce on fresh worlds — the winner's-curse pattern round 8 measured on Fai labels (V1-ov 0.167 at k=25). The implication for Stage 1 is direct: bounds alone may not be the binding problem, and **worlds per candidate (k)** becomes a candidate calibration axis. Whether k enters the Stage-1 grid on this outcome is decision **D6** (§9) — it is registered here, before Stage 0 runs, so the contingency is not invented after the read.
- **Mean diff < 0:** the old teacher's fires were harmful on Gravy. Calibrating bounds around the same decision rule is not supported; the builder's recommendation on this read is to close the round at Stage 0 and report, with any successor (a different overturn rule, a value-target line) as a new design.

At LABEL_W = 50 over 118 jobs the pooled per-overturn standard error is roughly ±0.01 (the ruling's estimate) — enough to separate these three reads.

### 3.3 Stage 0 cost

118 jobs, no new games, no registry change (label worlds are fresh seeds, §3.1). Per-job cost from round 8's measured label costs on **Fai** states — stated as references, not Gravy measurements:

| Basis | Per job | × 118 jobs (serial) |
|---|---|---|
| Round-8 pilot labeler, k=25-class, mean (1,194 jobs) | 4.3 s | ≈ 507 s ≈ **8.5 min** |
| Same, p95 | 8.6 s | ≈ 17 min |
| Round-8 W=100 check, mean — **upper-bound reference** | 45.8 s | ≈ 5,404 s ≈ **90 min** |

Gravy worlds run longer than Fai worlds, so the Fai figures are a floor, not an estimate; the planning range, stated as a range, is **0.15–1.5 box-hours serial**, minutes-to-~25-minutes of wall across the 4 shards. Even at ten times the pilot mean the stage stays under ~1.5 box-hours. Stage 0 is the cheapest measurement in the round by an order of magnitude.

## 4. Stage 1 — Calibration

**Question:** which resource bounds make the search actually complete on Gravy states, and what does each candidate setting cost per decision? Stage 1 measures completion and cost. It measures no edge and licenses no edge claim.

### 4.1 State source — fresh capture primary, fleet snapshots not used for selection

- **Primary: fresh capture games.** 40 raw-v10 games vs the heuristic at the registered instrument (parameter 87 / trigger 62), mirror deck, seeds **21001–21040** (proposal, §9 D2; seat 1: 21001–21020, seat 2: 21021–21040), played with snapshot capture at every contested decision (top prior < 0.97 — the teacher's registered contest rule), the round-8 capture pattern. These are **teacher-root states**: the states at which the teacher would be consulted, on the trajectory distribution v10's own play produces.
- **The panel:** the first **240 contested snapshots** from the capture, stratified across games (cap 8 per game) and reported by branch, so one long game cannot dominate the calibration. Fleet scale says this is comfortably available (the fleet's teacher games carried 9,429 / 400 ≈ 23.6 contested decisions per game; 40 capture games should yield ~900). If the capture yields fewer than 240, capture extends in 10-game blocks (seeds 21041+) until the panel fills — a sizing contingency registered here, not a mid-run improvisation.
- **Round-7 fleet snapshots: not used for selection, for two stated reasons.** (i) The durably vaulted fleet snapshot population is the 118 overturn snapshots behind the Stage-0 jobs — states **conditioned on the old teacher having overturned under the old bounds**, a selected subset that would bias any completion comparison. (ii) The fleet's full snapshot directories live under `/tmp/ggate` — tmpfs, not a durable registered artifact; a calibration that must be re-runnable cannot rest on them. The fleet's published thin-prior rate (31.7%) is used only as a **comparability reference** for the baseline setting's panel read (§4.3), not as panel data.

### 4.2 The grid

Two bounds plausibly bind on Gravy, and the fleet record shows both signatures (rollout children dying on the hook budget — the `abort` class — and candidates dying on the 180 s deadline with 15–22 of 25 worlds finished). The grid is factorial so the binding bound identifies itself:

| Setting | Hook budget | Candidate deadline | Worlds k |
|---|---|---|---|
| B0 (fleet baseline, control) | 4,000 | 180 s | 25 |
| H1 | 8,000 | 180 s | 25 |
| H2 | 16,000 | 180 s | 25 |
| D1 | 4,000 | 360 s | 25 |
| HD1 | 8,000 | 360 s | 25 |
| HD2 | 16,000 | 360 s | 25 |

- **k is fixed at 25** in this grid: it is the registered teacher configuration in every converted measurement to date, and the round's question is whether the bounds that were sized for Fai's horizons — not the world count — are what starved the Gravy search. The registered exception is D6 (§9): a null Stage-0 read is the pre-stated argument for admitting k, decided by the reviewer before Stage 1 launches, not by the builder mid-stage.
- **Everything else fixed:** candidate rule, validity floor ≥20, overturn at 1.5 paired SE, continuation `va`, the 400 drive-step guard and the stuck counter (> 60) — the guard and stuck counter are named as *not* swept: the fleet record's aborts are recorded against the hook budget, and sweeping four axes on a 240-state panel would spend the stage's precision on interactions it cannot resolve. If no grid point qualifies (§4.4), the guard/stuck axes are named candidates for a reviewer-registered extension — they do not enter silently.
- **Evaluation form:** each panel state is evaluated under **all six settings** (ghost/label-style offline evaluation from the snapshot, production tree + production server per the label-path rule), paired by state across settings with common determinization seed bases where the machinery allows, so setting differences are within-state comparisons. **Sequencing:** B0 runs on the full panel first — it is the control and it prices the sweep (the round-7/8 planning lesson: smoke means understated production costs ~2× or worse, twice). The remaining five settings' launch registration carries B0's measured cost distribution.

### 4.3 Measures per setting

- **Thin-prior rate** (primary): fraction of panel states where the prior candidate fails the ≥20-finished-world floor — the fleet's 31.7% is the number to beat, on panel states. B0's panel rate is reported beside the fleet's 31.7% as a comparability check (different population — raw-trajectory roots vs the fleet teacher's own trajectory — so agreement within sampling noise is a sanity read, not an identity).
- **Overturn rate** among non-thin states, and finished worlds per candidate (mean / p95) — whether completion converts into fires at all.
- **Per-decision cost: mean AND p95 AND max wall**, plus error/abort counts by class. The standing lesson is registered here as a requirement, not a preference: no setting is priced on its mean alone (the contention probe's median decision wall was 32.3 s with max 88.2 s; the pre-gate's completed searches ran ~16–18 s mean against ~35–38 s for the ones that thinned).

### 4.4 Registered selection rule (proposal — the bar is the reviewer's to settle, D1)

**The calibrated setting is the cheapest setting — lowest mean per-decision wall; ties broken by lower p95, then lower max — whose pooled panel thin-prior rate is ≤ 5%.**

- At ≤ 5%, at least 95% of contested decisions receive a real search; the round-7 confound is closed by construction rather than by argument. (Fai's fleets ran at 0%; 5% is proposed for Gravy because his non-terminating mode may make the last few points of completion buyable only at fleet-killing cost — §6's arithmetic is where that trade is priced.)
- **If no setting qualifies:** Stage 1 reads **NO CALIBRATED SETTING IN GRID**. The round stops there; any grid extension (larger bounds, k, the guard/stuck axes) is a new registration by the reviewer. There is no silent extension and no "closest setting" fallback — a fleet run at a setting that leaves the confound alive would repeat round 7 at higher cost.

### 4.5 Stage 1 cost

The capture is 40 raw-speed games — not the cost driver. The sweep is: 240 states × 6 settings = **1,440 search evaluations**. Measured Gravy per-decision search walls from the record (pre-gate completed ~16–18 s mean; pre-gate thinned ~35–38 s; contention probe median 32.3 s / max 88.2 s) give a planning mean of **25 s (labeled extrapolation)**:

- At 25 s: 1,440 × 25 s = 36,000 s = **10.0 box-hours serial** (≈ 2.5 h wall across 4 trees).
- Range: at 18 s → 7.2 box-hours; at 38 s → 15.2 box-hours.
- Higher settings cost more per evaluation by design — that gradient *is* the measurement, and B0-first sequencing (§4.2) replaces this extrapolation with B0's measured distribution before five-sixths of the spend is committed.

## 5. Stage 2 — L3 on the calibrated teacher

**Question:** under the Stage-1 calibrated setting, do the teacher's overturns earn a per-decision edge over raw v10 on fresh worlds? Stage 2 is the round's decision measurement; Stage 3 exists only if Stage 2 converts under the bands registered here.

### 5.1 Form

- **Fresh games:** the calibrated teacher (v10 + Stage-1 setting, nothing else changed) plays **200 games** vs the heuristic, Gravy mirror, registered instrument, seeds **22001–22100 × both seats** (proposal, D2) — a block that collides with nothing used (checked in §9). Capped games score as draws at 0.5 for the co-reported game outcomes; the games' purpose is to generate on-policy decisions under the calibrated bounds.
- **Capture and audit:** every overturn decision is captured (snapshot + candidate set + priors, the fleet's capture discipline); L3 jobs are built for **all** overturns (`audit_overturns.py --sample 100000` form) and labeled exactly as Stage 0 — LABEL_W = 50, CRN across the two candidates, continuation `va`, production server — with **fresh label seed bases 955001 + shard × 10⁸** (proposal; the 555001 / 777001 / 855001 families are spent).
- **Read:** mean paired difference + game-clustered bootstrap CI (primary); fraction better / tied / worse; **per-game gain = mean difference × (overturns / 200 teacher games)**; co-reports: the calibrated teacher's thin-prior rate and overturn rate in live play (against Stage 1's panel predictions — a calibration that does not reproduce in live play is itself a finding), and the games' draw-scored outcomes beside the fleet's.
- **Expected job count (labeled extrapolation):** at the fleet's contested rate (23.6 / game), 200 games yield ~4,700 contested decisions; at thin ≤ 5% and the fleet's non-thin overturn rate (1.83%), ~85 jobs; if completion raises the overturn rate toward Fai's 12–16%, several hundred. The L3 pooled precision at ~100 jobs and W = 50 is ≈ ±0.01 (the ruling's estimate at 118 jobs); the launch registration restates precision from the actual job count before the read is taken.

### 5.2 Registered bands for proceeding to a fleet (proposals, D3)

Anchored by analogy: Fai's L3 magnitudes (mean diff +0.0966 / +0.0908; per-game gains +0.2209 / +0.2066, which were 87% and 100.8% of their fleets' Δ) and round 7's fleet precision (800 games read Δ with CI half-width ≈ 0.021).

- **PROCEED to Stage 3 registration:** mean paired diff > 0 with **CI lower bound > 0** AND **per-game gain ≥ +0.05**. Rationale for the floor: if the Fai pattern (per-game gain ≈ fleet Δ) carries, +0.05 projects a fleet Δ that round-7-scale precision can actually resolve; a smaller true edge would need a much larger fleet to read, and pricing that fleet is a different decision than this round registered.
- **DOES NOT PROCEED:** mean diff > 0 but CI includes 0, or per-game gain < +0.05. The calibrated search's edge is not shown large enough to price a fleet against. The round closes with a complete per-decision result; resizing Stage 2 is a new registration, not an automatic extension.
- **STOP:** mean diff ≤ 0. Calibrated overturns carry no per-decision edge — bounds were not the binding problem — and the round closes at Stage 2.
- **Integrity tripwire:** per-game gain > +0.25 (the Fai Δ scale) or mean diff > +0.20 triggers L1/L2-form impeachment checks **before** any proceed read is taken. An audit that is only run on believable numbers is not an audit.

### 5.3 Stage 2 cost

- **Teacher games:** 200 × the calibrated per-game cost — **not knowable until Stage 1 prices the setting**, and Stage 2's launch registration sizes it from Stage 1's measured per-decision distribution × the fleet's decision rates. Floor reference at the old bounds: 200 × 1,262.9 s (fleet teacher mean, 393 scored games) = 252,580 s ≈ **70 box-hours serial** (~18 h wall at the fleet's 4-chunk parallelism) — the calibrated setting costs more per decision than the floor by whatever factor Stage 1 measures.
- **L3 labeling:** ~85–500 jobs (extrapolated range, §5.1) × 4.3 s (pilot k=25-class mean) ≈ **6–36 min serial**; at the W=100 upper-bound reference (45.8 s/job) the 500-job end is ≈ 6.4 box-hours. Labeling is not the stage's cost risk; the teacher games are.

## 6. Stage 3 — Gate fleet (conditional; NOT pre-committed)

Stage 3 exists in this package as a **band structure and a form**, nothing more. It launches only if Stage 2 reads PROCEED (§5.2), and its own launch registration — seeds confirmed, timeout re-derived from a contention probe at the calibrated setting, cost priced from Stage 1–2 actuals — follows Stage 2's reads through the same approval path as every fleet before it.

- **Form (round 7's, verbatim in structure):** paired calibrated-teacher vs raw v10, Gravy mirror vs the heuristic, registered instrument (parameter 87 / trigger 62), **200 paired seeds × both seats × both arms = 800 games**, 4 chunks, draw-scored primary (capped = draws at 0.5), fallbacks = 0, registry merge before analysis. Proposed seed block: **23001–23200** (D2).
- **Timeout and fallback rules as in round 7:** teacher-arm wall-clock timeout = teacher loss (primary) with a drop-the-pair sensitivity table; raw-arm timeout = one re-run, a second hang scores raw 0.5 and keeps the pair; **teacher timeouts > 2% of teacher games → the fleet reads INCONCLUSIVE** (round 7 final: 7/400 = 1.75%, stop not fired — read on final counts, never interim rates). The fleet timeout value itself is **not** inherited from round 7's 3,870 s: it is re-derived by the contention-probe formula at the calibrated setting in Stage 3's own registration.
- **Bands (by analogy to the Fai gate and round 7's read):** pooled paired Δ (calibrated teacher − raw v10): **CI lower bound > 0 → converts**; **CI includes 0 → does not convert**; **Δ > +0.25 → impeach before reading** (L1/L2-form checks and the Stage-2 L3 carried forward as the attribution read: per-game gain as a share of Δ, as the Fai gates reported 87% and 100.8%).
- **Cost (planning arithmetic only, from the record):** the raw arm is raw-speed. The teacher arm at the *old* bounds cost 400 × 1,262.9 s = 505,160 s ≈ **140 box-hours serial** (fleet wall 37.5 h over 4 chunks, against an 18 h estimate — the planning lesson is part of this round's record, not a footnote). The calibrated arm multiplies the per-decision cost by Stage 1's measured factor: at an illustrative 2×, the teacher arm is ~280 box-hours / ~75 h wall. **That multiplication is exactly why Stage 3 is not pre-committed:** Stage 2's proceed read and Stage 1's price arrive together, and the fleet decision is made with both in hand.

## 7. Cost summary (measured numbers from the record; extrapolations labeled)

| Stage | Driver | Arithmetic | Serial box-hours |
|---|---|---|---|
| 0 — L3, old teacher | 118 jobs (existing file) | 118 × 4.3 s (pilot mean) to 118 × 45.8 s (W=100 upper bound) | **0.15–1.5** |
| 1 — Calibration sweep | 240 states × 6 settings = 1,440 evaluations | 1,440 × 18–38 s (measured Gravy per-decision walls); 25 s planning mean | **7.2–15.2** (10.0 at planning mean) |
| 2 — Calibrated L3 | 200 teacher games + ~85–500 label jobs | games: ≥ 200 × 1,262.9 s at the old-bounds floor, × Stage 1's measured factor; labels: jobs × 4.3 s (≤ 45.8 s upper bound) | **≥ 70** (games) + 0.1–6.4 (labels) |
| 3 — Gate fleet (conditional) | 400 calibrated-teacher games + 400 raw games | 400 × 1,262.9 s at old bounds = 140.3; × Stage 1's factor (illustrative 2× → ~280) | **~140–280+** |

Sources: fleet teacher mean 1,262.9 s/game and 37.5 h wall (`fleet-report.md`); round-8 pilot label costs 4.3 s mean / 8.6 p95 / 52.6 max per job and W=100 check 45.8 / 90.6 / 115.4 (`rounds/round8/pilot-report-final.md`, `wcheck-report.md`); Gravy per-decision walls (pregate-report.md §ghost analysis; fleet-alignment.md §3.3). No number in this table comes from a smoke or a single-state probe.

## 8. Standing disciplines carried into every stage

- **Measurement-build approval:** each stage's full plan and code go to Claude for approval before launch; launched sha == approved sha (or differs only under `rounds/`); the run manifest records both. Joe's explicit per-stage go in chat is separately required — approval of this design launches nothing.
- **SHM / containment:** (C) kernel-attribution sweeper (`code/shm_sweep.py`, sha256 `98027a8b…`, with the fail-safe KEEP on missing/≤0 pids) pointed at the run tree's Games/ dir; pre-launch G8 sweep before every launch; the operator segment stops as registered in the machinery (abort check at 2,800; 3,600 = operator stop). Any label work runs on the production tree with (C) pointed at that tree, per the round-7 ruling's L-run conditions.
- **Registry:** every game any stage plays is merged into the do-not-train registry (current: 6,241 games, sha256 `28b5acfa…`) before that stage's analysis; seed blocks are excluded from every corpus and training input thereafter. Label worlds use their own seed-base families (§3.1, §5.1) and never collide with game-seed blocks.
- **Fair play:** observation masking and the hidden-information canary (coverage form) unchanged; local Talishar only, never public queues; `DeleteCache` before parsing any copied snapshot; the store:=view checkpoint sync is load-bearing and untouched. The (b) featurizer correction is **not** in this round — v10 was trained and gated under the current featurizer, its teacher roots measured 0/647 disagreements, and changing the featurizer mid-lineage would hand the search a train/serve mismatch the round-6 ruling warned against; the correction stays with the next *training* registration.
- **Reporting:** artifacts cited by path + sha256; interim notices carry status and artifact paths only, never figures; each stage's records (row + stat files) are published to the repo so every read is independently recomputable, as rounds 7 and 8 were. Box spot-checks are builder-run per Joe's standing rule.

## 9. Decisions for the reviewer

- **D1 — The thin-prior bar (§4.4).** *Proposal: ≤ 5% pooled panel thin-prior for the selected setting.* Builder's reason: it closes the round-7 confound by construction (≥ 95% of contested decisions really searched) while acknowledging Gravy's non-terminating mode may price the last points beyond any fleet's reach; Fai's 0% is the aspiration, not the bar. Alternatives named: ≤ 2% (cleaner, possibly unreachable in-grid), ≤ 10% (cheaper settings qualify, confound half-alive). **Reviewer settles.**
- **D2 — Seed blocks.** *Proposal: Stage 1 capture **21001–21040**; Stage 2 games **22001–22100**; Stage 3 fleet **23001–23200**; Stage 2 label seed bases **955001 + shard × 10⁸** (Stage 0's 855001 family is already registered).* Checked against every range in the record: fleets 1001–1200 / 2001–2200 / 8001–8200; probes 3000-series (incl. 3003–3010 extended probe); controls 4001–4014; smokes 5001–5010 / 7001–7002; census 6001–6040; round-8 corpus 10001–10400; pre-gate control 11001–11010; pilot equivalence 12001–12010; Gravy pre-gate 8501–8510; contention probe 8601–8604; Gravy census 8801–8820; round-8 gate block 9001–9200 (reserved, never run — left untouched and unreused). The 21xxx–23xxx blocks sit clear of all of them and leave the 9001–9200 reservation intact.
- **D3 — Stage 2 proceed bands (§5.2).** *Proposal: PROCEED requires CI lower > 0 AND per-game gain ≥ +0.05; STOP at mean diff ≤ 0; tripwire at per-game gain > +0.25.* Builder's reason: the +0.05 floor is set by fleet resolvability (round-7 CI half-width ≈ 0.021 at 800 games; the Fai per-game-gain ≈ Δ pattern), not by what would be nice to find — a smaller edge is a real result that still cannot price the next stage.
- **D4 — The calibration grid's exact points (§4.2).** *Proposal: hook budget {4,000 / 8,000 / 16,000} × candidate deadline {180 s / 360 s}, k = 25 fixed, six settings.* Builder's reason: factorial in the two bounds the record implicates, spanning 4×/2× the fleet values; beyond HD2 the per-decision price, whatever the completion gain, almost certainly fails §6's fleet arithmetic — and if it wouldn't, the NO CALIBRATED SETTING read plus a registered extension is the route to it.
- **D5 — Stage 0 ordering.** *Proposal: Stage 0 runs FIRST, before Stage 1's capture; not in parallel.* Builder's reason: Stage 0 is the cheapest stage in the round (≤ ~1.5 box-hours worst case, jobs already built) and its read can change Stage 1's grid through D6 — running the capture and sweep in parallel saves a few hours of wall at the risk of building Stage 1 on a grid its own first measurement would have altered.
- **D6 — The k contingency.** *Proposal: if Stage 0 reads null (CI includes 0) or negative, the reviewer decides — before Stage 1 launches — whether one k = 50 setting (at the grid's best bounds point) joins the Stage-1 panel as a seventh, state-paired setting; the overturn margin (1.5 paired SE) does NOT move in either case.* Builder's reason: k is a search bound and belongs in a calibration if the evidence indicts it; the margin is the decision rule that defines what an overturn *is* in every converted measurement to date, and moving it would confound calibration with redefinition.

## 10. What this package is not

No code, no jobs run, no capture, no launch. On Claude's approval (with the §9 decisions settled), the builder returns a Stage-0 launch package first — the label runner and scorer deployment copies, hash-pinned, with the DELTA substitution shown — for code approval and then Joe's go, in that order. Stages 1–3 follow the same pattern, each on the previous stage's read.
