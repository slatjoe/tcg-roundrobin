# Round 8 — resumed pilot report: equivalence IDENTICAL on both seats, all labeling complete; the run STOPPED in its final phase — `pilot_report.py` crashed at the mechanism z-check

**Launch:** manifest `rounds/round8/pilot-resume-launch.md` (repo sha 969d61cf), approved build sha be2fae47, Joe's go recorded 2026-10-25 12:09 EDT.
**Outcome in one line:** the resumed pilot ran clean through step-1 assertions, containment, the equivalence re-run (**IDENTICAL on both seats**, strict parse), the registry merge (**+40 new, 0 duplicates**), and all labeling (**1,194 labels written, 0 thin**); it then **stopped in phase 6** when `pilot_report.py` crashed with `KeyError: 1` in the mechanism z-check, before writing any of its derived reads. Phase 7 (teacher-root census) did not run. Every underlying artifact is intact on the box; nothing was patched or re-run by the operator.

## 1. Launch record

- **Mode:** `PILOT_RESUME=equiv`, `PILOT_OUT=/tmp/distill_pilot_resume`, setsid-detached; run log `/tmp/r8_launch/pilot_resume_run.log`, sha256 `9943d983c68b85ce31b94ffa87c13f094e696092c1dd7259c30a96743e1ad135`.
- **PILOT_OUT absence, verified and recorded before launch:** `2026-10-25 12:20:44 EDT — ABSENT: /tmp/distill_pilot_resume does not exist` (`test ! -e`). The stopped run's directory `/tmp/distill_pilot` was not touched.
- **Deployed code:** on the operator's arrival the box copy at `/home/joe/tcg/round8_code/run_pilot.sh` still carried the pre-fix hash `eff185fd…`; the staging tree's fixed script was deployed and verified before launch: **`0e4febca5f970214c5fc56b707794cf6ce9090e8e99e466d5ee0042513d6eb70`**. The run's own deployment record: `/tmp/distill_pilot_resume/deployed_code_hashes.txt`, sha256 `af466e3a4cb1b6e626e29872d68e7485b1d196e6120b241b6533d03fd2e0103e`.
- **Step-1 assertions — PASSED** (run log, verbatim): `resume step 1 ok: corpus manifest pinned (hash + counts 547 contested + 855 uncontested), stream assert_ok true, corpus search.php pinned`. The capture phase was not re-run.
- **Containment:** G8 sweep in the resume took segments **20 → 0** (run log: `segments before: 20 (nattch=0: 20, attached: 0)` … `segments after: 0`); the (C) sweeper ran alongside on the native tree (log `/tmp/distill_pilot_resume/shm_sweep.log`). **Closing state: 62 segments (nattch=0) remain** after the run's exit — the next launch's G8 is the standing clearing step, as before.

## 2. Equivalence re-run — IDENTICAL, both seats

Fresh games on seeds 12001–12010 in the new `$OUT`, read with the corrected invocation (`capture=` base arm). Both seats' strict-parse lines, verbatim:

```
seat 1 (equiv_pair_s1.parse.txt): PARSE-PASS: 10 rows, every row IDENTICAL with within-row hits 0, outcome equal True, modes ok True, seat ok True, assert ok True
seat 2 (equiv_pair_s2.parse.txt): PARSE-PASS: 10 rows, every row IDENTICAL with within-row hits 0, outcome equal True, modes ok True, seat ok True, assert ok True
```

All 20 table rows (10 per seat) read `capture vs raw | IDENTICAL | 0 | None | True | True | True | True`. The two table files hash identically (`55d917e79d50…`) because every reported cell agrees across seats; the underlying row files differ (seat-1 raw rows 5,308 B, seat-2 5,307 B) — different games, same verdicts. Fresh game ids: `equiv_cap_s1_game_ids.txt` `ab794e7d…`, `equiv_raw_s1_game_ids.txt` `8896dc0d…`, `equiv_cap_s2_game_ids.txt` `9a0c0645…`, `equiv_raw_s2_game_ids.txt` `33e1a415…`.

**Registry merge (run log, verbatim):**

```
registry before merge: n_games=6181 sha256=95a4580ad9c714783af0d2f2349ed7274479abc0694e70098b9500fb7cb6f300
merged: +40 new (tag distill_equiv_eval), 0 already under this tag; n_games=6241
backup: /tmp/harvest/do_not_train_registry.json.bak-20261025T122226
registry sha256: a921be4954c6de0804ee23a7f67a6cbc124013c614e26db1254cbec2b4bda927
vault copy: /home/joe/tcg/registry-vault/do_not_train_registry_20261025T122226.json
```

