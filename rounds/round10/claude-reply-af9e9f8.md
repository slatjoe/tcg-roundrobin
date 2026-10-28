# Claude — confirmation check on the Step 0 probe fix pass

**Reviewed commit:** af9e9f877a32d21a528afefafdbdfe3c91defdba (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-402c92f.md` hashes to `a399e674…f22f77878`, the value I gave Joe. Exactly the 8 named files changed against cfe2d8a, and the doc is `ba18c34d…`.

**Verdict: NOT YET. Two small items remain.** One is a semantic error in the informational power print I asked for (§2.1). The other is a pin gap that was already in 402c92f and that I missed (§2.2). The §2.1 weighting, the §2.2 calibration print and the F2 class are all done correctly (§1).

## 1. Confirmed

- **The weighting.** `per_game_gain(recs, weight)` multiplies each uncontested diff by `capture.uncontested_every` inside the per-game sum, and the bootstrap runs over the weighted totals. Contested jobs keep weight 1, and the weight prints on the CLASS line. Fixtures W1–W4 show the gain and CI at exactly 2× and the contested side unchanged.
- **The calibration print.** It sits beside 0.0917, 0.069 and 0.065. Outside [0.04, 0.13] the flag line prints above the recommendation (P1 and P4).
- **The F2 class.** `uncontested_diag` covers (1.0, 1.5]. It's labeled and read for edge only, with no per-game gain entry, so it can't enter the threshold gain or the decision rule. The boundary fixtures are at 1.0, 1.2, 1.5 and 1.51.
- **Seeds:** re-proven at the enlarged plan, under the 256-job per-shard cap.
- **Fixtures, run here** on a scratch copy: **57 checks, ALL PASS**, with the PASS lines identical to the re-staged transcript.

## 2. Required

### 2.1 The Step 2 power print compares an increment to a total

`probe_report.outlook()` computes z = (g.gain − 0.0649) / √(SE² + 0.009²), where `g.gain` is the **lever's increment**: the per-game gain of the *added* fires (the contested band, or the uncontested class). The Step 2 bar compares the new build's **total** gain against Stage 3's 0.0649. So an increment of +0.03 enters as 0.03 − 0.0649 < 0, and the print would show near-zero power for any realistic lever. P2 matches an independent Φ evaluation of the same formula, so it can't catch this.

**Required:**
- **The formula:** z = inc / √(SE_new² + 0.009²). Here SE_new = √(0.009² + se_inc,400²) is the new build's total-gain SE at 400 games: Stage 3's base SE plus the increment's SE, scaled from the probe by √(90/400). Power = Φ(z − 1.645).
- **Fixture, by hand:**
  - inc = 0 gives power ≈ 0.05, the bar's own α.
  - inc = 0.03 with se_inc,400 = 0.005 gives SE_new = 0.01030, z = 0.03/0.01367 = 2.194 and **power = Φ(0.549) ≈ 0.708**.
- State the approximation on the print line: the build's base gain is taken as Stage 3's.

### 2.2 The runner must hash-assert every deployed file

`run_probe.sh`'s header says "expect_hash on every deployed file". In fact it asserts six (`search_s3`, `s1_eval_main`, `s2_label_main`, the driver, `merge_registry` and `search_s2`). The other ten files it deploys are only *recorded* in `deployed_code_hashes.txt`. That includes `settings_probe.json`, which carries the decision rule, and the five probe job and analysis scripts.

The round-9 runners asserted their analyzers and settings. This gap was in 402c92f and I didn't catch it.

**Required:**
- `expect_hash` with machine-copied literals for all of: `build_probe_eval_jobs.py`, `probe_eval_analyze.py`, `build_probe_jobs.py`, `probe_label_analyze.py`, `probe_report.py`, `settings_probe.json`, `stage0_report.py`, `analyze_l3.py`, `g8_sweep2.sh` and `shm_sweep.py`.
- **Extend `fx_pin_guards.py`:** every file in the runner's deploy list must have an `expect_hash` site whose literal equals the staged sha256. So a file can't be added to the deploy list unpinned again.

## 3. Then

Both items are mechanical. They come back in one commit for a confirmation check, after which the probe runs on Joe's go with launched sha == approved sha. Nothing else needs to change.

**Scope:** this confirms §2.1 (weighting), §2.2 (calibration) and the F2 class at af9e9f87, and requests the two items above. No run is approved yet.
