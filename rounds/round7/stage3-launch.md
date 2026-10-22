# Round 7 — stage 3 LAUNCH manifest (Gravy PPO)

**Approved sha:** `3a37f758f53ff976f6f3e96e3fb843f719c22ea1` (stage 3 approved by `claude-reply-3a37f75.md`, CONFIRMED).
**Launched HEAD:** `cc9106c08721f5ae434085f4c77ea5b941066642` — the reply commit on top of the approved sha; the difference is the reply file only, under `rounds/`.
**Registration of record:** `rounds/round7/stage3-alignment-final.md`; the rest of the stack `rounds/round7/followup-k1-k3-fix.md` (ba4e9c97) as amended by the final registration.
**Joe's per-stage go:** 2026-10-22 06:47 EDT, in chat.
**Status: LAUNCHED AND RUNNING.** This manifest covers pre-flight, the clearance flag, the K1 probe build, the launch, and verification through the first spot gate (v5: PASS). The run continues detached on the box; the C4 selection and the stage-3 report follow when PPO halts or completes.

---

## 1. The clearance flag — mechanism, setting, verification

**Mechanism (determined, not assumed).** `GRAVY_STAGE2_CLEARED` is an **environment variable on the launcher invocation** — there is no flag file or other persistent mechanism anywhere. Evidence: the launcher (`code/gravy_ppo_launch.sh:32`) tests `[ "${GRAVY_STAGE2_CLEARED:-0}" = "1" ]` and aborts before any other action if unset; the build package's registered launch line (§5) is `GRAVY_STAGE2_CLEARED=1 bash code/gravy_ppo_launch.sh`; a repo-wide search finds the string only in that check, its header comment, and prose recording that it was not set; a box search of `/tmp/r7launch/` and `gravy_bc/manifests/` finds only the stage-2 manifest's prose ("GRAVY_STAGE2_CLEARED was NOT set"). The stop package's stage-2 record is the same: no flag file exists under the sim tree.

**Setting.** The flag was set exactly as registered: exported in the launch environment of the stage-3 launch (§4). No file was created and no other gating scheme was introduced.

