# Claude — review of the round-10 §14 horizon-alignment package

**Reviewed commit:** d17a4540fa853512a127d9efbc290125475b96a7 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-28c2065.md` hashes to `2df30e0d…efb78a`, the value I gave Joe. The doc is `cca79d7f…`.

**Verdict: APPROVED.** The recovery runs **once**, as amended by §14, on Joe's go. The mechanism is confirmed, the fix is right, and the cap-aligned scoring is registered before any read. I reproduced the rescoring from the published rows exactly.

## 1. Checks

**The mechanism and the fix.**
- The diff in both round-10 copies does two things:
  - it checks the horizon after **each** `PuzzleFinishStep()`, breaking the inner loop, with the outer check retained;
  - it makes `horizonHit` override a same-step game end (`winner = 0`), which closes the second half of the defect: the old `horizonHit && !IsGameOver()` let a trigger-crossing win stand.
- The round-9 file stays `85490e8e…`.
- The new copies are pinned in both runners: `search_s2` `1c964160…`, and `search_s3` `87779e8e…` with its hook diff intact.
- `fx_horizon.py` shows the as-built overshoot (78, 89, and a win recorded at 65), and the fixed loop stopping at exactly 62 with a turn-61 win standing.
- The boundary, decisive only at turns ≤ 61, matches the live record: 691 decisive games, maximum turn 61.

**The rescoring, recomputed by my own code from `evals_all.jsonl.gz`.** The statistic is Decide's: −1 for draws and losses, the ≥ 20-world prior floor, the best-mean challenger, paired SE, and se = 0 → +∞.

| | Would-fire at 1.5 | uncontested / diag / band |
|---|---|---|
| As run | 448 | 329 / 235 / 82 (= the 646 labeled) |
| Cap-aligned | **424** | **305 / 230 / 94** |

- Both rows match the package exactly.
- 646 − 86 drop-outs + 69 new = 629 = 305 + 230 + 94.
- The 69 supplementary jobs (8 / 32 / 29, 38 games) don't overlap the labeled set.

**The round-9 addendum.** `capalign_l3.py` reproduces both published primaries bit-for-bit as run. Cap-aligned, Stage 2 is 0.056506 and Stage 3 is 0.041747, matching my +0.0565 and +0.0417.

**Pins.** The recovery script's 13 literals (12 unique), all 64 hex characters, every one matching a file at HEAD.

**Fixtures, run here** on a scratch copy:
- **round 10: 177 checks, ALL PASS**, with the transcript identical apart from the php binary path;
- **round 9: `fx_capalign_l3`, 7 checks, ALL PASS.**

## 2. The count discrepancy: resolved, on the basis

My "decisive after turn 63" counts were **both outcome signs**: Stage 2 had 327 wins + 205 losses = **532**, and Stage 3 had 349 + 327 = **676**. The addendum's 327 and 349 are the **win-only** counts of the same rows. Its after-61 figures, 591 and 589, are also wins only; with both signs they're 887 and 1,132.

Both are right on their own basis. Wins are the right count for the rescoring, since cap alignment only changes wins. **Amend the addendum's discrepancy note to state the two bases** (text only, under `rounds/`). It needn't hold the run.

## 3. Rulings on §14.6

- **(a) Supplementary labels under the fixed engine, the 636 under the as-built engine: accepted.** Below turn 62 the two engines take identical steps, so cap-aligned rescoring of an as-built world gives exactly the fixed engine's classification: decisive iff it ended by turn 61, otherwise a horizon draw. The supplementary family's worlds are cap-aligned by construction. Commensurable.
- **(b) `jobs_merged.jsonl` keeps the 646 lines verbatim, `Infinity` included: accepted, for this run only.** Its consumers are Python readers, which accept the token, and the analyzer's +∞ handling is fixtured. **Standing rule from here on:** any jobs file a PHP process will read is written strict (sentinel form). Future job files are written strict at the source, which the fixed writer already does.

## 4. Launch conditions

1. **Joe's fresh go.** §14 changed what the recovery runs, so his earlier approval doesn't carry over. Launched sha == d17a4540, or differing only under `rounds/`. **The run happens once.**
2. **Order, per the amended script:** eval-completeness (step 0) → cap-aligned rescoring (must reproduce the published `data/step0_capalign/` files byte-for-byte, or stop) → extract and label the ten (family A, 970,055,001) and the 69 (family B, 470,055,001) under the fixed loader and engine, with the 50-rows-per-candidate pre-check → merge → dual read → report → influence prints → manifest.
3. **The read is reported as registered.**
   - **The cap-aligned read carries the decision rule.** The influence prints and the hold rule apply to it.
   - **The as-run read** prints beside it, labeled, with no recommendation of its own.
   - "Buildable, single-game dependent" comes back to review before any Step 1 package.
4. **Standing:** status-only notices, a launch record for this run, and publication of the recovery outputs with a MANIFEST.

**Scope:** this approves the §14 package and the one-time recovery run at sha d17a4540fa853512a127d9efbc290125475b96a7 on Joe's go. Approval certifies the build as written, not the run as executed.
