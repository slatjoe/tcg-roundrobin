# Round 8 — pilot report: Gravy census complete; pilot STOPPED at the capture-equivalence check

**Launch:** manifest `rounds/round8/pilot-launch.md` (repo sha 3b68d5cb), approved build sha dc22f1d3, Joe's go 2026-10-25 11:49 EDT.
**Outcome in one line:** the Gravy census pre-step ran clean and its 20 games are registered; the pilot's capture phase completed (547 contested states), and the pilot then **stopped at its registered stop** — the capture-equivalence check's strict parse read FAIL on seat 1 — before any labeling. No V1/V2, mechanism, deadline, cost, or teacher-root-census reads exist. The failure evidence is below, verbatim, with the mechanism identified from the artifacts; the disposition is the reviewer's.

## 1. Launch record

- **Deployed code:** the staging tree's `rounds/round8/code/` (28 files) was deployed to `/home/joe/tcg/round8_code` on the box and every load-bearing file's sha256 verified there against the fix package's manifest before anything ran: `run_pilot.sh` `eff185fd24752130c918bbc1eda0e323a384f780340a0df036bd33de98800cfb`, `run_gravy_census.sh` `5dd71d580ab3f7e5d2ab46645886f2e66138aee3343bce304e80b5e651b85e44`, `run_capture_corpus.sh` `10c4e570d984625dbd23d9568b0f20352cfdb1c56c56f8a0ad7271141a15980b`, `distill_label_main.php` `4f1de80a2babd84bbdcf1e70670b746e4637d15b91793d150798943`, `label_reduce.py` `e2244fbb70ac0282490c155d527a0b1e0e60a5387b81ce0a4be9eeac2d73bb8c`, `pilot_prep.py` `3131264b9f02e002926199ee7fcf8bf9c3f217cae87a758d009118076d284a30`, `pilot_report.py` `45b557418c0517d4dd06562c17460e5fe8923c1d926e17788a33eaf54f85ad94`, `pilot_times.py` `c0556e2ae0b1d6d21125ff1ac787871398ec765b0b0fcf35902074171f2ef93e`, `shm_sweep.py` `98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33`, `g8_sweep.sh` `82b4d58ce3f7d2bb9e92d9fe75a55ae6b2e982fcaca0536ae44f1a3583b7caa0`, `parse_r3_pair.py` `ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1`, `patch_census_probe.py` `60a3808c9de55671cffb13bc01dcda8e84160da7c564a18ce23692661c3de8fd`, `tally_census.py` `fe2480bbab8eba2e8082f158459b5494566f2254c31a56c1c8ce917607cc9267`, `merge_registry.py` `13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe`. The pilot additionally wrote its own deployment record: `/tmp/distill_pilot/deployed_code_hashes.txt`, sha256 `2e0f958dbf36c8262b623fff11e0aa562640b2542ad4d58f0a5656770f7a8bd1`.
- **Trees re-verified before launch:** `/tmp/distilltree_native/featurize.php` = `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92`; `/tmp/distilltree_corrected/featurize.php` = `3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a`. Production server `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4`; v15 `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c`.
- **Pre-launch G8 sweep (standing condition):** 268 segments → **0** (all 268 at nattch=0; no game processes running). Evidence: `/tmp/r8_launch/g8_pre_before.txt` sha256 `ac2dbc187a82b6df872212199764b4823cf58950fd63c17d4a80f147a5da8442`, `/tmp/r8_launch/g8_pre_after.txt` sha256 `a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8`.

## 2. Gravy census pre-step — COMPLETE

Run 2026-10-25 ~11:51 EDT, `run_gravy_census.sh` as written (scratch tree from `/tmp/gatetree_r4` + round-5 probe patch; guards passed: search.php `6cd6f980…`, patched featurize `b2fa1ffe…`, production server `81ef2cdb…`; bridge model v10 `44f1e5d7…` loaded on cuda; **fallbacks 0** in both server logs). Tally from `tally_census.py`'s own output (`/tmp/gravy_census_diag/tally.txt`, sha256 `782dc957b4c04b6ab4c067bc23b3b50feb40315f83452c3e8f9421b0a4d9174d`):

- **TOTAL: 12,896 featurizations, 114 disagreements, 20 distinct games** (seat 1: 6,331 featurizations, 47 disagreements; seat 2: 6,565, 67).
- **Overall disagreement rate: 114/12,896 = 0.884%, Wilson95 [0.736%, 1.061%]** — all 114 in direction **view>store**; store>view 0; mixed 0.
- **By branch:** the disagreements are **all at ARS: 114/214 = 53.271%, Wilson95 [46.588%, 59.839%]**. Every other branch is 0 (A 0/984, B 0/616, D 0/984, DQ 0/5,357, M 0/1,916, M_END 0/1,561, P 0/1,264).
- **By player:** player 1: 51/6,371 = 0.801% [0.609%, 1.051%]; player 2: 63/6,525 = 0.966% [0.755%, 1.233%]. ARS by player: P1 51/119 = 42.857%, P2 63/95 = 66.316%.
- Differing cards: 22 distinct, 155 card-diff entries (largest: sunken_treasure_blue 22, call_to_the_grave_blue 21, jittery_bones_blue 15, portside_exchange_blue 15, loot_the_hold_blue 14 — all deltas −1 or −2, i.e. view counts exceed store counts).

