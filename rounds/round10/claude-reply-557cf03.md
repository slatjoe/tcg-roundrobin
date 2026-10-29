# Claude — confirmation check on the Step 1 pilot package, fix pass 1

**Reviewed commit:** 557cf033d8c8907d8cd438b423413a95b6e8b486 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-acc55a1.md` hashes to `372f0d6a…a7192d7`, the value I gave Joe. The doc is `54e9322d…` and the settings file is `0571e03a…`.

**Verdict: CONFIRMED. The pre-gate may run on Joe's go, and the pilot only after the pre-gate reads IDENTICAL**, with launched sha == 557cf033 (or differing only under `rounds/`).

## Checks

**§2.1, the seeds: closed.**
- `USED_GAME_BLOCKS` now carries round 9's full D2 list, including the contention probe 8601–8604, plus every block used since, with sources in the docstring.
- The pre-gate moved to **13001–13010** at every site: both `--seeds` lines, the header and the settings. A repo-wide search finds no prior use; the only hits are substrings of 23001-series seeds in Stage 3's pairing file.
- The runner pins are machine-refilled.

**§2.2, the one-sided bounds: closed.**
- One replicate set (B = 10,000, seed 20261020), cross-checked in code against `cluster_bootstrap`'s 2.5th and 97.5th percentiles.
- The 5th percentile feeds Δ_plan and the 95th feeds STOP, with the two-sided CI printed and the basis named.
- **Plant T:** the 95th percentile is 0.0784 and the 97.5th is 0.0896. STOP fires on the one-sided bound, where the old form wouldn't have.

**§2.3, portability and determinism: closed.**
- php is resolved through `find_php`, with a one-line failure message.
- Printed sets are sorted.
- The env fixture's records are written per invocation, and atomically. That's a real fix: interleaved appends from the block's parallel invocations were the source of the intermittent failures, and it's the right call to fold it in.

**Fixtures, run here** on a scratch copy:
- **pilot suite: 134 checks, ALL PASS, twice.** The two runs are byte-identical to each other and to the committed transcript.
- **round-10 suite: 197 checks, ALL PASS.**

**Non-blocking:** list the registered Stage 1 extension range **21041–21100** in `USED_GAME_BLOCKS` beside 21001–21040, as the probe's settings did. It was registered as a contingency block, so it stays out of reuse. It doesn't touch 13001–13010 or 25001–25050.

## Launch conditions

1. **Joe's go**, with the launched sha stated in a launch record.
2. **The pre-gate first** (`run_pilot_pregate.sh`, 13001–13010 × both seats, both builds), with its manifest recording the verdict, the build hash and the tuple. **The pilot runner refuses to start without IDENTICAL**, mechanically.
3. **The pilot** runs as registered: 100 games, 25001–25050 × both seats, timeout 7,845 s, every overturn captured, then labels at 700,055,001 + shard × 10⁸, then the read. The STOP rule and the Step 2 sizing print exactly as registered. Interim notices are status-only, never figures.
4. **Publication** of `data/step1/` with a MANIFEST, so every figure in the read recomputes from the repo.

**Scope:** this confirms fix pass 1 and approves the Step 1 pre-gate and, behind its IDENTICAL verdict, the 100-game pilot and its read at sha 557cf033d8c8907d8cd438b423413a95b6e8b486, on Joe's go. Approval certifies the build as written, not the run as executed.
