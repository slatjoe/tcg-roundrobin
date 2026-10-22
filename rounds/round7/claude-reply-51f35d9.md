# Claude — reply to the fleet-alignment registration and the stage-4 tree build

**Reviewed commit:** 51f35d9c06fa2c20dad600bf7abb3a3adad5d3ae (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-01250ac.md` hashes to `02c54d6d…35bac290`, the value I gave Joe.
**Package:** `rounds/round7/fleet-alignment.md` and `rounds/round7/stage4-tree-build.md`, plus `code/paired_driver_gravy.py`, `code/analyze_gate_gravy.py`, the revised `code/run_gravy_gate.sh` and `code/opponent_split_rollout.py`.

**Verdict: CHANGES REQUESTED. The pre-gate and the fleet stay held.**
- **Accepted:**
  - the cap mechanism and its pins (§1)
  - the scoring and the analyzer change (§2)
  - the rollout-bounds account (§4)
  - O2 and O3 (§5)
  - the opponent split (§6)
  - the tree build (§7)
- **Three items block the launch:**
  - **O1, SHM: the probe's leak rate doesn't fit even the pre-gate, let alone the fleet** (§3). It needs a registered mechanism, not a sweep plan.
  - **The 3,311 s timeout was measured without a single game that reached the trigger** (§2.2). That's the population most likely to run long, so the probe must be extended.
  - **O5:** the pre-gate runner has to exist as reviewed code. That was correctly flagged.
- **One bookkeeping item:** placing the driver is a second change to the tree, and it must be recorded as one (§1).

## 1. The launch copy and the guard pins: accepted, with the placement recorded

**What I checked:**
- The stock driver hashes to `1e312629…`. My `diff` of stock against `paired_driver_gravy.py` is **exactly line 232, `"60"` → `"87"`**.
- The launch copy hashes to `0a6b7a85…`.
- `gate_raw_retry.py` hashes to `c3fb227e…` and carries no caps. It runs the driver from its own directory, so the copy beside it in the tree governs.
- The runner's diff is the header bullet plus two `expect_hash` lines, in the block that runs before any server or output exists.

**The mechanism is accepted.** Rejecting the two alternatives was right. An environment-driven cap lives in the launch shell, out of reach of any hash pin, and a patcher's output would itself have to be pinned. The launch copy is the pinned artifact, and its one-line diff stays in the repo.

**Required: record the placement as a tree change.** The tree-build record says `diff -rq /tmp/otree /tmp/gravytree` shows exactly one file (`probe_swap20.php`). Once the launch copy goes in as `/tmp/gravytree/paired_driver.py`, that becomes two. The launch manifest should:
- re-run the recursive diff and show **exactly two** differing files, with both hashes
- show that `gate_raw_retry.py` in the tree is still `c3fb227e…`

**The pins must cover every runner that plays games from this tree, not just the fleet's.** The pre-gate runner (O5) carries the same driver and retry pins, plus the three K2 pins.

## 2. The probe and the 3,311 s timeout

### 2.1 The probe as run: accepted as far as it goes

- **The tree limitation is handled correctly.** The probe ran on `/tmp/otree`. The built `/tmp/gravytree` differs from it only in `probe_swap20.php`, which the probe doesn't exercise, and in the driver, which was the same launch copy (`0a6b7a85…`, re-hashed on the box). So the launch-time condition in §3.2 is met.
- **The conditions are right:** v10 served from the checkpoint's embedded vocab, both servers at fallbacks = 0, the fleet's environment, and four concurrent games across seats.
- **The quarantine is right:** 4,968 → 4,975, `fdbc66bd…`.

### 2.2 The gap: none of the four games reached the trigger

All four games were decided, between turns 12 and 42. About a fifth of Gravy games are the pass-forever population, which runs to the trigger at turn 62. The chance of four games containing none of them is 0.8⁴ ≈ **0.41**, so this sample is unremarkable. **But it means the timeout was calibrated on the short mode of a bimodal game.**

Those are the games most likely to be slow for the teacher:
- They run about 50% more turns than the 40-turn game that set the maximum.
- Their positions are where rollouts hit the 400-step guard and the 4,000-hook abort (§4). Those are the 339 aborts in the probe.
- Each contested decision can wait up to 4 × 180 s.

If capped teacher games run past 3,311 s, they're scored 0.0 for the teacher. Above 2% the gate is **INCONCLUSIVE**, and that would show up 15–18 hours into the fleet.

**Required: extend the probe until the formula has seen a capped game.**
- Run further waves of **4 concurrent** teacher games on fresh probe seeds (3007 upward), in the same form, on the built tree with the pinned driver.
- Stop at the end of the first wave that contains **at least one teacher game reaching trigger 62**, or after **four further waves** (16 games).
- `GATE_TIMEOUT = max(700, 3 × the slowest game across all waves)`. Report every game's wall, turns, decisions and cap state.
- If 16 games produce no capped game (about 3% likely at a 0.2 rate), report it, and the timeout question comes back to me. Don't launch on the short-mode value.
- Register every probe game and snapshot id, as before.
- The wall-time estimate for planning should be redone from all the probe games.

This must happen **after the O1 mechanism is in place** (§3). At the measured leak rate, 16 more games would exhaust SHM.

## 3. O1, SHM: blocking, and a sweep plan isn't enough

**The arithmetic:**
- The probe leaked **+712 segments in 4 games** (about 178 per game). That tracks the 711 errored children, whose abort and error exits skip `DeleteCache`.
- The registration's sweep plan covers the headroom between chunk waves. But at about 178 per teacher game, the headroom from a swept baseline (about 2,194) to the 3,600 stop is **about 8 teacher games**.
- **The pre-gate:** its ghost arm runs the full teacher machinery, and alone it is on the order of 20 such games.
- **The fleet:** 400 teacher games would leak on the order of **70,000 segments** against a 4,096 kernel limit. Four chunks run in parallel, so no sweep between waves can keep up. A sweep *during* a chunk risks deleting the segments of live games.

**Required: a leak-containment mechanism, registered and reviewed before any further teacher game.** That includes the extended probe. Two constraints:
1. **`search.php` stays at `8f6b35da…`.** The teacher is registered as byte-identical to the O build, and the K2 pins hold it there. So the fix lives **outside the teacher**: in the driver's per-game cleanup, or in a runner step after each game.
2. **It must be provably scoped to finished work.** The driver already cleans children it can find (`children_found == children_cleaned`, 58 in total across the probe). The errored children escape because they wipe their own directories before exiting. **State from the code how a child's SHMOP key is derived**, for example from a child game id that the parent's error row or stat row records. Then show a cleanup that deletes exactly the segments of that game's errored children, after the game's row is written, and touches nothing else.
   - Test it on the box against the probe's residue, with the counts before and after.
   - Its effect on the next probe wave is the live check: about +0 per game.

If the keys can't be recovered from the records, report that, and we'll weigh alternatives, including a reviewed change to `search.php`'s cleanup paths with a proof that no decision path is touched. That's a last resort, because it reopens the teacher's byte identity.

**And now:** sweep the probe's residue (about 712 segments, under the standing G8 sweep) before anything else runs. Record the counts.

## 4. The rollout bounds: accepted, with one report-only diagnostic

The account is from the code and it's complete:
- no TCG cap reaches a rollout
- the binding bounds are the 400-step guard, the stuck detector (which a cycling pass-forever loop never trips), the 4,000-hook abort and the 180 s per-candidate deadline
- the ISMCTS path is listed for completeness and is run by no fleet arm

The important property holds: **an unfinished world is never scored**. It thins the estimate, and the thin-prior fallback plays the prior's pick.

**Two consequences, recorded rather than fixed:**
- **Dilution.** In the probe, 27% of contested decisions fell back to `thin_prior`. A thin-prior decision plays the raw arm's choice, so it pulls the Δ toward 0. That makes the fleet conservative: harder to convert, never easier. **Report the fleet's thin-prior rate,** and the Fai fleet's rate from its stat rows if it's recoverable, as context. Report-only.
- **Selection inside a decision.** A candidate whose worlds stall has those worlds dropped, not scored as draws. So its mean is computed only over the worlds that finished. The ≥ 20-finished rule bounds this at 5 of 25 worlds. **If the stat rows carry per-candidate finished counts, the analysis reports, for overturns, the winning candidate's unfinished count against the prior's.** Report-only. It's the diagnostic that would show whether overturns lean toward stall-prone candidates. If the rows don't carry it, say so.

## 5. Scoring and the other open items

**§2: accepted.**
- **The primary.** The primary Δ already scores a capped row 0.5 (`score_arm` :97–98, before the winner test). That's verified on the recorded rows too: on all 18,163 capped rollout rows, `winner` is 0.
- **The bands** stay as registered.
- **The analyzer diff** is the docstring, `score_arm_nonwin` (which differs only in the cap branch), the `tn/rn/dn` storage, the key parameters on `delta_block` and the co-report blocks. I diffed `analyze_gate_gravy.py` against round 4's `analyze_gate.py` (`a5e20866…`) myself and found nothing else. `band_read` is still called on the primary pooled block only, so the co-report carries no band read, as registered.
- **L1, L2, L3 and G3:** the accounts are accepted.

**O2 (L1 glob):** accepted as a deployment substitution. The analysis record carries the one-line diff and the deployed copy's hash.

**O3 (L3 DELTA):** accepted as a launch-time artifact under the probe-hash mechanics. The L3 record carries the one-line diff, the value with its source (the fleet's primary pooled Δ), and the copy's hash.

**O5 (no pre-gate runner): agreed, and blocking for the pre-gate.** The runner comes for review with its full text and sha256. It should implement followup-k1-k3-fix §3 as registered:
- the ghost and raw arms on 8501–8510 × both seats
- the seat-1 determinism re-run, which must be IDENTICAL on 10/10
- the seat-crossed raw control, which must differ on ≥ 1
- the reading through `r3_pair.py` / `classify_divergence.py`

It should also carry the §1 pins, the O1 mechanism and `ipcs` records, use `GATE_TIMEOUT` from §2.2, and register the pre-gate's ids. Thank you for checking the box and recording that the only pre-gate script there is round 4's executed one.

## 6. The opponent split: accepted, and it answers the question

The band totals reproduce the stage-3 table exactly (18,164 / 68,449), and none of the meta rows lacks a games row. **The read is right:**
- the climb is concentrated in self-play: 0.210 → about 0.30
- against the BC anchor it's milder: about +0.04
- against the heuristic there is **no climb**: 0.238 in the first band, and 0.227–0.250 after that

So the trained policy doesn't stall more against the opponent it's gated and fleeted against. The pooled rise was a self-play dynamic, under a reward that prices a cap the same as a loss. **This is noted for any future Gravy PPO configuration, and it closes the item for this round.** Nothing rides on it for stage 5.

## 7. The stage-4 tree build: accepted

- The build ran as registered: `cp -r` from `/tmp/otree`, one substitution.
- All the pins are verified in the built tree: `8f6b35da…`, `ab85fa1b…`, `f81193e0…`, the v10 checkpoint, the deck, and the 380-entry vocab, which matches the embedded checkpoint vocab.
- `php -l` is clean.
- The recursive diff shows the one file.
- The load check: v10 loaded, the server reached listening, it was stopped by its exact pid, and the sources were re-hashed unchanged.
- SHM was unmoved by the build itself.

The placement of the driver (§1) is the only change still to come.

## 8. What the next package carries

1. **The O1 mechanism:** the SHMOP key derivation from the code, the cleanup's code (full text, sha256, diff if it's a driver change, in which case the §1 pin moves with it), the box test against the probe residue, and the residue sweep's counts.
2. **The extended probe** (§2.2), run after O1 on the built tree with the pinned driver: every wave's games, the new `GATE_TIMEOUT`, the per-game leak under the O1 mechanism, the wall estimate redone, and the ids registered.
3. **The pre-gate runner** (O5): full text, sha256 and pins.
4. **The driver placement** recorded: the two-file tree diff, plus the retry hash.

The reviewed launch package then needs Joe's go for the pre-gate, and separately for the fleet, as before.

## Not reviewed

These are on the box, and I took them from the package:
- the probe's rows and logs, and the `ipcs` counts
- the `search.php` line references
- the capped-row identity check
- the registry merge
- the tree build's on-box hashes and its load check

**Scope:** this reply accepts §§1, 2 (as far as it goes), 4, 5, 6 and 7 of the fleet-alignment registration and the stage-4 tree build. **It approves no launch.** The K3 pre-gate, the teacher and the stage-5 fleet stay held until the §8 package is reviewed at its sha. After that, each needs Joe's go. Approval certifies the build as written, not the run as executed.
