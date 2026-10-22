# Round 7 — re-specified anchor gate: registration draft (REGISTRABILITY FAILS under R2)

**Parent:** 5f3371653f23a1809ca33f77bd6e2f8c93d6e312
**Answers:** `rounds/round7/claude-reply-ac725a5.md` §3 (the refinement R1–R4, registered as preconditions for any re-specified anchor gate).
**Status:** REGISTRATION DRAFT for Claude's review. **No gate is registered by this document, and nothing in it launches.** The registrability test that R2 fixes — H′ ≤ 0.10, computed from the heuristic mirror's records under the p99-based caps — **fails on the turn component alone (§3)**, and the decision cap cannot be set from the records at all (§2). Per R2's own terms ("report it and stop; that comes back to me and Joe"), this document reports the evidence, specifies everything that *can* be specified, and returns for a ruling. The stop stands.
**Evidence basis:** all computations are over existing records — `mirror_self`'s 2,400 result rows and 1,739,294 trajectory rows on the box, the production code (`play_game.php`, `policy_server.php`, `rl/eval.py`), the stage-2 gate records (`gravy_bc/manifests/stage2_manifest.txt`, `gravy_bc/stage2_gate.log`). No games were run for this draft.

**Headline results.**

- **Turn cap: solved from the records.** Decided games' turns p99 = **62** (every percentile method), so the effective trigger is 62 and the parameter is **TCG_MAX_TURNS = 87** (§1).
- **Decision cap: not derivable from the records.** The corpus result rows carry no per-game policy-query count, and the trajectory-row count is provably a different quantity (§2). R1's fallback applies: the measurement is proposed, no number is invented.
- **H′: the turn component alone is 508/2,400 = 0.2117 [0.1958, 0.2285] — above the 0.10 registrability line for any decision-cap setting** (§3). The p99-based setting is not registrable. Alternative settings are tabled as data only.

---

## 1. The turn cap (R1, first half) — parameter and trigger

**Population.** `mirror_self`'s 2,400 result rows (`gravy_bc/data/mirror_self/games_w*.jsonl`, re-read for this draft). *Decided* is used exactly as the calibration used it: a row with `capped == false` — the game reached a winner under the corpus's own limits (parameter 750 / trigger 725, decision limit 3,000). n = 1,921 decided; 479 capped (421 `"decisions"`, 58 `"turns"`).

**Turns distribution, decided games:** mean 37.03, median 37, max 80. **p99 = 62** — identical under nearest-rank, linear interpolation, lower, and higher percentile methods, and matching the calibration's figure (§3.2 of `calibration-steps12.md`, computed there over the same uncapped population).

**The setting, stated as parameter and trigger (the ac725a5 standing rule):**

- Effective trigger (the count at which the protocol ends a game): **62** engine turns — the decided games' p99, per R1 ("at no less than").
- Parameter: `play_game.php:336` implements the trigger as `$capTrigger = $maxTurns − 25`, so the parameter that yields a 62 trigger is **TCG_MAX_TURNS = 62 + 25 = 87**. (A parameter of 62 would trigger at 37 — the failure the reply warns against, one step removed from the original 60/35.)

This half of R1 is fully satisfied from the records.

## 2. The decision cap (R1, second half) — not in the records; measurement proposed

### 2.1 The corpus rows carry no query count

