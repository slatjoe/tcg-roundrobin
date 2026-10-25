# Round 8 — build fix package (answer to claude-reply-a076148)

Parent: `fef86fb1` (the commit carrying the review). This file
answers the review's §2 (blocking), §3 (blocking), §4 (required)
and records §5. Corrected code is written over
`rounds/round8/code/` under the same filenames; the §2.3 fixture
outputs are under `rounds/round8/fixtures/`.

**Manifest choice:** `build-package.md` is left untouched (it is
the reviewed artifact); this file carries the new full §10-style
manifest in §6 below.

**Nothing here has been run beyond the review's own §2.3
fixtures.** The pilot scripts are written, not run. Every
go-gate from the build package stands unchanged: the pilot runs
only on the reviewer's approval of this fix at its committed sha
plus Joe's go; the corpus stays gated on the reviewer's pilot
read.

---

## §0 Discrepancies and notes (reported plainly, per the fix brief)

1. **The review file was not in the staging tree.** The local
   staging tree held only `build-package.md`,
   `distillation-design.md` and `code/`; the review was read
   from the upload original
   (`~/workspace/user/files/claude-reply-a076148.md`, sha256
   `f83bd0ed692b9e6bae6a8aea04feb854b810e4277666127f5c4abc7b67f7e707`).
   The parent commit `fef86fb1` carries it in the repo.
2. **§10's borrowed files were not in the staging code dir.**
   The original `run_pilot.sh` already referenced
   `patch_census_probe.py`, `tally_census.py`, `shm_sweep.py`
   from `$CODE_DIR`; build-package §10 lists them as "borrowed,
   deployed alongside" but no copies sat in `rounds/round8/code/`.
   The fix stages byte-identical copies (round 5 / round 7);
   their hashes match §10's borrowed note exactly
   (`60a3808c…`, `fe2480bb…`, `98027a8b…`), so the staging tree
   is now self-contained and the pilot's deployed-files guard
   can pass. `parse_r3_pair.py` (round 7, `ed47c9cd…`) is staged
   the same way — it is newly referenced by the pilot's §4.2
   equivalence phase (§3 below). A sweep over every round-8
   shell script confirms every `$CODE_DIR/…` reference now
   resolves to a file in the code dir.
3. **The preserved V2 copy's layout is flat**, not the layout
   the original `pilot_prep.py` expected: eight
   `gate_c{X}_teacher_s{Y}_snaps/` dirs (915 snap dirs total,
   each holding `teacher_snap_index.jsonl`) plus eight
   `gate_c{X}_teacher_s{Y}_log_search_stats.jsonl` files at the
   copy's root. The rewritten prep (§3) targets this layout.
4. **Unit wording in fixture 2:** `pregate_compare.py` counts
   (seed, arm, seat) units, so the determinism block reports 20
   units for the fixture's 10 seeds × 2 seats. The reviewer's
   "IDENTICAL 10/10" is the same result at seed granularity —
   all 10 seeds identical in both seats. Stated in the fixtures
   README rather than silently.
5. **The trainer's internals differed in shape from what the
   review's §4.1 wording implies** (it speaks of adding an
   evaluation; the file already had the held-out loop, a
   `value_head_before` snapshot assert, and an `epochs_max`
   config). The §4.1 changes were made against the file as it
   actually stands: §4 below names them exactly.

---

## §1 §2.1 — gate timeout recovery uses the stock retry

`run_distill_gate.sh`:

- The nonexistent `paired_driver.py --arm2 retry --base-rows`
  step and its splice machinery are **deleted** (the
  `RAW_RETRY_POLICY` heredoc is gone with them).
- Timeout recovery is the **stock `gate_raw_retry.py`**, read
  from the file itself before wiring: sha256
  `c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93`,
  present at the root of both gate trees, **hash-pinned in the
  runner for both trees** (`expect_hash`, abort on mismatch).
  Its real interface: `--tree --sock --seat --rows --logdir
  [--timeout] [--deck]`; it edits the rows file in place —
  drops only rows with `invalid == "timeout"`, re-invokes the
  tree's own `paired_driver.py` per removed seed (the driver
  resumes from the row file, so removed seeds are the only ones
  replayed), and a re-run that times out again leaves its fresh
  timeout row standing for the analysis to score 0.5.