The Gravy pattern is the Fai pattern (all-ARS, all view>store): overall rate 0.884% against Fai's 0.604% census figure (a different featurization mix), ARS rate 53.3% against Fai's 61.0%. Report-only, as registered; no verdict machinery attaches.

**Registry merge (done in this run, per the launch orders):** the 20 games (ids in `/tmp/gravy_census_diag/census_game_ids_s1.txt` sha256 `51f4536304ff631b00e5403b7464c7df3b561d01074a61b9087bfc720281cab8` and `census_game_ids_s2.txt` sha256 `24b706c23179896ffcca060b9e64f42d5a740d7aee6f6ea2c4626478f8255c1b`) were merged under tag `gravy_census_diag_eval`: **registry 6,161 → 6,181 games**; before sha256 `fc46f835cafefdca042457bc84b509af47e3f6ed28f63b453fde05261c225521`, **after sha256 `a26a92b60c0d946c99cd704830c45d40e9b6710d45a816f31f2b91f80572b939`**. Pre/post copies kept at `/tmp/gravy_census_diag/registry_before.json` and `registry_after.json`.

Other census artifacts: rows `/tmp/gravy_census_diag/census_s1.jsonl` sha256 `b7e1a253cbd38db9537d4cc8bf79695c7a485044862deba3268ca8e5fdf604c4`, `census_s2.jsonl` sha256 `21821335a1415c7e1b6376ac05dc4d3b86bbbf8b65d45a845b1828e2979497db`; census logs `census/census_s1.log` sha256 `31f3ede5558267985289692200d2b686a954e3f6d54b72e7b712f074ec67f645`, `census/census_s2.log` sha256 `298cb55b1564ae37751a5739c4825b7b54c79769f6636b4c3d2206521f2ea95a`; server logs sha256 `2ec1b54aaec398150f013b7f2598796a209b3ab3743e55c8e296b4c9e43b1bc7` / `4b390fd755a139bc0d89e4a5b52d42acff2fdb40cccd37991ac64d34a6652569`; run log `/tmp/r8_launch/census_run.log` sha256 `096c93171a7b8684800a1dd219243316535516ca334632a6d881687ace4266b8`.

## 3. The pilot — capture complete; STOPPED at the equivalence check

Launched 2026-10-25 ~11:52 EDT (`run_pilot.sh`, setsid-detached; run log `/tmp/r8_launch/pilot_run.log` sha256 `2715e3cc0c5bf0931a81c785ee45024e70445d08874674c8718fed0c4f54016f`).

### 3.1 Phase 1 (containment) — done

The pilot's own G8 sweep took the 20 segments left by the census run to 0 (`/tmp/distill_pilot/g8_before.txt` sha256 `737e1ec1015421993cf4b87ab6de7938503fa7341eb7b1e8713ce36dd5c8f3e1`, `g8_after.txt` sha256 `a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8`). The (C) sweeper ran alongside, pointed at the native tree's Games dir (log `/tmp/distill_pilot/shm_sweep.log` sha256 `8ac646b180b4ac09e0f816c63b53520fe9eabf3fd38ca196b5de6881214017d6`; observed deleting leaked segments during the capture phase, 0 failed).

### 3.2 Phase 2 (pilot capture, seeds 10001–10020) — COMPLETE

Corpus-tree capture (patch product asserted in the corpus manifest: `corpus_search_sha256` = `044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d`). Stream manifest (`/home/joe/tcg/distill_corpus/heur_s1.jsonl.manifest.json`): `assert_ok: true`, every check true (capture rows present; **capture pick == prior on all rows**; no rollout fields; no rollouts anywhere; teacher trace pick == prior argmax on all 1,402 teacher trace rows); server fallbacks 0. Corpus manifest (`/home/joe/tcg/distill_corpus/corpus_manifest.json`, sha256 `edc6e4fbea929f60ec3a157c39a30cb45106ca925f2eb5b42dc45fd4b215ea30`): `pilot_subset: true`; **547 contested + 855 uncontested states (1,402 snapshots), 20 unique game ids**. Capture log `/tmp/distill_pilot/pilot_capture.log` sha256 `25f86ee9d72f5473ea6514c633d9f25ff169b387a21b4e2672d9deecd0c3ff44`; rows `/home/joe/tcg/distill_corpus/heur_s1.jsonl` sha256 `9af4e5314220553aa792d9511661f323426e4dc872905dc4e39cd16ba7676565`; game ids `/home/joe/tcg/distill_corpus/heur_s1_game_ids.txt` sha256 `f659c39072e1d29672ba9ad77b9210b3efd16a56fa1a500f907d627eae9ceed8`. Run A's future labels on these games were **not** produced (see §3.3).

