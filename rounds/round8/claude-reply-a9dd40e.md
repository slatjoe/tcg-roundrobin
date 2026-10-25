# Claude — confirmation of the W = 100 amendment

**Reviewed commit:** a9dd40e2efba3e1b4f137fd2e1ada99a39d4cbb2 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-597d181.md` hashes to `54faf24b…7177e1d10`, the value I gave Joe.
**Package:** `rounds/round8/w100-amendment.md` and the code below. Every hash is verified:

| File | sha256 |
|---|---|
| `distill_label_main.php` | `acf5f4bb…` |
| `label_reduce.py` | `25a5f4cc…` |
| `run_label_corpus.sh` | `a46dae36…` |
| `run_w_check.sh` | `9d982a49…` |

**Verdict: CONFIRMED. The W = 100 V1 check may launch on Joe's recorded Option-1 go** (2026-10-25 14:46 EDT).

## Checks

- **The labeler:**
  - `LABEL_W` must be a positive integer (anything else exits 2), defaulting to 25
  - every job must carry `W` equal to the pin; a mismatch or a missing value aborts before any labeling
  - every raw row records `W`
  - the `$cfg` passed to `SimLabel_RunForSnapshot` takes `"W" => $W`
  - the decision path is untouched
- **The reducer:**
  - `W` is read from the rows
  - a non-integer, a bool or a mixed width aborts
  - it's stamped on labels, thin rows and counts
  - the arithmetic is unchanged; the "20" is the registered finished-worlds floor, not W, as the docstring says
- **The corpus runner:** defaults to 100 and records it in the manifest. Not run.
- **`run_w_check.sh`:**
  - the 547 pilot states × 2 at bases 555001 and 777001
  - the corpus-exact 4-tree sharding, with tree, server and v15 pins
  - G8 first, then (C) per tree
  - no games
  - V1 computed with the pilot's own arithmetic
  - the registered threshold (**V1-ov ≥ 0.50**) printed last, with PASS or STOP
- **The smoke** (one job: 300 rows, 100 finished per candidate, W = 100 throughout, and both pin violations aborting with no rows): accepted from the note.

**One fact for the record, harmless:** world seeds are `base + ji·100003 + w·31337`, so the W = 100 run A's first 25 worlds on each state coincide with the pilot's W = 25 run A worlds. A and B at W = 100 remain independent of each other, which is all V1 needs.

## Report-only additions to the W-check report

At W = 100, each candidate forks 100 children together against the label path's 300 s deadline, and grouped mode doesn't record kills directly. So the report should also carry:
- **The finished-worlds distribution per candidate,** computed from the labels' `n_worlds`: the minimum, the share below 100, and the share below 80. Add the raw rows' error-reason counts, which include deadline kills.
- **The cost:** per-job mean, p95 and max from the labeler's own `secs` lines, and the corpus estimate at W = 100 from them.
- **SHM:** the sweepers' totals (selected, deleted, failed, unattributed) and the closing count.

None of these changes the PASS/STOP read.

## Bookkeeping

**The resume guard: struck from the owed list.** It shipped in 9093f6d1 (report-fix §B: `PILOT_RESUME=equiv` refuses an `$OUT` that already holds `equiv_*` files, and is tested both ways). I missed it in my 597d181 §5. Still owed before their stages:
- the **option-(a) one-capture-per-seed declaration**, in the corpus manifest, with the pilot's W = 25 run-A labels superseded at W = 100
- the **sign-test fix**, before the gate

**Scope:** this confirmation approves `run_w_check.sh` at sha a9dd40e2efba3e1b4f137fd2e1ada99a39d4cbb2 under Joe's recorded go. It plays no games. On **PASS** (V1-ov ≥ 0.50), the corpus launch at W = 100 comes to Joe's go, with the option-(a) declaration in its manifest and my review of the W-check report first. On **STOP**, it comes back for decision. Approval certifies the build as written, not the run as executed.
