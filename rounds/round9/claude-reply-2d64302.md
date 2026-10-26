# Claude — confirmation check on the Stage 2 fix pass

**Reviewed commit:** 2d64302f2594f911130ed3530830bd48a1af203c (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-a0599d4.md` hashes to `27a1b7bb…377bfea6`, the value I gave Joe. Every changed file hashes to the amendment's table, and the package doc is `63d613ba…`.

**Verdict: CONFIRMED. Stage 2 is approved to launch on Joe's go**, with launched sha == 2d64302f (or differing only under `rounds/`), pre-gate first.

## 1. Checks

**§2.1, the pre-gate gate: closed.**
- **Placement:** the `PREGATE-GATE` block in `run_stage2_games.sh` sits after the tuple is built and before the G8 sweep and any spawn.
- **What it aborts on:** it aborts unless verdict == `IDENTICAL`, the recorded `search_s2_sha256` == `85490e8e…` and the recorded `teacher_tuple_json` == this run's env string. An absent manifest aborts too, and so does an unset tuple.
- **The writer side, read against the reader:**
  - `run_stage2_pregate.sh` writes the same three keys, and it writes them only after `pregate_check.py` has passed.
  - The verdict is parsed from the checker's `PREGATE: IDENTICAL` line (checker line 148).
  - The tuple builders in the two runners are byte-identical, so the strings match by construction.
  - Both runners resolve the manifest path from the same `${STAGE2_OUT}/pregate`.
- **Fixture:** `fx_s2_blocks` runs the block verbatim against five planted manifests. The pass case proceeds, and the other four (absent, NOT IDENTICAL, wrong hash, a tuple with margin 2.0) abort.

**§2.2, the completed-games rate: closed.**
- **The band population:** completed games are the driver rows with no `invalid` key, and every such row carries `gamename`, because it's set whenever a result exists. The band tallies count only stat rows whose `game` is in that set.
- **The co-report:** the `*_all` tallies sit beside the band tallies.
- **Unchanged:** the tuple audit still covers every row, and `build_s2_jobs.py` is byte-identical, so the L3 population is unchanged.
- **Fixture:** the timed-out game's planted overturn is excluded from the band rate (0.5) and present in the co-report (1.0).

**The §4 notes: done.** The draw = 0 points now print on the outcome line, and `jobs_no_shared_worlds` prints beside `jobs`. Both are fixture-asserted.

**F4: accepted as not implemented.** `rounds/round7/data/pregate/` holds only the two ghost-arm stat files, so there are no raw rows to compare against.

**Fixtures, run here** on a scratch copy: **7 suites, 120 checks, ALL PASS**, with the PASS lines identical to the committed transcript (`99a4cdb7…`).

**Pin audit:**
- The three runners carry 46 literals, all 64 hex characters, with 20 unique values.
- 16 match files at HEAD. The other four are the registered fleet-tree, checkpoint and deck values from my last review.
- The superseded `eb514b4e…` and `3ad70bbc…` are gone.
- `search_s2.php`, `s2_label_main.php`, `settings_stage2.json`, `build_s2_jobs.py` and `pregate_check.py` are unchanged.

**Hygiene:** no `.pyc` is tracked, and I left no cache in the clone.

## 2. Not conditions; for the next time this code is touched

- **The pass manifest is planted.** The gate fixture's passing manifest is planted rather than produced by the pre-gate runner's own manifest writer. I verified writer–reader agreement by reading both, so this is fine for launch. A round-trip case would make it self-proving.
- **A uniqueness guard on game names.** `gamename` is a random 9-digit id, so a collision across 200 games has odds of about 2 × 10⁻⁵. Asserting `len(completed_names) == games_completed` would make the join exact rather than near-certain.

## 3. Launch conditions

1. **Joe's go**, with launched sha == 2d64302f, or differing only under `rounds/`. The launch record states the sha.
2. **Run order:** `run_stage2_pregate.sh`, then `run_stage2_games.sh`, which now refuses to start without an IDENTICAL manifest under this build and tuple, then `run_stage2_l3.sh`.
3. **The standing rules:** the G8 sweep, the per-tree sweepers, the registry merges before analysis, status-only interim notices, and publication of `data/stage2/` with the report, so the read can be recomputed from the repo alone.

**Scope:** this confirms the fix pass and approves Stage 2 at sha 2d64302f2594f911130ed3530830bd48a1af203c (pre-gate, 200 games, L3, read against the registered bands) on Joe's go. Approval certifies the build as written, not the run as executed.
