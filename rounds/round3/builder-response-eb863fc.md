# Builder response — gate fleet results and the impeachment audit

Package parent: `eb863fcf5e77e444b270bc031edfa0edd53f1a82` (Joe's upload of
the reply to the run_gate.sh fix). The fleet ran under the APPROVED launch
sha `a148a6d523ddae0697ec6f81cc6de22bf8cdf0ee` with the reply's §2 timeout
(`GATE_TIMEOUT=1600`, recorded in the launch manifest, run_gate.sh itself
unedited) and its §3 operator stop watched throughout.

## 1. The fleet completed clean

- Launched Oct 19 ~17:01 EDT on Joe's go; `GATE-FLEET-DONE` Oct 20 ~03:40
  EDT; the fixed script exited on its own and reaped its servers (0 search
  servers, 0 drivers, 0 run scripts remained at the completion check).
- 800/800 rows (16 files × 50); 16/16 arm manifests `assert_ok` TRUE.
- Production `search_server.py` sha256 BEFORE == AFTER ==
  `81ef2cdb…` — launch condition 2 satisfied.
- Server final counters: s1 `evals=35038269 … fallbacks=0
  seat_mismatch=0`; s2 `evals=35475921 … fallbacks=0 seat_mismatch=0`.
- No raw timeouts (the retry path never ran); teacher timeouts 0/400;
  caps 0; draws 0; connect failures 0. Slowest teacher game 747.0s
  against the 1600s timeout.
- Shared memory: 97 segments at staging, 1,694 at the end; the 3,600
  operator stop was never tripped. Rollout-child cleanup from the arm
  rows: teacher 19,345 found / 19,345 cleaned; raw 0/0. The residue sits
  in kept game dirs (KEEP_GAME=1) — a G8-style sweep is owed before any
  future fleet, not a defect of this run.
- G9 registry merge ran BEFORE any analysis: 811 game ids + 915
  snapshot ids added, 550 → 2,276 games (4 benign id collisions from the
  seed-1001 smoke/fleet id reuse, all eval-only either way). New
  registry sha256
  `3882c7582048a7ff59af60e83622a611dc30608bf6e90ac8da52356624e8a270`.

## 2. The primary read

Full output in `data/gate-launch/analysis_output.txt`; rows and manifests
in `data/gate-launch/rows/` and `data/gate-launch/manifests/`.

- Pooled: teacher 0.7025 − raw 0.4500 = **Δ +0.2525**, seed-clustered
  bootstrap CI **[+0.2075, +0.2975]** (B=10000).
- Seat 1: Δ +0.2500 [+0.1800, +0.3200]. Seat 2: Δ +0.2550
  [+0.1900, +0.3200].
- Discordant units: teacher > raw 111, teacher < raw 10, tied 279;
  exact sign test p ≈ 0.0000. 400/400 units scored, 0 unscored.

**The pooled Δ crosses the registered +0.20 tripwire, so the analysis's
own registered READ is: IMPEACH BEFORE READING.** Section 3 is that
audit, run before this result is read as a conversion.

## 3. The impeachment audit

**(a) G3 first-divergence — one logger artifact, no play defect.**
Raw G3 output (`data/gate-launch/g3_output.txt`): 73 units identical,
319 first divergences are DECISION rows at teacher overturns, and
**8 units flagged MACHINERY_DEFECT, all class DUP_SEQ** (seeds 1035 s2,
1057 s1, 1075 s2, 1111 s2, 1112 s2, 1183 s1, 1185 s2, 1190 s1).
Localized: at the flagged seq, the teacher trace holds two rows — a
`rule=teacher` row with `state_hash` null and a `rule=bridge_pick` row
with the **same cand_hash**. This is the Decide-abort fallback path: the
teacher evaluation aborts, Decide logs a state-less marker, and the
bridge pick — the decision that actually played, and the same decision
the raw arm faced — logs at the same seq. The seq-alignment chokes on
the extra row. Re-running the registered classifier on those 8 units
with ONLY the marker row removed (raw traces untouched) reclassifies
**8/8 as LEGAL** — every unit's true first divergence is a DECISION at a
teacher overturn row (full lines in
`data/gate-launch/audit_checks.txt`). With that, all 400 units are
accounted for: 73 identical, 327 first-diverge at an overturn, 0
play-level machinery defects. The marker row is a trace-logger defect on
a rare path (8 of 400 games, one row each); it does not touch any played
pick. Disclosed as a defect of the instrumentation, not of the run.

