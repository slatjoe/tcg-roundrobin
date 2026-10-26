# Round 9 — Stage 0 launch package (L3 on the fleet's 118 overturns + the D7 horizon co-report)

**Status: built, not run.** This package is what comes back first
under §6 of `claude-reply-8dddf38.md`: the label runner, the L3
scorer, the (D) reporting, the D7 co-report construction, and
fixtures, staged for the reviewer's code review. Stage 0 launches
only on that review plus Joe's go. Joe adopted D7 on 2026-10-25
20:04 EDT ("Adopt D7 — the horizon goes into the grid"); this
package builds the co-report §3 of the reply requires once D7 is
adopted.

Parent records: `gravy-calibrated-search-design.md` (committed at
`8dddf387`), `claude-reply-8dddf38.md` (committed at `c76f6856`).

---

## 1. What Stage 0 is, in this package

The design's Stage 0 (§3): L3 on the round-7 fleet's 118 overturn
decisions — the gated teacher's contested Gravy decisions, labeled
offline at LABEL_W=50 with CRN pairing against the production
server, read by the L3 scorer with DELTA = +0.0075 (the fleet
result) and TEACHER_GAMES = 400, so the per-game gain is computed
against 0.295 overturns per teacher game (118/400). The reply's
§1 adds the (D) reporting and the instrument-limited condition;
§3 (with D7 adopted) adds the horizon-aligned co-report over the
same 118 jobs. Stage 0 plays no games and touches no registry
entry; the jobs file is vaulted and read-only to this package.

## 2. Inputs and pins

| input | value |
|---|---|
| jobs file | `/home/joe/tcg/registry-vault/jobs_all_gravy_fleet_l3.jsonl` — 118 jobs, 88 games; sha256 `5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b` (re-verified on the box at build time) |
| label tree source | `/tmp/gravytree` (the fleet tree): search.php `8f6b35da…`, featurize.php `f81193e0…`, play_game.php `4ac2d62d…`, ParseGamestate.php `0e88dd58…`, meas_label_main.php `3109176b…`, deck `nats2026_eriksen_gravy_60.txt` `b8b41390…` |
| snapshots | all 118 `snap_dir`s resolve under `/tmp/ggate` (asserted at build time; the runner re-asserts per job before labeling) |
| continuation server | production `rl/search_server.py` `81ef2cdb…`, serving Gravy ckpt_v10 `44f1e5d7…`, one server per seat |

`/tmp/gravytree` and `/tmp/ggate` are box-`/tmp` artifacts: they
are present and pinned today; if either is gone at launch, the
runner's pre-flight aborts on the pin/presence checks and names
what is missing. Nothing in this package rebuilds them.

## 3. The code (all in `rounds/round9/code/`)

| file | sha256 | what it is |
|---|---|---|
| `meas_label_main.php` | `3109176bb7137bc89b0645b8185f83c5722268c03028ca692642699cf7730b33` | the registered labeler, byte copy — the primary pass's driver |
| `analyze_l3.py` | `16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9` | the stock L3 scorer, byte copy (rounds 3/4 lineage) |
| `analyze_l3_deploy.py` | `3919bbb80db29eec91c87e6f640e6eb689fa8324865fb450a69292843008dd72` | the O3 deployment copy: exactly one substitution, DELTA 0.2525 → 0.0075 (`fixtures/analyze_l3_deploy_diff.txt`); it is byte-identical to the deployment copy the fleet itself produced (`/tmp/ggate/analyze_l3_deploy.py`) |
| `stage0_report.py` | `5019d94ee21c0d4b71e454b101bf2d0eff23d4749e2dd2033557fd4bd7a6ecef` | the (D) reporting (§5 below) |
| `search_horizon.php` | `6d63f5c37be840324bc847a454157a2688677354e952886980e4601f023d04a7` | the horizon tree's search.php: the fleet build plus the four-hunk D7 block, label functions only (`fixtures/search_horizon_diff.txt`) |
| `r9_label_main.php` | `2463fc29c5333839971a0b22244b3b642d9ff68994f8942214d15b8eb6ca76a1` | the horizon pass's driver: `meas_label_main.php` plus only the horizon pin (`fixtures/r9_label_main_diff.txt`) |
| `run_stage0_l3.sh` | `e3e20415388986a8081d2846c07dbe0c2d96b679a320dd7c73ad84a40f4dc22d` | the runner (§6) |
| `shm_sweep.py` / `g8_sweep.sh` | `98027a8b…` / `82b4d58c…` | the standing (C)/(G8) containment pair, byte copies from round 8 |

