# Round 9 — Stage 1 launch package (calibration: capture, panel, bounds grid, selection)

**Status: built, not run.** This package discharges clause 8 of
the Stage 0 package (§4(C) faithful evaluation, deferred there
by scope) and builds Stage 1 exactly as settled by
`claude-reply-16f02e2.md` §4. Stage 1 launches only on Claude's
code review of this package at its committed sha plus Joe's
explicit go for Stage 1.

Parent records: `gravy-calibrated-search-design.md` (committed
at `8dddf387`), `claude-reply-8dddf38.md` (design approval,
`c76f6856`), `stage0-report.md` + `claude-reply-16f02e2.md`
(Stage 0 POSITIVE at `16f02e2e`; the ruling at `8dce0fac`).

**Two places where the ruling supersedes the design text, and
this package follows the ruling:** (i) the selection rule —
the design's §4.4 proposal (pooled thin-prior ≤ 5%) is
replaced by the ruling's §4.3: **all-candidate completion
≥ 95%** (every candidate reaching the ≥20-finished-world
validity floor, as a fraction of all candidate evaluations),
cheapest by mean per-decision wall, ties by p95 then max;
(ii) the grid — the design's horizon-less factorial is
replaced by the ruling's §4.2: **B0** (old bounds, no
horizon, control), **B0+H**, and **{8,000 / 16,000} ×
{180 / 360 s} + H**, with the horizon at outcome −1.

---

## 1. What Stage 1 is, in this package

Stage 1 measures **completion and cost** — which resource
bounds make the search actually complete on Gravy states,
and what each setting costs per decision. It measures no
edge and licenses no edge claim (design §4 opening; ruling
§4). Form: 40 fresh raw-v10 capture games vs the heuristic
(seeds 21001–21040) → a panel of the first 240 contested
snapshots (≤ 8 per game) → every panel state evaluated
offline under all six registered settings at the fleet's
4-way contention, B0 first → the analyzer's reads and the
registered selection. The capture games join the
do-not-train registry before the panel is built.

## 2. Definitions that decide readings (for the reviewer's eye)

- **Completion (the selection metric)** is a property of a
  *(state, candidate)* evaluation: it completes iff ≥ 20 of
  its 25 worlds finished. A setting's completion is the
  fraction of ALL its candidate evaluations that complete —
  **not** the pooled finished-world share. The two part
  company exactly when a few candidates stall just under the
  floor in many states; fixture FX-ANALYZE scenario A plants
  that case (pooled 0.97, all-candidate 0.875) and the
  analyzer uses the all-candidate figure. The pooled share
  is printed as a diagnostic only.
- **Thin-prior** is the co-report from the design: the
  fraction of panel states whose *prior* candidate does not
  complete, printed beside the fleet's 31.7% (different
  population — raw-trajectory roots vs the fleet teacher's
  own trajectory — a comparability check, not an identity).
  The selection never depends on it.
- **Horizon value — where it is applied.** The ruling (§3)
  registers the horizon value as a property of the search:
  a rollout still running at the turn-62 trigger, and any
  natural drawn rollout, scores −1 for the root player.
  In Stage 1's form the evaluator never makes a live pick —
  every selected candidate receives its 25 worlds regardless
  of means — so the valuation cannot change any world,
  finished count, or wall time; it can only change how
  finished worlds are *priced in a read*. This package
  therefore applies it exactly where Stage 1 has reads: the
  analyzer computes the overturn co-reports from the raw
  rows under **both** valuations, with **draw = 0 (−1) the
  primary** per the ruling and 0.5 co-reported — for **every**
  setting, B0 included. `horizon_value` is nonetheless a
  full run pin (env + job tuple + row stamps, §5), so the
  registered parameter is carried and audited end-to-end.
  Where the −1 price changes behavior is the *live* Decide
  path — Stage 2's teacher build, behind the ghost pre-gate
  (ruling §4.6); that is a Stage-2 package item, flagged
  here so it is not lost.
- **B0's native valuation is 0** (draws priced 0.5): B0 is
  the fleet teacher as it ran — the control. Its tuple says
  so, and per the point above, none of B0's *reported*
  reads depend on the native value, since both valuations
  are computed for it anyway.
