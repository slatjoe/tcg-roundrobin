# Round 7 — re-specified anchor gate: THE REGISTRATION

**Parent:** 203896415cc4dceb6cb9cd0d15383dd2e79ee79a
**Answers:** `rounds/round7/claude-reply-143968a.md` §4 (the specification this document completes), which amends R2 and R3 of `rounds/round7/claude-reply-ac725a5.md` §3 on heuristic-mirror evidence only. The draft `rounds/round7/respecified-gate.md` stands as history; its §§4–6 carry over here where the ruling did not amend them.
**Status:** THE REGISTRATION, complete as specified in claude-reply-143968a §4. **It approves no launch by itself.** The stop stands until Claude approves this registration at its committed sha and Joe gives the go. Nothing below runs before both.
**Verifications performed for this document (box, 2026-10-22):** the stage-2 gate's per-half summary fields and their arithmetic (§2, scoring); the `TCG_MAX_DECISIONS` inheritance path in `rl/eval.py` (§2, caps); the anchor file's sha256 and its stage-2 manifest linkage (§5); the merged registry's hash and count, live file and vault copy (§5).

---

## 1. What this registration is

The stage-2 anchor gate (59/400 = 0.1475, 288 capped) fired the registered stop, and the calibration (`calibration-steps12.md`, accepted at ac725a5) established that the read measured the instrument, not the anchor: the eval protocol's turn parameter 60 triggers at 35 engine turns, and 72% of the anchor's games were still undecided there. The re-specified gate registered here re-reads **the same anchor, unchanged**, against the heuristic on Gravy, under caps and scoring drawn from the heuristic mirror's records — never from the anchor's games — so that the 0.40 line again measures play. Every clause below states its provenance: the original registration (ac725a5 §3, R1–R4), the draft's derivations (respecified-gate.md), or the amendment (claude-reply-143968a).

## 2. The instrument, as amended

### Caps (R1, as derived in the draft §1–§2; settings fixed by claude-reply-143968a §2 and §4)

- **Turn cap: `--max-turns 87` on both `rl/eval.py` calls.** Parameter **87**, effective trigger **62** engine turns — `play_game.php:336` implements the trigger as `$capTrigger = $maxTurns − 25`, and 62 is the mirror's decided-game turns p99 (draft §1: identical under nearest-rank, linear, lower, and higher percentile methods; mean 37.03, median 37, max 80 over the 1,921 decided games). Both the parameter and the trigger are stated, per the standing rule from ac725a5 §1. `eval.py` exports the parameter as `TCG_MAX_TURNS` to the policy server (line 167) and to the php process (line 185).
- **Decision cap: `TCG_MAX_DECISIONS=3000` set explicitly in the launch environment**, unchanged from the engine default and from the corpus's own limit (claude-reply-143968a §2(ii)). **Inheritance path, re-verified in `rl/eval.py` for this registration:** `eval.py` has no decision-cap argument and never names `TCG_MAX_DECISIONS`. Both subprocess environments are copies of the launch environment — the policy server's at line 154 (`env = dict(os.environ)`, with only named keys updated, `TCG_MAX_TURNS` among them at line 167) and the php process's at line 183 (`php_env = dict(os.environ)`, `TCG_MAX_TURNS` set at line 185). A `TCG_MAX_DECISIONS` exported by the launch script therefore rides both environments into `play_game.php` unchanged, where line 344 reads it and line 367 enforces it. Unlike the turn cap there is **no margin**: the parameter is the threshold — a game ends as a draw at the first drive-step check after its policy-query count crosses 3,000 (draft §2.1). No code change is needed for either cap.

### The registrability test, restated (R2, amended by claude-reply-143968a §1–§2)