Every pin literal in the runner was machine-copied from
`sha256sum` output and is format-asserted before comparison:
`expect_hash` aborts unless the pin matches `^[0-9a-f]{64}$` —
the round-8 W-check guard, whose absence cost a launch there.
An independent audit at build time confirmed all 14 distinct pin
literals in the runner equal the sha256 of the file each names.

## 4. The D7 co-report — route taken and why

**The primary pass's records cannot support an exact offline
co-report, so the horizon is implemented in the rollout child and
the co-report is a second labeling pass.** The determination is
mechanical, from the label child's result records in the fleet
build (`SimLabel_RunRollout`, gravytree `search.php`):

- A normal (non-error) world record carries `turns` — the absolute
  `currentTurn` at loop exit — so for worlds that ended on the
  stuck guard, the offline transform would be exact.
- But worlds that die on the 4,000-hook budget end as error rows
  (`{"error":"abort"}` and kin) **carrying no turn at all**. Such a
  world may or may not have crossed turn 62 before the budget ran
  out; the primary record cannot say. The same holds for the
  300-second parent deadline's `{"error":"timeout"}` rows. Round
  7's fleet worlds stalled exactly on these guards (31.7%
  thin-prior), so the unrecoverable class is the population the
  co-report exists for, not an edge case.

The in-child implementation, per the §4(C) pinned-parameter
pattern:

- `LABEL_HORIZON` is read from the environment by the horizon
  pass's driver: `off` (pin 0) or a non-negative integer; anything
  else aborts before labeling. Every job in the pass must carry
  `"horizon"` equal to the pin — a missing or unequal value aborts
  (exit 2) naming the snap and both values — and every emitted row
  is stamped `"horizon": <pin>`.
- In the child, the horizon is forwarded through the existing cfg
  (`SimLabel_RunForSnapshot` → child), read once in
  `SimLabel_RunRollout`, and checked in the drive loop after the
  stuck check: a world still running at absolute `currentTurn >=
  62` breaks the loop, and the result is written with
  `finished = 1` and `outcome = 0.0` (winner 0 — the score the
  game instrument itself assigns a draw), marked `"horizon": 1`.
  Precedence: a game that has actually ended keeps its own
  outcome; the horizon applies only to a world still running when
  it reaches the trigger. Candidate rule, validity floor, margin,
  the 4,000-hook budget, and the pair are untouched; the patch's
  four hunks sit inside `SimLabel_*` only — the teacher's Decide
  path is byte-identical.
- The primary pass does not use any of this: pristine tree,
  pristine driver, the registered instrument byte for byte. The
  horizon build exists only in the co-report pass's trees.

**Seed bases.** Primary: **855001 + shard × 10⁸** (the design's
registered family). Horizon pass: **875001 + shard × 10⁸** — the
sibling family at +20,000 on the same shard spacing, fresh worlds
in the same bookkeeping discipline: within either pass, a
(job, world) seed is unique by the labeler's own formulas
(seedBase + ji×100003, then +world×31337 in the child). The
co-report's reads come from the horizon-ON labels with the same
deployment scorer and the same (D) report — under the horizon,
"finished" includes the horizon draws.

**OFF-equivalence evidence (FX7, box build test):** three real
vaulted jobs (B `359158031_t2`, P `190554034_t1`, ARS
`308484385_t1`; 300 worlds per run) labeled three ways — pristine
construction, horizon construction with the pin off, and with the
pin at 62. The OFF construction reproduces the primary exactly:
winner, outcome, finished, turns, hooks, fallbacks and child_state
match on all 300 worlds; the only difference anywhere is the
horizon build's own result marker (`"horizon": 0` on non-error
results, a key the pristine build does not emit), and the 28 error
tuples are identical, as a set and row for row. With the pin at
62, the run finishes 300/300 (OFF: 272 finished, 28 error): the
28 `"horizon": 1` worlds are exactly the 28 tuples that error
under OFF — every one had crossed turn 62 before dying on the
hook budget (exit turns 62–227) — each written finished with
outcome 0.0, and the other 272 worlds match the primary on all
scoring fields. The pin-mismatch negative aborted before labeling
(exit 2). Full record in `fixtures/README.md` (FX7).

