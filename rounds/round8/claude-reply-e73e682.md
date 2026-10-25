# Claude — ruling on the round-8 pilot stop

**Reviewed commit:** e73e682d10986d0d7237d03df66467e1e5429b45 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch manifest `pilot-launch.md` (3b68d5c). The committed `claude-reply-dc22f1d.md` hashes to `b45c2549…6d5cb1cc`, the value I gave Joe.
**Package:** `rounds/round8/pilot-report.md` and `pilot-registry-merge.json`.

**Ruling: this is a build fix, not a reclassification.** The stop was correct, and so was not working around it. The pilot resumes **after** the capture phase, with the equivalence check re-run correctly (§2). The Gravy census and the capture phase are accepted (§3).

## 1. Why a fix, not K6

K6 reclassified a check whose **premise fails by construction** on Gravy: thin-prior rows can never carry the ghost stamp. The check was right in principle and wrong about the population.

This failure is different. **The check is right, and it was called wrong.** `r3_pair.py`'s `MODE_PREFIX` already has a `capture` entry (`"policy: search"`), which is exactly what the capture rows' mode line carries. `run_pilot.sh` (lines ~166–168) names **both** sides `raw=`, so every capture row is tested against `"policy: server"`, and it fails as it should. Called as `capture=… raw=…`, the mode check would test what it exists to test: that each arm actually ran in its own mode. Waiving it would remove a guard that this comparison can pass legitimately.

**There's a second reason the read can't be reclassified: it never happened.** `INVALID_MODE` takes precedence over the classifier's verdict in `r3_pair.py`. So the table shows hits 0 and outcomes equal, but **the classifier's own class (IDENTICAL or otherwise) was never displayed.** Equal outcomes and zero within-row hits are necessary for IDENTICAL, not sufficient. And seat 2 was never played, because the runner stopped at seat 1.

**The miss is shared.** I accepted this phase in the fix-package review without catching the arm labels.

## 2. The fix and how the pilot resumes

**The fix, in `run_pilot.sh`:**
- the equivalence read becomes `r3_pair.py capture="$OUT/equiv_cap_s${seat}.jsonl,…" raw="$OUT/equiv_raw_s${seat}.jsonl,…"`, with capture as the base arm and its own label
- nothing else in the phase changes: the same strict parser, 10 rows, and a stop on failure

**A pre-commit dry read (read-only, no games).** On the box, run the corrected invocation once over the **existing** seat-1 rows (`equiv_cap_s1.jsonl` and `equiv_raw_s1.jsonl` with their logs), then `parse_r3_pair.py --expect-rows 10`. Commit the table and the parse output with the fix. That shows whether the hidden classifier verdict is IDENTICAL before anything is launched. If it reads anything else, the pilot doesn't resume, and the read comes back to me.

**How the pilot resumes,** on Joe's go after I confirm the fix commit:
1. **The capture phase is not re-run.** The intact capture is asserted instead: the corpus manifest hash (`edc6e4fb…`), the stream manifest's `assert_ok: true`, the counts of 547 contested and 855 uncontested snapshots, and the corpus-tree `search.php` at `044ca8ec…`. Any mismatch stops the run. Run A's labels on these games then remain corpus labels, as registered.
2. **The equivalence phase is re-run in full, both seats, seeds 12001–12010,** with the corrected read. It's deterministic at raw speed, so it costs minutes. A fresh run on the same seeds gives a clean, complete record for both seats from one invocation, rather than a spliced read of one old seat and one new. The 20 games from the failed run are already registered. Register the new games the same way.
3. Containment is as before: the standing G8 sweep first (it clears the 20 residual segments), then (C) on the native tree.
4. Then phases 4–7 as registered: jobs, the V1 double label, V2 on 100 preserved snapshots with its thin count, the mechanism z-check, the deadline accounting, the cost over about 1,200 jobs, and the teacher-root census.

Implement the resume as an explicit, guarded mode (`PILOT_RESUME=equiv`, say) that performs step 1's assertions, rather than as a hand-edited copy of the script. It ships in the same fix commit, with its hash.

## 3. Accepted

**The Gravy census:**
- 12,896 featurizations, **114 disagreements (0.884%)**, all view>store, **all at ARS (114/214 = 53.3%)**, 0 at every other branch, across 20 games with both seats represented
- the tally comes from `tally_census.py`'s own output, with hashes
- fallbacks were 0

**It's the Fai pattern on a second hero:** ARS-concentrated and one-directional. That supports the (b) correction being a general property of the bridge, not a quirk of Fai. Report-only, as registered, and it closes the item round 7 dropped. **The registry:** 6,161 → 6,181 (`a26a92b6…`), then 6,201 (`95a4580a…`) with the equivalence games.

**The capture phase:**
- 547 contested and 855 uncontested states from seeds 10001–10020
- the patch product asserted
- `assert_ok: true`, with pick == prior on all 1,402 teacher trace rows and no rollouts anywhere
- fallbacks 0
- the corpus manifest recorded

## 4. Still owed (unchanged)

- The **one-capture-per-seed declaration**, in the corpus launch manifest (dc22f1d §3). Because the pilot's capture is kept, option (a) is now the natural one: the corpus skips 10001–10020 in the heur seat-1 stream, and `t1_build_data.py` asserts one game id per (stream, seed).
- The **sign-test fix**, before the gate (dc22f1d §2).

**Scope:** this reply rules the stop a build defect (the arm labels) and specifies the fix, a read-only dry read, and the guarded resume. It accepts the Gravy census and the capture phase. **It approves no run.** The fix commit comes back for a confirmation check, then the resumed pilot runs on Joe's go. The corpus stays gated on my pilot review.
