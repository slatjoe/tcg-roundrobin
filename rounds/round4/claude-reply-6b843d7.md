# Claude — reply to the round-4 O-results

**Reviewed commit:** 6b843d78b4039abc4a38dadd633272be06610b61 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-1f092f3.md` hashes to `4d9b3793…69191f59`, the value I gave Joe.
**Package:** rounds/round4/builder-response-6d25014.md
**Ruling:**
- The impeachment is **lifted**. The O result **converts under misspecification**, under the registered band, at the stated dose of **5.3% disagreement per server-queried opponent decision against BC3**.
- This is subject to **C2** (§1): commit the row files so the primary can be recounted, as I did for the gate. I expect it to hold.
- §3 records a finding from the five canary aborts that matters beyond this measurement.

## 1. The audit and the ruling

On every condition of the precedent registered in my 94b9449 reply, the O fleet reads the same way the gate did:

- **G3:** 73 identical units, 327 legal divergences, 0 machinery defects. The 5 DUP_SEQ units are the abort-marker class, now self-explaining through the §7 patch. With only the marker removed, all 5 reclassify as legal overturns (`dupseq_recheck.txt`, which I read).
- **L1:** clean. 13.4% of overturns have either pick unanimous (fail line 50%), and the one `se_diff == 0` overturn is at turn 23.
- **L2:** 40/40.
- **L3:** the mean paired difference is **+0.0908 [+0.0832, +0.0985]**. The integrity block is complete (91,000 rows, all zeros on the failure counters). The per-game gain of +0.2066 covers Δ in full.
- **Calibration:** predictions sit below outcomes in every bin, the conservative shape.
- **Fleet hygiene:**
  - build hash `8f6b35da…` as conditioned
  - both servers' startup lines show v15 learner and BC3 opponent, with weights hashes matching the selection table
  - fallbacks and seat mismatches 0, 0 timeouts
  - registry merged before analysis
  - production unchanged

**Read:** Δ = **+0.2050 [+0.1625, +0.2450]** clears "Δ ≥ +0.05 with lower bound > 0". So the result **converts under misspecification, at a 5.3% dose.**

**C2.** Unlike the gate package, this one doesn't commit the 16 row files or the chunk manifests. Every number in §2 therefore comes from the analyzer's printed report, and I can't recount it. Commit `o_c*_{teacher,raw}_s*.jsonl` and their manifests. I'll recompute Δ, the CI, the discordants and the validity checks from them, as I did for the gate. If the recount matches, the ruling stands with no further action.

## 2. What the conversion means, written into the record

- **The dose is low, and the test is correspondingly weak.**
  - BC3 departs from the heuristic on about 5% of its queried decisions, and that figure is diluted by forced moves.
  - Every opponent the project has measured under 10%. The registered ceiling statement applies.
  - The result shows the teacher's gain **survives a mildly misspecified opponent**: Δ moved from +0.25 against the heuristic to +0.205 against BC3.
  - It does **not** show general strength. The opponent pool sets that ceiling, not the teacher.
- **L3's full attribution is computed inside the teacher's own (heuristic) model.** The relabel continuation is `va`, as registered, so "100.8% of Δ" means the overturns' value under the heuristic model accounts for the real games against BC3. That suggests misspecification cost little at this dose. Pricing it directly is what the diagnostic `vb` would do.
- **Raw v15 scores 0.545 against BC3, against 0.450 against the heuristic.** BC3 is the weaker opponent for v15, which is consistent with the round-robin (v15 beat BC3 0.585). The paired design makes Δ comparable anyway. But the two Δs come from opponents of different strength, so they aren't a clean before/after on misspecification alone.

## 3. The five canary aborts are not a fair-play event, but they are a real finding

Each abort reads `SimFeat_Canary LEAK for player <learner>: <own card> ×N (legal ×N−1)`: two of the **learner's own** cards, each counted once too often in the root state.

- **It is not opponent information.** The cards belong to the learner's own seat. Both decklists are identical, but the canary attributes the excess to the learner's state.
- **The same state array passed Choose's canary moments earlier.** Under R17, Decide re-canaries Choose's `$state`, but **after** the checkpoint sync. The array didn't change. What changed is the zones the canary uses to establish legal counts: the sync moves store := view.
- **The mechanism this points to is the mixed-source featurization** registered last round as item (b). The deck counts come from the **store** (`SimV1_DeckCards`), and everything else comes from the **views**. Between syncs, a card that has just moved can sit in a view zone (hand, for example) and still be in the store's deck, so the featurized state counts it twice. Choose's pre-sync canary judges legality against the same mixed sources and passes. The post-sync canary judges it against consistent sources and catches the double count.
- **Consequence:** the bridge, and therefore v15 in every eval this project has run, sometimes decides on a state that **double-counts its own cards**. The canary caught 5 at teacher roots, after the sync. Before the sync, the bridge's own canary can't see this class at all, so the true frequency in ordinary play is unknown.

This doesn't touch the O read. Both arms play on the same featurization, and the 5 aborted decisions played the bridge pick. But it moves item (b) from "register and measure later" to **the next measurement to run**, before any training or new fleet. Run an inference-only census over a batch of plain bridge games: at each decision, compare the store-derived and view-derived deck counts for the deciding player, and report the rate of disagreement by branch. If the rate is material, a featurizer fix is a production change (it alters v15's inputs everywhere) and needs its own registration and re-evaluation. That's exactly why the frequency should be known first.

## 4. Next steps, in my order

1. **C2** (rows and manifests committed, then my recount).
2. **The (b) census from §3:** inference only, cheap, and it bears on the input integrity of everything trained or evaluated so far.
3. **The diagnostic `vb`:** optional at this dose. If run, its code comes back as its own reviewed commit, as registered. I'd rank it below the next item.
4. **The project's real test:** with every available opponent under 10% dose, further misspecification work has a low ceiling. The hero-transfer pipeline test (the same labeling and teacher on a second hero) and the cost question (372 s per game) are where the next information is.

## Not reviewed

- The row files and chunk manifests (C2).
- The L3 label outputs and stat files, which are on the box with hashes recorded.

**Scope:** this reply lifts the impeachment and rules the O result converted under misspecification at the stated dose, subject to C2. It approves no launch.
