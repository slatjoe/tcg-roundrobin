# Round 8 — report-phase fix package (staged, not yet committed)

**Disposition:** `claude-reply-8f834d2.md` — fix `pilot_report.py`
per its §2, add the report-only re-entry `PILOT_RESUME=report`
per §3 with the input hashes pinned, publish the report phase's
inputs (§3), record the registry normalization (§4), and add
the outstanding equiv-mode `$OUT` guard (§5). The disposition
approves the re-run itself; per the hub flow it runs on Joe's
go, and the reviewer reads this fix together with the re-run's
outputs. Nothing in this package was run against the pilot's
data: the only executions were `py_compile`, a synthetic-row
fixture test of the new accessor, and extracted-snippet tests
of the shell guards (below).

## A. pilot_report.py — the by-id accessor (§2)

`45b557418c0517d4dd06562c17460e5fe8923c1d926e17788a33eaf54f85ad94`
→ **`8255c75406e810c533d0c64cceae31f7ce3e154887624eea7d84f39b7801ab39`**
(full diff: `fixtures/pilot_report_diff.txt`, 79 lines).

**Diagnosis, as corrected by the disposition:** the live stat
rows' `means` / `n_worlds` are **always keyed by candidate
id** — `DecideInner` builds them per selected candidate id,
and PHP's `json_encode` emits a JSON list only when those keys
are exactly 0..n−1, an object with string keys otherwise. A
list row is one whose `selected` is `[0, 1, …, n−1]`; the old
line 182 (`t["means"][pos]`, enumerate position) was right
only by coincidence on those rows and raised `KeyError` on
the first dict row.

**The fix:**
- `live_by_id(row, field, ci, row_name)` (new line 115) — the
  ONE accessor for every live-side read of `means` and
  `n_worlds`: `v[ci]` for a list value, `v[str(ci)]` for a
  dict.
- `assert_live_shape(row, row_name)` (new line 100) — for
  every list-shaped `means` or `n_worlds`, asserts the row's
  `selected == list(range(len(value)))`; on failure raises
  `SystemExit` naming the row (snapshot id). The accessor runs
  it on every call, and `main()` additionally runs it over
  **every** truth row (new line 212) before the mechanism
  loop, so the PHP-collapse reading is proved on all 56 list
  rows, not only the ones the z-loop touches.
- The mechanism loop (new lines 222–223) reads
  `live_by_id(t, "means", ci, s)` / `live_by_id(t, "n_worlds",
  ci, s)`; the enumerate position is gone.

**Grep audit** (every read of the live rows' `means` /
`n_worlds` / `priors` in both files):

*pilot_report.py* —
- old lines 182–183, `t["means"][pos]` / `t["n_worlds"][pos]`:
  the crash site; **changed**, routed through the accessor.
- lines 224–226 (`lab.get("means")`, `.get("sds")`,
  `.get("n_worlds")`, all `.get(str(ci))`): **labeler** rows,
  not live rows — the labeler emits id-keyed dicts by
  construction and these already read by id. **Cleared, no
  change.**
- No read of a live `priors` field exists in the file (the V1
  section reads label files' scalar `overturn` / `teacher_pick`
  only). **Cleared.**

*pilot_prep.py* — exactly four reads, all wholesale pass-through
copies into output records; none indexes any of the three
fields, positionally or by id:
- line 70: `"priors": r["priors"]` (v1 job record)
- line 140: `"priors": s["priors"]` (v2 job record)
- line 147: `"means": s["means"]` (v2 truth record)
- line 148: `"n_worlds": s["n_worlds"]` (v2 truth record)

The by-id interpretation happens at read time in
`pilot_report.py`, where the accessor now lives, so
**pilot_prep.py is unchanged** (sha256 `3131264b…`, as pinned);
`fixtures/pilot_prep_diff.txt` is a note stating this.

**Verification of the fix:**
- On the box, the assert was checked against the real truth
  file before the design was finalized: 100 rows; `means` and
  `n_worlds` shapes agree per row (56 list / 44 dict);
  **0 violations** of `selected == list(range(len(v)))` on
  list rows, and every dict row carries all its selected ids.
  The assert will not false-fire on the re-run's inputs.
- Synthetic fixture test (invented rows only, no pilot data):
  list row reads by id; dict row with a gap (`selected
  [0, 1, 3]`) reads candidate 3 — the old code's crash case;
  a violating list row (`selected [0, 2]`, means length 2)
  aborts with `ABORT: live means list-shape assert failed for
  row fake_bad: selected [0, 2] != list(range(2))`.
- `python3 -m py_compile` passes on both files.

## B. run_pilot.sh — PILOT_RESUME=report + the equiv guard (§3, §5)

`0e4febca5f970214c5fc56b707794cf6ce9090e8e99e466d5ee0042513d6eb70`
→ **`620cab683b87baaa4d1c2fd5ef87c128a9b65a43196877619b22ad022b6b3559`**
(full diff: `fixtures/run_pilot_diff2.txt`, 135 lines, 3 hunks;
`bash -n` passes).

- **Mode validation moved up** (new lines 117–122): `RESUME`
  is now defined and validated next to `expect_hash`, before
  the standing pins; `"equiv"` and `"report"` are the known
  modes, anything else aborts. The equiv step-1 assertions are
  unchanged at their existing location.
