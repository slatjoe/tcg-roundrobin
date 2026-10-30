# Round 10 — Step 1 pilot: REPORT (2026-10-30)

**Question (registered, step1-pilot-package.md §3–§5, terms from claude-reply-243b9d8 §3):** the threshold teacher — the §14 build with ONE change, the uncontested threshold lifted so every decision with ≥2 candidates is contested — plays 100 live games; what are its realized fires/game by class, its on-trajectory per-game gain by class and in total (L3, W=50 CRN, cap-aligned), and does the registered STOP rule fire (STOP iff the total gain's one-sided 95% upper bound < 0.0849 = Stage 3's +0.0649 + 0.020)? If not STOP, Step 2 is sized at Δ_plan = pilot lower bound − 0.0649.

**Answer: DO NOT STOP.** Total on-trajectory per-game gain **+0.2646**, one-sided 95% UB **0.3384** against the 0.0849 threshold. **Step 2 sizing: n = 72 games** at Δ_plan = +0.1299 (below the 400-game Joe-cost flag). The contested class reproduces Stage 3 (+0.0638 vs +0.0649); the newly-contested class — the states the old build never searched — carries the lift (+0.2008 of the +0.2646). An independent audit (§4) reproduces every printed number from the fetched primary files exactly, and establishes what the read's one anomalous counter — **fallbacks 116** — actually counts (§5): a label-path substitution concentrated in four early-game jobs whose diffs are all ≤ 0, so it cannot be manufacturing the result.

## 1. Design recap

- **Build:** `search_s3_thr.php` (sha256 4a1936fe…) = the §14 engine with the single branch change `$bp >= 0.97` → `$bp >= 1.01` (priors ≤ 1.0, so the uncontested branch is unreachable; every ≥2-candidate decision is searched). Everything else unchanged: margin 1.5, k 25, hooks 8000, deadline 180 s, horizon trigger 62 priced −1, candidate rule (top-3 + prior ≥ 0.10, cap 4).
- **Pilot:** 100 live teacher games vs the heuristic, Gravy Bones mirror (Eriksen deck), instrument 87/62, seeds 25001–25050 × both seats; every overturn captured. Jobs: 791 (172 contested — top prior < 0.97, the class the §14 build also fires on; 619 newly_contested — top prior ≥ 0.97, searchable only under the lifted threshold).
- **Labels:** L3 on ALL overturns — W=50, CRN, production eval server, §14 label engine (`search_s2.php` 1c964160… via `s2_label_main.php`), tuple L3-W50+H; seed family 700,055,001 + shard×10⁸, 4 shards, cap 512/shard (realized 208/130/232/221 jobs).
- **Read (direct form, no weights — capture is complete):** a label world scores 1.0 iff outcome > 0 AND it ended by turn 61, else 0 (cap-aligned, §14); a job's diff is the mean over worlds finished in BOTH candidates of score[teacher pick] − score[prior pick]; per-game totals sum a game's job diffs over all 100 games (zero-job games contribute 0); bounds by game-clustered bootstrap, B=10000, seed 20261020, one replicate set for every bound; lb/ub are the one-sided 95% percentiles (5th/95th) per fix pass 1. Pilot games are never pooled into Step 2.

## 2. Run record

