# Claude — review of the round-10 combined Step 2 + 3 paired-fleet package

**Reviewed commit:** 5b5ada42996f785230e2fbf96c2830240a03e8c1 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-26cc773.md` hashes to `5776943a…46ec1fdc`, the value I gave Joe. The doc is `3832be2d…`. The package adds files only.

**Verdict: APPROVED.** The fleet launches on Joe's go, with launched sha == 5b5ada42 (or differing only under `rounds/`). Nothing blocking was found. Two non-blocking notes follow.

## Checks

**The build and the reuse.**
- Every reused file in `code/step2/` is byte-identical to its `code/step1/` counterpart: `search_s3_thr.php` `4a1936fe…` (the pre-gated build), `search_s3`, `search_s2` (the §14 label engine), both mains with the loud loaders, the driver, `analyze_l3`, `stage0_report`, `g8_sweep2`, `shm_sweep` and `merge_registry`.
- The pre-gate coverage is mechanical: the runner refuses unless pilot attempt 2's manifest reads IDENTICAL under this build hash and tuple. The tuple-string serialization is matched, and the parity fixture runs the runner's own gate code against the real published manifest.

**The design matches my §3.**
- Paired teacher vs raw v10, same seed and seat, 61 seeds × both seats = 122 pairs, fresh block 26001–26061, proven against the completed record.
- **The raw phase runs only after the teacher phase completes**, never concurrent, with one rerun per raw timeout.
- Timeout 8,031 s = ⌈3 × 2,676.8⌉, both arms.
- **Bands:** round 9's exact form, including both INCONCLUSIVE lines.
- **Life-differential:** imported from the single fixed `life_score` (the draw flag plays no part).
- **The Step 2 co-read:** off the teacher arm (122 ≥ 72 games), two-sample bar against +0.0649 (SE 0.0090), with the §4 ratio guard and the pilot never pooled.

**Sizing, verified.** (1.96 + 0.8416)² × 0.30116 / 0.14² = **120.6 → 121 → 122 pairs**.
- The two-sided z is **the correct convention**, not merely the conservative one: the band is "the 95% CI's lower bound > 0", a one-sided 2.5% test.
- q = 0.324 is the right input (97/299 discordant among non-identical pairs). The published 0.2425 is 97/400, all pairs, as the doc says.

**The anchor, run myself.** `fleet_read.py --primary-only` on round 9's published Stage 3 pairing and games report (with the stat files laid out as the reconciliation expects) prints:
- **+0.0475 [0.0000, 0.0950]** and **DOES NOT CONVERT**;
- 37,092 stat rows reconciled, 8 canary records, Δ05 +0.0300, life +0.0200.
- That's exact on the primary, even under the fleet's rng seed.

**The label family** at 1,100,055,001 + shard × 10⁸ is clear of every family, the pilot's at its cap included. Catching the 800,055,001 collision with the pilot's shard-1 base is the enumeration doing its job.

**The box pins** carry full hashes (`8f6b35da…`, `b8b41390…`, `44f1e5d7…`, `81ef2cdb…`), matching the deployed record.

**Fixtures, run here** on a scratch copy: **the fleet suite has 122 checks, ALL PASS, twice, byte-identical between runs.** It matches the committed transcript apart from five absolute paths in the `bash -n` lines.

## Non-blocking

1. **Commit the anchor as a fixture.** The Stage 3 reproduction is cited in the doc but isn't in the suite. It reads only published data, so it qualifies. Map round 9's flat `search_stats_<blk>.jsonl` to the `games_<blk>_log/` layout in a temp dir, as I did, and assert the primary line and the verdict.
2. **Strip absolute paths** from the five `bash -n` PASS lines, so the transcript reproduces byte-identically on any host.

## Launch conditions

1. **Joe's go.** The launch record states the launched sha, the deployed hashes and the gate's result against the attempt-2 manifest.
2. **Run order as registered:** gate check → teacher phase (4 blocks) → raw phase → raw reruns → registry merge → games report and primary read → `run_fleet_l3.sh` (jobs, labels, full read with the co-read).
3. **Status-only interim notices.**
4. **Publication of `data/step2/`** with a MANIFEST and the declared gzip label storage, so the primary, the co-read and the attribution all recompute from the repo.

**Scope:** this approves the combined Step 2 + 3 paired fleet at sha 5b5ada42996f785230e2fbf96c2830240a03e8c1 (122 pairs, the primary paired Δ against the registered bands, and the Step 2 co-read with attribution) on Joe's go. Approval certifies the build as written, not the run as executed.
