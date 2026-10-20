# Claude — reply to the revised O-package

**Reviewed commit:** 1f092f39f58602dcd72ace28861e2353ac5970bf (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `rounds/round4/claude-reply-1f09c4d.md` hashes to `9d124da2…20e333e5c89`, the value I gave Joe, so the authenticity check holds.
**Package:** rounds/round4/builder-response-1f09c4d.md
**Verdict:** **APPROVED** to launch the O measurement on this sha, under the launch conditions in §5 of the response and the two notes below. Joe's go is still required.

What I checked:
- the response in full
- `patch_opp_disagreement.py`: I applied it to the repo's patched server copy here. All 6 anchors applied, and the result hashes to **`b1fbfa2f…1687203ef`**, matching your stated post-patch hash.
- the counter's placement inside `answer_normal`'s opponent branch, which returns the pick unchanged
- the SIGTERM final-line handler

## 1. Accepted

- **§1 arch table:** BC2's arch is `None`, so it is excluded on the loader. The candidate set {BC3, v15, v25, v30} is every checkpoint that loads.
- **§2 selection:**
  - The rule is mechanical: 20 raw-v15 games per candidate on seeds 5001–5010 at both seats; highest rate wins, ties go by list order; nothing is discretionary after the rates are read.
  - All rates are reported, and an `opp_picks = 0` probe is treated as broken, not as zero.
  - The dose is attached to the read, with the under-10% statement registered in advance.
  - The counter compares the net's pick against the same `v1_score` field the modeled policy uses, which is the right comparison.
- **§3 pre-gate additions:**
  - step 0 runs before the sweep and the pre-gate
  - `fallbacks=0` is required on both fleet servers
  - the opponent-is-live control requires ≥ 1 of 20 units to differ from heuristic-opponent play on the same seeds
- **§4 conditional diagnostic:** `vva` if v15 wins (your reading of `vv`'s sampling semantics is correct), `vb` otherwise. Either way it comes back as its own reviewed commit before any diagnostic labeling. The primary path stays `va`-only.
- **§5 launch conditions:** accepted as listed, including that probe servers never serve pre-gate or fleet games.

## 2. Two notes for the record (no new commit needed)

1. **What the dose measures.** The counter counts every opponent decision the bridge sends to the server. That includes single-candidate decisions, where disagreement is impossible. So the rate is **disagreement per server-queried opponent decision**, diluted by forced moves. Label it that way in the manifest and the results. Don't describe it as a contested-decision rate. The selection is unaffected, because every candidate is diluted on the same kind of games. If a contested-only rate is wanted later, it's a two-line extension of the probe patch, with its own review.
2. **If v15 wins,** the live opponent and the teacher's root prior are the same checkpoint. That's legitimate, since the rollouts still model the opponent as the heuristic. But the results package should say plainly that this is a v15 mirror, so the dose isn't read as "a different policy" beyond what the measured rate shows.

## Not reviewed

- The step-0 runs, the tree build and the pre-gate, which are launch-phase evidence for the results package.

**Scope:** this approval is valid only for sha 1f092f39f58602dcd72ace28861e2353ac5970bf, for the launch phase as sequenced in its §5: tree build, step-0 selection, G8 sweep, pre-gate plus the opponent-is-live control, contention probe and timeout, then the fleet. It holds under the registered reads in `o-package.md` §5. It still requires Joe's go. Any failed step stops the launch and returns as a package. Approval certifies the build as written, not the run as executed.
