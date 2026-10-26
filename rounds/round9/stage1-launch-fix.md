# Round 9 — Stage 1 launch fix (runner eval supervision)

**Parent package:** edddf5ed (Stage 1 launch package), as
confirmed at 86de3be1 (claude-reply-86de3be: CONFIRMED,
launch on Joe's go). **Status:** REVIEW-GATED — the fix is
to `code/run_stage1.sh` (one token) plus a new fixture;
nothing here launches anything. The Stage 1 launch of
2026-10-26 (Joe's go, 07:19 EDT; launched sha 86de3be1)
died inside the runner's eval phase before B0 produced a
single row. This file is the record of that failure, the
fix, and the fixture that closes the hole it fell
through.

## 1. The defect

`code/run_stage1.sh` line 343 (the eval phase, per-setting
iteration) read, in the launched bytes
(run_stage1.sh sha256 c138a313…):

```
    PIDS="" FAIL=0 pid
```

The stray trailing token `pid` changes the line's parse:
bash treats `PIDS="" FAIL=0` as environment assignments
for a command named `pid`. There is no such command, so
the shell prints `pid: command not found` and — the
load-bearing part — **neither assignment takes effect in
the shell**. `FAIL` happens to be re-initialized by
nothing and read only after the wait loop; `PIDS` is
appended to at line 380:

```
      PIDS="$PIDS $!"
```

The runner runs under `set -u` (line 80), so the first
shard spawn's append reads an unset variable and the
shell dies on the spot: `PIDS: unbound variable`.

**Launch evidence.** The box launch log's lines 15–16
are the two symptoms in order — the phantom-command
error, then the unbound-variable death — at the first
eval iteration (setting B0, shard 0). The shard-0
subshell had already backgrounded when the parent died
and was orphaned; it has since been stopped. No capture
or panel output was harmed: the run died at the first
eval spawn, after capture, registry merge, and panel
had completed. No measurement rows exist from the
launched attempt.

## 2. Why the fixture net missed it

No fixture executed the runner's eval-supervision code.
The inventory at launch:

- `fx_s1_eval` drives `code/s1_eval_main.php` standalone
  against a stub tree — the PHP driver, not the bash
  that spawns it.
- `fx_stage1_analyze.py`, `fx_build_panel.py`,
  `fx_merge_registry.py` exercise Python units.
- `fx_b0_gate.sh` extracts the runner's B0GATE block
  verbatim — but that block sits **after** supervision
  in the runner (it consumes rows supervision was
  supposed to produce), so the verbatim-extraction net
  covered the gate and not the spawner.
- `bash -n` passes on the defective file: the line is
  syntactically valid. The defect is a runtime parse
  effect, invisible to syntax checks and to any read
  that treats the line as the initialization it
  resembles.

## 3. The fix

Line 343 now reads:

```
    PIDS="" FAIL=0
```

One token removed; nothing else in the runner changes.
Proof, not assertion: re-adding the token to the fixed
file reproduces the launched sha256 exactly
(c138a313ebf1e5d102398fecb25cda487abdb317d8a679a1c8a4c3d3ea74b284),
so the diff between the launched runner and the fixed
runner is that token and nothing else. `bash -n` is
clean on the fixed file.

**Initialization audit** (the same class, whole file).
Every `NAME=""` initialization in `code/run_stage1.sh`:

| line | text | form |
|---:|---|---|
| 170 | `SRV_PIDS=""` | standalone assignment |
| 171 | `SWEEP_PIDS=""` | standalone assignment |
| 261 | `SARGS=""` | standalone assignment |
| 306 | `SWEEP_PIDS=""` | standalone assignment |
| 343 | `PIDS="" FAIL=0` | standalone assignment (two variables; was the defect) |

No other instance of the class exists. (The runner's
remaining multi-assignment lines are environment
prefixes on real commands — the `setsid nohup` server
launches and the `php` eval invocation — which is the
construct line 343 accidentally imitated; in each of
those a command follows on the same logical line.)

## 4. The new fixture: fx_shard_supervision.sh

`fixtures/fx_shard_supervision.sh` executes the
runner's eval shard-supervision block **itself**,
extracted verbatim — runner lines 343–386, from the
PIDS initialization through the spawn loop, the wait
loop, the FAIL check, and both `cat` concatenations.
The region starts after tree setup (the tree copies,
`expect_hash` calls, and `start_sweeper` invocations
above line 343 are not supervision; the fixture
pre-creates the four tree dirs the block hardcodes)
and ends at the stats cat, the last supervision line
(the "setting done" echo and the B0GATE block after it
belong to other suites). The block runs under
`bash -u`, the runner's own mode.

Stubs: a fake `php` first on PATH appends one planted
row to `$MEAS_OUT` / `$EVAL_STATS` per invocation,
tagged by shard/player; a planted `jobs_FXSET.jsonl`
whose games hash (by the block's own splitter) across
3 shards with both players present. Cases, 19 checks,
**FX-SHARD-SUPERVISION: ALL PASS**:

- **Happy path:** all shards spawn; concatenated
  evals/stats hold all 8 stub rows (4 shards × 2
  players); a shard slowed 3 s per call still lands
  its rows in the concatenation, and elapsed time
  (6 s in the recorded run) proves the wait covered
  every spawned pid;
  FAIL stays 0, exit 0.
- **Failure path:** one shard's php exits 1 → the
  block prints `ABORT: an eval shard failed for
  setting FXSET` and exits 1 **before** concatenating.
- **Before/after:** the same fixture against the
  pre-fix block text (the token re-added to a temp
  copy of the extraction) reproduces the launch death
  exactly — `pid: command not found`, then
  `PIDS: unbound variable`, exit non-zero, no
  concatenation. The fixture fails on the text that
  launched and passes on the text that replaces it;
  that is the hole, closed.

## 5. Full-suite rerun

All six Stage 1 suites rerun after the fix (verbatim
transcript: `fixtures/fx_stage1_outputs.txt`):
fx_s1_eval 20, fx_stage1_analyze 25, fx_b0_gate 10,
fx_shard_supervision 19, fx_build_panel 5,
fx_merge_registry 6 — **85 PASS lines, every suite
ALL PASS, zero FAIL lines.**

## 6. What did not change

Hash diff over all 18 files in `code/`: **only
`run_stage1.sh` differs.** In particular
`stage1_analyze.py` (384676138d3fb57ca26fa66b2ead31420a2d6589618b4ebe6494b927d319e381)
and `settings_stage1.json` (de7e09d36f4c0f6c51baff80c9b984f58c480fb079f667a2d2836b0067514459)
are byte-identical to the confirmed package, and the
runner's internal pin literals are untouched (the
one-token diff of §3 proves it). The registered design
— settings, panel, selection rule, B0 gate — is
unchanged. The capture/registry/panel outputs of the
failed launch are unaffected by this fix and are not
re-run by it; whether the relaunch reuses them or
starts clean is a launch-manifest decision, not a
code question.

## 7. Hashes

- code/run_stage1.sh: c138a313ebf1e5d102398fecb25cda487abdb317d8a679a1c8a4c3d3ea74b284 -> b0b08c555b83c8b2ec681402a4eabeb5c9f360758e9e6b9a61f7fe21027339e6
- fixtures/fx_shard_supervision.sh (new): 9fb97219fd98c3517a006feb3e267b9ca662da0cb26212c854b8ca91f685cdbc
- fixtures/fx_stage1_outputs.txt (refreshed): d470f77acd16ee389399148366860c727921b180f273ad05abfc3ec612de14ef
- fixtures/README.md (Stage 1 section): ff737eed7e5b0a1a404f34cd0eb0f428ecc02a6ea928f0a0017b3048bb0077ac

## 8. The ask

Confirmation check on this file only: the one-token
runner fix, the initialization audit, and
fx_shard_supervision (including its before/after
demonstration). On confirmation, Stage 1 relaunches on
Joe's go with launched sha == approved sha.