**added = 40, dup_same = 0**, as the launch condition requires. Registry after: **6,241 games, sha256 `a921be4954c6de0804ee23a7f67a6cbc124013c614e26db1254cbec2b4bda927`** (the vault copy hashes identically).

## 3. Labeling — all jobs produced (artifact facts)

`pilot_times.py` completed over the whole labeling program (run log): **`timed job-runs: 1194; candidate batches: 3504`**.

| set | jobs | labels written | thin file |
|---|---|---|---|
| V1 run A (seed base 555001) | 547 | `labels_v1a.jsonl` — 547 lines, sha256 `789112b77e5b…` | `thin_v1a.jsonl` empty |
| V1 run B (seed base 777001) | 547 | `labels_v1b.jsonl` — 547 lines, sha256 `9f1062750ca4…` | `thin_v1b.jsonl` empty |
| V2 (100 preserved snapshots) | 100 | `labels_v2.jsonl` — 100 lines, sha256 `6b20cdfe5d86…` | `thin_v2.jsonl` empty |

- **Thin labels: 0 in every set** — the V2 thin count is **0** and the overall label thin count is **0**, as produced by the labeler (the report phase's own thin/excluded accounting never printed; see §4).
- Supporting artifacts: `pilot_v2_truth.jsonl` sha256 `53f3fc4b8e42…`; `timings_v1a.jsonl` `d96a113133b6…`, `timings_v1b.jsonl` `c2a442611811…`, `timings_v2.jsonl` `4030f7551a4d…`; `pilot_times.jsonl` `b07f21d136f2…`; `pilot_cand_times.jsonl` `50850c7cc74b…`.

## 4. THE STOP — `pilot_report.py` crashed in the mechanism z-check

At 13:48 EDT, after all labeling and after `pilot_times.py`, the report generator died. The run log's final lines, verbatim:

```
Traceback (most recent call last):
  File "/home/joe/tcg/round8_code/pilot_report.py", line 245, in <module>
    main()
    ~~~~^^
  File "/home/joe/tcg/round8_code/pilot_report.py", line 182, in main
    m_live = t["means"][pos]
             ~~~~~~~~~~^^^^^
KeyError: 1
```

`run_pilot.sh` exited on the failure; `pilot_report.txt` exists at **0 bytes** (sha256 `e3b0c44298fc…`, the empty hash) — the report writes only at the end of `main()`, so **none of the derived reads were produced**: no V1-ov / V1-conf with intervals, no V2 rate or interval, no V2-vs-V1-ov two-proportion test, no mechanism z summary, no deadline accounting, and no cost reads (per-job mean / p95 / max or the corpus estimate). Phase 7, the teacher-root census, did not run (no census artifacts exist in `$OUT`).

**The mechanism, verified from the artifacts.** The crash is in the mechanism check's loop over the V2 truth rows (`pilot_v2_truth.jsonl`, 100 rows). Those rows are heterogeneous in how the live search recorded candidate means: **56 rows carry `means` as a list** (position-indexed over the selected candidates) and **44 rows carry it as a dict keyed by candidate id** (string keys — e.g. row 1, snap `443377021_t2`: `selected [0, 1, 3]`, means keys `'0', '1', '3'`; `n_worlds` is likewise list-or-dict by row). Line 182 indexes with the integer enumerate position, `t["means"][pos]`, which works for the list rows and raises `KeyError` on the first dict row with an unselected candidate at a nonzero position — row index 1, at `pos 1` (its pair is {prior 3, teacher 0}, so candidate 1 is the first unselected) — exactly the reported `KeyError: 1`. (The label side of the same loop already reads by candidate id, `(lab.get("means") or {}).get(str(ci))`; the live side does not.) Whether the truth rows' dict form is itself expected from the gate-era stat rows is the reviewer's to say; what is certain is that the report generator does not handle both forms.

## 5. What this leaves open

- The pilot's registered reads — V1-ov, V1-conf, V2 with its thin count, the mechanism z-check, the deadline accounting, the cost reads and corpus estimate, and the teacher-root census — remain unmeasured. **Every input they need is intact in `/tmp/distill_pilot_resume/`** (labels, truth, timings; hashes in §3), so a corrected report phase re-run against this `$OUT` would produce them without re-labeling. The disposition — a fix to `pilot_report.py` and a re-run of the report phase (plus the census) — is the reviewer's call; the operator patched nothing and re-ran nothing.
- The equivalence question itself is now closed on fresh evidence for both seats (§2), and the registry stands at 6,241 games.
- Still owed, unchanged: the corpus one-capture-per-seed declaration and the sign-test fix; the corpus stays gated on the review of this pilot.
