# Claude — reply to the run_gate.sh fix

**Reviewed commit:** a148a6d523ddae0697ec6f81cc6de22bf8cdf0ee (HEAD verified after checkout; clean tree; equal to `origin/main`).
- It is a doc-only follow-up to the fix commit 3f713e51c81e4fcb1d0c22782007552114df37d1: its diff from 3f713e5 is one line of `builder-response-8d13b0f.md`.
- The chain is 8d13b0f → f64eba7 (Joe's upload of my reply) → 3f713e5 → a148a6d.
- The only code change since the approved 8d13b0f is `run_gate.sh`.

**Package:** rounds/round3/builder-response-8d13b0f.md
**Verdict:** the fix is **APPROVED**, and the gate launch is **APPROVED on a148a6d**. Launch with **`GATE_TIMEOUT=1600`, not 886** (§2), and with one added operator stop (§3). Joe's go is still required.

---

## 1. The fix: accepted, and I missed the defect

The diagnosis is right. A bare `wait` also waits on the two background server processes, which never exit. The script would therefore have hung after the last chunk, and the after-fleet production hash and the `ipcs` rollup are launch evidence that would never have been written.

The fix is minimal and correct:
- wait on the four chunk pids only
- reap the servers explicitly before the closing bookkeeping
- keep the EXIT trap as a backstop

`bash -n` is clean. The structural test is the right evidence: out-of-range seeds 3007–3014, all four chunks at once, a self-terminating script with `GATE-FLEET-DONE`, before and after production hashes equal, zero servers left, and 16/16 manifests `assert_ok`.

I approved 8d13b0f with this bug in it, and the probe found it, not my review. My review should have caught it.

## 2. Timeout: 1600 s, from the measurement that actually matches the fleet

Condition 3 was meant to set the timeout under fleet contention. The probe (seeds 3003–3006, slowest 295.3 s) was meant to represent that. Your structural test then ran the **actual fleet script** with all four chunks concurrent, and its slowest teacher game took **518.6 s**. That is the better fleet-conditions measurement, and it shows the probe understated contention.

Applying condition 3's formula to it gives max(700, 3 × 518.6) = 1555.8, rounded up to the next 100: **1600 s**. (886 also skipped the rounding the condition stated.)

**Why loosen it and not hold 886:**
- A timeout that's too tight turns load into teacher losses. Past 2% that makes the gate inconclusive, for reasons unrelated to the teacher.
- A loose timeout costs only wall time on a game that is genuinely hung, and raw games finish in seconds either way.
- No gate seed has been played, so this is still a pre-data registration.

**Launch command:** `GATE_TIMEOUT=1600 bash run_gate.sh`. The header comment's "886" is now stale. It changes no behavior, so don't change the file. Record 1600 and this reasoning in the launch manifest.

## 3. Shared memory: the "+1 per game" figure doesn't hold; add an operator stop

The structural test's `ipcs` went from 12 at the start to **97 after 32 games**, about **2.7 residual segments per game**. Mid-run chunk readings reached 154. That is consistent with the rerun ledger (about +5 per teacher game, +1 per raw game), not with §3.2's +1 per completed teacher game.

Projected for the gate, from a near-zero base: roughly 400 × 5 + 400 × 1 ≈ 2,400. That's under `shmmni` = 4096, but not by a wide margin if the rate runs higher under longer contended games.

**Added operator stop, as a launch condition:** read `ipcs -m | wc -l` at least hourly during the fleet. **If it exceeds 3,600, stop the fleet** (kill the run script, which reaps its servers) and report. A stopped fleet is **inconclusive**, not partially readable. The reason is that what the engine does on a failed cache write is unknown, and a wrong outcome there would be silent.

Separately, after the run, count residual segments per game by arm, so the leak rate is measured rather than estimated.

## 4. Everything else stands

Everything else is unchanged from my 8d13b0f reply:
- launch conditions 1, 2, 4 and 5, with condition 3 now satisfied by §2
- the registered bands
- the standing stops: G3 defects; overturn rows failing their own logged margin; teacher timeouts above 2%; canary refusals above 2% per arm-seat; the calibration impeachment
- the reported monitors: overturn rate against the 12–16% null band; deadline-killed children per chunk, which matters more now that contended games take 500+ s against a 180 s per-candidate child deadline; raw-hang position

The seed-1002 probe game and the 3003–3014 test games are registered eval-only at the real merge.

## Not reviewed

- The box's `/tmp/gatetree_r4` build. Condition 1 covers it.

**Scope:** approval is valid only for sha a148a6d523ddae0697ec6f81cc6de22bf8cdf0ee, for `run_gate.sh` as committed, run with `GATE_TIMEOUT=1600`, under the conditions and reads above and in my 8d13b0f reply. It still requires Joe's go. Approval certifies the build as written, not the run as executed.
