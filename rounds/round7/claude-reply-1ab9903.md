# Claude — ruling on the K3 pre-gate report

**Reviewed commit:** 1ab9903b2f513592c10a444ada8f6e4ebc415b10 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch manifest `pregate-launch.md` (e4911b2). The committed `claude-reply-a6d8442.md` hashes to `19316ff9…7b800b8153`, the value I gave Joe.
**Package:** `rounds/round7/pregate-report.md`.

**Verdict:**
- **The pre-gate PASSES under one reclassification, ruled here and checked by a mechanical test that Joe runs (§2).**
- The INVALID_ASSERT on all 20 units is a defect in the manifest check's premise, not a divergence. The check was written on Fai, where the thin-prior fallback never fired, and on Gravy it fails by construction.
- Determinism, R16, the server evidence, the containment and the registry are all accepted (§1, §3).
- **The fleet may launch on Joe's go once his §2 check returns the expected line**, under the conditions in §4.

## 1. What passed outright

- **Determinism:** `PARSE-PASS`, 10/10 rows IDENTICAL, hits 0, every column True. Joe confirmed the line on the box. His correction to §9 stands: the verdict line is in `pregate_pair_determinism.parse.txt`, not the table file.
- **R16:** `RAW-CONTROL: PASS`, with all 10 seeds differing across seats.
- **The servers:** both loaded `ckpt_v10.pt`, 250 status lines all at `fallbacks=0`/`seat_mismatch=0`, 50/50 games at `cf=0`. The production server's hash was unchanged.
- **Attempt 1:** it refused without `PREGATE_SWEEP=1` before touching anything. That's the guard working, and it's disclosed. The run of record is attempt 2.
- **The two ghost tables are byte-identical. That's expected, not suspicious.** The table carries no seat-specific field (no game ids, no seat column), and all 20 rows have the same values. The per-seat difference sits in the rows and manifests, which have different hashes.

## 2. The ghost read: the reclassification

**The mechanism is confirmed from the code, not only from the report.** The repo's copy of the teacher (`code/search-gate-tree.php`, an earlier build with the same `DecideInner` structure) shows it:
- the thin-prior branch logs `$base` with `fallback = "thin_prior"` and `pick = $priorPick`, then **returns**
- the `TEACHER_GHOST` block that stamps `ghost = 1` comes later and is reached only by a search that clears the floor
- `$base` already holds `means` and `n_worlds`, so the driver's `arm_assertions` (`paired_driver_gravy.py`) counts a thin-prior row as a **rollout row**
- `ghost_flag_on_all_rollouts = all(r.get("ghost") == 1 for r in rollout_rows)` therefore fails whenever any thin-prior decision occurs

On Fai and O the thin-prior rate was 0 of about 21,500 decisions, so the premise always held. On Gravy, every unit contains at least one thin-prior decision.

**What the pre-gate exists to show is shown.** Running the full machinery and then forcing the prior's pick leaves the live game action-identical to raw:
- 20/20 units with within-row hits 0 and outcomes equal
- trace rules `ghost_prior` on every teacher trace row
- the pick equal to the prior on all 1,917 teacher rows

The thin-prior decisions also ran the machinery: they forked children, burned their deadlines and aborted worlds. So the side effects the ghost test guards against were exercised on those decisions too. The only thing that never happened on them is the force itself, because the fallback already plays the prior.

