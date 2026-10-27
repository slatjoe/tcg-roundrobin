# Round 9, Stage 3 — launch package

**Status: FOR CLAUDE'S CODE REVIEW. This package approves nothing and launches nothing.** Stage 3 runs only after (i) Claude's approval of this package at its committed sha, (ii) Joe's explicit go in the TCG chat, (iii) the launched sha equals the approved sha (rounds-only diff aside), and (iv) the launch conditions in §6 hold — including the pre-gate coverage condition: **no new pre-gate is run; Stage 2's IDENTICAL covers this build and tuple, and the games runner gates mechanically on that manifest. Any change to `search_s2.php` or to the teacher tuple voids the coverage and requires a new pre-gate before any launch.**

Basis: Claude's ruling on the Stage 2 report, `claude-reply-d593faf.md` — §4 is the registration this package implements clause by clause; §3 carries two homework items, discharged in §2 (G8) and §3 (free-space pre-flight) of this package. Stage 2's result, which Stage 3 exists to test at game level: the calibrated teacher's overturns carry an L3-measured per-decision edge (primary +0.0621 [0.0440, 0.0809], per-game gain +0.1096 at the live rate) — a valuation under the rollout continuation, not a game-level win. The ruling's caution stands behind the whole stage: round 7's projection overstated, and Stage 2's unpaired games (teacher 87/200 = 0.435) lean the same way. **Stage 3 is the test.**

All pinned Stage 3 values live in `code/settings_stage3.json`: its `teacher_tuple` and `label_tuple` are byte-identical to Stage 2's (deep-equality verified at build time; the teacher tuple's canonical `json.dumps` string equals the string recorded in Stage 2's pre-gate manifest), so the Stage 2 placements — runner-built env pin, analyzer audit — carry over unchanged in form.

---

## 1. Clause-by-clause: ruling §4 → this package

### §4.1 Form — paired fleet (`code/run_stage3_games.sh`, `code/stage3_games_report.py`)

