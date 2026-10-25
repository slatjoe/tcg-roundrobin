# Round-8 fix package — §2.3 functional fixture tests

The only executions in the fix package (claude-reply-a076148
§2.3/§6): file computations on round 7's published rows plus one
machinery retry. Run 2026-10-25. All three fixtures PASS against
the reviewer's expected values.

## Fixture 1 — fixed analysis on round 7's published rows

- **Code under test:** `../code/analyze_distill_gate.py` (the
  §2.2 rewrite).
- **Inputs:** `rounds/round7/data/rows/` — the 16 published
  Fai-gate row files from the same paired driver
  (`gate_c{1..4}_{teacher,raw}_s{1,2}.jsonl`, seeds 8001–8200).
- **Mapping:** `shim_analyze_rows.py` (in this dir) copies them
  into the analysis's fleet layout (`{raw,dist}_c{N}_s{S}.jsonl`)
  with teacher files as the "dist" arm; the only field rewritten
  is a teacher row's `arm` ("teacher" → "raw"), because the
  analysis collects raw-arm driver rows (both round-8 gate arms
  play raw).
- **Where run:** on the box (the analysis reads the registry at
  its hardcoded `/tmp/harvest/do_not_train_registry.json`), with
  `DISTILL_REGISTRY_SHA256=fc46f835…` (the registry on disk
  matched). Fleet dir built at `/tmp/r8_fixtures/fleet_r7`.
- **Outputs:** `analyze_r7_output.txt` (full stdout),
  `analyze_r7_report.json` (the `--out` report).

| Quantity | Expected (§2.3) | Observed |
|---|---|---|
| paired units | 400 | 400 |
| timeout units | 7 | 7 |
| sum of paired diffs | +6.5 | 6.5 |
| Δ (dist − raw) | +0.01625 | 0.01625 |
| diverged units | 88 | 88 |
| unusable units | — | 0 |
| band read | DOES NOT CONVERT | DOES NOT CONVERT (CI [−0.00375, +0.03625] includes 0) |

For reference: identical units 305; absolute scores dist
0.54875 / raw 0.5325; per-seat Δ seat1 +0.0175, seat2 +0.015.

## Fixture 2 — pregate_compare.py on round-7 raw rows

- **Code under test:** `../code/pregate_compare.py` (the §2.2
  rewrite).
- **Inputs:** `pregate_r7_rows.jsonl` (in this dir), built by
  `make_pregate_fixture_rows.py` from round 7's
  `gate_c1_raw_s1.jsonl` + `gate_c1_raw_s2.jsonl`, seeds
  8001–8010, both seats, verbatim — 20 rows (10 seeds × 2 seats)
  in pre-gate shape. The same file fills all four slots
  (native run1/run2, corrected run1/run2): this fixture tests
  the comparator, not two trees.
- **Output:** `pregate_fixture_report.json`.

| Check | Expected (§2.3) | Observed |
|---|---|---|
| determinism, file vs itself | IDENTICAL 10/10 | deterministic, 0 diffs on all compared fields across 20 units (10 seeds × 2 seats) |
| seat control (seat-1 vs seat-2 rows) | must differ | 10/10 seeds differ on `gamelog_sha` (pass) |

Unit note: pregate_compare counts (seed, arm, seat) units, so
the determinism block reports 20 units; the reviewer's "10/10"
is the same statement at seed granularity — all 10 seeds are
identical in both seats.

## Fixture 3 — stock retry fires only on the timeout row

- **Code under test:** the stock `gate_raw_retry.py`
  (sha256 c3fb227e…) from the native distill tree, invoked
  exactly as the fixed `run_distill_gate.sh` invokes it
  (`--tree --sock --seat --timeout --deck --rows --logdir`,
  `GATE_GAME_IDS_FILE` set).
- **Setup (on the box, `/tmp/r8_fixture_retry/`):** a v15
  production-shape server from the native tree on a fixture
  socket. Rows file: one real decided round-7 raw row (seed
  8004, winner 1) + one injected minimal row
  `{"seed": 999901, "arm": "raw", "seat": 1, "invalid": "timeout"}`.
- **Log:** `retry_fixture.log` (the full session trace);
  final rows in `retry_fixture_rows_final.jsonl`; the control
  file after its run in `retry_fixture_rows_control_final.jsonl`.

| Step | Expected (§2.3) | Observed |
|---|---|---|
| control run (rows file with no timeout row) | nothing runs | "no raw timeouts; nothing to retry"; no game played, no ids file entries |
| main run | retry fires only for the timeout row; at most one raw game | "raw retry seed 999901: completed winner=1"; exactly one game played (game id 520460677, 2.5 s, winner 1); the seed-8004 row is untouched and still first in the file |

The server was killed at the end of the fixture session.
