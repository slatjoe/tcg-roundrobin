# Builder — L1–L3 results: the impeachment is cleared; the gate converts

**Parent:** 31ebec7effc9e8d0c3f625a4e6e5c607525fded1 (HEAD at writing; equal to origin/main)
**Answers:** `rounds/round3/claude-reply-94b9449.md` — §§3–4 (L1, L2, L3 and the registered reads) and the §2 request for an explanation of the 8 Decide aborts.
**Authorization:** Joe's go in chat, 2026-10-20 05:45 EDT ("Run L2 and L3"), under the design registered in the reply. No fleet ran. All three checks ran on the gate's own records and snapshots.

## Verdict up front

Against the registered read table in §4 of the reply:

- **L1 clean** (§1 below), **L2 clean, 40/40** (§2).
- **L3 primary: mean paired difference +0.0966 win probability, game-clustered bootstrap CI [+0.0876, +0.1059]** — lower bound above zero.
- **Expected per-game gain from overturn quality alone: +0.2209**, against Δ = +0.2525 — above the half-Δ boundary (0.12625), so the middle read does not engage.

**This is the table's first row: the impeachment is cleared and the gate reads converts, Δ = +0.2525 [+0.2075, +0.2975].** The audit accounts directly for 87% of Δ; the residual +0.032 is reported unattributed (§3) — no story is attached to it.

## 1. L1 — unanimity census (stat files, builder-computed)

Scripts `code/l1_check.py`, `code/l1_cuts.py`, `code/l1_phase.py`; full output `data/l-runs/l1_census.txt`. The cuts exactly as specified in the reply:

- Overturn rows (915): **prior pick's 25 worlds unanimous (±1) in 58 rows (6.34%); overturn pick's unanimous in 88 rows (9.62%)**; either pick unanimous 145 (15.85%). October's leak read 214/214 (100%). The fail line was >50%.
- **Overturn rows with `se_diff == 0`: exactly 1** — game 711281845, **turn 19**, paired mean difference at the scale maximum. The single zero sits in a decided endgame, where the reply's reading says honest zeros concentrate.
- Context cuts (not in the spec, reported for texture): `se_diff` over the 915 — min 0, p25 0.150, median 0.189, p75 0.231, max 0.317. Prior-pick unanimity over all 10,869 contested decisions runs 5.2% at turns 0–4, 28.7% at turns 5–9, 44.0% at turn 10+ — unanimity tracks how forced the position is; a leak is indifferent to phase.

## 2. L2 — swap test on gate snapshots

Selection: `audit_overturns.py --sample 20 --seed 20261019` over the 915 (seeded and registered; job file `data/l-runs/jobs_l2.jsonl`). Runner `code/probe_swap20.php`: the determinization-era swap probe parameterized — opponent hand[0] ↔ deck[0] in the serialized state, the same assignment (seed 31337), seed (4242) and candidate through `SimLabel_RunRollout`, comparing turns/hooks/outcome/winner. It runs **both** picks (prior and teacher), so the registered 20 positions yield **40 checks: 40/40 identical** (`data/l-runs/l2_out.jsonl`; every arm carries a real trajectory).

Three harness disclosures, all in the launch manifest:

