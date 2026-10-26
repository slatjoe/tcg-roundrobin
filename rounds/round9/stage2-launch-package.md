# Round 9, Stage 2 — launch package

**Status: FOR CLAUDE'S CODE REVIEW. This package approves nothing and launches nothing.** Stage 2 runs only after (i) Claude's approval of this package at its committed sha, (ii) Joe's explicit go in the TCG chat, (iii) the launched sha equals the approved sha (rounds-only diff aside), and (iv) the ghost pre-gate (§3.3) has passed IDENTICAL — the games runner must not start before it.

Basis: Claude's Stage 1 ruling, `claude-reply-d7b92fd.md` §3 (numbering below is his), and the Stage 2 registration in `gravy-calibrated-search-design.md` §5. The calibrated setting is H8k-180+H from the Stage 1 report (`stage1-report.md`, commit d7b92fdf): hooks 8,000, deadline 180 s, horizon 62 at −1, k 25, margin 1.5 — per-state completion 1.0000 (240/240) at mean wall 26.5486 s. The ruling's §2 finding stands behind the whole stage: the bounds are inert and the calibration *is* the horizon — H8k-180+H is B0+H with headroom, and Stage 2 exists to test whether the calibrated teacher converts live, not to assume it.

All pinned values live in one file, `code/settings_stage2.json` (teacher tuple, label tuple, games, bands, panel/fleet references, timeout derivation). The runners build their env pins from it; the analyzers audit every stamped row against it — the Stage 1 two-placement pattern throughout.

---

## 1. Clause-by-clause: ruling §3 → this package

### §3.1 The live teacher build — `code/search_s2.php`

Byte-derived from `code/search_s1.php` (sha256 1fcacaa3…); the full change set is `fixtures/search_s2_diff.txt` and nothing else changes. Three changes:

1. **The tuple** (`SimTeacher_Tuple`). The run's parameters `{name, hooks, deadline_s, horizon, horizon_value, k, margin}` are read from env `TEACHER_TUPLE_JSON`, validated field by field (types, ranges; k ∈ [20, 1000] against the ≥20 finished-worlds validity floor), resolved at the top of `SimTeacher_DecideInner` **before any eval or decision**, and stamped as `"setting"` on **every** teacher stat row Decide/DecideInner writes (contested, uncontested, capture, thin-prior/base, eval-failure, and the wrapper's exception row). A present-but-malformed pin throws; the Decide wrapper logs the abort with the stamp `{"name": "malformed"}`; the games report fails the run on any such row (§3.4 audit). **Unpinned, the tuple is the legacy constants** (hooks 4000 via the label default, deadline 180, horizon 0/off, horizon_value 0.0, k 25, margin 1.5), so an unparameterized call reproduces the pre-Stage-2 live teacher and the registered label instrument exactly (fixture-proven, §6).
2. **DecideInner parameterization.** `$K`, the per-candidate parent deadline, and the paired margin `1.5 * $seD` now read the tuple. The rollout children are forked with `"horizon" => $T["horizon"]` and `"hookBudget" => $T["hooks"]` in cfg — the two keys the live path never passed before, which is why the children used to run at horizon-off and the 4,000 label default. The guards themselves are the existing code, now fed by the live tuple:

   ```php
   // SimLabel_ChildChoose / SimLabel_ChildDQ (unchanged lines):
   $GLOBALS["ssHooks"] = ($GLOBALS["ssHooks"] ?? 0) + 1;
   if (($GLOBALS["ssHooks"] ?? 0) > intval($GLOBALS["ssLabelHookBudget"] ?? 4000))
     throw new SimSearchAbort();
   // SimLabel_RunRollout (unchanged line):
   $GLOBALS["ssLabelHookBudget"] = intval($cfg["hookBudget"] ?? 4000);
   // SimTeacher_DecideInner (new): cfg carries
   //   "horizon" => intval($T["horizon"]), "hookBudget" => intval($T["hooks"])
   ```

   The fixture proves the guard follows the *live* tuple both ways: planted 6,000-hook worlds complete under a pinned 8,000 and abort under a pinned 4,000 (§6, fx_s2_live).
3. **The horizon value inside the means.** When a finished world's `winner` is 0 — horizon-ended or a natural draw — DecideInner prices it at `$T["horizon_value"]` in the candidate means, where it changes picks. Raw outcomes are untouched everywhere else. (Flag F3 below on the natural-draw case.) Per-candidate tallies land on the stat row: `n_horizon`, `n_draws`, and `horizon_life` (§3.2), so the valuation is auditable from the row.

