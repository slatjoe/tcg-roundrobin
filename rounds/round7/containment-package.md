# Round 7 — the containment package: (C) as production code + the revised pre-gate runner

**Parent:** 500b03ee60088af7207eeb506e838574e8547b16 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-ad1d7c6.md` §2 ((C) preferred, to be built and verified), §5 (the pre-gate runner's four changes) and §7 (the sequence), on the evidence of `rounds/round7/extended-probe.md` — tests (ii)/(iii)/(iv) hold, (i) shown empirically, GATE_TIMEOUT restated at **3,870 s**.
**Status: NOTHING LAUNCHES on this package.** It carries (C) as production code (§1) and the revised pre-gate runner (§2). The pre-gate launches only on Claude's approval of this package at its sha **and** Joe's go; the fleet after it, the same way (reply §7 steps 3–4). (A) is not engaged: (C) passed its field tests in the probe.

**Package contents**

| File | Role |
|---|---|
| `containment-package.md` | this package: §1 (C) as code, §2 the revised pre-gate runner, §3 the launch state |
| `code/shm_sweep.py` | §1: the (C) production sweeper (NEW), 9,884 B, sha256 `728a0149e1241079ba09898481c9cacfe6606b53c5aa3bab09b3a1009269b290` |
| `code/parse_r3_pair.py` | §2.1: the strict r3_pair table parser (NEW), 4,162 B, sha256 `ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1` |
| `code/run_gravy_pregate.sh` | §2: the pre-gate runner, revised in place, 14,934 B, sha256 `ddbc9d3c642f8d5e542fa072cceee4d3512f7dc41809704a7d2bb0bcb2def7ea` (supersedes the §8 draft `19cb3c13…`) |
| `code/run_gravy_gate.sh` | §1.4: the fleet runner, revised in place (the sweeper pin + integration), sha256 `49cf0d78c0263a31cf692c87a759332c2f9dfa3289bab7bebcc3434cced38e4e` (chain `2895c4a0…` → `0c458627…` → this) |
| `code/shm_selector.py` | **untouched** — the probe's dry-run artifact, sha256 `23f15ea7…` as committed |

---

## 1. (C) as code — `shm_sweep.py`, the fleet's containment

### 1.1 The production form

`shm_sweep.py` is derived from the probe's `shm_selector.py` with the selection machinery carried over **unchanged** — `parse_segments`, `live_pids`, `game_keys`, `select`, and the four selection rules of reply §2(C) are the same code that passed tests (ii)–(iv) in the probe (a segment is selected iff: (1) owner `joe` and `nattch == 0`; (2) `cpid` and `lpid` both dead; (3) its key is in neither `{n, n + 1000000}` for any directory `n` under the tree's `vendor/talishar/Games/`; (4) its shmid was not in the run-start listing). What the production form adds is the deletion pass and the mode flag:

- **LIVE mode (the default):** in the same pass that selects it, each selected segment is deleted with `ipcrm -m <shmid>`; the result is logged per deletion (`DELETE shmid=… key=… -> OK` / `-> FAILED rc=… <err>`), and a per-pass tally is written (`DELETED pass=N count=… failed=…`). A failed `ipcrm` is reported in the log and never silently passed; it does not stop the sweep (the segment is re-selected next pass if it still qualifies, and the failure stays on the record).
- **`--dry-run`:** the probe behavior exactly — same selection, same PASS/SELECT logging, no deletion — so one binary serves the (C) tests and production. The log's start line records the mode.
- The PASS and SELECT lines keep the probe's formats (pass timestamp; per segment: shmid, key, cpid, lpid, nattch, create/attach/change times), so a production log reads against a probe log directly.

### 1.2 Interface

Self-looping: one pass immediately, then one per `--interval` seconds (default 60, the probe's cadence), until `--stop-file` exists. Arguments: `--log`, `--start-file` (rule 4's exclusion set, one shmid per line), `--games-dir` (the tree's `vendor/talishar/Games`), `--interval`, `--stop-file`, `--dry-run`. The form is chosen because the runners already manage long-lived helpers with exactly this lifecycle — the tree's search servers are started in the background, tracked by pid, and reaped under the runner's trap — so the sweeper is started the same way (after the run-start listing is saved) and stopped the same way (after the last game). A per-pass external invocation would have to re-derive the rule-(4) set on every call and could not guarantee the cadence against the run's own chunk boundaries.

### 1.3 Safety (restated briefly; the full argument is the file's header)

The selector can only over-keep, never wrongly delete: a live game's segments are protected twice (live pids under rule 2; its directory under rule 3); anything predating the run is excluded by rule 4; selection and deletion happen in one pass from one `ipcs` snapshot, and every borderline case resolves to KEEP. The one operational hazard is **pid reuse**: a dead child's recycled pid makes its segment look alive under rule 2, so it is kept — the safe direction (the leak grows by that segment; the run is never harmed). The probe's coverage test bounds the effect empirically: its selected set accounted for the wave's residue exactly (584 selected + 1 rule-3 exclusion = 585).

### 1.4 The box tests (disclosed; no games)

Run 2026-10-22 on the box, scratch dir `/tmp/shmtest/` (its logs are the evidence, kept there). The deployed test copy was hash-verified against the committed file (`728a0149…`) before running.

| Step | Record |
|---|---|
| (a) syntax | `python3 -m py_compile` under the runners' interpreter (`rl-env` python) — **OK** |
| (b) dry-run on the baseline | box at **0 segments**; one `--dry-run` pass: `total=0 selected=0`; count after: **0** |
| (c) live micro-test | A throwaway `php -r`-style script (`make_segs.php`; PHP 8.5.4) created three `shmop` segments and exited, leaving `cpid = lpid = 814971` (dead), `nattch = 0`, owner `joe`: keys **777000111** (shmid 547192832) and **777000222** (shmid 547192833) — orphans — and key **555000111** (shmid 547192834), equal to a fabricated directory `555000111` under the scratch Games root. One LIVE pass with `--games-dir` at the scratch root: `total=3 selected=2`; `DELETE … -> OK` for exactly the two orphans, `failed=0`; the rule-3 segment was **not selected** and remained |
| close-out | the kept segment removed by hand (`ipcrm -m 547192834`), the fabricated directory removed; final count **0 = baseline** |

No step misbehaved; nothing was tuned.

### 1.5 Runner integration (the fleet)

`run_gravy_gate.sh` revised in place — **second in-place revision** (chain: `2895c4a0…` fleet-alignment draft → `0c458627…` fleet-alignment registration, the driver + retry pins → **`49cf0d78…`** this package), `bash -n` clean:

- a guard pin on the sweeper: `expect_hash "$TREE/shm_sweep.py" 728a0149…` (line 100), beside the K2 and driver pins — a tree without the reviewed sweeper aborts before any output;
- after the guard, the run-start listing is saved (`$OUT/gate_ipcs_run_start.txt`) and its shmids extracted (`$OUT/gate_shm_start.txt`); the sweeper is started in the background before the servers (lines 108–121), 60 s passes, log at `$OUT/gate_shm_sweep.log`;
- after the last chunk, the stop file is touched and the runner waits for the sweeper's final pass before killing the servers (line 191), so the fleet's closing `ipcs` counts are post-containment; the cleanup trap kills the sweeper as a backstop;
- deployment: the launch manifest places `code/shm_sweep.py` at the tree root, as it does the driver — the guard verifies the placed bytes.

`GATE_TIMEOUT` remains a required env input with no default; the launch manifest supplies **3,870** (extended-probe.md §6), now noted in the runner's header.

---

## 2. The pre-gate runner, revised — `run_gravy_pregate.sh`

Revised in place: `19cb3c13…` (the §8 draft) → **`ddbc9d3c…`** (14,934 B), `bash -n` clean. Everything the reply §5 found right is kept: the pins (now nine — below), `GATE_TIMEOUT`/`GRAVY_MODEL` required with no defaults, the arm order (ghost s1, ghost s2, raw s1, raw s2, the determinism re-run), determinism read **before** the ghost tables, the R16 control through `--raw-control` (its own `RAW-CONTROL: PASS` string), the fallbacks stop, and the production-server hash before/after. The four §5 items, mapped:

### 2.1 [§5.1] Parse the determinism check; don't grep it

The draft's `grep -c IDENTICAL` is gone. The new helper **`code/parse_r3_pair.py`** (sha `ed47c9cd…`, pinned in the guard, line 143) parses `r3_pair.py`'s markdown table strictly: a table with the exact 9-column header (`seed | pair | verdict | within-row hits | seq | outcome equal | modes ok | seat ok | assert ok`); exactly `--expect-rows` data rows (10); and **every** row with verdict `IDENTICAL`, within-row hits `0`, outcome equal `True`, modes ok `True`, seat ok `True`, assert ok `True`. Any defect — a short table, a `MISSING_GAME`/`INVALID_*` row, a `False` in any checked column — prints a `PARSE-FAIL` line per defect and exits 1. The determinism read (runner lines 266–278) runs the parser on `pregate_pair_determinism.txt` and **stops the pre-gate** on a non-zero exit, before the ghost tables are produced. The same parser is run over both ghost tables with its output recorded (`pregate_pair_ghost_s{1,2}.parse.txt`, runner lines 297–304, record-only): the ghost read ships in the launch record using this same parser, its disposition (including the K5 marker class) made there, as the §8 draft had it.

*Parser verification (synthetic, disclosed):* a fabricated 10-row all-IDENTICAL table passes (exit 0); the same table with one row's outcome-equal flipped to `False` fails with that row named; with one row's within-row hits at 3, likewise (`PARSE-FAIL: seed 8510: …`). The column set and value spellings are `r3_pair.py`'s own print formats (round-3 code, sha `13f95ebe…`, the tree's copy hash-identical).

### 2.2 [§5.2] Containment inside the run

- `PREGATE_SWEEP=1` is **forced**: the runner aborts if it is not set to `1` (lines 157–161), and the start-of-run sweep is the standing G8 script itself — `bash gate_ipcs_cleanup.sh $OUT/pregate_ipcs_startsweep` (line 162) — not the draft's inline copy of its form. The script's evidence files (`_before/_after/_attached_kept/_stale_ids`) land beside each prefix in `$OUT`.
- The standing G8 sweep runs again **after ghost_s1** (line 252, prefix `pregate_ipcs_post_ghost_s1`) and **after ghost_s2** (line 256, prefix `pregate_ipcs_post_ghost_s2`); between arms no driver is running, and the G8 guard (it refuses only while `play_game`/`paired_driver` live) lets the servers stay up. A failed sweep stops the run.
- **Before each arm** — all five driver invocations, via `check_headroom` (lines 210–219), called at the head of `run_arm` — the run aborts if the segment count is above **2,800**; the count is logged to `pregate_ipcs.txt` either way.
- **Both mechanisms run** (the package's registered choice, argued here as the reply invites): the (C) production sweeper also runs LIVE for the run's whole duration (started at lines 168–181 from the post-sweep run-start listing, stopped at line 317 before the closing listings). §5.2 was written before (C) passed its tests; its G8 points are quiescent checkpoints in a sequential run and cost nothing, and the periodic (C) sweep is the containment that also guards the gaps *within* a 20-game ghost arm — at the original probe's rate an arm alone could add ~3,560 segments, which the between-arm sweeps by themselves would only answer after the fact. Carrying both keeps §5.2's registered steps intact and makes (C)'s first production run a sequential, low-stakes one before the fleet depends on it.

### 2.3 [§5.3] `TCG_CLEAN_CHILDREN=1` on the ghost arms

`run_arm` sets it in the ghost arms' driver environment only (line 229); the raw arms' invocations are the registered text unchanged (the driver reads it from its own environment and applies it after each completed teacher-family game — the ghost machinery's timeout-killed and Throwable children are the classes it cleans). Registered in the reply as the K3 text's omission, now carried in the runner's header and at the call site.

### 2.4 [§5.4] The registry step: game ids only; driver exit codes checked

- The `--snap-index` arguments are **dropped** (registry call at lines 336–340: `--registry … --ids $IDS` only). The reasoning is stated in the runner's header: the driver sets `TEACHER_SNAP_DIR` only for the `capture` arm (`paired_driver_gravy.py`: the env is set inside the `a.arm == "capture"` branch) and this runner never sets it, so **neither the ghost arms nor the raw arms produce a snapshot index at all** — there is nothing to quarantine beyond the game ids, and the earlier draft's paths would simply have been missing. (The fleet and the probes differ: their runners set `TEACHER_SNAP_DIR` externally, and their snapshot merges stand.) The `gate:gate` tag fallback for the chunkless ids file is unchanged, as accepted.
- **Every driver call's exit code is checked**: `run_arm` captures `$?` after either branch and stops the pre-gate on non-zero (lines 243–248); the same stop-on-failure form covers the two between-arm sweeps and the determinism `r3_pair.py` invocation (via the parser's verdict on its output).

### 2.5 The pins

Nine `expect_hash` pins now run before any server starts or any output is created: the K2 three (`search.php` `8f6b35da…`, `featurize.php` `f81193e0…`, `rl/search_server.py` `ab85fa1b…`), the driver `0a6b7a85…`, the retry `c3fb227e…`, the checkpoint `44f1e5d7…`, and the three runner-side tools the launch manifest deploys at the tree root — `gate_ipcs_cleanup.sh` `338183e2…` (the round-3 committed copy; the box's probe-deployed copy is hash-identical), `shm_sweep.py` `728a0149…`, `parse_r3_pair.py` `ed47c9cd…`.

---

## 3. The launch state this leaves

- **Timeout:** `GATE_TIMEOUT = 3,870 s` (extended-probe.md §6: `max(700, ⌈3 × 1,289.8⌉)` over all 8 probe games, the sample now containing the trigger population); supplied by each launch manifest, inherited by neither runner.
- **Registry:** **4,981 games**, sha256 `d5cfcf79…` (extended-probe.md §5), unchanged by this package (no games were played for it; the micro-test created no game ids).
- **SHM:** the box stands at **0 segments** — the micro-test's close-out restored the clean baseline the probe left.
- **Trees and tools:** `/tmp/gravytree` carries the placed launch-copy driver with all K2 pins verified (extended-probe.md §0); the launch manifest's remaining placements are the three runner-side tools of §2.5 at the tree root, each abort-checked by the pregate guard (the fleet guard pins its own tool, §1.5).
- **What waits:** (1) Claude's approval of this package at its sha, then (2) the pre-gate on Joe's go (fleet wall not engaged; the pre-gate is 50 sequential games under (B)+(C) containment), then (3) the fleet on Joe's go, with (C) as its containment and 3,870 s as its timeout — the reply §7 sequence, unchanged. (A) remains the un-engaged fallback: it would be needed only if (C) misbehaves in production, and its conditions (reply §2(A)) are untouched by anything here.

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude reviews; the pre-gate and the fleet launch only on Claude's approval of this package at its committed sha plus Joe's go in chat. Box test records: `/tmp/shmtest/` (the sweeper's dry-run and live logs, the test driver, the segment maker).*
