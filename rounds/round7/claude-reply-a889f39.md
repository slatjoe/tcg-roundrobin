# Claude — reply to the round-7 stage-3 follow-up (K1–K5)

**Reviewed commit:** a889f3940fc8e0ef31a127127a0179d01468eabd (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-dd4cb2f.md` hashes to `0c2d9cee…ac4f533c`, the value I gave Joe.
**Package:** rounds/round7/followup-k1-k5.md
**Verdict:** **CHANGES REQUESTED, two small items.**
- **K2, K4 and K5 are accepted** as written.
- **K1 needs one correction, and it's my error** (§1).
- **K3's control has a factual error** that would make the pre-gate unreadable (§2).
- Both fit in one small commit. Stages 1–2 are still running, so it costs no wall time.
- The pending-hash approach for the probe is accepted (§3).

What I checked:
- the follow-up in full
- the `gravy_ppo_launch.sh` diff: the probe variable, a guard before any `mkdir` or worker, and `--probe` passed explicitly
- the `run_gravy_gate.sh` hash-guard description
- `build_gravy_probe.py`'s argument surface (a single `--corpus`, `--expect-games` default 2400, `--per-corpus` 9000)
- the O results' pre-gate control wording

## 1. K1: build the probe from all three corpora, as the recovered recipe does

Recovering the Fai recipe from primary records was well done:
- the tool and its hash
- `build.log`'s four lines
- the selection rule at `probe_kl.py:28–58`
- the Gate's fixed 4,096 subsample with seed 20261016
- reference log-probs computed once

That recovery shows the Fai probe came from **all three of its run's training corpora** (mirror, cross and the DAgger batch, 9,000 each, 27,000 states). My K1 named only the mirror corpus because I didn't know the recipe. With the recipe in hand, "verbatim" means the same three-corpus structure:

- **Required:** build `probe/probe_gravy_v1.jsonl` from `gravy_bc/data/{mirror_self, cross_self, mirror_bc}` at 9,000 each, 27,000 states, through `probe_kl.py build` exactly as Fai's was, with the independent re-scan verifying each corpus's kept sequence.
- **Game-count guards per corpus:** 2,400 / 750 / 1,500.
- The DAgger batch matters most here: its states come from the clone's own play, closest to where the PPO policy will actually play.
- All three corpora exist when stage 1 completes, which is before stage 2. So the build still lands inside the current window.
- This is a small extension of `build_gravy_probe.py`: a corpus list, and an expected-games value per corpus. Commit it with its scratch test, re-run in the same form as V.2.

## 2. K3: the control is described backwards

The follow-up says the same-seat raw re-run is "expected to **differ** on all 10 units… the bridge's play is not a deterministic replay." **That's wrong, and if it were true the pre-gate couldn't work.** The whole ghost-equals-raw design rests on the bridge being **deterministic under a fixed seed**:
- round 2: bridge vs bridge-repeat, 19/19 byte-identical
- round 3: the rerun's per-seat games replaying exactly
- round 6: the pick-flip run replaying the census games byte for byte

A ghost/raw match only means something if raw replays itself. The round-3 standing control that *must differ* is a different pair: **raw seat 1 against raw seat 2 on the same seeds**. That was the check that caught the seat-routing defect.

**Required:**
- **Determinism check:** a second raw run at seat 1 on 8501–8510 must be **IDENTICAL** to the first on all 10 units. Any difference stops the pre-gate, because the comparison would then be meaningless.
- **Standing raw control:** raw seat 1 against raw seat 2 on 8501–8510 must **differ** on at least 1 unit (the R16 rule). This uses the pre-gate's existing raw runs, so it needs no extra games.
- **State what the O pre-gate's "raw-control self-pairing differed on 10/10" actually paired.** If it was seat 1 against seat 2, it's this control and the wording should say so. If it was a same-seat re-run that differed, that's a determinism problem in the O pre-gate, and I need to see it.
- Read the pass criterion through the standard instruments: `r3_pair.py` / `classify_divergence.py` IDENTICAL with `within_row_hits = 0`, plus the outcome fields. The gamelog sha alone isn't enough.

## 3. The pending probe hash: accepted as a launch artifact

Approval covers the recipe, the builder, the guards and the independent re-scan, not a hash that can't exist yet. Treat the hash as a launch-time artifact, like the extended vocab's:
- the builder records it in a builder note and in the stage-3 manifest
- a recomputation mismatch at manifest time voids the build, which is then rebuilt
- **No re-review is needed for the hash itself**, provided the build passes every guard. A guard failure (short yield, re-scan mismatch, game count) stops stage 3 and comes back as a package.

## 4. Accepted

- **K2:** the tree is built from `/tmp/otree`, with the abort patch carried and the hashes pinned in the runner, guarded before any `mkdir` or server, and dry-run tested with a wrong-hash tree. The census diagnostic's guard stays as is.
- **K4:** stop (e) restated as the climb-and-ahead calibration pattern.
- **K5:** the two-condition DUP_SEQ rule, with the precedent stated at its actual scope.
- **K3's ghost arm:** `TEACHER_MODE=1` + `TEACHER_GHOST=1`, with the ghost block at `search.php:1029` forcing the prior's pick after the full machinery runs. That's the registered arm.

## Not reviewed

- The updated `run_gravy_gate.sh` guard block's code text. I took it from the follow-up's description and dry-run evidence; the next commit's diff will show it.

**Scope:** stage 3 and later are not yet approved. The next commit carries the three-corpus K1 builder and the corrected K3 controls; on review of that sha (with the probe hash recorded as a launch artifact under §3), stage 3 onward can be approved. Stages 0–2 continue under the dd4cb2fe approval.
