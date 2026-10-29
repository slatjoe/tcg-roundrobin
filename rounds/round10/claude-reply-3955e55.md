# Claude — review of the Step 1 pre-gate repair package

**Reviewed commit:** 3955e5548e23c78093b6dde11c01578056092d13 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch record at dcaf8368. The committed `claude-reply-557cf03.md` hashes to `545eadac…a623a7`, the value I gave Joe. The doc is `96e2c749…`. The build is untouched, and the pilot didn't launch, correctly.

**Verdict: CHANGES REQUESTED, two small items.** The diagnosis is right and I reproduced it independently (§1). The repaired checker is the right shape. But as written, it would pass a pre-gate in which most games timed out (§2.1). I'm also setting the tolerance (§2.2).

**On process, for the record:** the repaired checker's read-only IDENTICAL on attempt 1's data is a diagnostic, **not a gate result**. A checker revised after seeing a failure doesn't get to re-read that data as the verdict. **The gate is attempt 2**, run fresh under the checker as approved here. Attempt 1's NOT IDENTICAL stands as recorded.

## 1. The diagnosis: reproduced from the published rows by my own code

I paired arms by seed through the driver rows and decisions by sequence order within each seed's game pair:

| Seat | Completed seeds | Timeouts | Contested pairs | `selected` diffs | max \|Δprior\| | Newly contested | Off-shape | Length mismatches |
|---|---|---|---|---|---|---|---|---|
| 1 | 5 | 5 | 97 | 0 | 5.364e-07 | 309 | 0 | 0 |
| 2 | 7 | 3 | 122 | 0 | 7.153e-07 | 456 | 0 | 0 |

- **Every completed thr game is byte-identical by gamelog** to both its §14 ghost counterpart and the raw game.
- All three layers hold as diagnosed:
  - **A:** the failures were the 1,200 s driver default killing thr games;
  - **B:** pairing keyed on the arm-local instance id, so nothing was ever paired;
  - **C:** exact equality on GPU-served priors.
- The 85-against-97 count is the hand alignment's row filter; the checker and I agree on 97.
- **Fixtures, run here:**
  - **pilot suite: 140 checks, ALL PASS**, transcript identical;
  - **round-10 suite: 197 checks, ALL PASS.**
  - The saved v1 checker fails the planted real-shape population, as it should.

## 2. Required

### 2.1 A timeout can't pass the gate

The played-action leg judges identity "over the seeds both arms completed", and a timed-out seed is excluded from pairing. So an attempt in which, say, eight of ten seeds per seat timed out would read **IDENTICAL on the two that finished.**

That was a fair way to *diagnose* attempt 1. It isn't a gate. At 7,845 s, 6.8× the slowest completed thr game, a timeout is itself an anomaly.

**Required:**
- In attempt 2, **IDENTICAL requires all 10 seeds at both seats to complete in every arm.**
- Any timeout prints **`PREGATE: INCONCLUSIVE (timeout: …)`**, names the seeds and arms, and exits non-zero. So the pilot gate refuses, and the case returns to review.
- **Fixture:** one timeout row in an otherwise identical population gives INCONCLUSIVE, not IDENTICAL.

### 2.2 The priors tolerance: 1e-5, with the decision fields exact

The 1e-6 bound sits only about 1.4–1.9× above the observed maxima, so a fresh attempt could fail on float noise alone and send us round this loop again.

The principled scale is the server's float32 arithmetic: about 1.2e-7 relative per ULP, with observed differences of a few ULPs. **1e-5 (absolute, on probabilities)** is about 80 ULPs at 1.0. That's far above serving noise, and far below any difference that could move a candidate in or out of the selection.

**Required:**
- `PRIORS_TOL = 1e-5`, justified on that basis, not on attempt 1's maxima.
- On every contested pair, **`selected` exact** (as now) **and `prior_pick` exact.**
- Keep printing the observed maximum per seat.
- **Fixtures:** a pair at 5e-6 passes; a pair at 2e-5 is counted bad; a pair with equal priors but a different `prior_pick` is counted bad.

## 3. Accepted as built

- **Seed pairing** through the driver rows, and **sequence-order decision pairing.**
- **Off-shape combinations counted by name.**
- **Tails** split by arm and reason.
- **`--timeout 7845`** on both ghost arms, one timeout story across pre-gate and pilot, with the parity fixture asserting the literal.
- **The attempt mechanics:** attempt 1 untouched in its flat layout; attempt N in `pregate/attempt<N>/` under the single-shot guard; the pilot gate reading the latest attempt's manifest.

**Cost note (not a condition):** the thr ghost arm ran 15–30 minutes a game. The launch record for attempt 2 should re-price both the pre-gate and the pilot's teacher arm from attempt 1's completed walls, not the probe's 1,840 s.

**Scope:** §2.1 and §2.2, with their fixtures, come back in one commit for a confirmation check. Pre-gate attempt 2, then the pilot behind an IDENTICAL verdict, run on Joe's go after that. No run is approved yet.