The (b) featurizer correction stays out — this lineage never carried it.

**Valuation flip, proven through the live path** (fx_s2_live, not the offline analyzer): a planted root decision whose prior pick's worlds all lose (−1) and whose challenger's worlds all end at the horizon (raw outcome 0) — Decide picks the challenger and overturns at horizon_value 0.0 (the 0.5-equivalent: outcome 0 is score 0.5), and keeps the prior pick with means {−1, −1} at horizon_value −1. Same code, same state; only the pin differs.

### §3.2 Life totals at the horizon — fields `life_root` / `life_opp`

`SimLabel_RunRollout` records, on **every world that ends at the horizon** (and only those), `life_root` and `life_opp`: both players' life totals in root frame, read through `GetHealth()` — the same accessor `play_game.php` uses for its `p1life`/`p2life` result fields. They appear:

- **in the L3 label rows** (the result object), so `stage2_analyze.py` prices the life-differential co-report per world exactly: ahead = win, behind = loss, tied = draw at the primary's draw price (0);
- **in the live stat rows** as per-candidate tallies `horizon_life = {ci: {ahead, behind, tied, life_root_sum, life_opp_sum}}` over that decision's horizon worlds — the live path emits no per-world rows (it never has), so the decision-level record carries the counts from which the life-differential candidate means are computable. Flag F2: if Claude wants per-world live capture, that is a change to ask for, not one smuggled in.

Fixture: planted horizon worlds with root behind 8 vs 14 produce `life_root=8, life_opp=14` on every label row and `horizon_life[1] = {ahead 0, behind 25, tied 0, sums 200/350}` on the live row; non-horizon worlds carry no life fields anywhere.

### §3.3 Ghost pre-gate — `code/run_stage2_pregate.sh` + `code/pregate_check.py`

Before any live game: the new build, tuple pinned as in the games, `TEACHER_GHOST=1`, against raw v10 through the standard instruments on the round-7 pre-gate seed block (8501–8510, both seats; flag F4): determinism (seat-1 raw rerun), the R16 seat-crossed raw control, ghost-vs-raw outcome and gamelog equality per seed, the driver-manifest checks, and **K6 as registered** (claude-reply-1ab9903 §2) implemented mechanically in `pregate_check.py`: the line *(rollout rows, unstamped, unstamped-not-thin-prior, unstamped-with-pick≠prior)* per seat; the assert is satisfied iff every other ghost check is true and the last two counts are 0. Thin-prior should now be ~0 at the calibrated setting, so K6 should rarely apply — it is implemented regardless. The checker is fixture-proven on planted records (clean / K6-only / one-bad-row / diverged-gamelog). The pre-gate's game ids merge into the registry (tag `round9-stage2`) only when the verdict is IDENTICAL; the runner exits non-zero otherwise.

### §3.4 The games — `code/run_stage2_games.sh`

200 games: calibrated teacher vs heuristic, Gravy mirror, **seeds 22001–22100 × both seats**, instrument 87/62, four blocks in parallel (s1a/s1b/s2a/s2b, 50 seeds each, per-block tree copies of the fleet tree with `search_s2.php` installed and hash-asserted), the tree's patched servers (ab85fa1b…), per-block snap dirs — **every overturn captured** with its snapshot and index row. Containment: G8 sweep pre-launch, one (C) kernel-attribution sweeper per tree, `TCG_CLEAN_CHILDREN=1`. **Registry merge before analysis** (all four blocks' game-id files, tag `round9-stage2`). Then `code/stage2_games_report.py`: tuple audit over every teacher stat row (any mismatch or malformed-pin abort fails the run before any rate is believed), game accounting (completed / invalid / **teacher timeouts reported; there is no paired arm**), live rates, and the draw-scored outcomes.

**Game timeout — derived from the tail, shown in full** (inputs are published records; the same numbers are in `settings_stage2.json`):

| input | value | source |
|---|---|---|
| per-decision wall mean | 26.5486 s | `data/stage1/stats_H8k-180+H.jsonl` (240 panel decisions) |
| per-decision wall p95 | 46.820 s | same file (report cross-check: 46.8204) |
| per-decision wall max | 56.382 s | same file (report: 56.382) |
| cross-check B0+H | mean 26.5662 / p95 46.877 / max 55.838 | `data/stage1/stats_B0+H.jsonl` |
| contested per game mean | 23.5725 (9,429 / 400) | `data/round7` fleet stat files, published |
| contested per game p95 | 39 | same |
| contested per game max | 57 | same |

