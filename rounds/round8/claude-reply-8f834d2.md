# Claude — disposition of the resumed pilot's report-phase crash

**Reviewed commit:** 8f834d2ced646f4b2d5617eb62a8730fede174ea (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch manifest `pilot-resume-launch.md` (969d61c). The committed `claude-reply-be2fae4.md` hashes to `00d12bec…dd70e65817`, the value I gave Joe.
**Package:** `rounds/round8/pilot-report-resumed.md`.

**Disposition: fix `pilot_report.py` as below, and re-run only the report phase and phase 7 against the intact inputs.** That re-run is **approved now**. It plays no games and labels nothing, and it can be repeated at will, so I'll review the fix's diff together with its outputs rather than gating the re-run on a separate confirmation.

## 1. Accepted from the run

- **The launch condition was met:** `PILOT_OUT` was recorded absent before launch.
- **The fixed script was deployed:** `0e4febca…`. Catching the stale box copy was good operating.
- **Step 1 passed.**
- **Equivalence is IDENTICAL on both seats, on fresh games,** PARSE-PASS on both. The merge shows **added 40, dup_same 0**. **The capture-equivalence question is closed:** capture with the uncontested patch is action-identical to raw v15, so the corpus is v15's state distribution.
- **Labeling is complete:** 547 / 547 / 100 labels, **0 thin in every set, and a V2 thin count of 0**, as Fai's rates predicted.

## 2. The crash, and the right fix

The diagnosis is close, but one point needs correcting, because it determines the fix. **The live `means` and `n_worlds` aren't "position-indexed over the selected candidates" in some rows and id-keyed in others. They're always keyed by candidate id.** `DecideInner` builds `$means[$ci]` for `$ci` in the sorted `$sel`. PHP's `json_encode` writes such an array as a JSON **list** only when its keys are exactly 0…n−1, and as an **object** with string keys otherwise. So:
- a list row is one whose `selected` is `[0, 1, …, n−1]`, where position and id coincide
- the 44 object rows are the ones with a gap, like your `[0, 1, 3]`

Line 182's `t["means"][pos]` was therefore correct only by coincidence, on the list rows.

**Required fix:**
- read the live values **by candidate id** in both shapes: `v[ci]` for a list, `v[str(ci)]` for a dict
- **assert, for every list-shaped row, that `selected == list(range(len(means)))`**, and abort with the row named if not. That proves the PHP-collapse reading on all 56 list rows rather than assuming it.
- apply the same accessor to `n_worlds`
- grep the rest of `pilot_report.py` and `pilot_prep.py` for any other read of the live stat rows' `means`, `n_worlds` or `priors`, and route each through the same accessor

## 3. The re-run (approved)

- **The mode:** a report-only re-entry (`PILOT_RESUME=report`, say) against `PILOT_OUT=/tmp/distill_pilot_resume`. It first **asserts the §3 input hashes**: the three label files, the truth file, the three timings files, `pilot_times.jsonl` and `pilot_cand_times.jsonl`. Then it runs `pilot_report.py` and phase 7, the teacher-root census, featurizing the pilot's roots with no games. Any input mismatch aborts.
- **No labeling, no games and no capture.** If the mode would invoke any of them, it's wrong.
- **Publish the inputs.** Commit the report phase's inputs under `rounds/round8/data/pilot/`: the label files, the truth file, the timings, and the V1/V2 job files. They're small, and they let me recompute **V1-ov, V1-conf, V2, the two-proportion test and the z-check myself** before I rule on the pilot, as I did for round 7's fleet.

## 4. The registry normalization: record it

Joe's message says that after the run the registry was **28b5acfa…**, after "a value-shape normalization of the builder's 20 records-merge entries". The report gives `a921be49…` after the merge, and **no committed document records the normalization.** Membership is unchanged, which is what matters for exclusion, but an edit to the registry needs the same record as a merge:
- which 20 ids
- each one's old value and new value
- the before and after hashes (`a921be49…` → `28b5acfa…`)
- a backup and vault copy

Put that in the next commit. Use one value shape from now on: the tag string, as every other entry has.

## 5. Still owed

- **The one-capture-per-seed declaration** in the corpus launch manifest. Option (a) fits: skip seeds 10001–10020 in the heur seat-1 stream, keep the pilot capture and its run-A labels, and assert one game id per (stream, seed).
- **The sign-test fix**, before the gate.
- **The resume guard** that refuses an `$OUT` already holding `equiv_*` files (be2fae4 §2), in the next code commit.

**Scope:** this reply approves the `pilot_report.py` fix in §2 and the report-only re-run in §3. Neither plays a game, and both are reviewed together with their outputs. It also asks for the registry normalization record (§4). The corpus stays gated on my review of the completed pilot reads.
