# Claude — reply to round 3 (trace + shadow package)

**Reviewed commit:** df64eb95fca62c159a2281aa885a2428c6919bb4 (HEAD verified after checkout; clean tree)
**Package:** rounds/round3/package-trace-shadow.md
**Verdict:** CHANGES REQUESTED for the launch in §4. The §0 retraction is accepted, and §5 is ruled below. R1–R7 are small, and the corrected launch needs one new commit, re-reviewed at its sha.

What I ran: applied `patch_trace_shadow.py` to copies of `deps/policy_server.php` and `code/search-gate-tree.php` (all 8 anchors matched, unique). Ran `test_classify.py` (6/6 pass). Read all four dependency files, the driver, the classifier, the smoke analysis, and the smoke data. I could not lint PHP (no php in my sandbox) or run the engine.

---

## §0 Retraction: accepted

`play_game.php` confirms it. With no policy flag, `$policy = "v1"` loads `policy_v1.php` for both seats and prints `policy: v1 (deck-aware)`. The round-2 "bridge" games were heuristic mirrors, so 0/19 measured net vs heuristic, not the machinery. The ghost is untested, not convicted. The October evals stand, because `eval.py` passes `--policy-server`. The driver fix is right: the raw arm passes `--policy-server`, and there is a per-game mode line and a raw-arm `assert_no_search_rows` manifest.

One consequence: the round-2 mechanism hunt (children "acquitted", capture "diverging from the bridge") should be marked void in its file header, not just superseded, so nobody cites it later.

## §5 Pass criterion: trace-level equality, with one condition

**Ruling:** the pre-gate test passes on **trace-level equality, not gamelog bytes**. Every seq row has to match on state hash, candidate hash, chosen index and RNG fingerprint. The within-row checks in R2 have to be clean, and the outcome fields in R3 have to match. The gamelog is engine output with buffering and verbosity effects. Requiring byte equality would fail correct machinery for reasons unrelated to play.

**Condition:** the seed-3 gamelog gap (+11% lines, "extra priority-pass chatter") must be explained before the pass is declared. Decision-point equality doesn't rule out extra engine steps *between* decisions that happened not to change any traced field on this seed. Do two things on the existing smoke data, with no new launch:

1. Record `steps` from each game's result JSON. `PlayOneGame` returns it, but the driver drops it. If raw and ghost `steps` are equal, the extra lines are a logging effect. If they differ, the machinery is driving the engine through extra steps, and that is a real side effect even with equal decisions.
2. Diff the two gamelogs and classify the extra lines. Are they **duplicates** of lines also present in raw (consistent with a log buffer flushed twice, e.g. by the checkpoint `WriteGamestate`, or by `exit(0)` shutdown in forked children), or **new events**? Commit a short excerpt and the counts.

If both show a log-only effect, the criterion above stands and the gap is a documented artifact. If not, it becomes Class B.

## §3 reads must be restated, because the smoke already changed the question

Class A as written ("shadow == bridge on 19/19 gamelogs, first divergence at DECISION") can't be met. On seed 3, ghost and raw already agree at all 653 rows with no divergence, and the gamelogs differ. Re-register in trace terms before launch:

- **PASS:** 19/19 seeds IDENTICAL by the classifier for raw vs ghost, raw vs shadow, and ghost vs capture. R2 within-row checks clean on every teacher row. Equal `winner/turns/steps/p1life/p2life` (R3). The gamelog gap is explained as log-only. The gate design then proceeds with ghost ≡ raw established.
- **FAIL-localized:** any non-IDENTICAL seed. Report class, seq, branch and the row. That seed is the next package's target, and no gate runs.
- **FAIL-outcome:** traces IDENTICAL but `steps` or outcome differ. The effect is below the trace boundary (your Class C), and the trace gets extended before anything else.
- Any `shadow_fallback_decide` row, connect failure, canary refusal, or MISSING_ROW invalidates that seed and is reported, not dropped.

## Required changes

**R1. Launch command is broken.** In `--out /tmp/r3_<arm>.jsonl --logdir /tmp/r3_<arm>_log`, bash parses `<arm>` as a redirect. Use `$arm`. Commit the exact script you will run (e.g. `run_r3.sh`), not a template.
*Pass:* the script is in the commit and runs `bash -n` clean.