### 3.3 Phase 3 (capture-equivalence check) — THE REGISTERED STOP FIRED

The runner's own stop line, verbatim from `/tmp/r8_launch/pilot_run.log`:

```
PILOT STOP: capture equivalence FAILED seat 1 - see /tmp/distill_pilot/equiv_pair_s1.parse.txt
```

The strict parser's output (`/tmp/distill_pilot/equiv_pair_s1.parse.txt`, sha256 `fcc10e1f22e61adfd64b6ccc6fe2a565f1a7701d91050ab3239f04b9e04c8e2d`), identical for all 10 seeds 12001–12010:

```
PARSE-FAIL: seed 12001: verdict INVALID_MODE (want IDENTICAL)
PARSE-FAIL: seed 12001: modes ok False (want True)
... (the same two lines for every seed through 12010)
```

The comparison table itself (`/tmp/distill_pilot/equiv_pair_s1.txt`, sha256 `824c2349d3d1f1658444bbf2f13397e932c899522c7aa4b64c11bea5fb462bcb`), all 10 rows:

```
| seed | pair | verdict | within-row hits | seq | outcome equal | modes ok | seat ok | assert ok |
| 12001 | raw vs raw | INVALID_MODE | 0 | None | True | False | True | True |
... (identical shape for 12002–12010)
```

**The only failing column is `modes ok`.** Outcomes are equal on all 10 seeds (the two arms' winners match seed-by-seed in the run log: 12001 → 2/2, 12006 → 1/1, 12009 → 1/1, 12010 → 1/1, and so on), within-row divergence hits are 0, seat and assert checks are True.

**The mechanism, from the artifacts.** `r3_pair.py`'s `mode_ok(arm_name, row)` requires each game row's `mode_line` to begin with the arm's registered prefix (`MODE_PREFIX = {"raw": "policy: server", "teacher": "policy: search", "ghost": "policy: search", "shadow": "policy: search", "capture": "policy: search"}`). `run_pilot.sh` invokes the comparison with **both sides named `raw`**:

```
r3_pair.py raw="$OUT/equiv_cap_s${seat}.jsonl,..." raw="$OUT/equiv_raw_s${seat}.jsonl,..."
```

The capture rows' `mode_line` is `"policy: search (seat 1 via /tmp/distill_pilot/equiv_s1.sock)"` (10/10 rows in `/tmp/distill_pilot/equiv_cap_s1.jsonl`, sha256 `d6521708170f3b740624e40d31bbeb1b9be8e1404f933ee49947a5a669f841d6`) — the capture arm runs under the search bootstrap by design, and its correct prefix under the table is the `capture` entry, not `raw`. The raw rows' `mode_line` is `"policy: server (v1-equivalent via ...)"` (10/10 rows in `equiv_raw_s1.jsonl`, sha256 `096c9d0352e10681466e91eb649243c09cc569a191a661137b1047ed288b8141`). So every capture row fails `mode_ok` under the name `raw`, the verdict is INVALID_MODE on all 10 seeds, and the strict parser — which requires IDENTICAL — reports FAIL. The pilot stopped before seat 2's check and before all labeling, exactly as registered. Game ids: `equiv_cap_s1_game_ids.txt` sha256 `65db670232c196645c7106923b73af84f71f8961b40cbc2eee9010603bce96de`, `equiv_raw_s1_game_ids.txt` sha256 `576910e653708713c0053c862137177562c1aa5aebd63d6e26567a48538f314d` (20 games, seeds 12001–12010 ×2 arms; not merged into the registry by this operator — they await the records commit's disposition, as do the 20 capture games of §3.2).

Whether this is a K6-class reclassification (the check's arm-naming vs the capture arm's by-design mode line, with play demonstrably identical on outcomes and trace hits) or a defect the build must fix is the reviewer's call, not the operator's. No workaround was attempted and nothing was re-run.

### 3.4 Phases 4–7 — NOT RUN

No further artifacts exist, and none of the following were produced: jobs files, labels, **V1-ov / V1-conf, V2 (and its thin count), the mechanism z-check, the deadline accounting, the cost reads and corpus estimate, and the teacher-root census.** The pilot directory contains only the phase 1–3 artifacts listed above. **Closing segment state:** 20 segments remain (the equivalence games' parent segments, all nattch=0, kept under rule 3 while the sweeper ran; the sweeper was stopped by the pilot's exit trap before any end-of-run listing). A G8 sweep is the standing pre-launch condition for whatever runs next.

## 4. What this leaves open

- The pilot's registered purpose — V1/V2 label validity, the deadline and cost reads, the teacher-root census — is entirely unmeasured. The corpus stays gated, as before.
- The capture corpus-so-far (547 contested + 855 uncontested states from seeds 10001–10020) sits intact at `/home/joe/tcg/distill_corpus/`; if the equivalence question is resolved by reclassification or by a build fix, run A's labels on these games remain available as registered.
- The one-capture-per-seed declaration for the corpus manifest (approval §3) is still owed, unchanged.
