# Round 8 build package — distillation (per-hero, Fai)

Parent: **2be3e3b4** (repo HEAD; carries the design
`rounds/round8/distillation-design.md`, commit 926f6c31, and the
reviewer's reply `rounds/round8/claude-reply-926f6c3.md`).

This package implements the reply's §8 build list, items 1–7.
Everything below was assembled and verified on the box on
2026-10-25: trees built, hashes taken from the files themselves,
patchers exercised on throwaway copies, one featurization smoke
run (the only execution in this package — no games, captures,
label jobs, training, census, or gate were run). Every script
carries a REVIEW-GATED header: nothing here runs before the
reviewer's code review of this package at its committed sha,
and each stage then needs Joe's go separately (§8).

Where the machinery did not match what the design/reply
described, the package says so plainly and names the gap
(GAPS 1–2, §2 and §5, plus the smaller named limits collected in
§9). Nothing was improvised silently.

---

## §1 The featurizer correction and the two trees (reply §8.1)

### The correction

`featurize.php` had exactly two deck reads, both through
`SimV1_DeckCards` (the STORE globals `$p1Deck/$p2Deck`,
policy_v1.php:44): line 97 (`SimFeat_BuildState`'s
`deck_counts`) and line 148 (`SimFeat_LegalCounts`, the canary's
own allowance count). The correction moves **both** reads to a
new helper that reads the deck through the getter VIEW — the
round-5 census probe's exact view-side definition:

```diff
--- native/featurize.php
+++ corrected/featurize.php
@@ -58,6 +58,20 @@
   ];
 }

+function SimFeat_DeckIDs($player) {
+  // Round-8 (b) correction: the deck zone read through the getter
+  // VIEW (GetDeck, CardGetters.php - the same getter family every
+  // other zone in this file is read through), with the featurizer's
+  // own per-zone treatment (ZoneIDs with DeckPieces()). Before this
+  // correction the two deck-count reads below used SimV1_DeckCards,
+  // which reads the STORE globals ($p1Deck/$p2Deck, policy_v1.php).
+  // SimV1_DeckCards itself is NOT changed: the heuristic's own
+  // deck-awareness (policy_v1.php) keeps reading the store; only the
+  // featurizer's reads move to the view.
+  $deck = &GetDeck($player);
+  return SimFeat_ZoneIDs($deck, DeckPieces());
+}
+
 function SimFeat_BuildState($player, $branch, $candidates) {
   $player = intval($player);
   $hand = &GetHand($player);
@@ -94,7 +108,7 @@
     "hand_size" => count($handIDs),
     "intellect" => $intellect,
     "arsenal" => $arsenalIDs,
-    "deck_counts" => SimFeat_Counts(SimV1_DeckCards($player)),
+    "deck_counts" => SimFeat_Counts(SimFeat_DeckIDs($player)),
     "board" => [1 => SimFeat_BoardSide(1), 2 => SimFeat_BoardSide(2)],
     "chain_links" => $chainCount,
     "chain_attack" => $attackID,
@@ -145,7 +159,7 @@
   $legal = [];
   $hand = &GetHand($player);
   SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs($hand, HandPieces())));
-  SimFeat_MergeCounts($legal, SimFeat_Counts(SimV1_DeckCards($player)));
+  SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_DeckIDs($player)));
   SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetArsenal($player), ArsenalPieces())));
   foreach ([1, 2] as $q) {
     SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_ZoneIDs(GetAllies($q), AllyPieces())));
```

Two properties of this shape, stated for the review:

- **The canary site moves with the featurizer.** `LegalCounts`
  is the hidden-information canary's allowance list. At a
  view>store state a store-based allowance would under-count
  and the canary would false-positive on the corrected build's
  own output. The correction is featurizer-scoped, and the
  canary is part of the featurizer.
- **`SimV1_DeckCards` itself is untouched**, and the
  load-bearing store:=view checkpoint sync in search.php is
  untouched (search.php is byte-identical in both trees — see
  the hash lists). The heuristic's own pitch logic keeps
  reading the store, exactly as it did for the gated teacher.

`code/patch_featurize_correction.py` (anchor-asserted, count==1
per edit) reproduces the corrected file from the native base;
verified on a throwaway copy: product sha256 =
`3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a`,
`php -l` clean, byte-identical to the staged
`code/featurize_corrected.php` and to the corrected tree's file.

### The trees

Built on the box as copies of `/tmp/gatetree_r4` (`__pycache__`
removed):

- `/tmp/distilltree_native` — the gate tree as-is.
- `/tmp/distilltree_corrected` — the same + the corrected
  featurize.php.

**Full-tree hash comparison** (every file, both trees, 13,639
files each): the trees differ in **exactly one file**,
featurize.php (`f81193e0…` → `3dcf32c9…`). (One vendor doc file
with spaces in its name — `New Developer Guide.md` — failed to
hash under `xargs` in both trees identically; it is not code.)

Load-bearing hashes (identical in both trees unless noted):

| file | sha256 |
|---|---|
| search.php | `6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a` |
| featurize.php (native) | `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92` |
| featurize.php (corrected) | `3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a` |
| rl/search_server.py (tree) | `ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c` |
| paired_driver.py | `1e312629c9ebe30e97e0480c1f9d5530e82eba3c1a9511b3a929bc6f2d92471d` |
| play_game.php | `4ac2d62ddf64c8e8b6dfb64fac59beb639cb697026aaeb4b968fd91aa707f1d8` |
| policy_server.php | `64c215392ddcac0dc92ce1e4a3c455969d87423e23d71be57991247ce53827b3` |
| policy_v1.php | `8b71f7eedb2084826fe169ffaa6fd8f855a6324959f53d5577bc0519449c3803` |
| meas_label_main.php | `3109176bb7137bc89b0645b8185f83c5722268c03028ca692642699cf7730b33` |
| snap_relabel_main.php | `2e4abccd7627aabc3562b2d568d1ab1d990540a25c988d2bd839846842ca744c` |
| bc_features_v3.py | `081402e8689c32b5a347f797e1056b74eeeb94d41b7ac06f4c796c2b5113e47b` |
| bc_features.py | `7f8fcd6ff12d0cadab594375562fc8c0e063cb128d2974020b6d642dd78f713a` |
| ppo_model_v3.py | `91d3bfe591e814476f223b6733f52d2521e2269b669634937e2c1033ccc26c0c` |
| decks/nats2026_ashlyn_fai_60.txt | `7397684b9d07debe0f0661f35bbc09c607c2e09953b822b5daa0fbbfa46f332a` |

Shared pins outside the trees:

| artifact | sha256 |
|---|---|
| v15 `rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt` | `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c` |
| BC3 `bc3_out/bc3_policy.pt` | `78e2950c1628e8546d4a1faf7e335caebbdce3f1f1a9284a4377846018eb7bb9` |
| production server `rl/search_server.py` | `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4` |
| standalone vocab `bc2_out/card_vocab.json` | `3592bf44196bf4d0375ad8ae5625fd728a1c11025d45a0ab84565143804182c8` |

(The vocab the servers and trainers actually use is the one
embedded in the v15 checkpoint — `ckpt["vocab"]`, 379 entries;
the standalone file is listed for provenance.)

### The featurization smoke (the package's one execution)

Tool: `code/featurize_snapshot.php` — batch-featurizes snapshot
dirs through whichever tree it runs in (LABEL_DRIVER bootstrap
like `snap_relabel_main.php`; DeleteCache before ParseGamestate;
emits `SimFeat_BuildState` + the canary result per snapshot).

Runs made (2026-10-25, gate-fleet snapshots from
`/tmp/gate_r4/gate_c*_teacher_s*_snaps/`):

- **Two-snapshot smoke** (one branch-M, one branch-ARS): both
  builds featurize cleanly, canary passes under both; the
  native offline featurization **equals the gate index's stored
  live state exactly (0 differing leaves)**; native vs corrected
  also 0 differing leaves on both.
- **40-snapshot scan** (seeded sample, Random(20261025), across
  all 8 gate streams; branches M 20 / B 16 / P 4): 0 errors;
  native-vs-corrected differing = **0 on all 40**;
  stored-live vs offline-native differing = **0 on all 40**.

**Conclusion, stated plainly:** offline featurization of parsed
snapshots is faithful (parsed == live-stored at Decide roots),
and parsed roots encode no store/view splits in this sample —
the split is a live-play transient *between* syncs, and Decide
roots are post-sync by construction. The correction therefore
binds at **live serving** (bridge featurizations between syncs;
the round-5 census measured the split at 0.604% of
featurizations, ARS-concentrated), which is exactly what the
pre-gate's featurizer-only control (§5) measures. Two
consequences are built into the package rather than assumed
away:

1. T1's dual featurization (§4) remains well-defined — it is
   computed per state by running both builds — and
   `t1_build_data.py` **asserts** offline-native == the capture
   index's stored live state for every corpus state, counts
   violations (expected ~0 at roots by the same post-sync
   argument), and **drops** violators from both datasets.
2. The teacher-root census (§3) inherits the same caveat: it
   censuses parsed (post-sync) roots, so a null there does not
   bound the live in-transit subclass. Stated again at §3.

---

## §2 Capture and the labeler (reply §8.2)

### Capture-arm verification — the reviewer's claim holds

`paired_driver.py` (both trees, `1e312629…`) implements
`--arm capture` exactly as the reply described: the driver sets
`TEACHER_MODE=1 + TEACHER_CAPTURE=1 + TEACHER_SNAP_DIR`; in
`search.php` (≈line 856) the capture branch snapshots **every
contested decision** (game-dir copy + a
`teacher_snap_index.jsonl` row carrying cands, the native live
state, priors, prior_pick, selected), plays the prior pick, and
never rolls out. The driver manifest asserts it: capture rows
carry `capture=1`, `pick == prior`, no rollout fields, no
rollouts anywhere in the arm, and trace picks == prior argmax.
No new recorder was written.

One scope note the package states rather than hides: the driver
plays mirror decks and has **no opponent flag** — opponent
identity is a server property (the O fleet's routing). The
corpus's three matchups are therefore a *runner composition*,
not a driver change: `run_capture_corpus.sh` routes the
non-learner seat through the in-tree server's `TCG_OPP_MIX`
(format verified in `rl/search_server.py`: `heuristic:1.0` /
`ckptpath:<path>:1.0`).

### GAP 1 — uncontested snapshots do not exist (named, with fix)

The capture arm snapshots contested decisions only.
`SimTeacher_Decide`'s uncontested early-return (≈search.php:837)
logs a stat row and the driver trace carries hashes, not
states — so the corpus as the driver produces it has **nothing
to compute the T1 KL term on** (the reply's §3 requires
uncontested states from the same corpus games). Fix shipped:
`code/patch_capture_uncontested.py`, an anchor-asserted patch to
the **corpus tree only** (a third, derived tree the capture
runner builds from the native tree at launch; the two gate
trees are never touched). Under `TEACHER_CAPTURE &&
TEACHER_CAPTURE_UNCONTESTED` it snapshots the uncontested state
through the existing snapshot machinery — snapshot-only, in a
try/catch, never changing the pick — with index rows carrying
`"uncontested": 1` and no `selected`. Verified on a throwaway
copy: applies cleanly, `php -l` clean, product search.php
sha256 `044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d`
(the capture runner records the built tree's hash in
`corpus_manifest.json` rather than asserting a fixed value, and
asserts the corpus tree's featurize.php stays **native**).

### The corpus runner

`code/run_capture_corpus.sh`: 400 games, seeds **10001–10400**
(fresh, disjoint from every registered range), learner = v15 in
both seats, one stream per (matchup, seat):

| matchup | seat 1 | seat 2 | games |
|---|---|---|---|
| vs heuristic | 10001–10080 | 10081–10160 | 160 |
| vs BC3 (`TCG_OPP_MIX=ckptpath:<BC3>:1.0`) | 10161–10220 | 10221–10280 | 120 |
| mirror v15 (`ckptpath:<v15>:1.0`) | 10281–10340 | 10341–10400 | 120 |

Per stream the runner aborts unless the driver's capture
manifest has `assert_ok == true`. Output goes to
`/home/joe/tcg/distill_corpus` — durable disk, **not** tmpfs: a
snapshot dir runs ≈260 KB (measured on the gate streams) and
the corpus holds contested + uncontested snapshots for 400
games (≈37k states by the gate's rates, ≈9.6 GB); round 7's
stage-1 /tmp fill is the standing lesson. `corpus_manifest.json`
records tree hashes, per-stream snapshot counts, and game ids.

### The labeler

Composed from the existing label machinery — nothing new was
invented:

- `SimLabel_RunForSnapshot` (search.php:1397, both trees) is
  the registered procedure: loads a snapshot into `Games/<game>/`
  + `Games/label_scratch/`, **DeleteCache before
  ParseGamestate**, rootKey = branch|player|cands (R17),
  determinizes W worlds per candidate with seed = seedBase +
  w×31337 (same base for all candidates — paired), forks
  `SimLabel_RunRollout` children (forceIdx, pair "va"), 300 s
  per-candidate deadline; returns per-(candidate, world) rows:
  `{outcome ∈ {−1,0,+1} root-perspective, finished, winner}` or
  `{error}`.
- `code/distill_label_main.php` (modeled on the tree's
  `snap_relabel_main.php`): reads jobs (snap_dir, cands,
  selected, prior_pick), enforces `candIdx =` the job's
  registered `selected` set, **pins LABEL_W at 25 and aborts on
  any other value** (the L-era W=50 sets are a different
  instrument), runs against the production server socket, and
  appends provenance (prior_pick, selected, game, branch,
  player, turn, seed_base) to every raw row. Per-job wall time
  goes to stderr for the pilot's cost read.
- `code/label_reduce.py`: reduces raw rows with the live
  Decide arithmetic mirrored exactly — candidate mean over
  finished worlds; prior candidate < 20 finished → **thin:
  excluded and counted** (`thin.jsonl`), never prior-labeled;
  best = argmax mean (strict >, ascending selected order);
  overturn iff paired_n ≥ 20 AND mean_diff > 1.5 × se_diff over
  shared finished worlds (se = sqrt(Σ(d−mean)²/(n−1))/sqrt(n));
  best≠prior with paired_n < 20 → confirmation flagged
  `paired_thin` and counted. Emits `labels.jsonl` (state id,
  prior pick, teacher pick, candidates, n_worlds, mean_diff,
  se_diff) + counts.

**Placement, stated explicitly (the reply's §2 reasoning):**
the labeler PHP runs in **`/tmp/distilltree_native`**
(featurize `f81193e0…` — the gated teacher's own build) against
the **production server** (`81ef2cdb…`), because the labeler's
picks must be the gated teacher's picks and the round-3 note
R12 records that the patched tree server rejects the label
path's seat-0 eval requests. The **student's** training records
featurize the same snapshots through the **corrected** build,
offline, in the T1 data builder (§4). Label truth is native;
student inputs are corrected; the package never confuses the
two.

**Concurrency constraint:** `SimLabel_RunForSnapshot` wipes the
fixed `Games/label_scratch/` dir, so exactly **one label
process per tree**. `code/run_label_corpus.sh` shards the
corpus's contested jobs across **4 copies of the native tree**
run in parallel (each hash-asserted), jobs split by root player
to the matching seat's production server, with a (C) sweeper
per label tree (§6). Labels merge into one `labels.jsonl` whose
sha256 lands in `label_manifest.json`.

Parts manifest (label path): search.php `6cd6f980…` (labeler
host, native tree), production server `81ef2cdb…`,
`distill_label_main.php` `4fcb960e…`, `label_reduce.py`
`c3b0511c…` (full hashes in the §10 manifest).

---

## §3 The pilot (reply §8.3)

Runner: `code/run_pilot.sh` (written, NOT run). Twenty label
jobs, chosen by `code/pilot_prep.py` as a stratified sample
(quotas 3,3,3,3,2,2,2,2 across the 8 Fai gate streams,
Random(20261025)) of gate-fleet overturn snapshots. Each job is
labeled **twice** — run A `DISTILL_SEED 555001`, run B
`777001` (different world seeds) — in the native tree against
per-seat production servers, with a (C) sweeper on the native
tree's Games dir and a pre-launch G8 (§6).

**V2 survival — verified on the box.** The Fai gate fleet's
teacher snapshots survive: `/tmp/gate_r4/gate_c{1..4}_teacher_s{1,2}_snaps/`
holds **915 snapshot dirs == 915 overturn stat rows** (every
stream's snap count equals its overturn-row count). The index
rows carry teacher_pick, prior_pick, mean_diff, se_diff, cands,
and the live state — but **not** `selected`/`priors`; those join
from the stream's `search_stats.jsonl` overturn rows by game +
within-game order. The join was **verified** on game 725976967
(3↔3 rows; picks, priors, branches all equal), and
`pilot_prep.py` asserts pick/prior/branch equality per row and
aborts on any mismatch. **Named V2 limit:** Decide snapshots
only overturns, so V2 covers the overturn side; confirmations
are covered by V1 only. No fallback capture set is needed.

**The reads** (`code/pilot_times.py` + `code/pilot_report.py`):

- **Cost:** per-snapshot label time over the 40 job-runs —
  mean, p95, max — and the corpus sizing read (10k contested
  labels at the pilot's mean and p95). Timeouts for later
  stages derive from the tail, never the mean (§6).
- **V1 self-consistency:** agreement between run A and run B
  labels per snapshot — overall, and conditional on run A's
  verdict (overturns; confirmations), in both directions, with
  Wilson intervals. This is the noise floor.
- **V2 live-consistency:** the offline labeler's pick vs the
  LIVE teacher pick on the same 20 snapshots, per run and
  pooled, with Wilson intervals, and a two-proportion z-test p
  for V2-vs-V1. The indistinguishability judgment is the
  reviewer's; the report carries the numbers, not a verdict.
- **Thin-label count:** labels whose prior candidate finished
  < 20 worlds (excluded from any corpus, counted here first).

**Teacher-root census (report-only).** The pilot's last stage
builds a probe tree from the native tree with the round-5
census patcher (product featurize asserted at
`b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a`
— re-derived this session by applying
`rounds/round5/code/patch_census_probe.py` to the native base)
and runs `featurize_snapshot.php` over the 20 pilot roots with
`CENSUS_LOG` set, tallied by `tally_census.py`. **Caveat,
registered with the result:** parsed roots are post-sync
serialized records — the census reads the population the round-6
closure named (teacher Decide roots), and per §1's smoke the
store/view split does not survive serialization at roots; a
null tally bounds the parsed-root population only, not the live
in-transit subclass, which is not reproducible offline.

---

## §4 T1 — the supervised distillation trainer (reply §8.4)

### Data builder

`code/t1_build_data.py`. Inputs: the capture corpus (snap
indexes), `labels.jsonl`, both trees. For **every** usable
snapshot it runs `featurize_snapshot.php` in batch in the native
tree AND in the corrected tree (the dual featurization the
reply's §2/§3 require), then:

- **Assertion:** for every snapshot whose capture index row
  stored the LIVE state, offline-native must deep-equal it (§1's
  smoke: 40/40 on gate snapshots). Mismatches are counted,
  listed, and **dropped from both datasets** — never trained on.
- **Held-out split:** ~10% of corpus **games** held out BY GAME
  (seeded, `split.json`); every record carries its game's split.
- **Contested records** (labeled only; thin labels are absent
  from `labels.jsonl` by construction): corrected tensors +
  `action = teacher_pick`, in the BC3 shard shape plus a
  per-record `game`/`split`/`ncand` (documented extension — the
  trainer's held-out CE filter needs them).
- **KL records:** uncontested states with **paired** native and
  corrected tensors.
- Encoding is the trees' own (`bc_features_v3.featurize_state_v3`
  + `bc_features.featurize_candidate`, hash-pinned §1), vocab
  from the v15 checkpoint.
- `build_report.json` carries every count (contested, KL, thin
  dropped, mismatches dropped, split sizes).

### Trainer

`code/t1_trainer.py` + `code/t1_config.json`. Adapted from the
BC3 trainer's shape (`bc3_train.py`, tree root, `e0b05c7d…`):
`PPOPolicyV3` initialized **from v15** (vocab asserted 379),
trained on:

    loss = CE(student ‖ teacher pick)            [contested, corrected tensors]
         + β · KL(v15 ‖ student),  β = 1         [uncontested states]

with v15's KL-side distribution computed from the **native**
tensors and the student's from the **corrected** tensors,
candidate-masked softmaxes on both sides. **Uniform label
weighting** (the reply's §4: no upweighting, no value weighting).

**No value-head training, enforced in code, not just stated:**
the value head is frozen (`requires_grad` off, excluded from
the optimizer) and the trainer **asserts tensor-equality of the
saved checkpoint's value head against v15's** before writing.

**Selection (the reply's §5(2) rule):** no game-based selection.
Fixed schedule from the config; **early stopping on held-out
cross-entropy** (held-out games only), patience **5 epochs**,
min-delta **1e-4**; the checkpoint at the held-out-CE minimum is
the **one** checkpoint written (`{"arch": "v3", "model",
"vocab", "version": "t1-distill-r8"}` — loadable by the tree
server unchanged). Config values proposed here for the review:
lr **1e-4** (Adam), batch 1024, epoch cap 30, seed 20261025.
The reply registered β, the split, and the stopping rule; the
numeric schedule is this package's proposal, flagged as such.

T2 (PPO) is **not** in round 8 (reply §4) — no PPO code ships
in this package, and the halt-at-budget launch-copy fix travels
with a future T2 registration, not this one.

---

## §5 The gate (reply §8.5)

### Pre-gate

`code/run_distill_pregate.sh` + `code/pregate_compare.py`,
seeds **11001–11010** (fresh). Per tree: hash pins asserted at
start (search.php, the tree's featurize.php, tree server,
driver, deck, v15); the raw arm (v15, both seats, vs heuristic)
run **twice**; determinism read **strictly from the driver's own
rows** by the compare script (winner, turns, decisions,
gamelog_sha256 — the round-4 never-eyeball rule); fallbacks = 0
verified from server logs and driver manifests; the R16-style
seat-crossed control read from the same rows (the two seats of
one tree must differ on ≥ 1 of 10 seeds).

**Featurizer-only control (reply §5(3), report-only):** v15 raw
on the corrected tree vs v15 raw on the native tree, paired on
the same pre-gate seeds — identical-gamelog count and
winner-difference count reported, no band registered on it.
This is the control that isolates the correction's own effect
on v15's play, and per §1 it is where the correction's effect,
if any, must appear: at live serving between syncs.

### Gate fleet

`code/run_distill_gate.sh` — the round-7 paired pattern adapted
to two trees. Four servers (native tree + v15, corrected tree +
the T1 checkpoint, × seats 1/2, distinct sockets); chunks
c1 9001–9050, c2 9051–9100, c3 9101–9150, c4 9151–9200; per
chunk/seat both arms raw via `paired_driver.py` with the Fai
deck passed explicitly; per-arm timeout recovery (the
round-7 `gate_raw_retry` splice). **800 games.** Serving runs
through each tree's own `rl/search_server.py` — the distilled
checkpoint is a new artifact whose serving the pre-gate
certifies; no production-server substitution (the anchor
re-gate precedent).

- **`GATE_TIMEOUT` is a REQUIRED launch input** — the script
  refuses to start without it. It is set at launch from the
  pre-gate/pilot tail behavior, never inherited from another
  population (the round-7 timeout lesson: the 8-game probe
  underestimated the mean ~2× and the tail worse).
- **Registry before analysis:** on fleet completion the runner
  merges all 16 game-id files into
  `/tmp/harvest/do_not_train_registry.json` via
  `code/merge_registry.py` (tag `distill_gate_eval`, timestamped
  backup + vault copy in `/home/joe/tcg/registry-vault/`) and
  prints the merged registry's sha256.

### Analysis

`code/analyze_distill_gate.py` (adapted from the round-4 gate
analysis): asserts `DISTILL_REGISTRY_SHA256` against the
registry on disk before reading; primary paired Δ
(distilled − v15), draw-scored (capped/drawn = 0.5; post-retry
timeout rows score 0.5 for that arm, counted and reported);
cluster bootstrap CI by seed + normal-approximation cross-check
+ exact sign test; per-seat splits; absolute scores with the
distilled arm beside this fleet's v15 arm and, labeled
historical, the Fai gate's 0.4500; **divergence rate**
(game-level: units with differing gamelog_sha / 400; first-
divergence decision depth reported when the rows carry pick
sequences). Bands exactly as registered in the reply §5:

- **CONVERTS:** Δ ≥ +0.10 AND CI lower > 0.
- **PARTIAL:** CI lower > 0 AND Δ < +0.10 — read with the
  divergence rate.
- **DOES NOT CONVERT:** CI includes 0 (suspects in order:
  label definition, then corpus).
- **IMPEACH:** Δ > +0.25 — banner printed, verdict withheld
  pending investigation.

### The L2-form swap test

`code/build_swap_jobs.py` + `code/swap_test.py`.

**GAP 2 — the registered snapshot source does not exist
(named, with substitute).** The reply's §5(4) draws the swap
test's states from "the gate's divergence decisions" — but the
gate's raw arms snapshot nothing (raw play records rows and
final game dirs only), so divergence decisions are not
recoverable as states after the fleet. Substitute, registered
here: **corpus capture snapshots where the two policies'
offline picks diverge** — distilled argmax on the corrected
featurization ≠ v15 argmax on the native featurization,
computed from the data builder's dual featurizations —
sampled to 20, spread across branches as far as the pool
allows. These are states where the two policy/build pairs
actually part company: the population the test exists to
interrogate. The substitution is disclosed wherever the result
is cited.

The test itself is the round-3 L2 form adapted to a raw policy:
per job, snapshot B swaps the root player's opponent's
hand[0] ↔ deck[0] in `gamestate.txt` (line positions from
`probe_swap20.php`: P1 hand 1 / deck 2, P2 hand 19 / deck 20 —
two cards equally hidden from the root); A and B are featurized
through **the arm's own tree** and the pick computed locally
with the server's masked argmax over the tree's `bc_features`.
PASS iff the two state arrays are deep-identical AND the picks
are equal. Run for the distilled policy (corrected tree) and
v15 as control (native tree); **invariance is required on
both**. `probe_swap20.php`'s forced-rollout trajectory form is
deliberately NOT used: that form tests the label/rollout path;
the arm under test is a raw policy whose serving path is
featurize → net → argmax, and the L2 form interrogates exactly
that path. Jobs whose opponent hand or deck is empty are
counted as unswappable and excluded — never scored as passes.

### Records publication

As round 7: after the gate, the fleet's row files and search
stat files are committed under `rounds/round8/` with the
analysis report (the round-7 records commit 26290bb2 is the
pattern). Nothing about the fleet is citable before that commit
exists.

---

## §6 Containment (reply §8.6)

- **(C) kernel-attribution sweeper** — `rounds/round7/code/shm_sweep.py`
  (sha256 `98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33`),
  deployed alongside every teacher/label run in this package:
  the pilot (native tree), the corpus label stage (one per
  label tree), the gate (one per gate tree). Run pattern: run-start
  `ipcs -m` listing saved as the shmid start-file; sweeper stopped
  via its stop file after the last chunk/job.
- **Pre-launch G8 sweep** — `code/g8_sweep.sh` (the round-3
  `gate_ipcs_cleanup.sh` carried forward: removes only
  `nattch == 0` segments, aborts if game processes are running,
  writes before/after evidence) runs before the pilot, the
  label stage, and the gate fleet — the round-7 ruling's
  condition for ANY production-tree teacher work. The fleet
  close left 227 rule-3 parent segments on the box; the pilot's
  pre-launch G8 is the first sweep that clears them.
- **Timeouts derive from the pilot's tail, never its mean:**
  `GATE_TIMEOUT` is a required launch input (§5), and the label
  stages inherit the label path's own 300 s per-candidate
  deadline; the pilot's p95/max reads are the sizing evidence
  the corpus and gate launches cite.

---

## §7 Gravy census pre-step (reply §8.7)

`code/run_gravy_census.sh` (written, NOT run) — the round-7
build package's registered diagnostic, carried into round 8 by
the reply §6: scratch tree copied from `/tmp/gatetree_r4` +
the round-5 census probe patch (guards asserted: search.php
`6cd6f980…`, probe-product featurize
`b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a`),
**production server** (`81ef2cdb…`), bridge model = Gravy PPO
v10 (`rl_out/gravy_ppo_gravybc3/ckpt_v10.pt`, sha256
`44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3`),
Gravy deck mirror (`decks/nats2026_eriksen_gravy_60.txt`),
seeds **8801–8820** (seat 1: 8801–8810; seat 2: 8811–8820),
out `/tmp/gravy_census_diag`, tallied by the round-5
`tally_census.py`. Report-only: no registration attaches to the
tally. The 20 games are eval-only and are registered afterward
via `merge_registry.py` (tag `gravy_census_diag_eval`) — the
runner prints the exact command. This pre-step is independent
of the pilot/corpus/gate go-gates; it runs on Joe's go alone.

---

## §8 Sequencing and go-gates

1. **This package** → the reviewer's code review at its
   committed sha. Nothing runs before that review lands.
2. **Gravy census pre-step** (§7) — Joe's go; independent of
   the rest.
3. **Pilot** (§3) — Joe's go. Its V1/V2 + cost reads are the
   corpus's unlock: **the corpus is approved only after the
   pilot reads clean** (the reply's sequencing).
4. **Corpus** (§2: capture, then label) — Joe's go after the
   pilot.
5. **T1 training** (§4) — Joe's go after the corpus. Exactly
   one checkpoint comes out.
6. **Pre-gate, then gate** (§5) — Joe's go after T1; the gate's
   `GATE_TIMEOUT` is fixed at launch from the pilot/pre-gate
   tails.
7. **Swap test** (§5) — follows the gate (its jobs need the
   distilled checkpoint and the corpus's dual featurizations);
   required for a conversion read.
8. **Records publication** — fleet row/stat files + analysis
   committed post-gate, as round 7.

Deployment (before any run): copy `rounds/round8/code/*` plus
three borrowed files into `CODE_DIR` (default
`/home/joe/tcg/round8_code`) and verify hashes against §10:
`rounds/round5/code/patch_census_probe.py`
(`60a3808c9de55671cffb13bc01dcda8e84160da7c564a18ce23692661c3de8fd`),
`rounds/round5/code/tally_census.py`
(`fe2480bbab8eba2e8082f158459b5494566f2254c31a56c1c8ce917607cc9267`),
`rounds/round7/code/shm_sweep.py`
(`98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33`).

---

## §9 Named gaps and limits (consolidated)

1. **GAP 1 (§2):** uncontested snapshots do not exist in the
   capture arm's output. Fixed by `patch_capture_uncontested.py`
   on a derived corpus tree (product search.php
   `044ca8ec…`, recorded in the corpus manifest at build time).
2. **GAP 2 (§5):** the swap test's registered snapshot source
   (gate divergence decisions) is not recoverable — raw arms
   snapshot nothing. Substitute: divergent-pick corpus
   snapshots, disclosed wherever cited.
3. **V2 limit (§3):** V2 covers overturns only (Decide
   snapshots only overturns); confirmations rest on V1.
4. **Parsed-root caveats (§1, §3):** offline featurization is
   faithful at roots and parsed roots show no store/view split
   in the samples — the split is a live transient between
   syncs. Consequences are built in (the data builder's
   stored-state assertion; the featurizer-only control as the
   correction's live read; the teacher-root census's stated
   bound).
5. **Label serialization (§2):** one label process per tree
   (fixed `Games/label_scratch/`); the corpus label stage
   shards across 4 tree copies.
6. **Corpus volume (§2):** ≈37k snapshots ≈ 9.6 GB — durable
   disk, not tmpfs.
7. **Trainer knobs (§4):** lr 1e-4, batch 1024, epoch cap 30,
   patience 5, min-delta 1e-4 are this package's proposals for
   the review; β = 1, the by-game split, and the
   no-game-selection rule are the reply's registrations.
8. **Divergence depth (§5):** the game-level divergence rate is
   the registered read; first-divergence depth is reported only
   when fleet rows carry pick sequences.

---

## §10 Code manifest (rounds/round8/code/)

Syntax checks (all passed 2026-10-25): `bash -n` on every
`.sh`; `python3 -m py_compile` on every `.py`; `php -l` on
every `.php` (on the box); `t1_config.json` parses.

| file | sha256 |
|---|---|
| analyze_distill_gate.py | `de65600efeb7e4dec68c530113c9ec534aa8d625e5910f8794431ffea8d3c335` |
| build_swap_jobs.py | `0871f3710042688610ded481db612bcf857eca9a4af481c660d399f4c5e454e2` |
| distill_label_main.php | `4fcb960ecd34d6c803ef7be9bc9713610eb6b99192636f32638c3647bf1661d9` |
| featurize_corrected.php | `3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a` |
| featurize_snapshot.php | `bef241d1b4fd09059fe4dd4a4b5cdc324ccf7288caad631cffedac925f7c0882` |
| g8_sweep.sh | `82b4d58ce3f7d2bb9e92d9fe75a55ae6b2e982fcaca0536ae44f1a3583b7caa0` |
| label_reduce.py | `c3b0511cd7b85ac87877cd1fef90a17a903df1ca716900f6d8614f29b3f84623` |
| merge_registry.py | `13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe` |
| patch_capture_uncontested.py | `68c92679867ceba35a0d7a1023d57f6abc173741a6e612677c1d66583152f90c` |
| patch_featurize_correction.py | `1594c8640df7a794c3a12d39c52c9da606994e5181e00f113164f1fa595d241d` |
| pilot_prep.py | `a9bcc1a6550ecb1256a68210d1e081900fd751d8877afc3b7ef99c90be3d39b5` |
| pilot_report.py | `ec67ee5c9939ef505e59f1e075c84965936050d661d7b3a13af93dade5bea22c` |
| pilot_times.py | `d4a811a92e0063cd151c06e088e6c029c0224a16fc2465a86699aeb42fce0a63` |
| pregate_compare.py | `b961b1256839fa91752e0950b8c8528193cbe20b6614eb26efe400b4e6088324` |
| run_capture_corpus.sh | `4d04b5a6284af174a9e2623ae1a89e834581c7ee1ad32dee76e795d4dc702f9f` |
| run_distill_gate.sh | `9e60d46b5f58fe6c98e17ce76fa3b4bc045940dfa25f30d22a5fe96c50a8204a` |
| run_distill_pregate.sh | `dcb5037f9817ff78990d7f61fb0bc9eca42a962d3c8381afdbcf311c5e2479fd` |
| run_gravy_census.sh | `5dd71d580ab3f7e5d2ab46645886f2e66138aee3343bce304e80b5e651b85e44` |
| run_label_corpus.sh | `4983f70d6cc4c4383aad49037f954f120bbab58e1f784d5747d717ea14e723ae` |
| run_pilot.sh | `067aced0e33b4ee8276083f2f830aa6eb5b17c6d0e305b4d315c579807ce81e6` |
| swap_test.py | `04777aacbe8442cc65bf541bb9004d0074c6a43f066cfb4dcdd4754abfd4d4ed` |
| t1_build_data.py | `811564224650545012bcd051c1e4de993f491aa6540dae17fe930444ec43830c` |
| t1_config.json | `43e12cc2ea3f7e64b5dda0644f6a01929612fd45a84df7e7a20d6c17492d67bf` |
| t1_trainer.py | `2b1735aa4460fd4ffc8b2958937b53e4c3fc39007d3b392865544999d8ab0206` |

Borrowed, deployed alongside (§8): `patch_census_probe.py`
(round 5, `60a3808c…`), `tally_census.py` (round 5,
`fe2480bb…`), `shm_sweep.py` (round 7, `98027a8b…`).

*End of build package. Staged for the builder's audit and
commit; nothing in this package has been run beyond the §1
featurization smoke, and no stage runs before the reviewer's
code review at the committed sha and Joe's go for that stage.*