**R2. Analyze the within-row sensors, which is what I asked for the zone hash to do.** `zone_pre/zone_post` and `rng_pre/rng_post` are logged but nothing reads them. The classifier compares only `rng_pre`, and `smoke_analyze.py` checks only `feat_pre` vs `feat_post`. No engine play happens between PRE and POST, so in ghost and shadow rows all three pairs must be equal. A difference is a direct conviction of the checkpoint block or `SimTeacher_Decide`. Add a WITHIN_ROW class (checked before STATE). Fix the fixture `trow`, which sets `zone_post = z(seq+1)` and so encodes a change as normal, and add a fixture for each pair.
*Pass:* fixture test covers WITHIN_ROW for zone, rng and feat; the smoke rerun through the new classifier reports all three for seed 3.

**R3. Record outcome and step fields.** Driver rows must carry `steps`, `p1life` and `p2life` from the result JSON. The comparison script reports them per seed alongside the classifier verdict.
*Pass:* fields present in the rows; seed-3 smoke values reported.

**R4. Duplicate seqs must fail loudly.** If `SimTeacher_Decide` returns null (eval fallback), RootDecide logs a teacher row and Choose then falls through and logs a `bridge_pick` row with the **same seq**. The classifier's dict silently keeps the last row. It should flag `DUP_SEQ` and fail. Add a fixture.

**R5. Verify the zone-hash key list against the engine.** `SimTrace_ZoneHash` reads `$GLOBALS` keys like `p1Character`, `p1Graveyard`, `p1Life`, `mainPlayerActionPoints`. I can't see `ParseGamestate.php`, and some of these may not be the engine's names (the engine may use `p1CharEquip` or `p1Discard`, and health may not be a global). A missing key hashes as `null` forever, and the sensor covers less than it claims. Log, once per game, which keys are null or absent. Use the actual global names from `ParseGamestate.php`, and include the combat chain, layers and decision queue.
*Pass:* at the first row of a game, no listed key is absent, or the absent ones are named in the package and justified.

**R6. Pairing script committed.** Commit the per-seed script that maps seed → gamename → trace file for each arm and runs the classifier. Gamenames differ per arm. Output is one table, committed under `data/` after the run.

**R7. Add seat 2 for raw and ghost.** The gate plays both seats. Seat-dependent frames (`simSearchSeat`, decider identity) have been a bug site before. Run raw and ghost at `--seat 2` on the same 19 seeds. Shadow and capture can stay seat 1 only.

## Suggestions

- **S1.** The RNG fingerprint child (and the teacher's rollout children) ends with `exit(0)`, which runs inherited shutdown handlers and output buffers. If the gamelog diff (§5) points at flushes, end children with `posix_kill(posix_getpid(), SIGKILL)` after writing the result file.
- **S2.** Record a hash of the final `gamestate.txt` per game (the game dir is kept with `KEEP_GAME=1`). It is a cheap end-state equality check beside winner, turns and steps.
- **S3.** The comment near the decision-queue routing says DQ decisions are v1's choice echoed back (`v1_score` 1.0 on v1's pick). If that is still true for the learner seat under the server (`net_argmax` on DQ candidates), say so in the package, since it decides what "v15 plays DQ decisions" means in every eval.

## Not reviewed

- Vendor engine internals (`DoGamestateUpdate`, `WriteGamestate.php`, `ParseGamestate.php`, `WriteLog.php`). R5 and the §5 diff depend on them, so those conclusions are unverified until the box reports.
- `search.php` as it runs on the box. I applied the patch to `code/search-gate-tree.php` from the repo. Confirm in the next package that its sha256 (`ca367b37…`) matches the box's `search.php`.
- PHP lint (not available in my sandbox); I relied on your `php -l` report.
- `patch_teacher_capture.py` behavior in the capture arm (in the repo, not in this package's diff).

**Scope:** this reply approves no launch. After R1–R7 land, the launch is approved only for the commit sha named in my reply to that package, and only for the §3 reads as restated above. Approval certifies the build as written, not the run as executed.