## 5. The (D) reporting (`stage0_report.py`)

Computed from the same jobs + label rows as the scorer, beside
the primary read:

- The primary read itself is computed by importing the deployment
  scorer's `aggregate`/`summarize`, and cross-checked against the
  scorer's standalone output (jobs scored, mean diff, CI,
  per-game gain — agreement to 1e-9, asserted; the bootstrap is
  seeded, so the two must agree exactly). Any disagreement aborts.
- **Unfinished share per candidate and pooled:** unfinished /
  (finished + unfinished) over each candidate role's rows
  (teacher pick, prior pick, pooled). Error rows are counted
  separately and never enter a share — they carry no outcome.
- **Paired-n distribution:** per scored job, the number of worlds
  both candidates finished (the primary's n): min / p25 / median /
  mean / p75 / max, bucket counts (50, 40–49, 20–39, 1–19), and
  the missing-job count.
- **Sensitivity read:** worlds where both candidates have a
  non-error row, scored with unfinished = draw (0.5 — the
  instrument's own price for a game that does not end); per-job
  mean diffs, mean over jobs, the scorer's game-clustered
  bootstrap CI, per-game gain at TEACHER_GAMES = 400. Printed
  beside the primary.
- **The registered condition, printed with its inputs:** pooled
  unfinished share > 20% with a null or negative primary read →
  **INSTRUMENT-LIMITED** (cannot trigger CLOSE at Stage 0; the
  round proceeds to Stage 1); a positive read (mean > 0, CI lower
  > 0) stands either way.

Definitions worth the reviewer's eye: the sensitivity pairing
excludes a world when either candidate's row is an error —
timeouts and aborts have no outcome to price, draw or otherwise;
they are counted in the integrity tallies and in neither read.
The primary finished-only read is the scorer's own, unchanged.

## 6. Run plan

Deployment: the package's `code/` is copied to
`/home/joe/tcg/round9_code` on the box (`CODE_DIR` overridable);
the runner is launched detached from there, output in
`STAGE0_OUT` (default `/tmp/r9s0_out`).

1. Pre-flight: `expect_hash` on the vaulted jobs file, the
   production server, ckpt_v10, every deployed code file, and
   the fleet-tree pins.
2. Shard copies built from the vaulted file (the original is
   never modified): shard = sha256(game) mod 4; `snap_dir`
   rewritten to the absolute `/tmp/ggate/<rel>` on the copies
   only, each asserted to exist; horizon copies additionally
   stamped `"horizon": 62`. Counts asserted: 118 total.
3. G8 sweep; then the two production servers (one per seat),
   load-verified against ckpt_v10 from their logs.
4. Primary pass: per shard, a pristine tree copy + a (C)
   kernel-attribution sweeper; jobs split by root player, each
   group labeled against its seat's server, LABEL_W=50, seed
   base 855001 + shard×10⁸. Shards run in parallel.
5. Horizon pass: same shape with horizon trees, the r9 driver,
   LABEL_HORIZON=62, seed base 875001 + shard×10⁸.
6. Scoring: the deployment scorer standalone on each pass, then
   `stage0_report.py` (which re-derives the primary from the
   scorer's own code and asserts the cross-check).
7. `stage0_manifest.json`: output hashes, label-row counts, both
   reports.

**Cost** (design §3, for the primary): 0.15–1.5 box-hours — the
fleet's own L3 estimate for these 118 jobs at W=50, most worlds
fast, the stall tail bounded by the 300 s candidate deadline.
The horizon pass adds the same 118 jobs again at the same width;
its worlds truncate at the turn-62 trigger where the primary's
stalled, so its cost should land at or below the primary's —
stated as an expectation from the mechanism, not a measurement:
total Stage 0 budget ≈ 0.3–3 box-hours.

## 7. Fixtures

`fixtures/run_fixtures.py` (local, synthetic, hand-computed —
the arithmetic is in `fixtures/README.md`): the primary read
(FX1), unfinished-share accounting and the draw-sensitivity read
(FX2), the instrument-limited line from both sides (FX3/FX3b),
the positive-read-stands case (FX4), the pin-format guard
negatives (FX5), and the scorer self-test + O3 substitution
(FX6). **24 checks, ALL PASS** (verbatim output in the fixtures
README). FX7 is the box build test of §4: three real vaulted jobs
through the pristine and horizon constructions — OFF-equivalence,
ON mechanics, and the pin-mismatch abort. Verdict: OFF reproduces
the primary field-for-field (sole difference: the build's own
`"horizon": 0` marker key); ON finishes all 300 worlds, the 28
horizon draws being exactly the 28 worlds that error under OFF;
the pin-mismatch abort fires as specified. Full record in
`fixtures/README.md` (FX7).

## 8. Clause list — claude-reply-8dddf38, as it applies to Stage 0

§1 (instrument validity):
1. *Unfinished-world share reported per candidate and pooled* —
   **DONE** (§5; fixture FX2).
2. *Paired-n distribution reported* — **DONE** (§5; FX1/FX2).
3. *Sensitivity read with unfinished worlds scored as draws,
   printed beside the primary* — **DONE** (§5; FX2).
4. *The >20% instrument-limited condition printed and applied;
   a positive read stands* — **DONE** (§5; FX3/FX3b/FX4).

§3 (D7):
5. *Horizon-aligned L3 as a co-report in Stage 0* — **DONE**
   (§4: in-child horizon, second pass, same scorer/report).
   The exact-offline alternative was determined impossible on
   the primary records (error rows carry no turn) — §4 states
   the determination and its evidence.
6. *The horizon is the instrument's own draw trigger (absolute
   currentTurn ≥ 62, outcome 0, finished 1); candidate rule,
   floor, margin, continuation unchanged* — **DONE** (§4; the
   patch diff is four hunks inside `SimLabel_*`).

§4(C) (faithful offline settings), as it applies to this stage:
7. *Run-pinned parameters: env-read, recorded on rows, abort on
   job/pin mismatch* — **DONE** for the one parameter Stage 0
   adds (the horizon; §4, FX7's negative test). Stage 0 has no
   Stage-1 setting to run: its instrument is the registered one
   (300 s label deadline, 4,000 hooks) and stays byte-pristine.
8. *Exact per-setting deadline/hook parameterization of the
   evaluator* — **NOT DONE here, by scope**: that machinery
   belongs to the Stage 1 calibration package (the grid's
   settings do not exist in Stage 0). It is not waived — it is
   owed with the Stage 1 launch package, before any grid cell
   runs.
9. *Ghost pre-gate re-proving a new build action-identical before
   live teacher games* — **NOT DONE here, by the reply's own
   staging**: §4(C) requires it "before the calibrated teacher
   plays a live game in Stage 2." Stage 0 fields no live teacher
   and plays no games; the label-side analogue owed here — the
   horizon build's OFF-equivalence — is FX7 (§4).

§6 (what comes back first) + standing conditions:
10. *Stage 0 label runner + scorer as deployment copies,
    hash-pinned, substitutions shown as diffs* — **DONE** (§3;
    `fixtures/analyze_l3_deploy_diff.txt`,
    `fixtures/search_horizon_diff.txt`,
    `fixtures/r9_label_main_diff.txt`).
11. *DELTA = +0.0075 substitution, TEACHER_GAMES = 400* —
    **DONE** (fixture FX6 asserts both from the file).
12. *Fixtures with known answers for the new reporting* —
    **DONE** (§7).
13. *Containment standing (G8 + (C) sweepers), registry
    untouched, no games played* — **DONE** in the runner (§6);
    the vaulted jobs file is read-only to it (copies only).
14. *No launch without the reviewer's code review of this
    package and Joe's go* — **DONE** as the package's status:
    the runner's header carries the gate, and nothing in this
    package has been run as a measurement. (The FX7 build test
    labeled 3 jobs to prove the construction — build
    verification under the measurement-gate skill, reported as
    such, not a Stage 0 read.)

## 9. What the reviewer is asked to rule

- The §4 determination (error rows carry no turn ⇒ no exact
  offline co-report) and the in-child route it forces.
- The horizon precedence rule (a game that ended on its own
  keeps its outcome; the horizon prices only worlds still
  running at the trigger).
- The sensitivity pairing's exclusion of error worlds.
- The horizon seed family (875001 + shard×10⁸).
- Clauses 8–9 scoped to the Stage 1 / Stage 2 packages.