- **Approval chain:** package acc55a14 → fix pass 1 (557cf033) → CONFIRMED 4b6cd6f6; pre-gate attempt 1 NOT IDENTICAL (instrument defects only) → repair package 3955e554 → repair pass 2 (f349b313) → CONFIRMED, claude-reply-f349b31 (committed 6c2f42b2). Joe's go 2026-10-29 16:48 EDT; launched sha 6c2f42b2 (approved f349b313, differing only by the committed reply file under rounds/). Launch record: `step1-pilot-launch.md` + the staged launch-facts note.
- **Pre-gate attempt 2:** launched 2026-10-29 16:49:39 EDT; **PREGATE: IDENTICAL** (pregate_check.txt written 19:55 EDT; all 10 seeds × both seats complete in every arm, zero timeouts; contested pairs 215/172, max |dprior| 8.941e-07 inside the 1e-5 tolerance). Registry merge +70 games (tag r10_step1_pilot_pregate) → **7,541** (registry sha256 0f8b458e…). Outputs: `data/step1/pregate_attempt2/`.
- **Pilot attempt 1:** launched 19:56:10 EDT; the pilot's PREGATE-GATE passed, then its **FREESPACE pre-flight aborted** — available 3,200,053,248 B < required 3,749,692,064 B × 1.25 headroom (the pilot needs 8 scratch trees; the pre-gate's five were still resident). No games ran, no read state consumed (pilot.launch.log).
- **Cleanup:** on Joe's approval (chat, 2026-10-29 20:06 EDT) exactly the five pre-gate scratch trees were deleted (≈2.64 GB on the df measure; /tmp available 3,200,053,248 → 5,844,172,800 B). The round-8 distill trees, probe-era trees and round-9 trees were not touched.
- **Pilot relaunch:** 20:06:42 EDT (pilot.launch2.log). Pre-gate gate and freespace pre-flight passed; TEACHER_TUPLE_JSON verified in the live game processes' environments (the pinned H8k-180+H tuple). Games completed the morning of Oct 30 — the pilot's registry merge is stamped 20261030T085339 (**+100 games, tag r10_step1_pilot → registry 7,641 games, sha256 6995d9ba…**). Jobs built (791 over 99 games), labels ran, and the read + pilot_manifest.json were written by 10:50 EDT Oct 30. Relaunch → read ≈ 14 h 43 min wall; games phase ≈ 12 h 47 min of it (four concurrent blocks), labels + read ≈ 1 h 57 min.
- **Wall actuals (games):** mean **1,773.357 s**, p95 2,440.8, max 2,676.8, min 627.8 — ≈49.3 box-hours of game wall in aggregate. The realized mean is ≈1.8–2.1× the ghost-based planning band (855–993 s/game): live trajectories, steered by the teacher's own picks, run longer than the raw-policy trajectories the band was measured on — the direction the re-price (package §12) said attempt-1 data could not sign. Teacher timeouts: **0**.

## 3. The registered read (verbatim, data/step1/pilot_read.txt)

```
=== ROUND-10 STEP 1 PILOT -- READ ===
games 100; jobs 791 (scored 791); label rows finished 79093 / unfinished 7 / refusals 0; fallbacks 116; jobs_no_shared_worlds 0
class contested: fires/game 1.7200 (172 jobs); edge 0.0371; per-game gain 0.0638, two-sided 95% CI [0.0220, 0.1132], one-sided 95% lb 0.0280 / ub 0.1042; LOGO range [0.0517, 0.0669], largest share 0.1975 (game 152925466)
class newly_contested: fires/game 6.1900 (619 jobs); edge 0.0324; per-game gain 0.2008, two-sided 95% CI [0.1368, 0.2698], one-sided 95% lb 0.1470 / ub 0.2584; LOGO range [0.1879, 0.2061], largest share 0.0737 (game 686801642)
z-band (1.5, 2.0]: 435 jobs, edge 0.0170
z-band (2.0, 2.5]: 228 jobs, edge 0.0212
z-band (2.5, 3.5]: 106 jobs, edge 0.0519
z-band >3.5: 22 jobs, edge 0.3964
TOTAL: per-game gain 0.2646, two-sided 95% CI [0.1816, 0.3538], one-sided 95% lb 0.1948 / ub 0.3384; LOGO range [0.2473, 0.2713], largest share 0.0748 (game 375620641); wall mean 1773.3570000000002 p95 2440.8 max 2676.8; timeouts 0
STOP rule: STOP iff total one-sided 95% upper bound < 0.0849; total ub (95th percentile) 0.3384 -> DO NOT STOP
Step 2 sizing: Delta_plan 0.1299 (pilot one-sided lb 0.1948 - 0.0649); SE_pilot 0.0435; n = 72 games at 80% power
```

