# Round 7 — hero-transfer package (DESIGN DRAFT): the Fai pipeline, replicated on Gravy Bones

**Parent:** 997c50c1f2914acad037e5bc09af214d263015de (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round6/claude-reply-3e2f6f1.md` §3 item 1 — "Run the same pipeline (labeler, teacher, gate) on a second hero, to find out which parts are hero-agnostic."
**Status: DESIGN DRAFT for review. Nothing launches on this package.** It registers the question, the design, the costs, and two flagged decisions (§5, §4.3) for Claude's review and Joe's ratification. A follow-on build package (code + fleet registration, scoped in §7) comes after that review, under the standing measurement-build rule: plan and code approved by Claude, launched sha == approved sha, Joe's go in chat.

**Decision flags in this draft (both need explicit ratification — neither is buried):**
- **Flag 1 (§5):** the (b) featurizer correction. Claude's closure defers it to "the next training run's registration." This package's BC/PPO stages *are* a training run. Recommendation: train Gravy on the **current** featurizer; the correction debuts in the distillation run instead. Reasoning in §5.
- **Flag 2 (§4.3):** the canonical suite inside the PPO stage is Fai-specific by construction. Recommendation: run the Gravy PPO **without** the suite gate (KL budget, spot-gates, and heartbeat retained), the deviation named. Reasoning in §4.3.

---

## 1. The question and the design principle

The project's stated goal is a hero-**independent** player. Everything measured so far is Fai: the teacher converts against the heuristic (+0.2525) and against BC3 at a 5.3% dose (+0.2050), and neither number says anything about a second hero. This package designs the minimal faithful replication of the Fai pipeline on **Gravy Bones**, mirror matches on `decks/nats2026_eriksen_gravy_60.txt` (70 tokens: hero `gravy_bones_shipwrecked_looter` + 9 equipment + 60 cards; 37 unique card ids; sha256 `b8b41390c5420ab8…`), in the same stages in the same order:

1. heuristic self-play corpora + behavior cloning to a BC anchor (the BC3 recipe);
2. gated PPO from the BC anchor to a raw policy checkpoint (the `fai_ppo_bc3b` configuration);
3. the teacher, identically configured, over that raw policy;
4. a gate fleet against the heuristic with the Fai gate's registered bands and the same impeachment audit (L1/L2/L3).

**Design principle:** change only what the hero change forces. Every stage below states what is forced, what is a free choice (and how this draft chooses), and what it costs — costed from the Fai run's actual records, not estimates of convenience. Where a stage can be shortened without changing what the test measures, the shortening is registered in place; where it cannot, the cost stands.

A note on the opponent: the gate is against the **heuristic** (the vendor Talishar AI) playing the same Gravy deck in mirror, exactly as the Fai gate's heuristic played the Fai deck. The heuristic demonstrably plays Gravy — the Fai corpus's cross batch is 750 heuristic Fai-vs-Gravy games (283,638 records) — but its Gravy strength is whatever it is; the gate measures the teacher-vs-raw delta against it, and the delta is the registered primary (§6), not the absolute level.

## 2. The baseline problem — inventory, decided from evidence

**There is no Gravy policy in the current lineage.** Old Gravy runs exist (`rl_out/gravy_b003_long`, `gravy_sweep_b*`, `gravy_baseline_20261010`, from the October 10–14 block-shaping era), but their checkpoints are the v2 format — verified by direct load: `rl_out/gravy_b003_long/ckpt_v40.pt` keys are `[version, model, vocab]`, `arch = None`, vocab size 512. The v3 serving path asserts `arch == "v3"` (the same wall BC2 hit in round 4), so none of them can serve as the gate's raw arm, and all of them predate the corrected evaluation gauge (their results were retracted with that era's). **The raw arm must be trained by this pipeline.** That is not a detour — stages 1–2 are the pipeline whose transfer is being tested.

**The representation mostly already covers Gravy.** The card vocabulary (`bc2_out/card_vocab.json`, 379 entries, sha256 `3592bf44196bf4d0…`) was built from corpora that included the Fai-vs-Gravy cross batch, so Gravy's cards entered it then. Checked id-by-id against both deck files:

| Deck | Unique ids | In vocab | Missing |
|---|---|---|---|
| Fai (control) | 34 | 34 | — |
| Gravy | 37 | 36 | `nullrune_hood` (equipment, head) |

**What happens to an out-of-vocab card today:** in the v3 slot encoder, `_slot_index` is `vocab.get(card_id, empty_idx)` (`bc_features_v3.py:41–44`) — an unknown id maps **silently** to the EMPTY slot index. No crash; a quiet mis-encoding if the card ever occupies a slot position. `nullrune_hood` is equipment and does not enter hand/arsenal/opponent-exposed slots in ordinary play, and the base features hash card *names* (md5-seeded projection, `bc_features_v2.py:23–35`), so the base featurization handles any id. The hazard is the silence, not this one card: the fix registered in stage 0 is an append-only vocab extension (Fai indices untouched), with the run's vocab carried in its checkpoints exactly as the Fai lineage carries its own.

**The featurizer is deck-derived, with one exception.** The state-v3 representation is: the v2 base (97 dims — zone aggregates over the generic zone list `['DQ', 'Hand', 'Character', 'Arsenal', 'Banish', 'Item', 'Ally']`, `bc_features_v2.py:20`, hashed card multisets per zone group, and exact deck scalars computed from the state's deck counts), plus 9 own slots and 6 opponent exposed slots indexed through the vocab. Nothing in it names a hero; the same code on the Gravy deck is the faithful transfer, and zones that were structurally empty for Fai (Ally above all — the Eriksen deck runs four ally types) simply carry content for Gravy. The one exception:

- `bc_features_v2.py:123` — `f[base + 7] = int(dc.get('phoenix_flame_red', 0)) / 3.0`: one base channel is a **named Fai-deck card** (Phoenix Flame copies remaining in deck). For Gravy the channel reads a card that is never in the deck: permanently 0. **Registered choice: keep the code exactly as is.** The channel is part of the representation whose transfer is being tested; re-pointing it at a Gravy card would change the representation mid-test. A Gravy-trained net sees a constant-0 input there and learns around it, the mirror image of Fai's ally channels sitting empty. This is the honest like-for-like.

## 3. Hero-specific machinery audit

Greps run over the serving/training code paths (O-tree patched lineage for the PHP side; box sim root for the Python side) for hero names, weapon ids, talent checks, and named cards (`phoenix`, `emberblade`, `searing`, `draconic`, `ninja`, `fai`):

| Component | Hits | Class |
|---|---|---|
| `featurize.php` (state builder, canary) | Phoenix mentions are comments only (the canary's double-homing note, :120–130; :173 in `search.php` likewise) | **generic** — card-id strings throughout; deck counts via `SimV1_DeckCards` (store), both heroes alike |
| `policy_v1.php` (heuristic scores / BC labels) | no named-card logic | **generic** — labels are `argmax(v1_score)` for any deck |
| `search.php` (teacher Decide + labeler) | no named-card logic; teacher parameters are code constants — `$K = 25` (:928), the overturn rule "prior pick exceeds 1.5 paired SE, n ≥ 20 shared finished worlds" (:804) | **generic** — identical configuration carries over by using the identical file |
| `policy_server.php` (bridge) | none | **generic** |
| `bc_features_v2.py` | `phoenix_flame_red` deck scalar (:123) | **Fai-deck-hardcoded** — one channel; registered treatment in §2 (keep, dead for Gravy) |
| `bc_features_v3.py` | none; slots are vocab indices sorted by card id, EMPTY = `len(vocab)` | **parameterized** (by the run's vocab) |
| `bc3_build_data.py` / `bc3_train.py` | corpora paths and `--vocab` are arguments | **parameterized** |
| `rl/trainer_v4.py` (PPO) | decks passed as `--learner-deck` (:276); anchor/suite/probe are run configuration | **parameterized**, except the suite (Flag 2) |
| Canonical suite (50 positions, BC3 baseline 46/50) | positions mined from Fai games; "known-correct" answers are Fai-strategy judgments | **Fai-specific by construction** — Flag 2, §4.3 |
| Vendor heuristic (Talishar AI) | plays any deck the engine deals; 750 Gravy cross games on record | **generic** |
| Gravy's distinguishing mechanics — allies, Gold/treasure tokens | engine mechanics (vendor snapshot 3da4648); allies featurize through the existing Ally zone; token permanents through the generic board zones | **generic code, new content** — the representation has the slots; the distribution is new. That is the transfer question, not a blocker |

**Audit headline:** exactly one Fai-hardcoded line in the numerical path (the Phoenix Flame scalar), one Fai-specific instrument (the suite), and one missing vocab entry. Everything else the pipeline touches is deck-parameterized or hero-blind. The build risk is therefore low; the open risk is empirical — whether the *learned* pipeline (data → clone → PPO → teacher) produces the same shape of gain on a slower, board-based hero whose games the heuristic plays differently.

## 4. The staged design

Each stage: inputs · code state · cost (Fai-measured) · registration needs.

### 4.0 Stage 0 — vocab extension and deck registration

- **Inputs:** `bc2_out/card_vocab.json` (379) + the Gravy deck's id list.
- **Work:** append any missing Gravy-deck ids (today: `nullrune_hood` only) at the end, preserving every existing index; save as the run's vocab artifact with its hash; register the deck file hash (`b8b41390c5420ab8…`). A build test asserts every deck id (both decks) resolves to a non-EMPTY slot index under the run vocab — the loud version of the silent fallback.
- **Code state:** to-build (a short script + assertion), scoped in §7.
- **Cost:** minutes.

### 4.1 Stage 1 — corpora generation (heuristic self-play + DAgger)

The BC3 corpus recipe, regenerated fresh under uniform provenance (the existing cross records are *not* reused: they predate the run, and mixing provenance inside a measurement's training data invites a format question the build would have to answer anyway; regeneration costs under an hour at the measured rate):

| Batch | Fai corpus (as trained on) | Gravy design |
|---|---|---|
| mirror self-play (heuristic mirror) | 922,107 records (rescued subset of a 5,183-game batch) | heuristic Gravy mirror, ~2,400 games, target ≈ 920k records |
| cross (heuristic, vs the other hero) | 283,638 records / 750 games Fai-vs-Gravy | 750 games Gravy-vs-Fai, ≈ 284k records |
| DAgger (clone-driven mirror, heuristic labels) | 562,753 records / 1,500 games, driven by bc v1 | 1,500 games driven by the pass-1 Gravy BC (below), ≈ 563k records |
| **Total** | **1,768,498 records / 4,646 games** | **≈ 1.77M records / ≈ 4,650 games** |

- **The two-pass BC (a forced deviation, registered):** Fai's DAgger batch was driven by bc v1, the previous generation's clone. No previous Gravy clone exists. The faithful analog: train a **pass-1 BC** on mirror+cross only (stage 2's recipe, a ~7-minute job), drive the DAgger batch with it through the bridge, then re-featurize all three batches and train the real anchor on the full corpus. The pass-1 net is scaffolding — never gated, never the raw arm.
- **Generation discipline (from the October 15 lessons, binding):** the fixed `bc2_gen.sh` (worker copies include `bc_train.py` + `bc_features.py`), absolute deck paths everywhere, completion read from per-batch record counts — never from a DONE file.
- **Code state:** exists (generator + driver), deck arguments swapped; worker-copy fix already in the script.
- **Cost:** full-fidelity raw-state logging measured at ~14 games/min across 6 workers → ≈ 5.5–6 h for ~4,650 games.
- **Registry:** corpus games are the training set by design (not eval games); the do-not-train registry discipline applies to every *evaluation* game from stage 2 onward.

### 4.2 Stage 2 — re-featurization, BC anchor, anchor gate

- **Re-featurize** all corpora with `bc3_build_data.py` under the run vocab (state v3, outcome join from final life totals, truncated games excluded from value training only — the BC3 rules verbatim). Fai cost: under an hour for 1.77M records on one process.
- **Train the anchor** with `bc3_train.py`'s recipe verbatim: policy cross-entropy, Adam lr 3e-4, batch 1024, 10 epochs (Fai: ~31 s/epoch); then the value head alone, trunk frozen, 3 epochs on raw undiscounted outcomes (~28 s/epoch). Total ≈ 7 min of GPU.
- **Anchor gate (diagnostic, registered as report-only):** 400 seat-balanced games, anchor vs heuristic, Gravy mirror, server-log-verified (learner loaded, fallbacks=0) — the BC3-standard protocol. Fai's anchor read 0.450 (150/333 verified). The Gravy anchor's read is a per-stage transfer diagnostic reported beside it; it gates nothing by itself, but a clone that cannot approach its teacher (say, point estimate under ~0.40) is reported as a stage-2 finding before PPO time is spent — the same report-at-the-gate discipline the Fai build used.
- **Code state:** exists verbatim; `--vocab` and corpora arguments change.
- **Cost:** ≈ 1.5 h including the gate.

### 4.3 Stage 3 — gated PPO to the raw policy

- **Configuration:** `rl/trainer_v4.py` with the `fai_ppo_bc3b_20261016` configuration transcribed verbatim — frozen-anchor forward-KL budget 0.125 (acceptance can never re-anchor), LR 3e-5, 2 epochs, batch 65,536, spot-gates every 5 versions (50 games, floor 0.30, fail = revert to last spot-verified + halt), trailing-150-game heartbeat (floor 0.30), LR halving on rejections, 10-rejection halt — with decks swapped to the Gravy mirror and the anchor swapped to the stage-2 BC. The build package must diff its launch configuration against the 3b run's recorded one and show the diff (decks + anchor + Flag-2 suite line only).
- **Flag 2 — the canonical suite.** The 3b configuration includes a suite gate (BC3 baseline 46/50) on 50 positions mined from Fai games, whose reference answers are Fai-strategy judgments. A Gravy policy scored on Fai positions measures the wrong thing; a Gravy suite does not exist. Options: **(a)** run without the suite gate, KL/spot/heartbeat retained — the suite is the weakest of the run's gates on the Fai record itself (in Phase 3 run 1 it held 46/50 for a policy winning zero games; the behavioral gates are the ones that caught real failures); **(b)** mine a 50-position Gravy suite first (teacher-agreement-filtered, per the Phase 1d recipe) — roughly a day of mining and verification, and it inserts a brand-new unvalidated instrument as a halting gate inside the transfer test. **Recommendation: (a)**, with the deviation named in the run's manifest and results. Ratification requested.
- **Checkpoint selection (mirrors how v15 was chosen):** the raw arm is the first spot-verified checkpoint that passes a formal 400-game seat-balanced gate vs the heuristic at the BC standard (the rule that selected `ckpt_v15`, which read 202/400 = 0.505). If the run halts with no checkpoint passing, that is reported as the stage-3 transfer finding — the teacher stage does not run on an ungated policy.
- **Cost:** Fai's 3b run reached v35 in 46 min of wall-clock (4 rollout workers, 13,956 games); plus the selection gate ≈ 30–45 min. Budget ≈ 1.5 h.

### 4.4 Stage 4 — the teacher and the gate fleet

- **Teacher configuration: identical.** The same patched lineage (`search.php` with the abort-logging patch on the O-tree base), the same constants (k=25 worlds; candidates top-3 + prior ≥ 0.10, cap 4; continuation `va`; overturn at margin > 1.5 paired SE with ≥ 20 shared finished worlds; R17 root state), the same bridge and eval plumbing, raw arm = the stage-3 checkpoint, opponent = heuristic via `TCG_OPP_MIX`, mirror Gravy on the Eriksen deck.
- **Fleet design: the Fai gate's, verbatim in structure.** 200 paired seeds × both seats × both arms = 800 games, 4 chunks concurrent, fresh seed range **8001–8200** (outside every range used to date: fleets 1001–1200 / 2001–2200, probes 3000-series / 4001–4014 / 5001–5010, census 6001–6040, smokes 7001–7002; the build package confirms no registry collision). Pre-gate first (trace-equality discipline, 20 units), opponent-is-live control, and a **contention probe on Gravy teacher games** to set the fleet timeout exactly as the O build did (Fai teacher games ran ~372 s; Gravy's board states may run longer — the timeout comes from the probe, not from Fai's number).
- **Standing fleet discipline:** G8 shared-memory sweep immediately before the fleet (segments stood at 2,191 at draft time; the 3,600 operator stop applies), production server hash before == after, chunk manifests `assert_ok`, registry merge of all 800 game ids as eval-only **before** analysis.
- **Cost:** Fai's gate fleet ran 10.7 h wall (17:01 → ~03:40) at 4-way concurrency. Gravy's is registered at the same figure, explicitly provisional on the contention probe.

### 4.5 Stage 5 — the impeachment audit (standard, not post-hoc)

L1 (overturn census: prior/overturn-pick unanimity against the 50% fail line, `se_diff == 0` cases read individually), L2 (40-game trace-verified replay on the production server), L3 (fresh-world relabeling of every overturn, continuation `va`, per-game attribution against the Δ/2 boundary) — the same scripts and the same standards as the Fai gate and the O measurement. Plus the G3-style first-divergence audit over the fleet traces and the G5 calibration shape, reported with the primary. Fai's L3 ran ≈ 2–4 h across 4 shards (≈ 910 jobs at the gate's overturn count; Gravy's job count follows its own overturn rate).

## 5. Flag 1 — the (b) featurizer correction: surfaced, with a recommendation

Claude's round-6 closure: item (b) is closed for the bridge population, the blind spot is "immaterial to play at this sample's resolution," and **the featurizer correction (deck counts from the view, so the whole state comes from one source) carries forward into the next training run's registration**, so training and serving change together. This package's stages 1–3 *are* a training run — the deferred decision lands here, and it trades two registered commitments against each other:

- **Option A — train Gravy on the current featurizer (store deck counts).** The transfer read stays clean: one variable differs from the Fai run (the hero), so the Gravy Δ reads against Fai's +0.2525 as a pipeline comparison. The correction's known behavioral weight on the current lineage is nil at play (pick-flip: 0 flips in 163, prior shifts ≤ 0.0024), so omitting it does not obviously handicap the Gravy nets. The correction then debuts in the **distillation run** (Claude's §3 item 2) — which is also a training run, on the Fai lineage where (b) was actually measured, and where its effect can be isolated as that run's own variable.
- **Option B — train Gravy with the correction applied.** Honors the closure's letter at the first opportunity. Costs the transfer read its attribution: any Gravy-vs-Fai Δ difference becomes hero *and/or* featurizer, inseparable without a second Gravy gate under the other featurizer — i.e., roughly doubling the expensive stage (~11 h fleet + audit) to recover the attribution, or leaving the project's headline question confounded.

**Recommendation: Option A.** The correction is not lost — it is scheduled into the distillation run's registration, where it belongs mechanically (that run retrains the Fai-lineage policy the blind spot was measured on) — and the transfer test keeps the one-variable discipline every prior round has enforced. **This recommendation needs Claude's and Joe's explicit ratification**, because it re-times a commitment Claude registered; if either prefers B, the package's §6 interpretation bands must be rewritten before any build, since the comparative read changes meaning.

## 6. Registered readings

**Primary (per gate):** the Gravy gate's pooled Δ (teacher vs its own raw policy, both vs the heuristic, paired seeds), read under the Fai gate's band table, verbatim:

| Result | Read |
|---|---|
| Δ ≥ +0.05 with CI lower bound > 0 | converts |
| Lower bound > 0 but Δ < +0.05 | real but small |
| CI includes 0 with upper bound < +0.10 | the projection overstated conversion |
| Δ > +0.20 | **impeach before reading** |

Plus the standing stops: any G3 machinery defect stops the read; teacher timeouts > 2% make the gate inconclusive whatever Δ says; canary refusals > 2% per arm-seat breach coverage; a fleet overturn rate well above ~5% impeaches the margin rule before Δ is read; the G5 calibration shape is reported with the result, and the void-gate pattern impeaches the run.

**Transfer interpretation (registered in advance, comparative):** the Gravy Δ is reported beside Fai's +0.2525 [+0.2075, +0.2975] with both intervals, and read as:

- **Transfers:** the Gravy gate converts with a point estimate ≥ +0.15 — the pipeline's gain reproduces at a comparable magnitude on a mechanically dissimilar hero.
- **Partial transfer:** the Gravy gate converts below +0.15, or reads "real but small" — the pipeline works but the gain shrinks; the per-stage diagnostics (§4.2 anchor read, stage-3 selection record, fleet overturn rate vs the Fai teacher's ≈ 8.5% of contested decisions) name where it shrank, and the follow-on investigates there.
- **Does not transfer:** the Gravy gate fails to convert (CI includes 0), or a stage stalls as registered (anchor gate collapse, no PPO checkpoint passing) — the Fai result was hero-specific. Stated consequence, in advance: the teacher's edge would then read as riding on Fai-mirror structure (an aggro mirror against a heuristic whose Fai play the pipeline has thoroughly mapped), the hero-independent thesis reverts to unproven, and the distillation line should be re-aimed per-hero or hero-conditioned rather than hero-blind.

**Cost comparison (reported with the results):** wall-clock per stage, Gravy actuals beside the Fai figures in §4, including teacher seconds/game on Gravy vs Fai's ~372 s — the cost question (Claude's §3 item 2) gets its second data point from this run whether or not distillation follows.

## 7. Staging — what the follow-on build package must contain

This draft is design-only. The build package (its own commit, reviewed before anything launches) contains:

1. Stage-0 vocab script + the deck/vocab assertion test, with hashes.
2. The corpus generation driver as launched (fixed `bc2_gen.sh`, absolute paths), batch record-count targets, and the pass-1/pass-2 BC sequencing.
3. Training manifests for the anchor and the PPO run — the PPO launch configuration **diffed against `fai_ppo_bc3b_20261016`'s recorded configuration**, the diff limited to decks, anchor, run directory, and the Flag-2 suite line.
4. The gate fleet package proper: tree build (patched lineage + abort patch), `run_gate`-equivalent for the Gravy deck and 8001–8200, pre-gate + contention probe + opponent-is-live control, timeout derivation, G8 sweep record, registry-merge step, and the analysis scripts (primary + L1/L2/L3 + first-divergence) with their file hashes.
5. Both flag decisions **as ratified**, restated in the build manifest — the build does not proceed on a flag the review left open.

Estimated build-package scope: small-to-moderate. No new machinery is designed anywhere in §4; the genuinely new code is the stage-0 vocab script and the fleet runner's deck/seed substitution. Everything else is configuration transcription with diffs shown — which is itself the transfer claim at the code level.

## 8. Standing constraints inherited

- Observation masking and the hidden-information fair-play canary are mandatory in every run (teacher, labeler, fleets); canary refusals are a coverage metric under the amended rule.
- Local Talishar only; never public queues.
- Measurement-build approval rule: plan **and** code approved by Claude before launch; launched sha == approved sha (rounds-only diff excepted); run manifests record both shas; Joe's go in chat launches, nothing else does.
- Do-not-train registry: every evaluation game (anchor gate, PPO formal gates, gate fleet, L-runs) is registered eval-only and merged before analysis; training corpora are the registered exception, generated for that purpose.
- Shared memory: G8 sweep before any fleet; 3,600 segments is the operator stop (2,191 resident at draft time).
- Every eval's own server log (weights-loaded line, fallbacks=0) is part of its result; a handoff summary is never evidence; decisive numbers are verified from primary records.

## 9. Build verification — inventory evidence

Every factual claim above, with its evidence:

- **Claude's ordering and the (b) deferral:** `rounds/round6/claude-reply-3e2f6f1.md` §2–§3 (committed; sha256 of the reply file recorded in commit 997c50c1's message).
- **Old Gravy checkpoints unusable:** direct `torch.load` of `rl_out/gravy_b003_long/ckpt_v40.pt` on the box — keys `[version, model, vocab]`, `arch = None`, vocab 512. (The v3 loader's `arch == "v3"` assertion is the round-4 record.)
- **Vocab coverage:** box-side comparison of `bc2_out/card_vocab.json` (379 entries) against the token lists of `decks/nats2026_eriksen_gravy_60.txt` and `decks/nats2026_ashlyn_fai_60.txt` — Gravy 36/37 (missing `nullrune_hood`), Fai 34/34.
- **Silent EMPTY fallback:** `bc_features_v3.py:41–44` (`vocab.get(card_id, empty_idx)`), read on the box (file sha256 `081402e8689c32b5…`).
- **Phoenix Flame channel:** `bc_features_v2.py:123`, read on the box (file sha256 `7f8fcd6ff12d0cad…`); generic zone list at `bc_features_v2.py:20`; name-hash projection at :23–35.
- **Teacher constants:** `/tmp/otree/search.php:928` (`$K = 25`), :804 (overturn rule); PHP-side greps for named cards returned comments only (`featurize.php:120–130`, `search.php:173`).
- **BC3 recipe and corpus:** `bc3_out/metrics.json` (1,768,498 records; val agreement 0.9519), `bc3_train.log` (policy epoch 31 s; value epochs 27–28 s; final val 0.9519/0.8845), `bc3_build_data.py` header (re-featurization + outcome join rules), day logs 2026-10-15/16 (corpus composition 922,107 + 283,638 + 562,753; generation rate ~14 games/min across 6 workers; the DONE-file and worker-copy lessons).
- **PPO configuration and cost:** `rl_out/fai_ppo_bc3b_20261016/status.json` (35 accepted / 4 rejected, KL budget 0.125, suite baseline 46, spot-gate halt at v35, 13,956 games) and the 2026-10-16 day log (launched 22:13, halted 22:59; trainer_v4 design: frozen anchor, spot-gates every 5 versions at 0.30, heartbeat floor 0.30). v15's formal gate 202/400 = 0.505 is the verified-numbers ledger figure.
- **Gate fleet cost and teacher pace:** round-3/round-4 packages (fleet 17:01 → ~03:40 ≈ 10.7 h; teacher 372.1 s/game vs raw 3.8 s — Claude's round-4 reply); Fai teacher overturn rate ≈ 8.5% from the O fleet's record (910 / 10,648 contested).
- **Deck artifact:** `decks/nats2026_eriksen_gravy_60.txt` sha256 `b8b41390c5420ab8…` (box, at draft time).
- **Segment count at draft time:** `ipcs -m | wc -l` = 2,191 (box, at draft time).

**Could NOT verify / not claimed:**
- Gravy teacher game pace — no Gravy teacher games have ever run; §4.4 registers the contention probe instead of a number.
- The Gravy anchor's and PPO's outcomes — nothing in §4 predicts them; the registered readings (§6) cover the outcomes rather than forecasting them.
- The heuristic's Gravy strength as a baseline level — the cross batch proves it plays Gravy end-to-end; its win-rate level is an output of stage 2's gate, not an input.
- `trainer_v4.py`'s full argument list was not re-transcribed for this draft; §7 makes the launch-config diff a build-package deliverable precisely so the transcription is reviewed there.