Products: p95×p95 = 1,826.0 s; max×p95 = 2,198.9 s; p95×max = 2,668.7 s; **max×max = 56.382 × 57 = 3,213.8 s → TIMEOUT = 3,214 s** (ceil). A timeout is a validity bound, not an estimate — it must not kill a game the instrument could legitimately produce — so both factors are the observed maxima of the registered populations. For scale: the mean-priced game is ~626 s, a p95 game ~1,826 s, and the round-7 fleet's timeout under the old bounds was 3,870 s.

### §3.5 L3 — `code/run_stage2_l3.sh` + `code/s2_label_main.php` + `code/build_s2_jobs.py` + `code/stage2_analyze.py`

Every captured overturn becomes a job (`build_s2_jobs.py`: `selected` = the {prior, teacher} pair, candidate records verbatim, snap dirs asserted, jobs sharded by game), labeled by `s2_label_main.php` — the Stage 1 clause-8 pin pattern derived from `s1_eval_main.php` (diff in fixtures) — at **LABEL_W=50, pair "va", CRN, production server** (81ef2cdb…), **seed bases 955001 + shard × 10⁸**, horizon 62 pinned in the label tuple (L3-W50+H: hooks 8000, deadline 180 — flag F5). Jobs carry the tuple; the driver aborts on any mismatch before labeling; every row is stamped.

