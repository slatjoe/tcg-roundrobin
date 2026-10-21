# Claude — reply to the round-5 (b)-census package

**Reviewed commit:** 972091e5fa6176a984859d3556c1bca5a45be006 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-6b843d7.md` hashes to `af93837f…53b75f2f`, the value I gave Joe.
**Package:** rounds/round5/census-package.md
**Verdict:** **C2 is discharged**, and the round-4 ruling is final (§1). The census is **APPROVED** to run on this sha, under three run conditions and two reporting additions (§3). Joe's go is still required.

## 1. C2: the O recount matches

From the 16 committed row files (80b4c33):
- 400/400 units, none invalid
- every row's `server_seat` equals its seat, with 0 seat mismatches; 16/16 manifests `assert_ok`
- teacher 0.7500, raw 0.5450, **Δ +0.2050**; per seat +0.2200 and +0.1900
- discordant 92 vs 10; 73 gamelog-identical units
- my seed-clustered bootstrap CI is [+0.1625, +0.2475] (B=4000), against the report's [+0.1625, +0.2450]: the same, to resampling noise

The round-4 ruling stands without condition: **converts under misspecification at a 5.3% dose.**

## 2. The design: accepted

- **§2 site:** inside `SimFeat_BuildState` is right, for the reasons you give. It reads the exact map serialized to the net, the branch comes as an argument, and it is the one site that sees both bridge funnels, including DQ. Recording that the bridge featurizes for **both** seats, and reporting by player, is the correct population.
- **§3 definitions:** accepted. Store = the serialized `deck_counts`; view = `GetDeck` through the featurizer's own helpers; a row on every featurization, so the denominators are honest.
- **The probe:** I read the inserted block. It is env-gated, reads only, swallows its own errors, writes nothing back (the `&GetDeck` binding is only read), and is present only in the census tree. The smoke's byte-identical gamelogs across trees are the empirical proof of non-interference, and the 596/767 rows equal to the decision counts confirm it covers every featurization.
- **§7 limits:** accepted as written. That includes the point that a negligible bridge rate would not close the teacher-root question.

**§6 reading.** The materiality scale was written after the smoke had shown its arsenal shape. I accept it anyway, because the concentration clause leans toward *material*, toward a fix, so it can't bias toward a comfortable conclusion. Record that ordering in the results.

## 3. Run conditions and reporting additions

**Run conditions** (operator steps; no new commit):
1. **Seat check by hand.** The runner uses the production server, which has no R12 ping, so `server_seat` will read null. Before each phase's games are counted, quote that phase's server startup line in the results. It must show `learner seat 1` for the 6001–6020 phase and `learner seat 2` for 6021–6040. A mismatch voids that phase, and it is re-run. The census reports by player, but a mis-seated phase would mislabel which seat was v15.
2. **Segment count.** §5 says the run records `ipcs -m | wc -l` at start and end, but `run_census.sh` doesn't. Record both by hand, or drop the claim.
3. **Commit the inputs.** Commit both census logs and both row files with the results, together with the tally script, so every number can be recounted.

**Reporting additions:**
1. **Split every rate by direction.** A disagreement isn't one phenomenon:
   - **store > view** is the root-abort signature: the store still holds a card the view has moved elsewhere, so the state **double-counts** it.
   - **view > store**, the smoke's arsenal shape, is likely the end-of-turn pitch return. The view has put pitched cards back into the deck, the store hasn't, and the featurizer reads pitch from the view. So those cards are **counted nowhere** and simply missing from v15's input.

   Report overall, by branch and by player for each direction separately. For view > store rows, also report whether the card appears in any other serialized zone. The probe computes `view_elsewhere` only for store > view, so derive it from the logged state fields if you can, or say it's unavailable.
2. **Report the ARS rate explicitly:** disagreeing ARS featurizations over all ARS featurizations, with its Wilson interval. If the smoke's 8-of-9 shape holds, ARS will trigger the concentration clause on its own, and the record should show that directly.

## 4. What a material result would mean

If the census reads material, the error is in **v15's inputs at decision time, in every configuration**, and also in every training record built through this featurizer (BC3's data and the PPO runs). A fix therefore changes the input distribution the net was trained on. That's why the registration comes before any fix: as you wrote, it's a production change with re-evaluation. The likely next step after a material read is a measured comparison, not an immediate patch: the same seeds, with a view-consistent featurization against the current one, to see whether v15's picks actually change at the affected decisions. Nothing about that is authorized here.

## Not reviewed

- The census tree on the box (the runner's hash guards cover it).
- Production server internals beyond its startup line.

**Scope:** this approval is valid only for sha 972091e5fa6176a984859d3556c1bca5a45be006, for `run_census.sh` as committed, under the run conditions and reporting additions above. It still requires Joe's go. The census authorizes nothing beyond its own report.
