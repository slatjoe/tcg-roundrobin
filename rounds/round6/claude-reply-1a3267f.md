# Claude — reply to the round-6 pick-flip package

**Reviewed commit:** 1a3267f3b7af93a19dcff85ef54716b2af9a9b94 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-f7e4534.md` hashes to `6bc75d24…04415a8`, the value I gave Joe.
**Package:** rounds/round6/pickflip-package.md
**Verdict:** **APPROVED** to run on this sha. The single-site decision, the eval plumbing and the reconciliation plan are accepted. There is one resolution note on the read (§2) and two reporting additions (§3), none needing a new commit. Joe's go is still required.

What I checked:
- the package and `run_pickflip.sh` (`bash -n` clean; hash guards on all three PHP files)
- the probe patch's eval helper: no RNG calls, and on a transport failure it drops the shared socket global, so the next pick reconnects
- the tally fixture, which I reran here: output identical to `expected_tally.txt`

## 1. Design: accepted

- **Single site.** The DQ funnel hardcodes branch `"DQ"`, so `Choose` is the only place an ARS featurization can occur. One block there sees the whole population exactly once. Instrumenting the DQ funnel would have added a branch that can't occur.
- **Eval plumbing.**
  - `SimSearch_EvalState` rebuilds the state, so it can't evaluate a variant, and `search.php` isn't loaded in bridge mode. That makes a probe-local eval send over the bridge's own connection the correct shape: the same framing, payload, response requirements and two-attempt discipline as `SimSearch_Eval`, with only the response parse new.
  - The eval handler reads no seat and featurizes from `state["player"]`, so both seats' ARS states evaluate through v15. That's correct.
- **Definitions.**
  - The store and view definitions are the census's, so the agree flags reconcile row-for-row.
  - The variant is a deck-counts-only copy, never canaried, played or written back.
  - Candidate identity is by index into one shared list, with `card_id`/`zone`/`zone_index` logged for audit. Argmax and flip follow the codebase's first-strict-max convention.
- **The control** is the strong form: agreeing rows send byte-identical payloads, so they must show **identical prior vectors** and 0 flips, and anything else is a machinery defect. The smoke already met it (4/4 identical).
- **Non-interference:**
  - the eval is stateless on the server
  - the played pick comes from the untouched `Query` path on a strictly sequential connection
  - byte-identical gamelogs across trees in the smoke
  - the smoke's ARS counts match the census smoke's game for game
- **Reconciliation:** the counts are stated in advance (267 ARS rows: 163 disagreeing, 104 agreeing), with winners and decision counts checked against the committed census rows, and gamelogs compared if they persist, otherwise said so. A mismatch is reported as a machinery failure. Accepted as written.

## 2. Resolution note on the registered read

There will be about 163 disagreeing rows. Even **zero** flips gives a 95% Wilson upper bound of about **2.3%**, just above the 2% line. So this sample cannot *prove* the rate is under 2%. It can only show a point estimate at or below it.

The reading stays as registered, on the point estimate, but the results must state the Wilson upper bound beside it. If the point estimate is ≤ 2% and the upper bound is above 2%, write the read as **"immaterial to play at this sample's resolution."** The prior-shift distribution then carries the rest. The smoke's shifts were at most 1.4×10⁻⁵, and if the full run looks like that, deck counts barely move v15's priors at these decisions, which is stronger evidence than the flip count alone. If anyone later wants a tighter bound, it's a separate run on fresh seeds, not an extension of this one.

## 3. Reporting additions (no code change to the run; tally additions disclosed)

1. **Report flips and prior shifts by player** as well as pooled. The registered read stays pooled, since both seats' states are v15-perspective states in mirror play. But the learner-seat rows are the ones that actually move v15's play in evals, and the record should show them separately.
2. **Consistency check on the learner seat (optional but cheap).** On learner-seat rows, the current-state eval argmax should equal the pick the bridge then plays (`net_argmax` on the same logits). If the driver's trajectory or trace output carries the played index, report the agreement rate. A mismatch above near-zero would mean the eval and pick paths are evaluating different things, which would undercut the flip reading. If the played index isn't available without a change, say so and skip it.

## Not reviewed

- The flip tree on the box (the runner's hash guards cover it).
- The production server internals beyond the eval handler cited.

**Scope:** this approval is valid only for sha 1a3267f3b7af93a19dcff85ef54716b2af9a9b94, for `run_pickflip.sh` as committed, under §6's registered reading with the §2 resolution note and the §3 additions. It still requires Joe's go. The run authorizes nothing beyond its own report.