The analyzer renders, from one set of rows: **PRIMARY = horizon-aligned (62) at draw = 0** (finished world scores 1 iff the root player won it; draws score 0, the Swiss price), **co-report at draw = 0.5**, **co-report at the life-differential price** from `life_root`/`life_opp`; game-clustered bootstrap CI (the stock scorer's, B=10000); unfinished share and refusal tallies in the Stage 0 taxonomy (the four refusal classes excluded and tallied; everything else unfinished); the exactly-50 world-count guard; fallbacks.

### §3.6 Bands — as registered, unchanged

Per-game gain = primary mean diff × **live** overturns/game (from the games report — the live run's rate, never the panel's). **PROCEED** iff CI lower bound > 0 AND per-game gain ≥ +0.05. **DOES NOT PROCEED** iff mean > 0 but the CI includes 0, or per-game < +0.05. **STOP** iff mean ≤ 0. **Tripwires:** per-game gain > +0.25 OR mean diff > +0.20 → the L1/L2-form impeachment checks run **before the read is reported**, in the output and in this order: (i) leave-one-game-out range of the primary mean, (ii) the L2 sensitivity read (unfinished worlds priced as draws at 0.5 in score units, pairs dropped only on a refusal), (iii) the per-game table. Fixture-proven: the planted tripwire population prints `TRIPWIRE FIRED` and all three checks before the `PRIMARY` line, with hand-computed values (LOGO range [0.0, 0.75]; sensitivity 0.364583…).

### §3.7 Co-reports

In `stage2_analyze.py`'s output, from the games report: **live thin-prior rate and live overturn rate** against the panel's (0 and 0.0917 at draw = 0); **the games' draw-scored outcomes** (teacher W/D/L and points per game) beside the fleet's round-7 record (teacher 216.0 = 173W/86D/141L, raw 213.0, over 400 paired games — different seed block, unpaired: a co-report, not a comparison test).

### Standing clauses

Containment as above in every runner; registry merges before analysis; status-only interim notices; every pin literal in the runners is a 64-hex literal passed through `expect_hash`'s format assert; every runner block that spawns or waits carries a verbatim-extraction fixture (§5).

---

## 2. Cost model — priced from Stage 1's wall tail

Claude's extrapolation (~26.5 s × 23.6 ≈ 10–11 min/game → ~35 box-hours serial) is the **mean-priced cross-check**, and it checks out exactly: 26.5486 × 23.5725 = 625.9 s/game → 200 games = **34.8 box-hours serial**. The planning price, per the brief, comes from the tail: p95 wall × p95 contested = 1,826.0 s/game → **101.4 box-hours serial-equivalent**; the games runner's 4 blocks run concurrently, so the wall-clock planning bound is ~25 box-hours at the tail price and ~9 at the mean price, before server contention (two blocks share each seat server; Stage 1's walls were themselves measured at 4-shard contention over two servers, so the inputs already carry comparable contention). Pre-gate: 20 ghost games ≈ 3.5 box-hours serial-equivalent (two seats concurrent) + 30 fast raw games. L3: Stage 1's per-world cost was 26.5486 s / (2.8375 cands × 25 worlds) = 0.374 s/world; an L3 job is 100 worlds → ~37 s/job; at the ruling's extrapolated ~2.2 overturns/game (~440 jobs, labeled an extrapolation there and here) ≈ 4.6 box-hours serial, ~1.2 h over 4 shards.

## 3. Run order

1. `run_stage2_pregate.sh` → `pregate_check.py` must print IDENTICAL (registry merge of pre-gate ids included). **No live games before this passes.**
2. `run_stage2_games.sh` — pins, tuple from settings, 200 games, registry merge, games report (tuple audit must be OK).
3. `run_stage2_l3.sh` — jobs, labels, `stage2_analyze.py` read against the bands.
4. Publication (at report time, mirroring Stage 1): commit the report with `data/stage2/` (driver rows, stat logs, snap indexes, label rows gz, jobs, manifests, analyzer outputs) so the read is recomputable from the repo alone.

## 4. Runner blocks and their fixtures

Every block that spawns or waits, enumerated; `fixtures/fx_s2_blocks.sh` extracts each **verbatim** and executes it against stubs (servers that load / servers that stay silent, workers that succeed / one worker that fails):

| runner | block | spawns / waits | fixture result |
|---|---|---|---|
| pregate | PS-SRV | 2 patched servers + load wait | loads → completes; silent → aborts |
| pregate | PS-SWEEP | 2 (C) sweepers | 2 spawned |
| pregate | PS-GHOST | 2 ghost drivers + wait | both run; one failing fails the block |
| games | GS-SRV | 2 patched servers + load wait | loads → completes; silent → aborts |
| games | GS-SWEEP | 4 (C) sweepers | 4 spawned |
| games | GS-DRIVERS | 4 block drivers + wait | all run; one failing fails the block |
| l3 | LS-SRV | 2 production servers + load wait | loads → completes; silent → aborts |
| l3 | LS-SWEEP | 4 (C) sweepers | 4 spawned |
| l3 | LS-SHARD | 4 shard subshells (8 label runs) + wait | all run; one failing fails the block |

The raw pre-gate arms and the L3 seat groups inside each shard are foreground-sequential driver calls — they spawn nothing in the shell and carry no block; the drivers' own subprocess supervision is the paired driver's / label driver's, exercised in their fixtures.

**Fixture-section note (etiology).** The Stage 1 launch abort came from the line `PIDS="" FAIL=0 pid`: harmless inside Stage 0's function (where `local` made it a three-variable declaration), lethal when transplanted to top level, where bash reads it as assignments prefixing a nonexistent `pid` command. Every Stage 2 runner uses the clean two-name form (`PIDS="" FAIL=0`, or `local` with exactly two names inside functions), the three-name form appears nowhere, and `fx_s2_blocks.sh` greps every runner for it — a transplant that reintroduces it fails the suite.

## 5. Fixtures — all suites PASS (109 checks)

Runner: `fixtures/run_fx_s2.sh`; full transcript: `fixtures/fx_s2_outputs.txt` (run on PHP 8.3.6 CLI with pcntl; the box PHP 8.5 qualifies equally).

| suite | checks | proves |
|---|---|---|
| fx_s2_live | 37 | §3.1 flip through the real Decide path at both horizon values; tuple stamps on contested rows; malformed-pin aborts (missing field, k=10) before any decision; hook guard follows the live tuple (6,000-hook worlds: complete at 8,000, abort at 4,000); unpinned = legacy; §3.2 live `horizon_life` tallies; label-path default regression (unparameterized = horizon off / 4,000 hooks: draw worlds unfinished, hook worlds abort) and horizon-armed label rows carrying `life_root`/`life_opp` |
| fx_s2_label | 14 | L3 driver pins, aborts (job k≠pin, missing setting), row/stat stamps incl. teacher_pick, life fields pass through, cfg forwarding (W=50, 62, 8000, 180, va) |
| fx_s2_blocks | 21 | §4's block table + inventory guards + the three-name-form grep |
| fx_build_s2_jobs | 10 | job shape, selected pair, tuple stamp, shard partition, aborts (teacher==prior, duplicate snap) |
| fx_pregate_check | 5 | IDENTICAL (clean), IDENTICAL under K6-only unstamped thin-prior rows (line 13 3 0 0), NOT IDENTICAL (one unstamped non-thin row), NOT IDENTICAL (diverged gamelog) |
| fx_stage2_games_report | 8 | games accounting, draw-scored points, live rates, tuple audit OK; audit failures (wrong tuple value; malformed-pin abort row) exit 2 |
| fx_stage2_analyze | 14 | hand-computed three reads (primary 0.375, draw05 0.40625, lifediff 0.4375), per-game gain at the live rate, tripwire + impeachment-before-read with exact LOGO/sensitivity values, unfinished/refusal accounting, STOP on the negated population (primary −0.4375 — at draw = 0 the read is not antisymmetric under negation, as it should not be), tuple-stamp abort, world-count guard |

One fixture find worth naming: the games-report fixture caught a real bug in `stage2_games_report.py` (its per-candidate map normalizer was applied to the string-keyed `abort_reasons` map and would have crashed the production report). Fixed in the report code; the fixture now covers it.

## 6. Hashes (machine-copied at build time)

New code:

| file | sha256 |
|---|---|
| code/search_s2.php | `85490e8ed1ef1587b31112c572a55bc1f521202f2068415e1ce285e838f0d8fa` |
| code/s2_label_main.php | `c7a76af4fb59e8e6e0b69a6d06157efc44597b04238cdb3b2efe48350cdda888` |
| code/settings_stage2.json | `2a1634ccbe67cf2f16993a1e38fc4df6005c492cb9dd769d59c9b3c19cd72f50` |
| code/build_s2_jobs.py | `b91f3a6c27fcc8abb060ed4efa351f71f112cc971932cfe4ba41623c6d84851d` |
| code/stage2_games_report.py | `eb514b4ed7c383e68ca96aca79d0fbf5a819cafea2ade68601f9726116a547e9` |
| code/stage2_analyze.py | `3ad70bbc41b04f62b90755e5e0fc03b380ec285f316f1de73abea9349a3a2cf4` |
| code/pregate_check.py | `bc5327d380dfe73308ac2ce737e527a568c0de42a8f80f82d8775f481290496a` |
| code/run_stage2_pregate.sh | `b26f0ebfce8928d6122c1005240967627e16a62aa57fbad18e59a09efbc23418` |
| code/run_stage2_games.sh | `48e88557938d66fed4ed28530593424d280a2f1968022621c9b8215230bd26ad` |
| code/run_stage2_l3.sh | `7bd3d33158cc6a4d4b2b96a50812f1d610cb49ede933bec077b2f510312c007a` |

Derivations: `fixtures/search_s2_diff.txt` (`c12a5cd8…`), `fixtures/s2_label_main_diff.txt` (`8c92d1c6…`). Reused unchanged and pinned in the runners: paired_driver_gravy.py `3389b1b9…`, stage0_report.py `5c7e5393…`, analyze_l3.py `16017ffa…`, merge_registry.py `13a655e3…`, shm_sweep.py `98027a8b…`. Every pin literal in the three runners passed `expect_hash`'s `^[0-9a-f]{64}$` format assert at build time (the literals were machine-injected from these hashes and from the committed Stage 0/1 constants, then `bash -n` verified).

## 7. Flags for the reviewer (judgment calls, named rather than buried)

- **F1 — horizon_value units.** The tuple carries horizon_value in outcome units (−1), consistent with the settings' stamped −1 from Stage 1. The fixture's comparison arm is horizon_value 0.0, which *is* "draw priced 0.5" in score units (score = (outcome+1)/2). The package doc and settings file state the mapping explicitly.
- **F2 — live life data is tallies, not world rows** (§3.2 above).
- **F3 — natural draws in the live means.** A finished world with winner 0 that is *not* horizon-ended is also priced at horizon_value in Decide's means — the same convention as the analyzer reads, where the draw price applies to drawn worlds. Rollouts rarely produce natural draws before turn 62; if the reviewer wants horizon-only pricing in the means, it is a one-line change plus a fixture case.
- **F4 — pre-gate seeds.** 8501–8510 reused from the round-7 pre-gate: the standard instrument block for a new build's ghost test. The games join the do-not-train registry under the round9-stage2 tag.
- **F5 — L3 child bounds.** The label tuple runs the label children at the calibrated bounds (8000 hooks / 180 s) rather than the Stage 0 label defaults (4000 / 300): Stage 2's L3 audits the calibrated teacher, and the registration pins W, the bases, and the horizon for L3 but not separate child bounds. The unparameterized-default regression (the registered label instrument) is proven separately in fx_s2_live and is unaffected — the driver always pins explicitly.

**This package approves nothing and launches nothing.** It is staged for Claude's code review; Stage 2 launches only on his approval of the committed package, Joe's go, and launched sha == approved sha, with the pre-gate first.
