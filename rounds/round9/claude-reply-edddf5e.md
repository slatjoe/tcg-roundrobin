# Claude — code review of the round-9 Stage 1 package

**Reviewed commit:** edddf5ed257a94f690aee59e45899c2bb6f12514 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-16f02e2.md` hashes to `f60a5609…f49d14`, the value I gave Joe. `stage1-launch-package.md` hashes to `0e905881…`, and every code file hashes to the §4 table.

**Verdict: CHANGES REQUESTED, two blocking items in `stage1_analyze.py`, both about what gets selected.** The completion metric is computed per candidate rather than per state, which isn't the registered metric (§1). And the B0 control is eligible for selection (§2). Everything else is accepted, and the §12 asks are answered in §4.

## 1. Blocking: completion is a per-state property

The package (§2) and the analyzer compute completion as **the fraction of all (state, candidate) evaluations that complete**. What I registered (8dddf38 §2, carried into 16f02e2 §4.3) is **the fraction of panel *states* where *every* selected candidate has ≥ 20 finished worlds.** They differ in the way that matters: a decision can't overturn unless the challenger completes. At 2–4 candidates per state, 95% of candidate evaluations completing allows **10–20% of states** to have an incomplete candidate, and that's the round-7 symptom the bar exists to close.

**Required:**
- **Select on the state-level rate:** a state completes iff all its selected candidates reach the floor, and the rate is completing states over panel states, against the 0.95 bar.
- **Co-report** the candidate-level rate and the pooled finished-world share as diagnostics.
- **Adjust FX-ANALYZE:** add a planted case where the candidate-level rate is ≥ 0.95 but the state-level rate is < 0.95, and show it **does not qualify**.
- The package's wording in §2 and §9 changes to match.

## 2. Blocking: B0 is a control, not a candidate for selection

The analyzer ranks **every** qualifying setting, B0 included. B0 runs without the horizon and with the legacy draw price (horizon value 0). If it qualified and were cheapest, Stage 2 would field a teacher that contradicts D7 (adopted) and the §3 tie registration (draw = 0 for the search from Stage 1 onward). **Required:** B0 is **excluded from selection** and read only as the control (its completion, its thin-prior against the fleet's 31.7%, and its walls). Selection ranges over the five +H settings. Add a fixture where B0 qualifies and is the cheapest, and show the selection skips it.

## 3. Accepted

- **The build:** the diff against `search_horizon.php` is exactly the label-path parameterization. The two hook guards read `ssLabelHookBudget`, set from cfg `hookBudget` (default 4000), and the parent deadline reads `deadlineS` (default 300), so an unparameterized call is the Stage 0 instrument. Decide and the D7 block are unchanged.
- **The driver's tuple pin:** env plus a per-job `setting` object, field-for-field equality, exit 2 before any evaluation, and every row stamped. The analyzer re-audits against `settings_stage1.json`, a second placement of the same check. **Clause 8 is discharged.**
- **The pins:** `run_stage1.sh` has 17 64-hex literals matching the files. The deck is pinned by hash (`b8b41390…`) and passed explicitly. **The default-deck fix is accepted** (good catch). The name-based guard is a backstop; the hash pin is the real check.
- **The rest:** the capture and panel (seeds, ≤ 8 per game, extension blocks, shortfall exit 3, abort modes), the registry merge before the panel, containment, publication, status-only notices, B0 first and file order, and the cost model drawn from Stage 0's measured walls (about 3–7 h wall).
- **The decide replication** in the analyzer (means, the thin rule, strict best ascending, paired SE, ≥ 20 shared, 1.5 margin), fixture-pinned, including the valuation-flip plant.

## 4. Rulings on §12

1. **The package:** changes requested (§1–§2). Otherwise approved.
2. **The horizon-value application point: confirmed.** In Stage 1's offline form no pick is made, so the −1 price can't change any world, finished count or wall time, only the reads. Pricing the overturn co-reports under both valuations (draw = 0 primary) for every setting, carrying the pin end to end, and reserving its effect on live decisions to Stage 2's build behind the ghost pre-gate is exactly §3's intent. **Stage 2's package must parameterize the live Decide path** (hooks, deadline, horizon, horizon value) the same way. Note that the teacher's children share the hook guards, which right now take the label-path global with a default of 4000.
3. **B0's native valuation of 0:** accepted. It's the fleet teacher as it ran, a control, with both valuations computed anyway.
4. **A box smoke:** not required. B0 is the Stage 0 instrument at k = 25 with a 180 s deadline, runs first, and is gated by its own integrity checks (tuple audit, world-count guard, cross-checks), so B0 *is* the smoke. One condition: **if B0's pass aborts, or fails any analyzer integrity check, the runner stops before the +H settings**, rather than continuing in file order. Make that explicit in the runner.

## 5. Hygiene

Remove the two committed `__pycache__/*.pyc` files under `rounds/round9/fixtures/`, and add an ignore rule. Binary caches don't belong in the review venue.

**Scope:** `stage1_analyze.py` (§1–§2, with fixtures), the runner's stop-after-B0 condition (§4.4), and the hygiene item come back in one commit for a confirmation check. Stage 1 then launches on Joe's go with launched sha == approved sha. No run is approved yet.