Full-precision values are in `data/step1/pilot_read.json`; the run's own manifest (rows, hashes, tuple audit, games report) is `data/step1/pilot_manifest.json`. Teacher game outcomes (context, not the read): W70 / D7 / L23, 70.0 points at draw=0 over the 100 games.

## 4. Audit — independent recompute from the fetched primary files

The auditor re-implemented the registered read from the spec (it does not import the run's read code) over the files in `data/step1/` and compared against `pilot_read.json` at full precision. **All 38 compared quantities agree with an absolute difference of 0.0** — the gains, both CI bounds, both one-sided bounds, SEs, edges, LOGO ranges and shares, band edges, Δ_plan, R, and the wall statistics. (The bootstrap is exactly reproducible: the registered algorithm and seed are deterministic given the per-game totals, and the recomputed totals match bit-for-bit.) The sizing arithmetic re-derives: Δ_plan = 0.194816… − 0.0649 = 0.129916…; R = (0.129916…/2.4866)² − 0.0090² = 0.0026487…; n = ceil(100 × 0.043522…² / R) = ceil(71.5…) = **72**. STOP test: UB 0.3384 ≥ 0.0849 → DO NOT STOP.

| Quantity | Printed | Recomputed |
|---|---|---|
| games population / rows | 100 / 100 | 100 / 100, exactly seeds 25001–25050 × seats {1,2}, 25 per block file |
| driver rows with `invalid` (timeouts) | 0 | 0 |
| wall mean / p95 / max (s) | 1773.357 / 2440.8 / 2676.8 | identical (min 627.8) |
| jobs (contested / newly) | 791 (172 / 619) | identical; fires/game 1.72 / 6.19 / 7.91 |
| label rows | 79,100 | 79,100; 0 rows for non-job snaps, 0 for non-selected candidates, 0 duplicate (snap, cand, world) |
| label rows finished / unfinished / refusals | 79,093 / 7 / 0 | identical |
| jobs scored / no shared worlds | 791 / 0 | identical |
| contested gain [CI], lb/ub | 0.0638 [0.0220, 0.1132], 0.0280/0.1042 | identical |
| newly_contested gain [CI], lb/ub | 0.2008 [0.1368, 0.2698], 0.1470/0.2584 | identical |
| total gain [CI], lb/ub, SE | 0.2646 [0.1816, 0.3538], 0.1948/0.3384, 0.0435 | identical |
| LOGO total range / largest share | [0.2473, 0.2713] / 0.0748 (game 375620641) | identical |
| z-band edges (jobs) | 0.0170 (435), 0.0212 (228), 0.0519 (106), 0.3964 (22) | identical |
| Δ_plan / R / Step 2 n | 0.1299 / 0.0026487 / 72 | identical |

Integrity checks beyond the read:

- **Fetch integrity:** every sha256 in `pilot_manifest.json`'s own table matches the fetched bytes (games ×4, jobs_all + 12 shard/part files, labels_all + 8 shard parts, games_report.json, pilot_read.json; the manifest's flat `search_stats.jsonl` and `teacher_snap_index.jsonl` entries are the s2b arm's copies — both match). `data/step1/MANIFEST.md` covers the staged tree.
- **Pins:** the box's deployed_code_hashes.txt (fetched with the run) equals the repo pins for every file that ran — build `search_s3_thr.php` 4a1936fe…, label engine `search_s2.php` 1c964160…, `s2_label_main.php` 1c1dfd9f…, `pilot_read.py` 69cae860…, `settings_pilot.json` 0571e03a…, pre-gate checker 98b3d2ff…, both runners as deployed for attempt 2. The manifest's tuple audit checked all 9,886 teacher stat rows against the pinned tuple (with the `pinned` flag): 0 bad rows, 0 malformed-pin aborts. The games report's class tallies (contested 172 fires / 2,501 searched decisions; newly 619 / 7,385; thin-prior 0) match the job build exactly.
- **Registry:** the pilot DID merge its games — record in `games/registry_merge.txt` (+100, tag r10_step1_pilot, 0 already under the tag → 7,641; registry sha256 6995d9ba…; vault copy + backup stamped 20261030T085339). Note `pilot_manifest.json` itself carries no registry section; the merge record lives in the games directory. Chain: 7,471 (post-probe) → 7,541 (pre-gate) → **7,641 (current)**.
- **The 7 unfinished label rows:** all seven are `{"error": "abort"}` results (a SimSearchAbort in the label child — hook budget / hook check), none is a refusal class. They touch 6 jobs, all newly_contested: 152925466_t3 (teacher cand, world 7), 951682359_t2 (prior cand, world 32), 572324691_t1 (world 21 in BOTH candidates), 731363457_t6 (prior cand, world 47), 450812471_t1 (teacher cand, world 8), 676196321_t1 (prior cand, world 21). Scoring impact: a job scores on worlds finished in both candidates, so each affected job's diff is the mean over **49 shared finished worlds instead of 50**; no job is dropped (jobs_no_shared_worlds = 0, all 791 scored). The label mains' per-job stat rows (cand_finished counts) agree with the row-level recount for every affected job.

## 5. The fallbacks finding (fallbacks = 116)

Prior label runs printed fallbacks 0 (e.g. the probe's merged 71,500 rows), so this counter gets its own section. Everything below is from the label engine's code (`search_s2.php`, the file that ran, sha-pinned above) plus the fetched rows.

**What the counter counts.** In `SimLabel_RunRollout`, each rollout world plays out under `SimLabel_ChildChoose`, the callback for below-root decisions at net-controlled seats. For each such decision it (1) runs the hidden-information fair-play canary, `SimFeat_Canary($player, $state)`, and (2) asks the eval server, `SimSearch_Eval($state, $candRecs)`, for the priors that drive the pick. If the canary throws, OR the eval returns nothing, the child substitutes `SimLabel_V1Argmax($candRecs)` — the anchor policy's own v1-score argmax over the candidate records — for that one decision, and increments `$GLOBALS["ssLabelFallbacks"]` (exactly two increment sites, search_s2.php lines 1511 and 1516, both in `SimLabel_ChildChoose`; the counter resets per world and is written into the world's result row). `s2_label_main.php` sums the per-world counts into each job's stat row; `pilot_read.py` sums them over all label rows and prints the total. The sibling callback `SimLabel_ChildDQ` applies the same substitution without incrementing, so 116 counts substitutions on the ChildChoose path and is a floor on all such substitutions in the label worlds. The rows do not record which of the two triggers fired on any given event.

**What it is not.** It is not a dropped or fabricated world: a fallback is a single below-root decision inside an otherwise normal rollout — the world runs to its ordinary end (game over or the §14 horizon) and its outcome scores exactly like any other world's. Nor is it the live games path: the games phase keeps its own tallies (games_report `child_fallbacks` 0, `eval_fail_rows` 0 over the 9,886 teacher stat rows); the 116 are label-path only.

**Where the 116 sit.** 116 events in **34 world-rows** (34/79,100 = 0.043% of worlds carry ≥1), concentrated in exactly **4 jobs** — every one the first snapshot captured in its game (snap index t1; the jobs' game turns are 1, 1, 3 and 4), every one newly_contested:

| job (game) | world-rows with fallbacks | events | job diff |
|---|---|---|---|
| 599028118_t1 | 12 | 27 | −0.10 |
| 625909670_t1 | 11 | 37 | 0.00 |
| 528341562_t1 | 7 | 42 | −0.04 |
| 330533965_t1 | 4 | 10 | −0.06 |

(Per-job totals agree between the label rows and the label mains' own stat rows.) **All 34 worlds finished, and all 34 entered a scored diff** (their CRN pair-world also finished). The four jobs' diffs sum to −0.20: they pull the total DOWN by 0.002 per game. Deleting the four jobs wholesale would move the total gain from 0.2646 to 0.2666 — the fallback events sit in jobs that, on net, score against the teacher, so they cannot be manufacturing the positive read. The concentration (four early-game states, up to 15 events in a single world) reads as a state-shape-specific canary/eval failure mode in the game's opening turns, not a fleet-wide degradation: 787 of 791 jobs have zero fallback events.

## 6. Interpretation (bounded)

- **Continuity where the builds agree.** The contested class is the class both the §14 build and the threshold build fire on, measured the same way (live fires, L3 on the teacher's own trajectory): pilot **+0.0638** per game vs Stage 3's **+0.0649**. The instrument and the shared class reproduce; what changed is only what the build change added.
- **The newly-contested class carries the result.** +0.2008 of the +0.2646 total (76%) comes from states the §14 build never searched. Per job its edge is a little SMALLER than the contested class's (0.0324 over 619 jobs vs 0.0371 over 172) — the class wins on volume, 6.19 fires/game against 1.72.
- **Against the probe's estimates — carefully.** The probe priced this lever OFF the teacher's trajectory (offline eval on raw-policy games): its full-class per-job edge estimate was +0.0698. The pilot's realized on-trajectory per-job edge for the class is 0.0324 — about half. The probe's §3 bounding illustrations for its additive per-game figure were distinct-once ≈ 0.27 and best-fix-per-game ≈ 0.13; the pilot's newly-class gain, +0.2008, falls inside that illustration band. The pilot TOTAL (+0.2646) sits near the band's top, but it is not the quantity the illustrations bounded — it adds the contested class's +0.0638, the §14 teacher's already-established edge. These are comparisons across different estimands (probe: additive over sampled raw-trajectory states; pilot: realized, direct form, on the threshold teacher's own trajectory), stated as orientation, not as one number confirming another.
- **z-band shape.** Per-job edge rises monotonically with the eval z: (1.5, 2] 0.0170 (435 jobs), (2, 2.5] 0.0212 (228), (2.5, 3.5] 0.0519 (106), >3.5 **0.3964 (22 jobs)**. The tail is 2.8% of jobs and contributes 33% of the summed diffs (8.72 of 26.46) — outsized but not load-bearing alone: the remaining 97% of jobs still sum to +0.1774 per game. LOGO agrees: total range [0.2473, 0.2713], largest single-game share 7.5% — no game carries the read. The one concentration to note is in the contested class: its largest-share game (152925466, 19.7%) is also its weakest LOGO exclusion (gain 0.0517 with it removed — still positive).
- **Cost, realized.** The games cost ≈49.3 box-hours in aggregate (mean 1,773 s) and the whole pilot ≈14.7 h wall including labels. For Step 2 planning, the teacher-arm component of a 72-game fleet prices at ≈35 box-hours at the realized per-game wall (72 × 1,773 s), before its paired arm and labels — the ghost-based band must not be reused for that pricing.
- **Scope of the claim.** This is a pilot on one matchup (Gravy mirror) against the heuristic, on the teacher's own trajectory: it establishes that the lifted threshold converts at pilot scale and sizes the confirmatory gate. It does not by itself clear the Stage 3 bar — that comparison is Step 2's registered job (two-sample, vs +0.0649 with SE 0.0090, at n = 72, pilot games never pooled). Step 2 is a new package for review; nothing in this report launches it.

## 7. Files

- `data/step1/` — the full fetched run output (games, labels, read, manifests, launch logs, pre-gate attempt-2 outputs) with `data/step1/MANIFEST.md` (sha256 per file; log/snapshot trees as aggregate entries).
- Code as run: `code/step1/` at the pins listed in §4 (unchanged since the confirmed package, f349b313).
- Design + read registration: `step1-pilot-package.md` §3–§5 (as amended through §12); launch record: `step1-pilot-launch.md`.