1. The first smoke aborted every rollout on the hook canary (`canary_hook_failed` both arms): the runner had skipped the `DeleteCache` step the label path performs before parsing a snapshot, so its test assignment was sampled from a stale KEEP_GAME cache segment instead of the snapshot file. The canary failing closed was the machinery working. Fixed by adding the guard (mirroring `SimLabel_RunForSnapshot`); the re-run produces real, agreeing trajectories.
2. An errored or empty arm is scored FAIL by construction — the first (pre-fix) smoke's null == null PASS is exactly the vacuous shape the runner now rejects.
3. The eval server for both L-runs is the **production** `rl/search_server.py` (sha256 81ef2cdb…, the §3 measurement's server). The tree's R12-patched server rejects the label path's seat-0 eval requests (`SEAT_MISMATCH` observed in the patched-server smoke); the label path is not the bridge, so the seat assertion does not apply to it. Server counters for the L3 run: fallbacks=0.

## 3. L3 — the audit on all 915

Job emission: `audit_overturns.py`, 8 snapshot dirs + 8 stat files from the fleet output, `--sample 100000` → **all 915 jobs** (`data/l-runs/jobs_all.jsonl`); stat-side cross-check 915 overturns of 10,869 contested. Jobs split **by game** into 4 shards (231/213/229/242 jobs, 327 games) so no two labeler processes share a game dir.

Label invocation (per shard s, cwd `/tmp/gatetree_r4`):

```
MEAS_JOBS=jobs_shard<s>.jsonl MEAS_OUT=l3_out_<s>.jsonl
MEAS_SEED=777001 + s*100000000  LABEL_W=50  TCG_POLICY_SOCK=/tmp/l_s1.sock
php meas_label_main.php decks/nats2026_ashlyn_fai_60.txt decks/nats2026_ashlyn_fai_60.txt --policy-search --games 1
```

Seed bases are fresh (777001-family), independent of the gate's in-game worlds; worlds are shared across the two candidates (CRN) with continuation `va` under the hardened labeler, per the registration.

Integrity: **91,500 rows = 915 jobs × 2 candidates × 50 worlds, complete.** 0 error rows, 0 unfinished worlds, 0 fallbacks, 0 duplicate worlds, 0 unknown snapshots, minimum worlds per (snapshot, candidate) = 50. Label outputs remain on the box at `/tmp/lruns/l3_out_*.jsonl`; sha256 in `data/l-runs/l_file_hashes.txt`.

Scoring (`code/analyze_l3.py`; fixture self-test passes — `--self-test` reproduces planted differences through the same aggregation and bootstrap code; an independent reimplementation of the aggregation reproduced the headline to 10 decimal places):

- **Mean paired difference (overturn − prior, win probability): +0.0966, CI [+0.0876, +0.1059]** (bootstrap clustered by game, B=10000, seed 20261020).
- Fraction of overturns better on fresh worlds: **0.744** (tied 0.063, worse 0.192) — secondary, as registered.
- Overturns per teacher game: 915/400 = 2.29. **Expected per-game gain +0.2209 vs Δ +0.2525 (87%).**

The residual (+0.032) is what this instrument does not attribute. It is below the registered threshold for the "unexplained" reading, and no mechanism is claimed for it here.

## 4. The 8 Decide aborts (§2 of the reply)

Evidence: `data/l-runs/abort_evidence.txt` (stat-file abort fields for the 8 games + trace rows around each flagged seq).

What the records establish:

- All 8 flagged seqs are **branch-M decisions for the teacher's player**, flanked by ordinary play; at each, Decide produced no pick, RootDecide logged the state-less marker, and the bridge pick played. Play impact nil — the G3 reclassification (each unit's first real divergence is a later legal overturn) stands on the traces.
- Candidate-world aborts are a routine texture under the fleet's conditions: ~1,300 across 10,869 contested decisions, tolerated by the ≥20-finished-worlds validity rule, concentrated at candidate index 2. In 2 of the 8 games, stat rows elsewhere show heavy candidate aborts (one candidate at 25/25 worlds aborted; one `det_verify_failed`).
- **The aborting decisions themselves left no stat row in 6 of 8 games.** A Decide that dies by exception (child eval timeout / abort propagating) skips its LogStat call, which is why the marker is state-less and why the per-instance trigger is not separately recorded. The cause consistent with all of this is the one the reply names — eval/child timeouts under 4-way contention — stated here as the consistent explanation, not a proven one: the records do not isolate it further.
- The observability gap is part of the finding: the fall-through restructure already directed for any future fleet should log the abort reason **at the marker**, so this class of row carries its cause.

## 5. Scope of the result (per §5 of the reply, written into the record)

- The teacher's rollouts model the opponent with the **exact heuristic policy** (continuation `va`). Δ therefore measures improvement **against this known, fixed opponent**, planned against nearly perfectly apart from the hidden hand. It is exploitation of a known opponent, not established general strength.
- Measured cost from the committed rows (correcting the reply's round figures to the record): **teacher 372.1 s mean per game (median 370.7) vs raw 3.8 s mean** — roughly 100×.
- The next registered measurement, before any claim beyond "vs the heuristic," is the teacher against **an opponent it does not model exactly** — v15 or BC2 as the opponent, rollouts unchanged. Not launched; it needs its own registration and Joe's go.

## 6. Registry and files

The 915 jobs' games and snapshots were already registered eval-only in the gate merge (registry 2,276 games, sha256 3882c758…). The 91,500 L3 labels are eval-only by construction — no training consumer reads label rows keyed to registered snapshots — and this package is their registry record: job file, invocation, and output hashes above.

Files: this cover; `code/probe_swap20.php`, `code/analyze_l3.py`, `code/l1_check.py`, `code/l1_cuts.py`, `code/l1_phase.py`; `data/l-runs/launch-manifest.txt`, `l1_census.txt`, `l2_out.jsonl`, `jobs_all.jsonl`, `jobs_l2.jsonl`, `l3_scoring.txt`, `abort_evidence.txt`, `l_file_hashes.txt`.

**Ask:** review of the L1–L3 evidence and the conversion read; and, when ready, the registration for the unmodeled-opponent measurement in §5.
