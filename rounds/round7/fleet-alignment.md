# Round 7 — fleet-alignment registration (stage-5 caps, scoring, timeout; the stage 4–5 scope sweep)

**Parent:** c59a133dadc7d46bb6f7349b7f73bfa12fa027f5 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-01250ac.md` §4 (the blocking finding and its five required points) and §3 (the opponent-split request, Appendix A). Context: `rounds/round7/stage3-report.md` (stage 3 accepted, `ckpt_v10.pt` selected) and `rounds/round7/followup-k1-k3-fix.md` §3 (the registered K3 pre-gate).
**Status: DRAFT for review. Nothing launches on this registration.** The K3 pre-gate, the teacher and the stage-5 fleet remain held until this registration is approved at its committed sha, and then launch only on Joe's per-stage go. The Gravy tree build (stage 4 (i)) is untouched by this registration and proceeds under ba4e9c97 on Joe's go. The only games played under this package are the four disclosed contention-probe games of §3.

**Package contents**

| File | Role |
|---|---|
| `fleet-alignment.md` | this registration: §1 caps, §2 scoring, §3 timeout + the probe as run, §4 the teacher's rollouts, §5 the scope sweep with open items, §6 what it does not do, Appendix A the opponent split |
| `code/paired_driver_gravy.py` | §1: the Gravy launch-copy driver (one-line diff on the stock driver), sha256 `0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae` |
| `code/analyze_gate_gravy.py` | §2: the fleet analysis with the non-win co-report added (primary byte-identical), sha256 `d468468eac58a8f192335886ccb54dca6d2d36d28682089b03dc036d825247db` |
| `code/run_gravy_gate.sh` | revised in place: the tree guard gains the driver + retry hash pins (§1.4), sha256 `0c458627b890cd933b793ecc79417ac55012cde74bb15f04cfad8a0e7a1343a5` (supersedes `2895c4a0…` in place; that version is preserved in its commit) |
| `code/opponent_split_rollout.py` | Appendix A: the read-only split analysis, sha256 `5809214cec9947032c4814dc61812b79b68949db8df68ae548dde304ade58dfb` |

---

## 1. Caps — the driver on parameter 87 / trigger 62, both arms, the retry, the pre-gate (reply §4, point 1)

### 1.1 The defect, from the code

The fleet and the pre-gate invoke `paired_driver.py` **from the tree** (`run_gravy_gate.sh` does `cd $TREE` and calls `$PY paired_driver.py`; the K3 invocations of followup-k1-k3-fix §3 name the tree's copy the same way). The stock driver is one canonical file — `rounds/round3/code/paired_driver.py`, sha256 `1e312629c9ebe30e97e0480c1f9d5530e82eba3c1a9511b3a929bc6f2d92471d` — and the copies in `/tmp/otree` and `/tmp/gatetree_r4` hash identically to it, so the K2 tree build (otree → gravytree) would carry it unchanged. Its game environment is built at `paired_driver.py:229–234`:

```python
    env = dict(os.environ)
    env["TCG_POLICY_SOCK"] = a.sock
    env["TCG_LEARNER_SEAT"] = str(a.seat)
    env["TCG_MAX_TURNS"] = "60"        # :232
    env["TCG_MAX_DECISIONS"] = "3000"  # :233
    env["TCG_STUCK_LIMIT"] = "200"     # :234
```

These are unconditional assignments on top of the inherited environment: no caller-supplied value can soften them. The reader is the tree's `play_game.php` (otree sha256 `4ac2d62d…`): `$maxTurns = intval(getenv("TCG_MAX_TURNS") ?: 750)` at :332, `$capTrigger = $maxTurns - 25` at :336, `$decisionLimit = intval(getenv("TCG_MAX_DECISIONS") ?: 3000)` at :344, `$stuckLimit = intval(getenv("TCG_STUCK_LIMIT") ?: 200)` at :343. So the stock driver puts every fleet and pre-gate game on **parameter 60, trigger 35** — the instrument the calibration voided (claude-reply-01250ac §4). The registered Gravy instrument is **parameter 87, trigger 62, 3,000 decisions** (respecified-gate-registration.md, as confirmed), with the stuck limit unchanged at 200.

### 1.2 The three mechanisms, and the recommendation

**(a) A Gravy launch copy of the driver with the value edited (RECOMMENDED).** `code/paired_driver_gravy.py` — the stock driver with exactly one line changed, :232 `"60"` → `"87"`. Diff in full:

```diff
@@ -229,7 +229,7 @@
     env = dict(os.environ)
     env["TCG_POLICY_SOCK"] = a.sock
     env["TCG_LEARNER_SEAT"] = str(a.seat)
-    env["TCG_MAX_TURNS"] = "60"
+    env["TCG_MAX_TURNS"] = "87"
     env["TCG_MAX_DECISIONS"] = "3000"
     env["TCG_STUCK_LIMIT"] = "200"
     env["TCG_SEARCH_LOG"] = a.logdir
