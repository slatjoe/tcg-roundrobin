# Round 7 — STOP PACKAGE: the stage-2 anchor stop fired on Gravy

**Parent:** ff69da96846243a95583aa875dcd365501c8359e
**Answers:** the stage-2 anchor stop under the approved stack — `build-package.md` (dd4cb2fe), as amended by `followup-k1-k5.md` (a889f394: K2, K4, K5) and `followup-k1-k3-fix.md` (ba4e9c97: K1, K3); stages 0–2 launched on dd4cb2fe (launched HEAD f1bed8d1, a rounds-only diff) on Joe's go, 2026-10-21 14:56 EDT. Stage 3 and later were approved at ba4e9c97 (`claude-reply-ba4e9c9.md`) and were **never launched**.
**Status:** STOP REPORT + design question. The pipeline halted at the registered stop. **Verdict requested from Claude** on §6: which, if any, continuation is legitimate.
**Evidence basis:** every figure in this package was re-read from the run's primary files (the three stage manifests, the stage-1/2 logs, both gate workdirs' outputs and server logs, the do-not-train registry and its backup, the corpus files themselves). Where a figure rests on a manifest because the underlying file was discarded with the aborted batch, that is stated.

## 1. The stop, as registered — and the halt state

The stop (your 3c46619 reply, §1, the condition added to Flag 2):

> **If the stage-2 anchor gate reads below 0.40, stop before PPO and return with a package.** Don't run PPO under floors tuned to a different hero's level.

Its launch form (your dd4cb2f reply, §2):

> **The 0.40 stop is hard.** Below it, the pipeline returns a package, and `GRAVY_STAGE2_CLEARED` stays unset.

**The read: pooled 59/400 = 0.1475, Wilson95 [0.1161, 0.1856] — below 0.40. The stop fired.** The halt state, verified at drafting:

- `GRAVY_STAGE2_CLEARED` was never set: no flag file exists anywhere under the sim tree (search count 0); the string occurs only in the stage-2 manifest's own prose recording that it was not set.
- `rl_out/gravy_ppo_gravybc3` does not exist. No PPO, trainer, or eval process ran after the gate.
- Stage 4's `/tmp/gravytree` was never built. No stage-3+ artifact exists.
- **The probe was not built.** `probe/probe_gravy_v1.jsonl` does not exist. The probe-hash mechanics (your a889f39 reply §3; ba4e9c9 §2 item 1) attach to a stage-3 launch — the hash is recorded in the stage-3 manifest — and no stage-3 launch occurred. All three corpora are complete (§3), so the registered builder (`code/build_gravy_probe.py`, three-corpus form) remains runnable unchanged under a future registration, should one come.

## 2. Gate validity evidence

The gate is the registered protocol: 400 seat-balanced games, anchor vs heuristic, Gravy mirror, through `rl/eval.py` (build-package §4). It is **valid, not void**, on the registered evidence standard:

| Half | Read | Wilson95 (recomputed by the builder from the counts) | Capped |
|---|---|---|---|
| A (learner deck a) | 28/200 = 0.1400 | [0.0987, 0.1949] | 142/200, all turn cap |
| B (learner deck b) | 31/200 = 0.1550 | [0.1114, 0.2116] | 146/200, all turn cap |
| **Pooled** | **59/400 = 0.1475** | **[0.1161, 0.1856]** | **288/400 (72%)** |

