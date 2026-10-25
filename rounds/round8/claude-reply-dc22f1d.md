# Claude — review of the round-8 fix package

**Reviewed commit:** dc22f1d39301d9e24201354591eca0deba57530b (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-a076148.md` hashes to `f83bd0ed…7b67f7e707`, the value I gave Joe.
**Package:** `rounds/round8/build-fix.md`, the corrected `rounds/round8/code/`, and `rounds/round8/fixtures/`.

**Verdict: APPROVED. The pilot may launch on Joe's go.** Two items must be fixed before the stages they touch, and neither affects the pilot:
- a sign-test bug, before the gate (§2)
- one capture per corpus seed, declared before the corpus run (§3)

## 1. The fixes, checked

**§2.1 and §2.2 (the gate path and the row schema):**
- the invented retry step is gone
- the stock `gate_raw_retry.py` (`c3fb227e…`) is pinned in both trees and runs on `invalid == "timeout"` rows only
- scoring branches in the registered order
- divergence is computed on `gamelog_sha`, with timeout units kept separate
- `pregate_compare.py` is keyed on `(seed, arm, seat)`

**The retried-ids defect you found in passing** (retried games escaping the registry merge) is real, and it's fixed by the stock invocation. Good catch.

**Fixture 1, re-run here independently.** I took the committed `analyze_distill_gate.py`, changed only its registry path to a scratch file, ran it on `rounds/round7/data/rows/` through the committed shim, and diffed the result against `fixtures/analyze_r7_report.json`. **They're identical on every key:**
- 400 units, Σd +6.5, **Δ +0.01625**
- **88 diverged**, 305 identical, **7 timeout units**
- CI [−0.00375, +0.03625], **DOES NOT CONVERT**
- 0 unusable

These are the values I computed from the rows before the fix.

**Fixtures 2 and 3** ran on the box: determinism 0 diffs, the seat control 10/10, and the retry firing only on the injected timeout row while the control runs nothing. Accepted from the committed logs. The unit wording in §0.4 (20 units = 10 seeds × 2 seats) is fine.

**§3, the pilot:** built as registered.
- the capture limited to 10001–10020
- V1-ov and V1-conf from a double label
- V2 on 100 stratified snapshots from the **preserved copy**, with a per-row equality assert on the join
- the two-proportion test **V2 against V1-ov**, with the trajectory caveat printed
- the z-check on unselected candidates (borrowing the labeler's per-world SD is a sound construction, and it's stated)
- the deadline accounting through split-candidate calls. The same seeds give the same rows, so it's an instrument change only, and the corpus runner never uses it.
- the cost over about 1,200 jobs
- the capture-equivalence phase, which stops the pilot before any labeling if it fails

**§4:**
- the value-head set is asserted non-empty, and the name `value_head` is confirmed from the model code, so the freeze was never vacuous
- epoch −1 is the baseline, and there's no gate checkpoint if nothing beats it
- overturn recall and confirmation accuracy are logged
- the KL set drops `ncand ≤ 1`
- the registry-disjointness abort
- input hashes are recorded
- the swap test uses a differing pair and asserts the swap took effect through `debug_opp_hand`, with invalid swaps never counted as passes
- the corpus tree's product hash is asserted

**§5 (the preserved copy):** `/home/joe/tcg/gate_r4_v2_preserve/` holds 915 snapshot dirs and the 8 stat files, with `MANIFEST.sha256` `f4d0cd09…`. The empty self-entry is disclosed. Accepted.

**Staging the borrowed files byte-identical** (so every `$CODE_DIR` reference resolves) is right.

## 2. Before the gate: the sign test is wrong

`analyze_distill_gate.py:239–242` sums the binomial tail over `i ≤ wins` when wins ≥ losses (and over `i ≤ losses` otherwise). That's the tail containing the *larger* count, so p is capped at 1.0 whenever the counts are unequal. Fixture 1 shows it: **wins 19, losses 10, p = 1.0.** The correct two-sided exact p is 2 · P(X ≤ min(wins, losses)) for X ~ Bin(29, ½), which is **0.136**.

The bands don't read the sign test, so the pilot is unaffected and nothing reported so far is wrong. **Fix it before the gate:** sum over `i ≤ min(wins, losses)`. Add the fixture-1 expectation `{wins 19, losses 10, p ≈ 0.1360}` to the fixtures README, and commit the re-run output.

## 3. Before the corpus: one capture per seed

§4(i) says the full corpus run will **re-run** seeds 10001–10020, overwriting the pilot's capture, and that run A's pilot labels are ordinary corpus labels. Those two can't both hold. A re-run creates new game names and therefore new snapshot ids, so run A's labels won't join the re-run's snapshots. Worse, if both captures end up in the corpus directory, the **same seed's game appears twice under different game ids.** The by-game held-out split would then treat them as different games, and the same game could land in both train and held-out.

**Declare one of two options in the corpus launch manifest:**
- **(a)** the corpus run **skips** 10001–10020 in the heur seat-1 stream, the pilot's capture directory is merged in as-is, and run A's labels are kept
- **(b)** the pilot's capture and labels are discarded and the corpus re-captures and re-labels those seeds

Either way, `t1_build_data.py` should assert **one game id per (stream, seed)** and abort on a duplicate.

## 4. Report-only, for the pilot report

A V2 snapshot the labeler finds **thin** drops out of V2's denominator. The live teacher wasn't thin there, so print the V2 thin count beside V2. On Fai's rates it should be 0. If it isn't, I'll read it as a disagreement.

**Scope:** this reply approves the round-8 build at sha dc22f1d39301d9e24201354591eca0deba57530b for **the pilot** (capture 10001–10020, the equivalence check, V1, V2, the deadline and cost reads, and the teacher-root census), and **the Gravy census pre-step**, each on Joe's go. **The corpus** stays gated on my pilot review, with §3 declared in its manifest. **The gate** additionally requires the §2 fix. Approval certifies the build as written, not the run as executed.
