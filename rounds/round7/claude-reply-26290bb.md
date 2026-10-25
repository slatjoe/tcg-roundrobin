# Claude — independent recomputation; round 7 closed

**Reviewed commit:** 26290bb294846343872258e35bc2cc0c97184c59 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-9fb0e98.md` hashes to `fd7af492…1e99a1232c`, the value I gave Joe.
**Package:** `rounds/round7/fleet-records.md` and `rounds/round7/data/`.

**Verdict: every figure recomputes exactly from the published files. The ruling stands, and round 7 is closed.**

## 1. The files

I hashed all 26 published data files here. For the 8 gzipped stat files, I hashed the decompressed content. **Every hash matches** the fleet report's §11 (16 row files and 8 stat files) or the pre-gate report (the 2 ghost stat files).

## 2. The recomputation

I wrote my own scorer from the registered rules; I didn't use the builder's scripts. The rules:
- unit = (seed, seat)
- a teacher timeout scores 0, a raw timeout 0.5
- an engine-capped game or a draw scores 0.5
- otherwise a win or loss by seat
- the bootstrap is clustered by seed, B = 10,000

| Quantity | Report | Recomputed here |
|---|---|---|
| Units / duplicate keys / invalid rows | 400 / – / 7 teacher timeouts | 400 / 0 / 7 teacher timeouts, 0 raw |
| Teacher W–D–L | 173–86–141 | 173–86–141 |
| Raw W–D–L | 163–100–137 | 163–100–137 |
| Points, teacher − raw | 216.0 − 213.0 | 216.0 − 213.0 |
| **Primary Δ** | **+0.0075** | **+0.0075** (Σd² 18.0) |
| Bootstrap CI | [−0.0138, +0.0288] | [−0.0138, +0.0288] (my RNG seed; same to 4 places) |
| Seat 1 / seat 2 | +0.0075 / +0.0075 | +0.0075 / +0.0075 |
| Discordant pairs | 19 / 17 | 19 / 17 |
| Chunks c1–c4 | +0.030 / +0.005 / +0.010 / −0.015 | same |
| Teacher timeouts | 7/400 = 1.75% | 7/400 = 1.75% |
| Drop-sensitivity Δ | +0.0165 | +0.01654 (n = 393) |
| Non-win co-report | +0.0250 [+0.0025, +0.0500] | +0.0250 [+0.0025, +0.0500] |
| Stat rows / teacher / contested | 37,133 / 37,120 / 9,429 | same |
| Thin-prior | 2,988 = 31.7% | 2,988 = 31.69%; no other contested fallback |
| Overturns (flag; pick ≠ prior) | 118; 118 | 118; 118 |
| Non-thin overturn rate | 1.83% | 1.83% |
| **Stop (a)**: overturns with mean_diff ≤ 1.5 × se_diff | 0 | **0** |
| se_diff = 0 rows | mean_diff 2, 2 | (se 0, mean 2) × 2 |
| **K6 line** (pre-gate ghost files) | `496 133 0 0` | **`496 133 0 0`** |

That closes the independence gap from the builder-run checks. The primary, the timeout stop, the diagnostics, stop (a) and the pre-gate's K6 pass have all now been confirmed from primary data, outside the builder's session.

## 3. Records

- **Stop (a):** stated, not fired.
- **The planning lesson:** recorded (fleet-records §3).
- **Publication:** confirmed by Joe.
- **One housekeeping item:** the L3 jobs file is recorded at `/tmp/ggate/jobs_all.jsonl` (`5fe5c0d8…`). `/tmp` on the box is tmpfs. Copy it into `registry-vault/`, or commit it under `data/`, so it survives a reboot if a Gravy-search round ever wants it. Record its hash beside the copy. This doesn't affect the closure.

## Round 7: the record of result

- **The question:** does the Fai teacher pipeline, replicated faithfully, transfer to a second hero (Gravy Bones)?
- **The answer:** **no, as built.** The paired Δ is +0.0075 [−0.0138, +0.0288], read PROJECTION OVERSTATED, and the read is valid: no stop fired.
- **The reason in the record:** the teacher barely acted. 305 of 400 games were identical to raw, 31.7% of contested decisions never completed a search, and completed searches overturned at 1.83% against Fai's 12–16%. Search limits sized for Fai don't carry over to Gravy-length games.
- **Not answered:** whether search calibrated for Gravy would help. If that's ever pursued, the retained L3 jobs are its first measurement.

**Scope:** this reply confirms the round-7 records from published primary data and closes round 7. No launch is approved or pending.
