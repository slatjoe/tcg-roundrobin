# Round 7 — stage 3 REPORT (Gravy PPO: training, C4 selection, the stop)

**Parent:** 42f590d8a2c4bd01a752ad166ee839f365f18d32 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** the stage-3 approval chain — stage 3 approved on sha `3a37f758…` by `claude-reply-3a37f75.md` (CONFIRMED), under the registration of record `stage3-alignment-final.md` and the ba4e9c97 stack as amended; launched under Joe's per-stage go (2026-10-22 06:47 EDT), launch manifest `stage3-launch.md` (42f590d8). The trainer stop and the formal gates were executed under Joe's order of 2026-10-22 14:15 EDT.
**Status: STAGE 3 COMPLETE, pending Claude's review.** Training ran to its KL ceiling and was stopped by Joe's order with the policy frozen; the C4 selection ran in the registered order and **selected `ckpt_v10.pt`** at the second formal gate (the first passer). Stage 4 is **not** launched by this package.

**Headline numbers.** Final training state: **version 399 — 399 accepted, 25 rejected**; 68,436 games seen (status) / 68,449 rollout game rows on disk; KL cumulative **0.1250 of the 0.125 budget**, reached in the v133 era and never moved again (every later candidate prints KLstep ±0.0000). Formal gates: **v5 FAIL** (draw-score 0.51125 vs R\* 0.51213 — short by half a point of 400), **v10 PASS** (0.52250 [0.47914, 0.56586]). Registry after all merges: **4,968 games**, sha256 `b2ea4558…`.

---

## 1. Training account

### 1.1 Launch and probe

Launched 2026-10-22 **06:55:16 EDT** (trainer log start 10:55:16Z), detached under `setsid`, tree `rl_out/gravy_ppo_gravybc3`, launched HEAD cc9106c0 on the approved sha 3a37f758; the full pre-flight, flag mechanics, and deployment record are in `stage3-launch.md`. **Probe re-verification (K1):** on 2026-10-22, before the gates, `probe/probe_gravy_v1.jsonl` was re-hashed: **sha256 `efcee286a7ef1202da9b5e060bd506708239a3c8746592c1ca9b73d7986de551` — identical to the launch-time artifact** recorded in the launch manifest. The K1 build stands; no mismatch, nothing voided.

### 1.2 Final state (the Phase-1 snapshot, taken before the stop)

`status.json` final write 2026-10-22T18:17:51Z, seconds before the trainer was stopped:

| Field | Value |
|---|---|
| version / accepted / rejected | **399 / 399 / 25** (consecutive rejections 0) |
| games_seen | 68,436 |
| capped_games | 18,159 (cumulative 0.2653 of games_seen) |
| learner_decisions | 27,877,304 |
| KL cumulative | **0.125** of budget 0.125 |
| learning rate | 8.94e-13 (decayed from 3e-05) |
| heartbeat_wr | 0.487 (n = 150), wr_recent 0.4775 |
| last spot gate | v395, pass, WR 0.47; spot_verified_version 395 |
| halted | **false** — the trainer never halted itself (see §1.5) |

Records deltas, stated once: the rollout files on disk hold **68,449 game rows** (`games_w0..3.jsonl`) with **68,444 unique game ids** (5 ids appear in two worker files) and **18,163 capped** among unique ids; the per-version join (§2) totals 68,449 games / 18,164 capped because it counts the 5 duplicated ids twice. The status counters (68,436 / 18,159) were written before the last in-flight games completed. All figures below name their source.

### 1.3 KL trajectory (candidate-line KLcum, from `trainer_v4.log`)

| Attempt at version | KLcum printed |
|---|---|
| 0 | 0.0006 |
| 25 | 0.0166 |
| 50 | 0.0334 |
| 75 | 0.0472 |
| 100 | 0.0793 |
| 125 | 0.1175 |
| 132 | last nonzero step (KLstep 0.0001, 13:20:14Z) |
| 133 → 398 | **0.1250, KLstep ±0.0000 on every candidate line (289 lines)** |

The accepted cumulative KL reached the **0.125 budget in the v133 era** (13:21Z, 09:21 EDT). From then on the trainer kept accepting versions whose printed step is zero (216 lines print `KLstep 0.0000`, 73 print `-0.0000`): **267 versions (v133–v399) were accepted on the plateau**, roughly five hours of wall time, while the learning rate decayed to ~1e-12. (This corrects the morning's running estimate, which put the ceiling at ~v200 from a status read; the log's own candidate lines put it at v133.)

