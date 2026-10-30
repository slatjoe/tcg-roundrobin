# Step 1 pre-gate attempt 2 + pilot — launch facts (staging note, uncommitted)

- Approval: Claude CONFIRMED repair pass 2 (claude-reply-f349b31.md, committed 6c2f42b2). Joe's go: 2026-10-29 16:48 EDT.
- Approved sha: f349b3136220af9d3f420d102ec10800b1148e52
- Launched sha: 6c2f42b24afda472805565e2ff84ff49c4217f9f (differs from approved only by the committed reply file claude-reply-f349b31.md under rounds/)
- Attempt number: 2 (runner-resolved; attempt 1's flat layout under pregate/ untouched)

## Deploy (box: /home/joe/tcg/round10_code/step1/)
Audit of all 18 step1 files: exactly 3 differed from the box copies and were deployed; read-back sha256 on the box matches the repo copies:
- pregate_check_pilot.py 98b3d2ff68e389bf5c76987247329be6233a3230f39391f556b69c66a29d1f46 (box was 671f2c205c…)
- run_pilot.sh c95107314656831b44cce023287a7c8f9862b90f23d61e37a31196dd630ace0e (box was d45d605053…)
- run_pilot_pregate.sh e8741c6b2f896c0e2e35446d33c5baff325bd15b8aca4695fbe98b0250d61cda (box was d1a586bfe…)
The other 15 files were already byte-identical on the box (incl. search_s3_thr.php 4a1936fe…, settings_pilot.json 0571e03a…, search_s3.php 87779e8e…, search_s2.php 1c964160…). Both runners pass bash -n on the box.

## Pre-flight numbers (box, 2026-10-29 ~16:49 EDT)
- /tmp: 20G total, 3,200,778,240 B available before launch. Runner FREESPACE guard: per-tree 468,711,508 B × 5 trees = 2,343,557,540 B; ×1.25 = 2,929,446,925 B ≤ available → PASS (margin ≈271 MB above the 1.25 factor).
- Stale processes: none (only the probe's own ssh line matched).
- SHM segments before launch: 1 (nattch 0); the runner's G8 pre-launch sweep took it to 0.
- Attempt-1 scratch trees /tmp/r10pilot_pg_* (~2.5G) present at launch; the runner rm -rf's and recreates its five scratch trees itself. Nothing was deleted by hand.

## Pre-gate attempt 2 launch
- Launch command: `cd /home/joe/tcg/round10_code/step1 && setsid nohup bash run_pilot_pregate.sh > /home/joe/tcg/r10pilot_out/pregate_attempt2.launch.log 2>&1 < /dev/null &`
- Box launch time: 2026-10-29 16:49:39 EDT (runner pid 769895)
- Output dir: /home/joe/tcg/r10pilot_out/pregate/attempt2/
- Launch log: /home/joe/tcg/r10pilot_out/pregate_attempt2.launch.log
- First-minutes verification (~16:52 EDT): runner alive; both eval servers logged "search model loaded" (srv_s1.log, srv_s2.log); raw phase complete (pg_raw_s1 / pg_raw2_s1 / pg_raw_s2 = 10 rows each); ghost phase starting (SHM segments rising).

## Pre-gate attempt 2 verdict
- pregate_check.txt verdict line: `PREGATE: IDENTICAL` (file present in attempt2/ by 19:55:52 EDT; all four ghost arms 10/10 rows, raw arms 10/10 each; no timeout rows in any arm).
- pregate_manifest.json written (verdict IDENTICAL, attempt 2, search_s3_thr_sha256 4a1936fe…); registry merge ran (tag r10_step1_pilot_pregate). Runner exited cleanly ("PILOT PRE-GATE COMPLETE" in the launch log). Pre-gate wall: 16:49:39 → ~19:55 EDT ≈ 3 h 05 min (the thr arms' early seeds ran 1,338–1,728 s/game; attempt 1 had never measured those seeds' completed walls — they were its timeouts).
- Attempt-2 thr completed walls (rows' secs field): seeds 13001/13002 ran 1,338–1,728 s in both seats.

## Pilot launch — ATTEMPT ABORTED AT PRE-FLIGHT (no games ran)
- Launch command: `cd /home/joe/tcg/round10_code/step1 && setsid nohup bash run_pilot.sh > /home/joe/tcg/r10pilot_out/pilot.launch.log 2>&1 < /dev/null &`
- Box launch time: 2026-10-29 19:56:10 EDT (launcher pid 1156159)
- The pilot's PREGATE-GATE PASSED: launch log line "pre-gate gate: manifest IDENTICAL under this run's search_s3_thr.php pin and tuple - proceeding".
- Then the pilot's own FREESPACE pre-flight ABORTED (verbatim from pilot.launch.log):
  - "free-space pre-flight: required_bytes=3749692064 (per-tree 468711508 x 8 trees) available_bytes=3200053248 headroom_factor=1.25"
  - "ABORT: free-space pre-flight: available_bytes=3200053248 < required_bytes=3749692064 x 1.25"
  - The pilot needs 8 trees (the pre-gate needed 5); factored requirement 4,687,115,080 B vs 3,200,053,248 B available → shortfall ≈ 1.49 GB against the factored requirement (≈0.55 GB against the raw 8-tree bytes).
- State after the abort: no pilot processes; /home/joe/tcg/r10pilot_out/games/ contains only deployed_code_hashes.txt — no games ran, no single-shot state consumed beyond that file. Nothing was deleted.
- /tmp occupants at the abort (du -sh, top): /tmp/distill_wcheck 1.8G and /tmp/distill_pilot_resume 752M (round-8 leftovers, never ordered deleted); the pre-gate's five scratch trees /tmp/r10pilot_pg_raw + pg_ghost{14,thr}_s{1,2} ≈ 2.52G total (attempt 2's outputs all live under /home/joe/tcg/r10pilot_out/pregate/attempt2/; the trees are scratch copies); probe-era trees ≈ 3.0G (r10probe_cap_s1/s2, r10probe_rec_tree_0, r10probe_l3_tree_0-3); /tmp/r9s1_tree_e0/e1 ≈ 1.0G.
- Freeing the five pregate scratch trees alone (≈2.52G) would lift available to ≈5.72G ≥ 4.69G factored → the pilot guard would pass with ≈1.03G to spare. Freeing /tmp/distill_wcheck alone (1.8G) would also cover the shortfall. DECISION PENDING (parent/Joe): no deletion made by the operator.

## Cleanup + pilot relaunch (Joe approved in chat 2026-10-29 20:06 EDT)
- Deleted EXACTLY the five pre-gate scratch trees, nothing else (sizes as du -sb bytes, confirmed before deletion): /tmp/r10pilot_pg_raw 477,894,141; /tmp/r10pilot_pg_ghost14_s1 472,072,223; /tmp/r10pilot_pg_ghost14_s2 471,859,173; /tmp/r10pilot_pg_ghostthr_s1 472,072,223; /tmp/r10pilot_pg_ghostthr_s2 471,439,340. NOT touched: /tmp/distill_*, probe-era trees, round-9 trees.
- /tmp free space: 3,200,053,248 B before → 5,844,172,800 B after (freed 2,644,119,552 B on the df measure). No pilot/pregate processes were running at cleanup time.
- Relaunch command: `cd /home/joe/tcg/round10_code/step1 && setsid nohup bash run_pilot.sh > /home/joe/tcg/r10pilot_out/pilot.launch2.log 2>&1 < /dev/null &` (fresh log name pilot.launch2.log so the first attempt's abort record in pilot.launch.log stays intact).
- Box relaunch time: 2026-10-29 20:06:42 EDT (runner pid 1156718).
- First-minutes verification (from the box): the pilot's PREGATE-GATE passed again ("manifest IDENTICAL under this run's search_s3_thr.php pin and tuple - proceeding"); the FREESPACE pre-flight PASSED (required_bytes=3749692064, available_bytes=5844172800, headroom_factor=1.25); G8 sweep took SHM segments 1 → 0; run_pilot.sh block processes alive and play_game.php teacher games running (seed 25001, both seats, Gravy mirror, --policy-search) within ~2 minutes of launch. TEACHER_TUPLE_JSON verified in the live play_game processes' environments (pids 1156988/1156989, both seats): {"deadline_s": 180, "hooks": 8000, "horizon": 62, "horizon_value": -1, "k": 25, "margin": 1.5, "name": "H8k-180+H"} — the registered pinned tuple, matching pregate_manifest.json. Block stdout confirms the eval server identity (Gravy v10 checkpoint ckpt_v10.pt, correct learner seat per arm). At 20:22 EDT (~16 min in): 73 play_game processes alive, 80 SHM segments (rollout caches active), live game dirs' gamestate.txt files updating within the last 3 minutes, the pilot's scratch trees built under /tmp (free space 3,742,924,800 B with all 8 trees in place). Completed game rows: 0 at 20:22 — consistent with the measured thr wall distribution (attempt-2 early seeds ran 1,338–1,728 s/game); first completions expected shortly after. Monitoring continues to the terminal state.