- **The margin never moves:** the overturn co-reports use
  the registered rule (candidate means over finished
  worlds; best by strict improvement in ascending order;
  paired test over shared finished worlds, ≥ 20 shared,
  mean > 1.5 × paired SE) — replicated from the build's
  `SimTeacher_DecideInner` and pinned by fixture.

## 3. Inputs and pins

| input | value |
|---|---|
| settings registry | `code/settings_stage1.json` — the single source: the runner stamps its tuples into job copies and env pins; the analyzer audits every row against it |
| capture/eval tree source | `/tmp/gravytree` (the fleet tree): search.php `8f6b35da…`, featurize.php `f81193e0…`, play_game.php `4ac2d62d…`, ParseGamestate.php `0e88dd58…`, deck `nats2026_eriksen_gravy_60.txt` `b8b41390…` |
| continuation server | production `rl/search_server.py` `81ef2cdb…`, serving Gravy ckpt_v10 `44f1e5d7…`, one server per seat (the label path's rule) |
| registry | `/home/joe/tcg/registry-vault/do_not_train_registry.json` — 6,241 games, sha256 `28b5acfa…` at package time; the runner records pre/post sha256 + n_games in the manifest and aborts on an unreadable or regressed (< 6,241) registry |
| snapshots | created by this run's own capture under `$OUT` (durable disk) — Stage 1 has **no** `/tmp/ggate` dependency; the panel asserts every snap dir exists before any evaluation |
| seed blocks | capture games **21001–21040** (seat 1: 21001–21020; seat 2: 21021–21040); extension blocks of 10 from 21041 (5 per seat) if the panel falls short; eval worlds **885001 + shard × 10⁸** (settings constants; the driver strides jobs by 100003 within a shard file). Clear of every spent family: fleets 1001–1200 / 2001–2200 / 8001–8200, corpus 10001–10400, label bases 555001 / 777001 (round 8), 855001 / 875001 (Stage 0); the 9001–9200 reservation stays untouched |

`/tmp/gravytree` is a box-`/tmp` artifact: present and pinned
today; if it is gone at launch, the runner's pre-flight aborts
on the pin checks and names what is missing. Nothing in this
package rebuilds it.

## 4. The code (all in `rounds/round9/code/`)

| file | sha256 | what it is |
|---|---|---|
| `settings_stage1.json` | `de7e09d36f4c0f6c51baff80c9b984f58c480fb079f667a2d2836b0067514459` | the registered settings: six tuples (B0 4000/180/off/0; B0+H 4000/180/62/−1; H8k-180+H; H8k-360+H; H16k-180+H; H16k-360+H 16000/360/62/−1), k=25, margin 1.5, floor 20, bar 0.95, eval seed base 885001, fleet thin reference 0.317 |
| `search_s1.php` | `1fcacaa3eb35d06e33a13b4f53a7b901279cf48eb34bdea14539c86e770ecd52` | the eval tree's search.php: byte-derived from `search_horizon.php` (`6d63f5c3…`) with ONLY the clause-8 label-path parameterization (§5); the diff is `fixtures/search_s1_diff.txt` (`4dff586e…`), **recomputed byte-identical at build time** |
| `s1_eval_main.php` | `73ed24822baaaa9cc8ceebe4f9e082320932cc6e64b5e5f8e3f74b81764cae5a` | the evaluator driver: `r9_label_main.php`'s pin pattern generalized to the full setting tuple; per-job wall + per-candidate finished/error tallies to the stats file |
| `paired_driver_gravy.py` | `3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359` | the capture driver (gate-driver lineage): arms incl. `capture`, per-arm assertions, timeout SHM cleanup, registry id harvest (G9). **Builder's fix at build time:** the inherited default deck was the *Fai* deck — now the Gravy deck, with a fail-loud abort on any non-Gravy deck (§8) |
| `build_panel.py` | `8f22d84546e0f0775b5c538c1e356fda622632a30731be4e335eaa30807db576` | the panel builder: first 240 contested snapshots in capture order, ≤ 8/game; a non-capture row or a duplicate snap aborts (exit 2); a shortfall writes what it found, marks the report incomplete, exits 3 |
| `stage1_analyze.py` | `1ee8511edcfb5108c43753f237556b36725ee76fe9ca01042a1ba387e7b7dada` | the analyzer: clause-8 tuple audit (second placement), world-count guard (exactly k rows per candidate), stat/world cross-checks, draw-marker agreement check, completion + thin-prior + wall distribution, overturn co-reports under both valuations, the registered selection |
| `merge_registry.py` | `13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe` | the registry merge (round-7 pattern): retag conflicts abort, atomic write + timestamped backup + vault copy, prints the merged sha256 |
| `run_stage1.sh` | `7e166c42885b35ef287fa7e3beba1bfafd7708222383ce2517ef33c5d725c419` | the runner (§6). Every pin literal in it was machine-copied from `sha256sum` output and is format-asserted (`^[0-9a-f]{64}$`) by `expect_hash` before comparison — verified at build time: all 17 literals are 64-hex and match the files above |
| `shm_sweep.py` / `g8_sweep.sh` | `98027a8b…` / (as Stage 0) | the standing (C)/(G8) containment pair, byte copies |

Syntax verification at build time: all PHP lints clean
(PHP 8.3.6, user-space; the box runs 8.5.4 — the Stage 0
builds linted the same way and ran), all Python compiles,
the settings JSON parses, `bash -n` clean on the runner.

## 5. Clause 8 discharged — the parameterization

The Stage 0 package left §4(C) as clause 8, *not done by
scope*: hooks/deadline/horizon become env-read run-pinned
parameters, recorded on every stat row. Here:

- **The build** (`search_s1.php`, diff-verified): the label
  path's two rollout hook guards read `$ssLabelHookBudget`
  (cfg `hookBudget`, default 4000) and the label parent's
  per-candidate deadline reads cfg `deadlineS` (default
  300) — **the defaults are the registered label
  instrument**, so an unparameterized call behaves exactly
  as the Stage 0 labeler did. The horizon block is the D7
  block, unchanged. The Decide path and every non-label
  function are byte-identical to the horizon build.
- **The driver** (`s1_eval_main.php`): the run's tuple is
  pinned by env — `EVAL_SETTING_NAME`, `EVAL_HOOKS`,
  `EVAL_DEADLINE_S`, `LABEL_HORIZON` (the r9 semantics:
  "off" or a turn), `EVAL_HORIZON_VALUE`, `EVAL_K`. Every
  job must carry a `setting` object equal to the pins field
  by field; a missing field, a mismatch, or a malformed pin
  aborts (exit 2) **before any evaluation**. The tuple is
  forwarded through cfg into the build (fixture-proven) and
  stamped onto every world row and stat row.
- **The analyzer** re-audits every stamp against
  `settings_stage1.json` before any read (the second
  placement of the rule), plus the world-count and
  cross-checks of §4. Mismatch anywhere = abort, no read.

## 6. Run plan

`run_stage1.sh`, phases via env (`PHASE=capture|panel|eval|
analyze|all`; `BLOCK` for capture extensions; `SETTINGS=`
to run one setting's eval). Order inside `all`:

1. **Pre-flight:** pin checks (§3/§4) + registry sanity;
   `deployed_code_hashes.txt` written.
2. **Capture block 1:** G8 sweep; production servers up
   (one per seat, model asserted from their own logs); the
   two seat streams play in per-stream fleet-tree copies
   under per-tree (C) sweepers. The driver's arm assertions
   are checked from its manifest — **assert_ok or the run
   aborts** (the stat-side assertions are what convicted the
   round-8 capture misbuild). Stream specs append to
   `streams.txt` in run order.
3. **Registry merge** (tag `r9s1_capture`), before the
   panel exists.
4. **Panel:** if short of 240, exit 3 with the registered
   instruction (another `BLOCK`, then `PHASE=panel`). Snap
   dirs asserted present.
5. **Eval, B0 first:** per setting — job copies stamped
   from the settings file; 4 shard trees (game-hash
   sharding) with `search_s1.php` in place (hash-asserted
   per tree); per-shard player split against that seat's
   server; the setting's own deadline enforced by the build
   itself. After each setting, its row counts print
   (status only). The remaining settings price off B0's
   measured walls before they are committed — the
   sequencing the design registered (§4.2) — because the
   runner runs settings strictly in file order and B0's
   report is readable after its pass.
6. **Analyze + manifest:** the analyzer's report
   (`stage1_report.txt/.json`) and `stage1_manifest.json`
   (hashes of panel/evals/stats/reports/job copies, the
   registry's post-merge identity, the selection).

Interim notices during the run carry status and artifact
paths only, never figures (standing rule).

## 7. Fixtures

Four suites, **46 checks, ALL PASS** locally (verbatim
transcript: `fixtures/fx_stage1_outputs.txt`; entries in
`fixtures/README.md`):

- **`fx_s1_eval/`** (21 checks) — the REAL
  `s1_eval_main.php` against a stub `play_game.php`:
  stamping, stats accounting (a drawn world counts
  finished), the cfg-forwarding proof, and four abort
  cases (job/pin mismatch, missing job setting, malformed
  horizon-value pin, malformed hooks pin), each exiting 2
  with **no rows written**.
- **`fx_stage1_analyze.py`** (14 checks) — the completion
  metric trap (pooled 0.97 vs all-candidate 0.875), the
  horizon-value flip (overturn at 0.5, none at draw = 0,
  planted means exact), the p95 tie-break, the max
  tie-break, NO CALIBRATED SETTING, and the tuple-audit
  abort.
- **`fx_build_panel.py`** (5 checks) — order + cap, the
  shortfall exit 3, both abort modes.
- **`fx_merge_registry.py`** (6 checks) — clean merge,
  idempotent re-merge, retag-conflict abort with the
  registry byte-identical afterwards.

Plus **`fixtures/search_s1_diff.txt`** (sha256
`4dff586e15d5177d251b24fa93000e9b3a01ca99a34fdb49d716dd29a98c71cf`):
the evaluator build's delta against the horizon build,
recomputed byte-identical at build time — the diff is the
proof, as with the Stage 0 build diffs.

**Not run anywhere:** the FX7-form box build test (real
jobs through the new build on the box). Stage 0's package
ran one because its horizon block was new machinery; here
the only new machinery is the label-path parameterization,
whose defaults reproduce the Stage 0 labeler — and the
fixture above exercises the parameterized driver
end-to-end. If the reviewer wants a box smoke (a handful of
panel states through B0 and B0+H) before the full run, it
slots in as a pre-launch step under the same pins; the
package does not presume it.

## 8. Builder's fixes and disclosures at build time

1. **`paired_driver_gravy.py` default deck** was the
   Ashlyn **Fai** deck (inherited from the gate driver it
   was copied from): a capture run without `--deck` would
   have played Fai games and harvested a Fai panel under a
   Gravy registration. Fixed: the default is the Gravy
   deck, and the driver now aborts on any deck whose name
   does not contain "gravy" — this copy's only registered
   use is the Gravy mirror. (The runner passes `--deck`
   explicitly regardless.)
2. **`build_panel.py`'s stream-prefix wording** said the
   prefix is "the runner's capture logdir"; the snapshots
   and index actually live in the stream's
   `TEACHER_SNAP_DIR` (the logdir's `snaps/` dir). Wording
   corrected; the runner passes the snaps dir.
3. **The analyzer's `decide()` replication** was verified
   line-by-line against the build's
   `SimTeacher_DecideInner` (means over each candidate's
   own finished worlds; thin iff the prior's finished
   count < floor; strict-improvement best in ascending
   order; paired test over shared worlds with the
   sample-variance SE, ≥ floor shared, margin 1.5) — and
   is pinned executably by FX-ANALYZE's planted cases.
4. **No `run_stage1.sh` existed** in the staged code
   although the settings file and the panel builder both
   referenced it; it is written here (§6), modeled on
   `run_stage0_l3.sh`.

## 9. Clause list — claude-reply-16f02e2 §4 (+ §3), as it applies to Stage 1

- §4.1 **Capture** (40 games, 21001–21040, blocks of 10;
  panel 240, ≤ 8/game): **DONE** — driver + panel builder +
  runner phases; fixture-proven.
- §4.2 **The grid** (B0, B0+H, {8k/16k}×{180/360}+H;
  horizon −1; k=25; margin fixed): **DONE** —
  `settings_stage1.json` is the single source for the
  runner, the driver pins, and the analyzer's audit.
- §4.3 **Selection** (cheapest by mean wall, ties p95 then
  max; all-candidate completion ≥ 95%; thin-prior
  co-reported vs 31.7%; NO CALIBRATED SETTING stops the
  round): **DONE** — analyzer + fixtures for the metric,
  both tie-breaks, and the no-qualifier verdict.
- §4.4 **Faithful settings / clause 8** (env-read,
  run-pinned, recorded on every row, abort on mismatch;
  each setting's own deadline at 4-way fleet contention;
  B0 first): **DONE** — §5 of this package; the contention
  is the runner's 4 shard trees; B0 is first in the
  settings file and the runner runs file order.
- §4.5 **Containment and registry as standing;
  publication pattern; status-only interim notices:**
  **DONE** — (C)/(G8) in the runner; registry merge before
  analysis with pre/post identity in the manifest; the
  run's rows, stats, reports and manifest publish under
  `rounds/round9/data/stage1/` in the report package, as
  Stage 0's did.
- §4.6 **Ghost pre-gate before Stage 2's live games:**
  **NOT IN THIS PACKAGE, BY THE RULING'S OWN SCOPE** — it
  is a Stage-2 prerequisite, discharged in the Stage-2
  package against the new teacher build.
- §3 **Tie value** (draw = 0 primary, 0.5 co-reported;
  horizon outcome −1; deadline stays turn 62): **DONE** —
  §2's definitions; both valuations computed for every
  setting; the turn-62 trigger is the D7 block, unchanged.
- Stage 0 clause list carry-over: clause 8 **DISCHARGED
  HERE**; clause 9 (ghost pre-gate) remains open by scope,
  owned by Stage 2.

## 10. Cost model (Stage 0's measured distribution; arithmetic shown)

Stage 0 is the closest completed run: 118 jobs × 100
worlds (2 candidates × W=50), 4 shards. Measured walls
from the run's own artifacts: primary pass (no horizon)
≈ 31 min wall → ≈ 124 min serial-equivalent → **≈ 63 s/job
≈ 0.63 s/world**; horizon pass ≈ 19 min wall → **≈ 39 s/job
≈ 0.39 s/world** (horizon worlds end at the trigger).

A Stage-1 evaluation is one panel state under one setting:
(2–4 selected candidates) × 25 worlds = 50–100 worlds.

| piece | arithmetic | estimate |
|---|---|---|
| capture, block 1 | 40 raw-speed games, 2 streams in parallel; the design (§4.5) prices capture as not the cost driver; driver timeout caps a game at 1,200 s | **≤ ~1 h wall** |
| eval, B0 | 240 evaluations × ~31–63 s serial (50–100 worlds at 0.63 s/world) | 2.1–4.2 box-h serial → **0.5–1.1 h wall** at 4-way |
| eval, five +H settings | horizon worlds run cheaper per world (0.39 s) but ×2–×4 hook budgets and ×2 deadlines let the tail run long; planning band per evaluation 30–125 s | 10–21 box-h serial → **2.5–5.5 h wall** |
| analyze + merge | seconds-to-minutes | negligible |

Whole stage planning range: **≈ 3–7 h wall**, with B0's
measured distribution in hand after the first ~1 h —
before five-sixths of the eval spend is committed (the
registered reason B0 runs first). Cross-check: the
design's older planning mean (25 s per live Decide at
k=25) over 1,440 evaluations gives 10 box-h serial, inside
the band above. No figure here comes from a smoke or a
single-state probe; if B0's measured mean lands outside
the band, the run's own report — not this model — prices
the remainder, and the operator can stop between settings
(the runner's `SETTINGS=` / phase structure exists for
exactly that).

## 11. Launch gate

This package is **staged for review; nothing in it has
run**. Stage 1 launches only when (a) Claude has approved
this package's code at its committed sha, (b) Joe gives
his explicit go for Stage 1 in chat, and (c) the launched
sha equals the approved sha (or differs only under
`rounds/`). The run manifest will record both shas. The
ghost pre-gate is **not** a Stage-1 launch condition
(ruling §4.6); it gates Stage 2.

## 12. What the reviewer is asked to rule

1. The package as a whole (approve / changes requested).
2. §2's horizon-value application point: the −1 price
   applied in the analyzer's reads (both valuations
   computed for every setting), the pin carried end-to-end,
   its live-Decide effect reserved to Stage 2's build —
   confirm this matches the §3 registration's intent for
   Stage 1's offline form.
3. §2's B0 native valuation (0, the fleet teacher's own
   price) as the control's tuple value.
4. Whether a box smoke (a few panel states through B0 and
   B0+H under the launch pins) is required before the full
   eval, or the fixtures + B0-first sequencing suffice.