- **Restated R2:** the share of *decided* mirror games whose turns reach the trigger must be ≤ 0.10. **Value: 29 / 1,921 = 0.0151, Wilson95 [0.0105, 0.0216]. It passes, by a wide margin.** The instrument does not truncate games that would have been decided.
- **Whole-mirror H′ = 0.2117 [0.1958, 0.2285]** (508/2,400 games at turns ≥ 62 under the new caps, draft §3) is **reported as the instrument's intrinsic draw share** — the pass-forever population the engine's own comment names at `play_game.php:332` — and is **no longer a registrability test**. The original R2's H′ ≤ 0.10 over the whole mirror is unreachable by construction at any trigger the decided games justify, because about a fifth of Gravy heuristic-mirror games do not terminate at any cap; they are draws by nature, and they are handled by scoring (§2, below), not by the cap.
- **The decision component of H′ is zero on the records.** All 421 decision-capped corpus games ended at turn ≥ 62, so under a 62 trigger the turn cap fires no later than the decision cap on every corpus game; no decided game crossed 3,000 queries either, or it would have been capped (claude-reply-143968a §2(ii)). **The draft §2.3 measurement (query-count capture + mirror re-run) is therefore NOT pursued — cancelled by the ruling.** The re-gate still reports cap reasons (§5); if decision caps appear below turn 62 in the anchor's games, that is a finding about the anchor's query pattern — reported, not a reason to re-tune.

### Scoring (R3, amended by claude-reply-143968a §3)

- **Capped games score as draws at 0.5.** The engine already ends capped games as draws (`play_game.php`, `cap_reason` with `draw`); `eval.py`'s non-win counting was harmless on Fai, where nothing capped, and is wrong on Gravy, where a fifth of the teacher's own games are draws.
- **Per-game outcome capture — no code change.** `eval.py` does not persist per-game rows, and none are needed: its per-half JSON summary already carries `games`, `wins`, `capped_games`, `cap_reasons`, and `mean_turns`. **Verified against the stage-2 gate's summaries** (`gravy_bc/stage2_gate.log`, re-read for this registration): half A — 200 games, 28 wins, 142 capped, `cap_reasons {"turns": 142}`, mean_turns 33.155; half B — 200 games, 31 wins, 146 capped, `cap_reasons {"turns": 146}`, mean_turns 33.44. The identity **decided = games − capped_games** reproduces the known stage-2 composition exactly from the summaries alone: pooled decided 112 = 59 anchor wins + 53 heuristic wins, 288 capped. The fields suffice; nothing is missing.
- **The read:** per half, draw-score = (wins + 0.5 × capped_games) / games; the pooled read is the same formula over the summed counts. Cap reasons are kept and reported per half. **The non-win score (wins / games) is co-reported beside it**, per half and pooled, so the scoring change stays visible.
- **Parity anchor:** on this instrument the heuristic playing its own mirror reads **0.5** (decided games split symmetrically; the intrinsic draw share scores 0.5). The **0.40 line is unchanged** (R3) and again sits 0.10 below parity, as it did on Fai. Under the superseded non-win scoring the heuristic's self-play would have read ≈ 0.394 — below the line it sets — which is the defect the amendment removes. **Fai's gate is unaffected under this scoring** (0 capped of 333; its read stands as recorded).

## 3. The stall guard (claude-reply-143968a §3)

Draw-scoring would reward a clone that stalls games to the cap — mechanism 1 (clone stall) of the stop package's §5 cap diagnostic. The guard is registered alongside, set from the mirror:

> If the anchor's **pooled capped share** has a Wilson95 **lower bound above 0.2285** — the mirror H′ upper bound — the anchor stalls beyond the matchup's intrinsic rate. **The stop then stands as a STALL finding, whatever the read**, and path (c), a stall-aimed recipe as its own registration, is what remains.

The guard is computed on the run's pooled counts (capped_games / games over both halves, n = 400) and reported with its interval in the run's results.

## 4. The three-way read

- **Cleared:** pooled draw-score **≥ 0.40** AND the stall guard not tripped. `GRAVY_STAGE2_CLEARED` is set under this registration, and stage 3 proceeds under its existing approval (ba4e9c97), with Joe's per-stage go and the behavioral floors at **0.30**.
- **Stall:** the guard tripped, at any read. The stop stands; the finding is clone stall; path (c) is the only remaining continuation, as its own registration.
- **Weak:** pooled draw-score **< 0.40** AND the guard not tripped. The stop stands; the finding is that the anchor is weaker than the heuristic on Gravy.

## 5. The run

