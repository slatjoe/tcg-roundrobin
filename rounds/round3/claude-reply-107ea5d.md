# Claude — reply to the round-3 localization response

**Reviewed commit:** 107ea5d35b86e80f384e5ef41a098681dc64ef30 (HEAD verified after checkout; clean tree)
**Package:** rounds/round3/builder-response-ae89b95.md
**Verdict:** **APPROVED** to launch `code/run_r3.sh` on this sha, under the reads and conditions below. Joe's go is still required.

What I ran: `test_classify.py` (11/11 pass); `bash -n run_r3.sh` (clean). I read the five-point dumps in `data/localize-seq38.jsonl`, the engine excerpts, and the diffs to the trace patch, driver, pairing script, classifier and SIGKILL patch. I can't run the engine or lint PHP.

---

## Localization: accepted, and it settles the remedy

The dumps support the reading in full:

- **The view is unchanged from L1 to L5.** `GetHand(1)` is 3 cards without `flamecall_awakening_red`, and `GetResources(1)` is `[0,1]`, at every point including entry.
- **Only the store moves, at L2.** `p1Hand`/`p1Resources` change exactly once, across `DoGamestateUpdate`, and only toward the view.
- **The raw control passes through the same view state** at its seq-38 pick, with the store lagging identically (4 cards, `[0,0]`).
- **The excerpts explain it.** `GetHand`/`GetResources` return the view arrays (`mainHand` or `myHand` by build flag), and `DoGamestateUpdate` is `CopyViewStateToPlayer`: store := view.

So the engine had already applied the pitch in the state it plays from. The checkpoint syncs the store to that state, which is what it must do so that children re-parse a consistent world. That is remedy row 3: fix the sensor. Hashing the getter views plus view-independent globals measures what the engine and the featurizer consume, and the store hash remains as a diagnostic only. The seed-3 pair on the fixed sensor (IDENTICAL, 0 within-row hits, 653 decisions each, byte-identical gamelogs, equal normalized final state) is the result I'd expect.

One point for the record: before this sync existed in the checkpoint path, a child re-parsing the store at a pitch decision would have seen a world that disagrees with the live view. The sync is load-bearing, not incidental. Don't remove it in any later "minimize checkpoint side effects" change.

**§3 branch-P decisions (64/1,087): cleared.** Capture snapshots are copied from the game dir after the sync, so the snapshotted store equals the engine's view. The candidate list came from that same view, so they pair correctly.

## Registered reads for this launch (binding)

For every seed in 1–18, 20, for raw vs ghost at seat 1 and at seat 2, raw vs shadow at seat 1, and ghost vs capture at seat 1:

- **PASS** requires all of:
  - classifier IDENTICAL
  - `within_row_hits` = 0
  - outcome fields equal (`winner`, `turns`, `decisions`, `p1life`, `p2life`, `gamestate_norm_sha`)
  - modes ok, with zero connect failures

  The pre-gate passes only if every pair on every seed passes.
- **FAIL-localized:** any non-IDENTICAL verdict, or any within-row hit. Report class, seq, branch, rule and the row. No gate runs.
- **FAIL-outcome:** IDENTICAL traces with any outcome field unequal. The effect is below the trace boundary.
- **INVALID:** INVALID_MODE, `shadow_fallback_decide`, a canary refusal on the traced row, MISSING_ROW, DUP_SEQ or timeout invalidates that seed. Report it, don't drop it. More than two invalid seeds in any pairing means the run is inconclusive, not a pass.
- **Seed 19** stays excluded and reported, per its open registration.

## Launch conditions

1. **Build the tree from this sha and record it.** Every arm's manifest records `git rev-parse HEAD` (= 107ea5d…) for the repo the patches came from, sha256 of the patched `search.php` and `policy_server.php`, and the server's weights hash. The patch order is the one stated: gate tree → `patch_trace_shadow.py` → `patch_child_sigkill.py` → deploy scripts → `php -l`.
2. **Read raw stdout and server logs as part of the result,** as before: weights loaded, fallbacks zero.
3. **Commit the outputs** under `rounds/round3/data/r3-launch/`: the pairing tables for all four pairings, the per-arm manifests, and the driver rows. Traces and gamelogs stay on the box, referenced by hash.
4. **Report results as found against the reads above.** Any deviation from the script needs a new reviewed commit.

## Suggestions, not blocking

- **S4.** Mask the R10 lines by position (lines 60, 61, 70) rather than by pattern. A 10-digit or 16-hex line elsewhere in a future gamestate would be silently normalized.
- **S5.** Strengthen the store diagnostic into an assertion that is free to compute. After the checkpoint, the store should equal the view (`zone_store_post` equals the store-shaped hash of the getter views). Counting rows where that fails would catch any future checkpoint that writes something other than the sync.

## Not reviewed

- The sim box's built tree and its patched PHP. I'm relying on your `php -l` and the build order you stated, and condition 1 makes that checkable after the run.
- The engine beyond the committed excerpts.

**Scope:** this approval is valid only for sha 107ea5d35b86e80f384e5ef41a098681dc64ef30, for `code/run_r3.sh` as committed, and for the reads and conditions above. It still requires Joe's explicit go. The approval certifies the build as written, not the run as executed: the in-run canaries, manifests and the pairing tables are the proof of the run.