- Invocation per chunk/seat/arm, servers still up, exactly as
  round 7 ran it — including `GATE_GAME_IDS_FILE` set to the
  arm's **main** ids file. (The deleted code wrote retried ids
  to separate `*_retry_game_ids.txt` files that were never in
  the runner's registry-merge list; retried games would have
  escaped the registry merge. The stock invocation merges them
  with the fleet's ids by construction.)

## §2 §2.2 — row handling rewritten against the driver's real schema

Schema (verified against round 7's published rows from the same
driver): `seed`, `arm`, `seat`, `winner` (0 on draw/cap),
`capped`, `draw`, `gamelog_sha`, and `invalid` only on timeout
rows (`"timeout"`).

- **`analyze_distill_gate.py`** — `score_row` applies the four
  branches **in the registered order**: (1) `invalid ==
  "timeout"` → 0.5, counted as a timeout unit; (2) any other
  `invalid` → unusable, the unit is printed and excluded, never
  scored; (3) `capped` or `draw` or `winner ∈ {0, None}` → 0.5;
  (4) win/loss by the row's own seat. Divergence is computed on
  `gamelog_sha`; units where either arm timed out are counted
  separately (`timeout_units`) and never as diverged. The report
  carries `sum_paired_diffs` alongside the delta.
- **`pregate_compare.py`** — keyed by `(seed, arm, seat)`;
  determinism compares `winner`, `turns`, `decisions`,
  `gamelog_sha`; the featurizer-only control and the R16-style
  seat control both read `gamelog_sha`.
- **Grep proof:** no file under `rounds/round8/code/` reads
  `learner_seat`, `gamelog_sha256`, `timed_out` or
  `keep_game_dir` (grep over the whole dir: no matches; also no
  `arm2`, `--base-rows`, or `*_retry_game_ids` anywhere).

## §3 §2.3 — fixture tests (run; all pass)

Full record in `fixtures/README.md`; outputs committed under
`fixtures/`.

| Fixture | Expected (review §2.3) | Observed |
|---|---|---|
| Fixed analysis on round-7 rows (teacher as "dist", raw as "raw", via `fixtures/shim_analyze_rows.py`) | 400 units; Σ paired diffs +6.5; Δ +0.01625; 88 diverged; 7 timeout units; DOES NOT CONVERT | **400; 6.5; 0.01625; 88; 7; DOES NOT CONVERT** (CI [−0.00375, +0.03625]); 0 unusable |
| pregate_compare, round-7 raw rows vs themselves | IDENTICAL 10/10 | deterministic, 0 diffs, 20/20 units (10 seeds × 2 seats — see §0.4) |
| pregate_compare seat control (seat-1 vs seat-2 rows) | must differ | 10/10 seeds differ on `gamelog_sha` |
| Stock retry on a 2-row file (1 normal + 1 injected `invalid:"timeout"`, seed 999901), native distill tree | retry fires only for the timeout row; ≤ 1 raw game | "raw retry seed 999901: completed winner=1"; exactly one game played (id 520460677); the normal row untouched. Control run on a timeout-free file: "no raw timeouts; nothing to retry", no game played |

## §4 §3 — pilot restructured (written, not run)

`run_pilot.sh` phases, in order: guards/pins (now including the
native tree's `r3_pair.py`, pinned `13f95ebe…`) → G8 + (C)
sweeper on the native tree → **pilot capture** → **capture
equivalence check** → jobs → labels → reads → teacher-root
census.

- **(i) Pilot capture.** `run_capture_corpus.sh` gains
  `PILOT_CAPTURE=1`: it runs only the heur seat-1 stream
  restricted to seeds **10001–10020** and marks the manifest
  `pilot_subset`. Those 20 games are the corpus's first 20; the
  full corpus run later re-runs all 400 streams' games including
  them (capture is deterministic at raw speed; the re-run
  overwrites). **The full 400-game corpus does not run in the
  pilot.**
- **(ii) V1.** `pilot_prep.py --mode v1` takes every contested
  row of the capture games' snap index directly (the index rows
  carry `selected`/`priors`/`prior_pick`; no join), ~540 jobs.
  Each is labeled **twice**: run A `DISTILL_SEED 555001`, run B
  `777001`. Run A's labels are ordinary corpus labels.
  `pilot_report.py` reports **V1-ov = P(B same overturn | A
  overturned)** and **V1-conf = P(B confirms | A confirmed)**
  with Wilson 95% intervals.