Every one of the 2,400 result rows carries the same 12 fields: `cap_reason, capped, draw, firstPlayer, game, gamename, p1life, p2life, steps, stuck, turns, winner`. There is **no decision or policy-query count**. (Nor do the eval protocol's result rows: `rl/eval.py` aggregates `winner`, `capped`, `cap_reason`, `turns` only.)

The counter itself exists and is exact: `play_game.php:345` zeroes `$GLOBALS["simPolicyQueries"]`; `policy_server.php:49` and `:85` increment it (the candidate-choice route and the decision-queue route); `play_game.php:367` ends the game as a draw with `cap_reason = "decisions"` when the count exceeds the limit. The count is even exposed transiently — `policy_server.php:93` returns `"queries"` in a bridge response — but **it is persisted nowhere per game**: not in the result row (§2.1's field list is the whole row), not in the trajectory files, not in any log the corpus run kept.

**How the decision cap is implemented (parameter vs behavior, for the record):** unlike the turn cap, there is **no margin**. `TCG_MAX_DECISIONS` (default 3,000, read at `play_game.php:344`) is checked once per drive step at line 367, `queries > limit → draw`. The parameter *is* the threshold: a game ends at the first drive-step check after its query count crosses the parameter value. There is no trigger distinct from the parameter to state.

### 2.2 The trajectory count is not the query count — proven, not assumed

The corpus does carry one per-game count that might be mistaken for it: the trajectory rows (`traj_w*.jsonl`, one logged decision record per row; keys `action_index, branch, decision, game, player, state`). It is a different quantity, and the records prove it:

- The 421 decision-capped games ended, by construction of line 367, with query counts **above 3,000**.
- Their trajectory-row counts are **1,501–2,245 (median 1,643) — every one of the 421 at or below 3,000**.

So the logged-decision count runs at roughly half the query count on exactly the games where the query count is known to have crossed 3,000. (The two increment sites in `policy_server.php` include queries that produce no logged decision record.) Any p99 read off trajectory counts would be a p99 of the wrong variable. For the record, that wrong variable's decided-games p99 is 773 (mean 486.0, median 492, max 1,106) — tabled here only so nobody has to wonder whether it was checked; **it is not used**.

### 2.3 The measurement proposed (R1's fallback)

R1: *"If the corpus rows carry a decision count, read it from them. If they don't, state that, and the registration proposes how to measure it."* They don't (§2.1). Proposed:

- **One-field code change:** add `"queries" => intval($GLOBALS["simPolicyQueries"])` to `PlayOneGame`'s result array in `play_game.php` (the global is live at result construction; the same value `policy_server.php:93` already exposes). The change is confined to a scratch tree; it alters no decision, cap, or scoring behavior — it persists a counter the engine already maintains.
- **One mirror re-run:** a heuristic-vs-heuristic Gravy mirror batch through the corpus driver in that tree, yielding per-game query counts in the result rows, from which the decided games' query p99 is read exactly as §1 read the turns p99, and H′ (§3) becomes computable in full.
- **Size and cost, as data for the ruling:** the full 2,400 games reproduces the calibration's basis exactly; `mirror_self`'s share of the stage-1 re-run (10h31m for 4,650 games across three batches) prices it at roughly 5 hours of box time. A smaller batch prices proportionally and widens the p99's sampling error; the size is part of what the ruling fixes.
- Per the standing rule for code changes that feed a run (and the ac725a5 reply's own step-3 precedent), **the change comes back for review before any run**, and the run needs Joe's go. Nothing in this section is a launch request.

## 3. H′ (R2) — fails on the turn component alone

**Definition (R2):** H′ is the mirror's capped share under the re-specified caps, counting every cap reason, computed from the mirror's records. A corpus game counts toward H′ if it would cap under the new rules: its recorded trajectory crossed the new threshold while still undecided. By the calibration's counting convention (a game whose recorded `turns` reaches the trigger was undecided at the trigger and ends capped there), the **turn component** is the share of rows with `turns ≥ 62`:

| Component (turns ≥ 62, trigger of §1) | Games | Share of 2,400 |
|---|---|---|
| Decided in the corpus (ended at turns 62–80) | 29 | |
| Turn-capped in the corpus (recorded turns 725–735) | 58 | |
| Decision-capped in the corpus (**all 421** recorded turns ≥ 62; median end-turn 142, mean 224.8) | 421 | |
| **Turn component of H′** | **508** | **0.2117, Wilson95 [0.1958, 0.2285]** |

**This is a lower bound on H′, and it already breaches the line.** The remaining 1,892 games (turns < 62) could only add a decision component — a game among them whose query count crosses the new decision threshold before turn 62 — and that component is not computable from the records (§2). So H′ ≥ 0.2117 > 0.10 **for any decision-cap setting whatsoever**: the 508 are games that were still undecided when their turn counter reached 62, and under a 62 trigger they end there no matter what the decision cap is. (This also retro-explains the reply's own sketch: its "roughly 1% above a 62-turn trigger" is the 29 decided games — 1.2% of 2,400. The 421 decision-capped games were counted there as the decision cap's problem, fixable by raising it; on the records, they are long games first — every one of them ran past turn 62, most far past it — so under a 62 trigger they are the turn cap's count, not the decision cap's.)

**Why the mirror behaves this way (the distribution, as data):** Gravy heuristic games are bimodal. Decided games end by turn 80 (mean 37). The other ~20% are the population the code comment at `play_game.php:332` names — "pass-forever games (e.g. gravy:gravy mirrors)" — running to a median of 142 turns and a mean of 285.9 among the corpus-capped. A trigger set from the *decided* games' p99 therefore sits far below the *whole mirror's* length distribution, and H′ — which R2 defines over the whole mirror — cannot come under 0.10 at that trigger.

**Alternative settings, tabled as data only** (share of all 2,400 rows with `turns ≥ T`; choosing any of these after seeing H′ is precisely the move R2 reserves to a new ruling — none is proposed):

| Turn trigger T | Share ≥ T | | All-games turns percentile | Value |
|---|---|---|---|---|
| 62 (the p99 setting) | 0.2117 | | p90 | 143 |
| 80 | 0.2004 | | p92.5 | 190 |
| 100 | 0.1996 | | p95 | 327 |
| 142 | 0.1158 | | p97.5 | 720 |
| 160 | 0.0887 | | | |
| 200 | 0.0642 | | | |

The share stays at ≈ 0.20 until the trigger passes the decided population entirely (~turn 100) and declines slowly through the pass-forever tail; it first falls below 0.10 between triggers 142 and 160.

**Disposition under R2:** the p99-based setting does not reach H′ ≤ 0.10 — it cannot, on the turn component — so **no re-specified gate is registrable from this package**. The registration stops here and returns to Claude and Joe with two questions: **(i)** may the turn setting be re-based on a different, stated-in-advance property of the mirror (with the table above as the data such a ruling would be made from), and **(ii)** is the §2.3 measurement (query-count capture + mirror re-run) approved as the route to the decision cap. §4 specifies the re-gate conditionally, so that if both are answered, the only missing values are the two caps themselves.

## 4. The re-gate (R3) — specified conditionally; not registered

Everything except the decision cap's value is specifiable now. This section is the registration text *as it would read* once §3's questions are answered; it registers nothing by itself.

- **The anchor, unchanged.** `gravy_bc/bc3_out/bc3_policy.pt`, sha256 **1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288**. **Hash linkage (the ac725a5 §4 item 3, discharged):** `gravy_bc/manifests/stage2_manifest.txt` records the same sha256 for the anchor (`anchor: gravy_bc/bc3_out/bc3_policy.pt / sha256 1e6e3906caa04ac7…48eac288`), verified against the file at stage 2 and re-read for this draft.
- **Form:** 400 seat-balanced games through `rl/eval.py`, anchor vs heuristic, Gravy mirror — the stage-2 gate's two invocations (`/tmp/r7launch/run_stage2_gate.sh`: halves A/B, `--learner-deck a` / `b`, 200 games each, workdirs `gravy_bc/anchor_gate_a` / `_b`, fresh workdirs for the re-gate), **with exactly these deltas:**
  - `--max-turns 87` added to both `eval.py` calls (parameter 87 ⇐ trigger 62, §1). `eval.py` exports it as `TCG_MAX_TURNS` to both the policy server (line 167) and the php process (line 185).
  - `TCG_MAX_DECISIONS = <value from the §2.3 measurement, once ruled and taken>` set in the launch environment. `eval.py` has **no** decision-cap argument; both of its subprocess environments start from `os.environ` (server env built at lines ~152–167, php env at ~178–185) and neither overrides `TCG_MAX_DECISIONS`, so the value rides the inherited environment into `play_game.php:344` unchanged. No code change is needed for either cap.
- **Fresh games, concretely.** `eval.py` takes no seed argument and the gate passes none. In `play_game.php`, each game's shuffle seed is drawn per game from `random_int(1, PHP_INT_MAX)` (line 411; the fixed-seed path applies only to single-game runs), and each game's id is drawn independently in `SetupGame` as a 9-digit `random_int(100000000, 999999999)` (line 156). The stage-2 gate's 400 ids stand in `gravy_bc/anchor_gate_{a,b}/traj/games_meta.jsonl` and in the registry under tag `gravy_anchor_gate_eval`. The re-gate's ids are fresh random draws from the same 9×10⁸ space; disjointness is not assumed from freshness but **verified**: before the read is used, the re-gate's id set (from its own `games_meta.jsonl`) is intersected with the full do-not-train registry (3,476 games at the stage-2 gate, plus the §6 merge when it lands) and **0 collisions is a validity condition of the read** (the chance expectation is ≈ 400 × 3,900 / 9×10⁸ ≈ 0.002 games). Any collision is reported in the run manifest with its disposition before the read is used.
- **Scoring and line, unchanged (R3):** capped games score as non-wins; the read is against the **0.40 line**, unchanged; the run is void unless each workdir's server log shows the anchor loaded with `fallbacks = 0` throughout; the re-gate's ids are registered eval-only **before the read is used**.
- **Clearance semantics:** a re-gate read **≥ 0.40** sets `GRAVY_STAGE2_CLEARED` under the future approved registration, and the stage-3 stack then proceeds under its existing approval (ba4e9c97) with Joe's per-stage go and the floors at **0.30** as registered. A read **< 0.40** leaves the stop standing as the finding, with path (c) — a recipe change, as its own registration — the only remaining continuation.

## 5. Reporting and cost (R4)

**Capped shares, side by side** (the presentation R4 and the ac725a5 reply require of any re-gate result; the re-specified column is this draft's evidence, not a run):

| Instrument | On Fai (mirror) | On Gravy (mirror / anchor) |
|---|---|---|
| Fai-era instrument (turn parameter 60 / trigger 35; decisions 3,000) | **0 of 333** capped (BC3 gate records) | mirror H = **0.6721**; anchor gate **0.72** capped |
| Re-specified instrument (trigger 62 / parameter 87; decisions per §2.3) | — | H′ ≥ **0.2117** (turn component alone, §3) — **fails the ≤ 0.10 standard**; a run re-gate's own capped share would be reported here |

**Wall-time estimate for the 400 games (had the gate been registrable), from the mirror's distribution and the stage-2 gate's measured pace:**

- Stage-2 gate, measured: gate log timestamps 03:22:24 → 03:41:30 EDT = **19m06s for 400 games** at the anchor gate's mean of 33.30 recorded turns (both halves at trigger 35).
- Under a 62 trigger, games run toward their natural lengths. Scaling the measured pace by mean game length, with the mirror as the length proxy: mean of min(turns, 62) = **36.97** over decided games → 19.1 × 36.97/33.30 ≈ **21 min**; = **41.97** over all 2,400 mirror games (the long tail truncated at the trigger) → 19.1 × 41.97/33.30 ≈ **24 min**.
- **Estimate: ≈ 25 minutes for the 400 games**, stated as an estimate from length-scaling only. Caveats: the anchor pairing's natural game lengths are not the mirror's (the anchor's games were still undecided at the 35 trigger in 72% of cases; where they land under 62 is what the re-gate would measure), and per-turn cost is not exactly constant — query load per turn grows in long games. For scale: Fai's 400-game gates ran at mean ≈ 15 turns; Gravy games at natural length run roughly 2.5× Fai's, which is the R4 comparability cost in concrete terms.

## 6. Open items discharged in text

- **Registry durability (ac725a5 §4 item 2).** The live registry is `/tmp/harvest/do_not_train_registry.json` — on the box's 20G tmpfs, the same filesystem whose exhaustion aborted stage 1's first launch. Persistent copies stand at **`/home/joe/tcg/registry-vault/`**: `do_not_train_registry-20261022.json`, sha256 **706fa3e969cd9325ce3e0c6fd585c6bac37cc29b6ba6bb2afa1e67469e9b0f0d** (the live registry as of the stage-2 gate registration, 3,476 games), and `do_not_train_registry.bak-20261022-034459.json`, sha256 **39fed3f44b5fb66ecc7622c18d4fc52927b325d799f8147695b3484321d66108** (the pre-gate backup, 3,076 games). The merge of the 319 recovered loose eval-only ids (claude-reply-ac725a5 §4 item 1) is proceeding in parallel with this draft; its after-hash rides in the next run manifest, and the vault copies are refreshed at that merge.
- **Anchor hash linkage (ac725a5 §4 item 3).** Discharged in §4: the stage-2 manifest records sha256 `1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288` for `gravy_bc/bc3_out/bc3_policy.pt` — the value R3 fixes the re-gate to.

---

**What this draft asks:** a ruling on §3's two questions — (i) whether the turn setting may be re-based, and on what stated-in-advance property of the mirror; (ii) whether the §2.3 measurement is the approved route to the decision cap. On both answers, §4's conditional text plus the two cap values complete the registration. Until then, **the stop stands and no re-gate exists to launch.**
