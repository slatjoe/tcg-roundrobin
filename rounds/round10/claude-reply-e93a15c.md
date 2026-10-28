# Claude — confirmation check on the Step 0 probe's second fix pass

**Reviewed commit:** e93a15cded0ddd5909854ae02a08f6922e2e1b08 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-af9e9f8.md` hashes to `be8524be…15705cf23`, the value I gave Joe. Exactly the 7 named files changed against bbadc42, and the doc is `81961f20…`.

**Verdict: CONFIRMED. The Step 0 probe is approved to run on Joe's go**, with launched sha == e93a15cd (or differing only under `rounds/`).

## 1. Checks

**Item 1, the power print: closed.**
- `outlook()` now uses the increment against the build's total-gain SE: SE_new = √(0.009² + se_inc,400²), with se_inc scaled by √(90/400), z = inc / √(SE_new² + 0.009²) and power = Φ(z − 1.645).
- The print line states the approximation that the build's base gain is Stage 3's.
- **Run through the full report path:**
  - P2a: inc = 0 gives power **0.04998**, the bar's own α.
  - P2b: inc = 0.03 with se_inc,400 = 0.005 gives SE_new 0.010296, z 2.1938 and power **0.7084**. That matches my hand values, 2.194 and 0.708.
- The settings note records the corrected form.

**Item 2, the pins: closed.**
- `run_probe.sh` now hash-asserts all 16 deployed files. I checked every staged file's sha256 against the runner: **16 of 16 present**.
- The runner has 19 hex literals in all (16 header pins plus 3 tree-install pins), every one 64 characters.
- `fx_pin_guards.py` takes the deploy list from the runner's own recording loop and requires a matching pin for each file. Its negative copy, with the `probe_report.py` pin stripped, fails on exactly that file.

**Fixtures, run here** on a scratch copy: **86 checks, ALL PASS**, with the PASS lines identical to the re-staged transcript.

**Hygiene:** no cache was left in the clone.

## 2. Launch conditions

1. **Joe's go**, with launched sha == e93a15cd, or differing only under `rounds/`. The launch record states the deployed hashes. The runner now refuses any mismatch on all 16 files.
2. **Phase order as registered:** capture → eval → jobs → labels → analyze → report. The jobs phase prints the realized class counts at 1.5, 1.25 and 1.0 and proceeds, per the F2 ruling. Under the extension rule, if class (a) realizes fewer than 5 jobs, the read is reported as uninformative or an extension block is ordered before labels.
3. **The standing rules:**
   - free-space and G8 pre-flights;
   - registry merge of the capture games (tag `r10_probe_capture`) before analysis;
   - status-only interim notices, never figures;
   - publication of `data/step0/` with the report, so every rate, edge and gain recomputes from the repo.
4. **The report's recommendation follows the registered decision rule.** The calibration flag, the power prints and the price prints are informational, and NO BUILD is an allowed outcome. Any Step 1 build is a new package and review.

**Scope:** this confirms the second fix pass and approves the Step 0 probe at sha e93a15cded0ddd5909854ae02a08f6922e2e1b08 (90 capture games, the offline k = 25 eval of every snapshot, the labels, the analysis and the report) on Joe's go. Approval certifies the build as written, not the run as executed.
