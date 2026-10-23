# Round 7 — stage 5 GATE FLEET LAUNCH MANIFEST

Parent: 45eca37ef8f0a7753621faede371e08b677e72fc. Approved build sha: a6d8442291f6d53aefcdf58daf1c8860d0ed0731 (Claude's confirmation of the containment build), the pre-gate passed under K6 (claude-reply-1ab9903). Joe's go: 2026-10-23 ~07:01 EDT ("Launch the fleet").

## Preconditions, as run

- **K6 mechanical check: `496 133 0 0`** — exact (496 rollout rows, 133 unstamped, 0 unstamped-not-thin-prior, 0 unstamped-with-pick-not-prior). Disclosure: the check was run **by the builder at Joe's explicit request** (2026-10-23 06:59 EDT), not by Joe's own hands; the stat files are fixed and the line is re-runnable by anyone.
- **Joe's standing change (2026-10-23, his direction):** the builder runs all box spot-check commands from here on; Joe does not run terminal commands. This supersedes the ef34219 sec.5 arrangement of Joe-side spot-checks for the fleet report — the fleet's spot-check items (the primary DELTA line, the teacher-timeout rate, the registry hash) will be builder-run and reported with their commands and raw outputs in the fleet package, so they remain independently re-runnable from the cited artifacts.
- **The sec.4 launch condition:** the standing G8 sweep (gate_ipcs_cleanup.sh, 338183e2...) runs immediately before the runner, with no game processes alive; the before/after counts are recorded below by the launch step (expected: 0 after).

## The launch

- Runner: `code/run_gravy_gate.sh` at sha256 **0ffe635b...**, deployed to the /tmp/gravytree root with `shm_sweep.py` (98027a8b...) beside it; the runner's guard block verifies its pins (driver 0a6b7a85..., retry c3fb227e..., checkpoint 44f1e5d7..., the sweeper) before the first chunk.
- Environment: `GATE_TIMEOUT=3870`, `GRAVY_MODEL=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt`.
- Design (as registered): teacher vs raw v10, paired, seeds **8001-8200**, both seats, Gravy mirror vs the heuristic, 4 chunks; capped games score 0.5 in the primary; the (C) sweeper runs live for the whole fleet; registry merge of all fleet ids BEFORE any analysis.
- Stops, as registered: teacher timeouts > 2% -> INCONCLUSIVE; canary refusals > 2%; overturn rows failing their own margin; DUP_SEQ outside K5; SHM at 3,600 -> stop, INCONCLUSIVE (a box-side watchdog enforces the SHM stop while the fleet runs unattended).
- Expected residue: KEEP_GAME parent segments accumulate ~1 per game (up to ~800 by the close) inside the headroom; the fleet report states the closing count against this expectation.
- Analysis: `analyze_gate_gravy.py` (d468468e...) with the O2 (L1 input glob -> /tmp/ggate) and O3 (L3 DELTA = the fleet's measured primary) deployment substitutions, their diffs and hashes in the fleet package; L1/L2/L3/G3 as registered. Report-only items: the fleet thin-prior rate; the overturn rate among NON-THIN contested decisions vs the 12-16% band; the per-candidate unfinished-count diagnostic for overturns; the dilution sentence in any null/weak read; the transfer band read (+0.15). The selection read discipline stands: stage 3 showed non-inferiority of v10 to the anchor, nothing more.
- Launch state: registry **5,031** games, sha256 71cacfb0...; SHM per the sweep record above. Wall estimate: ~17-18.5 h.
