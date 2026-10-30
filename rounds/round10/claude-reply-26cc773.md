# Claude — ruling on the round-10 Step 1 pilot report

**Reviewed commits:** f996b27d (the report and run files) and 26cc773e4a9096b66c2465b025b99f76f92f97e0 (the label parts). HEAD was verified after checkout: a clean tree, equal to `origin/main`.
- **My last reply:** the committed `claude-reply-f349b31.md` hashes to `85200bd3…68a727`, the value I gave Joe.
- **The report:** `32d7fd37…`.
- **Code:** none changed since the confirmed f349b313.
- **The publication:** all eight `.jsonl.gz` parts decompress to their MANIFEST hashes, and concatenated they hash to `labels_all`'s **`91808248…`**. The 422 workaround is accepted.

**Ruling: DO NOT STOP stands, and Step 2 sizing at n = 72 stands as registered.** Both are recomputed below. The pilot also carries a game-level signal that changes what the next package should be (§3).

## 1. Recomputed from the published rows

My own code, with the cap-aligned scoring, CRN-paired job diffs, per-game totals over all 100 games, and a game-clustered bootstrap (my seed):

| Read | Jobs | Per-game gain | One-sided 95% lb / ub | Report |
|---|---|---|---|---|
| Contested | 172 | **0.0638** | 0.0272 / 0.1040 | 0.0638 [0.0280 / 0.1042] |
| Newly contested | 619 | **0.2008** | 0.1470 / 0.2562 | 0.2008 [0.1470 / 0.2584] |
| **Total** | 791 | **0.2646** | 0.1946 / 0.3374 | 0.2646 [0.1948 / 0.3384] |

- **The means match exactly.** The bounds differ only by bootstrap draw.
- **STOP needs an upper bound below 0.0849.** The upper bound is 0.338, so DO NOT STOP.
- **The sizing:** SE = 0.0435 and Δ_plan = 0.1299 give R = 0.0026480 and **n = ⌈71.5⌉ = 72**. That reproduces exactly.
- **Integrity:**
  - **The labels:** 0 decisive worlds after turn 61, so the §14 engine is visibly in force. Fallbacks are 116.
  - **The jobs:** class assignment agrees with top prior on all 791.
  - **The games:** 100 played, 0 invalid, 0 timeouts.
- **The fallbacks finding (§5) is accepted.** It's four early-game jobs, label path only, a −0.002-per-game effect.

**The contested class reads +0.0638, against Stage 3's +0.0649.** That's continuity: the §14 engine didn't change what the old teacher's class is worth. The lever is the newly contested class at **+0.20 per game**, inside the 0.13–0.27 band my probe ruling bounded. The probe's +0.47 really was the raw-trajectory overcount.

## 2. Cost

The realized cost is **1,773 s per teacher game**, close to the probe's 1,840 s. The ghost-based 855–993 s band was wrong in the direction §12 couldn't sign: live picks lengthen games. **Use 1,773 s for all future pricing.**

## 3. The game-level signal, and what the next package should be

The pilot's teacher went **70 W / 7 D / 23 L** against the heuristic: a 0.700 win rate at draw = 0. For comparison:

| Run | Wins | Rate |
|---|---|---|
| Stage 2 teacher | 87 / 200 | 0.435 |
| Stage 3 teacher | 174 / 400 | 0.435 |
| Stage 3 raw v10 | 155 / 400 | 0.388 |

**These are unpaired, on different seed blocks, and not a registered read.** But the gap is about 6 binomial SEs, draws fell from about 20% to 7%, and the size, about +0.27 over the old teacher, agrees with the L3 gain (+0.26). It's the first time in rounds 7–10 that the per-decision valuation and the realized outcomes have pointed at the same large number. It's worth stating plainly, and it's exactly what Step 3 exists to test.

**What it changes:**
- **Step 2 as registered** (an L3 gate on 72 fresh games against Stage 3's +0.0649) is now near-certain to pass. The pilot's one-sided lower bound, 0.195, is three times the bar.
- **The decisive open question is the paired fleet.**

**Recommendation for the next package (Joe's choice on cost):** combine Steps 2 and 3 into **one paired fleet**: threshold teacher against raw v10, same seed and same seat, on a fresh block.
- **The registered Step 2 read** is computed from the fleet's teacher arm, which must be at least 72 games: L3 on all its overturns, the two-sample bar against Stage 3. It's reported as the gate co-read.
- **The fleet's paired Δ is the primary**, with round 9's bands (draw = 0, seed-clustered CI; CONVERTS / DOES NOT CONVERT / HARMS / INCONCLUSIVE), life-differential and draw = 0.5 co-reports, and the attribution ratio under the §4 guard.
- **This saves a whole teacher arm, about 35 box-hours.** The only thing it gives up is the option to skip the raw arm, and raw games are nearly free.
- **Sizing**, by the corrected method (variance per pair ≈ (1 − p₀)·q − Δ², with p₀ = 1/100 zero-fire games in the pilot and q = 0.324 from Stage 3), at **80% power for Δ_plan = 0.14**:
  - that's the pilot's L3 lower bound 0.195 × Stage 3's observed Δ-to-gain ratio of about 0.73, deliberately conservative against the 0.27 the outcomes suggest;
  - it comes to **about 122 pairs: 244 games, with a teacher arm of about 60 box-hours, roughly 15 h of wall time at 4 blocks.**
  - At Δ_plan = 0.10 it would be about 246 pairs (about 121 box-hours). The package states the sizing arithmetic and leaves the choice to Joe.
- **Standing rules:** fresh seed block, the pilot never pooled, the registered pre-gate coverage (same build, same tuple) checked mechanically, every round-10 standing requirement, timeout 7,845 s or re-derived from the pilot's 2,676.8 s maximum (for example 3 × max ≈ 8,031 s), and publication with a MANIFEST.

**If Joe prefers the registration as written,** Step 2 at 72 games runs first (about 35 box-hours plus labels) and the fleet follows. Both paths are sound; the combined one is cheaper and gets to the answer sooner.

**Scope:** this accepts the pilot report (DO NOT STOP, n = 72, recomputed and verified) and recommends a combined Step 2 + 3 paired fleet for Joe's decision. It approves no build or run. The next package comes back for review.
