# Round 10 Step 2+3 combined paired fleet — launch facts (compiled from the launch coordinator's and the builder's records; committed with the §18 repair package)

## Approval chain
- Package: rounds/round10/step2-fleet-package.md (approved sha 5b5ada42).
- Claude approval: claude-reply-5b5ada4 (APPROVED).
- Fix pass committed: 7f906f9b = LAUNCHED SHA (differs from 5b5ada42 only under rounds/).
- Joe's go: 2026-10-30 13:09 EDT.

## Deploy (2026-10-30, before launch)
- All 17 files of rounds/round10/code/step2/ copied to box /home/joe/tcg/round10_code/step2/ via scp over the Tailscale tunnel proxy.
- Read-back: sha256sum of all 17 deployed files compared against the repo copies — ALL MATCH.
  Key pins: run_fleet_games.sh 8e3c3fbd…, run_fleet_l3.sh 2f28e0cc…, fleet_read.py 7370b989…, search_s3_thr.php 4a1936fe…, settings_fleet.json 1a8de290…, paired_driver_gravy.py 3389b1b9….
- The runner additionally records its own deployed-code hash table at /home/joe/tcg/r10fleet_out/deployed_code_hashes_games.txt when it starts.

## Box hygiene at launch (2026-10-30 13:09–13:12 EDT)
- No stale processes matching paired_driver / run_fleet / run_pilot / search_server / play_game.
- SHM: 11 segments, all 32,768 B, all nattch 0 (far below the 3,600 stop threshold; the runner's prespawn shm_sweep handles unattached segments).
- Pre-gate manifest in place at the runner's configured box path /home/joe/tcg/r10pilot_out/pregate/attempt2/pregate_manifest.json; sha256 685fefa337f7b8f13f0d5dabc8ef95184e4e469b18ff1d91877b774bb5bb832f — byte-identical to the published repo copy rounds/round10/data/step1/pregate_attempt2/pregate_manifest.json.
- /tmp at launch: 20,899,102,720 B total, 1,616,302,080 B available (93% used).
  - Runner FREESPACE basis: per-tree (du of /tmp/gravytree) 468,711,508 B × 8 trees = 3,749,692,064 B required; with the ×1.25 headroom rule the launch needs ≥ 4,687,115,080 B available.
  - Largest /tmp residents: /tmp/distill_wcheck 1,845,812,615 B; /tmp/distill_pilot_resume 740,110,317 B; pilot scratch trees /tmp/r10pilot_gm_s1a/s1b/s2a/s2b ≈ 477 MB each (~1.91 GB total) and /tmp/r10pilot_l3_tree_0–3 ≈ 469 MB each (~1.87 GB total); probe-era trees ~0.47–0.48 GB each.
  - Nothing was deleted: per the launch brief, the runner's own FREESPACE pre-flight is the guard and any cleanup is Joe's decision.

## Launch
- Launched 2026-10-30 13:10:38 EDT: `setsid nohup bash run_fleet_games.sh` from /home/joe/tcg/round10_code/step2/, log at /home/joe/tcg/r10fleet_out/fleet_games.launch.log.
- Runner output, in order:
  - "pins OK; deployed code hashes recorded" (runner's own table at /home/joe/tcg/r10fleet_out/deployed_code_hashes_games.txt).
  - settings: timeout=8031, registry tag r10_step2_fleet; teacher tuple built from settings_fleet.json (H8k-180+H).
  - **PREGATE-GATE ok: attempt 2 IDENTICAL under the fleet's build sha + tuple** — the mechanical gate PASSED against /home/joe/tcg/r10pilot_out/pregate/attempt2/pregate_manifest.json.
  - **FREESPACE ABORT**: "freespace: per-tree 468711508 B x 8 trees = required 3749692064 B; available 1616302080 B" → "ABORT: /tmp free space below required x 1.25".
- The runner exited before any spawn (freespace precedes the G8 sweep and all server/driver starts). Verified after the abort: zero fleet/driver/server processes; /tmp unchanged at 1,616,302,080 B available.
- Outdir /home/joe/tcg/r10fleet_out/ holds only deployed_code_hashes_games.txt and fleet_games.launch.log. The single-shot guards (games_manifest.json, fleet_read.json) are absent, so a relaunch after cleanup starts clean from the top (hashes re-recorded, gate re-checked, freespace re-measured).
- Shortfall: the launch needs ≥ 4,687,115,080 B available; it has 1,616,302,080 B — ≈ 3.07 GB short. Freeing the pilot's own scratch trees alone (/tmp/r10pilot_gm_* ≈ 1.91 GB + /tmp/r10pilot_l3_tree_* ≈ 1.87 GB ≈ 3.78 GB total) would clear it with room to spare; the round-8 distill trees (/tmp/distill_wcheck 1.85 GB, /tmp/distill_pilot_resume 0.74 GB) would also cover most of it. NO cleanup was performed — that decision is Joe's, as with the pilot.
- STATUS: fleet NOT running. Awaiting a cleanup decision, then relaunch.

## Relaunch (parent-executed, 2026-10-30 13:38 EDT) — FREESPACE passed, ABORT at teacher-server start
- Joe approved the cleanup; the parent agent executed it: exactly the pilot's eight /tmp scratch trees deleted (/tmp/r10pilot_gm_s1a/s1b/s2a/s2b and /tmp/r10pilot_l3_tree_0–3). Nothing else was deleted.
- Relaunch at 13:38 EDT (the launch command's own timestamp: 13:38:14 EDT): `setsid nohup bash run_fleet_games.sh` from /home/joe/tcg/round10_code/step2/, log at /home/joe/tcg/r10fleet_out/fleet_games.launch2.log. Runner sequence this time:
  - pins OK; PREGATE-GATE ok (attempt 2 IDENTICAL under the fleet's build sha + tuple).
  - **FREESPACE PASSED**: 5,844,172,800 B available (≥ the 4,687,115,080 B factored requirement).
  - SHM sweep took the segment count 11 → 0.
  - **ABORT at teacher-server start**: /home/joe/tcg/r10fleet_out/srv_18241.log reads "search_server: SEARCH_MODEL missing: ''".
- ROOT CAUSE (verified on the box by the parent): run_fleet_games.sh's two search_server.py spawn blocks (teacher ~line 201, raw ~line 268) never set SEARCH_MODEL, which the pinned production server (sha256 81ef2cdb…, its lines 68–69) requires. The teacher block instead carries the patched server's env names (TCG_POLICY_SEARCH_CKPT etc.), which the production server never reads. run_fleet_l3.sh is UNAFFECTED — it sets SEARCH_MODEL correctly (line 207).
- Consumption: ZERO games ran, ZERO seeds consumed; games_manifest.json and fleet_read.json still absent (single-shot guards untouched), so a post-repair relaunch starts clean.
- Disposition: a repair package is being built in staging for Claude's approval (measurement-build rule: plan + code approved before launch). The fleet launches only after that approval plus Joe's fresh go. This coordinator's follow-through brief resumes at that launch.
- STATUS: fleet NOT running. Standing by — no launch, no further deletions.
- Detail folded in from the builder's duplicate section before commit (that section removed): the cleanup was executed immediately before the relaunch (Joe's approval 13:37 EDT; pre-delete check found zero fleet/pilot/driver processes; post-delete /tmp available 5,844,172,800 B against the factored requirement 4,687,115,080 B); the FREESPACE line in the launch2 log reads per-tree 468,711,508 B × 8 = required 3,749,692,064 B, available 5,844,172,800 B; the abort line in the runner output is "ABORT: teacher server 18241 not ready".
