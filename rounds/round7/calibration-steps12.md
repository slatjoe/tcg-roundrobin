# Round 7 — instrument calibration, steps 1–2 (+ §4 open item 1)

**Parent:** f4c7de5a7da2c8d836162526a6cb9ec6018f9723
**Answers:** `rounds/round7/claude-reply-2706e33.md` §3 (the registered instrument calibration, steps 1–2 and the records branch of step 3) and §4 open item 1.
**Status:** ANALYSIS ONLY. No games were run, nothing was launched, no code was changed. Every figure below is read or recomputed from primary records: the box's code (`rl/eval.py`, `play_game.php`, `bc2_gen.sh`, `featurize.php`), the anchor gate's surviving workdir records, the BC3 regate logs, and `mirror_self`'s result rows.

**Headline results.** The eval protocol's turn cap is the parameter `TCG_MAX_TURNS = 60`, implemented as a trigger at **35** engine turns (§1) — the gate's reported means are arithmetically impossible under a cap-at-60 reading and reproduce exactly under the trigger. The Fai anchor gate's records survive: **0 capped of 333**, mean turns 15.06 (§2). The unit test for step 3 passes — the corpus driver's `turns` and the eval protocol's `turns` are the same counter from the same code — so H is computable from records: **H = 1,613/2,400 = 0.6721 [0.6530, 0.6906]**, the ≥ 0.40 band under the registered rule (§3). The 400-game heuristic-mirror run is **not** needed. Open item 1: **319 of the 320 loose eval-only game ids are recoverable; exactly 1 is not** (§4).

---

## 1. Step 1 — the eval protocol's turn cap: value, unit, reconciliation

### 1.1 The cap, from the code

`rl/eval.py` (box, `/home/joe/tcg/tcg-sim/rl/eval.py`):

- Lines 105–108: `--max-turns`, type int, **default 60**, help text: *"harness turn cap (TCG_MAX_TURNS); capped games end as draws in the engine and count as learner non-wins, reported via capped_games"*.
- Line 167: the value is exported as `TCG_MAX_TURNS` in the policy server's environment; line 185: the same export in the php process's environment. The Gravy anchor gate's invocation (`/tmp/r7launch/run_stage2_gate.sh`, the two registered `rl/eval.py` calls for halves A and B) passes **no** `--max-turns`, so the gate ran at the default: **TCG_MAX_TURNS = 60**. (The Fai gate's script, `run_gate_bc3.sh`, passed `--max-turns 60` explicitly — same value.)

`play_game.php` `PlayOneGame` (production file, same tree eval copies from):

- Line 332: `$maxTurns = intval(getenv("TCG_MAX_TURNS") ?: 750)`.
- Line 336: **`$capTrigger = $maxTurns - 25`** — with the comment at lines 334–335: the turn counter can jump several turns inside one `PuzzleFinishStep`, so the cap triggers a margin early to keep the final turn count ≤ `$maxTurns`.
- Lines 361 and 366: after every finish step (and every drive step), if `$turns >= $capTrigger` the game ends as a draw with `cap_reason = "turns"`.
- The other caps, all at the same defaults in both harnesses (neither `rl/eval.py` nor `bc2_gen.sh` sets them): decisions — line 367, policy queries > `TCG_MAX_DECISIONS ?: 3000` → `"decisions"`; stuck — line 370, unchanged state hash > `TCG_STUCK_LIMIT ?: 200` → `"stuck"`; steps — line 331, `TCG_MAX_STEPS ?: 30000` → `"steps"`/`"guard"`.
- The result row (lines ~381–391): `"turns" => $turns` (the maximum engine turn counter observed), `"capped" => $capReason !== null`, `"cap_reason" => $capReason`. `eval.py` lines 222–231 tally `capped_games` / `cap_reasons` from these rows and compute `mean_turns` as the mean of the rows' `turns`.

**The cap stated precisely:** the protocol's turn-cap parameter is **60**; the cap as implemented **ends a game when its turn counter reaches 35**, and capped games' recorded `turns` land in **[35, 60]** by construction (the margin exists to guarantee the upper bound).

