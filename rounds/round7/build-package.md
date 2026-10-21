# Round 7 — hero-transfer BUILD package: the Fai pipeline, replicated on Gravy Bones (code + registrations)

**Parent:** 0ff9b16581b2e0c8fac494af25c44c4fd28cceec (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/transfer-package.md` (design, commit 3c466195, approved as the basis for this package), `rounds/round7/claude-reply-3c46619.md` (both flags ratified; corrections C1–C5 registered for this package), `rounds/round7/builder-note-ratification.md` (Joe's ratification of both flags, 2026-10-21).
**Status: BUILD PACKAGE for review. Nothing launches on this package.** Under the standing measurement-build rule, each stage launches only when (i) Claude has approved this package at its committed sha, (ii) Joe gives the go in chat, and (iii) the stage's launch manifest (template: `configs/launch_manifest_template.md`) records approved sha == launched sha modulo rounds-only diffs. What has run so far is disclosed in §9: scratch applications, the stage-0 tests in both directions, the trainer patch + logic test, syntax checks, and guard dry-runs. No games were played for this package.

**Package contents**

| File | Role |
|---|---|
| `build-package.md` | this build registration |
| `code/extend_vocab.py` | stage 0: append-only vocab extension |
| `code/test_vocab_assertion.py` | stage 0: the loud slot assertion |
| `code/gravy_corpus_driver.sh` | stage 1: corpora + pass-1 + DAgger driver |
| `code/patch_trainer_launch.py` | stage 3: builds the PPO launch copy of trainer_v4.py |
| `code/gravy_ppo_launch.sh` | stage 3: workers + trainer launcher (stage-2-stop guard) |
| `code/run_gravy_gate.sh` | stage 5: the gate fleet runner |
| `configs/ppo_config_diff.txt` | stage 3: the full configuration diff vs the 3b run |
| `configs/launch_manifest_template.md` | per-stage manifest incl. the Flag 1 amendment record |

**Ratified decisions carried in (restated, per design §7 item 5):**
- **Flag 1 — Option A (ratified by Claude §1 and by Joe):** the Gravy pipeline trains on the **current** featurizer (store deck counts). The (b) correction debuts in the distillation run. The re-timing is recorded as an **amendment to the round-6 closure** in the stage-1 launch manifest (template carries the amendment text) — not a silent change.
- **Flag 2 — option (a) (ratified by both):** the Gravy PPO runs **without** the canonical-suite gate; KL budget (0.125, frozen anchor), spot gates (every 5, 50 games, floor 0.30) and the trailing-150 heartbeat (floor 0.30) are retained at their 3b values. **Claude's added stop rides with it:** if the stage-2 anchor gate reads **below 0.40**, the pipeline stops before PPO and returns with a package (§4).

**Scope (C5, stated in the registration as required):** this build tests whether the *pipeline* transfers — data, clone, PPO, teacher, gate on a second hero, producing a second **hero-specific** policy. It does **not** test a single hero-independent policy; that is a later registration, with the distillation run as its natural place.

---

## 1. Stage map and stage gates

| Stage | What | Output | Hard gate to the next stage |
|---|---|---|---|
| 0 | vocab extension + loud assertion | `gravy_bc/card_vocab_gravy.json` (380) | assertion PASS on the extended vocab (both decks) |
| 1 | corpora: mirror + cross + pass-1 + DAgger | `gravy_bc/data/{mirror_self,cross_self,mirror_bc}` | per-batch game counts exact (2,400 / 750 / 1,500) |
| 2 | re-featurize + BC anchor + anchor gate | `gravy_bc/bc3_out/bc3_policy.pt` + anchor read | **anchor read ≥ 0.40** (Claude's stop) |
| 3 | gated PPO + C4 selection + census diagnostic | raw arm checkpoint (C4) | first candidate passing the C4 rule; "no checkpoint passing" ends the pipeline as a finding |
| 4 | gate tree build | `/tmp/gravytree` (hash-verified) | tree hashes == §6 values |
| 5 | pre-gate, contention probe, fleet, registry, audit | primary Δ + L1/L2/L3 + G3 | the §7 stops govern the read |

Stage reports go to Joe as each stage completes; a hard-gate failure stops the pipeline and returns as a package, per the stage-gated protocol (§8).

---

## 2. Stage 0 — vocab extension and the loud assertion

**Code:** `code/extend_vocab.py`, `code/test_vocab_assertion.py`.

**Extension (registered invocation, box sim root):**
```
python3 code/extend_vocab.py \
  --vocab-in  bc2_out/card_vocab.json \
  --vocab-out gravy_bc/card_vocab_gravy.json \
  --decks decks/nats2026_eriksen_gravy_60.txt \
          decks/nats2026_ashlyn_fai_60.txt
```
The script collects deck ids in first-appearance order, appends the missing ones at the next free indices, asserts every original (id → index) pair is unchanged and the output indices are contiguous before writing, and prints both files' sha256. Build-test result (§9): **379 → 380 entries; exactly one append, `nullrune_hood → 379`; moved = 0** (also confirmed by an independent diff of the two files: `moved = {}`, `added = {'nullrune_hood': 379}`). The extended vocab produced in scratch has sha256 `361b1a871808465fdc6105aedeaf875761e42aa925b227429ace05c312f60f20`; the stage-0 launch regenerates it at `gravy_bc/card_vocab_gravy.json` and the manifest records the hash it actually produces (expected identical).

**Loud assertion (registered invocation):**
```
/home/joe/tcg/rl-env/bin/python code/test_vocab_assertion.py \
  --vocab gravy_bc/card_vocab_gravy.json \
  --features-dir /home/joe/tcg/tcg-sim \
  --state-template probe/probe_v1.jsonl \
  --decks decks/nats2026_eriksen_gravy_60.txt \
          decks/nats2026_ashlyn_fai_60.txt
```
For every unique id in each deck, the test places the card — through the real `bc_features_v3.featurize_state_v3` code path, on a real state template — in own hand (slot 0), own arsenal (slot 8), and opponent pitch (opp slot 0), and asserts the slot encodes the card's own vocab index, never the EMPTY index (`len(vocab)`). Any failure names the card and exits 1. Build-test results (§9), both directions as registered:
- **Unextended vocab (379): FAIL, exit 1** — Gravy 36/37, Fai 34/34 (control clean); the one failure named: `nullrune_hood`, resolving to EMPTY (379) in all three positions.
- **Extended vocab (380): PASS, exit 0** — Gravy 37/37, Fai 34/34; EMPTY index 380.

The stage-0 gate is the extended-vocab PASS. The run vocab travels inside every checkpoint the pipeline writes (the trainer's `save_ckpt` carries `vocab`, as the Fai lineage's do), so serving and training share it by construction.

---

## 3. Stage 1 — corpora (mirror + cross + pass-1 + DAgger)

**Code:** `code/gravy_corpus_driver.sh` (wraps the box's fixed `bc2_gen.sh`, sha256 `58a5686454565b4d88d11572c0b9f153144f9ffd8f8ae4e1f959998a04c92f07`). Output tree: `/home/joe/tcg/tcg-sim/gravy_bc/` with `data/{mirror_self,cross_self,mirror_bc}`, `pass1_data/`, `pass1_out/`, `bc3_data/`, `bc3_out/` — the Fai layout (`bc2_data` → `bc3_data` → `bc3_out`) inside one hero directory.

| Batch | Invocation (via the driver) | Games | Design target |
|---|---|---|---|
| mirror_self | `bc2_gen.sh 6 400 G60 G60 gravy_bc/data/mirror_self` (no driver model — heuristic both seats) | 2,400 | ≈ 920k records |
| cross_self | `bc2_gen.sh 6 125 G60 F60 gravy_bc/data/cross_self` (heuristic both seats; Gravy in seat A, mirroring the Fai corpus's hero-in-A orientation) | 750 | ≈ 284k records |
| mirror_bc (DAgger) | `bc2_gen.sh 6 250 G60 G60 gravy_bc/data/mirror_bc gravy_bc/pass1_out/bc_policy.pt` | 1,500 | ≈ 563k records |

Record counts are design targets (per-game yield on Gravy is an output, as the design states); **the binding completion check is games**: the driver counts `games_w*.jsonl` rows per batch and aborts the stage if any batch is short — never a DONE file (the October-15 lesson). Record counts are reported in the stage-1 report beside the targets.

**The pass-1 clone — a build-level correction to the design's parenthetical, surfaced with its evidence.** The design (§4.1) describes the pass-1 BC as trained with "stage 2's recipe" (bc3_train.py, v3 features). That clone cannot drive the DAgger batch: the generation server in every `bc2_gen.sh` worker copy is `policy_server.py`, which loads its driver model through the **v1-generation pair** — `from bc_train import BCPolicy` + `from bc_features import …` (`policy_server.py:51–52`) — and a v3 checkpoint (`arch == "v3"`, slot architecture) cannot load there. This is exactly why Fai's DAgger was driven by bc **v1**. The build therefore registers the faithful analog:

- **Pass-1 = a v1-generation clone**, trained by the sim-root pair (`bc_train.py`, sha256 `2ea551f17e6306caa9cdd8cf66c187672cf5b9dd9ac37b6c02004e18e100f7ef`; root `bc_features.py` = the v2-content generation, sha256 `7f8fcd6ff12d0cad…`, STATE_DIM 97) on batches 1+2 only:
  ```
  /home/joe/tcg/rl-env/bin/python bc_train.py \
    --data gravy_bc/pass1_data --out gravy_bc/pass1_out
  ```
  (defaults: epochs 10, batch 256, lr 3e-4; `pass1_data/` holds symlinks to the two batch dirs, matching bc_train.py's `<data>/<batch>/traj_w*.jsonl` layout.)
- The DAgger batch then runs with **BCWHEELS unset** — worker copies take the sim-root pair, the same pair that trained the driver. (Fai pinned `BCWHEELS=$SIM/bc_v1` because its driver was the older bc_v1 pair; the pin follows the driver's training pair, and here that pair is the root.)
- The pass-1 clone is scaffolding: never gated, never the raw arm, and its feature generation touches nothing downstream — the anchor trains from the re-featurized corpus (§4), and the corpus *labels* are the heuristic's v1 argmax in both the Fai recipe and this one. What the driver changes is only which states get visited, which is the DAgger mechanism itself.

**Registry treatment (design §8):** corpus games are the training set by design — the registered exception. Their game ids are recorded per batch in the stage-1 report (from `games_w*.jsonl`) for provenance. Every *evaluation* game from stage 2 onward is registered eval-only in the do-not-train registry (3,076 games at build time) before the stage that consumes its read.

**Cost (design §4.1, Fai-measured):** generation ≈ 5.5–6 h at ~14 games/min across 6 workers; the pass-1 training (CPU, bc_train.py) runs inside that window's tail.

---

## 4. Stage 2 — re-featurization, BC anchor, anchor gate, and THE STOP

**Re-featurize** (BC3 rules verbatim — outcome join from final life totals; truncated games excluded from value training only):
```
PY=/home/joe/tcg/rl-env/bin/python
$PY bc3_build_data.py --corpora gravy_bc/data/mirror_self \
    gravy_bc/data/cross_self gravy_bc/data/mirror_bc \
  --vocab gravy_bc/card_vocab_gravy.json --outdir gravy_bc/bc3_data
```
(`bc3_build_data.py` sha256 `8188dd25c00063cd5b340b05ddf74d7c0b95c0664c5d7ec67ea5ea10269bcfa8`.)

**Train the anchor** (bc3_train.py recipe at its defaults — policy CE, Adam lr 3e-4, batch 1024, 10 epochs; then the value head alone, trunk frozen, 3 epochs):
```
$PY bc3_train.py --data gravy_bc/bc3_data \
  --vocab gravy_bc/card_vocab_gravy.json --outdir gravy_bc/bc3_out
```
(`bc3_train.py` sha256 `e0b05c7d52881a40fd6835e0f7d3ae04c87f7cc6036b091b96451653d1520af9`; output `gravy_bc/bc3_out/bc3_policy.pt` + `metrics.json`. Fai cost ≈ 7 min of GPU.)

**Anchor gate (registered protocol — the BC3-standard formal gate):** 400 seat-balanced games, anchor vs heuristic, Gravy mirror, through `rl/eval.py` (whose sim copy list is the fixed one — `bc_features_v3.py` + `ppo_model_v3.py` present at `rl/eval.py:57`):
```
$PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
  --games 200 --deck-a $G60 --deck-b $G60 --learner-deck a \
  --workdir gravy_bc/anchor_gate_a --sock /tmp/gravy_anchor_a.sock \
  --sim-dir /home/joe/tcg/tcg-sim
$PY rl/eval.py ... --learner-deck b --games 200 \
  --workdir gravy_bc/anchor_gate_b --sock /tmp/gravy_anchor_b.sock
```
The read is the two summaries' wins/games summed, reported with its Wilson 95% interval. **Server-log verification is part of the read** (the October-16 lesson): each workdir's server log must show the anchor loaded as learner with **fallbacks = 0**, or the gate is void and re-run. The Fai anchor's read on this protocol was **0.450 (150/333)** — the verified figure (the earlier 0.505 was retracted as a fallback artifact and is not the standard). All 400 games' ids (from the workdirs' `games_meta.jsonl`) are merged into the do-not-train registry as eval-only before stage 3.

**CLAUDE'S STOP (hard):** if the anchor read is **below 0.40**, the pipeline **stops before PPO** and returns with a package. The behavioral floors inside PPO (spot 0.30, heartbeat 0.30) were tuned against a Fai anchor at 0.450; they are not re-tuned here — a sub-0.40 anchor is a stage-2 finding, reported with the anchor's agreement metrics and the corpus record, and the floor question goes back to Claude and Joe. The stage-3 launcher enforces the stop mechanically (`GRAVY_STAGE2_CLEARED`, §5).

**Cost:** ≈ 1.5 h including the gate (design §4.2).

---

## 5. Stage 3 — gated PPO, the C4 selection, and the census diagnostic

**Configuration:** `configs/ppo_config_diff.txt` is the full record — the 3b run's recorded configuration against this launch, arg by arg. The complete delta is four items: (1) `--out-dir rl_out/gravy_ppo_gravybc3`; (2) `--bc3` / worker `BC_MODEL` = the stage-2 anchor; (3) the Gravy mirror deck (worker deck args, `TCG_MATCHUPS=gravy:gravy:1.0`, in-trainer spot-gate deck); (4) `--suite none` (Flag 2). Nothing else differs — no lr/budget/batch/epoch/floor/window change anywhere.

**Code:** `code/patch_trainer_launch.py` + `code/gravy_ppo_launch.sh`. Two facts about the trainer forced code, both surfaced here rather than absorbed:

1. **There is no trainer deck argument.** The spot-gate deck is the module constant `DECK_FAI` (`trainer_v4.py:259`), consumed by `run_spot_gate`'s eval.py subprocess (`--deck-a/--deck-b`, :273–274). Unpatched, a Gravy run's spot gates would evaluate the policy playing the **Fai** deck. The patch repoints the constant (`DECK_SPOT` → the Gravy deck, both use sites).
2. **There is no suite off-switch.** `Gate` loads the suite file unconditionally (`trainer_v4.py:190`) and acceptance is `kl_cum <= budget and suite_fine` (:509). The patch maps `--suite none` to a `None` suite path → zero positions; `suite_score` then returns (0, 0, {}) and `suite_ok` against a (0,0,{}) baseline is True, so acceptance reduces to the KL budget alone. Both behaviors were exercised in the build test (§9): the patch applies to the pristine trainer (sha256 asserted), produces launch copy sha256 `dc95d81a7f59139a9e290bc661e1b17f0cf85a93cdd2a829f63436a3829bf70a`, compiles, and the empty-suite logic returns exactly (0,0,{}) / True. The launch copy is installed at `rl/trainer_v4_gravy.py` so `SIM_ROOT` resolves to the sim root; the launcher hash-guards it.

**Surfaced sub-item (for Claude's eye; decided as stated, reversible by his word):** the retained `--probe` instrument, `probe/probe_v1.jsonl` (sha256 `974fef83498b0ac6…`), is 27,000 **Fai-game** states (fixed 4,096-state subsample, seed 20261016). The anchor's reference log-probabilities — and therefore every candidate's forward-KL against the 0.125 budget — are computed on Fai states for a Gravy policy. The build **retains it verbatim**: it is a fixed instrument, its role is a divergence budget rather than a quality judgment, and substituting a Gravy probe set would introduce a second unvalidated instrument change in the same run that Flag 2 already touches. The manifest records the retention. If Claude prefers a Gravy-state probe set, that is a one-line config change before launch — flagged here so the choice is his, not silent.

**Launch (registered):**
```
GRAVY_STAGE2_CLEARED=1 bash code/gravy_ppo_launch.sh
# workers: rl/run_workers.sh 4 $G60 $G60 rl_out/gravy_ppo_gravybc3
#   env SIM=/home/joe/tcg/tcg-sim BC_MODEL=<anchor>
#       TCG_MATCHUPS=gravy:gravy:1.0 (mix/temp/RL_MODEL at defaults)
# trainer: rl/trainer_v4_gravy.py --out-dir rl_out/gravy_ppo_gravybc3
#          --bc3 <anchor> --suite none (all else default)
```
**Live validity reporting (October-16 lesson):** mid-run reads come only from the trainer's own artifacts — `status.json`, the per-version spot reads, and the worker server logs at `/tmp/rlw*/server.log` **read during the run** (cleanup deletes them), each spot read quoted with its server log's loaded-weights line and fallback count. The halt mechanics are 3b's unchanged (spot failure → revert to last spot-verified + halt; 10 rejections → halt; heartbeat breach → revert + halt).

**C4 checkpoint selection (registered exactly as corrected):** candidates are the run's spot-verified checkpoints, tested **in version order (v5, v10, v15, v20), at most 4 formal gates**. Each formal gate is the §4 protocol (400 seat-balanced games vs heuristic, Gravy mirror, server-log-verified, games registered eval-only before the next step). A candidate **passes iff** (i) its formal-gate point estimate **≥ the stage-2 anchor's gate read**, AND (ii) the **lower bound of its Wilson 95% interval > anchor read − 0.05**. The **first** passer is the raw arm. If no candidate passes in 4 gates, that is the **"no checkpoint passing" finding**: reported as a result with all four reads, and the pipeline stops there — no teacher, no fleet. (The design §4.3 wording — "first checkpoint meeting the Fai standard" — is superseded by this protocol, per C4.)

**Post-stage-3 diagnostic (Flag 1 addition, report-only):** the round-5 census probe, **unchanged** (`rounds/round5/code/patch_census_probe.py`, producing the `b2fa1ffe…` featurize build), run on **20 plain Gravy bridge games** — seeds **8801–8810** (learner seat 1) and **8811–8820** (seat 2), fresh out-of-range seeds — in a scratch copy of the gate tree (`/tmp/gatetree_r4` — the same source stage 4 copies) plus the probe patch, against the production server, with the stage-3 selected checkpoint as the bridge model and the Gravy deck as the mirror. The runner follows `rounds/round5/code/run_census.sh`'s shape with tree/deck/model/seeds/out substituted (out `/tmp/gravy_census_diag`); tree identity guards check `search.php == 6cd6f980…` (the Gravy tree carries no abort patch, §6) and `featurize.php == b2fa1ffe…`. The tally (overall + by branch, `analyze_census.py` unchanged) is reported **with the stage-3 report, with no registration attached** — a representation note for Gravy, nothing more. These 20 games are eval-only and join the registry with the stage-3 merge.

**Cost:** PPO ≈ 1.5 h (3b reached v35 in 46 min across 13,956 worker games; the Gravy run's halt point is its own); selection gates ≈ 25 min each at the outside; diagnostic ≈ 20 min.

---

## 6. Stage 4 — the Gravy gate tree

**Build (registered):** copy the gate tree and substitute the arm:
```
cp -r /tmp/gatetree_r4 /tmp/gravytree
# verify inside /tmp/gravytree:
#   rl/search_server.py == ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c
#   search.php          == 6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a
#   featurize.php       == f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92
# then ONE substitution: probe_swap20.php line 17's bootstrap deck
#   decks/nats2026_ashlyn_fai_60.txt -> decks/nats2026_eriksen_gravy_60.txt
# (analysis copy only; the fleet machinery takes its deck from
#  paired_driver.py --deck, which the runner passes explicitly)
```

**What changes vs the Fai gate tree:** the served model (the C4-selected Gravy checkpoint, passed as `SEARCH_MODEL` by the runner), the deck (runner-passed), output/run names (`run_gravy_gate.sh`, out `/tmp/ggate`, sockets `/tmp/ggate_s{1,2}.sock`), the fleet seeds (§7), and the one-line L2 bootstrap deck above. **What is byte-identical:** `search.php` (6cd6f980… — teacher constants k=25, overturn 1.5 paired SE, top-3 + prior ≥ 0.10 cap 4, continuation va ride inside it), the patched server build (ab85fa1b…), `featurize.php` (f81193e0… — **current** featurizer; Flag 1), `paired_driver.py`, `gate_raw_retry.py`, the label machinery, and the vendor engine. Tree hashes verified in the build (§9).

**Abort-log patch — decision: the Gravy tree does NOT carry it.** Justification: comparability is the transfer design's spine — the Fai gate, the number this fleet is read against, ran on the un-patched search.php (6cd6f980…), so the Gravy fleet runs the identical file and the Δ comparison stays a one-variable difference (hero + policy). The patch's evidence value is real but already banked: its five root-canary aborts are what *posed* item (b), and (b) is now closed for the bridge population by the census + pick-flip, while the teacher-root population it samples is explicitly registered as a separate follow-up "if the teacher path develops further" (round-6 closure) — the stage-3 census diagnostic partially covers the representation question for Gravy in the meantime. If Claude wants root-population evidence from this fleet, adding the patch (`search.php → 8f6b35da…`, as in the O tree) is a one-file change to this section before launch — surfaced as his call, not taken silently either way.

---

## 7. Stage 5 — the gate fleet and the impeachment audit

**Fleet structure (the Fai gate's, with the hero substituted):** teacher (plain `TEACHER_MODE=1`: k=25, top-3 + any prior ≥ 0.10 cap 4, continuation va, overturn at 1.5 paired SE, R17 root state) vs the C4-selected raw checkpoint, **paired seeds 8001–8200, both seats, both arms vs the heuristic**, Gravy mirror deck — 400 (seed, seat) units, 800 games, four chunks (c1 8001–8050 … c4 8151–8200) in parallel, one patched server per seat, traces on, per-chunk game-id files. Runner: `code/run_gravy_gate.sh` (§9, guards dry-run).

**Pre-gate (registered):** 20 units — seeds **8501–8510 × both seats**, raw arm, Gravy tree vs the plain bridge on the production build. Pass = **trace-level equality** (the round-3 standard; result-JSON step counts are not engine counters). A self-pairing teacher-vs-teacher check is not a substitute (the round-2 lesson).

**Contention probe → timeout (registered formula, O precedent):** 4 concurrent teacher games on out-of-range seeds **8601–8604**; `GGATE_TIMEOUT = max(700, 3 × slowest probe game)`, recorded in the launch manifest and passed to the runner as `GATE_TIMEOUT`. No Fai/O number is inherited.

**G8 sweep before launch (hard):** the launch wrapper sweeps orphan segments first (resident count **2,191** at build time; operator stop 3,600; recorded before/after each chunk by the runner, production server hash before/after the fleet). The G3 trace re-classification sweep is armed before any reading (the G3 registration below).

**Struck registrations, with reasons:** *opponent-is-live* — n/a: the opponent is the built-in heuristic; there is no second model to keep live (its O-run replacement, the dose statement, is likewise n/a — no misspecified learned opponent is involved). The registrations that DO apply are carried whole: canary coverage (arm rate ≤ 2%; any branch > 5% reported by name), seed invalidation rules, timeout scoring (engine caps = 0.5 both seats; teacher wall-clock timeout = teacher loss, primary, with the drop-sensitivity; raw timeout = one re-run, then 0.5 and keep the pair), and the checkpoint sync (the tree build's store:=view sync is load-bearing and untouched).

**Registry merge before analysis (hard order):** fleet ids + teacher snapshot ids → `register_gate_ids.py` (sha256 `5515705b…`) merged eval-only into the do-not-train registry **before** any analysis script runs (registry at 3,076 games at build time; expected +800 games + snapshots). Analysis against an unmerged registry does not happen.

**Analysis (registered invocations; the gate/O scripts unchanged):**
- **Primary** — `analyze_gate.py` (sha256 `a5e20866…`) over the fleet rows + stat files + the merged registry: pooled Δ (teacher − raw) with the seed-clustered bootstrap CI, per-seat Δs, discordant counts with the exact sign test, timeout accounting, the G5 calibration table. Bands as designed (§7 reads).
- **L1** — the overturn census over the teacher stat rows (the gate/O census scripts, re-run provenance stated as in the O results), reported against its historical fail line (composite rate vs the 50% line).
- **L2 (C2, specified correctly)** — the **hidden-card swap test**: from the fleet's overturn snapshots, **20 snapshots sampled with seed `20261023`** (registered here for the Gravy fleet; selection = seeded shuffle of the L3 jobs file, first 20), each checked at **both picks** (prior pick and teacher pick) = **40 checks**: the opponent's hand[0] and deck[0] are swapped before assignment (same unseen pool, same sizes), the identical assignment (seed 31337) and rollout (seed 4242) run through `probe_swap20.php` (sha256 `6993ece4…`, in the Gravy tree per §6), and the paired rollout results are compared. Production server (the label path is R12-rejected by the patched server). Any mismatch stops the audit (impeachment trigger (a)/(b) territory, §7 stops).
- **L3** — jobs for **all** fleet overturns (`audit_overturns.py` sha256 `20853c43…`, `--sample 100000 --seed 20261023`), labeled at **LABEL_W = 50** fresh worlds through `meas_label_main.php` (sha256 `3109176b…`) on the production server, seed bases **855001 + shard×10⁸** (4 shards by game hash, `OPP_MIX` n/a — the continuation is the teacher's va), scored by `analyze_l3.py` (sha256 `16017ffa…`). The script's built-in reference constants are the Fai gate's (Δ = 0.2525, 400 teacher games); as registered for the O run, its printed delta-boundary block is disregarded and the per-game gain is computed in the results package from its JSON outputs against **this fleet's** measured Δ (teacher games = 400 by construction).
- **G3** — `gate_first_divergence.py` (sha256 `9aaca155…`) first-divergence census over every unit where the arms' games differ, with `classify_divergence.py` (sha256 `1518427b…`) categories; the O fleet's re-classification precedent (DUP_SEQ-class rows are legal game differences, not machinery defects) is the standing rule, and the sweep runs **before** Δ is interpreted.

**Audit cost:** ≈ 2–4 h (L3 dominates; the Fai gate's audit ran 91k label rows ≈ 3 h at 4 shards).

### Reads (C3)

The gate primary is pooled Δ under the **Fai band table verbatim** (design §5.3). Co-reported, for both heroes, as context that never feeds the bands:
- **Headroom-normalized gain** = Δ / (1 − raw rate). Fai reference, recomputed from the gate record: Δ +0.2525, raw 0.4500 → 0.2525 / 0.55 = **0.4591**.
- **Log-odds difference** = logit(teacher rate) − logit(raw rate). Fai reference: logit(0.7025) − logit(0.4500) = **+1.0599**.

Gravy band wording (C3): where the Fai table's third band reads as the projection having overstated the gain, the Gravy read is **"no detectable conversion"** (`analyze_gate.py`'s printed label for that band is read under this wording in the results package; the script itself is unchanged). The **transfer interpretation bands** (design §5.4) then apply: converts at **≥ +0.15** = transfers; converts below +0.15 / real-but-small = partial transfer, with the per-stage diagnostics naming where the gain shrank (anchor read, C4 reads, overturn rate, L3 retention); no conversion = does not transfer, with the registered consequence for the distillation run's aim.

### Stops (C1 — restated exactly as corrected; this list supersedes design §6's trigger list)

The audit stops and the result is referred back — not read — on:

- **(a)** any **G3 machinery defect**;
- **(b)** any overturn row failing its own logged margin: **`mean_diff > 1.5 × se_diff` on ≥ 20 shared worlds** (the L1 census checks every overturn row against its own row);
- **(c)** **teacher timeouts > 2%** → the gate is **inconclusive**;
- **(d)** **canary refusals > 2% per arm-seat**;
- **(e)** the **calibration void pattern** (predicted-vs-actual empty in two or more of the top bins, as in the round-2 addendum trigger list).

The overturn rate is **reported against the 12–16% null band**; **above 30% it triggers a sample review before Δ is read**. That is its whole role. No other overturn-rate threshold appears anywhere in this build. (For the record, since the design draft carried one: the "~5% impeaches" rule was withdrawn by Claude in round 3 and is **not** part of this registration.)

Impeachment conversion rule (standard, unchanged): L1 + L2 clean and the L3 mean difference > 0 with CI lower bound > 0 → the impeachment clears and the result converts; mean > 0 but per-game gain < Δ/2 → converts with the excess reported as unexplained; CI includes 0 → do not convert.

---

## 8. Launch protocol

1. **Stage-gated execution.** Each stage's outputs are verified (hashes, counts, reads — per §§2–7) before the next stage starts. The stage-2 anchor stop (< 0.40) and the C4 four-gate cap are **hard stops**: hitting either ends the pipeline and returns a package; no re-tuning, no extra gates, no extension runs.
2. **Launched sha == approved sha.** Per stage, the launch manifest (template in `configs/`) records the approved sha, the launched HEAD, Joe's go (timestamp + words), and every artifact hash the stage depends on. Any code change after approval — however small — returns for review before launch; rounds-only diffs are the standing exception.
3. **ETAs (per stage, from the Fai-measured costs in the design):** stage 0 ≈ minutes; stage 1 ≈ 5.5–6 h; stage 2 ≈ 1.5 h; stage 3 ≈ 1.5 h + ≤ 4 × 25 min selection + 20 min diagnostic; stage 4 ≈ minutes; stage 5 ≈ 10.7 h provisional (replaced by the Gravy contention probe at launch) + 2–4 h audit. Total ≈ 24 h of box time across the stage gates.
4. **Reporting cadence:** a stage report to Joe as each stage completes (artifact hashes, the stage's read, the next stage's gate status), and a check-in time stated in clock times in every report. Fleet progress reads come from the box's own files (rows, manifests, ipcs), never from delivery timing.

---

## 9. Build verification (what was actually run, 2026-10-21)

All scratch work on the box under `/tmp/r7build/`; the box's production tree was never written to. **No games were played.**

1. **Vocab extension (scratch application).** `extend_vocab.py` against the real `bc2_out/card_vocab.json` and both deck files: `379 -> 380 entries; appended: nullrune_hood -> 379; moved: 0 (asserted)`; extended vocab sha256 `361b1a871808465fdc6105aedeaf875761e42aa925b227429ace05c312f60f20`. **Independent diff** (separate check, not the script's own assertion): `moved = {}`, `added = {'nullrune_hood': 379}`.
2. **Assertion, both directions** (real `featurize_state_v3`, real probe state template):
   - unextended vocab: `Gravy 36/37, Fai 34/34` → **FAIL exit 1**, naming `nullrune_hood` at hand/arsenal/opp-pitch (all → EMPTY 379).
   - extended vocab: `Gravy 37/37, Fai 34/34` → **PASS exit 0** (EMPTY index 380).
3. **Trainer launch patch.** Applied to the pristine `rl/trainer_v4.py` (input sha256 asserted = `8fd52d82…`): 5 anchored replacements in 3 changes (suite-None load, `--suite none` mapping, `DECK_FAI` → `DECK_SPOT` + both use sites); launch copy sha256 `dc95d81a…`; `py_compile` clean; logic test in-process: `suite_score` on zero positions = (0, 0, {}), `suite_ok` vs (0,0,{}) baseline = True. The patch script prints the full unified diff on every application; `configs/ppo_config_diff.txt` §C records the change summary and both hashes.
4. **PPO config diff** produced from the primary artifacts (argparse table `trainer_v4.py:308–325`; `run_workers.sh` interface; 3b `status.json` / `trainer_v4.log` / `workers.log`) — `configs/ppo_config_diff.txt`. **Unexpected-difference check:** the only items beyond the design's expected "deck args, anchor path, run dir, suite line" are the two code-level facts the patch exists for (the deck is a constant, not an arg; the suite has no off-switch) and the surfaced `--probe` retention (§5). No other argument differs.
5. **Syntax + guards.** `bash -n` clean on all three shell scripts; `py_compile` clean on all three Python scripts. Guard dry-runs (no env): `run_gravy_gate.sh` exits 1 naming `GRAVY_MODEL`; `gravy_ppo_launch.sh` exits 1 on the stage-2 stop; neither creates any directory or file.
6. **Tree hashes (read-only verification).** In both `/tmp/gatetree_r4` and `/tmp/otree`: server `ab85fa1b…`, `featurize.php` `f81193e0…`; gate `search.php` `6cd6f980…`; O `search.php` `8f6b35da…` (abort patch — the value §6 declines to carry). Resident shared-memory segments at check time: **2,191** (G8 sweep registered before the fleet).

**Stated as unverifiable at build time** (each is a launch-condition read, registered above rather than assumed): the Gravy per-game record yield and generation rate (targets, §3); the Gravy teacher game time, hence the fleet timeout and duration (contention probe, §7); Gravy BC learning quality (anchor read, §4); whether the census diagnostic's store/view pattern on Gravy resembles the Fai ARS concentration (report-only, §5); and the 3b launcher's exact historical invocation, which survives only as the reconstruction in `configs/ppo_config_diff.txt` from the run's own artifacts (the values it pins — defaults equal to status.json, the workers.log matchup line — are primary; the invocation's *form* is the reconstruction).

---

*Builder: Muse (for Joe Slattery), 2026-10-21. Review venue: this repository. Joe relays; Claude reviews; launches happen only on Claude's approval at the committed sha plus Joe's go in chat.*
