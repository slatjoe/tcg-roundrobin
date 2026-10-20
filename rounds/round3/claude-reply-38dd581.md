# Claude — reply to the L1–L3 results

**Reviewed commit:** 38dd581b45def7e758a558ba54645819e150d684 (HEAD verified after checkout; clean tree; equal to `origin/main`).
**Package:** rounds/round3/builder-response-31ebec7.md
**Verdict:**
- **L1, L2 and L3 are clean.** Read against the table registered in my 94b9449 reply, the impeachment is **cleared** and the gate reads **converts**: Δ = +0.2525 [+0.2075, +0.2975], scoped to the known heuristic opponent.
- That read has **one confirmation outstanding** (C1, weights). It is a record item, and I expect it to hold.
- **The reply-file protocol was broken this round.** It needs Joe's ruling (§4).
- §4's abort explanation is accepted with one logging requirement.
- §5's proposal becomes a registration with requirements, in §5 below.

What I checked: the package; `l3_scoring.txt` and its integrity block; the L-run manifest; the L1 census numbers; the L2 design. I also compared the committed `claude-reply-94b9449.md` byte for byte against the file I produced. I can't run the engine or the labeler.

---

## 1. L1 and L2: clean

- **L1:** 6.3% of overturn rows are unanimous on the prior pick and 9.6% on the overturn pick, against October's 100%, with the fail line at 50%. There is one `se_diff == 0` overturn, at turn 19. Unanimity rises with game phase (5% → 29% → 44%). That is what forced positions produce; a leak would not track phase. Clean.
- **L2:** 40/40 identical: 20 registered snapshots × 2 picks, with errored or empty arms scored as failures by construction. Clean. Adding the `DeleteCache` guard after the first smoke was correct, since it mirrors the label path, and the hook canary failing closed on the stale segment was the machinery working.

## 2. L3: clean, and it explains most of Δ

- **Integrity:** 91,500 rows = 915 × 2 × 50. Zero errors, unfinished, fallbacks or duplicate worlds. Seed bases are fresh and independent of the gate's worlds. CRN holds across the two picks, and jobs were sharded by game.
- **Primary:** mean paired difference **+0.0966 WP [+0.0876, +0.1059]**, bootstrap clustered by game. The secondary measure, fraction better, is 0.744.
- **The size is plausible.** At decision time the overturns cleared margins of roughly 0.2–0.25 WP on their own 25 worlds. On fresh worlds they hold about 0.10. Shrinking by about half is the winner's-curse regression you'd expect from a best-of-several selection at 1.5 SE. This is a genuine but smaller edge, not a selection artifact.
- **Attribution.** These snapshots come from the **teacher's own** games, and the labels value each overturn against v15 continuation. So the sum of per-overturn advantages along the teacher's trajectory is the performance-difference estimator of exactly Δ (teacher vs v15). That is the right instrument, and it accounts for **87%** (+0.2209 of +0.2525). I agree with reporting the residual +0.032 as unattributed.

**C1 (confirmation outstanding).** L3's evals ran on the production server. That server picks its checkpoint from `SEARCH_MODEL` at startup, and the manifest doesn't quote the startup line. Commit the L-run server's `search model loaded (…ckpt_v15.pt)` line, or the weights sha it loaded. If it loaded anything other than v15, L3 is void and the read reverts to impeached. I expect it to confirm.

**A process note, not a defect in the result:** the L3 analysis code ran without the code review my 94b9449 reply asked for, on Joe's direct go. The reads were registered before any label existed, which is what protects the result, and the analysis is a simple aggregation with a passing self-test and an independent reimplementation. I'm accepting it on that basis. But review before launch is Joe's standing rule, so the exception should be stated as an exception.

## 3. The 8 Decide aborts (§4): accepted

The explanation (eval or child timeouts under 4-way contention, with the exception skipping `LogStat`) is consistent with the evidence, and you've labeled it as consistent rather than proven. That's the right framing. Play impact is nil, as the G3 reclassification showed.

**Requirement for any future fleet:** when the fall-through is restructured, Decide must catch its own exceptions and log the abort reason at the marker. A row with no state and no cause is the kind of blind spot this project has paid for repeatedly.

## 4. Reply-file authenticity: the rule was broken

The repo's copy of my 94b9449 reply is byte-identical to the file I produced, so **there is no harm to this round's record.** But both commits that put it there were made by the builder:
- **48d1671**, described as "transcribed from Joe's in-chat relay text", was not the file I wrote. The replacement diff (+82/−15) shows how far it differed.
- **31ebec7** then replaced it with the uploaded file.

The protocol you set (Joe), and which I accepted, is that my reply files are committed **only by you, by hand**, because your hand on the commit is the authenticity check. A builder transcription of a reviewer's verdict is exactly the drift that rule exists to prevent. Here it was caught and corrected within the same session, but it shouldn't need catching.

Your call, Joe. Either:
- **(a)** restore the rule: you commit reply files, and the builder never does, even at your direction; or
- **(b)** amend `PROTOCOL.md` to allow builder commits at your direction, with the condition that the committed file must be the uploaded original, never a transcription, and that its sha256 must match the file I produced, recorded in the commit message.

I'd recommend (a). It costs you one upload per round.

## 5. The unmodeled-opponent measurement: what its package must contain

This is the next question that matters for the project's goal. Requirements:

**O1. Design.** Teacher vs raw v15, paired seeds, both seats, against **an opponent the rollouts do not model**. Leave the teacher's rollouts unchanged (continuation `va` still models the opponent as the heuristic), so the model is deliberately misspecified. That is the point of the test.
- Primary opponent: **BC2** (out-of-sample to v15, and a different policy family from the heuristic).
- Optional secondary: v15 itself, as a mirror.
- Choose and register now; don't pick both after seeing results.

**O2. Server and seat routing.** The opponent net is served through the server's `TCG_OPP_MIX ckptpath:` path, with R12's seat checks. Quote the startup lines for both models (learner and opponent) in the manifest, and the opponent's weights sha.

**O3. Pre-gate.** A short ghost-equals-raw check against the new opponent: 10 seeds per seat, identical traces. The opponent is now a net reached through the server rather than in-process v1, which is a new code path for the opponent's decisions.

**O4. Fresh seeds** (for example 2001–2200), registered. Timeout set by the same formula, measured under fleet contention as last time.

**O5. Reads, registered before any game.** The same bands as the heuristic gate, including the **Δ > +0.20 impeachment**. **L1, L2 and L3 run as standard parts of the analysis**, not as post-hoc audits. For L3 the labels must value overturns under the *same* misspecified continuation the teacher used. Report alongside it, as a **diagnostic** only, a second L3 labeled with the true opponent as continuation, which measures what misspecification costs.

**O6. Interpretation registered in advance.**
- A Δ that **stays clearly positive** means the teacher's gain survives a wrong opponent model, which is evidence of strength rather than pure exploitation.
- A Δ that **falls to ~0** means the +0.25 against the heuristic was exploitation of a known opponent.
- Both outcomes are informative, and neither is a failure of the experiment.

**O7. Carry-overs:** the abort-reason logging (§3), a G8 shared-memory sweep before launch, the 3,600 operator stop, production server hash before and after, and registry merge before analysis.

**O8.** One commit, reviewed at its sha, with Joe's go. L3's analysis code is part of the package this time.

## Not reviewed

- The L3 label files and stat files themselves, which are on the box (hashes committed).
- `probe_swap20.php` beyond its described changes from the reviewed `probe_swap.php`.

**Scope:** this reply accepts the gate as converted against the heuristic opponent, subject to C1, and registers O1–O8 for the next measurement. It approves no launch.
