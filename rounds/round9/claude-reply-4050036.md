# Claude — ruling on the Stage 2 analyzer stamp-audit fix

**Reviewed commit:** 4050036701588c9a1f3c607214540592a8b7f7fa (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch record at e8c4b7fa. It differs from the approved 2d64302f only under `rounds/`, and it states launched sha == approved sha.

The committed `claude-reply-2d64302.md` hashes to `c219be3e…cb529`, the value I gave Joe. The changed files hash to the fix doc's §4 table, and the transcript is `82ce580a…`.

**Ruling: FIX CONFIRMED.** The fixed analyzer (`ee4daa88…`) runs **once** against the existing L3 labels, under the conditions in §3. No re-labeling, and no games re-run.

## 1. The diagnosis is right, and it was my miss too

- **The two shapes:** `s2_label_main.php` (line 112) stamps exactly six fields, the six in `settings_stage2.json`'s `label_tuple`. The pre-fix audit expected those six plus `"pinned": 1`, and that key only the live tuple resolver writes (`search_s2.php`).
- **The consequence:** every label row failed on shape. The defect failed safe: an abort before any read, not a wrong read.
- **My share:** I read this audit in the a0599d4 review and accepted "every row is stamped" without checking the reader's key set against the writer's. It's the same species as the planted-manifest note in my last confirmation, and I flagged that one without looking for its twin. The standing rule this adds: **a fixture plants the counterparty's real output, and every writer/reader pair gets a round-trip case.**

## 2. Checks

**The diff.**
- `fixtures/stage2_analyze_diff.txt` applied to the confirmed `9b1a0677…` regenerates `ee4daa88…` byte-identically.
- The only hunk is the audit block. It projects each stamp on `settings["label_tuple"]`'s own keys and compares the result to the registered tuple.
- A wrong value aborts, and so does a missing field (it projects to `None`). Extra keys are ignored.
- The message, the count and exit 2 are unchanged, and the audit still runs before any read.
- **The read code is byte-identical:** the world-count guard, the three scorings, the bands, the tripwires and the impeachment ordering are all untouched.

**The other files.**
- `run_stage2_l3.sh` changes only the analyzer pin literal. It's 64 hex characters and matches the file.
- Every other Stage 2 code file is byte-identical to 2d64302f.

**Fixtures, run here** on a scratch copy: **7 suites, 124 checks, ALL PASS**, with the PASS lines identical to the committed transcript. The new cases:
- the round-trip: genuine `s2_label_main.php` rows go through the analyzer and come out `{rows: 200, bad: 0}`, exit 0;
- real-shape stamps pass;
- `pinned: 1` extras are ignored with the read unchanged;
- a missing field aborts;
- the k = 25 wrong-value case still aborts on the real shape.

**Hygiene:** a clean tree, and I left no cache in the clone.

## 3. Conditions for the analyzer run (Joe's go)

1. **The labels are proven untouched before the run.**
   - **Record:** before deploying, write a pre-run record with the sha256, row count and mtime of every `labels_shard*_p*.jsonl` file, `labels_all.jsonl`, `jobs_all.jsonl`, `jobs_report.json` and `games/games_report.json`.
   - **Expect:** `labels_all.jsonl` holds **35,300** rows, and every mtime predates the abort.
   - **Why:** the aborted runner never wrote `l3_manifest.json`, so this record is the labels' first hash. It goes into the report.
2. **Keep the aborted output.** Preserve the aborted run's `stage2_read.txt` (the ABORT line, no read) as `stage2_read_aborted.txt`, and publish it. It's the evidence that no read existed before the fix.
3. **Run the read only, once.**
   - Deploy `stage2_analyze.py` and the L3 runner, and verify `ee4daa88…` through the runner's own `expect_hash` before use.
   - Run **verbatim the runner's tail from `# --- the read` through the manifest**. Do **not** run the whole runner: it would rebuild the jobs and re-label.
   - The read runs once, and its output is the read.
4. **Publish the data.** Publish `data/stage2/` with the report, as registered: the driver rows, stat logs, snap indexes, labels (gz), jobs, the pre-run record, the aborted read text, `stage2_read.json` and `.txt`, `l3_manifest.json` and the games report. I'll recompute the read, the per-game gain and the rates from those rows independently.
5. **Fix the tracker's phase rule (not a condition for this run).** It should require `stage2_read.json` and `l3_manifest.json`, not just labels present and no runner, before it shows "complete". Until then it says "awaiting read".

**Scope:** this confirms the analyzer fix at sha 4050036701588c9a1f3c607214540592a8b7f7fa and approves one run of the fixed analyzer against the existing Stage 2 labels, under §3 and Joe's go. Approval certifies the build as written, not the run as executed.
