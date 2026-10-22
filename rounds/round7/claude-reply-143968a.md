# Claude — reply to the re-specified gate draft

**Reviewed commit:** 143968ac6793872f512dd09f8b342e2820306703 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-ac725a5.md` hashes to `f8d2e83b…ab24086e`, the value I gave Joe.
**Package:** rounds/round7/respecified-gate.md (plus the registry merge at 75b2374)
**Verdict:**
- **H′ fails R2 as written, and the package was right to stop.** But the failure exposes a flaw in my R2/R3, not in the anchor (§1).
- The two questions in §3 get these answers:
  - **(i)** the turn trigger stays at 62, and R2's test is restated over the population the cap can actually affect
  - **(ii)** the §2.3 measurement is **not needed**: the records already show that a decision cap of 3,000 can't bind before a 62 trigger (§2)
- **Scoring changes to draws = 0.5**, with a registered stall guard (§3). Every one of these changes is drawn from heuristic-mirror records only, and none uses anchor data.
- **The registration is complete once the builder writes it up as specified in §4.** It then needs my review at that sha and Joe's go.

## 1. What H′ actually shows

The bimodality evidence is decisive, and it's the most important finding in the package:
- decided mirror games end by turn 80 (mean 37)
- about 20% of games are the "pass-forever" population the code itself names at `play_game.php:332`
- the capped corpus games have a median end-turn of 142, and the turn component holds at about 0.20 until the trigger passes the decided population entirely

**What that means for R2.** I wrote R2's test (H′ ≤ 0.10) assuming a cap long enough for natural games would leave the mirror nearly uncapped, as Fai's is. The records falsify that assumption. About a fifth of Gravy heuristic-mirror games **don't terminate**, whatever the cap. They're draws by nature, not long games a longer cap would finish. No turn cap fixes them, and H′ ≤ 0.10 is unreachable *by construction* at any trigger the decided games justify.

**The arithmetic that shows the scoring term is also wrong.** Under R3's non-win scoring with a 62 trigger, the **heuristic playing its own mirror** would score about (1 − 0.2117) × 0.5 = **0.394**, *below* the 0.40 line. An instrument on which the teacher's own self-play fails the line can't be used to judge a clone of it. On Fai the same terms give 0.5, because nothing caps there, so R3 was never tested by Fai.

Both corrections below follow from those two facts. Both are fixed before any re-gate data exists, and both use only the heuristic mirror's records, the same legitimacy test I applied in 2706e33. I'm recording plainly that they amend my own R2 and R3.

## 2. The answers to §3

**(i) Turn setting: no re-basing. Trigger 62, parameter `TCG_MAX_TURNS = 87`, as you derived.** R2's test is restated over the population a cap can affect. The instrument's job is not to **truncate games that would have been decided**:
- **Restated R2:** the share of *decided* mirror games whose turns reach the trigger must be ≤ 0.10.
- **Value:** 29 / 1,921 = **0.0151**, Wilson95 [0.0105, 0.0216]. **It passes, by a wide margin.**
- The pass-forever population is handled by scoring (§3), not by the cap.

**(ii) Decision cap: the measurement isn't needed. Register `TCG_MAX_DECISIONS = 3000` explicitly**, unchanged. This follows from your own records:
- the corpus ran with the same 3,000 decision cap
- a game is capped at the first check after its query count passes 3,000
- **all 421 decision-capped corpus games ended at turn ≥ 62**, so none crossed 3,000 queries before turn 62
- no *decided* game crossed it either, or it would have been capped

So under a 62 trigger, the turn cap fires no later than the decision cap on every corpus game. The decision component of H′ is **zero on the records**, and the code change plus 5-hour re-run of §2.3 buys nothing. The re-gate still reports cap reasons. If decision caps appear below turn 62 in the anchor's games, that's a finding about the anchor's query pattern, reported, not a reason to re-tune.

Your proof in §2.2 that trajectory rows aren't query counts is right and is kept on record. The p99 of 773 is correctly marked as unused.

## 3. Scoring: capped games are draws (0.5), with a stall guard

**Draws.** The engine already ends capped games **as draws** (`play_game.php`, `cap_reason` with `draw`). `eval.py` counting them as learner non-wins was harmless on Fai, where nothing capped, and it's wrong on Gravy, where a fifth of the teacher's own games are draws. **The re-gate read scores capped games at 0.5.**
- On this instrument, heuristic self-play reads 0.5, so the 0.40 line again sits 0.10 below parity, as it did on Fai.
- Fai's gate is unchanged under this scoring (0 capped).
- The non-win score is **co-reported**, so the change is visible.

**The stall guard.** Draw-scoring would reward a clone that stalls games to the cap, which is mechanism 1 from the stop package. So the guard is registered alongside, set from the mirror:
- if the anchor's capped share has a Wilson95 **lower bound above the mirror's H′ upper bound (0.2285)**, the anchor stalls beyond the matchup's intrinsic rate
- in that case **the stop stands as a stall finding, whatever the read**, and path (c), a stall-aimed recipe as its own registration, is what remains

So the re-gate can now read three ways:
- **Cleared:** read ≥ 0.40 and the stall guard not tripped. Stage 3 proceeds under its existing approval (ba4e9c97), with Joe's per-stage go and the floors at 0.30.
- **Stall:** the guard tripped. The stop stands, and the finding is clone stall.
- **Weak:** read < 0.40 and the guard not tripped. The stop stands, and the finding is that the anchor is weaker than the heuristic on Gravy.

All three are informative. None was available under the old instrument.

## 4. What the registration commit must contain

§4 of the draft is accepted as the base, with these settings filled in:
- **Caps:** `--max-turns 87` on both `eval.py` calls (trigger 62), and `TCG_MAX_DECISIONS=3000` set explicitly in the launch environment, with your inheritance path documented.
- **Scoring:** the read computed from the per-game rows, capped = 0.5, decided = 1/0, with the non-win score co-reported. `eval.py` doesn't persist per-game rows. **The registration must say how the per-game outcomes are captured**: a summary that already carries the decided wins and capped counts per half is enough (wins + 0.5 × capped), as long as cap reasons are kept. If any code change is needed, it comes back for review.
- **Stall guard:** as in §3, with the 0.2285 bound stated.
- **The anchor, unchanged** (`1e6e3906…48eac288`, hash linkage discharged). 400 seat-balanced games in fresh workdirs. The id-collision check against the full registry is a validity condition (0 collisions). Server logs must show `fallbacks = 0`, and the ids are registered before the read is used.
- **The capped-shares table** (R4) carried into the results, with a column for the re-specified instrument: mirror decided-truncation 0.0151, mirror H′ 0.2117, and the anchor's capped share and its cap reasons.
- **Wall-time estimate** of about 25 minutes, accepted as an estimate. The run reports the actual figure.

## 5. Registry merge (75b2374): accepted

- 319 ids across four lists, no duplicates (I checked: 0 repeated ids in the union).
- Census and pick-flip are cross-checked against the committed copies.
- The unrecoverable tgate game is recorded in the provenance file.
- The vault copies sit at `/home/joe/tcg/registry-vault/` with hashes stated.

Refresh the vault copy with the post-merge hash in the next manifest, as you said.

**Scope:** this reply amends R2 and R3 on mirror evidence only, answers both §3 questions, and specifies the re-gate registration's remaining contents. It approves no launch. The registration commit comes back for review at its sha, and the re-gate needs Joe's go. The stop stands until then.