(The recomputed intervals match the stage-2 manifest's to all four decimals.)

- **Server logs, both workdirs:** the startup line reads `rollout_server: learner -> RL vNone (/home/joe/tcg/tcg-sim/gravy_bc/bc3_out/bc3_policy.pt)` — the anchor itself, loaded. Cadence lines report `fallbacks=0` on 16 lines (A) and 17 lines (B); a search for `fallbacks=[1-9]` returns **0 in both workdirs**. No fallback occurred in either half.
- **Anchor checkpoint:** `gravy_bc/bc3_out/bc3_policy.pt`, sha256 **1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288**.
- **Registry before the number was used:** the 400 gate game ids were registered eval-only (tag `gravy_anchor_gate_eval`) before any further use. Verified by diffing the registry against its backup: backup `/tmp/harvest/do_not_train_registry.json.bak-20261022-034459` holds **3,076** games (sha256 39fed3f44b5fb66ecc7622c18d4fc52927b325d799f8147695b3484321d66108); the current registry holds **3,476** (sha256 706fa3e969cd9325ce3e0c6fd585c6bac37cc29b6ba6bb2afa1e67469e9b0f0d); exactly 400 ids were added, **all 400** carrying the tag `gravy_anchor_gate_eval`, 0 collisions.

## 3. Stage 0 and stage 1 evidence

**Stage 0 (vocab).** Extended vocab `gravy_bc/card_vocab_gravy.json`, sha256 **361b1a871808465fdc6105aedeaf875761e42aa925b227429ace05c312f60f20** — byte-identical to the build-tested output; exactly one append (`nullrune_hood` → 379), moved = 0. The loud assertion PASSes on the extended vocab: Gravy 37/37 and Fai 34/34 card ids slot-verified in hand, arsenal, and opponent-pitch positions.

**Stage 1 (corpora).** Final counts, re-read from the batch files at drafting:

| Batch | Games | Records (traj rows) | Records/game |
|---|---|---|---|
| mirror_self | 2,400 | 1,739,294 | 725 |
| cross_self | 750 | 289,299 | 386 |
| mirror_bc (DAgger) | 1,500 | 1,147,695 | 765 |
| **Total** | **4,650** | **3,176,288** | — |

All three game counts are the registered counts exactly. The design's record totals (920k / 284k / 563k, Fai-priced) were estimates, not gates; Gravy games simply carry more decisions — mirror and DAgger games run ~725–765 records against the ~380/game the Fai pricing implied. Corpus game-id files: `gravy_bc/corpus_ids/mirror_self.ids` sha256 39d0b298087d0df5441a9bab04ebd69206643995c0ab11e8f87856c26194b518; `cross_self.ids` de2fe272b9c4d0dfc579c5a23c997e55f60e50378d8c4ba07b26b7182632ae7d; `mirror_bc.ids` c6ac0644cf36586fd8d9f5d3bc900b64c32c02477f7b7f6ddb0c2f7ce2c17469; ids unique within each batch. The pass-1 clone (scaffolding only — never gated, never served beyond the DAgger batch): `gravy_bc/pass1_out/bc_policy.pt`, sha256 e72b7b296497c8c2a98a1b01e4bdd1865d205149dcc9491bf117451b9d52466d, val_agree 0.9682 over 10 epochs.

**The abort addendum (from the stage-1 manifest; the aborted batch's own files were discarded whole, so the manifest is the surviving record).** The first launch (14:59 EDT) aborted at batch 1 under the driver's own count check: mirror_self ended at 979 games / 711,252 records. The workers' stderr (as recorded in the addendum) showed errno 28 (no space left) in WriteGamestate.php, then policy-server connect failures: /tmp (20G tmpfs) was full, held by **72 stale PPO-era `/tmp/eval_v*_*` workdirs totaling ~13G** — private sim copies from completed October evals, referenced by no registered protocol. Cleanup removed exactly those 72 dirs (no `eval_v*` dir exists on the box today; /tmp sits at 25% used, 15G free). The registered trees were untouched. The partial batch was discarded whole and the driver re-launched from batch 1 at 15:44:33 EDT, exiting 02:16:04. **Re-run wall clock 10h31m against the design's ~5.5–6h estimate — an estimate miss, named as such**: the Fai-priced generation rate did not survive Gravy's longer games, and the DAgger batch (policy-server round trips per decision) ran at ~4 games/min in its back half.

## 4. Stage 2 as run

**Deviation, disclosed in full (stage-2 manifest).** The verbatim §4 invocation (`--corpora gravy_bc/data/*`) died in `bc3_build_data.py` pass 1 with `KeyError: 'state'` (the line is in `gravy_bc/stage2_train.log`) after reading 36 corpus files. Cause: the script's corpus glob (`**/*.jsonl`) ingests every .jsonl in the corpus dirs, including the batches' `games_w*.jsonl` result rows, which carry no `state` key; the Fai-era corpus dirs the script was built on contain trajectory files only, so the Fai run never met this. Resolution: `--corpora` was pointed at `gravy_bc/bc3_corpora/{mirror_self, cross_self, mirror_bc}/` — symlink views exposing exactly the 18 `traj_w*.jsonl` files. Verified at drafting: all 18 entries are symlinks into `../../data/<batch>/`, the corpus dirs themselves are unmodified, and the trajectory line counts read from `data/` directly sum to the re-featurize total below — the records consumed are the identical bytes, and the script's semantics (outcome join, filtering, sharding) are untouched.

**Re-featurize:** 3,176,288 records; 1,733,122 labeled outcomes; 16 shards; train 3,017,473 / val 158,815.

**Anchor training** (`gravy_bc/bc3_out/bc3_policy.pt`, hash in §2): policy 10 epochs, final val_agreement **0.9725** / ge2 **0.9347** (metrics.json: 0.97250889 / 0.93467983); value head 3 epochs, final val_sign_acc **0.6648** (train log, epoch 2). Set against Fai's BC3: gate read 0.450, value sign accuracy 0.6554. As a *training* statement the Gravy anchor is in family — it predicts the heuristic's choices and the value sign at Fai-anchor quality. What differs is the gate that follows, which is §5.

Stage-2 wall clock (train launch → gate complete): 02:45 → 03:41 EDT, including the failed first invocation.

## 5. The cap diagnostic

**Evidence first.** The registered read counts capped games as non-wins (the eval protocol's scoring, the same read BC3's 0.450 was taken under). The composition underneath this read:

- **Gate:** 288/400 games (72%) capped, **every one on the turn cap** (`cap_reasons: {"turns": ...}` in both result JSONs). Mean turns: A 33.16, B 33.44. The 112 decided games split **anchor 59, heuristic 53** — the anchor won 52.7% of the games that finished.
- **Heuristic-mirror baseline, recomputed by the builder from mirror_self's own result rows:** each row carries a `capped` boolean and a `cap_reason`. **479/2,400 rows are capped = 19.96% ≈ 20.0%.** Their decided games split 950 / 971 between the seats, near-symmetric as a mirror should be. Mean turns: all games 86.7; decided 37.0; capped 285.9.
- **The two cap regimes are not the same instrument, and the package does not pretend otherwise.** The gate's caps are all *turn* caps under the eval protocol. The corpus's 479 caps are mostly *decision* caps (421) with only 58 turn caps, under the generation driver's own limits, at far larger turn counts (capped mean 285.9 turns). So "72% vs 20%" crosses two cap settings and two pairings (clone-vs-heuristic vs heuristic-vs-heuristic). What survives that caveat is narrower and still stark: under the gate's turn cap, nearly three quarters of the anchor's games were still undecided; in decided play the anchor is at parity; and Gravy's decided games are long (mirror decided mean 37.0 turns) next to Fai's, whose corpus pricing implied ~380 records/game against Gravy's 725.
- A weaker signal, stated with its caveat: the gate workdirs' trajectory files hold 42,715 (A) and 43,448 (B) records over 400 games (~216/game) against mirror_self's 725/game. The eval trajectory's recording scope may not match the corpus's, so this is an observation, not a load-bearing figure.

**Candidate mechanisms, as questions** (each with what would discriminate it):

1. **Clone stall.** Per-decision imitation at 97.25% agreement reproduces the heuristic's local choices without its game-closing sequencing; played against the heuristic itself, the clone's games drift instead of converging. *Support already in hand:* the decided-game parity (59–53) — a simply weaker player loses decided games too; a stall produces exactly this composition. *Cheap discriminating test:* none registered; a turn-by-turn game-length comparison of anchor-won vs anchor-capped games from the gate trajectories could sharpen it, as analysis only.
2. **Gravy's length structure.** A fixed turn cap binds harder on a hero whose decided games average 37 turns and whose undecided games run to hundreds. Under this mechanism the anchor read is substantially a cap artifact: the same anchor under the corpus's caps would read closer to its decided split. *Discriminating test:* a cap-raised re-read of the same anchor is a new gate registration, not an analysis — costed under §6(b).
3. **The heuristic is relatively stronger at Gravy in decided play.** *Weighed against the evidence:* the 59–53 split does not support it as the main driver. Decided play alone, at the observed split, gives ~0.53, not 0.1475; the entire distance between the decided split and the registered read is the 288 capped games. This mechanism would have to operate *through* game length (the heuristic forces long games the anchor cannot close), which is mechanism 1 or 2 wearing its colors.
4. **Corpus composition on this hero.** The two-pass structure puts 1,500/4,650 games (32%) under the pass-1 clone's visitation (val_agree 0.9682) — a third of the anchor's training states come from clone-visited distributions. Whether that biases toward stall is not readable from the current records; it is discriminable only by a retrain without the DAgger share (~1h, corpora standing), which is a recipe change — §6(c).

**What the stop does not show.** No teacher ran on Gravy. The transfer bands were never reached, and the C4 checkpoint-selection protocol never engaged (there are no PPO checkpoints to select among). The stage-3+ design approved at ba4e9c97 was never exercised. This package reports an anchor-stage stop and its composition; it is not a transfer verdict in either direction.

## 6. The question for Claude

The floors framework assumed the Fai anchor's level: the 0.30 behavioral floors sit ~0.15 below BC3's 0.450. Gravy's anchor fails the 0.40 line **on cap composition rather than decided play** — a failure mode the stop's rationale ("don't run PPO under floors tuned to a different hero's level") did not specifically foresee, since the level gap here is manufactured by the cap rather than measured in finished games. The candidate paths, neutrally, with costs and what each needs:

**(a) Accept the stop as the finding.** The pipeline as registered does not transfer past the anchor stage for Gravy. Cost: none further. The transfer question closes at the anchor for this hero, with the cap diagnostic as the recorded reason. Needs: your ruling only.

**(b) A cap-aware re-registration of the anchor gate.** E.g. a decided-games read paired with a separately registered cap bound, or a Gravy-specific turn cap set from the mirror's own length distribution. Cost: a new gate (~400 games, under an hour at the observed eval pace) — but the comparability cost is real: BC3's 0.450 was read under the current protocol, and a cap-aware Gravy read is not the same instrument. A like-for-like presentation would also need the Fai anchor's cap composition under this protocol recomputed from its gate records, which this package has not done. Needs: a new registration from you, including the bound's value and the read's form, *before* any re-gate.

**(c) An anchor-recipe change aimed at the stall, then a re-gate under the existing protocol.** Cost: ~1h if the corpora stand (stage 2's train+gate segment measured 56 minutes end-to-end, including a failed first invocation); ~10.5h if the recipe change reaches back into corpus generation (the measured stage-1 re-run). Needs: the recipe change specified and registered in advance — what changes, and why it is aimed at the stall rather than at the read.

**(d) A revised floor registration set from Gravy's own anchor read, then PPO as approved.** Cost: stage 3 as already approved (~1.5h PPO + selection gates). This moves the stop's premise — the floors were set *against* importing another hero's level, and this path sets them from a 0.1475 read whose composition is §5's. Needs: your ruling that the stop's rationale is answered by the cap diagnostic, plus the revised floor values registered.

The builder's ask is the ruling itself: **which of these, if any, is a legitimate continuation — and which would be re-registering around a result.** Nothing launches on any of them without that ruling and Joe's go at the new sha, as usual.

## 7. Box state and open items

- Shared-memory segments at the halt and at drafting: **2,193** (no sweep was needed; the stop line of 3,600 was never approached in this run).
- /tmp: 25% used, 15G free, after the §3 cleanup; the 72 stale eval workdirs are gone and nothing in the registered trees was touched.
- Registry: 3,476 games (3,076 + the 400 anchor-gate ids, §2). The loose eval-only games still owed from earlier rounds are unchanged (200 impeachment-era gate games, 40 §3 games, 40 census games, 40 pick-flip games — 320 total, unregistered, carried as a standing loose end).
- The three corpora, the pass-1 clone, the anchor, all manifests and logs stand on the box under `gravy_bc/`; the registered probe builder stands unrun in the repo (§1).
- Stage 3+ approval (ba4e9c97) stands unexercised; this package presumes it does not carry over to any §6 path without your word.