**Unit.** `turns` is `$GLOBALS["currentTurn"]` — the Talishar engine's turn counter (gamestate line 41). The same value is exposed to the bridge as the state field `"turn"` (`featurize.php:87`) and encoded in the policy state vector as `turn / 30.0` (`bc_features_v2.py:53`). One count per player-turn, starting at 0 at the opening decision (two counts per full round). Every `turns` figure in this document — eval rows, corpus rows, state vectors — is this one counter.

### 1.2 Reconciliation with the gate's means (33.16 / 33.44, 72% capped)

The reply's bound: with 72% of games at the cap, a cap value T satisfies mean ≥ 0.72·T, so T ≤ ~46 in reported units — against round 3's registered "engine turn cap 60". The code resolves it: **60 is the parameter, 35 is where games actually end.**

- Under a cap-at-60 reading, the pooled mean would be at least 0.72 × 60 = **43.2**. The reported pooled mean is **33.30**. That reading is arithmetically impossible.
- Under the trigger (35), the split derived in §1.3 — capped games averaging ≈ 36.1 recorded turns (just past the trigger; overshoot from the final finish step), decided games ≈ 26.2 — gives 0.72 × 36.07 + 0.28 × 26.18 = **33.30**, the reported pooled mean to two decimals. Both halves check the same way.

### 1.3 The gate's mean turns, split by decided vs capped

**What survives, and what does not.** `eval.py` aggregates the php result rows in memory and persists none of them; the gate workdirs (`gravy_bc/anchor_gate_a`, `anchor_gate_b`) hold only `php.log` (a 60-byte banner), `server.log`, and `traj/` — per-decision records whose `"t"` field is a per-game *query counter* (`rl/rollout_server.py:388–425`: starts at 0, increments per logged decision), **not** turns, plus `games_meta.jsonl` (ids and seats). There are no per-game result rows for the gate. The split below is therefore **derived**, by a stated method, from the traj state vectors — each decision record's `sv[0]` is the state's engine turn ÷ 30 (§1.1) — and validated against the aggregates, which are exact.

**Method.** Per game: last-query turn = max over its decision records of `sv[0] × 30`. Validation against the halves' exact totals (200 × mean_turns): A — Σ last-query turns 6,593 vs 6,632 exact, shortfall 39; B — 6,645 vs 6,688, shortfall 43 (≈ 0.2 turns per game: a game's final turn runs past its last learner query by 0–1 turns in about a fifth of games). Classification: capped status is monotone in game length, so the 142 (A) / 146 (B) games with the largest last-query turns are the capped class; the boundary falls at last-query turn 34 in both halves (19 games sit there in A, 20 in B — split 13 capped / 6 decided in A and 14 / 6 in B by the count identity). Class means are computed from the last-query sums plus the known total shortfall, allocated three ways (all to capped / proportional / all to decided) to give the range.

|  | capped n | capped mean turns | decided n | decided mean turns |
|---|---|---|---|---|
| Half A | 142 | **36.1** (35.9–36.1) | 58 | **26.0** (25.9–26.6) |
| Half B | 146 | **36.1** (35.8–36.1) | 54 | **26.3** (26.2–27.0) |
| Pooled | 288 | **36.1** (35.9–36.1) | 112 | **26.2** (26.0–26.8) |

Capped games' last-query turns, both halves: **min 34, median 36, max 43** — i.e., recorded final turns of ≈ 35–44, piled just past the 35 trigger, never near the 60 bound. The gate's own records thus confirm the §1.1 mechanics empirically.

---

## 2. Step 2 — the Fai anchor gate's cap composition (BC3, the 150/333)

**The records survive.** The repaired-harness regate's aggregate logs are on the box at `rl_out/regate_bc3_heu_a.log` and `rl_out/regate_bc3_heu_b.log`, with their workdirs (`traj/`, `server.log`, `php.log`) alongside. The two aggregates sum to exactly the cited gate (69 + 81 = 150 wins; 165 + 168 = 333 games):

