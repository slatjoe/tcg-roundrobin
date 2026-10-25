# Round 8 — W=100 V1 check: ABORTED at the v15 hash pin (defective pin literal in run_w_check.sh)

**Launch:** manifest `rounds/round8/wcheck-launch.md` (repo sha 08ea4bb7), approved build sha a9dd40e2, Joe's Option-1 go recorded 2026-10-25 14:46 EDT.
**Outcome in one line:** the check **did not run**. `run_w_check.sh` aborted during its pre-flight hash pins, before G8, containment, or any labeling: its v15 pin literal is **62 hex characters** — two digits short — so it can never match the checkpoint it guards. The box's v15 file is the correct one (its full 64-char hash is the value recorded throughout rounds 7–8). No games were played, nothing was labeled, and no report reads or report-only additions exist. The fix is a one-literal code change; per the flow it returns as a code commit for the reviewer's confirmation, and the check relaunches on Joe's recorded go. The operator edited nothing and relaunched nothing.

## 1. Launch record

- **Deployed code, verified by sha256sum on the box BEFORE launch** (`/home/joe/tcg/round8_code/`): `distill_label_main.php` = `acf5f4bb3d8b0c7dbbdb3ba1dffa18aeebbde166c07f492ac74a70411e674cc4`; `label_reduce.py` = `25a5f4cc8ad2875e0d3233ae40e09c4ce2c4468befce71e46d575daf2e685399`; `run_w_check.sh` = `9d982a49d580a55d7e9ccb7f3c31fd939ea6765109c80ada9870990d684a82d8` (all three exactly as the task pinned them). The box's `pilot_report.py` (imported by the check's finisher) is the fixed `8255c754…`.
- **Pre-launch state:** `/tmp/distill_wcheck` absent (verified); the source job file `/tmp/distill_pilot_resume/v1_jobs.jsonl` present at 547 lines.
- **Launch:** `bash run_w_check.sh` from `/home/joe/tcg/round8_code`, setsid-detached, 2026-10-25 15:07 EDT; run log `/tmp/r8_launch/wcheck_run.log`, sha256 `3fb4b0571c8e70da4c72392763b3b8479772af2d8066c35018443e5ab79ae37e` — **one line**, the abort below.
- The script created its OUT (`/tmp/distill_wcheck/`, containing only `deployed_code_hashes.txt`, written before the pins) and then aborted. **Closing SHM state: 126 segments** — the pre-launch count, unchanged; the sweepers never started.

## 2. The abort, verbatim, and the diagnosis

The run log's only line:

```
ABORT: v15 hash 0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5e9c82c != 0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5e9c82c
```

The two strings differ in **length**, not in any visible digit — which is why the line reads as a hash disagreeing with itself. Measured on the box:

- **The checkpoint's hash** (sha256sum and an independent hashlib pass agree): `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5e9c82c` — **64 chars**. This is the v15 value recorded since round 7 (the pilot launch record verified the same string).
- **The pin literal in `run_w_check.sh`** (the `expect_hash "$V15" …` call): `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5e9c82c` — **62 chars**. First difference at index 56: the file has `…d67d5d0e9c82c` where the pin has `…d67d5e9c82c` — the pin drops the `d0` at file indices 58–59 and is two characters short overall. No 62-char string can equal a sha256; the pin fails on **every** run, against the correct file.

**Scope of the defect — audited, so the fix can be exact:**

- The literal sits in the **committed** file: the staging tree's `rounds/round8/code/run_w_check.sh` carries the same 62-char literal, and the box copy hash-matches that file (`9d982a49…`). This is not a deployment corruption.
- It is the **only** defective pin in the script. `run_w_check.sh` contains three long hex literals: the production-server pin `81ef2cdb…` (64, correct), the native-featurize pin `f81193e0…` (64, correct), and this v15 pin (62).
- The other runners are clean: `run_label_corpus.sh` and `run_pilot.sh` both carry the full 64-char v15 literal. (The pilot's own step-1 pins passed on the same value at its launches.)
- The confirmation of a9dd40e2 verified the script's file hash and the pin *design*; the literal itself is short, which a file-hash check cannot see.

## 3. What does not exist

No labels, no `wcheck_report.txt` / `wcheck_report.json`, no threshold read, and none of the confirmation's report-only additions (no finished-worlds distribution, no error-reason counts, no W=100 timings or corpus estimate, no sweeper totals — the sweepers never started; closing SHM = 126, above). The PASS/STOP question is untouched: the check's evidence has not been produced, in either direction.

## 4. Disposition (operator's — for the builder and reviewer)

The correction is one literal: the v15 pin in `run_w_check.sh` becomes `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5e9c82c`. Because the script is a confirmed measurement build, the operator made no edit and no relaunch; the fix belongs in a code commit the reviewer confirms, after which the check relaunches under the same manifest and Joe's recorded Option-1 go. A cheap guard for the fix commit, offered for the reviewer's consideration: assert every `expect_hash` literal is 64 hex chars before comparing — a length check would have caught this at the first pin, in the build's own smoke, rather than at launch.
