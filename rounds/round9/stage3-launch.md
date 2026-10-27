# Round 9 — Stage 3 LAUNCH RECORD

**Joe's go:** 2026-10-27 08:01 EDT (in chat, with tracker —
F-S3-3 answered yes). **Approved sha:** `fdd68d64` (Claude's
confirmation, `3cb82748`). **Launched sha:** `3cb82748` —
differs from the approved sha only under `rounds/` (the
confirmation reply and this record). **Build:** the fix-pass
package at `fdd68d64`; deployed hashes read back on the box
match the staging tree for all 15 package files (launch
manifest, below).

**Deploy:** the eight Stage 3 files were copied to
`/home/joe/tcg/round9_code/` and read back matching
(`settings_stage3.json` `34337753…`, `g8_sweep2.sh`
`d49981ca…`, `run_stage3_games.sh` `db89f107…`,
`stage3_games_report.py` `fe313d09…`, `stage3_analyze.py`
`0e39fee3…`, `run_stage3_l3.sh` `2588d595…`,
`build_s3_jobs.py` `fabecae5…`, `stage3_attr_analyze.py`
`788cd28a…`); the reused pinned files already on the box
re-verified at their registered values (`search_s2.php`
`85490e8e…`, `s2_label_main.php` `c7a76af4…`,
`paired_driver_gravy.py` `3389b1b9…`, `merge_registry.py`
`13a655e3…`, `stage0_report.py` `5c7e5393…`,
`analyze_l3.py` `16017ffa…`, `shm_sweep.py` `98027a8b…`).
Nothing was missing. Pre-flight: Stage 2's pre-gate manifest
present at `/home/joe/tcg/r9s2_out/pregate/`; no stray sim
processes; the registry at its post-Stage-2 state (6,531
games, `031b3c5d…`).

**Launch manifest:** `/home/joe/tcg/r9s3_out/
stage3_launch_manifest.json` — written before attempt 1
(sha256 `d91f1d4e…`), updated in place after attempt 2 with
the attempts record (sha256 `cddb44c2…`).

## Attempt 1 — aborted at the free-space pre-flight

Launched 2026-10-27 08:03:29 EDT (pid 1343589; log
`/home/joe/tcg/r9s3_out/games_launch.log`, three lines).
The PREGATE-GATE passed — Stage 2's manifest IDENTICAL
under this run's pin and tuple — and then the runner's own
free-space pre-flight refused: `required_bytes=3749692064`
(per-tree 468,711,508 × 8 trees) against
`available_bytes=3215175680`, short of even the raw
requirement before the 1.25 headroom. Nothing was copied or
spawned. This is the pre-flight doing the job it was built
for after Stage 2's mid-copy disk-full abort: a sized
refusal before any work, not a partial tree during it.

## Cleanup — verify-then-delete

/tmp is a 20 GB tmpfs (RAM) on the box; it carried ~17 GB
of scratch trees from closed rounds. Each candidate was
verified on the box before deletion: (a) a Talishar tree
copy, (b) its round/stage closed with data published,
(c) no live process referencing it (bracket-camouflaged
/proc scan), (d) newest file predating 2026-10-27 08:00
EDT. Deleted (sizes by `du -sb`): `/tmp/r9s0_fx7`
940,330,988; `/tmp/harvest` 597,703,457;
`/tmp/r9s1_cap_s1` 475,490,538; `/tmp/r9s1_cap_s2`
475,408,885; `/tmp/r9s1_tree_e2` 468,633,952;
`/tmp/r9s1_tree_e3` 468,633,952; `/tmp/r9s2_l3_tree_0..3`
468,643,474 each — total reclaimed 5,300,775,668 B;
available went 3,215,175,680 → 9,080,950,784 B.
**Skipped, left untouched:** `/tmp/distill_wcheck`
(1,845,812,615 B) and `/tmp/distill_pilot_resume`
(740,110,317 B) failed property (a) — flat run-output
directories, not tree copies. Nothing else in /tmp was
touched.

## Attempt 2 — launched and running

A first invocation at 08:08:55 EDT died inside setsid —
`Permission denied`: the deployed runner's mode is
`-rw-rw----` (no execute bit). The runner never started;
the output is preserved at
`/home/joe/tcg/r9s3_out/games_launch2_execfail.log`.
Relaunched through `bash` (attempt 1's interpreter form):
**2026-10-27 08:09:25 EDT, runner pid 1346456**, log
`/home/joe/tcg/r9s3_out/games_launch2.log`.

First-minutes verification, all from box state:
(a) PREGATE-GATE proceeding line present; (b) FREESPACE
passed (`available_bytes=9080950784`); (c) G8 sweep clean
(segments 15 → 0); (d) both teacher servers loaded
`ckpt_v10.pt` on cuda (`srv_s1.log`, `srv_s2.log`);
(e) 4 teacher block drivers running — t1a/t2a on seeds
23001–23100, t1b/t2b on 23101–23200, seats split, timeout
3214; (f) stat rows flowing in all four blocks' logs, a
JSON-level audit of every row showing 0 bad stamps (each
`setting` = the H8k-180+H tuple with `pinned: 1`);
(g) no ABORT in the launch log or server logs. /tmp at
6,980,968,448 B available with the eight trees in place.

**Run order from here (the runner's own):** teacher phase
→ raw phase → RAW-RERUN → registry merge → games report →
the Δ read (`/home/joe/tcg/r9s3_out/games/stage3_read.json`
/ `.txt`); then `run_stage3_l3.sh` (attribution) is
launched when the games complete. **Tracker:** the Stage 3
Tracker artifact + its 10-minute poller are live; its phase
rule is the amended one ("complete" only on
`stage3_read.json` + the L3 manifest).
