# Claude — confirmation check on the Step 0 probe's third fix pass

**Reviewed commit:** 5ce1f585d14f11d2a7acbe599124caf6f63a2785 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-e93a15c.md` hashes to `0af87a5b…23da9f11`, the value I gave Joe.
- **Changed files:** exactly the five named. `run_probe.sh` is `7c7b8f80…`, and the doc is `29266b2f…`.
- **Unchanged:** `search_s3.php`, the driver and the nine reused files are byte-identical.

**Verdict: CONFIRMED. The probe may relaunch on Joe's go**, with launched sha == 5ce1f585 (or differing only under `rounds/`), under §3. The TEACHER_TUPLE_JSON flag is accepted as analyzed (§2).

## 1. The defect, the fix and the fixture

- **The diagnosis is right.** The hook gates on `TEACHER_CAPTURE && TEACHER_CAPTURE_UNCONTESTED` (`search_s3.php:1000`). The driver's capture arm sets the first; nothing in the runner set the second. Every fixture had set the environment by hand.
- **This is my miss too.** I instituted the writer→reader round-trip rule for files and didn't apply it to the environment that the runner passes into the game.
- **The fix:** one env-prefix variable on the capture invocation. It's the right channel, because the driver seeds the game's environment from `dict(os.environ)` and spawns with `env=env`.
- **`fx_runner_env.py` closes the class, not just the instance.** It runs BLOCK:CAPTURE verbatim against an env-recording stub. It lifts the driver's arm lines and the hook's gate verbatim, and asserts the **composed** environment carries both variables. The negative copy fails on exactly those two checks.
- **The §11 env audit is the right standing artifact.** Every consumer of an environment variable is traced to its channel.

**Fixtures, run here** on a scratch copy: **99 checks, ALL PASS**, with the PASS lines identical to the re-staged transcript.

## 2. Ruling on TEACHER_TUPLE_JSON: the analysis is accepted, no remedy required

**I verified the inertness claim in the code.** `SimTeacher_DecideInner` resolves the tuple at entry, and under `TEACHER_CAPTURE`:
- the uncontested branch returns at the priors;
- the contested capture block (`search_s3.php:1086`) logs and returns `$priorPick` **before** `$K = intval($T["k"])`, the first tuple-bound quantity.

The hook's candidate rule uses the literal Decide constants, not the tuple. The eval and label paths pin their own tuples through the mains' EVAL_* env and the jobs' setting objects. The only effect is the capture stat stamp (`"unpinned"`), and no probe consumer reads it.

**One condition, documentation only:** the probe report and its data MANIFEST state that capture stat rows are stamped `unpinned` **by design**. The capture arm never uses the search tuple, and `settings_probe.json`'s `capture.teacher_tuple` is descriptive of the build, not a delivered pin. Nobody should read the stamp later as a defect.

## 3. Relaunch conditions

1. **Attempt 2 is void and stays void.**
   - Its outputs are archived under a void-attempt directory, and nothing from it is consumed by the relaunch.
   - Its 50 capture-game ids are merged into the do-not-train registry (tag `r10_probe_capture_void`) if they weren't already.
   - **Reusing seeds 24001–24090 is accepted.** Capture games are raw-policy and deterministic, and no measurement was taken from the void attempt.
2. **A launch record covering attempts 1, 2 and 3** is committed with the relaunch. It records:
   - attempt 1's free-space abort;
   - attempt 2's defect, what it produced (608 contested snap rows, 0 uncontested) and that it was killed;
   - attempt 3's launched sha and deployed hashes.
3. **First-minutes check, added:** uncontested index rows are appearing. Record the uncontested-to-contested snap ratio over the first completed games. At EVERY = 2 it should be near 34 : 24 per game, not 0.
4. **Standing:** status-only notices, registry merge before analysis, and publication of `data/step0/` with the report.

**Scope:** this confirms the third fix pass and approves relaunching the Step 0 probe at sha 5ce1f585d14f11d2a7acbe599124caf6f63a2785 on Joe's go, under §3. Approval certifies the build as written, not the run as executed.
