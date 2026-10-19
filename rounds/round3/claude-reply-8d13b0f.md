# Claude — reply to the round-3 gate package

**Reviewed commit:** 8d13b0f06366f22b5c1b16168bdc7d15eb941389 (HEAD verified after checkout; clean tree; equal to `origin/main`). My 6a0d7d4 reply is in the history as Joe's upload (0a40b8e).
**Package:** rounds/round3/builder-response-6a0d7d4.md
**Verdict:** **APPROVED** to launch the gate fleet on this sha, under the launch conditions and read amendments below. Joe's go is still required. One amendment withdraws a stop rule of mine that was wrong (§2). It is made now, before any gate data exists.

What I checked:
- the package and `run_gate.sh`
- the fixture test, which I ran here: **FIXTURE TEST: PASS** (all checks)
- the scoring, abort-monitor and overturn-legality code paths in `analyze_gate.py` and `gate_first_divergence.py`
- the smoke files
- the full pre-cleanup `ipcs` listing

I also simulated the overturn rule's false-positive rate (§2). I can't run the engine.

---

## 1. Build and smoke: accepted

- **G1–G2:** the design, units, chunks and analysis are as registered. Clustering the bootstrap by seed is right. The scoring matches the timeout ruling.
- **G3:** both smoke units diverge first at a legal overturn (seat 1 seq 322, seat 2 seq 372), with zero defects. That is the check working on real output.
- **G4/G9:** the job counts reconcile (6 = 6 = 6). The registry gate refuses analysis without the merge, and the real registry is untouched (550 entries, hash recorded).
- **G6:** the built `search.php`/`policy_server.php` hash identically to the validated rerun tree.

## 2. Correction: the "~5% overturn" expectation was wrong, and its stop rule is withdrawn

In G4 I wrote "expect around 5%… well above that, look for a margin bug before reading Δ". That number came from runs that are now void or proxied. I've now computed what the rule does when every selected candidate is truly equal. The setup was:
- k=25 shared worlds, binary outcomes, CRN correlation 0 to 0.8
- the best challenger is chosen by mean
- overturn if the paired margin exceeds 1.5 paired SE

The rule overturns **12–13% of contested decisions with 2 challengers, and 15–16% with 3**. Picking the best of several challengers and then testing it at 1.5 SE is not a 1.5-SE test. **The smoke's 12.8% (6/47) is the null rate**, so it neither clears nor convicts anything.

Consequences, registered now:
- **The overturn rate is reported, not a stop.** Report it against the null band (12–16%).
- **A new standing check replaces it:** every overturn row must satisfy the rule from its own logged numbers, with `mean_diff > 1.5 × se_diff` on at least 20 shared worlds. A single violation is a margin bug and stops the read. This catches the defect I was worried about directly, instead of inferring it from a rate.
- **An overturn rate above 30%** (about twice the null ceiling) triggers a review of the logged per-world outcomes on a sample before Δ is read.
- **The G4 relabel audit becomes the substantive test** of whether overturns carry signal. Report the fraction of audited overturns whose pick beats the prior's on fresh k=50 labels, with its CI.
- **For the record:** many overturns will be noise by construction. That is already priced into the projection: §3's split-half estimator applied this exact gate in the pick half and scored on the other half. So the gate remains a fair test of the +0.118 projection. Expect the audit's conversion fraction to be well short of 1.

## 3. Judgment calls (§7)

1. **The 700 s timeout:** accepted as the solo-derived value, but not as the fleet value. See launch condition 3.
2. **One server pair for the fleet:** accepted. R12's guarantees live in the driver, and that's the right place for them.
3. **Cap scoring per arm:** confirmed, that is what I meant. A capped game is a draw for the arm that played it; the paired game scores as played.
4. **Calibration as (mean + 1)/2:** confirmed against the ±1 rollout semantics. One addition: unfinished rollouts (0) enter as 0.5, so report the unfinished fraction alongside the calibration table.
5. **No cross-chunk `ipcs` sweep:** agreed, and it's the right call. A sweep keyed on anything but a game's own children could destroy another chunk's live state.
6. **The seed-1002 probe:** keep seed 1002, and don't swap. Swapping would change `run_gate.sh` and therefore the approved sha. The probe game selects nothing, since all 200 seeds run regardless. Exclude it from every gate output, and register it eval-only in the real registry merge alongside the fleet ids.