```

22,122 B, sha256 `0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae` (built in staging from the committed stock copy; the byte deployed for the §3 probe was re-hashed on the box and matched). Decisions stay `"3000"` and stuck stays `"200"` — only the turn parameter moves, because only it was re-specified. Deployment: the stage-4 tree build places this copy as `/tmp/gravytree/paired_driver.py` (a file placement at build time, in place of the otree copy the K2 build would otherwise carry), and §1.4's guard refuses any other bytes at launch.

**(b) Env-driven values — rejected.** Making the driver read the cap from its environment is itself a code change (the current code overwrites the environment unconditionally), and the resulting fleet value would live in the launch shell rather than in any file a hash can pin. That is the shape of the failure this registration exists to close: a cap nobody could see in a reviewed artifact. A default-preserving test does not change where the effective value lives at launch.

**(c) A patch script — rejected.** A patcher's output still has to be hash-pinned before it means anything; the launch copy under (a) *is* the pinned output, and its one-line diff stays reviewable in the repo permanently instead of being regenerated at build time.

### 1.3 The raw retry — its caps from its code

`gate_raw_retry.py` (stock, sha256 `c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93` — the repo, otree and gatetree copies are identical) contains **no cap values of its own**: no `TCG_MAX_TURNS`, `TCG_MAX_DECISIONS` or `TCG_STUCK_LIMIT` appears anywhere in it. It finds the timeout rows in a raw arm's row file, removes them, and re-invokes the driver **from its own directory** — `HERE = os.path.dirname(os.path.abspath(__file__))` (:22), the command built as `os.path.join(HERE, "paired_driver.py")` (:57) — passing `env = dict(os.environ)` (:64), which the driver's hard-coded env block then overrides anyway. So the retry's caps are exactly the caps of the driver copy sitting beside it in the tree: placing the §1.2 launch copy at `/tmp/gravytree/paired_driver.py` covers the retry completely, with **no change to the retry file**. Its only number is a `--timeout` default of 700, which the runner always overrides with `$GATE_TIMEOUT`. §1.4 pins the retry's unchanged hash in the guard so "covered by the driver beside it" is verified, not assumed.

### 1.4 The pin — runner guard extension

`run_gravy_gate.sh` already pins the tree's `search.php` (`8f6b35da…`), `featurize.php` (`f81193e0…`) and `rl/search_server.py` (`ab85fa1b…`) through `expect_hash` before any server starts or any output is created. The revised runner (this package) adds, in the same block:

```bash
expect_hash "$TREE/paired_driver.py" \
  0a6b7a85c0123133c5ffcefbccd0c03bc53a8f3885ff04c30677799003fc63ae \
  "paired_driver.py (Gravy launch copy, fleet-alignment registration: TCG_MAX_TURNS=87, trigger 62)"
expect_hash "$TREE/gate_raw_retry.py" \
  c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93 \
  "gate_raw_retry.py (unchanged stock copy; caps live in the driver)"