**Verification (both directions, against the deployed launcher, before the probe existed):**
- No env: `bash code/gravy_ppo_launch.sh` → exit 1, `ABORT: stage-2 anchor stop not cleared (GRAVY_STAGE2_CLEARED!=1)`.
- `GRAVY_STAGE2_CLEARED=1 bash code/gravy_ppo_launch.sh` → exit 1, `ABORT: Gravy KL probe missing: /home/joe/tcg/tcg-sim/probe/probe_gravy_v1.jsonl` — the launcher **passed the flag guard** and proceeded to the next guard, proving it sees the flag. (Both aborts fire before the launcher's `mkdir`, so the tests left no state.)
- At the real launch (§4) the same launcher proceeded past all guards (flag, probe, anchor, trainer-hash) into the run.

## 2. Pre-flight (2026-10-22, before launch)

| Check | Expected | Found |
|---|---|---|
| Do-not-train registry (live, `/tmp/harvest/do_not_train_registry.json`) | 4,168 games, sha256 `5547cf2b…` | **4,168 games** (`n_games` field and map length agree), sha256 `5547cf2bd61a4ba83169bf154ba7c8aa30a01d4796a6238f027124f242fc264b` ✓ |
| Anchor `gravy_bc/bc3_out/bc3_policy.pt` | `1e6e3906…48eac288` | `1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288` ✓ |
| SHM segments | < 3,600 (operator stop) | **2,195** ✓ |
| `/tmp` free | sane | 15 G of 20 G free ✓ |
| Stage-1 corpora at their K1 guards | 2,400 / 750 / 1,500 games | mirror_self **2,400**, cross_self **750**, mirror_bc **1,500** ✓ (also asserted by the probe builder, §3) |
| Pristine trainer `rl/trainer_v4.py` | `8fd52d82…` | `8fd52d829acee231b5f066adba879178593de3ffc1a689ca224948186b6a837f` ✓ |
| Competing processes | none | No trainer, no `run_workers.sh`, no rollout servers running (verified with bracketed pgrep patterns; two earlier positive hits were the probing shell's own command line matching its pattern text, resolved and re-checked clean) |
| Output tree `rl_out/gravy_ppo_gravybc3` | absent (fresh run) | Absent ✓ |

**Deployment.** The box had no `$SIM/code/` directory and no installed launch copy; the committed round-7 code was deployed to `/home/joe/tcg/tcg-sim/code/` and every file hash-verified against the committed copy:

| Deployed file | sha256 |
|---|---|
| `code/patch_trainer_launch.py` | `8826e39975bad516ed23af3d9257a202ba4374b420d40c532c8db466ee36cd27` ✓ (= registered) |
| `code/gravy_ppo_launch.sh` | `53d20b824eb414ed77a3a4796c1dc7f00f66a0c9150673178cefc6d4a4715210` ✓ (= registered) |
| `code/build_gravy_probe.py` | `6f5e64b691ef7e20c47ff6b11357db89d6dbea25a9f90a6955c90395e6075b05` ✓ (= K1 fix §V.4) |
| `code/run_formal_gate.sh` | `421934d85bd34c047aa6143ce418bebb5ec9cade33c728462076211b8249c461` ✓ (= registered) |
| `code/run_regate.sh`, `code/run_gravy_gate.sh`, `code/gravy_corpus_driver.sh`, `code/extend_vocab.py`, `code/test_vocab_assertion.py` | deployed with the set; hashes match the committed copies (recorded in the launch working notes) |

**Launch copy.** Produced on the box by the deployed patch script, `python code/patch_trainer_launch.py rl/trainer_v4.py rl/trainer_v4_gravy.py` (exit 0), installed at `rl/trainer_v4_gravy.py`: sha256 **`a48c4abc94f081397bacbdbb09cf04ffdd3c336b08b4eb2eeb51ca18c501a80a`** ✓ (= the registered launch copy), `py_compile` clean. The aligned changes were verified **in the installed file**, not from the draft: change 4 at `:269` (`capped_total` accumulator), `:278` (`"--max-turns", "87"`), `:284` (`"TCG_MAX_DECISIONS": "3000"` in the eval subprocess env), `:304` (capped accumulation), `:309` (`wr = (wins + 0.5 * capped_total) / played`); change 5 at `:454–455` (`won = (0.5 if capped else 1.0 if winner == seat else 0.0)`); changes 1–3 at `:190` (suite None), `:261` (`DECK_SPOT` = the Gravy deck), `:366` (the `--suite none` Flag-2 comment).

## 3. K1 probe — built at launch (launch-time artifact)

Registered invocation (K1 fix §1.5), run on the box 2026-10-22 06:50 EDT:

```
/home/joe/tcg/rl-env/bin/python code/build_gravy_probe.py --sim-root /home/joe/tcg/tcg-sim
```

Build log: `/home/joe/tcg/tcg-sim/probe/build_gravy_probe_20261022.log`. Every guard passed:

| Corpus | Games (guard) | Kept |
|---|---|---|
| `gravy_bc/data/mirror_self` | 2,400 ✓ | 9,000 |
| `gravy_bc/data/cross_self` | 750 ✓ | 9,000 |
| `gravy_bc/data/mirror_bc` | 1,500 ✓ | 9,000 |

- One `probe_kl.py build` invocation over all three corpora, `--per-corpus 9000`; the builder's independent per-corpus re-scan reproduced each corpus's kept `(game, decision)` sequence (`kept sequence verified` ×3).
- Output: `/home/joe/tcg/tcg-sim/probe/probe_gravy_v1.jsonl`, **27,000 states**, 82,914,371 bytes, 27,000 lines.
- **`PROBE_SHA256 efcee286a7ef1202da9b5e060bd506708239a3c8746592c1ca9b73d7986de551`** — the builder's printed value, confirmed by an independent `sha256sum` of the written file. Recorded here per K1 §1.5; a later recomputation mismatch voids the build.

## 4. Launch

```
cd /home/joe/tcg/tcg-sim
setsid env GRAVY_STAGE2_CLEARED=1 bash code/gravy_ppo_launch.sh \
    > /tmp/r7launch/stage3_launch.log 2>&1
```

- **Detached** under `setsid`; the run survives session loss. Launcher pid **555111**; workers (`rl/run_workers.sh 4 $G60 $G60 rl_out/gravy_ppo_gravybc3`, env `SIM`, `BC_MODEL` = the anchor, `TCG_MATCHUPS=gravy:gravy:1.0`) server pids 555146/555151/555156/555161.
- **Trainer start (its own log line): 2026-10-22T10:55:16+00:00 (06:55:16 EDT)** — `trainer_v4 (Phase 3b) starting on cuda; out=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3; drift budget=0.125`; two seconds later: `gate instruments ready: probe 4096 states; suite baseline (BC3) = 0/0 {}` — the Gravy probe loaded at the registered 4,096-state subsample and the suite empty under `--suite none` (Flag 2), as designed.
- Output tree: **`/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3`** (the approved path, build package §5 / launcher `OUT`).
- Configuration: the 3b configuration with the registered four-item delta only (out-dir, anchor, Gravy mirror deck, `--suite none`); canonical KL budget **0.125** against the frozen anchor's probe log-probs; spot gates and heartbeat on the aligned instrument (trigger 62 via `--max-turns 87`, `TCG_MAX_DECISIONS=3000`, draw-scored reads, floors 0.30); rollout workers at **engine defaults** — no cap variables added anywhere (final registration §3.3).
- **Manifest values required by claude-reply-3a37f75 §Scope:** R\* = **0.51213** (the C4 reference for the post-PPO selection); registry **4,168 games / sha256 `5547cf2b…`**; patch script `8826e399…`; launch copy `a48c4abc…`; probe sha256 `efcee286…` (§3).

## 5. Early health (verified from the run's own records)

- **Workers producing games:** all four worker server logs (`/tmp/rlw0..3/server.log`) read `rollout_server: BC loaded (380 cards), mix=self:0.5,bc:0.25,heuristic:0.25 temp=1.0` — the anchor loaded under the 380-entry Gravy vocab, the canonical opponent mix. Each log carries `fallbacks=0` lines and **zero `fallbacks≥1` lines**. `games_w0..3.jsonl` accumulating in the out tree.
- **Heartbeat moving, tally aligned:** `status.json` within the first minute: `games_seen 171, capped_games 34, heartbeat_wr 0.488 (n=43), wr_recent 0.509, halted false`. The 0.5-for-capped tally is change 5 of the **installed launch copy** (`:454–455`, §2) — the running trainer is that file (the launcher execs it and hash-guards it), so the aligned tally is the code in the running tree, verified from the file the process loaded.
- **Versions accepting:** v1 at 10:56:25Z, v2 at 10:57:20Z (KL step ~0.0002/version against the 0.125 budget); no rejections, no halt.

## 6. First spot gate — v5: PASS

Trainer log, 2026-10-22T11:01:22+00:00 (07:01:22 EDT): **`spot-gate v5: pass (WR 0.520 over 50 games, floor 0.3)`**; `status.json` records `last_spot {version 5, wr 0.52, games 50, verdict pass}`, `spot_verified_version 5`.

- The read is the aligned draw-scored read, `(wins + 0.5 × capped) / played`, from the launch copy's `run_spot_gate` (§2, change 4) — the registered read for this instrument, against the unchanged 0.30 floor.
- **Server-log verification (per half):** `spot/v5_a/server.log` and `spot/v5_b/server.log` both read `rollout_server: learner -> RL v5 (/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v5.pt)` with `fallbacks=0` throughout and **no `fallbacks≥1` line**; 25 games per half in `traj/games_meta.jsonl` (50 total).
- **The non-win split is not separately recoverable, and is not reported as a number.** `eval.py` persists no per-game rows for the spot games (the same records property as the anchor gate); the trainer consumed the two summaries in memory and logged only the pooled draw-scored read. A reconstruction from the workdirs' `traj.jsonl` (final-record life channels, `bc_features_v2.py` scalars [1]/[2]) was attempted and **failed its cross-check** — it derives 20 W / 0 L / 30 capped (draw-score 0.70) against the trainer's authoritative 0.520 — because games end on finish steps and opponent actions after the learner's last recorded query, so the final record systematically precedes the game's end (it classifies most learner losses as still-alive "capped"). The derivation is rejected; the draw-scored 0.520 stands as the read of record, and the missing split is a records limitation, recorded here rather than filled in.

## 7. State at hand-back (2026-10-22 07:04 EDT) and what follows

`status.json` at 11:04:09Z: **version 8, accepted 8, rejected 0, halted false**; `games_seen 1,578`, `capped_games 331` → **rollout capped share so far 331/1578 = 0.2098** (the final registration §3.3 report-only figure, tracking the mirror's intrinsic ~0.21); `learner_decisions 589,484`; `kl_cum_last 0.0068` of the 0.125 budget; `heartbeat_wr 0.487` (window full at n=150), `wr_recent 0.485`. SHM segments 2,198 (2,195 at pre-flight) — no leak signature. The run continues detached; nothing about the hand-back stops or alters it.

What follows under the approved stack (not part of this manifest's execution): PPO runs to its halt/completion under the unchanged 3b mechanics; then the **C4 selection** — spot-verified candidates in version order (v5, v10, v15, v20), at most 4 formal gates via the deployed `code/run_formal_gate.sh` in the 8×50 form with the registered partial-completion rule and the §3 run-time conditions of claude-reply-3a37f75, passing against **R\* = 0.51213**; the first passer is the raw arm for stages 4–5. The stage-3 report owes: the rollout stream's capped share per accepted version, the capped-episode reward restated (−1.0, final registration §10), and each formal gate's report-only stall diagnostic. Run logs: trainer stdout `/tmp/r7launch/stage3_launch.log`; workers `rl_out/gravy_ppo_gravybc3/workers_launch.log`; worker server logs `/tmp/rlw*/server.log` (present only during the run).

---

*Builder: Muse (for Joe Slattery), 2026-10-22. Stage 3 launched under Joe's go at the approved sha; this manifest is the launch record for Claude's and Joe's review.*