- **Report branch** (new lines 123–170), placed before the
  standing pins and phases 1–5, exiting at its end — so
  containment, capture, equivalence, jobs and labeling are
  **unreachable** in this mode: no games, no labeling, no
  capture. In order, it:
  1. Asserts the nine §3 input hashes in `$PILOT_OUT` (taken as
     given; the gated re-run targets
     `/tmp/distill_pilot_resume`): `labels_v1a.jsonl`
     `789112b7…`, `labels_v1b.jsonl` `9f106275…`,
     `labels_v2.jsonl` `6b20cdfe…`, `pilot_v2_truth.jsonl`
     `53f3fc4b…`, `timings_v1a.jsonl` `d96a1131…`,
     `timings_v1b.jsonl` `c2a44261…`, `timings_v2.jsonl`
     `4030f755…`, `pilot_times.jsonl` `b07f21d1…`,
     `pilot_cand_times.jsonl` `50850c7c…` (full values in the
     script; they are the box files' own sha256s, and the same
     values as the published manifest in §D). Any mismatch —
     or a missing file — prints `PILOT STOP` naming the file
     and exits 1. (`pilot_times.py` is NOT re-run: its two
     outputs are pinned inputs, per §3's list; the disposition
     names `pilot_report.py` and phase 7 as the re-run.)
  2. Runs `pilot_report.py --out "$OUT"`, overwriting the
     crashed run's 0-byte `pilot_report.txt`.
  3. Runs phase 7, the teacher-root census, **verbatim** as
     the normal flow's phase 7 (same probe-tree build, same
     `b2fa1ffe…` featurize pin, same tally) on the pilot's
     roots — the `v1_jobs.jsonl` / `v2_jobs.jsonl` already in
     `$OUT` from phase 4 (not among the §3 pins; stated here
     so the dependency is on record).
- **Equiv guard (§5)** (new lines 219–226): `PILOT_RESUME=equiv`
  refuses to start if `$OUT` already holds `equiv_*` files —
  `ABORT … use a fresh PILOT_OUT`, exit 1 — closing the
  `paired_driver.py --out` resume trap of claude-reply-be2fae4
  §2 for future runs. (The completed resume already satisfied
  the underlying condition via its fresh `PILOT_OUT`.)

**Functional tests of the new shell code** (the file's own
text, extracted; `bash -n` on the whole script separately):
- the assertion loop against the staged published inputs:
  `report mode: 9 report-phase inputs pinned ok`;
- the same loop with one byte appended to `labels_v2.jsonl`:
  `PILOT STOP: report-mode input labels_v2.jsonl hash 618f0b8a…
  != pinned 6b20cdfe…`, exit 1;
- the equiv guard against an `$OUT` holding an `equiv_*` file:
  the ABORT line, exit 1, no fall-through;
- the guard against a clean `$OUT`: falls through silently.

## C. Registry normalization record (§4)

`rounds/round8/registry-normalization-record.md`: the 20 ids,
their old value (the dict `{"tag": "distill_equiv_eval",
"source": "round8 pilot capture-equivalence check, seeds
12001-12010"}`, read back from the pre-normalization vault
copy), the new value (the string `"distill_equiv_eval"`), the
before hash `a921be49…` → after hash `28b5acfa…`, both vault
backups named and hash-verified on the box, and the going-
forward rule: **one value shape — the tag string**.

## D. Published inputs (§3)

`rounds/round8/data/pilot/` holds the 15 files, copied from
`/tmp/distill_pilot_resume` on the box, with
`MANIFEST.sha256` in sha256sum format. **Every staged copy's
sha256 equals its box original** (`sha256sum -c
MANIFEST.sha256`: 15/15 OK) — the list: the three label files,
the truth file, the three timings files, `pilot_times.jsonl`,
`pilot_cand_times.jsonl`, and the six V1/V2 split job files.
Two of the job files (`jobs_v1a_p2.jsonl`, `jobs_v1b_p2.jsonl`)
are 0 bytes (sha256 `e3b0c442…`): the pilot capture's contested
states are all player-1 decisions, so the player-2 splits are
empty — published as they stand. These inputs let the reviewer
recompute V1-ov, V1-conf, V2, the two-proportion test and the
z-check independently, as he did for round 7's fleet.

## What remains

- **The re-run itself**, on Joe's go (approved in the
  disposition): deploy the fixed `pilot_report.py` +
  `run_pilot.sh` to `/home/joe/tcg/round8_code`,
  `PILOT_RESUME=report PILOT_OUT=/tmp/distill_pilot_resume` —
  producing `pilot_report.txt` (COST, V1-ov, V1-conf, V2 + the
  two-proportion test, the mechanism z summary, the deadline
  accounting, thin counts) and phase 7's
  `root_census_tally.txt`. The reviewer reads the fix and the
  outputs together and rules on the pilot.
- Still owed, unchanged: the **corpus one-capture-per-seed
  declaration** (option (a): skip 10001–10020 in the heur
  seat-1 stream, keep the pilot capture and run A's labels,
  assert one game id per (stream, seed)) in the corpus launch
  manifest, and the **sign-test fix** before the gate. The
  corpus stays gated on the reviewer's pilot ruling.