|  | games | wins | capped | cap reasons | mean turns |
|---|---|---|---|---|---|
| Half A (learner deck a) | 165 | 69 | **0** | {} | 15.309 |
| Half B (learner deck b) | 168 | 81 | **0** | {} | 14.815 |
| **Pooled** | **333** | **150** | **0** | — | **15.06** |

- **Capped count: 0 of 333.** No cap of any reason (turns / decisions / stuck / steps) appears in either aggregate.
- **Decided split: 150 learner – 183 heuristic** (all 333 games decided; half A 69–96, half B 81–87).
- Both halves carry `"error": "play_game.php timed out (partial results used)"` — the 333-of-400 partial completion under concurrent training load that the 2026-10-16 corrected gate note records; `traj_games` (166 / 169) exceeds the counted games by one per half, the in-flight game at the timeout.
- Same protocol family: `run_gate_bc3.sh` ran `rl/eval.py` with `--max-turns 60` explicit — the same parameter, the same 35 trigger. Fai games under it averaged ≈ 15 turns and never reached the trigger.

---

## 3. Step 3 (records branch) — H, the heuristic mirror's capped share under the eval protocol

### 3.1 The unit test

H may be read off `mirror_self`'s rows **iff** the corpus driver's `turns` unit matches the eval protocol's. It does, by construction:

- Both harnesses consume the **same emitter**: `PlayOneGame`'s result row in the production `play_game.php`. `rl/eval.py` aggregates its stdout rows; `bc2_gen.sh` captures the identical stdout into `games_w*.jsonl` (its workers run copies of the same `play_game.php` and `vendor/` from the same source tree).
- `turns` in both is `$GLOBALS["currentTurn"]` (§1.1). The driver and the eval run the same engine snapshot; no cap-relevant code differs between them.
- The only cap difference is the parameter: `bc2_gen.sh` sets no `TCG_MAX_TURNS`, so the corpus ran at the code default (parameter 750, trigger 725). All other cap parameters sit at the same unset defaults in both harnesses.

A mirror game replayed under the eval protocol would be capped iff it reaches the eval trigger (35 turns), hits the shared decision/stuck/steps limits, or was already capped in the corpus. The registered formula — *the share of games whose turn count exceeds the eval cap, counting already-capped rows as capped* — is therefore computable from the 2,400 rows, with "the eval cap" read as §1 establishes the protocol's cap to be: the count at which it ends games, **35**.

### 3.2 H

From `gravy_bc/data/mirror_self/games_w*.jsonl` (2,400 rows, re-counted):

- Already capped (any reason): **479** — 421 `"decisions"`, 58 `"turns"`.
- Not capped, with `turns` ≥ 35 (would reach the eval trigger): **1,134** of 1,921.
- **H = (479 + 1,134) / 2,400 = 0.6721, Wilson95 [0.6530, 0.6906].**

Supporting distribution — the mirror's uncapped games' turns (n = 1,921): mean 37.03, median 37, 99th percentile 62, max 80. A typical Gravy heuristic game runs *past* the eval trigger; the protocol caps the teacher's own mirror at roughly two-thirds.

**Decomposition** (each reading of the two choices, so the band's dependence on them is visible; the primary is the first row, per the registered formula and §1's code facts):

| reading | computation | H | Wilson95 |
|---|---|---|---|
| **already-capped (all reasons) + turns ≥ 35 (the trigger)** | (479 + 1,134) / 2,400 | **0.6721** | [0.6530, 0.6906] |
| turns-only + turns ≥ 35 | (58 + 1,134) / 2,400 | 0.4967 | [0.4767, 0.5167] |
| already-capped (all reasons) + turns > 60 (the parameter) | (479 + 36) / 2,400 | 0.2146 | [0.1986, 0.2315] |
| turns-only + turns > 60 | (58 + 36) / 2,400 | 0.0392 | [0.0321, 0.0477] |

