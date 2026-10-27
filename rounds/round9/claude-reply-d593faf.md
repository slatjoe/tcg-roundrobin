# Claude — ruling on the round-9 Stage 2 report

**Reviewed commit:** d593faf2de9e0099115315ec44e417028739bf22 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-4050036.md` hashes to `3f33507d…f410a3e`, the value I gave Joe. The correction in report §4 is accepted: the misstatement was only in a commit message. No code changed after the confirmed analyzer.

**Ruling: PROCEED stands.** I recomputed every figure from the published rows (§1). Stage 3 is registered on the terms in §4, for a launch package.

## 1. Recomputed from the raw rows

My own code, using neither `stage2_analyze.py` nor `stage2_games_report.py`:

**The data.**
- `labels_all.jsonl.gz` decompresses to **35,300 rows** with sha256 `f5f1522c…`, which equals the pre-run record.
- There are 353 jobs and 706 candidate groups, each **exactly 50** worlds.
- **4 worlds are unfinished** (`abort`, 2 per arm), and there are 0 refusals.

**The reads.** Each job's paired diff is computed over its shared finished worlds. Jobs are weighted equally, and the CI is a 10,000-draw bootstrap clustered on the 152 games.

| Read | Jobs | Mean diff | 95% CI |
|---|---|---|---|
| **Primary (draw = 0)** | 353 | **+0.0621** | [+0.0437, +0.0810] |
| Draw = 0.5 | 353 | +0.0494 | [+0.0351, +0.0645] |
| Life-differential | 353 | +0.0451 | [+0.0293, +0.0621] |

The means agree exactly with the report. The CI endpoints differ only by bootstrap draw, in the fourth decimal.

**The live rates.**
- Over the 200 completed games there are 5,087 contested teacher rows, 0 thin-prior and **353 overturns**. That's **1.765 per game**, and 0.0694 of contested decisions.
- The overturns match the 353 jobs one-for-one by (game, prior pick, teacher pick), over 152 games.
- All 20,009 teacher rows carry the exact H8k-180+H stamp, and there are no ghost rows.

**The verdict.** Per-game gain = 0.0621 × 1.765 = **+0.1096**. The CI lower bound is above 0, and the gain is at least +0.05, so the result is **PROCEED**. Both tripwires are far away.

**The games.**
- 200 of 200 seed–seat pairs completed, with 0 timeouts.
- **87W / 41D / 72L**: seat 1 went 45/19/36 and seat 2 went 42/22/36.
- All 41 draws are turn-cap games.

**The 20,013 − 20,009 difference: explained.**
- The four extra lines are not teacher rows. They are `{"branch":"M","fallback":"canary","missing":{…}}`, written by `SimSearch_RootDecide`'s R14 root canary (`search_s2.php`, about line 1276) when the missing-card conservation check refuses a root decision. That decision then goes down the plain bridge, raw v10, and no teacher row is written.
- That's 4 refusals in about 20,013 root decisions. The round-7 fleet logged 13 against 37,120 teacher rows, the same order of magnitude.
- **Immaterial and expected.** The Stage 3 report should name the class instead of carrying an unexplained count.

**The two "absences" in report §2.** The L2 sensitivity line and the per-game table are **tripwire-conditional by registration**, printed only when a tripwire fires. None fired, so nothing is missing. Say so in that sentence of the report.

## 2. What the result means, and what it doesn't

**What it establishes.**
- The calibrated teacher's overturns carry a real per-decision edge under the competition price.
- All three pricings agree in sign and exclude 0.
- The horizon closed the coverage problem in live play: thin-prior was 0, unfinished 0.01%, and 0 of 353 jobs were unpaired.

That's the question Stage 2 was registered to answer, and it answers it.

**What it doesn't establish:** a game-level win.
- The +0.11 per game is an L3 valuation. It's the value of the overturned choices measured by rollouts under the rollout continuation, not against the live opponent, and not counting how decisions compound.
- **Round 7's lesson was that this projection can overstate.** Its read was PROJECTION OVERSTATED.
- The Stage 2 games are already a caution. The teacher won 87 of 200 (0.435, about ±0.07). Round 7's raw v10 won 163 of 400 (0.408) on a different seed block. If the +0.11 converted one-for-one, a win rate near 0.52 would be expected.
- These are unpaired and on different seeds, so this is a caution, not a test. **Stage 3 is the test.**

**A post-hoc note on round 7 (no verdict changes).**
- Re-scoring round 7's published paired rows at the now-settled draw = 0 price gives fleet Δ **+0.0254 [+0.0025, +0.0509]**. That's 393 complete pairs with timed-out pairs dropped and a seed-clustered bootstrap.
- At the 0.5 price it read +0.0165 [−0.0026, +0.0371].
- Round 7's verdict was registered at 0.5 and stands. This is labeled post-hoc.
- It is consistent with Stage 0's positive result: the old teacher's few completed overturns may have had a small real edge that the 0.5 price diluted.

## 3. On the runs

- **Labeling attempt 1:** the G8 guard reported game processes while the process listings showed none, and the cause wasn't established. G8 is Stage 3 containment, so **the Stage 3 package explains this** (from the guard's code and the attempt's log) **or adds a fixture** reproducing whatever condition fired it. An unexplained containment trip shouldn't carry into a 800-game fleet.
- **Labeling attempt 2:** the full /tmp was caught by the installed-file pin, as designed. **Stage 3's runners check free space** before copying trees, and abort with the required and available sizes.
- **The read run:** it met all four §3 conditions. The pre-run hash equals the post-run hash, which equals the published labels.

## 4. Stage 3 registration terms (for the launch package)

1. **Form (design §6, round 7's structure):**
   - paired calibrated teacher against raw v10;
   - Gravy mirror against the heuristic, instrument 87/62;
   - **seeds 23001–23200 × both seats × both arms = 800 games**.
   - The teacher is `search_s2.php` `85490e8e…` with the H8k-180+H tuple, pinned, stamped and audited exactly as in Stage 2.
   - Raw is v10 on the same tree with the teacher off.
   - Every overturn is captured.
2. **Pre-gate:** Stage 2's IDENTICAL pre-gate covers this exact build and tuple. The Stage 3 games runner carries the `PREGATE-GATE` block against that manifest. **Any change to the build or the tuple requires a new pre-gate.**
3. **Primary read:**
   - **pooled paired Δ at draw = 0**: a win scores 1, and a draw, cap or loss scores 0;
   - CI from a seed-clustered bootstrap, B = 10,000, with both seats in a seed's cluster.
   - **Co-reports:**
     - Δ at draw = 0.5, for round-7 continuity;
     - **game-level life-differential**, where a capped game scores by life at the cap: ahead = 1, behind or tied = 0. In Stage 2 the teacher was ahead in 25, behind in 13 and tied in 3 of its 41 capped games. This is the top-cut price;
     - per-seat Δ.
4. **Bands:**
   - **CONVERTS** iff the CI lower bound > 0;
   - **DOES NOT CONVERT** iff the CI includes 0;
   - **HARMS** iff the CI upper bound < 0 (made explicit);
   - **Δ > +0.25** → impeachment checks print before the read.
   - **Precision**, priced from round 7's paired rows at draw = 0: a 95% half-width of about **0.024** at 393 pairs. So 400 pairs resolves an edge of about +0.05, and the conversion question has real power.
5. **Timeouts:**
   - **The value: 3,214 s, kept.** Stage 2 **is** the contention probe the design asked for, 200 games at the calibrated setting and 4-block contention. Its game wall was mean 503 s, p95 807 s and **max 2,143 s**, so 3,214 s is 1.50× the observed maximum, with 0 timeouts.
   - **Why not the product of maxima:** that derivation is retired. Stage 2's contested-per-game max was **90**, against round 7's 57, while the per-decision wall fell (mean 19.5 s, max 59.8 s). The direct game-wall measurement replaces the product.
   - **The condition:** the teacher arm runs at Stage 2's concurrency (4 blocks over 2 servers), and the raw arm is **not concurrent** with it. Higher concurrency needs its own probe.
   - **Scoring:** a teacher timeout counts as a teacher **loss** (primary), with a drop-the-pair sensitivity table. **Teacher timeouts > 2% of teacher games → INCONCLUSIVE**, read on final counts.
   - **Raw hangs:** one re-run. A second hang **drops the pair** and is listed. At draw = 0, a draw score would credit the teacher, so round 7's 0.5 rule doesn't carry.
6. **Attribution (co-report, not a gate):**
   - L3 on **all teacher-arm overturns** at the Stage 2 label instrument (L3-W50+H, CRN, va), with a fresh label seed family. The package proposes it and shows it's clear of 855001 and 955001.
   - Report the per-game gain, the Stage 3 live rate, and **per-game gain ÷ Δ** (the Fai gates were 87% and 101%).
   - That's about 700 jobs, roughly 2–3 h. It answers directly whether L3 overstates.
7. **Cost, from Stage 2 actuals:**
   - The teacher arm is 400 × 503 s ≈ **56 box-hours serial**, about 14 h of wall time at 4 blocks.
   - The raw arm runs at raw speed, and L3 adds 2–3 h.
   - Plan about **18–20 h of wall time**, priced in the package from these rows.
8. **Standing:**
   - containment, with the G8 item from §3;
   - the free-space pre-flight;
   - registry merge before analysis;
   - status-only notices;
   - pins format-asserted;
   - verbatim-extraction fixtures for every spawn or wait block;
   - **new: a round-trip fixture for every writer/reader pair**, with the reader fed the writer's real output, including the games-report → analyzer and pre-gate → gate pairs;
   - publication of `data/stage3/`.
   - The tracker's phase rule as amended, with "complete" only on the final read file.

**Scope:** this accepts the Stage 2 report (PROCEED, recomputed and verified) and registers Stage 3's terms. It approves no build and no run. Stage 3 launches only on my approval of its package and Joe's go.