### 1.4 Spot-gate trajectory

**79 spot gates ran (v5–v395, every 5 accepted versions); all 79 passed** the unchanged 0.30 floor on the aligned draw-scored read. Range **0.390–0.690**, mean **0.5132**. The four C4 candidates' reads: **v5 0.520, v10 0.610, v15 0.500, v20 0.440**. The full series (version: WR): v5 .520, v10 .610, v15 .500, v20 .440, v25 .540, v30 .530, v35 .430, v40 .440, v45 .550, v50 .610, v55 .590, v60 .550, v65 .490, v70 .560, v75 .520, v80 .470, v85 .440, v90 .410, v95 .490, v100 .550, v105 .490, v110 .490, v115 .390, v120 .440, v125 .580, v130 .390, v135 .480, v140 .540, v145 .650, v150 .500, v155 .500, v160 .600, v165 .500, v170 .480, v175 .470, v180 .530, v185 .420, v190 .550, v195 .600, v200 .540, v205 .580, v210 .480, v215 .520, v220 .520, v225 .570, v230 .510, v235 .510, v240 .570, v245 .490, v250 .570, v255 .450, v260 .540, v265 .530, v270 .480, v275 .570, v280 .420, v285 .470, v290 .530, v295 .460, v300 .500, v305 .460, v310 .650, v315 .510, v320 .600, v325 .590, v330 .400, v335 .390, v340 .580, v345 .450, v350 .550, v355 .690, v360 .530, v365 .610, v370 .410, v375 .460, v380 .540, v385 .500, v390 .500, v395 .470.

### 1.5 Heartbeat trajectory (recorded snapshots)

`status.json` is overwritten in place, so no dense heartbeat series survives; the snapshots recorded at the time are: ~1 min in (10:56Z) 0.488 (n=43); hand-back 11:04Z **0.487** (n=150, window full); 11:46Z (v49) 0.513; 14:52Z (v199) 0.49; 18:08Z (v389) 0.563; final (v399) **0.487**, wr_recent 0.4775. The heartbeat never approached the 0.30 floor and no heartbeat halt or revert fired at any point in the run (no halt line exists in the trainer log; `halted` stayed false to the stop).

### 1.6 The wind-down and the stop

The trainer has **no halt condition that fires when the KL budget is reached exactly**: its candidates at the ceiling print KLstep ±0.0000 and are accepted, so after v133 the run produced five hours of zero-step versions at full rollout cost. Joe ordered the stop at **14:15 EDT**; it was executed at **14:18:04 EDT** as follows: the launch tree rooted at the recorded launcher pid 555111 was enumerated by parent-walk (22 pids — launcher, `run_workers.sh` parent 555116, worker shells 555169/555170/555172/555176, rollout servers 555146/555151/555156/555161, trainer 555187, 11 transient game processes) and sent TERM — **no KILL was needed**, and a verification scan found no trainer/rollout/worker process alive anywhere. The tree `rl_out/gravy_ppo_gravybc3` is preserved untouched (checkpoints, logs, `games_w*.jsonl`, `status.json`). SHM segments after the stop: **2,194** (2,196 before Phase 1; no leak signature).

## 2. Rollout capped share per accepted version (final registration §3.3 — report-only)

**Method.** Version acceptance timestamps from `trainer_v4.log` (`ACCEPTED -> version N` lines). Each rollout game's timestamp comes from `traj_w*/games_meta.jsonl` (`ts`); its capped flag from `games_w*.jsonl`, joined on the game id (meta `game` == games row `gamename`). A game is binned to the version whose acceptance interval contains its `ts`; games before the first acceptance are version 0 (the anchor's own rollouts). Approximation, stated: worker servers reload the current checkpoint on their own cycle and in-flight games span version boundaries (~171 games per version), so a few games per boundary may be mis-binned; band aggregates are insensitive to it. This is the **rollout** instrument — engine-default caps (turn trigger 725 / 3,000 decisions), *not* the gate instrument; the two capped shares measure different things and are never pooled.

**Restated (§10 of the final registration):** `assign_episode_rewards` pays a capped episode a terminal **−1.0** to the learner, regardless of the recorded winner — a capped rollout episode is priced exactly as a loss. That value is unchanged by this round.

