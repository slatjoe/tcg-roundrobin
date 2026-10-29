# Round 10 — Step 0 probe: RECOVERY RUN RECORD (2026-10-29)

Approved build **d17a4540** (Claude's approval, `claude-reply-d17a454.md`, committed 3ef1815a). Launched sha **3ef1815a** — differing from the approved sha only under `rounds/` (the approval reply + the round-9 addendum's basis note). Joe's fresh go: 2026-10-29 08:10 EDT. The run happened **once**, as registered.

**Execution:** deployed from staging to `/home/joe/tcg/round10_code` (22 files; all box read-backs matched staging, including every literal in the script's own `expect_hash` block; the published `data/step0_capalign/` files placed at `/home/joe/tcg/r10probe_published_capalign/`). Launched 2026-10-29 **08:13:05 EDT** (`GTREE=/tmp/gravytree setsid bash run_probe_recovery.sh`, log `recovery_run.log` in `/home/joe/tcg/r10probe_out`).

**Steps, in order — all passed until the influence step:**

1. Pins + preconditions: passed.
2. **Step 0, eval completeness: CLEAN** — 5,253 job lines, 381,625 rows, 5,253 states complete, **missing states 0**, no (job, candidate) count ≠ k; split finished 381,587 / unfinished 38 / refusal 0.
3. **Step 0b, cap-aligned rescoring: reproduced the published reclassification BYTE-FOR-BYTE** — all 7 in-run outputs sha256-identical to `data/step0_capalign/` (86 drop-outs; 69 newly qualifying: 8 uncontested / 32 diag / 29 band; 39 regrouped).
4. Free-space pre-flight: passed.
5. Extraction: the 10 jobs → `jobs_supp.jsonl`.
6. Containment: segments 21 → 0; labeling servers on ckpt_v10.
7. **Family A** (the ten, MEAS_SEED 970,055,001): fixed loader asserted `s2 label jobs=10`; world-count pre-check OK — 10 × 2 × 50 = **1,000 rows**.
8. **Family B** (the 69, MEAS_SEED 470,055,001): loader count asserted; pre-check OK — 69 × 2 × 50 = **6,900 rows**.
9. **Merge:** `jobs_merged.jsonl` 715 jobs (646 verbatim + 69 appended; the ten ride inside the 646); `labels_merged.jsonl` **71,500 rows**.
10. **Analyze (dual read):** cap-aligned grouping excluded the 86 drop-outs; jobs_no_shared_worlds 0 of 715; label rows 71,500 (finished 71,497, unfinished 3, refusals 0); fallbacks 0.
11. **Report: WRITTEN** (`probe_report.txt`/`.json`, 08:26 EDT; full text in `data/step0_recovery/`). **The registered read, cap-aligned primary:** margin lever per-game gain **+0.0076** (lower bound **−0.0067**) — not buildable; **threshold lever per-game gain +0.4734 (lower bound +0.2080)** — buildable; calibration 0.0549 in-band, no flag; **RECOMMENDATION (registered rule): threshold 0.97** — only the threshold's lower bound exceeds 0. As-run co-report beside it (threshold +0.5418, LB +0.2231; margin +0.0062, LB −0.0089; same recommendation). Capture stat rows are stamped `unpinned` **by design** (the capture arm never uses the search tuple; `settings_probe.json`'s `capture.teacher_tuple` is descriptive of the build, not a delivered pin — Claude's §2 condition from the third fix pass confirmation).

12. **Influence: CRASHED — the step never produced output.** `probe_influence.txt` is 0 bytes; `probe_influence.json` was never written:

```
File "/home/joe/tcg/round10_code/probe_influence.py", line 439, in main
    logo_by_lever[lever] = logo
NameError: name 'logo_by_lever' is not defined
```

The name is a `decide_hold` parameter and is assigned at line 439, but **no initialization exists anywhere in the file**, and `fixtures/fx_probe_influence.py` never references it — the L-fixtures exercised `decide_hold` with hand-built inputs; `main()`'s composed LOGO loop was never run end-to-end by any fixture. 13. **Manifest: NEVER RAN** (it sits after the influence step). `recovery_manifest.json` does not exist. The script's single-shot state is consumed: its refusal-list outputs exist, so the script as written refuses a second invocation. Nothing was retried and nothing was patched. The run's outputs stand on the box as produced; no leftover processes; 0 shared-memory segments.

**Status of the read:** the report exists and is published below with the run's outputs, but the registered influence prints (state inspection, LOGO, the hold-rule determination) **do not exist**, so the recommendation is **not final**: under the registered hold rule, if the threshold lever's gain lower bound is ≤ 0 with any single game excluded, the report must carry "buildable, single-game dependent" and the recommendation returns to review before any Step 1 package. The completion (influence + manifest, computed offline from the fetched outputs) is a separate reviewed step.

**Outputs:** `data/step0_recovery/` ( fetched from the box, sha256-verified; `labels_merged.jsonl.gz` raw sha256 `c2688f24…`, 71,500 rows). The recovery manifest and influence outputs will be added there by the completion step, with this record amended.

## Amendment (2026-10-29, the completion)

The influence completion ran **once** on 2026-10-29 (confirmed fdfe37af; approval committed 9aa1dfa0; launched sha 9aa1dfa0, rounds-only difference; Joe's standing go of 08:50 EDT), offline from this record's published outputs, under the fixed probe_influence.py (dc79bdad…) with argument parity to the registered invocation (verified by fixture fx_invocation_parity.py). All in-run pins verified; the inspected-game assertion passed ("inspected game ok: 540261752 is a capture game"). Outputs added to `data/step0_recovery/`: `probe_influence.txt` (d0df2c50…), `probe_influence.json` (faf9f8e1…), `recovery_manifest.json` (bfc30373…), `completion_run.log` (86309cb3…). The manifest carries eval_completeness missing_states 0, the sec14 block, and the completion provenance block; the completion's single-shot state is consumed.

**The hold rule does NOT fire.** Threshold LOGO: full gain +0.4734 (LB +0.2080), range [+0.3259, +0.4863]; the weakest exclusion is the largest carrier, game 635852068 (31.92% share) — with it excluded, gain +0.3259, **lower bound +0.1753 > 0**. `single_game_dependent: []`, `influence_hold_lines: []`. The probe's registered read is complete; the finalized report is `step0-probe-report.md`.