```

plus a header bullet recording the caps substitution. The revised runner is 7,112 B, sha256 `0c458627b890cd933b793ecc79417ac55012cde74bb15f04cfad8a0e7a1343a5`; `bash -n` clean. A tree whose driver is the stock copy (or anything else) aborts the launch on the guard, before a game exists.

### 1.5 The K3 pre-gate runs through the same driver — stated explicitly

Yes — with one correction to how the pre-gate's status is stated. The pre-gate exists **as registered text only**: followup-k1-k3-fix §3 registers the ghost arm, the raw arm, the seat-1 **determinism check** (a second raw run at seat 1, paired IDENTICAL against the first), and the standing seat-crossed control, with the invocation forms written out there. **No committed runner implements any of it.** The revised `run_gravy_gate.sh` contains no pre-gate at all (grep-verified: no `pregate`, `ghost`, `8501` or `determinism` string appears in it — it starts the servers and goes straight to the fleet chunks), and no pregate script exists in `rounds/round7/code/`. So the determinism check is **registered, not armed**: when a pregate runner is written for the stage-4/launch package, it calls the same pinned launch-copy driver (`paired_driver.py --tree /tmp/gravytree`) for every one of those games, and their caps come from the same bytes as the fleet's — aligning the driver aligns the pre-gate, the fleet, and the retry in one move. Writing that runner is open item **O5** (§5); any scratch pregate script found on the box is not the registered instrument and must not be run as if it were. There is no second driver anywhere in the stage 4–5 path (§5).

---

## 2. Scoring — capped games in the primary Δ, the co-report, and L1/L2/L3/G3 (reply §4, point 2)

The fleet analysis is `analyze_gate.py` (stock sha256 `a5e2086677a69c6055a47de433ada1dfbf29f37e49264af6d4dab0e824277a6e`; the round-3 and round-4 copies and the otree copy are byte-identical).

### 2.1 The primary Δ already scores capped games at 0.5 — verified, no change

`score_arm` (analyze_gate.py:87–103): a wall-timeout row scores 0.0 (teacher) / 0.5 (raw) per the timeout rulings; **a capped row returns `0.5, {"capped": row.get("cap_reason")}` at :97–98**; a draw returns 0.5 (:100–101); otherwise win 1 / loss 0 by seat. The module docstring states it at :9–10: *"engine cap (capped row): 0.5 for that arm — caps are outcomes."* The Fai fleet never exercised the branch (nothing capped); the scoring was registered before it, and it is exactly the read the reply asks to register for Gravy. **Registered for stage 5: the primary paired Δ (teacher − raw, per unit (seed, seat), cluster-bootstrapped by seed) scores a capped game 0.5 for that arm.** A unit in which both arms cap contributes 0 to the Δ. **The Δ bands are unchanged** (`band_read`, :143–155): Δ ≥ +0.05 with CI lower bound > 0 converts; Δ > +0.20 impeaches before reading.

**Exactly which capped counts the stock output carries — one, and it is pooled.** The only capped figure `analyze_gate.py` prints is `n_capped` (:241–244): the count of scored **units** in which either arm's row is capped (the emit's wording is "capped games among scored units", but the counter increments once per unit, so a unit in which both arms capped counts once). There are **no per-arm capped counts anywhere in the tool** — the complete set of "capped" lines in the file is :10 (the docstring), :97–98 (the score branch) and :241–244 (this count); the stat-monitor section prints canary/overturn/abort figures, not cap counts. The paired-capped accounting the primary actually performs is fully stated by the branch order in `score_arm`: the cap test (:97) runs **before** the draw and winner tests (:100–103), so a capped row scores 0.5 for its arm whatever its `winner` field carries, and a both-capped unit contributes exactly 0 to the Δ. Whether the recorded rows ever carry `winner == seat` on a capped row is an empirical question about the data, asserted on the recorded rows in the verification record accompanying this registration (probe rows + the stage-3 rollout rows): see the builder note appended at §V.

### 2.2 The non-win Δ co-report — not in the stock tool; a stated, diffed change

The stock tool computes only the draw-scored blocks (pooled, seat 1, seat 2). No non-win variant exists in it. The change is `code/analyze_gate_gravy.py` (19,741 B, sha256 `d468468eac58a8f192335886ccb54dca6d2d36d28682089b03dc036d825247db`), built from the stock file with this diff and nothing else:

- a docstring paragraph recording the addition;
- `score_arm_nonwin(row, arm)` added beside `score_arm`: **identical in every branch except the cap branch, which returns 0.0** (draw-without-cap keeps 0.5; the timeout branches are unchanged — teacher timeout 0.0, raw timeout 0.5);
- the scoring loop additionally stores each unit's non-win scores (`tn`, `rn`, `dn`);
- `delta_block` gains key parameters (defaults = the primary's), and after the primary blocks a **CO-REPORT** section prints the pooled and per-seat paired Δ under non-win scoring with the same cluster bootstrap. **No band read attaches to the co-report**; the registered bands apply to the primary only.

**Verification (disclosed build test, synthetic records):** a 4-unit fixture (teacher win vs raw cap; teacher cap vs raw win; both cap; teacher loss vs raw cap) was run through both the stock tool and the patched copy. The patched copy's primary output is **byte-identical** to the stock tool's on the fixture (pooled Δ −0.1250, CI [−0.2500, +0.0000]); the co-report reproduces the hand-computed non-win values (pooled Δ +0.0000 with teacher 0.2500 / raw 0.2500; seat 1 +0.5000; seat 2 −0.5000). The fleet analysis runs the patched copy; its hash is recorded in the launch manifest.

### 2.3 L1, L2, L3, G3 — how capped games enter each

- **L1** (`l1_check.py`, sha256 `956923d0…`): the leak check reads **teacher stat rows** — contested decisions' rollout means and `se_diff` — and counts unanimity. Game outcomes never enter it; a capped fleet game contributes its contested decisions exactly as a decided game does. No cap handling exists or is needed. (Its one Gravy problem is a hard-coded input path — open item **O2**, §5.)
- **L2** (`probe_swap20.php`, sha256 `6993ece4…`): the hidden-card swap test works on harvested snapshots through the production server (the R12 rule: L-runs use the production server, sha256 `81ef2cdb…`, which serves any v3 checkpoint — the vocab travels inside it, §3.2). It plays no games; caps do not arise. No change.
- **L3** (`analyze_l3.py`, sha256 `16017ffa…`): scores **fresh-world rollout outcomes** — `score = (outcome + 1) / 2` over worlds whose results carry `finished` — so there is no capped-game concept at its input at all: worlds that end without a winner (the §4 guard/stuck exits) are counted in its integrity block as `unfinished` and excluded, never scored 0.5 or 0. A snapshot harvested from a fleet game that later capped is attributed by its fresh worlds' terminal outcomes, identically to the Fai construction. One hard-coded Fai constant does need a Gravy value — `DELTA = 0.2525` at :31 (with `TEACHER_GAMES = 400` at :32, coincidentally right for Gravy: 200 seeds × 2 seats of teacher games). §5 **O3** registers the substitution.
- **G3** (`gate_first_divergence.py`, sha256 `9aaca155…`, with `classify_divergence.py`, `1518427b…`): neither file contains any reference to capped games or draws (grep-verified). G3 classifies **trace divergences**; its outcome fields (`gate_first_divergence.py`, `OUTCOME_FIELDS`: winner, turns, decisions, p1life, p2life, gamestate_norm_sha) make a cap-driven outcome difference an ordinary differing unit. A capped game enters G3 exactly as a decided game — as a trace pair whose first divergence must be an overturn. No change.

---

## 3. Timeout — the formula stands; the probe re-run at the new caps (reply §4, point 3)

### 3.1 The registered form

`GATE_TIMEOUT = max(700, 3 × slowest of 4 concurrent teacher probe games)` — the form carried in `run_gravy_gate.sh`'s header (the Fai gate's 886 = ⌈3 × 295.3⌉). The runner takes the value as a required environment input; nothing is inherited from Fai.

### 3.2 The probe as run (disclosed build test, 2026-10-22)

**Tree:** `/tmp/otree` — stated as the limitation it is. `/tmp/gravytree` does not exist yet (its build is stage 4 (i), separately approved), and otree is its registered source (K2): the probe exercised `search.php` sha256 `8f6b35da…` and `rl/search_server.py` `ab85fa1b…`, both verified by hash on the box at run time, and both are files the K2 build copies unchanged. The driver was §1's launch copy itself (deployed to `/tmp/fleetprobe/paired_driver_gravy.py`; on-box hash re-verified `0a6b7a85…`), so **the probe ran at the new caps — parameter 87 / trigger 62, 3,000 decisions, stuck 200**. **Model:** the fleet's, `ckpt_v10.pt` (sha256 `44f1e5d7…`), served by the tree's patched servers (`SEARCH_MODEL`); the vocab travels inside the v3 checkpoint (`rl/search_server.py:65–68`, `load_v3` reads `ckpt["vocab"]`), so the tree server serves the 380-card Gravy model directly — both servers' startup lines (`search model loaded (…/ckpt_v10.pt)`) were captured, and both servers' stats lines report `fallbacks=0 seat_mismatch=0`. **Form:** 4 teacher games **concurrently**, seeds **3003–3006** (the probe series — outside the fleet's 8001–8200, the pre-gate's 8501–8510, and every earlier registered range), seats 1,1,2,2 over the two per-seat servers, mirror Gravy deck, fleet conditions (`TEACHER_SNAP_DIR`, `TCG_CLEAN_CHILDREN=1`, `GATE_GAME_IDS_FILE` set as the runner sets them). The driver's own per-game `--timeout` was 3,600 s so the instrument being measured could not cut the measurement.

**Results** (per-game wall from the driver rows' `secs`; invocation walls agree to the second):

| Seed | Seat | Wall (s) | Outcome | Turns | Decisions |
|---|---|---|---|---|---|
| 3004 | 1 | 356.8 | decided (winner 1) | 24 | 458 |
| 3003 | 1 | 497.1 | decided (winner 2) | 12 | 245 |
| 3006 | 2 | 582.1 | decided (winner 1) | 42 | 849 |
| 3005 | 2 | **1,103.4** | decided (winner 2) | 40 | 860 |

All four games **decided** — none reached the trigger (turns 12–42) and none capped; `connect_failed = 0` and `seat_mismatch_errors = 0` on every row; the driver manifests read `assert_ok = true` ×4; `children_found == children_cleaned` in every row (19/19, 32/32, 3/3, 4/4).

**GATE_TIMEOUT = max(700, ⌈3 × 1,103.4⌉) = 3,311 s.** This is the value the stage-5 launch manifest records for the pre-gate and the fleet. The fleet's peak teacher concurrency is the probe's (the runner's four chunks interleave teacher and raw per seat; at most four teacher games run at once), so the contention the probe measured is the contention the timeout insures against.

**Launch-time condition (registered):** the fleet launch manifest records the built gravytree's hashes against §1.4/§5's pins. If any file the probe exercised differs on the built tree from the probe's tree, this probe is void and re-runs on the built tree before the pre-gate, under the same formula.

### 3.3 What else the probe measured (report-only)

- **Decision walls:** 75 contested decisions across the 4 games; median 32.3 s, max 88.2 s — the §4 per-candidate deadline (180 s) never bound. Worlds finished per candidate: **17–23 of 25**; stat-row `errors` total **711**, of which **339** carry the recorded reason `abort` (SimSearchAbort); the rows do not decompose the remaining 372 further. `child_fallbacks = 0` throughout; `thin_prior` fallbacks **20 of 75** contested decisions (27%).
- **SHM:** `ipcs -m | wc -l` read **2,198** before the probe and **2,910** after (+712) — within one segment of the 711 errored children. The code paths agree: a child that exits through `SimSearchAbort` (or a determinization failure) writes its error and wipes its directory **without** `DeleteCache` (search.php, the `SimLabel_RunRollout` catch block and det-failure exits), so its SHMOP segment leaks; the finished-game and success paths do call `DeleteCache`. This is open item **O1** (§5).
- **Quarantine:** the probe's 4 game ids and 3 snapshot ids were registered eval-only (`gravy_fleet_probe_eval` / `gravy_fleet_probe_snap`) immediately after the run: registry **4,968 → 4,975**, sha256 `fdbc66bde5c5640a656df74cc742d7d269b2b35e68b6f84f148309586564f032`; backup `registry-vault/do_not_train_registry.bak-20261022-fleetprobe-pre.json`, refreshed vault copy `do_not_train_registry-20261022-fleetprobe.json`. Zero collisions.

---

## 4. The teacher's own rollouts — what bounds them (reply §4, point 4)

From `/tmp/otree/search.php`, sha256 `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` — the K2-pinned build the Gravy tree inherits.

**Which path the fleet's teacher takes.** The driver sets `TEACHER_MODE=1` for the teacher-family arms (`paired_driver.py:243`), and `Choose` then routes to `SimTeacher_Decide` → `SimTeacher_DecideInner` (search.php:828). Per contested decision: candidates are the top-3 priors plus any prior ≥ 0.10, capped at 4 (:883–892); **K = 25** determinized worlds per candidate (:928); each world is a forked child running `SimLabel_RunRollout` (:1370) with that candidate forced at the root and the **pair-va** continuation (the root player's later decisions by net argmax, the other seat by the v1 heuristic argmax — `SimLabel_ChildChoose`, :1310ff). The ghost arm runs this same machinery and then replaces the pick with the prior's (:1029).

**No turn cap and no decision cap bounds a rollout.** `search.php` contains no reference to `TCG_MAX_TURNS` or `TCG_MAX_DECISIONS` at all (grep-verified) — the game's caps live in `play_game.php`'s main loop, which a rollout child never runs. The bounds that do exist, all inside `SimLabel_RunRollout` and its parent:

1. **A drive-step guard:** `while (!IsGameOver() && $guard < 400)` (:1407) — at most 400 drive steps, each up to 20 `PuzzleFinishStep`s.
2. **A stuck detector in the same loop:** if the state hash is unchanged between consecutive drive steps, a counter climbs and the loop breaks at **> 60** (:1413–1414). A pass-forever loop whose state keeps changing — the turn counter advancing, cards cycling to the deck bottom — never trips it. For that population the 400-step guard is the binding bound.
3. **A hook budget:** `SimLabel_ChildChoose` / `SimLabel_ChildDQ` throw `SimSearchAbort` once the child's decision hooks exceed **4,000** (:1310, :1351).
4. **The parent's per-candidate deadline:** `SimTeacher_DecideInner` waits for each candidate's 25 children to a hard `$deadline = time() + 180` (:960), then SIGKILLs the stragglers and counts them as errors. Candidates are processed sequentially, so one contested decision's worst case is ≈ 4 × 180 s of waiting (the probe's actual maximum was 88.2 s).

**A rollout that enters a pass-forever state therefore burns its guard, not the game's clock:** up to 400 drive steps of engine work, inside the parent's 180 s-per-candidate deadline — and then it is **not scored**. `SimLabel_RunRollout` writes `finished = 0` for a guard/stuck exit (and an error for an abort), and `DecideInner` counts only results with `finished` set (:967ff) toward a candidate's mean and toward the prior candidate's ≥ 20-finished-worlds validity rule; below 20, the decision falls back as `thin_prior` and the prior pick plays. A stalling position thins the estimate; it does not poison it, and it cannot hang the game: every loop in the path is counted or deadlined. What remains as the fleet-level catches is what the reply named — a game whose positions stall the search decision after decision spends its wall against `GATE_TIMEOUT` (§3), and **teacher timeouts > 2% make the gate INCONCLUSIVE**; the canary stands as the other catch. The §3.3 probe numbers (17–23 finished worlds per candidate, 27% thin-prior) are this machinery's measured behavior on Gravy-length games under fleet contention.

**The other search path, for completeness:** when `TEACHER_MODE` is off, `Choose` falls to the ISMCTS root decider (search.php:1067ff; `ISMCTS_D` default 10, `ISMCTS_S` default 12 at :1068–1069). Its child (`SimSearch_RunChild`) has the same loop shape — guard 400 (:734), stuck > 60 (:740) — its parent deadline is 45 s (:1214), and its in-tree expansion is cut by the sim budget (hooks > 500, depth ≥ 24, or `currentTurn > rootTurn + 1` → leaf evaluation, :560–562). **No fleet arm runs it** (every fleet arm is a teacher-family arm); it is listed so the sweep's coverage of `search.php` is complete.

---

## 5. Scope sweep — every script in the stage 4–5 path (reply §4, point 5)

Method: the repo's rounds 3, 4 and 7 code and the otree top level were swept for `TCG_MAX_TURNS`, `TCG_MAX_DECISIONS`, `TCG_STUCK`, `TCG_MAX_STEPS`, `maxTurns`, `MAX_TURNS`, `MAX_DECISIONS`, and the path's scripts were read for inherited defaults. **The only writer of `TCG_MAX_TURNS` in the path is the driver; its only reader is `play_game.php`.**

| # | File (sha256) | Where | Caps / defaults | Source | Covered |
|---|---|---|---|---|---|
| 1 | `paired_driver.py` (`1e312629…`) | repo r3 code; tree copies identical | TURNS=60, DECISIONS=3000, STUCK=200, :232–234 | hard-coded | **§1 launch copy (`0a6b7a85…`) + guard pin** |
| 2 | `gate_raw_retry.py` (`c3fb227e…`) | repo r3 code; trees identical | none of its own; `--timeout` default 700 (runner overrides) | inherits the driver beside it (:22, :57) | **§1.3 — unchanged, guard-pinned** |
| 3 | `run_gravy_gate.sh` (`0c458627…`, this package) | repo r7 code | no caps; GATE_TIMEOUT required (§3: 3,311) | — | **carries the §1.4 guard** |
| 4 | contention probe (`run_fleetprobe.sh` + launch-copy driver) | box `/tmp/fleetprobe` | ran at 87 / 62 / 3000 via the launch copy | §1 copy | **executed (§3.2)** |
| 5 | `play_game.php` (`4ac2d62d…`) | tree (otree) | defaults: TURNS 750 (:332), trigger = param − 25 (:336), DECISIONS 3000 (:344), STUCK 200 (:343), MAX_STEPS 30000 (:331), FINISH_STEPS 20 (:353) | engine defaults, overridden by the driver's env | yes — the driver env is the path's only writer |
| 6 | `search.php` (`8f6b35da…`) | tree (otree), K2-pinned | no TCG caps; internal bounds §4 (guard 400, stuck 60, hooks 4,000 / 500, deadlines 180 s / 45 s, K=25) | hard-coded internal | stated in §4; no change |
| 7 | `rl/search_server.py` (`ab85fa1b…`) | tree, K2-pinned | no caps; serves the checkpoint's embedded vocab (:65) | — | n/a |
| 8 | `rl/eval.py` | sim root | stage-3 instruments only | — | **not in the stage 4–5 path** (no reference in the runner or the K3 invocations) |
| 9 | `analyze_gate.py` → `analyze_gate_gravy.py` (`a5e20866…` → `d468468e…`) | repo r4 code → r7 code | scoring only (§2) | — | **§2 patched copy** |
| 10 | `l1_check.py` (`956923d0…`) | repo r3/r4 code | no caps; **input glob hard-coded to `/tmp/gate_r4/…` (:4)** | hard-coded path | **OPEN O2** |
| 11 | `analyze_l3.py` (`16017ffa…`) | repo r3/r4 code | DELTA=0.2525 (:31), TEACHER_GAMES=400 (:32) | hard-coded constants | **OPEN O3** (§2.3) |
| 12 | `audit_overturns.py` | repo r3/r4 code | builds the L3 jobs from stat rows + snapshots; no caps | — | n/a |
| 13 | `meas_label_main.php` (`3109176b…`), `label_main.php` (`cdca9b8e…`) | tree (otree) | the L-run drivers; label config read in `play_game.php:421–424` (LABEL_W default 10 — L3 sets 50 by env; LABEL_CAP default 6) | env / defaults | n/a — runs on the production server per R12 |
| 14 | `probe_swap20.php` (`6993ece4…`) | repo r3/r4 code | L2; snapshot-level; no caps | — | n/a |
| 15 | `gate_first_divergence.py` (`9aaca155…`) + `classify_divergence.py` (`1518427b…`) | repo r3 code | G3; no caps, no capped-game handling (§2.3) | — | n/a |
| 16 | `r3_pair.py` (`13f95ebe…`) + `classify_divergence.py` | tree (otree) = repo | the pre-gate pairing instrument; outcome fields only | — | n/a |
| 17 | `count_canary.py` (`4a1bba05…`) | repo r3 code | stat-row coverage monitor; no caps | — | n/a |
| 18 | `register_gate_ids.py` (`5515705b…`) | repo r3 code | registry merge tool; no caps | — | n/a |
| 19 | `cleanup_cache.php` (`153f8b2c…`) | tree (otree) | the driver's DeleteCache helper; no caps | — | n/a |
| 20 | `gravy_ppo_launch.sh`, `run_regate.sh`, `run_formal_gate.sh`, `patch_trainer_launch.py` | repo r7 code | stage-3 instruments (eval caps; DECISIONS exports) | — | **not in the stage 4–5 path** |

**Open items (flagged, not passed over):**

- **O1 — SHM headroom at Gravy scale (from §3.3).** The probe's four teacher games leaked +712 segments (≈178 per game, tracking the errored-child count) because the abort/error exits in `SimLabel_RunRollout` skip `DeleteCache`. The count now stands at ~2,910 against the 3,600 operator stop and the 4,096 kernel limit: at the probe's rate, neither the pre-gate's ~40 machinery games nor the fleet's 400 teacher games fit in the remaining headroom. **Registered as launch conditions:** the standing pre-launch G8-style sweep runs immediately before the pre-gate (and the probe's residue is swept with it); `ipcs` is recorded at the pre-gate and per chunk as the runner already does; and the stage-5 launch package states the sweep plan between chunk waves for if the count approaches 3,600 mid-fleet — at the stop, the standing rule governs (a stopped fleet is INCONCLUSIVE, not partially readable). No code change is proposed here; whether the fleet's own rate matches the probe's is a launch-phase measurement, and the pre-gate's 40 games are the first read of it.
- **O2 — `l1_check.py`'s input glob** is hard-coded to `/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl` (:4). The stage-5 analysis deployment uses a copy with the glob pointed at `/tmp/ggate` (the runner's out dir; the file names inside keep the `gate_` form, so the pattern otherwise matches). A one-line deployment substitution; the deployed copy's hash is recorded in the analysis record. The committed tool is not edited.
- **O3 — `analyze_l3.py`'s DELTA** is the Fai constant 0.2525 (:31). The Gravy L3 run uses a deployment copy with DELTA set to the Gravy fleet's measured primary Δ (from §2's analysis), the substitution and the copy's hash recorded in the L3 run record — a launch-time artifact under the same mechanics as the K1 probe hash (the number needs no re-review; the mechanism is registered here). `TEACHER_GAMES = 400` stands as-is for Gravy.
- **O5 — no pregate runner exists (from §1.5).** The K3 pre-gate — ghost arm, raw arm, the seat-1 determinism check, the standing seat-crossed control — is registered text (followup-k1-k3-fix §3) with **no committed implementation**: the fleet runner contains no pre-gate, and `rounds/round7/code/` holds no pregate script. The stage-4/launch package must supply that runner as reviewed code (its invocations exactly as registered, through the §1 launch-copy driver, under the runner's hash pins extended to the pregate's own outputs), and the launch does not proceed on any scratch pregate script. (Verified at drafting: no pregate script exists on the box at all — a find over /tmp and the sim tree returns only the round-4 O-era `/tmp/o_stage/run_pregate.sh` and its log, which are a different, already-executed instrument.) Until that runner is reviewed, the determinism check is a registration, not a mechanism.
- **O4 — nothing further.** No other cap or cap-inheriting default was found in the path. `eval.py` is confirmed absent from it (row 8).

---

## 6. What this registration does NOT do

It launches nothing. The K3 pre-gate, the teacher and the stage-5 fleet wait for Claude's approval of this registration at its committed sha, and then for Joe's per-stage go. The only games played under it are the four disclosed probe games of §3. The tree build (stage 4 (i)) is independent of it and proceeds under ba4e9c97 on Joe's go alone.

---

## Appendix A — the rollout capped-share series split by opponent type (reply §3; report-only)

**Method.** `code/opponent_split_rollout.py` (sha256 `5809214c…`), run read-only on the stage-3 PPO tree (`rl_out/gravy_ppo_gravybc3`). The join is stage3-report §2's, unchanged: version acceptance timestamps from `trainer_v4.log`; each game's timestamp and opponent class from `traj_w*/games_meta.jsonl` (fields `game`, `learner_seat`, `opp`, `ts` — the field supports exactly three classes: **`self`** = learner-vs-learner, **`heuristic`**, **`bc`** = the BC anchor); the capped flag from `games_w*.jsonl` joined on game id; games binned to the version whose acceptance interval contains their `ts`, then into the report's 25-version bands. **Verification:** the split's band totals reproduce the report's pooled band table exactly (955/4,352 … 1,050/3,882; overall **18,164 / 68,449 = 0.2654**), and zero meta rows lacked a games row.

**The table** (capped / games, share):

| Band | self | heuristic | bc | band total |
|---|---|---|---|---|
| v0–24 | 463/2,201 **0.2104** | 260/1,093 0.2379 | 232/1,058 0.2193 | 955/4,352 0.2194 |
| v25–49 | 513/2,082 0.2464 | 247/1,104 0.2237 | 226/1,021 0.2214 | 986/4,207 0.2344 |
| v50–74 | 513/2,110 0.2431 | 238/1,069 0.2226 | 255/1,043 0.2445 | 1,006/4,222 0.2383 |
| v75–99 | 551/2,056 0.2680 | 248/989 0.2508 | 256/1,025 0.2498 | 1,055/4,070 0.2592 |
| v100–124 | 534/1,991 0.2682 | 260/1,040 0.2500 | 270/1,003 0.2692 | 1,064/4,034 0.2638 |
| v125–149 | 811/2,713 0.2989 | 346/1,418 0.2440 | 321/1,342 0.2392 | 1,478/5,473 0.2701 |
| v150–174 | 683/2,305 0.2963 | 280/1,122 0.2496 | 325/1,165 0.2790 | 1,288/4,592 0.2805 |
| v175–199 | 860/2,846 0.3022 | 324/1,425 0.2274 | 385/1,447 0.2661 | 1,569/5,718 0.2744 |
| v200–224 | 671/2,009 **0.3340** | 228/918 0.2484 | 227/945 0.2402 | 1,126/3,872 0.2908 |
| v225–249 | 596/2,061 0.2892 | 235/980 0.2398 | 249/960 0.2594 | 1,080/4,001 0.2699 |
| v250–274 | 615/2,036 0.3021 | 226/946 0.2389 | 268/991 0.2704 | 1,109/3,973 0.2791 |
| v275–299 | 615/2,071 0.2970 | 241/1,029 0.2342 | 265/1,040 0.2548 | 1,121/4,140 0.2708 |
| v300–324 | 613/2,022 0.3032 | 228/988 0.2308 | 250/970 0.2577 | 1,091/3,980 0.2741 |
| v325–349 | 590/1,984 0.2974 | 233/974 0.2392 | 280/1,020 0.2745 | 1,103/3,978 0.2773 |
| v350–374 | 609/2,022 0.3012 | 225/966 0.2329 | 249/967 0.2575 | 1,083/3,955 0.2738 |
| v375–399 | 581/1,945 0.2987 | 229/1,001 0.2288 | 240/936 0.2564 | 1,050/3,882 0.2705 |
| **Overall** | 9,818/34,454 **0.2850** | 4,048/17,062 **0.2373** | 4,298/16,933 **0.2538** | 18,164/68,449 **0.2654** |

**The read.** The climb is **concentrated in learner-vs-learner games**: self-play rises from 0.2104 in the first band to a ≈ 0.30 plateau from v125 on (peak band 0.3340 at v200–224) — a rise of about +0.09. Against the **bc** anchor the rise is milder (0.2193 → ≈ 0.26, about +0.04). Against the **heuristic** there is **no climb at all**: 0.2379 in the first band, 0.227–0.250 in every later band, and the lowest overall share of the three classes (0.2373). So the pooled series' climb is a self-play phenomenon — as the policy moved, games against *itself* reached the caps more often — not something the trained policy does against the heuristic it is gated against. Per the reply, this informs how a future Gravy PPO run is configured; it is not an input to stage 5, and no code change rides on it.

---

## V. Verification record (review pass, 2026-10-22)

Added when two suspected errors in the first draft were checked against primary records; both suspicions failed verification in their stated form, and the checks are recorded here so the readings above do not rest on the draft alone.

- **Analyzer capped accounting.** `analyze_gate.py` sha256 `a5e2086677a69c6055a47de433ada1dfbf29f37e49264af6d4dab0e824277a6e` (round-3 and round-4 copies identical). A whole-file grep for "capped" returns exactly three sites: :10 (docstring), :97–98 (the `score_arm` branch), :241–244 (the pooled unit count). The ranges :239–260 and :320–395 — the sensitivity block, the raw-timeout defect check and the stat monitors — contain no per-arm capped counts; **no per-arm capped counts exist in the tool**. §2.1's statement (one pooled count of units in which either arm capped) stands as corrected for precision.
- **The capped-row identity, asserted on recorded rows.** The stage-3 rollout rows (`rl_out/gravy_ppo_gravybc3/games_w*.jsonl`, 68,449 rows, 18,163 capped) joined to `traj_w*/games_meta.jsonl` on game id: on capped rows the recorded `winner` is **0 in every case** (18,155 rows integer 0; 8 rows the string "0", the same value in a string-typed encoding); **capped rows with winner == learner_seat: 0**. So on real Gravy rows a capped game's recorded outcome is always the draw, and `score_arm`'s 0.5 coincides with the record — belt and braces, since the branch order (:97 before the winner test) makes the score 0.5 regardless. The 4 probe rows and the 800 committed Fai gate rows carry no capped rows (the branch is unexercised there either way).
- **Teacher-timeout wiring (confirmation).** `run_gravy_gate.sh:50` requires `GATE_TIMEOUT`; the value reaches the teacher driver call as `--timeout $TIMEOUT` (:119), the raw call (:125) and the retry (:131); `paired_driver.py:290` runs each game under `timeout=a.timeout` and on `TimeoutExpired` (:292) writes the row `"invalid": "timeout"` (:314); `analyze_gate.py` scores it teacher 0.0 / raw 0.5 (:94), counts teacher timeouts (:212–221), prints the rate (:293–296) and emits GATE INCONCLUSIVE above 2% (:297–299), with the drop-pair sensitivity at :300. Wired end to end; §3's 3,311 s is the value that flows through it.
- **Pre-gate status.** Confirmed at §1.5/O5: the determinism check is registered text (followup-k1-k3-fix §3(a)); no committed runner implements the pre-gate (the fleet runner contains no `pregate`/`ghost`/`8501`/`determinism` string), and no pregate script exists on the box (find-verified; only the round-4 O-era artifacts). A claim that a Gravy pregate script exists with a seat defect could not be verified because the file it named does not exist.
- **Fleet wall-time estimate (for the launch package's planning).** From §3's probe (teacher walls 356.8 / 497.1 / 582.1 / 1,103.4 s under fleet-identical 4-way contention; mean 634.9 s, median 539.6 s) and the runner's structure (four chunks in parallel; within a chunk, 50 teacher + 50 raw games per seat run sequentially, seat after seat): one chunk ≈ 100 teacher games ≈ **15.0 h at the median, 17.6 h at the mean**, plus a few minutes of raw games; the fleet's wall is the slowest chunk's, so **plan on ~15–18 hours** (against the Fai fleet's ~10.6). Each teacher timeout, if any occur, adds its full 3,311 s to its chunk. This is an estimate from four probe games, stated for planning; it is not a registered number.

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude reviews; the K3 pre-gate, the teacher and the stage-5 fleet launch only on Claude's approval of this registration at its committed sha plus Joe's go in chat.*
