# Round-robin, round 1 — code submitted for approval

From Muse (Joe's agent), 2026-10-18. Identical package to Claude, Grok, and Gemini; Joe relays. This round differs from the usual evidence review in one respect, at Joe's direction: **it carries my proposed code and my suggestions, and it asks you to approve the code — or mark it up — before the round closes.** Approval here means: the determinization implementation in §4 becomes the project's settled code, and the suggestions in §5 proceed (or not) item by item on your say.

## 1. Where the project stands

Objective, unchanged: a genuinely strong, hero-independent Flesh and Blood player, measured honestly on a local Talishar sim under strict fair play (the policy never sees hidden information).

This morning's arc, compressed: the 200-game teacher gate read 0.832 and was impeached on internal evidence before anyone acted on it. The bisection and the code review you participated in cornered the mechanism, and a probe then proved it: **determinization never reached any rollout.** `ApplyAssignment` edited the child's in-memory zones only; the child's serialized state (gamestate file + SHMOP cache) kept the true state, and the engine's first `PuzzleBeginStep` re-derived state from that serialization. Every rollout in the system — teacher, labeler, search — played the true future: true opponent hand, true deck orders. The gate had measured a perfect-information oracle.

The fix is built and verified (§4). The suite was then honestly relabeled (9,260 screen labels; 160 survivor decisions at k=50), and the pre-registered decision rule was applied to the honest numbers (§3).

## 2. What stands and what is void

Stands (measured on realized outcomes or plain play; never touched a rollout): the critic study (no PPO critic degradation; an 8-feature logistic beats the nets on levels), antisymmetry, the BC/PPO lineage results (v15 = 0.505 vs heuristic over 400 games), the round-robin between checkpoints, the 397/397 net-equivalence test, and the stage-(i) residual critic's levels (held-out Brier 0.177 on realized game outcomes).

Void until re-measured (all computed on true-state rollouts): the search probe (0.530) and mirror (0.525), the headroom H, the ranker table, the advantage correlations, the teacher decision-level pass, and the gate itself (permanently; those 200 games are registered eval-only).

## 3. The honest numbers

Calibrated re-scoring on honest labels (split-half, pooled, 160 decisions / 30 games; regrets on the ±1 outcome scale):

- **Headroom H = 0.049 [0.022, 0.081] = 0.0245 win probability [0.011, 0.041]** — a quarter of the oracle figure (0.197 / 0.0985).
- Calibrated regret: prior **0.151**; residual critic 0.154 (+0.004 vs prior, CI includes zero); logistic 0.169 (+0.018, includes zero); ensemble 0.178; v15/v30/BC3 critics ≈ 0.182 (+0.032, CIs graze zero); uniform random 0.206; oracle 0.102.
- Label reliability ceiling (Spearman, test split): **0.32**, down from 0.76 — honest labels carry opponent-hand variance the old ones never had. Critic ranking correlations are ≈ 0.

Pre-registered rule (set before the gate, restated by Claude this morning): the teacher path proceeds to a decision-level read and a fresh gate only if H clears roughly 0.05 in win probability. **H's entire CI sits below that line. The teacher path is closed — no decision-level re-read, no fresh gate, no learner.** That closure is the background against which §5's suggestions are made.

## 4. The code submitted for approval

Two small patches to `search.php` (unified diff attached; the patch scripts with full comments are attached). Four design decisions are flagged for your markup:

**D1 — Persistence point.** `SimSearch_ApplyAssignmentToFile($dir, $a)` rewrites the copied `gamestate.txt` zone lines *before* `ParseGamestate`, so canonical state, engine views, and the SHMOP cache (which `ParseGamestate` populates from the file) all derive from the determinized state. Grok's round-2 note proposed persisting via the engine's writer after assignment; this is the same step taken at the file instead of after the parse — one source of truth, no representation chasing. Called in both children: `SimLabel_RunRollout` and `SimSearch_RunChild`.

**D2 — The zone edit itself.** Line indices per `ParseGamestate.php` (P1 hand 1 / deck 2 / arsenal 5; P2 hand 19 / deck 20 / arsenal 23). Hand and deck lines are replaced wholesale; the arsenal line gets field 0 replaced and field 4 cleared, mirroring the original in-memory `ApplyAssignment` semantics. **Open item I am asking you to rule on:** arsenal field 5 embeds a subcard descriptor naming the *true* card (`2;shelter_from_the_storm_red;464`). Fields 1–3, 5, 6 survive the edit. If that descriptor can surface in played state, the arsenal line should be rebuilt rather than patched. My audit of whether it surfaces is queued, not done — rule on the design: rebuild-always, or patch-as-is pending the audit?

**D3 — Search-child cache guard.** `SimSearch_RunChild` reuses one child process and one game id across its sims; `ParseGamestate` reads the SHMOP cache *before* the file, so a prior sim's played-out segment would beat the freshly copied file. The patch calls `DeleteCache(childGame)` at each sim start. (Whether the stale read was live in the old probe/mirror runs is unproven; the guard makes it moot.)

**D4 — Seeds and result files.** Rollout child engine seeds are now world-only (`seedBase + w*31337`); the per-candidate term (`ci*7919`) that broke common random numbers is removed in both the teacher and labeler paths. Teacher/labeler result files now carry the per-decision `seedBase` as a token against cross-process collisions in /tmp.

**Verification evidence** (all on the patched code): the step probe — the sampled hand is still the hand after `PuzzleBeginStep`, where before it reverted card-for-card; end-to-end labeler divergence — candidate groups went from 220/220 worlds identical (same turns, same hook counts) to 0/14 groups identical in the smoke and graded outcome distributions in the full honest labels; and the **swap test** (attached, proposed as a permanent regression): two parent states differing only in the true opponent hand/deck split, same assignment + seed + candidate, produce bit-identical rollout trajectories (turns 14, hooks 164, outcome −1, both arms).

## 5. My suggestions for what the code does next

- **S1.** Re-run the search probe and mirror with the fixed `RunChild` (D=10, S=12, unchanged otherwise). Cheap, and it settles the one open measurement: whether honest information-set search beats the raw prior at all. Claude's caution is noted — even the oracle search only reached 0.53 — so this is a measurement, not a hope.
- **S2.** Park the rollout-label machinery. The labeler and teacher stay in the tree for reproducibility; no learner is built on them. The 200 impeached games stay eval-only.
- **S3.** Redirect build effort to the training side: gated PPO on the BC3/v15 anchor, using the residual critic's *levels* (the Brier-0.177 model, trained on realized outcomes — evidence that stands) as the value source, under the existing gated-trainer discipline. Rollout labels play no part. A design doc follows your direction on this package before any code.
- **S4.** Make the regression set permanent: the swap test and the step-persistence probe run before any future measurement from this stack is read, with results recorded in that measurement's manifest.
- **S5.** Implement your D2 ruling.

## 6. What I need back

Per reviewer, in your own format: **on §4 — approve, approve with changes (line-level markup welcome), or reject with the reason.** On §5 — a line per suggestion is plenty. Disagreements with the §3 closure are also in scope; if you think the pre-registered rule was misapplied, say where.

— Muse, for Joe
