# Claude — code review of the round-8 build package

**Reviewed commit:** a0761486266830f325e9e81aff16f9770d103a11 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-926f6c3.md` hashes to `a7aefc05…22963b4128`, the value I gave Joe.

**Hashes verified:**
- all 24 files under `rounds/round8/code/` hash to the §10 manifest
- the three borrowed files (`patch_census_probe.py`, `tally_census.py`, `shm_sweep.py`) match too

**Verdict: CHANGES REQUESTED. Nothing runs yet.** The design is carried faithfully, and most of the machinery is right (§1). But:
- **The gate path won't run as written, and parts of it would read silently wrong** (§2). The runner calls driver flags that don't exist, and three scripts key on row fields the driver doesn't write.
- **The pilot's V1/V2 test, as I specified it, is biased against the labeler and too small to decide anything.** The bias is my error, and §3 fixes it.
- **The V2 snapshot set sits on tmpfs.** Copy it to durable disk now (§5).

## 1. Accepted

- **The featurizer correction:** the helper plus two call sites. **Moving the canary's `LegalCounts` with it is right**: a store-based allowance against a view-based state would false-positive on the corrected build's own output. `SimV1_DeckCards` and the sync are untouched. The patcher reproduces `3dcf32c9…`.
- **The two trees:** a full-tree comparison of 13,639 files, differing in exactly `featurize.php`.
- **The featurization smoke and its consequence.** Parsed roots equal the stored live state (40/40), and native equals corrected at roots. So **the correction binds only at live serving, between syncs**, and the featurizer-only control is where it shows. That's a real finding, it's handled correctly, and its two consequences are built in: the data builder's assertion, and the census caveat.
- **The capture arm** as the corpus recorder. Routing opponents through `TCG_OPP_MIX` is a runner composition, not a driver change. Correctly done.
- **The labeler's composition** (`SimLabel_RunForSnapshot` under the job's registered `selected` set, W pinned at 25, pair va), and **`label_reduce.py`**. I checked it against the repo's copy of `SimTeacher_DecideInner`. It matches:
  - the sorted selection
  - finished worlds only
  - the prior's 20-world floor, with thin labels excluded and counted
  - strict > in the best scan
  - paired ≥ 20 worlds
  - sample SE over √n, and the 1.5 × SE margin
- **The placement:** the native tree plus the production server (R12), one label process per tree, sharded across four tree copies.
- **The corpus runner's shape:** 400 games on seeds 10001–10400, the matchup split, an `assert_ok` gate per stream, durable disk.
- **GAP 1's fix** (the patched corpus tree), subject to the equivalence check in §4.2.
- **GAP 2's substitute** (corpus divergent-pick states), subject to §4.4.
- **The T1 objective as coded:** cross-entropy plus β·KL with β = 1, v15's side native and the student's corrected, masked softmaxes (no NaN path), uniform weights, the value head frozen, held-out-CE early stopping, one checkpoint out.
- **The trainer knobs** (lr 1e-4, batch 1024, cap 30, patience 5, min-delta 1e-4) are accepted as proposed.
- **The Gravy census, containment and sequencing.**

## 2. Blocking: the gate path and the row schema

**2.1 The gate runner's timeout recovery calls a driver that doesn't exist.** `run_distill_gate.sh` (lines ~195–207) runs `paired_driver.py … --arm2 retry --base-rows …`. The driver (`1e312629…`) accepts neither flag, and `--arm` is restricted to `raw/teacher/ghost/shadow/capture`. The step runs **unconditionally** for every arm and seat of every chunk, so argparse exits 2, `|| return 1` fires, and **the fleet aborts at the end of chunk c1.**

The splice policy it feeds also selects "pending" rows by `keep_game_dir` and `gamelog_sha256`. Neither field exists, so every row would count as a timeout.

**Required:** use the **stock `gate_raw_retry.py`** (`c3fb227e…`, in each tree, beside that tree's driver), with its real interface (`--tree --sock --seat --rows --logdir --timeout --deck`), exactly as round 7 did. Run it only on rows with `invalid == "timeout"`.

**2.2 The analysis, pre-gate comparison and runner use field names the driver doesn't write.** From the driver's actual row schema (round-7's published rows, the same driver), the keys are `seat`, `gamelog_sha`, `winner` (0 on a draw or cap), `capped`, `draw`, and `invalid: "timeout"` on a timeout row. The round-8 scripts read:

| Script | Reads | Effect |
|---|---|---|
| `analyze_distill_gate.py` `score()` | `learner_seat` | **KeyError on the first decided game**, so the analysis crashes |
| `analyze_distill_gate.py` `score()` | the winner check *before* `capped` | a draw or cap (winner 0) returns None. It's rescued only because `gamelog_sha256` is always missing, so it scores 0.5 **by accident** |
| `analyze_distill_gate.py` `divergence()` | `gamelog_sha256` | both arms' values are missing, so they compare equal and **the divergence rate is silently 0** for every fleet |
| `analyze_distill_gate.py` | `timed_out` | never set; timeouts only score 0.5 through the same accident |
| `pregate_compare.py` | `learner_seat`, `gamelog_sha256` | KeyError, and the determinism and control reads would be meaningless |
| `run_distill_gate.sh` splice | `keep_game_dir`, `gamelog_sha256` | see 2.1 |

**Required:**
- Rewrite the scoring as explicit branches, in this order:
  1. `invalid == "timeout"` → 0.5 (the registered convention for raw arms), counted
  2. any other `invalid` → unusable, reported
  3. `capped` or `draw` or `winner ∈ {0, None}` → 0.5
  4. otherwise a win or loss by `seat`
- Compute divergence on `gamelog_sha`, with timeout units counted separately, not as diverged.
- Fix `pregate_compare.py` the same way.

**2.3 Functional tests with known answers, in the package.** "Syntax checks passed" can't catch any of 2.1–2.2. Round 7's published rows (`rounds/round7/data/rows/`) are a ready fixture from the same driver. Run `analyze_distill_gate.py` on them with teacher as "dist" and raw as "raw" (a filename-mapping shim is fine). Under round 8's rules, timeouts score 0.5 for both arms. **I computed the expected outputs from the rows myself:**
- 400 units
- Σd = **+6.5**, so **Δ = +0.01625**
- **88** diverged units (`gamelog_sha` differs), plus **7** timeout units
- the read: DOES NOT CONVERT

Also run `pregate_compare.py` on a fixture with a known answer. The round-7 raw rows against themselves should read IDENTICAL 10/10, and raw s1 against raw s2 should differ, for the seat control. Run the gate runner's retry step against a fixture row file with one injected `invalid: "timeout"` row and one without. Commit the outputs. **I'll check them against the numbers above.**

## 3. Blocking: the pilot's V1/V2 test, corrected (my error)

**The bias.** I asked for V2 (labeler against the live pick) to be "indistinguishable from V1" (labeler against itself) on gate overturn snapshots. That comparison is biased against the labeler even if it **is** the teacher. Those snapshots were *selected* because the live draw overturned. If the live run, A and B are three exchangeable draws per state, then on a selected population P(B = A | A overturned) exceeds P(A = live | live overturned), purely through the selection. (Roughly, it's E[p³]/E[p²] against E[p²]/E[p].) The package's comparison, V2 against **V1-overall on the same 20 selected states**, mixes this with confirmation agreement too.

**The size.** With n = 20, neither rate's interval is narrower than about ±0.2. The test could pass a wrong labeler or fail a right one.

**The corrected test (registered):**
- **V1 runs on unselected states:** take the **first 20 corpus capture games (seeds 10001–10020)** and label every contested state **twice** (runs A and B). That's roughly 540 states, with about 70 overturns expected. Run A's labels are ordinary corpus labels, so they aren't wasted.
  - **V1-ov** = P(B makes the same overturn | A overturned)
  - **V1-conf** = P(B confirms | A confirmed)
- **V2:** label **100** gate overturn snapshots once, stratified across the 8 streams.
  - **V2** = P(labeler makes the live pick | live overturned)
- **Exchangeability predicts V2 ≈ V1-ov.** Report both with Wilson intervals and the two-proportion test.
  - One caveat to state with it: gate states lie on teacher trajectories and V1's on v15's. They're the same game up to each trajectory's first overturn, so I'll read a small gap in that light.
  - The read is mine, at the pilot review.
- **Report-only, the mechanism check:** on the V2 snapshots, compare the labeler's per-candidate means with the live stat rows' `means`, for **candidates not in the live overturn pair** (they're unselected), as z-scores. They should be roughly standard normal.
- **The registered difference, measured:** the label path's per-candidate deadline is **300 s**, against the live teacher's **180 s**. Report how many label worlds finished *after* 180 s, and how many candidates were cut off at either deadline. If that's about 0, which Fai's rates suggest, the difference is moot.
- **Cost:** about 1,200 label jobs. Report the mean, p95 and max per job. The corpus estimate is computed from these, not from 20 jobs.

## 4. Required, non-blocking (fix in the same commit)

1. **`t1_trainer.py`:**
   - assert that the frozen value-head parameter set is **non-empty**, and print the names. If `PPOPolicyV3` doesn't name the head `value_head*`, the freeze and the equality assert both pass vacuously.
   - **evaluate held-out cross-entropy at epoch −1** (v15 itself). If no epoch beats it, T1 records "no improvement on held-out labels", and **no gate runs**: the round's result is "does not convert" at the training stage.
   - log per-epoch held-out **overturn recall** and **confirmation accuracy**, report-only. Held-out CE is about 87% confirmations, so CE alone can hide whether overturns were learned.
2. **The capture equivalence check, before the corpus run.** The corpus tree's capture arm (with the uncontested patch) against raw v15 on the native tree, 10 seeds per seat against the heuristic, through `r3_pair.py` with the round-7 strict parser: it must be **IDENTICAL**. That proves capture plus the patch doesn't change play, so the corpus really is v15's state distribution. It can run inside the pilot.
3. **`t1_build_data.py`:**
   - drop `ncand ≤ 1` states from the KL set and count them; a single legal move gives a KL of exactly 0
   - **assert corpus game ids ∩ the do-not-train registry = ∅**
   - record the input hashes (`labels.jsonl`, `corpus_manifest.json`) in `build_report.json`
4. **The swap test:**
   - choose a hand/deck pair whose cards **differ**. A same-card swap is a no-op, and it would pass trivially.
   - **assert the swap took effect**: the parsed opponent hand differs between A and B. Have `featurize_snapshot.php` emit it as a debug field outside the state.
   - count failed swaps as invalid, never as passes
5. **The corpus tree:** assert the patch product hash **`044ca8ec…`**, which is known now, rather than only recording it.

## 5. Now, before anything else: preserve the V2 set

`/tmp/gate_r4/gate_c*_teacher_s*_snaps/` (915 snapshot dirs) and the matching `search_stats.jsonl` files are on **tmpfs**. They're the only live-teacher labels on record, and a reboot loses them. **Copy them to durable disk** (`/home/joe/tcg/`) with a hash manifest, and point `pilot_prep.py` at the copy. This plays no games and needs no approval beyond Joe's say-so.

## 6. What comes back

One commit with:
- §2's fixes and the **fixture outputs**
- §3's restructured pilot (`run_pilot.sh`, `pilot_prep.py`, `pilot_report.py`)
- §4's five items
- the §5 copy record

I'll review that sha. The pilot, including the capture equivalence check, then runs on Joe's go, and the corpus stays gated on my pilot review.

**Scope:** this review accepts the items in §1 and requests the changes in §2–§5. It approves no run.
