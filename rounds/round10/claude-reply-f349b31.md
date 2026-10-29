# Claude — confirmation check on the Step 1 pre-gate repair, pass 2

**Reviewed commit:** f349b3136220af9d3f420d102ec10800b1148e52 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-3955e55.md` hashes to `6d233217…bfbcc3`, the value I gave Joe. The doc is `15b5dda2…`. The commit-message miscount (143) is noted: the transcript's 144 governs, and I counted 144 too.

**Verdict: CONFIRMED. Pre-gate attempt 2 may run on Joe's go, and the pilot only behind an IDENTICAL verdict**, with launched sha == f349b313 (or differing only under `rounds/`).

## Checks

**§2.1, timeouts gate: closed.**
- I ran the pinned checker (`98b3d2ff…`, pinned in both runners) myself on attempt 1's published rows with the runner's exact arguments.
- All identity legs print PASS over the completed population: 97 and 122 contested pairs, 0 bad. The checker then prints **`PREGATE: INCONCLUSIVE (timeout: ghostthr_s1 seeds 13001, 13002, 13003, 13005, 13010; ghostthr_s2 seeds 13001, 13002, 13005)`** and **exits 2**.
- The runner aborts before the merge and manifest steps, so the pilot gate refuses.

**§2.2, tolerance: closed.**
- `PRIORS_TOL = 1e-5`, justified by float32 ULPs.
- `selected` **and `prior_pick`** are exact on every contested pair.
- The observed maxima (5.364e-07 and 7.153e-07) are printed, now well inside the bound. `prior_pick` was exact on all 219 pairs.
- The fixtures (5e-6 passes, 2e-5 is bad, a `prior_pick` mismatch is bad) are present and pass.

**The cost re-price is accepted as the planning basis:**
- the thr ghost arm averages 855 s per game, or 993 s with the killed games floored at 1,200 s;
- **the pilot's teacher arm comes to about 24–28 box-hours, roughly 6–7 h of wall time**;
- the pre-gate is about 2.5–2.8 h.

The stated limits are right: the means are survivor-biased, and live trajectories may differ in length. The probe's 1,840 s figure is retired for planning, and GAME_TIMEOUT stays 7,845 s.

**Fixtures, run here** on a scratch copy:
- **pilot suite: 144 checks, ALL PASS**, transcript identical;
- **round-10 suite: 197 checks, ALL PASS.**

**Non-blocking:** the runner's abort message after a failed check still reads "pre-gate NOT IDENTICAL" even when the checker printed INCONCLUSIVE. The checker's own verdict line in `pregate_check.txt` is the record. Make the runner echo that line, the next time the file is touched.

## Launch conditions

1. **Joe's go.** The launch record states the launched sha and the attempt number (2), runs in `pregate/attempt2/`, and leaves attempt 1 untouched.
2. **The verdict is the checker's line, and nothing else:**
   - **IDENTICAL**, with all 10 seeds at both seats completed in every arm, writes the manifest, and the pilot may follow under the same go;
   - **INCONCLUSIVE or NOT IDENTICAL** stops everything and returns to review.
3. **The pilot**, if it launches, runs as registered:
   - 100 games, 25001–25050 × both seats, 7,845 s;
   - L3 at 700,055,001 + shard × 10⁸;
   - the read with the one-sided STOP and the sizing.
   - Status-only notices, and publication of `data/step1/` with a MANIFEST.

**Scope:** this confirms repair pass 2 and approves pre-gate attempt 2 and, behind its IDENTICAL verdict, the Step 1 pilot at sha f349b3136220af9d3f420d102ec10800b1148e52, on Joe's go. Approval certifies the build as written, not the run as executed.
