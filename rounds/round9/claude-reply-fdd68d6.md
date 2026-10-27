# Claude — confirmation check on the Stage 3 fix pass

**Reviewed commit:** fdd68d64507f2a09ca5195e481f826f759553c1d (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-c924b19.md` hashes to `fecdf537…f01cbb0`, the value I gave Joe. Every changed file hashes to the values stated, and the package doc is `6a63a46a…`.

**Verdict: CONFIRMED. Stage 3 is approved to launch on Joe's go**, with launched sha == fdd68d64 (or differing only under `rounds/`).

## 1. Checks

**§2.1, the life score: closed.**
- `life_score` now credits a win, or a capped game with winner 0 where the arm's own life is strictly greater. The draw flag plays no part.
- `stage3_analyze.py` deletes its copy and imports the function. `stage3_games_report.py` keeps its `__main__` guard, so the import runs nothing.
- **Recomputed here:** I loaded the module and ran it over the published Stage 2 rows. **25 of 41 capped games score 1, and life-wins total 112**, matching my registration.
- The fixtures assert the same counts on the real rows and the shared function object. The planted capped rows are re-planted in the driver's real shape.

**§2.2, the excluded-pairs limit: closed.** INCONCLUSIVE now also fires on (excluded + dropped) / attempted > 0.02, taken from the pairing statuses. The count and rate print on the "PAIRS OUT" line. Case E shows 9 pairs → INCONCLUSIVE and 8 → CONVERTS.

**§2.3, G8 names its match: closed.**
- On a trip, `pgrep -af` output for both patterns goes to `${PREFIX}_abort.txt` and to stderr before exit.
- The fixture finds the planted command line verbatim in both.
- The diff against `g8_sweep.sh` is confined to the header and the guard block.

**§2.4, the label base: closed.**
- `LABEL_BASE=50055001` appears in the runner, the settings and the round-trip fixture, which runs the real driver at that seed.
- The clearance is restated as range-disjoint, with span arithmetic that matches mine: about 35.7 M above Stage 2's same-shard top.
- No "100,000,000" clearance claim survives outside my reply.

**The two smaller items:**
- **§4, the ratio guard: done.** It prints `n/a (Δ ≤ 0)` or `unstable (Δ CI includes 0)` with Δ's CI beside it, one fixture per branch.
- **F-S3-4: done.** A duplicate rerun row aborts with exit 2.

**Fixtures, run here** on a scratch copy: the **Stage 3 suite has 6 suites and 100 checks, ALL PASS**, with the PASS lines identical to `fx_s3_outputs.txt` (`af55ed1b…`). The **Stage 2 suite's 124 checks still pass.**

**Pin audit:**
- The two runners carry 35 literals, all 64 hex characters, with 21 unique values.
- 17 match files at HEAD. The other four are the registered fleet-tree, checkpoint and deck values.
- None of the five superseded literals remains.

**Hygiene:** I left no cache in the clone.

## 2. One note (not a condition)

The fix-pass message calls the doc change "a dated amendment section". The diff also rewrites original sections in place: §4.3, §4.5, §4.6, §2, §4, §6 and the §7–§8 tables. The corrected text is right, and the reviewed original is preserved at c924b19 and quoted in my review, so nothing is lost. But the stated convention is original sections unrewritten, and the commit message should describe what the diff does. Next time, either keep the convention or say "amended in place."

## 3. Launch conditions

1. **Joe's go**, with launched sha == fdd68d64, or differing only under `rounds/`. The launch record states the sha and the deployed hashes.
2. **Run order:** `run_stage3_games.sh` (pins → PREGATE-GATE against Stage 2's manifest → free-space → G8 → teacher phase → raw phase → RAW-RERUN → registry merge → games report → read), then `run_stage3_l3.sh`. The Stage 2 pre-gate manifest must still be at `${STAGE2_OUT}/pregate/`, and the gate enforces it.
3. **The standing rules:** status-only interim notices, never figures; registry merges before analysis; publication of `data/stage3/` with the report so every read can be recomputed. A tracker (F-S3-3) is Joe's call; if built, "complete" keys on `stage3_read.json` and the L3 manifest.

**Scope:** this confirms the fix pass and approves Stage 3 at sha fdd68d64507f2a09ca5195e481f826f759553c1d (the 800-game paired fleet, the read against the registered bands, and the L3 attribution co-report) on Joe's go. Approval certifies the build as written, not the run as executed.
