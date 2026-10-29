# Claude — confirmation check on the Step 0 probe's fix pass 7

**Reviewed commit:** fdfe37afb79c41e6d797749224f7a398972be811 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-416872f.md` hashes to `220a60dc…cf19023`, the value I gave Joe. `run_probe_completion.sh` is `ce061988…` and the doc is `d684f4e7…`.

**Verdict: CONFIRMED. The influence completion runs once**, on Joe's standing go, with launched sha == fdfe37af (or differing only under `rounds/`).

## Checks

- **The invocation.**
  - `--game` is gone, so `probe_influence.py`'s default (540261752) applies, exactly as in the recovery.
  - I extracted both invocations myself: the flag sets are identical, `--jobs … --json-out`, eleven flags.
  - `fx_invocation_parity.py` asserts the same, with paths normalized. Run against the pre-fix script, it fails on the three defects.
- **The inspected-game assertion.** It sits immediately before the invocation and aborts naming the id and both driver files. The fixture runs the block verbatim both ways. `bash -n` is clean.
- **The recovery script is back to its as-run bytes.** Its `probe_influence.py` literal is `83f4f1d1…` again, and the whole file hashes to **`e9eea58c…`**, equal to the file at 3ef1815, the launched sha. The fixed pin lives only in the completion.
- **§15.6** records my §3 interpretation, labeled as such, and Joe's choice of the pilot-first Step 1.
- **Fixtures, run here** on a scratch copy: **197 checks, ALL PASS.** The transcript is identical apart from absolute paths in two lines (P1, P2) and the php binary path.

## Conditions

1. **One run.** Its outputs and the recovery manifest go into `data/step0_recovery/`, and the run record is amended.
2. **The finalized probe report carries three things:**
   - the influence prints: the inspection of 540261752 with the by-61 split, LOGO per lever, and the hold determination, verbatim;
   - the §15.6 interpretation addendum, labeled;
   - the registered recommendation as the rule produced it.
3. **If the hold fires** ("buildable, single-game dependent"), the report returns to review before the Step 1 package. **If it doesn't,** the Step 1 pilot package is drafted under §15.6's terms: no sizing from +0.47, and sized from on-trajectory numbers or a stated conservative bound.

**Scope:** this confirms fix pass 7 and approves the one-time influence completion at sha fdfe37afb79c41e6d797749224f7a398972be811. Approval certifies the build as written, not the run as executed.
