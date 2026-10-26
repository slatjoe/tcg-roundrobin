# Round 9 — Stage 1 RELAUNCH record (eval on reused capture + panel)

**Relaunched: 2026-10-26 07:49:24 EDT (11:49:24 UTC)** on
the sim box (golf-gamer), on Joe's explicit go in chat
(2026-10-26 07:46 EDT), under the conditions of Claude's
confirmation at a13cabc5 (`claude-reply-a13cabc.md` §2).
Runner: `PHASE=eval bash
/home/joe/tcg/round9_code/run_stage1.sh`, setsid detached
(runner pid 4179533 at launch). The aborted launch's capture,
registry merge, and panel are REUSED — PHASE=all was not
run; no game was re-captured and the registry was not
re-appended.

- **Launched sha:** `a13cabc5a95b2ae0d6cc9ed15a7d1bd3ecb1be23`
  (the fix commit Claude confirmed). **Repo HEAD at
  relaunch:** `2ffd9638` — differing from a13cabc5 only
  under `rounds/` (the confirmation reply file itself),
  the difference the confirmation allows.
- **Code:** the fixed runner was synced from the staging
  tree and read back on the box: `run_stage1.sh` sha256
  `b0b08c555b83c8b2ec681402a4eabeb5c9f360758e9e6b9a61f7fe21027339e6`.
  The other 17 files in `/home/joe/tcg/round9_code/` were
  re-hashed on the box before launch and are byte-identical
  to the confirmed package (full table in the run manifest).
- **OUT:** `/home/joe/tcg/r9s1_out` (shared with the aborted
  launch — its record files stay untouched, incl.
  `stage1_launch.log`). Relaunch log:
  `/home/joe/tcg/r9s1_out/stage1_relaunch.log`. Relaunch
  manifest: `/home/joe/tcg/r9s1_out/stage1_relaunch_manifest.json`.
  PHASE=analyze runs as the follow-up step once eval
  completes (per the confirmation's scope: eval, then
  analyze).

## Pre-launch records (claude-reply-a13cabc §2)

- **(§2.2) Processes:** a fresh process listing before
  launch shows NO leftover labeler, eval, or production
  search-server processes from the aborted run (the
  orphans stopped at ~07:27 EDT stayed stopped).
- **(§2.2) SHM:** 188 segments before the sweep — the
  killed orphans' leaks, all `nattch=0` — and the standing
  G8 sweep took it to **0** (evidence:
  `g8_relaunch_before.txt` / `g8_relaunch_after.txt` in
  OUT).
- **(§2.1) Registry:** `/home/joe/tcg/registry-vault/
  do_not_train_registry.json` sha256
  `902682fcd8c6ad109f66f3c50a1d21eb48d32d5c3339158bd541982e635b7bf3`,
  `n_games` **6281** — exactly the aborted launch's
  post-merge state, verified against its merge artifact
  (`registry_merge_b1.txt`: "+40 new (tag r9s1_capture),
  0 already under this tag; n_games=6281; registry sha256:
  902682fc…"), i.e. 6,241 (restored snapshot) + the 40
  capture games, unchanged since that merge.
- **(§2.1) Panel:** `panel_jobs.jsonl` sha256
  `64fac6ce6560322de6184142e4efe87fd4fd7e128da6f5bb11e481f7f40de7ad`,
  240 rows — the panel the aborted launch built
  (`panel_report.json`: 240 states over 31 games), reused
  as-is.
- **(§2.3) Stale B0 outputs (assertion baseline, sizes
  before launch):** the orphan's partials —
  `evals_B0_shard0_p1.jsonl` 1,442,846 bytes;
  `stats_B0_shard0_p1.jsonl` 3,154 bytes (plus its
  `eval_B0_shard0_p1.err`, 583 bytes). Not deleted: the
  runner truncates `evals_*`/`stats_*` per shard at each
  setting's start (runner lines 363–364), and B0's final
  counts are asserted against the registered world count
  by the analyzer's guard at the B0 gate.

## Supervision watch (the abort's lesson)

The relaunch was watched continuously from launch to the
B0 gate — the specific chain that failed the first time
(spawn → wait → concatenate → gate) is the chain that was
verified, from the log and the process table, not assumed:

- **All four shards spawned** for B0, both players.
  Splitter lines in `stage1_relaunch.log`: shard 0 p1 68
  jobs, shard 1 p1 48, shard 2 p1 16, shard 3 p1 24,
  shard 0 p2 44, shard 1 p2 16, shard 2 p2 8, shard 3 p2
  16 — 240 in total. The runner parent, both production
  servers, the four shard subshells, and their php eval
  workers were observed alive at every check.
- **Error scan over the whole relaunch log** at the gate:
  `command not found` 0, `unbound variable` 0, `ABORT` 0.
- **The wait worked.** Stat rows were watched landing
  incrementally (39 total at ~07:59 EDT) and the runner
  printed `setting B0 done` only after all 240 had
  landed: **`setting B0 done: 17025 world rows, 240 stat
  rows`** (~09:20 EDT; B0 eval + gate ≈ 91 minutes from
  the 07:49:24 launch). `evals_B0.jsonl` holds exactly
  17,025 rows (sha256 `c0be1d29…`) and `stats_B0.jsonl`
  exactly 240 (sha256 `5d906422…`) — the §2.3 assertion:
  B0's regenerated counts equal the registered counts;
  no orphan rows mixed in.
- **B0 gate PASSED** — the runner's own line: "B0 gate
  PASSED: B0's rows pass every analyzer integrity check;
  continuing to the +H settings" (artifacts:
  `b0_gate_settings.json`, `b0_gate_report.json`,
  `b0_gate_report.txt`, written 09:20 EDT).

**State at the end of the watch (2026-10-26 09:20:56
EDT):** the first +H setting, **B0+H**, is underway —
all four shard splitter lines printed (68/48/16/24 jobs,
player 1), 10 runner processes alive, error scan still
0/0/0. The eval continues in settings-file order through
the remaining +H settings; `PHASE=analyze` is the
follow-up step once eval completes, per the
confirmation's scope. Full machine-readable record:
`/home/joe/tcg/r9s1_out/stage1_relaunch_manifest.json`
(sha256 `f462a24816a0aa257e89e30a0a83a88f51219633418686d249f2313b00cb45c6`).
No measurement figures are reported here — none exist
until analyze runs.