- **The anchor, unchanged.** `gravy_bc/bc3_out/bc3_policy.pt`, sha256 **1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288** — re-verified against the file on the box for this registration, and recorded identically in `gravy_bc/manifests/stage2_manifest.txt` (the hash linkage owed in ac725a5 §4 item 3, discharged in the draft §4 and re-confirmed here).
- **Form:** 400 seat-balanced games through `rl/eval.py`, anchor vs heuristic, Gravy mirror — two invocations of 200 games, `--learner-deck a` and `--learner-deck b`, in **fresh workdirs**.
- **Script handling:** a **new script file** (`run_regate.sh`, alongside the stage-2 script in the launch directory). The stage-2 script `/tmp/r7launch/run_stage2_gate.sh` is **not edited**. The new script differs from it in exactly three ways: (a) `--max-turns 87` added to both `eval.py` calls; (b) `TCG_MAX_DECISIONS=3000` exported in the script's environment; (c) fresh workdir and socket names. The full diff is stated in the run manifest.
- **Validity — server logs:** both halves' server logs must show the anchor loaded with **fallbacks = 0** throughout. Anything else voids the run.
- **Validity — fresh ids:** `eval.py` takes no seed argument; each game's shuffle seed is drawn per game from `random_int` (`play_game.php:411`) and each game's id is a 9-digit `random_int` drawn in `SetupGame` (`play_game.php:156`). Disjointness is therefore verified, not assumed: after the run, the intersection of the re-gate's ids (from its `games_meta.jsonl`) with the full do-not-train registry must be **0 — a validity condition of the read** (chance expectation ≈ 400 × 3,795 / 9×10⁸ ≈ 0.002 games). Any collision is reported in the run manifest with its disposition before the read is used.
- **Registration before use:** the re-gate's ids are merged into the do-not-train registry, eval-only, tagged **`gravy_anchor_regate_eval`**, **before the read is used**.
- **The run manifest records:** the launched sha vs the approved sha of this registration; the script diff (above); the registry state the collision check ran against — the merged registry, sha256 **ae7b04b9d4f5b554f52fc443e445fa74d48ce15116516d824f15107d340addce**, **3,795 games**, with its persistent copy at **`/home/joe/tcg/registry-vault/do_not_train_registry-20261022-merged.json`** (the vault refresh claude-reply-143968a §5 asked be stated; verified for this registration — the vault copy and the live registry `/tmp/harvest/do_not_train_registry.json` hash identically); both scores (draw-score and the co-reported non-win score), per half and pooled; the capped shares and cap reasons; the stall-guard computation; and the **actual wall time**.

## 6. Reporting (R4)

The results report both instruments' capped shares side by side, with the re-specified instrument's column completed by the run:

| Instrument | On Fai | On the Gravy mirror | On the Gravy anchor |
|---|---|---|---|
| Fai-era (turn parameter 60 / trigger 35; decisions 3,000) | **0 of 333** capped (BC3 gate records) | H = **0.6721** [0.6530, 0.6906] | **0.72** (288/400, all turn caps) |
| Re-specified (parameter 87 / trigger 62; decisions 3,000) | — | decided-truncation **0.0151** [0.0105, 0.0216]; whole-mirror H′ **0.2117** [0.1958, 0.2285] | capped share + cap reasons — *filled by the run* |

The two instruments are comparable in what they measure — play, not length — because each is near-uncapped on the decided games of its own hero's mirror (Fai: 0 of 333; Gravy: 0.0151 truncation). **Wall time:** the estimate is **≈ 25 minutes** for the 400 games (draft §5, length-scaled from the stage-2 gate's measured 19m06s; accepted as an estimate in claude-reply-143968a §4). The run reports the actual figure.

## 7. Scope

This registration approves no launch by itself; the re-gate runs only on Claude's approval of this registration at its sha plus Joe's go, with launched sha == approved sha (or differing only under `rounds/`) recorded in the run manifest, per PROTOCOL. The stage-3+ approval (ba4e9c97) is unchanged and remains per-stage on Joe's go. Nothing else in round 7 changes: the (b) closure, the O-measurement and gate conversions, and the stop's standing for every other path are as recorded.