The > 60 rows answer a different question than the registered one: 60 is the bound the margin guarantees on a capped game's *recorded* turns, not a count games are allowed to reach — a mirror game at 40 turns does not "exceed 60", yet under the eval protocol it ends capped at ≈ 35, as the gate's own capped recordings (35–44, §1.3) show happening in practice.

### 3.3 The registered decision rule, applied

Under the primary reading, **H = 0.6721 ≥ 0.40** — the high band. The calibration is complete from records; the 400-game heuristic-vs-heuristic eval run is **not** needed, because the units match. The band's registered consequence, stated as the registration states it (claude-reply-2706e33 §3): *the protocol doesn't measure Gravy play at this cap, and the 0.40 line isn't meaningful on it; a re-specified gate may come back as a registration, under these terms — its turn cap set from the heuristic mirror's decided-game length distribution (the 99th percentile; 62 counts in the mirror's uncapped games, §3.2), never from the anchor's games; capped games score as non-wins, as now; the 0.40 line kept unchanged; the floors stay at 0.30.* Nothing in this section recommends for or against bringing such a registration; paths (b), (c), (d) remain as the reply ruled on them, and any continuation needs its own registration and Joe's go.

---

## 4. §4 open item 1 — the 320 loose eval-only games vs the 72 deleted dirs

The 72 `/tmp/eval_v*_*` dirs deleted during stage 1 held PPO league-eval sim copies (a different population from all four groups below). Each group's id records were sought in the surviving workdirs and the committed repo data. None of the four groups' records lived in the deleted dirs — all four workdir sets survive intact today.

| group | ids recoverable | where | notes |
|---|---|---|---|
| Oct 18-era gate games (tgate), 200 planned | **199** | `/tmp/tgate_c{0..3}{a,b}/traj/games_meta.jsonl` + `traj.jsonl` + `teacher_snaps/` (snap ids a strict subset in every chunk) | Chunk summaries record 196 completed games; 199 games left traj records. One planned game in chunk **c0b** (25 planned, 24 ids) recorded **no id anywhere** — searched meta, traj, snaps; the chunk summaries carry counts, not ids. |
| §3 measurement games, 40 | **40** | `/tmp/meas_c{0,1}{a,b}/traj/games_meta.jsonl` (10 per workdir) | The §3 harvest workdirs survive whole. |
| Census games, 40 | **40** | Result rows in `/tmp/census/census_s{1,2}.jsonl`; also committed: `rounds/round5/data/census/census_s{1,2}.jsonl` | Doubly recorded. |
| Pick-flip games, 40 | **40** | Result rows in `/tmp/pickflip/flip_s{1,2}.jsonl`; also committed: `rounds/round6/data/pickflip/flip_s{1,2}.jsonl` | Doubly recorded. |

**The loose end restated:** of the 320 eval-only games owed to the do-not-train registry, **319 ids are recoverable** from surviving records and remain unregistered (the merge itself is unchanged, still owed); **exactly 1 — a tgate chunk-c0b game that never reached the policy server's records — is unrecoverable** from any record found. The loose end is therefore *partly unrecoverable, by one game*, not wholly open. (Standing caveat, the reply's §4.2 point: the surviving workdirs above also live on the box's tmpfs; the registry and its backup were copied to persistent storage on 2026-10-22, but these id sources have no persistent copies except where the repo data duplicates them — census and pick-flip only.)

---

## 5. What this calibration does and does not establish

Steps 1–2 and the records branch of step 3 are complete: the cap is stated from code with its unit (parameter 60, trigger 35, engine turn counter); the gate's means reconcile exactly under it; the Fai anchor gate's composition is read from its surviving records (0 capped of 333); H is computed from the mirror corpus under the registered formula (0.6721) and lands in the ≥ 0.40 band, with the full decomposition tabled for any other reading. No games were run and no anchor was touched. What happens next is not this document's to say: a re-specified gate is a new registration, and the stop stands until one is approved and Joe gives the go.
