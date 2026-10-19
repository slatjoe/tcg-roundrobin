# Claude — reply to the round-3 rerun results

**Reviewed commit:** 6a0d7d4311d8fe451cd7abc2d971e6de5fa664fc (HEAD verified after checkout; clean tree; equal to `origin/main`). My reply a6e9a63 is in the history as Joe's upload (44a7b40).
**Package:** rounds/round3/data/rerun-launch/results-summary.md
**Verdict:** **the pre-gate PASSES.** I accept the result as reported, against the registered reads. This reply also gives the seed-19/timeout ruling and states what the gate build package must contain. No gate launch is approved here.

## Independent check of the result

I recomputed the pairings from the committed row files rather than reading the tables. On winner, turns, decisions, both life totals, normalized end state and gamelog sha:

- raw vs ghost: 19/19 equal at seat 1 and 19/19 at seat 2
- raw vs shadow: 19/19 equal
- ghost vs capture: 19/19 equal
- raw s1 vs raw s2: 0/19 equal, so the raw control passes
- validity: no row is invalid, every row's `server_seat` equals its arm seat, and there are zero seat mismatches and zero connect failures
- all six manifests have `assert_ok` true

Both launch conditions are met as recorded: built hashes match, and the production server hash is equal before and after. Both servers end with `fallbacks=0 seat_mismatch=0`.

**What this establishes:** the teacher machinery in ghost mode reproduces plain v15 decision for decision at both seats. In the gate, then, any difference between teacher and raw on a paired seed must begin at an overturn.

Two notes for the record:
- Ghost s2's canary rate (1.89%) sits just under the 2% cap. Watch it in the gate (see G7).
- The +19 shared-memory segments per raw arm are one per game, consistent with `KEEP_GAME=1` skipping the game's own `DeleteCache`. The ghost arms' ~+5 per game is from rollout children. G8 deals with this, because it now matters.

## Seed-19 and timeout scoring for the fleet (ruling)

The old seed-19 exclusion came from the misbuilt arms and is **retired**. Seed 19 is an ordinary seed, though the gate uses fresh seeds anyway (G1). For timeouts and caps, pre-registered now:

1. **Engine caps** (turn cap 60, decision cap 3,000, stuck limit) are game outcomes. Score them **0.5 for both seats** and report each one with its cap reason.
2. **A wall-clock timeout in the teacher arm** scores as a **teacher loss** in the primary analysis, because the teacher must not gain from running out the clock. Report a sensitivity analysis with those pairs dropped. **If teacher timeouts exceed 2% of teacher games, the gate is inconclusive** whatever Δ says.
3. **A wall-clock timeout in the raw arm** (raw games take seconds) is an engine hang. Re-run that game once. If it hangs again, score the raw arm 0.5, keep the pair, report the seed, and file the hang class. If raw times out but the teacher completes on the same seed before its first overturn, that contradicts the pre-gate. Treat it as a defect and stop.
4. **Set the timeout from data, not a guess:** 3× the 99th percentile of the ghost arms' game times in this rerun, stated in the package. Teacher games with overturns may run longer than ghost games. If the smoke shows that, set it from the smoke instead.

## What the gate build package must contain

This is the round-2 registration, updated for what we've learned since.

**G1. Design.**
- Teacher (`TEACHER_MODE=1`, no ghost/shadow/capture) vs raw v15 on **paired seeds**, both against the heuristic, **both seats**.
- **200 fresh seeds per seat**, a range never used before (e.g. 1001–1200), registered in the package.
- The teacher is exactly the measured artifact: k=25, top-3 plus prior ≥ 0.10 (cap 4), continuation `va`, overturn at 1.5 paired SE, R17 root state. A k=10 variant is a separate registration.

**G2. Analysis script committed before launch, with a fixture test I can run.**
- **Unit:** (seed, seat). Report per seat and pooled, with the bootstrap clustered by seed.
- **Primary:** paired Δ = teacher win rate − raw win rate, with its CI.
- **Discordant counts:** pairs where teacher wins and raw loses vs the reverse, with an exact sign test.
- **Bands as registered:**

  | Result | Read |
  |---|---|
  | Δ ≥ +0.05 with CI lower bound > 0 | converts |
  | Lower bound > 0 but Δ < +0.05 | real but small |
  | CI includes 0 with upper bound < +0.10 | the projection overstated conversion |
  | Δ > +0.20 | **impeach before reading** |

**G3. First divergence must be an overturn.** Keep the trace on in both arms. For every pair whose games differ, the first divergence must be a DECISION at a teacher row whose `decide_pick` ≠ the bridge argmax, which is an overturn. Any pair whose first divergence is anything else (STATE, WITHIN_ROW, RNG, or a DECISION at a non-overturn row) is a machinery defect. Any one of those stops the read. This is the direct consequence of the pre-gate, and it replaces "trust that only overturns changed the game" with a check.

**G4. Overturn audit.**
- Keep `TEACHER_SNAP_DIR` on, so every overturn snapshots its state.
- After the run, relabel a random sample (~100, or all if fewer) with fresh determinized rollouts at k=50 under the current labeler. Report the fraction where the overturn pick beats the prior pick, with its CI. This is realized conversion per overturn.
- Report the overturn rate. Expect around 5% of contested decisions. Well above that, look for a margin bug before reading Δ.

**G5. Calibration monitor (the October signature).** From the teacher's stat rows, plot the prior-pick rollout mean by decision ordinal against the realized outcome of that game. Honest play stays roughly calibrated. A climbing curve that runs ahead of the outcomes is the void-gate pattern, and it impeaches the run.

**G6. Fleet.**
- Four chunks, seats balanced within each chunk, per-seat servers (R12) with `seat_ok` on every row.
- Production server hash checked before and after.
- Launch conditions 1–2 carried over, with the gate tree's own built hashes.

**G7. Coverage.** Canary refusals ≤ 2% per arm-seat, with branches above 5% named, as amended. Report child aborts by reason and candidate. Stat rows must carry `det_persisted` on every row.

**G8. Shared memory, which is now a blocker, not bookkeeping.**
- The box is at 3,225 segments. At ~5 per teacher game, 400 teacher games add roughly 2,000 more.
- Linux's default `kernel.shmmni` is 4096. Report the box's value. If the gate's projected total would come within 20% of it, **clean stale segments first**: only segments with no attached process, verified by `nattch` = 0 and a game id whose process is gone.
- Add per-game cleanup of rollout-child segments in the teacher path, and record `ipcs` per chunk.
- What the engine does when a cache write fails is unknown. I don't want to discover it mid-gate.

**G9. Registry.** Register all gate game ids as eval-only in the do-not-train registry before any analysis runs. The overturn snapshots (G4) are eval-only too.

**G10. Smoke before the package.** One seed per seat through both arms, plus the analysis script on the smoke output. Report teacher game time, overturn count, and the G3 first-divergence check on any pair that diverges.

## Not reviewed

- The traces and gamelogs on the box. I relied on the committed rows, manifests and server counter lines.

**Scope:** this reply accepts the pre-gate result at 6a0d7d4 and registers the timeout ruling and gate requirements. It approves no launch. The gate returns as a package carrying G1–G10, reviewed at its sha, and still needs Joe's go.
