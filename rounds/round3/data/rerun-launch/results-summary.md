# Round-3 rerun — results (read against the registered reads, as found)

**Run:** launched 2026-10-19 09:45 EDT on Joe's go, approved sha
a6e9a6352f05f89e208d7eef9df2c198cf2a1ecb, tree /tmp/reruntree rebuilt
from that package. Completed ~12:55 EDT. Launch conditions recorded in
launch-manifest.txt: condition 1 build hashes MATCH (search.php
6cd6f980…, policy_server.php 64c21539…, in-tree server ab85fa1b…);
condition 2 production server hash BEFORE == AFTER ==
81ef2cdbefe687… — the run is not void. Both servers' final counter
lines: fallbacks=0, seat_mismatch=0 (verbatim in the manifest).

**Verdict: THE PRE-GATE PASSES.** Every pair on every seed passes
under the fc8faef §6 reads (107ea5d reads + canary amendment +
seat_ok + assert_ok + standing raw control):

| pairing | verdict | within-row hits | invalid seeds |
|---|---|---|---|
| raw vs ghost, seat 1 | **19/19 IDENTICAL** | 0 | 0 |
| raw vs ghost, seat 2 | **19/19 IDENTICAL** | 0 | 0 |
| raw vs shadow, seat 1 | **19/19 IDENTICAL** | 0 | 0 |
| ghost vs capture, seat 1 | **19/19 IDENTICAL** | 0 | 0 |

Per-seed detail in the four pair-*.md tables: every seed shows
outcome equal True, modes ok True, seat ok True, assert ok True.
Pairing tables were produced by r3_pair.py from the committed row
files and re-run independently by the builder after the completion
watcher's session timed out; both productions agree.

- **Standing raw control:** raw seat 1 vs raw seat 2 differ on
  **19/19 seeds** — RAW-CONTROL PASS (raw-control.txt). The seat
  defect's signature is absent.
- **No FAIL-localized, no FAIL-outcome, no INVALID of any class:**
  no INVALID_MODE / INVALID_SEAT / INVALID_ASSERT, no MISSING_ROW,
  no DUP_SEQ, no shadow_fallback_decide rows, no timeouts (seed 19
  excluded as registered; its R18 diagnostic was reported in the
  fc8faef package).
- **Canary coverage (amended rule; counted with count_canary.py
  over each arm's search_stats):** ghost s1 7/1,448 = 0.483%;
  ghost s2 25/1,322 = 1.891%; shadow s1 0.483%; capture s1 0.483%.
  All arm rates ≤ 2% cap; highest branch 3.23% (none above the 5%
  naming line). No refusal left a non-bridge_pick trace row — no
  seed is invalidated by a refusal. (Raw arms produce no teacher
  rows, hence no contested decisions.)
- **Assertions:** all six arm manifests assert_ok TRUE (raw arms:
  zero stat rows / zero teacher trace rows; ghost: pick == prior
  argmax on every teacher row, ghost flags present; shadow: all
  rules shadow_bridge; capture: capture rows with pick ==
  prior_pick and no rollout fields).
- **Shared memory (R16):** ipcs 2,911 before → 3,225 after
  (+314 over the run; per-arm ledger in r3x_ipcs.txt: +19 after
  each raw arm, +94 ghost s1, +69 ghost s2, +94 shadow, +19
  capture). No timeout kills occurred in this run, so the
  DeleteCache path was not exercised live (it was exercised in
  the fc8faef package's forced-timeout test, 66/66).

**What this establishes:** the ghost teacher IS raw v15 — the
teacher machinery, run in ghost mode, reproduces the plain bridge
game action-for-action at both seats, and shadow/capture agree
with it at seat 1. The pre-gate condition for the paired gate
(Claude's round-2 registration) is met. The gate itself is a
separate build + registration and is not launched by this result.

Files: launch-manifest.txt (conditions 1–2 + startup/counter
lines), pair-*.md (4), raw-control.txt, r3x_*.jsonl (6 driver row
files), r3x_*.jsonl.manifest.json (6 arm manifests), r3x_ipcs.txt.
Traces and gamelogs remain on the box in /tmp/r3x_*_log.