**Result.** The anchor's own rollout games (v0) capped at **0.2066** — the mirror's intrinsic rate, as at launch (0.2098 at hand-back). Under PPO the share **climbed steadily**: ~0.22 over v0–24, ~0.26 by v75–99, ~0.27 from v125 on, peaking in the v200–224 band at 0.2908, and plateauing at **≈0.27** through the KL plateau to the stop. Overall from the records: 18,164 / 68,449 = **0.2654**. Read plainly: as the policy moved away from the anchor, its rollout games reached the caps more often than the anchor's did — under an instrument where a cap pays −1.0 in training. The formal gates (§3) measure the selected candidates on the gate instrument separately; v10's gate capped share there is 0.215 (§3.2), and neither gate's stall diagnostic flagged.

Band table (games / capped / share):

| Versions | Games | Capped | Share |
|---|---|---|---|
| v0–24 | 4,352 | 955 | 0.2194 |
| v25–49 | 4,207 | 986 | 0.2344 |
| v50–74 | 4,222 | 1,006 | 0.2383 |
| v75–99 | 4,070 | 1,055 | 0.2592 |
| v100–124 | 4,034 | 1,064 | 0.2638 |
| v125–149 | 5,473 | 1,478 | 0.2701 |
| v150–174 | 4,592 | 1,288 | 0.2805 |
| v175–199 | 5,718 | 1,569 | 0.2744 |
| v200–224 | 3,872 | 1,126 | 0.2908 |
| v225–249 | 4,001 | 1,080 | 0.2699 |
| v250–274 | 3,973 | 1,109 | 0.2791 |
| v275–299 | 4,140 | 1,121 | 0.2708 |
| v300–324 | 3,980 | 1,091 | 0.2741 |
| v325–349 | 3,978 | 1,103 | 0.2773 |
| v350–374 | 3,955 | 1,083 | 0.2738 |
| v375–399 | 3,882 | 1,050 | 0.2705 |

The full per-version series (version: games/capped share) is Appendix A.

## 3. C4 formal gates

Run 2026-10-22 after the stop, by the committed `code/run_formal_gate.sh` (sha256 `421934d8…`, re-verified on the box before use), in the registered candidate order, under the four run-time conditions of claude-reply-3a37f75 §3. R\* is the script-carried exact value 190/371 = 0.51212938…; pass iff estimate ≥ R\* AND the normal-approximation lower bound > R\* − 0.05 = 0.46213. **Neither gate triggered the partial-completion rule** (no invocation summary carried the timeout error; both gates counted 400/400).

### 3.1 Gate 1 — ckpt_v5.pt (tag `fg_v5_20261022a`) — FAIL

