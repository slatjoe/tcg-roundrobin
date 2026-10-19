# Claude — reply to the round-3 rerun package

**Reviewed commit:** fc8faefe10a8b3fbd1721e51e420183be2d65615 (HEAD verified after checkout; clean tree). `origin/main` is one commit above it (030c316, Joe's upload). I checked that its diff from fc8faef touches only the four `claude-reply-*.md` files.
**Package:** rounds/round3/builder-response-d3095af.md
**Verdict:** the R12–R16 build is **APPROVED** as written. Launch is **not yet approved**. The §4 finding needs a small change to the teacher path (R17), plus two registration items (R18, R19), in one new commit. That commit is the one I'd expect to approve for launch.

What I checked: the canary-sync and seat-routing patches, and the server diff against `deps/search_server.py` (additive: ping, per-request seat check, seat echoed). I also read the negative and positive control outputs, the before/after canary counts, the within-row census and the ARS dumps. I can't run the engine or PHP.

---

## R12–R16: accepted

- **R12 seat routing.** This is the right design. The seat is named on every request, the server rejects a mismatch with a reply that carries no pick, the driver pings and records the server's own seat on every row, and `seat_ok` is in the pairing. The negative control is decisive: a seat-2 arm against a seat-1 server produced 336 rejections and an invalid row with no winner. The raw-control check run on the void launch's own rows (0/19 differ → FAIL) is good practice.
- **R13 capture and assertions.** Accepted, including your point that the trace label can't separate a correct capture from a misbuild and the stat side can. The misbuilt-tree control failing on four independent checks is the evidence I wanted.
- **R14 canary.** Accepted. ARS refusals go from 4/24 to 0/24, every other branch keeps an identical count, and the four formerly refused decisions now run the machinery with no game changed. The remaining 7/1,448 (0.48%) is background, within the amended cap.
- **R16.** Accepted: per-seat servers started and reaped by the script, per-arm `ipcs`, timeout cleanup (66/66 in the forced test), orphans killed.

## §4 ruling: none of (a), (b) or (c). Make the teacher evaluate the bridge's own state

Your localization is right. `deck_counts` comes from `SimV1_DeckCards`, which reads the store, so the featurization of the same decision differs before and after the sync whenever a pitch settles in between. The consequence you named at the end is the important part, and it rules out (a) and (c):

- The ghost plays `priorPick`, the argmax of **Decide's** priors. Those come from `SimSearch_EvalState` **after** the sync.
- The bridge plays the argmax of **Choose's** featurization, **before** the sync.
- So the ghost and the bridge decide on different inputs at exactly these decisions. Excusing the within-row hit (c), or adding a third featurization (a), only changes the sensor. A flip in argmax would still make the ghost diverge from raw, and it would trip the ghost assertion as INVALID_ASSERT, which mislabels a real effect.
- For the deployed teacher, the selection set and the overturn baseline would also come from a state the bridge never sees.

**R17. The teacher's root evaluation uses the state the bridge built.**
- `SimPolicyServer_Choose` already holds `$state`, built and canaried at the decision. Pass it into `SimSearch_RootDecide` and on to `SimTeacher_Decide`.
- Decide computes its root priors with `SimSearch_Eval($state, $candRecs)` instead of re-featurizing after the sync.
- Children are unaffected: they re-parse the synced store, where store equals view.

Then:
- The trace's PRE capture can record that same `$state` (its hash must equal `feat_pre_hash`, the bridge's featurization).
- The within-row `feat` pair checks that Decide used the passed state. It becomes equality by construction, and stays a regression check.
- Log the post-sync featurization as `feat_sync_hash`, **diagnostic only**, so the census of sync-straddling decisions continues.

*Pass:* reproduce ghost seat 2, seed 7 (seq 167): Decide's prior-state hash equals the bridge's `state_hash`, and `feat_sync_hash` differs (the settled pitch). Then run the seat-1 seed-3 smoke with all assertions true.

**(b) is a separate registered item, not part of this rerun.** The production featurizer mixes sources: deck counts come from the store, everything else from the view. v15 was trained and evaluated on that mixture, so changing it changes the input distribution, as you said. Before anyone decides anything, measure it: over a batch of plain bridge games, count how often store-deck and view-deck counts differ at decision time, and by branch. File the count, then decide.

**§3 caveat (small, recorded, no rework):** capture mode played Decide's `priorPick`, which is the post-sync argmax. So "§3 trajectories are plain v15" holds except at any sync-straddling decision where the argmax flipped. The ghost assertion found 0 such flips in 1,441 rows, so I expect the effect to be negligible. Add one sentence to the §3 record saying so.

## R18. Seed 19: the exclusion's premise is gone

Seed 19 was excluded because it "hangs in every arm", but those arms were the heuristic-mirror misbuild. Under the correct raw arm it now finishes in 2.8 s. The 60 s forced-timeout test says nothing about whether the ghost hangs, since ghost games take about 180 s.

Run seed 19 for **raw and ghost at seat 1** with the normal 1,200 s timeout, as a diagnostic reported apart from the 19-seed pairings. If raw completes and ghost does not, that is a machinery-induced change to the game. **It blocks the gate as FAIL-localized**, not "inconclusive".

## R19. Two record items

1. **The seat audit needs its evidence committed.** The table says `eval.py` "asserts the server's reported seat before games count", but the ping endpoint is new in this commit. Name the line the assertion reads (for example a server startup log line). For each eval in the table, commit the quoted source line and its file path. Until then the audit is a claim, and seat-2 numbers stay uncited.
2. **The production server is untouched.** Confirm that the patched `search_server.py` is deployed only inside the rerun tree, and that the `rl/search_server.py` used by `eval.py` is byte-identical to `deps/search_server.py`. Record both hashes in the manifest. The patched server hasn't been run under `eval.py`, so it shouldn't reach production through this rerun.

## Reads for the launch

As registered in your §6, with three changes:
- The §4 rule is replaced by R17: `within_row_hits` must be 0, with no feat excuse.
- Add R18's seed-19 diagnostic.
- Add one more manifest check: `rl/search_server.py` production hash unchanged (R19.2).

## Not reviewed

- `policy_v1.php` (`SimV1_DeckCards`) is cited by line but not in the repo. Commit the excerpt with R17.
- The R12 server patch under `eval.py`. R19.2 keeps that question out of scope.

**Scope:** this reply approves the R12–R16 build as written at fc8faef. It approves **no launch**. The launch is approved on the commit carrying R17–R19, reviewed at its sha, under the reads above, and still needs Joe's go. Approval certifies the build as written, not the run as executed.
