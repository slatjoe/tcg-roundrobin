# Claude — reply to the round-7 K1/K3 fix

**Reviewed commit:** ba4e9c97d4a89b25813d88d170c45e0b2b9f3a28 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-a889f39.md` hashes to `6b450462…8a5dbf7`, the value I gave Joe. `code/build_gravy_probe.py` hashes to `6f5e64b6…6075b05`, matching §V.4, and compiles.
**Package:** rounds/round7/followup-k1-k3-fix.md
**Verdict:** **APPROVED. Stage 3 and later are approved to launch on this sha**, as amended by `followup-k1-k5.md` (K2, K4, K5) and this fix (K1, K3). The probe hash is recorded as a launch-time artifact. Each stage still needs Joe's go and a stage manifest showing the launched sha equals the approved one.

## 1. The three focus items

**The three-corpus probe builder: accepted.**
- It runs one `probe_kl.py build` over `mirror_self`, `cross_self` and `mirror_bc` in driver order, at 9,000 each: Fai's exact form.
- The per-corpus game-count guards (2,400 / 750 / 1,500) run **before** anything is built.
- `kept == cap` is enforced for every corpus. A short yield aborts the build rather than becoming a probe to train against.
- The re-scan is segmented per corpus, not run over the merged file, which is the right strengthening.
- The overwrite refusal is kept.

The scratch evidence is the right kind:
- the positive run (50/50/50, verified per corpus)
- a **third, independent filter implementation** matching all three segments
- both negative tests: the game-count guard aborted with no file written, and the overwrite refusal fired

The short-yield branch wasn't exercised live, and you say so. It's the same comparison as before, applied per corpus, and I accept it on that basis.

**The corrected K3 controls: accepted.**
- **(a) Determinism check:** a second raw run at seat 1 must be **IDENTICAL** on 10/10 under `r3_pair.py`, and is read *before* the ghost comparison. The grounding (round 2's 19/19, the round-3 rerun, round 6's byte-for-byte replay) is stated as recorded behavior.
- **(b) Standing raw control:** the pre-gate's own raw runs across seats must differ on ≥ 1 of 10, with no extra games.
- **The pass criterion** reads through the standard instruments: IDENTICAL, within-row hits 0, outcome fields equal, and modes, seat and assert all OK. The gamelog sha alone isn't enough.
- The K5 marker exception is carried precisely.

**The O pre-gate pairing finding (§2): accepted, and the question is closed.** The evidence chain is complete, from primary records:
- the registration
- the instrument's own docstring and `raw_control()`
- the launch script's `--raw-control pg_raw_s1 pg_raw_s2` block
- both manifests (seat 1 and seat 2, the same seeds)
- the `raw_control.txt` output

It also explicitly separates out the distinct opponent-is-live control. The O control was the **standing seat-crossed control**. "Self-pairing" meant the pre-gate's own two raw runs, not a same-seat re-run. **There's no determinism anomaly in the O record.** The inverted control bullet in the follow-up is withdrawn, which is the right disposition.

## 2. Stage 3+ launch conditions (consolidated)

The full approved stack for stage 3 onward:
- `build-package.md` (dd4cb2fe), as amended by `followup-k1-k5.md` (a889f394: K2, K4 and K5 as written, the ghost arm) and by this fix (K1 three-corpus builder, K3 substitution text)
- C1–C5 and the C4 selection protocol
- the anchor stop (< 0.40, from stage 2)

Specifically:
1. **Probe:** built by the registered invocation after stage 1 completes all three corpora. `PROBE_SHA256` is recorded in a builder note and the stage-3 manifest, along with the three `PROBE_CORPUS` lines. A recomputation mismatch voids the build and it is rebuilt. Any guard failure stops stage 3 and returns as a package.
2. **Stage 3 starts only with** `GRAVY_STAGE2_CLEARED=1`, set only if the anchor read is ≥ 0.40, with server logs showing fallbacks = 0.
3. **C4:** at most 4 formal gates, in version order. If none passes, that's the finding, and the pipeline stops.
4. **Stage 4:** `/tmp/gravytree` from `/tmp/otree`, with the runner's pinned hashes.
5. **Stage 5 order:** G8 sweep, then the contention probe and timeout, then the pre-gate with (a) and (b), then the fleet, then the registry merge, then the analysis (primary, L1/L2/L3, G3). The stops are as restated: (a)–(d) as registered, (e) per K4.

## Not reviewed

- The box-side runs of §V beyond their reported outputs.
- The launch-time artifacts (probe hash, anchor read, C4 reads), which the stage reports will carry.

**Scope:** approval is valid for sha ba4e9c97d4a89b25813d88d170c45e0b2b9f3a28 and the stack above, for stage 3 and later. Each stage needs Joe's go. Approval certifies the build as written, not the run as executed.
