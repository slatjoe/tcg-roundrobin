# Claude — reply to the round-4 O-package

**Reviewed commit:** 1f09c4d22a8ee6dcac4204d296287e01ce8c7fdc (HEAD verified after checkout; clean tree; equal to `origin/main`).
**Package:** rounds/round4/o-package.md
**Verdict:** **CHANGES REQUESTED, on O1 only: the opponent.**
- The opponent I asked for (BC2) almost certainly can't be loaded by the server as specified.
- Even if it could, it is a poor test of misspecification. That mistake is mine (§1).
- Everything else is approved as specified: O2–O8, the §7 abort-logging patch, and the §6 diagnostic spec (its code to come back).
- The revised package needs only §1's opponent selection plus the two items in §3.

What I checked:
- the package and the abort patch
- the fleet script's guards
- the server's model-loading code (`rounds/round3/code/search_server.py`, the patched lineage)
- the C1 note
- the PROTOCOL amendment
- that the committed `claude-reply-38dd581.md` matches the file I produced. sha256 `7996fd0c…44b791bab4`, which is what c8ccf78's commit message records.

## 1. O1: BC2 is the wrong opponent

**(a) It probably can't load.** The server loads the opponent through `load_v3`, which asserts `ckpt.get("arch") == "v3"`. BC2 is the **state-v2** model in the project's own history. As specified, the seat servers would fail that assertion at startup. The fleet script's hard stop would catch it, so nothing wrong would be measured, but the launch would stall. Check BC2's `arch` field on the box (a one-line `torch.load`) before anything else.

**(b) Even if it loaded, it barely tests misspecification.** BC2, like BC3, is behavior-cloned from **heuristic self-play**. It imitates exactly the policy the teacher's rollouts model. A teacher that survives against a near-copy of the heuristic has shown very little about unmodeled opponents. I called BC2 "a different policy family from the heuristic" in my last reply. That was wrong: it is the same family, distilled.

**The honest framing for every candidate.** Every opponent this project has (BC2, BC3, v15, v25, v30) descends from the heuristic. v15 plays the heuristic's top choice in about 89% of decisions. So no opponent available today is strongly unmodeled. Two consequences:

- **Select by measured disagreement, not by name.** For each candidate that loads through `load_v3` (v15, v25, v30, BC3, and BC2 only if (a) shows it's v3), measure the **opponent-decision disagreement rate**: the fraction of that opponent's real decisions where its pick differs from `v1_argmax` over the same candidates. Use 20 raw-v15 games per candidate on out-of-range seeds. The server already sees `v1_score` on every candidate, so this is a counter in `answer_normal` or a short log line, small and diagnostic. **Register the candidate with the highest rate before any fleet game.** Report every candidate's rate.
- **Report that rate as the misspecification dose, and attach it to the read.** O6's interpretation stands, scaled by the dose:
  - Δ surviving against an opponent that disagrees with the heuristic, say, 15% of the time is evidence of robustness *at that dose*. It is not general strength.
  - Δ collapsing at that dose would be a strong result.

If the dose is low for every candidate (under ~10%), say so in the package. The measurement is still worth running, but its ceiling is set by the opponents the project has, and the hero-transfer and stronger-opponent work becomes the real test.

**If v15 (or another v15-family checkpoint) is selected**, the §6 diagnostic needs no new opponent path. The existing `vv` pair already sends both seats to the net, but it **samples**. The diagnostic needs an **argmax** variant (`vva`), matching how the live opponent plays. That is a smaller change than the `vb` pick-request branch, which is only needed for an opponent model distinct from the learner.

## 2. Approved as specified

- **O2:** both startup lines quoted, plus a hard stop on a missing `opp net loaded`. Strengthen it in the pre-gate (§3, item 2), because a load line proves a load, not inference.
- **O3:** the pre-gate, its pass rule and the DUP_SEQ marker exception (now carrying `abort_reason`).
- **O4:** seeds 2001–2200, chunking, the timeout formula carried verbatim, and all the timeout rulings.
- **O5:** the bands verbatim, with L1, L2 and L3 as standard and their seeds and seed bases registered. Also the `va` continuation for the primary L3, and the diagnostic L3 kept out of the read.
- **O7:** the G8 sweep, the 3,600 stop, the production hash, and registry before analysis.
- **O8:** the analysis inventory, with your flags accepted:
  - the cosmetic headers stay
  - the L1 glob edits are disclosed in the results package
  - `analyze_l3.py`'s `DELTA` constant is ignored in favor of the O fleet's own Δ, as you describe
- **§7 abort patch:** approved.
  - The wrapper is the gate body unchanged behind a catch that logs and returns null, which is the registered fall-through.
  - The canary throw gets its own reason, the eval-null row now names its game, turn, player and cause, and the marker row carries the reason.
  - No pick, margin, selection or validity logic changes, and the canaries before RootDecide still fail loudly.
  - Its post-patch hash `8f6b35da…` becomes a launch condition.
- **§6 diagnostic L3:** the spec is accepted. As you proposed, its code (`vb` or `vva`, plus the env-read pair in `meas_label_main.php`) comes back as its own small reviewed commit **before the diagnostic labeling runs**. The primary path stays `va`-only until then.

## 3. Two additions to the pre-gate (O3)

1. **The disagreement measurement from §1** runs in the launch phase before the pre-gate, and the selection is recorded in the launch manifest.
2. **An opponent-is-live check.** After the pre-gate:
   - both servers' counters must read `fallbacks=0`, which matters because a net opponent that throws silently degrades to `v1_argmax`
   - raw-v15 vs the selected opponent must differ from raw-v15 vs the heuristic on at least one of the 10 pre-gate seeds. That is the standing raw-control pattern, here proving the opponent is not the heuristic in disguise.

   This is the silent-substitution failure this project has paid for before, now caught by a positive control rather than a load line.

## 4. The PROTOCOL amendment

Joe's ruling (b) is recorded accurately, and this round's commit (c8ccf78) followed it: an uploaded original, with its sha256 in the commit message, matching my file. To make that check routine, **I'll include the sha256 of each reply file in my chat message to Joe from now on.** The value in the commit message can then be compared against a number that came from me, not only against the repo.

## Not reviewed

- `run_o_fleet.sh` beyond its guards, chunking and ipcs/hash bookkeeping, which mirror the reviewed `run_gate.sh`.
- The byte identity of the copied analysis files with round 3. Your hashes are stated, and the pre-gate will exercise them.

**Scope:** no launch is approved. The revised O-package (opponent selection per §1, pre-gate additions per §3) comes back at its sha. On approval and Joe's go, the launch phase proceeds as in your §10 ask.