- **Condition 1 (fresh workdir):** `gravy_bc/formal_gate/fg_v5_20261022a` verified **non-existent before the run** (the parent `gravy_bc/formal_gate/` did not exist either); created by the run. ✓
- Per-invocation (games / wins / capped): a1 50/19/20, a2 50/17/8, a3 50/26/5, a4 50/23/8, b1 50/14/15, b2 50/22/3, b3 50/26/7, b4 50/20/9 — all eight exit 0, walls 53–73 s.
- **Pooled: counted 400; candidate wins 167, heuristic wins 158, capped 75 — decided split 167–158; cap reasons {turns: 75}** (zero decision caps, as the ceiling proof predicted).
- **Draw-score 0.51125 [95% CI 0.46710, 0.55540]** (normal approximation on the score mean, var 0.20300); non-win score 0.41750 co-reported.
- **Pass test:** estimate 0.51125 ≥ 0.51213 → **false**; lower bound 0.46710 > 0.46213 → true. **GATE = FAIL** — by half a point: the estimate needed 205.0 points of 400 and scored 204.5 (one loss scored as a draw instead would have tied R\* exactly).
- **Stall diagnostic (report-only):** capped share 0.18750 [Wilson95 0.15229, 0.22866]; Wilson lower 0.15229 < 0.2285 → **not flagged**.
- **Condition 4 (server logs):** all eight workdir server logs checked and listed — `fg_v5_20261022a/{a1,a2,a3,a4,b1,b2,b3,b4}/server.log`: each shows `rollout_server: learner -> RL v5 (/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v5.pt)` and **zero `fallbacks≥1` lines** (a1's log carries only `fallbacks=0` lines, spot-verified in full). ✓
- **Registry:** the gate's 400 ids registered eval-only under `gravy_formal_gate_eval` (meta rows 400, unique 400, **collisions 0**); registry 4,168 → 4,568, sha256 `bc7eda7f…` after this merge. Backup before the merge: `registry-vault/do_not_train_registry.bak-20261022-141825-preformalgates.json` (and a second, pre-this-gate, timestamped backup).

### 3.2 Gate 2 — ckpt_v10.pt (tag `fg_v10_20261022a`) — PASS

- **Condition 1:** `gravy_bc/formal_gate/fg_v10_20261022a` verified **non-existent before the run**. ✓
- Per-invocation (games / wins / capped): a1 50/21/8, a2 50/15/13, a3 50/20/10, a4 50/19/15, b1 50/20/8, b2 50/24/11, b3 50/21/11, b4 50/26/10 — all eight exit 0, walls 53–72 s.
- **Pooled: counted 400; candidate wins 166, heuristic wins 148, capped 86 — decided split 166–148; cap reasons {turns: 86}** (zero decision caps).
- **Draw-score 0.52250 [95% CI 0.47914, 0.56586]** (var 0.19574); non-win score 0.41500 co-reported.
- **Pass test:** estimate 0.52250 ≥ 0.51213 → true; lower bound 0.47914 > 0.46213 → true. **GATE = PASS.**
- **Stall diagnostic (report-only):** capped share 0.21500 [Wilson95 0.17755, 0.25787]; Wilson lower 0.17755 < 0.2285 → **not flagged**.
- **Condition 4:** all eight server logs — `fg_v10_20261022a/{a1,…,b4}/server.log`: each shows `learner -> RL v10 (…/ckpt_v10.pt)` loaded and **zero `fallbacks≥1` lines**. ✓
- **Registry:** 400 ids under `gravy_formal_gate_eval` (collisions 0); registry 4,568 → **4,968** (§4).

**Gates 3–4 (v15, v20) were not run**: the registered rule stops at the first passer (§4.2 of the final registration: the first passer is the raw arm).

## 4. Registry after-state

- Live registry `/tmp/harvest/do_not_train_registry.json`: **4,968 games** (`n_games` field and map length agree), sha256 **`b2ea4558a6ba4158783cfc3bededefdcecf98457b4e92b7bd05b87d9a1cf2bb8`**.
- Tag `gravy_formal_gate_eval` = **800** (400 per gate run); all prior tags unchanged.
- Backups: pre-gates backup `registry-vault/do_not_train_registry.bak-20261022-141825-preformalgates.json` (the 4,168 state, sha `5547cf2b…`), plus a timestamped backup before each gate's merge.
- **Vault refreshed:** `registry-vault/do_not_train_registry-20261022-formalgates.json`, sha256 identical to the live post-merge hash.

## 5. The selection, and what stage 4 needs

**Selected checkpoint (the raw arm for stages 4–5):**

> **`/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt`**
> sha256 **`44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3`**

— the run's v10, spot-verified at 0.610 during training and formally gated at draw-score **0.52250** against R\* = 0.51213 (§3.2). The other candidates of record: v5 (sha `cd51d90d…`, gated 0.51125, FAIL), v15 (`b2ca3efa…`, not gated), v20 (`511e7e2e…`, not gated).

**Stage 4 needs next (not launched by this package):** (i) the **Gravy tree** `/tmp/gravytree` built from `/tmp/otree` with the abort-logging patch carried (K2, hashes pinned in the runner); (ii) the **K3 pre-gate** on that tree with `SEARCH_MODEL` = the selected checkpoint — ghost-vs-raw trace equality on seeds 8501–8510 × both seats, the seat-1 determinism re-run, and the R16 raw control — any non-IDENTICAL unit stops the fleet; (iii) the **teacher** at the byte-identical registered configuration over the selected checkpoint; then (iv) stage 5's **gate fleet** (fresh seeds 8001–8200) under its own registered instrument. Each launches on its own approvals and Joe's per-stage go, as before.

---

## Appendix A — rollout capped share per accepted version (games/capped, share)

Method and caveats at §2. Version 0 is the anchor's own rollout stream before the first acceptance.
v0: 213/44 0.2066  v1: 174/34 0.1954  v2: 184/35 0.1902
v3: 168/34 0.2024  v4: 179/36 0.2011  v5: 205/47 0.2293
v6: 150/30 0.2000  v7: 170/40 0.2353  v8: 177/41 0.2316
v9: 172/38 0.2209  v10: 180/40 0.2222  v11: 156/35 0.2244
v12: 177/34 0.1921  v13: 163/44 0.2699  v14: 172/37 0.2151
v15: 179/38 0.2123  v16: 166/42 0.2530  v17: 152/45 0.2961
v18: 185/36 0.1946  v19: 155/36 0.2323  v20: 183/41 0.2240
v21: 176/37 0.2102  v22: 172/40 0.2326  v23: 182/35 0.1923
v24: 162/36 0.2222  v25: 168/41 0.2440  v26: 178/38 0.2135
v27: 175/38 0.2171  v28: 170/38 0.2235  v29: 170/40 0.2353
v30: 168/37 0.2202  v31: 168/42 0.2500  v32: 167/40 0.2395
v33: 174/38 0.2184  v34: 168/45 0.2679  v35: 168/36 0.2143
v36: 157/35 0.2229  v37: 162/40 0.2469  v38: 177/42 0.2373
v39: 167/41 0.2455  v40: 188/38 0.2021  v41: 148/37 0.2500
v42: 157/46 0.2930  v43: 173/37 0.2139  v44: 172/39 0.2267
v45: 159/37 0.2327  v46: 152/47 0.3092  v47: 172/37 0.2151
v48: 180/39 0.2167  v49: 169/38 0.2249  v50: 186/48 0.2581
v51: 157/37 0.2357  v52: 167/46 0.2754  v53: 164/43 0.2622
v54: 158/35 0.2215  v55: 170/44 0.2588  v56: 159/37 0.2327
v57: 185/41 0.2216  v58: 176/38 0.2159  v59: 165/39 0.2364
v60: 191/45 0.2356  v61: 157/36 0.2293  v62: 154/36 0.2338
v63: 157/41 0.2611  v64: 182/36 0.1978  v65: 173/34 0.1965
v66: 152/45 0.2961  v67: 149/40 0.2685  v68: 198/39 0.1970
v69: 164/39 0.2378  v70: 165/41 0.2485  v71: 159/44 0.2767
v72: 168/41 0.2440  v73: 178/42 0.2360  v74: 188/39 0.2074
v75: 165/40 0.2424  v76: 168/36 0.2143  v77: 175/44 0.2514
v78: 155/43 0.2774  v79: 163/52 0.3190  v80: 183/40 0.2186
v81: 137/42 0.3066  v82: 170/41 0.2412  v83: 169/42 0.2485
v84: 160/43 0.2687  v85: 157/46 0.2930  v86: 155/46 0.2968
v87: 179/40 0.2235  v88: 142/49 0.3451  v89: 161/40 0.2484
v90: 168/40 0.2381  v91: 173/40 0.2312  v92: 152/36 0.2368
v93: 148/45 0.3041  v94: 166/38 0.2289  v95: 182/46 0.2527
v96: 161/42 0.2609  v97: 152/35 0.2303  v98: 166/44 0.2651
v99: 163/45 0.2761  v100: 157/43 0.2739  v101: 156/47 0.3013
v102: 173/38 0.2197  v103: 170/38 0.2235  v104: 160/47 0.2938
v105: 163/39 0.2393  v106: 167/41 0.2455  v107: 172/39 0.2267
v108: 154/47 0.3052  v109: 169/39 0.2308  v110: 163/37 0.2270
v111: 163/46 0.2822  v112: 158/53 0.3354  v113: 159/32 0.2013
v114: 338/92 0.2722  v115: 179/54 0.3017  v116: 198/51 0.2576
v117: 18/6 0.3333  v118: 45/19 0.4222  v119: 160/43 0.2687
v120: 168/40 0.2381  v121: 160/44 0.2750  v122: 155/45 0.2903
v123: 158/45 0.2848  v124: 171/39 0.2281  v125: 182/36 0.1978
v126: 179/35 0.1955  v127: 174/37 0.2126  v128: 151/47 0.3113
v129: 153/49 0.3203  v130: 170/41 0.2412  v131: 178/40 0.2247
v132: 616/189 0.3068  v133: 167/42 0.2515  v134: 170/38 0.2235
v135: 166/50 0.3012  v136: 300/90 0.3000  v137: 156/44 0.2821
v138: 172/42 0.2442  v139: 340/79 0.2324  v140: 333/81 0.2432
v141: 464/131 0.2823  v142: 161/48 0.2981  v143: 315/95 0.3016
v144: 149/47 0.3154  v145: 130/45 0.3462  v146: 154/47 0.3052
v147: 170/39 0.2294  v148: 161/47 0.2919  v149: 162/39 0.2407
v150: 145/46 0.3172  v151: 334/92 0.2754  v152: 301/94 0.3123
v153: 141/43 0.3050  v154: 163/43 0.2638  v155: 166/51 0.3072
v156: 157/43 0.2739  v157: 152/46 0.3026  v158: 161/42 0.2609
v159: 157/46 0.2930  v160: 325/88 0.2708  v161: 131/44 0.3359
v162: 187/39 0.2086  v163: 148/38 0.2568  v164: 336/87 0.2589
v165: 180/45 0.2500  v166: 151/43 0.2848  v167: 162/46 0.2840
v168: 151/52 0.3444  v169: 170/40 0.2353  v170: 173/47 0.2717
v171: 149/39 0.2617  v172: 160/45 0.2812  v173: 151/46 0.3046
v174: 141/43 0.3050  v175: 178/43 0.2416  v176: 458/134 0.2926
v177: 149/47 0.3154  v178: 164/43 0.2622  v179: 158/46 0.2911
v180: 150/57 0.3800  v181: 127/41 0.3228  v182: 157/43 0.2739
v183: 172/43 0.2500  v184: 171/40 0.2339  v185: 179/45 0.2514
v186: 458/126 0.2751  v187: 314/87 0.2771  v188: 151/51 0.3377
v189: 310/87 0.2806  v190: 150/40 0.2667  v191: 330/91 0.2758
v192: 153/43 0.2810  v193: 158/47 0.2975  v194: 171/39 0.2281
v195: 150/49 0.3267  v196: 161/43 0.2671  v197: 173/42 0.2428
v198: 823/199 0.2418  v199: 153/43 0.2810  v200: 182/44 0.2418
v201: 142/44 0.3099  v202: 159/42 0.2642  v203: 148/49 0.3311
v204: 146/42 0.2877  v205: 144/52 0.3611  v206: 154/45 0.2922
v207: 146/52 0.3562  v208: 165/39 0.2364  v209: 160/53 0.3312
v210: 185/48 0.2595  v211: 121/41 0.3388  v212: 145/39 0.2690
v213: 184/37 0.2011  v214: 169/39 0.2308  v215: 180/57 0.3167
v216: 123/39 0.3171  v217: 144/40 0.2778  v218: 138/55 0.3986
v219: 156/44 0.2821  v220: 156/51 0.3269  v221: 156/35 0.2244
v222: 149/49 0.3289  v223: 171/43 0.2515  v224: 149/47 0.3154
v225: 188/46 0.2447  v226: 128/38 0.2969  v227: 174/45 0.2586
v228: 150/41 0.2733  v229: 176/38 0.2159  v230: 204/47 0.2304
v231: 130/38 0.2923  v232: 153/44 0.2876  v233: 163/41 0.2515
v234: 149/44 0.2953  v235: 154/46 0.2987  v236: 162/43 0.2654
v237: 157/42 0.2675  v238: 155/49 0.3161  v239: 164/42 0.2561
v240: 194/53 0.2732  v241: 117/35 0.2991  v242: 167/42 0.2515
v243: 167/49 0.2934  v244: 146/36 0.2466  v245: 198/50 0.2525
v246: 133/36 0.2707  v247: 166/44 0.2651  v248: 169/48 0.2840
v249: 137/43 0.3139  v250: 193/55 0.2850  v251: 139/35 0.2518
v252: 162/42 0.2593  v253: 177/48 0.2712  v254: 159/43 0.2704
v255: 158/53 0.3354  v256: 136/36 0.2647  v257: 169/49 0.2899
v258: 153/44 0.2876  v259: 135/44 0.3259  v260: 172/43 0.2500
v261: 161/45 0.2795  v262: 165/39 0.2364  v263: 156/45 0.2885
v264: 153/40 0.2614  v265: 168/46 0.2738  v266: 146/41 0.2808
v267: 170/43 0.2529  v268: 152/47 0.3092  v269: 161/45 0.2795
v270: 189/56 0.2963  v271: 126/38 0.3016  v272: 148/41 0.2770
v273: 179/43 0.2402  v274: 146/48 0.3288  v275: 186/52 0.2796
v276: 133/34 0.2556  v277: 161/44 0.2733  v278: 157/46 0.2930
v279: 178/39 0.2191  v280: 187/46 0.2460  v281: 138/35 0.2536
v282: 145/49 0.3379  v283: 178/37 0.2079  v284: 143/41 0.2867
v285: 149/57 0.3826  v286: 264/71 0.2689  v287: 53/12 0.2264
v288: 157/46 0.2930  v289: 135/41 0.3037  v290: 181/40 0.2210
v291: 340/89 0.2618  v292: 27/5 0.1852  v293: 117/34 0.2906
v294: 307/92 0.2997  v295: 169/45 0.2663  v296: 147/41 0.2789
v297: 150/44 0.2933  v298: 168/43 0.2560  v299: 170/38 0.2235
v300: 183/60 0.3279  v301: 119/32 0.2689  v302: 161/44 0.2733
v303: 171/38 0.2222  v304: 165/43 0.2606  v305: 173/50 0.2890
v306: 134/36 0.2687  v307: 153/48 0.3137  v308: 163/42 0.2577
v309: 162/44 0.2716  v310: 177/54 0.3051  v311: 131/38 0.2901
v312: 167/42 0.2515  v313: 158/44 0.2785  v314: 170/40 0.2353
v315: 176/54 0.3068  v316: 152/41 0.2697  v317: 159/34 0.2138
v318: 155/47 0.3032  v319: 149/45 0.3020  v320: 200/48 0.2400
v321: 126/38 0.3016  v322: 163/50 0.3067  v323: 148/39 0.2635
v324: 165/40 0.2424  v325: 167/46 0.2754  v326: 153/46 0.3007
v327: 170/38 0.2235  v328: 162/44 0.2716  v329: 160/45 0.2812
v330: 164/44 0.2683  v331: 146/52 0.3562  v332: 148/46 0.3108
v333: 148/50 0.3378  v334: 158/45 0.2848  v335: 190/41 0.2158
v336: 123/38 0.3089  v337: 153/46 0.3007  v338: 173/46 0.2659
v339: 167/42 0.2515  v340: 167/51 0.3054  v341: 150/40 0.2667
v342: 161/41 0.2547  v343: 165/43 0.2606  v344: 154/43 0.2792
v345: 217/55 0.2535  v346: 100/31 0.3100  v347: 160/45 0.2812
v348: 166/39 0.2349  v349: 156/46 0.2949  v350: 166/51 0.3072
v351: 149/35 0.2349  v352: 149/45 0.3020  v353: 173/41 0.2370
v354: 176/38 0.2159  v355: 170/56 0.3294  v356: 138/33 0.2391
v357: 143/41 0.2867  v358: 164/52 0.3171  v359: 160/39 0.2437
v360: 166/39 0.2349  v361: 141/48 0.3404  v362: 171/44 0.2573
v363: 151/49 0.3245  v364: 167/43 0.2575  v365: 184/44 0.2391
v366: 145/42 0.2897  v367: 143/37 0.2587  v368: 175/46 0.2629
v369: 142/43 0.3028  v370: 195/53 0.2718  v371: 129/37 0.2868
v372: 151/47 0.3113  v373: 164/43 0.2622  v374: 143/37 0.2587
v375: 170/42 0.2471  v376: 163/44 0.2699  v377: 149/50 0.3356
v378: 165/41 0.2485  v379: 156/45 0.2885  v380: 170/48 0.2824
v381: 147/37 0.2517  v382: 169/43 0.2544  v383: 153/47 0.3072
v384: 155/46 0.2968  v385: 186/49 0.2634  v386: 144/44 0.3056
v387: 160/47 0.2938  v388: 171/39 0.2281  v389: 146/37 0.2534
v390: 186/42 0.2258  v391: 150/37 0.2467  v392: 148/47 0.3176
v393: 163/40 0.2454  v394: 157/46 0.2930  v395: 180/48 0.2667
v396: 142/43 0.3028  v397: 153/37 0.2418  v398: 165/40 0.2424
v399: 34/11 0.3235
---

*Builder: Muse (for Joe Slattery), 2026-10-22. Stage 3 executed under the approval chain recorded in the header; the trainer stop under Joe's order of 14:15 EDT. Claude reviews; stage 4 launches only on its own approvals and Joe's go.*
