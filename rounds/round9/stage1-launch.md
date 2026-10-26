# Round 9 — Stage 1 LAUNCH record

**Launched: 2026-10-26 07:21:43 EDT (11:21:43 UTC)** on the
sim box (golf-gamer), on Joe's explicit go in chat
(2026-10-26 07:19 EDT). Runner: `bash
/home/joe/tcg/round9_code/run_stage1.sh`, `PHASE=all`,
`BLOCK=1`, no `SETTINGS` restriction, setsid detached
(box pid 4142036 at launch).

- **Launched sha:** `86de3be13f42f48344abc332f2f0e8a15d10e8a1`
  (the sha Claude's confirmation at
  `claude-reply-86de3be.md` approves). **Repo HEAD at
  launch:** `6a874c4bea87d40a666cd7f8946f319c488d0654` —
  the difference from the approved sha is only under
  `rounds/` (the confirmation reply itself, committed at
  6a874c4b, and the rules-reference §6 amendment at
  8154df98), the difference the confirmation explicitly
  allows. All code bytes launched are the approved bytes.
- **Code:** the 18 files of `rounds/round9/code/` were
  hash-verified in the staging tree against the hash table
  in the committed (fix-pass amended)
  `stage1-launch-package.md` — all match, including
  `stage1_analyze.py` `38467613…d319e381` and
  `run_stage1.sh` `c138a313…19b74b284` — then synced to
  `/home/joe/tcg/round9_code/` and read back: box hashes
  identical to staging (full table in the run manifest,
  below).
- **OUT:** `/home/joe/tcg/r9s1_out`. Launch log:
  `/home/joe/tcg/r9s1_out/stage1_launch.log`. Run manifest
  (written at launch; the runner's own
  `stage1_manifest.json` follows at analyze):
  `/home/joe/tcg/r9s1_out/stage1_launch_manifest.json`.

## Pre-flight (all checks before the first game)

- **Fleet tree:** `/tmp/gravytree` present; `search.php`
  `8f6b35da…`, `featurize.php` `f81193e0…`, `play_game.php`
  `4ac2d62d…`, `ParseGamestate.php` `0e88dd58…`, deck
  `b8b41390…` — all match the runner pins.
- **Continuation server:** the production
  `rl/search_server.py` (`81ef2cdb…`) — the label path's
  server, not the patched gate server — one per seat, each
  log asserting the model loaded: Gravy `ckpt_v10`
  (`44f1e5d7…`) on cuda.
- **Registry — restoration disclosed.** At pre-flight the
  registered path `/home/joe/tcg/registry-vault/
  do_not_train_registry.json` did not exist anywhere under
  `/home/joe/tcg`. The canonical registry survived only as
  the vault snapshot
  `do_not_train_registry_2026-10-25_post-resume-normalized.json`,
  whose sha256 is exactly the registered `28b5acfa…` with
  `n_games` exactly 6,241. The live path was restored by
  copying that verified snapshot byte-for-byte before
  launch — an operational restore of a registered input,
  no content change. The runner's own registry pre-check
  then read `n_games=6241`.
- **SHM:** pre-flight G8 sweep (evidence
  `g8_preflight_before/after.txt` in OUT): 17 segments,
  all `nattch=0`, → 0; no game processes were running. The
  runner's in-run G8 then found 0 → 0.
- **/tmp space:** stale Stage 0 shard-tree copies
  (`/tmp/r9s0_tree_*`, 8 trees; Stage 0's artifacts of
  record live in `/home/joe/tcg/r9s0_out`) removed
  pre-launch; /tmp went from 80% used (4.1G free) to 65%
  (7.0G free).

## First verification (~07:23 EDT)

Runner alive; launch log free of aborts and pin mismatches.
Capture seat 1 **complete**: 20/20 games (seeds
21001–21020) in `cap_s1_b1.jsonl`, the paired driver's arm
assertions OK (the runner's manifest check printed its OK
line into the launch log). Capture seat 2 underway (the
game-id file growing past seat 1's ids). Snapshots landing
under the seat-1 stream logdir.

## Registered run order and outcomes (from the package)

Capture block 1 (seeds 21001–21040, two seat streams) →
registry merge (tag `r9s1_capture`) before the panel
exists → panel (240 contested states, ≤ 8/game; a
shortfall exits 3 for another capture `BLOCK`) → eval in
settings-file order, **B0 first with the B0 gate** (a B0
abort, or any B0 analyzer-integrity failure, stops the
run before the +H settings — ruling §4.4) → the five +H
settings → analyze + the runner's `stage1_manifest.json`.

Selection: cheapest qualifier (mean per-decision wall;
ties p95, then max) among the five +H settings at
**per-state completion ≥ 0.95** (a state completes iff
every selected candidate reaches ≥ 20 finished worlds);
B0 is the control — read and reported, never selected.
**NO CALIBRATED SETTING stops the round**; a qualifier
feeds Stage 2. Valuations: draw = 0 primary, 0.5
co-reported (ruling §3).

## ABORT — eval supervision defect (2026-10-26, ~07:25 EDT)

The launch did NOT survive into evaluation. Capture (both
seats), registry merge, and the panel (240 states over 31
games) completed under the runner's own checks. Entering the
eval phase, the runner's main shell died at the first setting
(B0): `run_stage1.sh` line 343 reads `PIDS="" FAIL=0 pid` — a
stray trailing token makes bash treat the assignments as
environment for a nonexistent `pid` command, so `PIDS` is
never set in the shell; line 380 (`PIDS="$PIDS $!"`) then
aborts the shell under `set -u`. Shard 0's subshell was
already backgrounded and ran orphaned (B0 shard 0 only);
shards 1-3 never spawned; no concatenation, gate, or further
settings could follow. The builder stopped the orphan
processes at ~07:27 EDT. The defect is unique to line 343 —
the capture/server supervision uses the correct pattern
(`SRV_PIDS=""`, line 170), which is why the early phases ran.

No measurement is affected: no setting completed, and B0's
partial shard-0 rows are orphaned outputs the fixed runner
regenerates from zero (OUT dir preserved as the record).
The fixture net's hole is named plainly: fixtures exercised
the eval main and the B0GATE block, never the shard
supervision block between them — Claude's review and the
builder's audit both missed a one-token typo there.

Path: one-token fix (line 343 -> `PIDS="" FAIL=0`) + a
fixture that executes the supervision block itself -> fix
commit for Claude's confirmation -> relaunch under Joe's
standing go. The approved bytes are otherwise untouched.