- **(iii) V2.** `pilot_prep.py --mode v2` draws **100**
  gate-fleet overturn snapshots, stratified across the 8 streams
  (quotas 13,13,13,13,12,12,12,12, seeded, top-up from surplus),
  from the **preserved copy** (§7) — never `/tmp/gate_r4`. The
  prep joins each index row to its live stat row (within-game
  order, as verified at build time) and **asserts** pick,
  prior_pick and branch equality per sampled row. The truth file
  carries the live pick **and** the live per-candidate means /
  n_worlds / selected list. The report gives **V2 = P(labeler
  pick == live pick | live overturned)** with a Wilson interval
  and the **two-proportion z-test of V2 vs V1-ov**, with the
  trajectory caveat printed next to the read (gate states lie
  on teacher trajectories, V1's on v15's; the judgment is the
  reviewer's).
- **(iv) Mechanism check (report-only).** `label_reduce.py` now
  emits per-candidate finished-world **means and sample SDs** on
  every label row. For V2 candidates in the live selected set
  but **not** in the live overturn pair, the report computes
  z = (labeler mean − live mean) / (sd_labeler ·
  √(1/n_labeler + 1/n_live)) and summarizes (mean, sd, max |z|,
  share |z| > 2). Construction stated in the report: live rows
  record means and counts, not per-world outcomes, so the
  per-world sd is borrowed from the labeler's own worlds for
  that candidate. Expect ~N(0,1).
- **(v) Deadline accounting.** Instrument: `distill_label_main.php`
  gains an env-gated split-candidate mode
  (`DISTILL_SPLIT_CANDS=1`, used by all pilot label runs, never
  by the corpus runner): one `SimLabel_RunForSnapshot` call per
  candidate with the **same per-job seed base** — the world seed
  for (candidate, world w) is `seedBase + w·31337` regardless of
  grouping, so the emitted rows are identical to the grouped
  call's; only the invocation grouping differs. Each call's wall
  time is that candidate batch's wall (batches fork their W
  children together against the label path's 300 s deadline).
  Sidecar rows `{snap, cand, secs, worlds, finished,
  timeout_errs}` go to `DISTILL_TIMINGS`; `pilot_times.py`
  aggregates them. The report counts: batches past 180 s (their
  finished counts are the **upper bound** on worlds finished
  after 180 s; batches at/under 180 s contribute exactly 0 —
  exact per-world finish times are not recorded by the
  machinery, stated in the report), and the worlds killed at
  the 300 s label deadline (`timeout_errs`) with the candidates
  they cut, against the live 180 s.
- **(vi) Cost.** `pilot_report.py` computes per-job mean, p95
  and max over all ~1,200 pilot job-runs (V1 ×2 + V2), and the
  corpus estimate from them (at the mean and at the p95, for
  the registered ~10,000 contested labels).
- **(vii) Capture equivalence (§4.2) as a pilot phase.** Corpus
  tree's capture arm (uncontested patch active, product hash
  asserted first) vs raw v15 on the native tree, seeds
  12001–12010 per seat vs the heuristic, compared through the
  native tree's `r3_pair.py` with the round-7 strict parser
  (`parse_r3_pair.py --expect-rows 10`) per seat. Both seats
  must read IDENTICAL; **a parse failure stops the pilot**
  before any labeling.
- **(viii) Teacher-root census** stays attached to the pilot's
  label roots (V1 + V2 job roots, union jobs file), report-only,
  with the parsed-root caveat as registered.

## §5 §4 — the required non-blocking fixes