**The rule (K6, registered here; it applies to the ghost arm's `ghost_flag_on_all_rollouts` check only):** a ghost arm's assert is satisfied iff
- every other ghost check is true (`pick_eq_prior_all_teacher`, `rollouts_present`, `trace_rules_all_ghost_prior`, `trace_teacher_pick_is_prior_argmax`), **and**
- every rollout row without `ghost = 1` carries `fallback = "thin_prior"` **and** `pick == prior_pick`

Under K6, a unit whose only failures are the INVALID_ASSERT verdict and `assert ok False` from this check reads as **IDENTICAL**. Any other unstamped row, or any other failing check, stays a stop.

**The mechanical check: Joe runs it on the box, independently of the builder.**

```
python3 -c "import json,sys; rows=[json.loads(l) for f in sys.argv[1:] for l in open(f)]; ro=[r for r in rows if r.get('teacher')==1 and ('means' in r or 'n_worlds' in r)]; un=[r for r in ro if r.get('ghost')!=1]; print(len(ro), len(un), sum(r.get('fallback')!='thin_prior' for r in un), sum(r.get('pick')!=r.get('prior_pick') for r in un))" /tmp/ggate/pregate_ghost_s1_log/search_stats.jsonl /tmp/ggate/pregate_ghost_s2_log/search_stats.jsonl
```

**Expected output: `496 133 0 0`.** That's the rollout rows, the unstamped rows, the unstamped rows that aren't thin-prior, and the unstamped rows whose pick isn't the prior's. If it prints exactly that, K6 is satisfied, and **the pre-gate passes as 20/20 IDENTICAL**. Anything else and the pre-gate stands failed, and it comes back to me.

**K5 disposition: none.** Agreed: the seq column is `None` on all 20 rows, and no abort-marker row appears.

## 3. Containment and the registry: accepted

**This was (C)'s first production run, and it was clean:**
- 188 passes
- **5,114 selected, 5,114 deleted, 0 failed, 0 unattributed**
- the G8 sweeps after the ghost arms found only 11 and 24 segments
- headroom stayed at most 20 before every arm

The 30 segments left at the end are the raw-arm parents, kept by rule 3 while their `Games/` directories exist.

**A note for the fleet:** the KEEP_GAME parents' directories persist, so their segments stay until the fleet's closing sweep. That's about one per game, up to roughly 800 by the end of the fleet, which is well inside the 3,600 headroom. It's expected residue, not a leak. The fleet report states the closing count against it.

**The registry:** 4,981 → **5,031**, `71cacfb0…`. 50 game ids, 0 snapshots, 0 collisions, all under `gate:gate` as disclosed. Joe confirmed the hash in full. Accepted.

## 4. The fleet: may launch on Joe's go, after `496 133 0 0`

**What launches:**
- `run_gravy_gate.sh` (`0ffe635b…`), with the tree pins as approved
- `GATE_TIMEOUT=3870`
- `GRAVY_MODEL` = `ckpt_v10.pt` (`44f1e5d7…`)
- `shm_sweep.py` (`98027a8b…`) placed at the tree root

**Conditions:**
1. **Immediately before launch,** run the standing G8 sweep (`gate_ipcs_cleanup.sh`, with no game processes alive), and record the count in the launch manifest (it should be 0). This is ef34219 §4. The runner itself doesn't sweep at start, and rule 4 never touches what already exists.
2. **The stops stand as registered:**
   - teacher timeouts above 2% → INCONCLUSIVE
   - canary refusals above 2%
   - overturn rows failing their own margin
   - DUP_SEQ outside K5
   - SHM at 3,600 → stop, INCONCLUSIVE, not partially readable
3. **I checked the fleet arm against K6's lesson.** The teacher arm's manifest checks hold on thin-prior rows by construction: `det_persisted` is set in `$base` before the fallback returns, and the checks are about presence. So **K6 is not needed for the fleet, and doesn't apply to it.**
4. **The analysis:** `analyze_gate_gravy.py` (`d468468e…`), with O2 (the L1 glob) and O3 (the L3 DELTA) as deployment substitutions with their diffs and hashes. It also carries the registered report-only items:
   - the thin-prior rate
   - the **overturn rate among non-thin contested decisions**, against the 12–16% band. The band was measured on Fai, where thin-prior was 0, so the pooled overturn rate is diluted on Gravy and the non-thin rate is the comparable one.
   - the unfinished-count diagnostic for overturns
   - the sentence on fallback dilution in any null or weak read

   The pre-gate's 26.8% matches the first probe's 27%. Expect a quarter of contested decisions to play the raw pick.
5. **The fleet report** cites every artifact by path and sha256, and Joe spot-checks the primary Δ line, the teacher-timeout rate and the registry hash on the box before I rule. Plan for about 17–18.5 hours of wall time.

## Not reviewed

These are on the box, and I took them from the report:
- the stat files
- the manifests and tables
- the sweeper log
- the registry file

Joe's spot-checks cover the determinism verdict, the registry hash and the INVALID_ASSERT count. His §2 command is what settles the ghost read.

**Scope:** this reply rules the ghost read under K6, with the pre-gate passing on Joe's `496 133 0 0`, and accepts the rest of the pre-gate report. On that output, **the fleet may launch on Joe's go** under §4. Approval certifies the build as written, not the run as executed.
