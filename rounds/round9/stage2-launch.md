# Round 9, Stage 2 — launch record

**Joe's go:** 2026-10-26 18:16 EDT, in the TCG chat. **Launched sha == approved sha `2d64302f2594f911130ed3530830bd48a1af203c`** (repo HEAD at go: `596baaed`, the confirmation commit; this record differs only under `rounds/`, as the launch conditions allow). Approval: `claude-reply-2d64302.md` (CONFIRMED).

**Deploy.** The committed `rounds/round9/code/` tree was synced to `/home/joe/tcg/round9_code` on the box; all 10 pinned files read back and match the package table exactly (search_s2.php `85490e8e…`, run_stage2_pregate.sh `581f47aa…`, run_stage2_games.sh `8bb176d0…`, run_stage2_l3.sh `f2c26978…`, stage2_games_report.py `62b5b319…`, stage2_analyze.py `9b1a0677…`, s2_label_main.php `c7a76af4…`, settings_stage2.json `2a1634cc…`, build_s2_jobs.py `b91f3a6c…`, pregate_check.py `bc5327d3…`).

**Pre-flight (recorded in the launch manifest).** No stray sim processes (standing services only: dashboard :8097, spectate :8901). SHM 14 segments pre-launch; the pre-gate's G8 sweep took it to 0. Registry present at `/home/joe/tcg/registry-vault/do_not_train_registry.json`, sha256 `902682fc…`, **6,281 games** — exactly the post-Stage-1 state, no restoration needed. Box PHP 8.5.4. Gravytree pins verified in place.

**Launch manifest:** `/home/joe/tcg/r9s2_out/stage2_launch_manifest.json` (sha256 `cf117f16…`) — launched/approved shas, Joe's go, deployed hashes, pre-flight, and the confirmation's two not-conditions logged for the next code touch (planted pass-manifest round-trip case; gamename uniqueness assert).

**Pre-gate: IDENTICAL.** Launched 18:17:59 EDT (pid 211958); exited cleanly ~19:16 EDT ("STAGE 2 PRE-GATE COMPLETE"). Verified from primary records: `pregate_check.txt` carries the checker's own `PREGATE: IDENTICAL` line; `/home/joe/tcg/r9s2_out/pregate/pregate_manifest.json` records verdict IDENTICAL + `search_s2_sha256` == `85490e8e…` + the `teacher_tuple_json` (H8k-180+H). The passed pre-gate's registry merge took the registry to 6,331 games (sha256 `7dcb2a7f…`).

**Games: launched 19:16:39 EDT** (runner pid 326157, setsid-detached, log `/home/joe/tcg/r9s2_out/games_launch.log`). First-minutes checks, all verified from box state at 19:19 EDT:
- the PREGATE-GATE passed — the log carries "pre-gate gate: manifest IDENTICAL under this run's search_s2.php pin and tuple — proceeding"; no gate abort;
- both patched servers loaded the correct checkpoint (ckpt_v10, on cuda) — `games/srv_s1.log`, `games/srv_s2.log`;
- all 4 block drivers (s1a/s1b/s2a/s2b) spawned and running;
- teacher stat rows flowing in all four block logs (`games/games_<blk>_log/search_stats.jsonl`), each carrying the tuple stamp `{"name":"H8k-180+H","hooks":8000,"deadline_s":180,"horizon":62,"horizon_value":-1,"k":25,"margin":1.5,"pinned":1}` (read directly from the rows);
- zero malformed/tuple-abort rows in any stat file; no ABORT anywhere in the launch log.

**Paths.** OUT `/home/joe/tcg/r9s2_out/` — `stage2_launch_manifest.json`, `pregate_launch.log`, `pregate/` (manifest, check text, row files, merge record), `games_launch.log`, `games/` (per-block rows, stat logs, snap dirs, server logs).

**What remains.** The 200 games run detached (planning bound ~9 box-hours at the mean price, ~25 at the tail). On completion the games runner merges the game ids and runs the tuple-audited games report itself; then `run_stage2_l3.sh` (jobs → labels → the registered read); then the Stage 2 report with `data/stage2/` published, per the package's run order. Interim notices are status + paths only.
