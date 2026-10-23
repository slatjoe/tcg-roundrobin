# Round 7 — stage 4 pre-gate LAUNCH MANIFEST

Parent: a4d801322a9337cc6ca65f86b526ae5cf334dadb. Launched sha (Claude's confirmation): a6d8442291f6d53aefcdf58daf1c8860d0ed0731. Joe's go: 2026-10-22 ~20:22 EDT ("Launch the pre-gate").

## The launch

- Runner: `code/run_gravy_pregate.sh` at sha256 **d519beb1...**, deployed to the /tmp/gravytree root with the launch-step tools it pins: `shm_sweep.py` (98027a8b...), `parse_r3_pair.py` (ed47c9cd...), `gate_ipcs_cleanup.sh` (338183e2...). The runner's nine pins verify every tool, the driver (0a6b7a85...), the retry and the checkpoint before the first arm.
- Environment: `GATE_TIMEOUT=3870`, `GRAVY_MODEL=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt` (sha256 44f1e5d7...), `PREGATE_SWEEP=1` (forced inside the runner regardless).
- Sequence (the runner's own): the standing G8 sweep at start; the determinism check (seeds 8501-8510 teacher replays, trace equality read by parse_r3_pair.py — a parser failure STOPS the run); ghost arm seat 1 (TEACHER_GHOST, TCG_CLEAN_CHILDREN=1); the G8 sweep; ghost arm seat 2; the R16 seat-crossed raw control; the registry merge. Headroom checked before every arm (abort above 2,800); the (C) sweeper runs live for the whole run.
- Launch state: registry **4,981** games, sha256 d5cfcf79... (Joe spot-checked it himself, 2026-10-22); SHM **0** segments (the runner's opening G8 sweep re-establishes the baseline regardless).
- The pre-gate report cites every artifact by path and sha256 (claude-reply-ef34219 sec.5): the determinism parse, the R16 control, both ghost tables with their parse records and any K5 disposition, the server load lines and fallbacks, the ipcs series and the sweeper log's pass totals (selected / deleted / failed / unattributed), and the registry merge record. Joe spot-checks headline figures (the parse verdicts and the registry hash at minimum) before Claude rules.