- Paired calibrated teacher against raw v10: a pair is (seed, seat); both arms play that seed from that seat against the heuristic, Gravy mirror (deck `nats2026_eriksen_gravy_60.txt`), instrument parameter 87 / draw trigger 62 (the paired driver sets `TCG_MAX_TURNS=87`; the trigger is the engine's parameter − 25).
- **Seeds 23001–23200 × seats {1, 2} × arms {teacher, raw} = 800 games, 400 pairs.** Blocks of 100 seeds: teacher t1a 23001–23100 seat 1, t1b 23101–23200 seat 1, t2a seat 2 low half, t2b seat 2 high half; raw blocks r1a/r1b/r2a/r2b mirror the teacher layout exactly.
- The teacher is `code/search_s2.php` (sha256 `85490e8e…`) with the H8k-180+H tuple, pinned by `TEACHER_TUPLE_JSON` built from `settings_stage3.json`, stamped on every teacher stat row and audited by the games report exactly as in Stage 2 (tuple audit failure = exit 2, the run is not a measurement). Raw is v10 on the same fleet tree with the teacher off (`paired_driver_gravy.py --arm raw`, the plain policy bridge); raw trees keep the fleet tree's own `search.php` (`8f6b35da…`, hash-asserted) — no Stage 2 build is installed in them.
- Every overturn is captured: teacher blocks run with `TEACHER_SNAP_DIR` per block, snap indexes feeding the attribution jobs (§4.6).
- **Concurrency (ruling §4.5's condition):** the teacher phase runs 4 blocks over the tree's 2 patched servers — Stage 2's exact concurrency. The raw phase starts only after the teacher phase completes (separate runner section, servers restarted inside the RS-SRV block); **the raw arm is never concurrent with the teacher arm.**

### §4.2 Pre-gate — Stage 2's IDENTICAL, mechanically gated

No new pre-gate run. `run_stage3_games.sh` carries the PREGATE-GATE block (the Stage 2 block, verbatim in substance) reading `${STAGE2_OUT}/pregate/pregate_manifest.json` **before** the G8 sweep and any spawn, aborting unless all three hold: the recorded verdict is IDENTICAL; the recorded `search_s2_sha256` equals this run's pin `85490e8e…`; the recorded `teacher_tuple_json` equals the tuple this run builds from `settings_stage3.json`. An absent or unreadable manifest aborts. The block's pin literal is format-asserted inside the block. Fixture: `fx_s3_blocks` runs the extracted block against a **byte-copy of the published Stage 2 manifest** (`rounds/round9/data/stage2/pregate_manifest.json` — the real writer's output, not a plant): the real manifest passes; copies with the verdict, the hash, or the tuple altered each abort; an absent manifest aborts.

### §4.3 The primary read — `code/stage3_analyze.py`

- **Pairing** is built by `stage3_games_report.py` (draft `--pairing-only` pass for the rerun step, then the final `pairing.json` in the full report): for each (seed, seat) in 23001–23200 × {1, 2} — exactly 400 attempted pairs, asserted — the teacher row and the raw row (a raw rerun row replaces its original; §4.5). Pair statuses: `scored`; `teacher_timeout` (scored in the primary as a teacher loss, §4.5); `dropped_raw_timeout` (out of the primary, listed); `excluded` (any other invalid or missing row, reason recorded, listed).
- **Scores (draw = 0):** a game scores 1 iff its arm's player won (`winner == seat`); a draw, a cap, or a loss scores 0. A teacher-timeout pair scores the teacher 0. Pair diff = teacher score − raw score ∈ {−1, 0, +1}.
- **PRIMARY: the pooled paired Δ at draw = 0** — the mean pair diff over scored pairs (statuses `scored` + `teacher_timeout`). **CI: seed-clustered bootstrap, B = 10,000** — both seats of a seed form one cluster; clusters are resampled with replacement and the statistic is the pooled mean over the resample's scored pairs; percentile interval with the `analyze_l3.py` indexing convention; the bootstrap rng seed (20261027) is registered in `settings_stage3.json`.
- **Co-reports:** Δ at draw = 0.5 (a draw scores 0.5 for both arms; a teacher timeout still scores 0 — a timeout is a loss at both prices); the **game-level life-differential** — per game, `life_score` = 1 iff the arm's player won **or** (the game was capped and the arm's player is *strictly ahead* on life at the cap), else 0, computed from the driver rows' `p1life`/`p2life` in the arm's seat frame (the paired driver already records both life totals on every completed row — verified against Stage 2's published rows; no driver change); Δ_lifediff = the mean over scored pairs of (teacher life_score − raw life_score); **per-seat Δ** at draw = 0.
- **Reconciliation before any read** (analyzer): attempted pairs == 400; its teacher stat-row count equals the games report's; the games report's tuple-audit-ok flag must be true, else abort (exit 2); gamename uniqueness across completed rows is asserted (the confirmation's not-condition (b), implemented here); and the **R14 root-canary refusal class is named and counted** — stat lines with `fallback == "canary"` and no teacher stamp (the missing-card conservation check refusing a root decision; that decision plays down the plain bridge and writes no teacher row) — printed by name with its count, never carried as an unexplained difference (ruling §1: Stage 2's 20,013 − 20,009 was exactly this class, 4 records).
- **Bands (§4.4):** **CONVERTS** iff the CI lower bound > 0; **DOES NOT CONVERT** iff the CI includes 0; **HARMS** iff the CI upper bound < 0; **INCONCLUSIVE** iff teacher timeouts exceed 2% of teacher games on final counts (§4.5) — INCONCLUSIVE overrides the other bands. **Impeachment:** primary Δ > +0.25 → the impeachment checks print **before** the verdict line, in this order: (i) the leave-one-seed-out range of the primary mean, (ii) the drop-the-teacher-timeout-pairs sensitivity table, (iii) the per-seat table, (iv) the per-teacher-block pair table. The `VERDICT:` line is always last.

### §4.5 Timeouts — 3,214 s, kept; derivation replaced

**GAME TIMEOUT = 3,214 s for both arms.** The derivation is now Stage 2's measured game walls: mean 503 s, p95 807 s, **max 2,143 s** over 200 games at the calibrated setting under 4-block contention — 3,214 s is 1.50× the observed maximum, with 0 timeouts observed. **The product-of-maxima derivation (per-decision wall max × contested-per-game max) is retired**; the registration records why (Stage 2's contested-per-game max rose to 90 while per-decision walls fell — the direct game-wall measurement replaces the product). Scoring: a teacher timeout counts as a teacher **loss** in the primary, with the drop-the-pair sensitivity table co-reported; **teacher timeouts > 2% of teacher games (final counts) → INCONCLUSIVE**; a raw hang is **re-run once** (the runner's RAW-RERUN section: the draft pairing identifies raw `invalid == "timeout"` rows, and the paired driver re-runs exactly those seeds for that block/seat into a rerun file the pairing builder substitutes); a second hang **drops the pair**, listed — at draw = 0 a draw score would credit the teacher, so round 7's 0.5 raw rule does not carry.

### §4.6 Attribution — L3 on all teacher-arm overturns (`code/build_s3_jobs.py`, `code/run_stage3_l3.sh`, `code/stage3_attr_analyze.py`)

Every overturn captured in the teacher arm becomes a job (the Stage 2 jobs builder's semantics: `selected` = the {prior, teacher} pair, snap dirs asserted, jobs sharded by game), labeled at the Stage 2 label instrument — **LABEL_W = 50, CRN, pair "va", production server, label tuple L3-W50+H** — under a **fresh label seed family: bases 1055001 + shard × 10⁸** (§4 of this package). The attribution analyzer is a fork of the *fixed* Stage 2 analyzer (the stamp audit in its fixed form: projection on the registered `label_tuple` keys only, extras ignored, wrong value or missing field aborts) and renders the same three reads (primary draw = 0, draw = 0.5, life-differential), the live Stage 3 rates against Stage 2's record, and the attribution line: **per-game gain** (= L3 primary mean diff × the Stage 3 LIVE overturns/game from the games report), the Stage 3 live overturn rate, and **per-game gain ÷ Δ** against the fleet's primary Δ from `stage3_read.json` — printed beside the Fai gate references (87% and 101%). The attribution is a co-report, not a gate: it carries no verdict bands. Its tripwire impeachment machinery (per-game gain > +0.25 or mean diff > +0.20 → checks before the read) is retained from Stage 2 — it impeaches the attribution read itself.

### §4.7/§4.8 Cost and standing clauses

Cost is priced in §5 from Stage 2 actuals. Standing clauses, all implemented: containment (G8 hardened sweep, §2, + one (C) kernel-attribution sweeper per tree in every phase); the free-space pre-flight (§3); registry merge (tag `round9-stage3`, over all blocks' game-id files incl. reruns) **before** the games report and analysis; status-only interim notices; every pin literal machine-copied and format-asserted through `expect_hash`; verbatim-extraction fixtures for every spawn/wait block (§7); **a round-trip fixture for every writer/reader pair** (§7); publication of `data/stage3/` with the report at report time; the tracker's phase rule as amended (flag F-S3-3).

---

## 2. Homework (a) — the G8 attempt-1 trip: explanation, hardened guard, fixture

**The evidence.** Stage 2 L3 attempt 1 (2026-10-27 04:32 EDT) aborted at the containment sweep with `ABORT: game processes are running; not cleaning.` The attempt's own log (`/home/joe/tcg/r9s2_out/l3_launch_aborted1.log`, read on the box) shows the jobs build completing (353 jobs, shards split) and then the abort — nothing was swept and no server started. Process listings taken immediately before and after showed **no** `play_game` or `paired_driver` processes. When attempt 3 ran the identical sweep three minutes later, it passed: its preserved `g8_before.txt` shows an **empty** shared-memory segment table. No game process existed at either moment.

**The mechanism.** The guard in `code/g8_sweep.sh` (the round-8 copy, used by every Stage 2 runner) is:

```
if pgrep -f '[p]lay_game' >/dev/null || pgrep -f '[p]aired_driver' >/dev/null; then
```

`pgrep -f` matches its pattern as a regular expression against the **full command line** of every process. The bracket form stops the guard matching *its own* text, but the pattern itself is the bare token `play_game` — it matches the **substring** anywhere in any command line: a process does not have to *be* a game; its command line only has to *mention* one. At 04:32 EDT the box carried exactly the traffic that produces such mentions: the relaunch sequence itself was being driven over ssh (remote command strings naming the run's files and logs), the Stage 2 tracker's poller was firing ssh checks against the same run directory on its 10-minute cadence, and two earlier launch attempts' shells and log tails were in flight. Any one of those command lines containing the substring `play_game` — in a path, a grep pattern, a filename — trips the guard while zero game processes exist. Which specific command line fired cannot be recovered after the fact (the guard records no match), and this package does not pretend otherwise; what the evidence settles is the *class*: the guard as written cannot distinguish a game process from a mention of one, and the attempt-3 pass on an empty segment table rules out the only alternative (a real game the listings somehow missed — a real teacher game would also have held segments and server sockets).

**The fix.** `code/g8_sweep2.sh` is byte-derived from `g8_sweep.sh` with **only the guard line changed** (verified by diff: the header comment plus one line) to require the executable token itself:

```
if pgrep -f '[p]lay_game\.php' >/dev/null || pgrep -f '[p]aired_driver_gravy' >/dev/null; then
```

A bare mention of `play_game` (a notes file, a path fragment) no longer trips; a real `php play_game.php …` invocation and a real `python3 …/paired_driver_gravy.py …` invocation still match. Bracket camouflage is retained. **Residual, stated plainly:** any command line containing the literal `play_game.php` token — an editor open on the file, an ssh command string that names the script — still trips the guard. That direction fails safe (a launch delayed, never a sweep over live games), and narrowing further (anchoring on argv structure) would risk the opposite failure — missing a real game whose invocation form differs. All Stage 3 runners call `g8_sweep2.sh` and pin it.

**The fixture** (`fixtures/fx_g8_sweep2.sh`, 8 checks) proves the discrimination with the **real** `pgrep` (only `ipcs`/`ipcrm` are stubbed, emitting a canned segment table with one stale segment): (a) clean table → the sweep proceeds and removes only the nattch=0 segment; (b) a background process whose command line carries the bare token (`play_game` in an argv[0]-forged mention, no `.php`) → the **old** guard aborts, the **new** guard proceeds — the attempt-1 vector, reproduced; (c) a command line carrying the `play_game.php` token in a longer string → both guards abort (the documented residual); (d) a genuine `play_game.php` invocation and a genuine paired-driver command line → the new guard aborts. A diff-confinement check asserts the two sweep files differ only in the header comment and the guard line.

---

## 3. Homework (b) — free-space pre-flight

Every Stage 3 runner that copies trees (`run_stage3_games.sh`: 8 trees — 4 teacher + 4 raw; `run_stage3_l3.sh`: 4 shard trees) carries a marked FREESPACE block after its pins and **before its first tree copy** (line order asserted by `fx_s3_blocks`). The block:

- measures the per-tree requirement **fresh** from the actual source tree at pre-flight time: `REQ_PER_TREE = du -sb "$GTREE"` bytes (the fleet tree measured 468,711,508 B ≈ 447 MiB on 2026-10-27; nothing is baked in);
- computes `REQUIRED = REQ_PER_TREE × N_TREES` and `AVAILABLE = df -B1 --output=avail` on the tree filesystem (/tmp);
- prints both, verbatim in form: `free-space pre-flight: required_bytes=<REQUIRED> (per-tree <REQ_PER_TREE> x <N_TREES> trees) available_bytes=<AVAILABLE> headroom_factor=1.25`;
- aborts (exit 1, before any copy) when available < required × 1.25, computed in integers (`AVAILABLE × 4 < REQUIRED × 5`).

**The 1.25 headroom factor, justified:** a copied tree is not the end of a tree's disk life — a running block writes its Games/ directories, gamelogs (a Stage 2 game log ran ~112 KB; a block holds 100 games), traces, and snap captures into or beside its tree for the phase's whole duration, and /tmp is shared with every other consumer on the box (it sat at 85% on 2026-10-27 with *other* runs' trees still resident). The copies alone at exactly 1.00× would leave the phase to discover exhaustion mid-run — which is precisely how attempt 2 died (its pin check caught a partial tree copy at a full /tmp; the pre-flight turns that discovery into a printed, sized refusal before anything is copied). 1.25 prices the copies plus a working margin without reserving so much that a healthy box refuses. Fixture (`fx_s3_blocks`, 6 cases over the two runners' extracted blocks, using the block's documented test seams for available/per-tree bytes): ample space proceeds with both sizes printed; short space aborts with both sizes printed; the straddle case (available between required × 1.0 and × 1.25) aborts.

---

## 4. Label seed family (registration for §4.6)

LABEL seed bases already used by this lineage: Stage 0 **855001** + shard × 10⁸; Stage 2 **955001** + shard × 10⁸ (shard ∈ 0..3 in both; family span at shard s is the working range above base + s × 10⁸).

**Stage 3 registers base 1055001 + shard × 10⁸.** Arithmetic clearance: at every shard offset the Stage 3 base sits exactly **+100,000,000** above the Stage 2 base and **+200,000,000** above the Stage 0 base; the families are disjoint at every shard, and no Stage 3 label seed can collide with a Stage 0 or Stage 2 label seed at the same shard. `run_stage3_l3.sh` carries `LABEL_BASE=1055001`; the round-trip fixture runs the real label driver at `MEAS_SEED=1055001` (§7).

## 5. Cost — priced from Stage 2 actuals

| piece | arithmetic | price |
|---|---|---|
| teacher arm | 400 games × 503 s (Stage 2's measured mean game wall at the calibrated setting, 4-block contention) | ≈ 55.9 box-hours serial ≈ **14 h wall** at 4 blocks |
| raw arm | round 7's raw games are not separately timed in the fleet record (flag F-S3-1); the raw policy plays a game in ~3.8 s of compute (gate record) and a raw game is bounded by the heuristic opponent's pace, so 400 raw games price at **≤ 1 h wall** at 4 blocks — an estimate on that basis, not a measurement | ~1 h wall (estimate) |
| attribution L3 | Stage 2's measured label cost: 35,300 worlds in ~61 min over 4 shards ≈ 9.7 worlds/s box-wide; Stage 3 expects ~700 jobs × 100 worlds = 70,000 worlds (job count is an extrapolation from Stage 2's 353 jobs / 200 games × 400 teacher games) | ≈ **2–3 h wall** |
| reruns, merges, reports | minutes each | — |
| **total** | | **≈ 18–20 h wall** |

Stage 3's own game walls will replace these prices in its report, as Stage 2's replaced Stage 1's.

## 6. Run order and launch conditions

1. `run_stage3_games.sh` — pins → PREGATE-GATE (Stage 2 manifest) → FREESPACE → G8 (hardened) → teacher phase → raw phase → RAW-RERUN (one re-run per raw timeout) → registry merge (tag `round9-stage3`) → games report (tuple audit must be OK) → `stage3_analyze.py` read against the §4.4 bands → games manifest.
2. `run_stage3_l3.sh` — jobs from the teacher blocks' snap indexes → labels at 1055001 + shard × 10⁸ → `stage3_attr_analyze.py` attribution read → L3 manifest. (Runs after the games: the Stage 3 read's Δ is an attribution input.)
3. Publication (at report time, mirroring Stages 1–2): the report with `data/stage3/` (driver rows for all blocks + reruns, stat logs, snap indexes, pairing.json, games report, stage3_read, label rows gz, jobs, attr read, manifests) so every read is recomputable from the repo alone.

**Launch conditions:** Claude's approval of this package at its committed sha; Joe's explicit go; launched sha == approved sha (rounds-only diff aside); the pre-gate coverage condition from the header (build and tuple unchanged since Stage 2's IDENTICAL — enforced mechanically by the PREGATE-GATE block at run time); /tmp free space passing the §3 pre-flight at launch time.

## 7. Runner blocks and fixtures — 87 checks, ALL PASS

Aggregator `fixtures/run_fx_s3.sh`; transcript `fixtures/fx_s3_outputs.txt` (regenerated from the passing run; the builder's audit re-run reproduced it line-for-line). The Stage 2 suite (`fixtures/run_fx_s2.sh`, 124 checks) also still passes, untouched.

| suite | checks | proves |
|---|---|---|
| fx_s3_blocks | 35 | block inventories for both runners (games: PREGATE-GATE, FREESPACE, TS-SRV, TS-SWEEP, TS-DRIVERS, RS-SRV, RS-SWEEP, RS-DRIVERS, RAW-RERUN; L3: FREESPACE, LS-SRV, LS-SWEEP, LS-SHARD); the three-name-form grep over both runners + `g8_sweep2.sh`; FREESPACE line-order (before the first tree copy) and its 6 size cases; every server block loads/aborts on stub servers; sweeper counts 4/4/4; driver blocks run all workers (4/4/8) and fail on a failing worker; RAW-RERUN spawns exactly 1 rerun on a planted raw timeout, 0 on none; PREGATE-GATE against the **real** Stage 2 manifest (pass; verdict/hash/tuple altered → abort; absent → abort) |
| fx_g8_sweep2 | 8 | §2's discriminating cases with the real `pgrep`: clean sweep removes only stale segments; bare-mention trips the old guard, not the new; `play_game.php`-token mention trips both (residual); genuine game/driver command lines trip the new; diff confinement (header + guard line only) |
| fx_stage3_games_report | 12 | planted 8-block population + rerun: pairing statuses incl. a rerun-sourced raw row and the dropped-pair variant; capped-game life tallies (ahead 1, tied 1, behind 0); the R14 canary record counted by name (`canary_refusal_rows` == 1) and excluded from teacher stat rows; tuple audit OK; a corrupted tuple row aborts (exit 2) |
| fx_stage3_analyze | 14 | round-trip on the games report's REAL output (Case A: hand-computed primary −0.5 with CI [−0.5, −0.5] → HARMS; lifediff −0.25; Δ0.5 −0.25; per-seat 0.0 / −1.0); Case B: 9 teacher-timeout pairs in 400 (rate 0.0225) → INCONCLUSIVE overriding a CI that excludes 0, impeachment text before the verdict at mean +0.9775; Case C: CONVERTS at mean +0.5, CI [0.43, 0.57]; Case D: a dropped raw pair listed, the primary unchanged |
| fx_s3_registry | 4 | the real `merge_registry.py`: merge incl. a rerun block's ids file, sha printed; re-merge is dup-same (count unchanged); a conflicting-tag id exits 1 |
| fx_s3_l3_roundtrip | 14 | the real `s2_label_main.php` at MEAS_SEED=1055001 under Stage 3's settings: genuine rows → `stage3_attr_analyze.py` accepts them (stamp audit 200 rows, 0 bad — the fixed form), hand-computed attribution (mean 0.2, per-game gain 0.2, ratio 0.2 / 0.05 = 4.0 exactly); pin aborts (bad k, missing setting) exit 2 |

Round-trip coverage, pair by pair (the ruling's new standing rule): Stage 2 pre-gate manifest → PREGATE-GATE (real file, fx_s3_blocks); games-runner rows → games report → analyzer (fx_stage3_analyze Case A consumes the report builder's real output files); jobs builder → label driver → attribution analyzer (fx_s3_l3_roundtrip, genuine driver rows); registry merge → report counts (fx_s3_registry + the report's attempted-pairs assert).

## 8. Hashes (machine-copied at build time)

New code:

| file | sha256 |
|---|---|
| code/settings_stage3.json | `b241515588b8152145bed2708432aa377ce4f054131fff150076e8998b5be912` |
| code/g8_sweep2.sh | `72b18b3402ca5132bcdd4d1c6ea1f9f6c8cc3fc9e3fea76472dc0a09e5293a86` |
| code/run_stage3_games.sh | `2fbcceed30b040e1401cdf3ca4663aac878ff6aba4fe4c1fe97e5eb3308230bd` |
| code/stage3_games_report.py | `4f19306d6ca1000756bccc05867ab6558dd47c3055870a56ff9de5052940fe25` |
| code/stage3_analyze.py | `e283a23711221c959aba138a8d9104893cebbcc78bb774b24b6d92bc908ff76e` |
| code/run_stage3_l3.sh | `36ae6f6398da11e03f97a64a71782277063711e75889a7c3d0e3f6e90a83f871` |
| code/build_s3_jobs.py | `fabecae5087d48c1eb2127e11ee750939d364c22b14e2d6b5d534a863fb2d498` |
| code/stage3_attr_analyze.py | `bc92a2c87c3c0dbf3264c2a949d87bde20ed9d5816ce2f88c6603f0e1cd05453` |

Fixtures: `fixtures/fx_s3_blocks.sh` `3ba32f12…`, `fixtures/fx_g8_sweep2.sh` `2a914b50…`, `fixtures/fx_stage3_games_report.py` `272801b4…`, `fixtures/fx_stage3_analyze.py` `03bf9032…`, `fixtures/fx_s3_registry.py` `89dbb771…`, `fixtures/fx_s3_l3_roundtrip/` (runner `5145d9c0…`, checker `3b0116f6…`, stub `1dab2284…`, jobs `ea5d8e7d…`/`20c2dff7…`/`010d7ee4…`), `fixtures/run_fx_s3.sh` `2cefb959…`, transcript `fixtures/fx_s3_outputs.txt` `e4480fb4…`.

Reused byte-identical and pinned in the runners: `search_s2.php` `85490e8e…`, `s2_label_main.php` `c7a76af4…`, `paired_driver_gravy.py` `3389b1b9…`, `stage0_report.py` `5c7e5393…`, `analyze_l3.py` `16017ffa…`, `merge_registry.py` `13a655e3…`, `shm_sweep.py` `98027a8b…`, `settings_stage2.json` `2a1634cc…` (Stage 2's file, referenced for nothing at run time — the tuples live in `settings_stage3.json`; it is listed here because the Stage 3 settings were verified against it). Every pre-existing Stage 2 file re-verified at its pre-build hash after this build: no existing file was modified.

## 9. Flags for the reviewer (judgment calls, named rather than buried)

- **F-S3-1 — the raw arm's price is an estimate.** Round 7's fleet record does not time the raw arm separately (its 1,262.9 s/game mean is the *teacher's*); the ~1 h raw figure rests on the gate record's raw compute pace (~3.8 s/game) and the heuristic opponent bounding the game's length. Marked as an estimate in §5; Stage 3's report replaces it with the measured figure.
- **F-S3-2 — fixture Case B's planted values differ from a naive reading of the registration example.** A population of 400 pairs cannot simultaneously have 9 teacher-timeout pairs and a mean of exactly +1.0 (a timeout pair scores the teacher 0; against a raw loss its diff is 0, not +1). The fixture plants the registered *rate* (9/400 = 0.0225 → INCONCLUSIVE) with the arithmetically consistent values (mean 391/400 = 0.9775, LOGO range [389/398, 390/398], drop-timeout sensitivity 1.0) and asserts INCONCLUSIVE overriding a CI of [0.9625, 0.99] — the registered behavior the case exists to prove.
- **F-S3-3 — the tracker question is Joe's, not this package's.** Stage 2's tracker (phase rule as amended: "complete" only on the final read file) exists as an artifact + poller pattern. Whether Stage 3 gets a tracker — and whether its end state keys on `stage3_read.json` + the L3 manifest the same way — is a decision for Joe at launch time. Nothing is built here.
- **F-S3-4 — RAW-RERUN appends.** Two raw timeouts in the same block are re-run concurrently (the driver-block pattern), appending to one rerun file from two driver processes — the paired driver's established append-per-process pattern throughout the fleet; rows are whole-line appends and the pairing builder keys on (seed, seat), so interleave order is immaterial.
- **F-S3-5 — `--expect-pairs` seam.** `stage3_analyze.py` defaults its attempted-pairs assert to `settings_stage3.json`'s 400 (the production path; the runner passes nothing) and accepts an override so fixtures can round-trip small planted populations through the real report — the Stage 2 `--expect-rows` pattern, same justification.

**This package approves nothing and launches nothing.** It is staged for Claude's code review; Stage 3 launches only on his approval of the committed package, Joe's go, and launched sha == approved sha, under the §6 conditions.
