# Round 8 — W=100 V1 check launch manifest

**Parent:** d8f66e78 (Claude's confirmation of the W=100 amendment).
**Approved build sha:** a9dd40e2 (amendment confirmed in `claude-reply-a9dd40e.md`).
**Authorization:** Joe's Option-1 choice, recorded 2026-10-25 14:46 EDT — the check launches on that go per the confirmation's scope.

## What launches

`code/run_w_check.sh` (sha256 `9d982a49…`) on the box, with the amended labeler (`acf5f4bb…`) and reducer (`25a5f4cc…`):

- The pilot's 547 V1 capture states stamped W=100, labeled twice — run A at world-seed base 555001, run B at 777001 — sharded across 4 native-tree copies exactly as the corpus labeler, G8 first, (C) containment per tree, production server per seat.
- **No games.** The check labels existing snapshots in place.
- Read: V1-ov and V1-conf with Wilson intervals (pilot_report.py's own arithmetic), thin counts, per-job timings — and the **registered threshold printed last: V1-ov ≥ 0.50 → PASS; below → STOP, reported for decision.**
- **Report-only additions** (per the confirmation; none changes the PASS/STOP read): the finished-worlds distribution per candidate from the labels' `n_worlds` (minimum, share below 100, share below 80) plus the raw rows' error-reason counts (including deadline kills); per-job mean / p95 / max and the corpus estimate at W=100; the sweepers' totals and the closing SHM count.

## Not launched

The corpus (on PASS it comes to Joe's go, after the reviewer's read of the check report, with the option-(a) one-capture-per-seed declaration in its manifest), T1, the gate. The sign-test fix remains owed before the gate.
