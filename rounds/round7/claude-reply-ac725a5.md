# Claude — reply to the round-7 calibration, steps 1–2

**Reviewed commit:** ac725a5d90523d3a1523d3ddf3042a6b199186db (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-ba4e9c9.md` hashes to `a054c0bc…15ad1ae4`, the value I gave Joe.
**A note on `claude-reply-2706e33.md`:** that reply was produced in a session whose files I can't see from here. Its committed sha256 (`64603119…92d185`) matches the value recorded in f4c7de5's commit message, and its content is consistent with my registrations. I can't cross-check the hash against a copy of my own in this session, so Joe's upload is the authenticity anchor for that one.
**Package:** rounds/round7/calibration-steps12.md
**Verdict:** **ACCEPTED.**
- The trigger-at-35 finding is established from code and reconciles the gate exactly.
- H = 0.6721 is computed correctly under the registered formula, and lands in the **≥ 0.40 band**.
- The open-item restatement (319 recoverable, 1 not) is accepted.
- One refinement must be registered **before** any re-specified gate is drafted (§3): the decision cap. It is set from the heuristic mirror's records, not the anchor's.

## 1. The trigger-at-35 finding: accepted

This resolves the inconsistency I flagged in 2706e33 §2, and it resolves it from code:
- `play_game.php:336`: `$capTrigger = $maxTurns − 25`, with the margin's purpose commented at :334–335
- `rl/eval.py` defaults `--max-turns` to 60, and the anchor gate passed none
- the result row's `turns` is the engine's `currentTurn`, the same counter as the state's `turn` and the feature's `turn/30`

**Reconciliation.** I checked the arithmetic: 0.72 × 36.07 + 0.28 × 26.18 = **33.30**, the reported pooled mean. A cap-at-60 reading would force a mean of at least 43.2. The split method is sound:
- the last-query turn comes from `sv[0] × 30`
- it is validated against the exact per-half totals (shortfalls of 39 and 43, about 0.2 turns/game)
- the class assignment relies on monotonicity in game length, with the boundary handled by the count identity
- the range is given across three shortfall allocations

The capped games' recorded turns (34–43, median 36) confirm the trigger empirically. You were also right to state that the gate workdirs persist no per-game result rows, and that the split is derived.

**What this changes in the record.** Round 3's "engine turn cap 60" was correct as a *parameter* and misleading as a *behavior*. Fai's games never reached 35, so the distinction never mattered until a hero whose ordinary games run past 35 hit it. Any future package that cites a turn cap must state both the parameter and the trigger.

## 2. Step 2 and H: accepted

**Fai composition.** 0 capped of 333 (69 + 81 = 150 wins, 165 + 168 = 333 games), mean 15.06 turns, under the same `--max-turns 60`. The partial-completion note (the timed-out runs, traj games one higher than counted games) is properly carried. This confirms the 0.40 line was drawn on an instrument where the cap never bound.

**H.**
- **The unit test passes.** Both harnesses consume the same `PlayOneGame` emitter on the same engine, so `turns` is one counter, and the only cap difference is the turn parameter (750 vs 60).
- **"Exceeds the eval cap"** is correctly read as the count at which the protocol ends games, 35, not the bound on a capped game's recorded turns, 60. My registration said "the eval cap" without anticipating the trigger. Your reading is the one that matches what the protocol does, and the gate's own 35–44 recordings show it.
- **H = (479 + 1,134) / 2,400 = 0.6721, Wilson95 [0.6530, 0.6906].** I reproduced the interval.
- Tabling all four readings was the right disclosure. None of the alternatives changes the band except the > 60 readings, which answer a different question, as you say.
- **Band: ≥ 0.40.** Under the rule fixed in 2706e33, the protocol doesn't measure Gravy play at this cap, and the anchor's 0.1475 is not evidence about the anchor. **The stop's reason is now known to be the instrument.** A re-specified gate *may* come back as a registration.

I couldn't recompute H independently, because the mirror_self rows aren't in the repo. The arithmetic is internally consistent, and the result rests on the box records as reported.

## 3. Refinement before any re-specified gate: the decision cap

The registered terms for a re-specified gate addressed only the turn cap (set from the mirror's decided-game p99, which is 62). Your own decomposition shows that isn't enough:
- **421 of the mirror's 479 already-capped games hit the decision cap** (`TCG_MAX_DECISIONS` 3,000), not the turn cap.
- The eval protocol uses the same 3,000 default.
- So a gate with only its turn cap raised would still cap about **17.5% of the heuristic mirror** on decisions, plus roughly 1% above a 62-turn trigger. That leaves the mirror's capped share near 0.21, short of the band where the instrument is clean.

To keep the refinement legitimate, it is drawn **only from the heuristic mirror's records**, under the same principle the rule used:

**R1. Both caps, from the mirror.** A re-specified gate sets two things:
- **its effective turn trigger** at no less than the mirror's decided-game p99, which is **62**. The *parameter* then follows from the trigger formula: `TCG_MAX_TURNS ≥ 62 + 25 = 87`. The registration has to state both, because a parameter of 62 would trigger at 37 and reproduce the problem.
- **its decision cap** from the mirror's decided-game distribution of policy queries at p99. If the corpus rows carry a decision count, read it from them. If they don't, state that, and the registration proposes how to measure it.

**R2. Show the instrument is clean before using it.** From the mirror's records, compute **H′**: the mirror's capped share under the re-specified caps, counting every cap reason. **The re-specified gate is registrable only if H′ ≤ 0.10**, the same standard as the low band ("the instrument isn't what failed"). If no p99-based setting reaches H′ ≤ 0.10, report it and stop; that comes back to me and Joe.

**R3. Everything else stays as registered:**
- capped games score as non-wins
- the 0.40 line is unchanged
- the floors stay at 0.30
- the anchor is re-gated **unchanged** (`1e6e3906…48eac288`), with 400 seat-balanced games through `rl/eval.py`, on **fresh seeds**, registered before the run, with server logs showing fallbacks = 0
- the gate's games go to the registry before the read is used

**R4. Cost and comparability, stated in advance.** Games that run to the mirror's natural length take longer (Gravy decided games average 37 turns against Fai's 15). The registration should estimate wall time from the mirror's distribution.

The re-specified gate is a different instrument from BC3's 0.450 gate. It is comparable in what it measures (play, not length) because both are now near-uncapped on their own hero's mirror (Fai: 0 of 333). The results must report both instruments' capped shares side by side.

Whether to bring that registration at all is Joe's call. Path (a), accepting the stop as the finding, remains available. But the calibration now says the stop recorded game length, not the anchor, so (a) would close the transfer question on an instrument artifact. I'd recommend the re-specified gate.

## 4. Open items

1. **The 320 loose games: accepted as restated.** 319 are recoverable and 1 isn't (the chunk-c0b game that never reached the server's records). **The 319 ids sit on tmpfs, and only 80 of them (census and pick-flip) have repo copies.** Don't leave the rest exposed:
   - merge all 319 into the do-not-train registry now, eval-only and tagged by group, with Joe's go
   - commit the id lists to the repo as the durable record
   - record the one unrecoverable game as a note in the registry's provenance

   This is bookkeeping, not a measurement, so it needs no code review.
2. **Registry durability:** the package says the registry and its backup were copied to persistent storage on 2026-10-22. State the path and both hashes in the next package.
3. **Anchor hash linkage:** still owed. Confirm that the stage-2 manifest records `1e6e3906…48eac288` for `bc3_policy.pt`. R3 depends on it.

**Scope:** this reply accepts calibration steps 1–2 and the records branch of step 3, rules H in the ≥ 0.40 band, and registers R1–R4 as preconditions for any re-specified anchor gate. It approves no launch. The stop stands until a re-specified gate is registered, reviewed and run under Joe's go.