**(b) Per-overturn margins — the standing stop does not trip.**
All 915 overturn rows carry `mean_diff` and `se_diff`; **0 violations**
of `mean_diff > 1.5 × se_diff`. The closest call cleared its bar by
2.7% (min ratio 1.027; game 528177756, 0.48 vs 0.467).

**(c) Coverage and integrity monitors.**
Canary refusal per arm-seat: 0.699%–1.365%, under the 2% cap everywhere.
`det_persisted` missing on 0 stat rows across all 8 teacher logs;
`child_fallbacks=0` everywhere. Decide-internal aborts total ~1,300
candidate-world aborts (tolerated under the ≥20-finished-world validity
rule), concentrated at candidate index 2; exactly **one
`det_verify_failed`** in 10,869 contested decisions (c4 teacher s2) —
the hardening hook failing closed and discarding that candidate's
worlds, as designed.

**(d) Calibration (G5) — the impeachment shape is absent.**
Prior-pick rollout predictions run BELOW realized outcomes at nearly
every decision ordinal (bins 1–5: predicted ≈ 0.46–0.48 vs realized
0.7025; bins 6–40: ≈ 0.52–0.55 vs 0.65–0.70; bin 41+: 0.6442 vs 0.6479,
converged). The pattern that would impeach — rollout values running
ahead of outcomes — is not present; the gap's direction is the one the
teacher's own added value produces, since realized outcomes are
post-overturn. Stated limit: G5 as registered cannot by itself separate
"the overturns created the gap" from "the rollouts undervalue these
positions." That separation is what the G4 k=50 relabel measures.

**(e) Baselines — where Δ's size comes from, as far as I can decompose
it.** The raw arm ran cold against its own history: 0.4500 on these
fresh seeds vs v15's eval.py 0.505 [0.456, 0.554]. The teacher ran hot
against §3's off-policy projection (≈ 0.505 + 0.118 ≈ 0.62). Neither
fact touches Δ as the gate's own paired measurement — same seeds, same
conditions, both arms, per-seat Δ nearly identical (+0.250/+0.255) —
but the size against the projection is presumably why the tripwire
exists, so the candidate explanations, in my order of likelihood:
(1) on-policy compounding — §3's gain was measured along the prior's
trajectory; on-policy, each overturn also improves the states later
decisions inherit, so the per-game gain grows past the off-policy sum;
(2) raw-arm seed-set coldness inside its historical CI; (3) an
un-audited machinery path — none found by (a)–(d). The discriminator
between (1) and noise-riding is G4.

**(f) Overturn rate.** 915 / 10,869 contested = 8.42% pooled — BELOW the
12–16% pure-noise band derived in the reply to 8d13b0f. Reported per
the current rule; no stop attaches.

## 4. Where this leaves the gate, per the registration

The impeachment audit the bands demand has been run, and every
registered machinery check comes back clean: no G3 play defect, no
margin violation, coverage inside caps, determinization persisted
everywhere, servers clean, production untouched. What the audit cannot
do — and was never designed to do — is prove the overturns are worth
what the margins claim. That is G4's job: relabel ~100 of the 915
captured overturn snapshots at k=50 and report the fraction where the
overturn pick beats the prior pick, with a CI. The snapshots and their
index are captured and registered; `audit_overturns.py` already shipped
in the approved gate package (8d13b0f).

**Proposal (no launch without Claude's read and Joe's go):** run the G4
audit as the next package — overturn-snapshot relabel at k=50 over a
registered ~100-snapshot sample — and read the gate as converted only
if G4's fraction clears 0.5 with its CI. Until then the honest status
is: Δ measured at +0.2525, machinery impeached and cleared, conversion
awaiting its second half.

## 5. Files in this package

`rounds/round3/builder-response-eb863fc.md` (this file) and under
`rounds/round3/data/gate-launch/`: `launch-manifest.txt` (launch +
completion readings), `analysis_output.txt`, `g3_output.txt`,
`audit_checks.txt`, `gate_prod_hash.txt`, `gate_ipcs.txt`, `rows/` (the
16 arm row files, 800 games), `manifests/` (the 16 arm manifests).
Teacher stat files remain on the box at `/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl`
(sha256 in `audit_checks.txt`); traces likewise under each arm logdir.
