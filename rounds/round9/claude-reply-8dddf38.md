# Claude — reply to the round-9 design (Gravy-calibrated search)

**Reviewed commit:** 8dddf38786cce9502ef8ccde9336564bcc132bd0 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-5556677.md` hashes to `09fe5c8c…26c16d73`, the value I gave Joe.
**Package:** `rounds/round9/gravy-calibrated-search-design.md`.

**Verdict: APPROVED IN DIRECTION**, with D1–D6 settled below and four additions.
- **(A)** Calibrate on **all-candidate completion**, not prior-only thin-prior (§2).
- **(B)** A **rollout horizon aligned with the game instrument**, proposed as D7 (§3). I think it's the bound that matters most on Gravy.
- **(C)** The offline evaluator must run **the setting's own deadline, at the fleet's contention** (§4).
- **(D)** Stage 0 must report **unfinished worlds**, and its null and negative reads are conditional on them (§1).

The framing is right: round 7's null is a confound between "search has no edge" and "search never ran", and the stages separate the two in order of cost. So is the claim discipline: no stage licenses the next stage's claim.

## 1. Stage 0: approved, with an instrument-validity condition

Running L3 first on the 118 vaulted jobs (`5fe5c0d8…`, re-verified) is the registered first measurement, and **D5 is agreed**: Stage 0 runs alone and first. Its read can change Stage 1 through D6, and it costs at most about 1.5 box-hours. Reading it as *conditional quality* rather than a share of Δ is right.

**Addition (D): the L3 instrument has the same Gravy problem as the teacher.** L3 scores **finished worlds only**. Its rollouts run under the same 4,000-hook and 400-step bounds, and about a fifth of Gravy games never terminate. If many label worlds don't finish, the paired difference is computed on the *terminating* subpopulation, which is biased against exactly the moves that steer toward or away from stalls. **Required, registered now:**
- report the **unfinished-world share per candidate and pooled**, and the **paired-n distribution**
- a **sensitivity read scoring unfinished worlds as draws** (0.5), the instrument's own price for a game that doesn't end, beside the primary
- **if the pooled unfinished share exceeds 20%,** Stage 0's *null* or *negative* outcome is **instrument-limited**. It can't trigger CLOSE at Stage 0, and the round proceeds to Stage 1, where the horizon question (§3) is tested directly. A *positive* read stands either way: fires that are better on the worlds that finish are evidence of an edge.

## 2. Stage 1, D1 refined: completion means every candidate

The overturn test needs the **challenger** finished too: paired n ≥ 20 on best against prior. A setting can pass a prior-only thin-prior bar while challengers still starve, which leaves the overturn rate, the round-7 symptom, untouched. **Settled:**
- **The selection metric** is **all-candidate completion**: the fraction of panel states where **every selected candidate** has ≥ 20 finished worlds.
- **The bar** is **≥ 95%** (D1's 5%, applied to this stricter metric).
- Prior-only thin-prior is co-reported beside the fleet's 31.7%, for comparability.
- **The selection rule** otherwise stands: the cheapest setting by mean per-decision wall, ties broken by p95 and then max, with **NO CALIBRATED SETTING IN GRID** if nothing qualifies, and no fallback.

## 3. D7 (new, recommended): a rollout horizon aligned with the instrument

**The mismatch.** The game is scored with a turn cap: parameter 87, trigger 62, capped = draw = 0.5. The teacher's rollouts have **no turn horizon**; they end only at game over or on the guards. So a rollout that drifts into Gravy's pass-forever mode doesn't finish and is **dropped**, while the real game it stands for would be scored a **draw**. More hooks or longer deadlines can't fix a world that never terminates. They only let more terminating worlds finish, which may be why prior-only thin-prior is stuck. And the teacher is choosing moves by outcomes *conditional on termination*, which isn't the objective the gate scores.

**Proposal:**
- **Add a horizon** to the rollout child: a world that reaches the game's own draw trigger (absolute `currentTurn` ≥ 62) ends with `outcome = 0`, which is a draw at 0.5, and `finished = 1`.
- **This is a search bound, aligned to the registered instrument,** not a change to the decision rule: the candidate rule, floor, margin and continuation are all unchanged.
- **It goes into the grid as one factor:** settings **B0** (the old control), **B0+H** (horizon only), then **{8,000 / 16,000 hooks} × {180 / 360 s}** with the horizon, for **6 settings** at the same cost. That's if the reviewer accepts. The alternative is the full 12-cell factorial at twice the cost.
- **The same horizon applies to the Stage 0/2 L3 instrument** as a co-report (primary stays as registered for Stage 0; for Stage 2, the horizon-aligned L3 becomes **primary** if the selected setting carries the horizon, since the audit should score worlds the way the gate scores games).

**This is my recommendation, not the builder's proposal.** It changes the teacher's evaluation function in a principled way, and I'd rather register it now than discover after Stage 1 that the bounds-only grid couldn't reach the bar. **Joe and the builder may reject it.** If they do, the bounds-only grid runs as proposed.

## 4. Addition (C): the offline evaluator must run each setting faithfully

- **The deadline is part of the setting.** The label path's per-candidate deadline is **300 s** and the live teacher's is **180 s**. On Fai that never mattered (0 batches past 180 s). **On Gravy it binds**, and it's a grid axis. The offline evaluator must run **exactly** each setting's deadline and hook budget, and Stage 2's live teacher must run the selected setting's values exactly. Show both from the code.
- **Contention.** Deadlines bind on wall time, which depends on load. The panel sweep must run at **the fleet's concurrency**: 4 evaluations in parallel on the box, matching the 4-chunk fleet, and per-decision walls are reported under that load. A setting chosen at idle load would thin again in a live fleet. Stage 2's live-against-panel co-report checks this. Keep it as registered.
- **The build:** the hook budget and deadline (and the horizon, if D7 is accepted) are constants in `search.php` today, so every setting needs a new teacher build. They become **env-read, run-pinned parameters**, like round 8's W: recorded on every stat row, aborting on mismatch, with the K2-style tree pins moving. Before any live teacher games (Stage 2), the **ghost pre-gate** re-proves the machinery against raw v10 on the new build: action-identical, as round 7's pre-gate did, with K6 applying.

## 5. The other decisions

- **D2, the seed blocks:** accepted. The check against the record is thorough, and leaving the 9001–9200 reservation unused is right. Stage 0's label family 855001 and Stage 2's 955001 are accepted.
- **D3, the Stage-2 bands:** accepted.
  - PROCEED iff the CI lower bound > 0 **and** the per-game gain ≥ +0.05
  - DOES NOT PROCEED or STOP as written
  - the tripwire at a per-game gain > +0.25 or a mean difference > +0.20
  - **And:** the per-game gain uses **the live overturn rate under the calibrated setting**, as written. If D7 is adopted, it uses the horizon-aligned L3.
- **D4, the grid:** accepted as the bounds axes, modified by D7 as in §3, if adopted.
- **D6, the k contingency:** accepted. **The margin does not move**, and the round-8 calibration closed that question for this lineage. A k = 50 cell joins Stage 1 only on a Stage-0 null that is **not** instrument-limited (§1). I decide that before Stage 1 launches.
- **Stage 3:** accepted as form and bands only, not committed. Its timeout is re-derived by contention probe at the calibrated setting, **from a probe large enough to see the tail** (round 7's lesson: 8 games underestimated the mean by about 2×). Size the probe in Stage 3's own registration.
- **The (b) featurizer correction stays out**, which is right: v10 was trained and gated without it.

## 6. What comes back first

The **Stage 0 launch package**:
- the label runner and scorer deployment copies, hash-pinned, with the DELTA = +0.0075 substitution shown
- the unfinished-share and draw-sensitivity reporting from §1
- **if D7 is adopted,** the horizon-aligned L3 as a co-report
- the containment and registry conditions as standing

**Scope:** this reply approves the round-9 design in direction, settles D1–D6 as above (with D1 refined to all-candidate completion), and proposes D7 for Joe's and the builder's decision. It approves no build and no run. The Stage 0 package comes back for code review, then needs Joe's go.
