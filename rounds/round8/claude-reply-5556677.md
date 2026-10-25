# Claude — round 8 closed: independent recomputation and the canary explanation

**Reviewed commit:** 5556677249a64947188f2b2808cc2d8508a31d5b (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-379b188.md` hashes to `b4a5222c…2811bf4c`, the value I gave Joe.
**Package:** `rounds/round8/data/wcheck/` (`MANIFEST.sha256` verifies 20/20 here) and `rounds/round8/wcheck-canary-note.md`.

**Verdict: everything recomputes exactly from the raw rows, the canary explanation holds, and round 8 is closed.**

## 1. Recomputation from the raw rows

I wrote my own reducer. It doesn't use `label_reduce.py`, `calibrate_margin.py` or the published label files; it starts from `raw_a_all.jsonl.gz`, `raw_b_all.jsonl.gz` and `jobs_w100.jsonl`, under the registered rule:
- finished worlds only
- the prior's 20-world floor
- best by strict > over the sorted selected set
- paired n ≥ 20, sample SE over √n
- overturn iff `mean_diff > m · se_diff`

The split is by game, seed 20261025, with the first ⌈20/2⌉ games in H1.

| | Report | Recomputed here |
|---|---|---|
| Labeled (A / B / both) | 545 / 546 / 544 | **545 / 546 / 544** |
| H1 / H2 states | 284 / 260 | **284 / 260** |
| m = 1.5: A overturns, V1-ov, V1-conf, advantage | 66, 29/66 = 0.439, 442/478, +0.153 | **66, 29/66, 442/478, +0.153** |
| m = 2.0 | 36, 0.389, +0.212 | **36, 14/36 = 0.389, +0.212** |
| m = 2.5 | 21, 0.571, +0.294 | **21, 12/21 = 0.571, +0.294** |
| m = 3.0 | 11, 0.545, +0.425 | **11, 6/11 = 0.545, +0.425** |
| H1 V1-ov at m = 1.5 / 2.0 / 2.5 / 3.0 | 16/36, 9/23, 7/13, 4/7 | **16/36, 9/23, 7/13, 4/7** |

Everything matches. **No m reaches 0.60 on H1, so CLOSE is confirmed from primary data.**

## 2. The canary explanation: accepted

**From the raw rows here:**
- run A: 600 `canary_hook_failed` (all of `286996099_t12` and `286996099_t16`, candidates 0–2) and 100 `abort` (`852109890_t72`, candidate 2)
- run B: 300 `det_persist_failed` (all of `286996099_t19`) and 100 `abort` (`852109890_t72`, candidate 2)
- **0 lines containing `LEAK`** in either file

**From the code** (the repo's copy of the teacher, `code/search-gate-tree.php`, the same structure): `canary_hook_failed` is returned by `SimSearch_HookCheck` when `SimSearch_Canary` fails. That is `SimSearch_MissingCards`: decklist conservation in the **child's own determinized copy**, meaning the decklist counts against the pool plus public counts, with chain-layer credits. It checks that a sampled world is card-consistent. Nothing in it reads or compares the true hidden contents, so a failure **excludes worlds**. It doesn't detect a leak.

The pattern fits too. These are whole-state, seed-dependent failures (A's states fail under A's seeds, B's under B's), and both failed jobs finish 300/300 when re-labeled serially at the same seed bases. **This is the determinization-refusal class, as stated.** The two points the note marks as unprovable from the record don't affect the classification or any read.

**The side finding** (`/tmp/distilltree_native` still holds the pre-amendment labeler, while the check ran the amended one via `run_w_check.sh`'s copy-in): noted. Before any later round reuses that tree, the tree copy is re-synced and re-pinned.

## Round 8: closed

The record stands as my 379b188 reply states it, now confirmed from published primary data:
- **The offline labeler is the gated teacher's procedure.**
- **The teacher's overturn labels are not reproducible enough to distill by argmax imitation:** 17% at k = 25, 44% at W = 100 (at about 10× the label cost), and at most about 55% under a stricter margin, by which point overturns have shrunk to about 2% of states.
- **The signal is real:** fresh worlds favor the overturned move, and the advantage survives selection at every margin. But it lives in small, noisy advantages that a thresholded label can't carry to a deterministic student.
- **No distilled policy was trained or gated,** by registered decision made on label-validity evidence alone.
- **For any future teacher-to-policy line:** value-based targets or stochastic serving, as a new design.

**Scope:** this reply closes round 8. No launch is approved or pending.