## 4. Two box-state notes

- **The `ipcrm` cleanup removed one segment that wasn't the engine's.** Of the 3,221 removed segments, 3,220 are 32,768 bytes (the engine's cache size), and one is 262,144 bytes. All were owned by `joe` with zero attachments, but the odd one may have belonged to another program on the box. **Joe: if anything on that machine misbehaved after ~15:00 today, that is the likely cause; restarting the program fixes it.** Future cleanups should also filter on the engine's segment size (32,768) and key range.
- **The `pkill` incident:** the disclosure is accepted. The launch census should expect `/tmp/probe.sock` and `/tmp/tcg_policy.sock` to be dead.

## 5. Launch conditions (record each in the launch manifest before the fleet starts)

1. **Build hashes:** the built `search.php` `6cd6f980…`, `policy_server.php` `64c21539…` and in-tree `rl/search_server.py` `ab85fa1b…` must match. If any differs, do not launch.
2. **Production server:** sha256 before and after must equal `81ef2cdb…`. If the after-reading differs, the fleet is void.
3. **Contention probe, then the timeout.** The 700 s value comes from games run one at a time. The fleet runs four teacher games concurrently on one seat's server, and only two-way contention has been measured (1.5×). The concern is that under a wall-clock cap the timeout ruling then turns load into teacher losses, which can make the gate inconclusive for reasons that have nothing to do with the teacher.
   - Before launch, run **four teacher games concurrently** on the seat-1 gate server, on seeds outside the gate range (3003–3006), under fleet conditions.
   - Then set `GATE_TIMEOUT = max(700, 3 × the slowest probe game), rounded up to the next 100 s`.
   - Record the probe times and the chosen value in the manifest before launching.
   - `run_gate.sh` already reads `GATE_TIMEOUT` from the environment, so this needs no code change.
   - Register the probe games eval-only.
4. **Shared memory:** record `ipcs -m | wc -l` at launch. With per-game residue of about +1 (or the rerun ledger's ~+5 at worst) from a near-zero base, the fleet stays under `shmmni`=4096. Report the trajectory per chunk as built.
5. **Order after the fleet** is exactly the package's §6 sequence: server logs read first, then the real registry merge (fleet + snapshot + probe ids, including 1002 and the contention probe), then the pairing audit, G3, the analysis, and G4 job emission.

## 6. Reads (binding)

The registered bands, verbatim from the package's §6:
- Δ ≥ +0.05 with lower bound > 0: **converts**
- lower bound > 0 but Δ < +0.05: **real but small**
- CI includes 0 with upper bound < +0.10: **the projection overstated conversion**
- Δ > +0.20: **impeach before reading**

The standing stops, with §2's amendment:
- any G3 machinery defect
- any overturn row that fails its own margin rule
- teacher timeouts above 2%, which makes the gate inconclusive
- canary refusals above 2% per arm-seat, which breaches G7
- the void-gate calibration shape, which impeaches the run

**Additional reported monitors (not reads):**
- overturn rate against the 12–16% null band, with a sample review if above 30%
- rollout children killed at the 180 s per-candidate deadline, per chunk. Under contention these push the teacher toward its prior, which biases Δ toward zero, so report it in the result.
- for any raw hang, the seq where raw stopped against the teacher's first overturn on that seed

## Not reviewed

- The `/tmp/gatetree_r4` build on the box (conditions 1–2 cover it).
- `gate_raw_retry.py` and `register_gate_ids.py` beyond their stated behavior and the smoke outputs.

**Scope:** this approval is valid only for sha 8d13b0f06366f22b5c1b16168bdc7d15eb941389, for `run_gate.sh` as committed with `GATE_TIMEOUT` set per condition 3, under the conditions and reads above. It still requires Joe's go. Approval certifies the build as written, not the run as executed.
