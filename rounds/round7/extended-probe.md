# Round 7 — the extended probe (timeout re-measurement, leak re-measurement, the (C) selector dry run)

**Parent:** a1d2c00bb9760edf7ecbfa2ef1bba9d25adbf893 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-ad1d7c6.md` §3 (the extended probe, released) and §2(i)–(iv) (the (C) verification items). Context: `rounds/round7/fleet-alignment.md` §3 (the original probe, the registered timeout formula) and `rounds/round7/launch-package.md` (the O1 stop-finding).
**Status: COMPLETE.** The probe stopped after **wave 1** under its registered stop rule — seed 3007 reached trigger 62. Headlines: **GATE_TIMEOUT = 3,870 s** (set by seed 3010, a decided game at 1,289.8 s); the leak re-measured at **+585 segments for 4 teacher games**; the (C) selector's tests **(ii), (iii) and (iv) all hold** on this run's evidence, with (i) shown empirically (§4). Registry after the quarantine merge: **4,981 games** (§5). This is a probe — not the pre-gate, not the fleet; it launches nothing.

**A note on this record's sources.** During the run, the monitoring outputs delivered to the builder's session described a different wave 1 (different walls, turns, verdict and segment rise, and an ids discrepancy in the wave's game-id file). Those outputs do not match the box's records and no artifacts corresponding to them exist. Every figure below was re-derived in a single post-run pass from the run's files on the box — driver rows, stat rows, the selector log, the `ipcs` listings and the supervisor log, whose timestamps and contents agree with each other — and an interim checkpoint drafted from the monitoring outputs was discarded in full. Where the two accounts differ, the disk is the record; the differences are enumerated in §2.3 so the correction is checkable.

---

## 0. Pre-flight (2026-10-22, before any game)

Hash pins on `/tmp/gravytree`, all verified on the box:

| File | sha256 | Pin |
|---|---|---|
| `search.php` | `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` | ✓ |
| `featurize.php` | `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92` | ✓ |
| `rl/search_server.py` | `ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c` | ✓ |
| `paired_driver.py` (the placed launch copy) | `0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae` | ✓ |
| `gate_raw_retry.py` | `c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93` | ✓ |
| checkpoint `rl_out/gravy_ppo_gravybc3/ckpt_v10.pt` | `44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3` | ✓ |

**Server SHM check (reply §3):** the tree's `rl/search_server.py` contains no shared-memory use — `grep -ni 'shmop|sysvshm|shm_'` returns nothing. The servers hold no segments and stayed up across the sweep, as the reply's form requires.

**PHP:** `PHP 8.5.4 (cli) (built: Oct 19 2026) (NTS)` — the engine whose `shmop` calls create the segments under test in §4(i).

**Baseline:** the run-start `ipcs` listing (full `-m` / `-m -p` / `-m -t`, saved at `/tmp/xprobe/ipcs_run_start.txt`) shows **0 segments** — the clean baseline the §8 sweep left. The selector's rule-4 exclusion set (run-start shmids) is therefore empty.

**Form:** as registered (fleet-alignment §3.2 + reply §3): two per-seat servers from `/tmp/gravytree` (`SEARCH_MODEL=ckpt_v10.pt`; both startup lines read `search model loaded (…/ckpt_v10.pt) on cuda`; both servers' stats lines report `fallbacks=0 seat_mismatch=0`), left up across waves; per wave, 4 teacher games concurrently through the placed launch-copy driver, mirror Gravy deck, seats 1,1,2,2, `TEACHER_SNAP_DIR` per game, `TCG_CLEAN_CHILDREN=1`, `GATE_GAME_IDS_FILE` per wave, the driver's own per-game `--timeout 3600`; waves on seeds 3007–3010, 3011–3014, 3015–3018, 3019–3022; before each wave an abort check at 2,800 segments; between waves, full quiescence, then the standing G8 sweep (`gate_ipcs_cleanup.sh`, the round-3 committed copy) with before/after listings kept. Stop at the end of the first wave containing a game that reaches trigger 62, or after wave 4.

---

## 1. The (C) selector, dry-run form

`code/shm_selector.py` — 6,194 B, sha256 `23f15ea72dc0b9bdfd7a49b93cb43d7ce1aef66c6877ad4792f0140b0ee5cde6` (the deployed copy on the box was hash-verified identical before launch). It implements the four selection rules of claude-reply-ad1d7c6 §2(C) exactly: a segment is selected iff (1) owner `joe` and `nattch == 0`; (2) its `cpid` is not a live pid **and** its `lpid` is not a live pid (`ipcs -m -p`); (3) its key is in neither `{n, n + 1000000}` for any directory `n` currently present under **`/tmp/gravytree/vendor/talishar/Games/`** (the exact directory read — the engine's game-directory root inside the built tree); (4) its shmid was not in the run-start listing. It ran every 60 s during the wave, logging every pass (per selected segment: shmid, key, cpid, lpid, nattch, create / last-attach / last-change times). **It deletes nothing** — the only deletions in this run are the G8 sweep's, after the wave, with the selector already stopped.

**Format note (from the live box):** this util-linux prints an `owner` column in the `-p` and `-t` listings and times as `Oct 22 18:54:40` (no weekday/year). The parser takes cpid/lpid as the last two `-p` fields and matches times with a pattern covering both forms; the values in §4 are as logged.

---

## 2. Wave 1 — seeds 3007–3010 (18:54:29 → 19:15:58 EDT games; sweep and close-out to 19:16:29)

### 2.1 Per-game records

Wall from the driver row's `secs`; contested / thin-prior / errors / aborts aggregated from that game's `search_stats.jsonl` (contested rows only; `errors` is the stat rows' error total, `aborts` the `abort_reasons.abort` total). Every row: `connect_failed = 0`, `seat_mismatch_errors = 0`, `child_fallbacks = 0` (stat rows), and `children_found == children_cleaned` in the driver.

| Seed | Seat | Game id | Wall (s) | Turns | Decisions | Outcome | Contested | thin_prior | errors | aborts |
|---|---|---|---|---|---|---|---|---|---|---|
| **3007** | 1 | 273635760 | 145.0 | **62** | 1,159 | **CAPPED — `cap_reason "turns"`, draw, 40–40 life** | 2 | 1 | 40 | 17 |
| 3008 | 1 | 665155746 | 665.3 | 32 | 701 | decided (winner 2) | 34 | 2 | 138 | 105 |
| 3009 | 2 | 186833908 | 644.5 | 31 | 626 | decided (winner 2) | 21 | 6 | 174 | 32 |
| 3010 | 2 | 304005370 | **1,289.8** | 43 | 869 | decided (winner 1) | 49 | 1 | 232 | 211 |
| | | **wave** | | | 3,355 | 1 capped, 3 decided | **106** | **10 (9.4%)** | **584** | **365** |

**The stop rule fired:** seed 3007 reached trigger 62 (capped at exactly 62 turns, both players still at 40 life — a game that never engaged; it was also the wave's *fastest* game at 145.0 s, with only 2 contested decisions). Waves 2–4 were not run. One sample fact, stated as such: in this wave the timeout's binding game is not the capped one but the long decided game (seed 3010).

Pooled with the original probe (20 thin-prior of 75 contested), the two probes' thin-prior rate is 30/181 = 16.6%; this wave alone reads 9.4%.

### 2.2 Segment accounting

Wave start **0** → pre-sweep **585** (rise **+585**) → G8 sweep (585 stale removed, 0 attached kept) → **0**; final count after server shutdown 0. The rise decomposes exactly (§4(iv)): **584** leaked child segments — equal, to the segment, to the wave's 584 stat-row errors — plus **1** parent segment (seed 3010's gamestate segment, rule-3-excluded). Per-game error counts (40/138/174/232) are the leak's per-game shape: ~146 segments per teacher game on average this wave, against ~178 in the original probe.

### 2.3 Corrections to the interim checkpoint (the §0 note, enumerated)

The discarded interim account said: walls 1,092.2 / 427.2 / 984.1 / 510.7 s; all four games decided, none capped, maximum 47 turns; segment rise +710; 16 selector passes and 5,344 selections; contested 77 with thin-prior 10 (13.0%); stat aggregates for seed 3010 of 56 rows / 20 contested / 179 errors / 158 aborts; and a game-id file missing one of the four ids. The disk says, respectively: walls **145.0 / 665.3 / 644.5 / 1,289.8**; seed 3007 **capped at the trigger** and the probe stopped; rise **+585**; **23 passes and 9,289 selections**; contested **106**, thin-prior **10 (9.4%)**; seed 3010's stat file holds **133 rows / 49 contested / 232 errors / 211 aborts**; and the wave's `GATE_GAME_IDS_FILE` contains **all four ids** (273635760, 665155746, 186833908, 304005370 — the set registered in §5, each also named by its game's stat rows and its driver row's `gamename`). The pre-flight section of the interim account was written from pre-run calls and stands as written in §0.

---

## 3. Waves 2–4 — not run

The registered stop rule (§0) ended the probe at the end of wave 1. Seeds 3011–3022 were never played, no further ids exist, and the timeout in §6 is computed over all 8 probe games as the reply's formula requires (the original 4 + this wave's 4).

---

## 4. The (C) tests

### (i) cpid/lpid populate, and PHP's shmop updates lpid — shown empirically

`ipcs -m -p` reports creator and last-op pids for these segments, and the selector's log shows them populated on **9,289 of 9,289** SELECT lines (no line lacks a nonzero cpid/lpid pair). The segments' creators are PHP 8.5.4 `shmop` children (the only segment creators in the run), and their `lpid` names the *last* process to attach/detach — for leaked children, the child itself: `cpid == lpid` on the example below and throughout the leaked population. **Example (one segment across two passes, 21 passes apart):** shmid `545914886`, key 338552158 — pass 2 (18:55:29): `cpid=794259 lpid=794259 nattch=0 ctime="Oct 22 18:54:40" atime="Oct 22 18:54:51"`; pass 23 (the final pass): every field **identical**. A dead child's segment, created 18:54:40, last attached 18:54:51, never touched again — the kernel attribution (C) relies on, observed directly. This is the empirical showing the reply's §2(i) allows in place of quoted `shm_lprid` semantics.

### (ii) The dry run

The selector ran for the whole wave: **23 passes** at 60 s intervals, **9,289 SELECT lines**, **584 distinct shmids** selected. It deleted nothing; the wave's only deletions were the closing G8 sweep's (585 `ipcrm`s, after the selector had stopped), under the (B) containment the reply registered for the probe.

### (iii) False-positive test — PASS (zero instances)

Three checks over the log and the pre-sweep listing (the last observation of every surviving segment):
- **Intra-log:** for every shmid, across its selections in pass order, no later selection shows a later last-attach time, a later last-change time, or a different lpid than an earlier one — **0 violations** in 584 shmids / 9,289 observations.
- **Pre-sweep extension:** treating the pre-sweep `ipcs -m -p`/`-t` listing as the final observation, the same three comparisons against each shmid's last selection — **0 violations**.
- **Key collision:** no selected segment's key ever matches the key set `{n, n+1,000,000}` of the Games/ directories present at pre-sweep — **0 matches**.

No segment the selector would have deleted was ever touched again by anyone. On this evidence the selector's errors go only the safe way, as designed.

### (iv) Coverage test — PASS (exact, zero unexplained)

At quiescence, pre-sweep, the wave's residue was **585 segments**. Accounting:
- **584** are in the selector's cumulative selected set;
- **1** is excluded by rule 3 alone: shmid `546865457`, key **305005370** = game 304005370 + 1,000,000 — the **gamestate segment of seed 3010's parent game**, whose directory still exists under `Games/` (a KEEP_GAME parent). Its cpid/lpid are both 794176, the parent's own (dead) process. This is the only parent segment surviving at pre-sweep — the other three parents' segments were already gone (their end-of-game cleanup ran) — so the per-game parent count for this wave is: **one segment, one game (3010)**;
- **0** in both sets; **0 unexplained**.

Cross-checks that close the accounting: the selector's selected-union (584) equals the wave's stat-row error total (584) exactly — one leaked segment per errored child, the identity the launch package inferred from the aggregate (+712 ≈ 711 + parent) now verified per segment; and every selected shmid survived to the pre-sweep listing (selected-but-not-in-residue = 0), so nothing the selector picked was reclaimed early by any other path.

**Verdict for §2's sequence: tests (ii), (iii) and (iv) hold, and (i) is shown.** (C) therefore returns as code for review — the selector as the fleet runner's periodic sweep, with its hashes — and (A) is not engaged.

---

## 5. Registration (quarantine)

Backup first (`registry-vault/do_not_train_registry.bak-20261022-xprobe-pre.json`, the 4,975 state at `fdbc66bd…`), then the bespoke merge in the first probe's style (the ids file's form gives no chunk token; the tool's `gate:<chunk>` tags do not apply):

- **Games** (tag `gravy_fleet_probe_eval`): 273635760, 665155746, 186833908, 304005370 — **4**
- **Snapshots** (tag `gravy_fleet_probe_snap`): `304005370_t1`, `304005370_t2` — **2** (only seed 3010's game produced a snapshot index; the other three games wrote none)

Zero collisions (asserted at merge). Registry: **4,975 → 4,981 games**, sha256 **`d5cfcf79e8562ff5bfaf2c3f382769fe34c8cde502428c89448fb222108d2f7e`** (`n_games` and map length agree); vault copy refreshed (`registry-vault/do_not_train_registry-20261022-xprobe.json`, hash identical to live).

---

## 6. GATE_TIMEOUT, the wall estimate, closing

**GATE_TIMEOUT = max(700, ⌈3 × slowest⌉) over all 8 probe games** (row `secs`; original probe from fleet-alignment §3.2): walls 356.8, 497.1, 582.1, 1,103.4 (seeds 3003–3006) and 145.0, 665.3, 644.5, **1,289.8** (seeds 3007–3010). Slowest = 1,289.8 s → **GATE_TIMEOUT = ⌈3 × 1,289.8⌉ = 3,870 s**. This is the value the stage-5 launch manifest records.

**Fleet wall estimate, redone from all 8 games (the §V method of the alignment):** mean wall 660.5 s, median 613.3 s; one chunk ≈ 100 teacher games → **≈ 17.0 h at the median, ≈ 18.3 h at the mean**; plan on **~17–18.5 hours**, plus 3,870 s per teacher timeout if any occur. An estimate from eight games, for planning; not a registered number.

**Closing.** The probe did its three jobs: the timeout now rests on a sample that contains the trigger population (3,870 s); the leak is re-measured (+585 for 4 games, one segment per errored child, verified per segment); and (C) passed its field tests — so the next package carries (C) as code for approval, alongside the revised pre-gate runner (reply §5), and the pre-gate then launches on Joe's go. The probe is not the pre-gate, and nothing here launches either of them.

*Builder: Muse (for Joe Slattery), 2026-10-22. Run records on the box at `/tmp/xprobe/` (supervisor log, per-game driver rows and logs, selector log, per-wave `ipcs` listings, sweep evidence).*
