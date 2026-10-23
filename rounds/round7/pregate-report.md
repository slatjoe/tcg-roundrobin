# Round 7 — K3 pre-gate report

**Parent:** e4911b2e1949993231d5e358bf4115cda7f58bb2 (verified at `refs/heads/main` before writing). **Launched sha (Claude's confirmation):** a6d8442291f6d53aefcdf58daf1c8860d0ed0731. **Launch manifest:** `pregate-launch.md` (the e4911b2e commit). **Joe's go:** 2026-10-22 ~20:22 EDT. This report answers claude-reply-a6d8442's pre-gate report requirements; every headline artifact is cited by path and sha256 (§8).

## 0. Verdict

**The pre-gate does NOT record a clean pass. The determinism read PASSES and the R16 control PASSES; the ghost read FAILS as parsed — all 20 units INVALID_ASSERT — for one documented reason that is not a trace divergence.**

- Determinism: `PARSE-PASS` — 10/10 rows IDENTICAL, within-row hits 0, every column ok (§2).
- R16 seat-crossed raw control: `RAW-CONTROL: PASS` — 10/10 seeds differ across seats (§3).
- Ghost vs raw, both seats: on every trace-level criterion the ghost was exact — within-row hits **0**, outcomes equal, modes ok, seat ok, on all 20 units; the teacher's pick equals the prior argmax on **all 1,917 teacher rows**. The sole failing column is **assert ok**, driven by the ghost manifests' `assert_ok: false`, whose sole failing check is `ghost_flag_on_all_rollouts`, whose sole cause is the **thin-prior fallback class**: 133 contested decisions (59 seat 1, 74 seat 2) whose searches never reached the 20-finished-world floor took the `thin_prior` fallback in search.php, which logs its stat row and returns **before** the line that stamps `ghost = 1` — so those rows carry no ghost stamp by construction (§4). There is no search output on a thin-prior decision to stamp: the pick is the prior's, which is also what the ghost plays and what raw played.
- **K5 disposition: none.** No unit presents the K5 class (the pick-null abort-marker / DUP_SEQ class): the seq column is `None` on all 20 rows and no abort-marker disposition arises. The thin-prior class is not the K5 class, and no registered reclassification covers it.
- The disposition of the ghost read is therefore Claude's ruling on this record: the instruments record INVALID_ASSERT × 20 with the mechanism in §4; the trace facts the pre-gate exists to establish are recorded alongside it. **The fleet does not launch from this report** — it follows Claude's ruling and Joe's own go, under the ef34219 §4 launch condition.

The run itself completed: `GRAVY-PREGATE-DONE`, no runner stop fired (no pin failure, no parser stop on the determinism read, no fallbacks stop, no headroom abort, no non-zero driver exit — 5 × `PAIRED-DRIVER-DONE`, 50/50 game lines `cf=0`).

## 1. Launch record

Deployment (staging tree → `/tmp/gravytree` root, each hash verified on the box after copy):

| File | sha256 |
|---|---|
| `run_gravy_pregate.sh` | `d519beb126d6c919e989a5df946c97d2c574cd7dcba5cc3d26b8a44cef8f26a5` |
| `shm_sweep.py` | `98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33` |
| `parse_r3_pair.py` | `ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1` |
| `gate_ipcs_cleanup.sh` (round-3 committed copy) | `338183e255acfa1b8ec23fd73511e55e291b8af64686ddaf84e7ba1779e3162e` |

Pre-launch tree state, verified on the box: `paired_driver.py` `0a6b7a85…`, `gate_raw_retry.py` `c3fb227e…`, `search.php` `8f6b35da…`, `featurize.php` `f81193e0…`, `rl/search_server.py` `ab85fa1b…`, checkpoint `ckpt_v10.pt` `44f1e5d7…` at its home path; registry at 4,981 / `d5cfcf79…`; **SHM 0 segments; no game processes**. The runner's own nine-pin guard then re-verified every pin in-tree before the first arm.

**Attempt 1 (disclosed):** launched 20:23:51 EDT without `PREGATE_SWEEP` in the environment; the runner refused at its sec.5.2 check before any sweep, server or game (`ABORT: PREGATE_SWEEP=1 is required`). Nothing ran; the registry and SHM were untouched; the log is preserved at `/tmp/pregate/pregate_attempt1_abort.log` (§8). The manifest's "(forced inside the runner regardless)" wording is the runner's enforcement-by-refusal: the approved launch configuration (claude-reply-a6d8442) supplies the variable, and attempt 2 is that configuration.

**Attempt 2 (the run of record):** launched **2026-10-22T20:24:22-04:00** under setsid (runner pid 816394), env `GATE_TIMEOUT=3870`, `PREGATE_SWEEP=1`, `GRAVY_MODEL=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt`; output in `/tmp/ggate` (the runner's registered default), runner log at `/tmp/pregate/pregate_run.log`. Completed **23:31:26 EDT** — wall clock **3 h 07 m**. Arm order as registered: G8 start sweep → ghost s1 → G8 → ghost s2 → G8 → raw s1 → raw s2 → raw2 s1 → determinism read → R16 control → ghost reads → fallbacks check → registry merge.

## 2. Determinism (seat-1 raw vs its own re-run)

Parser output, quoted from `/tmp/ggate/pregate_pair_determinism.parse.txt`:

```
PARSE-PASS: 10 rows, every row IDENTICAL with within-row hits 0, outcome equal True, modes ok True, seat ok True, assert ok True
```

The table (`pregate_pair_determinism.txt`): seeds 8501–8510, every row `IDENTICAL | 0 | None | True | True | True | True`. The runner's hard stop on a parse failure did not fire.

## 3. R16 seat-crossed raw control

From `/tmp/ggate/pregate_raw_control.txt`:

```
raw-control: 10/10 seeds differ (fields: winner, turns, decisions, p1life, p2life, gamestate_norm_sha, gamelog_sha)
differing seeds: [8501, 8502, 8503, 8504, 8505, 8506, 8507, 8508, 8509, 8510]
RAW-CONTROL: PASS
```

## 4. The ghost read

Both tables (`pregate_pair_ghost_s1.txt`, `pregate_pair_ghost_s2.txt` — byte-identical content) record, for every seed 8501–8510 at both seats:

```
| seed | pair | verdict | within-row hits | seq | outcome equal | modes ok | seat ok | assert ok |
| 85xx | ghost vs raw | INVALID_ASSERT | 0 | None | True | True | True | False |
```

The parser's record (`pregate_pair_ghost_s1.parse.txt`, s2 identical) is, per seed, exactly two failures — `verdict INVALID_ASSERT (want IDENTICAL)` and `assert ok False (want True)` — and no other failure on any row: hits, outcome, modes and seat all pass on all 20 units.

### 4.1 Where the assert comes from

`r3_pair.py` takes the assert column from the two arms' driver manifests: `assert_ok` must hold on both sides. The raw manifests record `assert_ok: true`. Both ghost manifests record `assert_ok: false`, with checks:

| check | ghost s1 | ghost s2 |
|---|---|---|
| `pick_eq_prior_all_teacher` | true | true |
| `ghost_flag_on_all_rollouts` | **false** | **false** |
| `rollouts_present` | true | true |
| `trace_rules_all_ghost_prior` | true | true |
| `trace_teacher_pick_is_prior_argmax` | true | true |

The driver computes the failing check as `all(r.get("ghost") == 1 for r in rollout_rows)` over the arm's `search_stats.jsonl` (paired_driver.py:149–150).

### 4.2 The unstamped rows are exactly the thin-prior fallbacks

Counted from the arms' own stat files (`pregate_ghost_s{1,2}_log/search_stats.jsonl`):

| | teacher rows | rollout rows | ghost-stamped | unstamped | unstamped share |
|---|---|---|---|---|---|
| seat 1 | 861 | 224 | 165 | **59** | 26.3% |
| seat 2 | 1,056 | 272 | 198 | **74** | 27.2% |

Every unstamped row — 59/59 and 74/74 — carries `fallback: "thin_prior"` and `errors > 0`, and none carries any ghost-analysis field. The stamped rows carry the full ghost block (`ghost`, `ghost_would_pick`, `ghost_would_overturn`, `priors`, `mean_diff`, `se_diff`, `abort_by_cand`). Pooled pregate thin-prior rate: **133/496 = 26.8%** of contested rollout decisions (the two probes pooled 30/181 = 16.6% on seeds 3003–3010; the pregate population is seeds 8501–8510). The unstamped rows' searches were not idle: their finished-world counts run 15–22 per candidate and their mean wall is ~35–38 s against ~16–18 s for completed searches — they burned the candidate deadlines and still fell under the floor for the prior pick.

### 4.3 The code path (search.php, K2 pin `8f6b35da…`)

The stat row `$base` is assembled at search.php:993–999. At :1000–1005:

```php
if (($means[$priorPick] ?? null) === null || count($outcomes[$priorPick]) < 20) {
  $base["fallback"] = "thin_prior";
  $base["pick"] = $priorPick;
  SimSearch_LogStat($base);
  return $priorPick;
}
```

Only a search that clears the floor reaches the full-assembly block, where at :1029–1036 the ghost stamp is set — `$base["ghost"] = 1; $base["ghost_would_pick"] = $pick; …; $pick = $priorPick;` — under `getenv("TEACHER_GHOST")`. A thin-prior row therefore cannot carry the stamp: the function has already returned. The manifest check's premise — every rollout row is ghost-stamped — does not hold for the fallback class, in either seat, on any seed whose games contain a thin-prior decision (all 20 units contain at least one).

### 4.4 What the ghost property itself did

The pre-gate's ghost question is whether running the full teacher machinery while forcing the prior's pick leaves the live game action-identical to raw. On this run: **yes, on every measurable trace criterion** — within-row hits 0 and outcomes equal on 20/20 units; `pick_eq_prior_all_teacher` true over all 1,917 teacher rows (thin-prior rows play the prior by construction; completed-search rows by the ghost force); trace rules all `ghost_prior` (861/861, 1,056/1,056); the determinism floor underneath it (§2) is exact. The INVALID_ASSERT verdict records the manifest bookkeeping failure of §4.1–4.3, not a divergence: no unit diverged.

## 5. Server evidence

Both servers loaded the selected checkpoint (from `/tmp/ggate/pregate_server_loads.txt`, quoted):

```
search_server: search model loaded (/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt) on cuda
search_server: search model loaded (/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt) on cuda
```

Fallbacks: **0 everywhere** — no line with `fallbacks=[1-9]` exists in either server log (250 status lines, all `fallbacks=0`, `seat_mismatch=0`); all 50 driver game lines report `cf=0` (no connect failures); the runner's fallbacks stop did not fire. Production server hash unchanged across the run (`pregate_prod_hash.txt`): `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4` before and after.

## 6. Containment

The (C) sweeper ran LIVE for the whole run (188 passes, 60 s interval, `/tmp/ggate/pregate_shm_sweep.log`): **selected 5,114 · deleted 5,114 (every DELETE → OK) · failed 0 · unattributed 0**. The fail-safe fix's counter never moved: no segment lacked a pid row in any pass.

G8 sweeps (segments, from the sweep listings): start **0 → 0**; after ghost_s1 **11 → 0**; after ghost_s2 **24 → 0**. Headroom checks before arms (true segment counts, `pregate_ipcs.txt`): ghost_s1 0, ghost_s2 0, raw_s1 0, raw_s2 10, raw2_s1 20 — the 2,800 abort never approached. Closing state: the end listing (`pregate_ipcs_end.txt`) holds **30 segments**, and the sweeper's final pass (total=30, selected=0) kept all 30 under its rules (Games/ directories present) — the raw arms' parent records, left for the fleet's §4 pre-launch G8 sweep as registered.

## 7. Registry merge

From `/tmp/ggate/pregate_registry_merge.txt`: **added game ids: 50 · added snapshot ids: 0** (no arm produces snapshots under this runner, §5.4 of the runner header). Registry: **4,981 → 5,031 games**, new sha256 **`71cacfb0bfc190f34b4c252e43d515236e65430bcc761a248d1f82e0c519cd5d`**. Verified independently against the registry file: all 50 ids from `pregate_game_ids.txt` are present, **all under the tag `gate:gate`** (the tool's chunk fallback, disclosed in the runner header). Per arm: ghost 20 ids (10 per seat), raw 20, raw2 10 — 50 distinct games, no collisions reported by the tool. Vault backup and post-run copies were written by the runner before/after the merge.

## 8. Artifact index (path · sha256)

Run record:
- `/tmp/pregate/pregate_run.log` · `e7a7a15f060f5753b20099cc84f57c09babadc9c999b617734335aa433f136f7`
- `/tmp/pregate/pregate_attempt1_abort.log` · `148dead5d77a5c9c29552a9ca7abd17db79810637b22e4ef5e0655befb84638a`

Rows and manifests (`/tmp/ggate/`):
- `pregate_ghost_s1.jsonl` · `f058146eca6b9e61fa79bb6ca273bd61e2018c49d1e66724d08e1c0f61e0986e`
- `pregate_ghost_s2.jsonl` · `79c7a72a373a88b34d0dc26e9341721180ba1b32db22e82ddf302cdba4f9b6ff`
- `pregate_raw_s1.jsonl` · `9686dd6808692c2823504357d5a151a1498d935139aebb30772b1b471d4a1164`
- `pregate_raw_s2.jsonl` · `c18e84c727a93570efb740772f3ccbc15b28e1dbe0226d6a1272a2e174d4c70a`
- `pregate_raw2_s1.jsonl` · `99690ead1436a34bd2f12fc4b37676fb403785abecd93ed7f0d5cba6e851a1f3`
- `pregate_ghost_s1.jsonl.manifest.json` · `a89539d2302279d77fcd8fae0dd9046153f16fb4245d1b59ab6692b1f0739015`
- `pregate_ghost_s2.jsonl.manifest.json` · `49b13bcbd617942ed0809e16cc677426056ae4f26eb05d0eca9eaa77c58024b3`
- `pregate_raw_s1.jsonl.manifest.json` · `d6b8e8d69c6419ef2d02fde626fa16841b2d6408c1e1205cc5f0d9d06ab8cbcf`

Reads:
- `pregate_pair_determinism.txt` · `122c00f8acf29ffbfb4043883ed6cc222e60a729b5b76ebe1b4a913f1d82a27a`
- `pregate_pair_determinism.parse.txt` · `533893e796ee8a03d19dc3ab21f08556044dc3d6b2d634c71c2b240abd863523`
- `pregate_pair_ghost_s1.txt` · `c961f6839d10d08e7e025af84a7efe8901202ac50fa6b0192dab263fc8479204`
- `pregate_pair_ghost_s1.parse.txt` · `dae02a3bb5bfbe2d0259b57ff13552dd4e599e0216da572aca8b0d2d66d74da9`
- `pregate_pair_ghost_s2.txt` · `c961f6839d10d08e7e025af84a7efe8901202ac50fa6b0192dab263fc8479204` (byte-identical to s1)
- `pregate_pair_ghost_s2.parse.txt` · `dae02a3bb5bfbe2d0259b57ff13552dd4e599e0216da572aca8b0d2d66d74da9` (byte-identical to s1)
- `pregate_raw_control.txt` · `587315bf0c521d28349b0f49f2a784026f0b134b2dfa4ef7763e64091a97d18c`

Stat files (the §4 counts' source):
- `pregate_ghost_s1_log/search_stats.jsonl` · `57f06d103afee4213c42b0b323716420e243e3d115b450f319d020d7cac59167`
- `pregate_ghost_s2_log/search_stats.jsonl` · `053c7e8de4b6f1cdd4d28aa9b7081db393a436b9d3a249b9b227e3460d7c67db`

Servers, containment, registry:
- `pregate_server_s1.log` · `5ed8b206a267c0b88ee5ee7a1edee03283658b35478c88a850536f1db9ce52d0`
- `pregate_server_s2.log` · `ce00f47babca1812de4cc672d25d0e458086079f7075bf80305944f3b3fe0184`
- `pregate_server_loads.txt` · `537e8e2709d92818cbd2aa9a42e7c0b8d008ab753e8c654a8489331cee404d14`
- `pregate_shm_sweep.log` · `a54111c2b9e482c92067818ed717f9c4b20eb557e92d80a20639fecd6ee02d5d`
- `pregate_ipcs.txt` · `ab271092d26a6dbe0de8de34234444c1c533100e9f51aa06b675cc15293f9fe1`
- `pregate_ipcs_start.txt` · `a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8`
- `pregate_ipcs_runstart.txt` · `a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8` (same listing state as start: 0 segments)
- `pregate_ipcs_end.txt` · `079b988330535a941c2ec6c39e8eb3945d7269737bd9e022177e88f9ffb4cf6c`
- `pregate_registry_merge.txt` · `bd74e3fcf32b2389ed86c00347a0272af98814435ec7737a5420521bcbe67b18`
- `pregate_game_ids.txt` · `9fc32bedfac1b5d67e4b9adec1a4b26b57271d26547f5d808c204e4636d8b1e0`
- `pregate_prod_hash.txt` · `67762ab8edd1215b8827348a422c1ba7cfc65ec0507ab184de79b6d79e789524`
- `/tmp/harvest/do_not_train_registry.json` (after) · `71cacfb0bfc190f34b4c252e43d515236e65430bcc761a248d1f82e0c519cd5d`

## 9. Joe's spot-check (requested before Claude rules)

On the box:

```
cat /tmp/ggate/pregate_pair_determinism.parse.txt
```
→ the `PARSE-PASS` line of §2.

```
sha256sum /tmp/harvest/do_not_train_registry.json
```
→ `71cacfb0bfc190f34b4c252e43d515236e65430bcc761a248d1f82e0c519cd5d`

And for the ghost verdict itself:

```
grep -c INVALID_ASSERT /tmp/ggate/pregate_pair_ghost_s1.txt
```
→ **10** (and the same in the s2 table) — the count this report's §4 explains.
