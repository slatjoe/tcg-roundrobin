# Claude — confirmation check on the Stage 1 fix pass

**Reviewed commit:** 86de3be13f42f48344abc332f2f0e8a15d10e8a1 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-edddf5e.md` hashes to `39a149fa…5c5f323`, the value I gave Joe.

**Hashes:**
- `stage1_analyze.py`: **`38467613…d319e381`**
- `run_stage1.sh`: **`c138a313…19b74b284`**
- The other 16 code files are unchanged.

**Verdict: CONFIRMED. Stage 1 may launch on Joe's go, with launched sha == 86de3be1** (or differing only under `rounds/`, in notes).

## Checks

**§1, completion per state:** a state completes iff `all(len(finished) ≥ floor for every selected candidate)`, and completion is completing states over panel states. The candidate-level rate and the pooled share are reported as diagnostics only. **Scenario D** is the registered trap: candidate-level 0.95 against per-state 0.90 **does not qualify**, and its 0.95 twin is selected.

**§2, the control is excluded:** the role is `control` iff the horizon is 0. The control is reported in full and filtered out of the qualifier list before the sort. **Scenario E:** a B0 that qualifies at 1.0 and is 9× cheaper is skipped, and the selection takes the +H setting.

**§4.4, the B0 gate:** after B0's pass, the runner runs the analyzer over a B0-only settings file and **stops before the +H settings on any non-zero exit**. A B0 eval abort already exits inside the iteration. `fx_b0_gate.sh` extracts the block verbatim from the runner and runs it against intact and corrupted outputs, including the no-op cases.

**The fixtures, run here:**
- `fx_stage1_analyze.py`: **ALL PASS**, including D and E
- `fx_b0_gate.sh`: **ALL PASS**
- the full 66-check transcript is accepted from the record

**The pin audit (standing):** `run_stage1.sh` carries 17 literals, all 64 hex characters. The analyzer pin moved to `38467613…`, matching the file.

**§5, hygiene:** no `.pyc` is tracked at HEAD, and the root `.gitignore` covers `__pycache__/` and `*.pyc`.

**Accepted code byte-identical:** `decide()` and `valued()` are unchanged, and only the two named files changed among the 18.

## Carried forward to Stage 2's package (not Stage 1 conditions)

- **The live decision path** (`SimTeacher_DecideInner` and its children's hook guards) gets the same env-read, run-pinned parameters: hooks, deadline, horizon, horizon value. That includes the shared hook guards, which currently read the label-path global with a default of 4000.
- **The ghost pre-gate** on that build before any live game.
- **Both players' life totals** recorded on every world that ends at the turn-62 horizon, so a life-differential price can be co-reported beside the registered −1. Per the rules reference (ba17c3c5), as I read it: −1 is the **exact** Swiss price, and life total is the elimination-round resolution.

**Scope:** this confirmation approves Stage 1 at sha 86de3be13f42f48344abc332f2f0e8a15d10e8a1 (capture, panel, B0-first evaluation with the B0 gate, the five +H settings, analysis and selection), on Joe's go. Approval certifies the build as written, not the run as executed.
