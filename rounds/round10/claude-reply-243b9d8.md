# Claude — ruling on the round-10 Step 0 probe's final report

**Reviewed commit:** 243b9d80b159c178e88f57f2b5414bd76da82e6b (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-fdfe37a.md` hashes to `0434f774…b44645`, the value I gave Joe. The report is `864b8367…`. No code or fixture changed since fdfe37af, and the completion's four outputs hash to the stated values.

**Ruling: the probe's read is FINAL as registered. Threshold 0.97 is buildable; the margin lever is closed at this registration.** Step 1 is approved in direction, pilot-first, on the terms in §3.

## 1. Recomputed

**The influence read**, using my own code over the published `labels_merged.jsonl.gz`, the cap-aligned classes, and the 90 capture games from the driver rows:

| Lever | Full gain | LOGO range | Largest single-game share | With that game excluded |
|---|---|---|---|---|
| Threshold | **0.4734** | [0.3259, 0.4863] | **0.3192** (game 635852068) | gain 0.3259, bootstrap lower bound ≈ 0.179 (report: 0.1753; the difference is bootstrap draw) |
| Margin | 0.0076 | [0.0052, 0.0103] | 0.3235 (game 221917095) | lower bound ≈ −0.008 |

- **The hold rule correctly does not fire** for either lever.
- **The state inspection of 540261752** matches mine from the eval rows snap for snap: 22, 15, 1 and then 0 wins by turn 61.

**The single-game check passed, and it's a real result, not a technicality.** The threshold's signal survives removing its largest carrier with a lower bound near +0.18. Combined with the §15.6 bounds (about 0.27 counting each choice once, about 0.13 counting the best fix per game, both well above Stage 3's 0.065), the threshold lever is **a genuine lead**. Its true on-trajectory size is unknown, and measuring it is exactly the pilot's job.

## 2. What round 10 has established so far

1. **The margin lever: closed.** Lowering the margin adds fires worth about nothing: an increment of +0.0076 [−0.0067, +0.0211], with a labeled edge of +0.007. That matches the direction review's prediction from round 9's z-bands.
2. **The confident states hide real catches.** The prior's ≥ 0.97 decisions fired at 9.9% per sampled state, against 5.5% for contested states. Labeled edge: +0.070 [0.034, 0.114] overall, and +0.48 [0.33, 0.61] on the 21 tail catches.
   - The concrete pattern is the 540261752 kind: raw v10 re-activating an ally into a turn-cap draw when a card in hand wins.
   - That's a policy blind spot a search **in those states** can fix, and the current teacher never looks there.
3. **The instrument is now aligned.** The horizon defect was found and fixed, and round 9's L3 conclusions were re-verified under the fix. All future builds carry the §14 engine.

## 3. Step 1, pilot-first: terms for the package

1. **One change, on the fixed engine.**
   - **The build:** the §14-fixed search (horizon checked per step, horizon-forces-draw), with **the uncontested threshold lifted**, so every decision with ≥ 2 candidates is contested.
   - **Unchanged:** margin 1.5, k 25, bounds 8000/180, horizon 62 at −1, and the candidate rule.
   - **What gets attributed:** the horizon fix also differs from Stage 3's live teacher, so the pilot reports **per-class** results. The contested class gives continuity with Stage 3's +0.065; the newly contested ≥ 0.97 class is the lever.
   - Pre-gate (ghost/K6 action-identity) as standard.
2. **The pilot.** It's a live teacher run, not a fleet.
   - **Size:** **100 teacher games** vs the heuristic, Gravy mirror, 87/62, on a **fresh seed block**, with every overturn captured.
   - **Cost:** at about 1,840 s per game, about **51 box-hours, roughly 13 h of wall time at 4 blocks.**
   - **Timeout:** a generous provisional value, stated with its derivation. For example, Stage 2's maximum game wall × the measured 3.66 cost factor × 1.0 ≈ 7,850 s. The pilot's own tail sets Step 2's timeout.
3. **What the pilot measures**, with L3 at the registered label configuration on **all** its overturns:
   - **fires per game** by class;
   - **per-game gain on the teacher's own trajectory**, by class and in total, in the direct form: game-clustered, all games including zero-fire games, no sampling weights;
   - **the edge** by class and by z-band;
   - **wall per game** (mean, p95, max) and timeouts;
   - **the influence read** (LOGO and largest single-game share).
4. **The pilot's registered rules, fixed before it runs.**
   - **STOP**, with no Step 2, if the total per-game gain's one-sided 95% **upper** bound is below **0.0649 + 0.020**. The new teacher then can't plausibly beat Stage 3's by the margin Step 2 could detect at 400 games.
   - **Otherwise, size Step 2 from the pilot:**
     - by the registered two-sample bar against Stage 3 (+0.0649, SE 0.0090);
     - at **80% power for Δ_plan = the pilot gain's one-sided 95% lower bound minus 0.0649**, never the point estimate, because Step 2 is selected by the pilot;
     - with SE_new scaled from the pilot's game-clustered SE by √n.
   - **If that size exceeds 400 games,** it goes to Joe as a cost decision.
   - **The pilot's games are never pooled into Step 2.**
5. **Standing requirements, all from this round.**
   - the §14 engine in every build and eval;
   - **strict JSON job files** (no non-finite tokens) and **loud loaders** in every PHP driver that reads jobs, `s1_eval_main.php` included;
   - the composed-environment fixture and env audit for every runner;
   - writer→reader round trips on real output shapes;
   - an invocation-parity fixture wherever a script re-invokes another's step;
   - `expect_hash` on every deployed file;
   - fixtures that read only published data;
   - status-only notices;
   - publication with a MANIFEST.

**Scope:** this accepts the Step 0 probe's final report (threshold buildable, margin closed, hold not triggered, recomputed and verified) and approves Step 1's direction on the §3 terms. It approves no build and no run. The Step 1 package comes back for code review, and the pilot launches only on Joe's go.