- **§4.1 `t1_trainer.py`.** (a) The frozen value-head set is
  asserted **non-empty by name** and the names are printed
  before training. Head naming verified from the model code:
  `PPOPolicyV3` (`ppo_model_v3.py`, native tree) names it
  `value_head` (an `nn.Sequential`), so the frozen set is
  `value_head.0.weight/bias`, `value_head.2.weight/bias` — the
  existing `startswith("value_head")` freeze was not vacuous,
  and now cannot silently become so. (b) **Epoch −1**: held-out
  evaluation of v15 itself before any training; the best-so-far
  starts at epoch −1, so an epoch wins only by beating v15 by
  `min_delta`. If no epoch does, the trainer records
  `"no improvement on held-out labels"`, writes
  `<out>.does_not_convert.json` (plus the train log), and writes
  **no gate checkpoint**. (c) Per-epoch held-out **overturn
  recall** and **confirmation accuracy** are logged with CE
  (report-only); the data builder now carries `prior_pick` and
  `overturn` on contested records for this.
- **§4.3 `t1_build_data.py`.** (a) KL set: states with
  `ncand ≤ 1` are dropped and counted
  (`kl_single_candidate_dropped` in `build_report.json`) — a
  single legal move gives KL exactly 0. (b) Registry assertion:
  the build aborts listing offenders if corpus game ids ∩ the
  do-not-train registry (6,161 games) ≠ ∅. (c)
  `build_report.json` records `input_hashes` (sha256 of
  `labels.jsonl` and of the corpus's `corpus_manifest.json`;
  the manifest's presence is asserted).
- **§4.4 swap test.** `swap_test.py`'s `make_swapped` now
  requires a hand/deck pair whose cards **differ** (first such
  (i, j); a snapshot with no differing pair is unswappable) and
  records the swapped card ids. `featurize_snapshot.php` emits
  **`debug_opp_hand`** — the parsed opponent hand via
  `SimFeat_ZoneIDs(GetHand(3−player), HandPieces())` — as a
  debug field **outside** `state`. For every tested snapshot
  the A/B debug hands must differ as sequences; equal (or
  missing, or a featurize error) counts as **INVALID** —
  excluded from `tested`, never a pass. The verdict reads
  INVARIANT only with zero failures, zero invalids and ≥ 20
  tested per arm; otherwise it reads NOT ESTABLISHED (or
  INVARIANCE FAILURE when a genuine failure occurred).
- **Corpus tree product hash.** `run_capture_corpus.sh` now
  **asserts** the capture-patch product
  (`search.php` == `044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d`)
  where the corpus tree is prepared, in place of merely
  recording it; `run_pilot.sh` re-asserts it before the
  equivalence phase.

## §6 Syntax + new full code manifest

Syntax checks (all passed 2026-10-25, after the fixes):
`bash -n` on every `.sh`; `python3 -m py_compile` on every
`.py` (including the two fixture scripts); `php -l` on both
changed `.php` files (on the box); `t1_config.json` unchanged
and parses.

Changed files (build-package §10 hash → new hash):

| file | was | sha256 (new) |
|---|---|---|
| analyze_distill_gate.py | `de65600e…` | `1dad9f6d637ab53ce7908a3654a036c45e94e583f7aa3d6d81299404023bff70` |
| distill_label_main.php | `4fcb960e…` | `4f1de80a2babd84bbdc7a162d1b9f1c70670b746e4637d15b91793d150798943` |
| featurize_snapshot.php | `bef241d1…` | `db93666c9c3ac6a94445b805ce61f107705300b44dda91bd668460b40886f0cf` |
| label_reduce.py | `c3b0511c…` | `e2244fbb70ac0282490c155d527a0b1e0e60a5387b81ce0a4be9eeac2d73bb8c` |
| pilot_prep.py | `a9bcc1a6…` | `3131264b9f02e002926199ee7fcf8bf9c3f217cae87a758d009118076d284a30` |
| pilot_report.py | `ec67ee5c…` | `45b557418c0517d4dd06562c17460e5fe8923c1d926e17788a33eaf54f85ad94` |
| pilot_times.py | `d4a811a9…` | `c0556e2ae0b1d6d21125ff1ac787871398ec765b0b0fcf35902074171f2ef93e` |
| pregate_compare.py | `b961b125…` | `56ddcb5ee86ef96c200b25b317ce5b9e91c8020c1eca82eb35c37d638d0e4b68` |
| run_capture_corpus.sh | `4d04b5a6…` | `10c4e570d984625dbd23d9568b0f20352cfdb1c56c56f8a0ad7271141a15980b` |
| run_distill_gate.sh | `9e60d46b…` | `279e48d27f1d26ca350b5d4093118706e1ddf07ac5b67db881a74c9fbdbe2de2` |
| run_pilot.sh | `067aced0…` | `eff185fd24752130c918bbc1eda0e323a384f780340a0df036bd33de98800cfb` |
| swap_test.py | `04777aac…` | `57ffab75673a8ec577b087fa45227d05cfc36e13e2bb0bf5fd78167553d1977f` |
| t1_build_data.py | `81156422…` | `7f758c921049d5fd5d83f2a02db3c36116dcfbab399afa163a76c5e576135b95` |
| t1_trainer.py | `2b1735aa…` | `44d169363e14fced729dbfdeae8ce9a26e50f7edd547a0ee7af77fd6df100da3` |

Staged alongside, byte-identical borrowings (new to the code
dir; see §0.2):

| file | source | sha256 |
|---|---|---|
| parse_r3_pair.py | round 7 | `ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1` |
| patch_census_probe.py | round 5 | `60a3808c9de55671cffb13bc01dcda8e84160da7c564a18ce23692661c3de8fd` |
| tally_census.py | round 5 | `fe2480bbab8eba2e8082f158459b5494566f2254c31a56c1c8ce917607cc9267` |
| shm_sweep.py | round 7 | `98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33` |

Unchanged from build-package §10: `build_swap_jobs.py`
(`0871f371…`), `featurize_corrected.php` (`3dcf32c9…`),
`g8_sweep.sh` (`82b4d58c…`), `merge_registry.py` (`13a655e3…`),
`patch_capture_uncontested.py` (`68c92679…`),
`patch_featurize_correction.py` (`1594c864…`),
`run_distill_pregate.sh` (`dcb5037f…`), `run_gravy_census.sh`
(`5dd71d58…`), `run_label_corpus.sh` (`4983f70d…`),
`t1_config.json` (`43e12cc2…`).

Fixtures (`rounds/round8/fixtures/`): `README.md`,
`shim_analyze_rows.py`, `make_pregate_fixture_rows.py`,
`pregate_r7_rows.jsonl`, `pregate_fixture_report.json`,
`analyze_r7_output.txt`, `analyze_r7_report.json`,
`retry_fixture.log`, `retry_fixture_rows_final.jsonl`,
`retry_fixture_rows_control_final.jsonl`.

## §7 §5 — preservation record (V2 source set)

On 2026-10-25 the gate fleet's V2 source set was copied from
`/tmp/gate_r4` (tmpfs) to durable disk at
**`/home/joe/tcg/gate_r4_v2_preserve/`**: **915 snapshot dirs**
(across the 8 `gate_c{X}_teacher_s{Y}_snaps/` stream dirs) and
the **8 `search_stats.jsonl`** files (28,120 lines total),
together with `MANIFEST.sha256` covering **15,052 entries**.
Plainly stated: the manifest file itself lists an empty
self-entry (its own line carries no hash), which is why a full
manifest check verifies 15,051 entries OK out of 15,052 listed.
Manifest sha256:
`f4d0cd09f2290a948a916f86d1f40617aa8943e0b9f2563e0894a4fbe10b63a3`.
Spot verification at copy time: the manifest check passed
(15,051 OK), and one full stat file was verified hash-identical
to its `/tmp` original (`f5aef0c0…`). The pilot's V2 prep reads
only this preserved copy.

---

*End of fix package. Staged for the builder's audit and commit;
nothing in this package has been run beyond the §2.3 fixtures
above, and no stage runs before the reviewer's approval of this
fix at its committed sha and Joe's go for that stage.*
