# Round 8 — equivalence fix package (staged, not yet committed)

**Ruling:** `claude-reply-e73e682.md` §2 — **BUILD FIX, not a
reclassification.** The phase-3 check is right and was called
wrong: `r3_pair.py`'s `MODE_PREFIX` already carries a `capture`
entry (`"policy: search"`, exactly what the capture rows'
mode line carries), but `run_pilot.sh` named both arms `raw=`,
so every capture row was tested against `"policy: server"` and
failed `mode_ok`. A second reason the failed read could not be
waived: `INVALID_MODE` takes precedence over the classifier in
`r3_pair.py`, so the classifier's own verdict was never
displayed — equal outcomes and zero within-row hits are
necessary for IDENTICAL, not sufficient, and seat 2 was never
played. This package implements the fix and the guarded resume
exactly as §2 specifies. One file changes:
`rounds/round8/code/run_pilot.sh`, sha256 `eff185fd24752130c918bbc1eda0e323a384f780340a0df036bd33de98800cfb`
→ **`0e4febca5f970214c5fc56b707794cf6ce9090e8e99e466d5ee0042513d6eb70`**
(`bash -n` passes; full unified diff in
`fixtures/run_pilot_diff.txt`, 145 lines, five hunks).

## Change 1 — the equivalence read (invocation only)

Old (lines 166–169 of the pre-fix file):

```
(cd "$NATIVE" && $PY r3_pair.py \
   raw="$OUT/equiv_cap_s${seat}.jsonl,$OUT/equiv_cap_s${seat}_log" \
   raw="$OUT/equiv_raw_s${seat}.jsonl,$OUT/equiv_raw_s${seat}_log" \
   > "$OUT/equiv_pair_s${seat}.txt" 2>&1)
```

New (lines 230–233): the capture side is named `capture=` and
listed **first** — `r3_pair.py` pairs against its first named
arm ("Pairs are formed against the FIRST arm listed", its own
docstring), so capture is the base arm, per the ruling:

```
(cd "$NATIVE" && $PY r3_pair.py \
   capture="$OUT/equiv_cap_s${seat}.jsonl,$OUT/equiv_cap_s${seat}_log" \
   raw="$OUT/equiv_raw_s${seat}.jsonl,$OUT/equiv_raw_s${seat}_log" \
   > "$OUT/equiv_pair_s${seat}.txt" 2>&1)
```

Nothing else in the phase changes: same strict parser
(`parse_r3_pair.py --expect-rows 10`), same seeds 12001–12010,
same stop on failure, both seats in the normal flow. A header
note (new lines 56–70) records the fix in the script itself.

## Change 2 — guarded resume mode `PILOT_RESUME=equiv`

New lines 127–169 (step-1 assertions), 184–198 (phase-2 skip),
244–266 (registry merge). Default mode (no `PILOT_RESUME`)
behaves exactly as before apart from Change 1; an unknown
`PILOT_RESUME` value aborts. In resume mode:

1. **Step-1 assertions on the intact capture, before
   containment or any game** — any mismatch prints a
   `PILOT STOP` line and exits: corpus manifest
   `/home/joe/tcg/distill_corpus/corpus_manifest.json`
   sha256 == `edc6e4fbea929f60ec3a157c39a30cb45106ca925f2eb5b42dc45fd4b215ea30`;
   corpus-tree `search.php` sha256 == `044ca8ecbce1aba5fa86d0ea206b8dfece1f431ec0b2df45b4cc75fbc313627d`;
   manifest counts **547 contested + 855 uncontested**; stream
   manifest (`heur_s1.jsonl.manifest.json`) `assert_ok` is true.
2. Containment as in the normal flow (phase 1: G8 sweep first,
   then the (C) sweeper on the native tree).
3. Phase 2 (capture) is **not** re-run — an echo records the
   skip. The Gravy census is not re-run either (it is a
   separate runner; nothing in this script re-invokes it).
4. Phase 3 re-runs **in full, both seats**, seeds 12001–12010,
   with the corrected read. The fresh equivalence game ids
   (all four seat/arm id files) are then merged into the
   do-not-train registry via `merge_registry.py` with tag
   `distill_equiv_eval` — the pilot-registry-merge pattern —
   with the registry's before count + sha256 printed to the
   run log first and the merge tool printing the after count
   + sha256 (plus its timestamped backup and a vault copy
   under `/home/joe/tcg/registry-vault`).
5. Phases 4–7 run exactly as the normal flow runs them (jobs,
   V1 double label, V2 on 100 preserved snapshots with the
   thin count, mechanism z-check, deadline accounting, cost
   reads, teacher-root census).

## The pre-commit dry read — verdict IDENTICAL

Read-only, no games, run on the box 2026-10-25 against the
**existing** seat-1 rows from the stopped run, with the tools
as pinned (`r3_pair.py` on the box hashes `13f95ebe…`, the pin
`run_pilot.sh` asserts; the deployed `parse_r3_pair.py` hashes
`ed47c9cd…`):

- Inputs: `/tmp/distill_pilot/equiv_cap_s1.jsonl` sha256
  `d6521708170f3b740624e40d31bbeb1b9be8e1404f933ee49947a5a669f841d6`
  and `equiv_raw_s1.jsonl` sha256
  `096c9d0352e10681466e91eb649243c09cc569a191a661137b1047ed288b8141`
  — both identical to the pilot report's own record of them.
- Corrected invocation (`capture=…` base, `raw=…`) over those
  rows: **all 10 seeds (12001–12010) read
  `capture vs raw | IDENTICAL | 0 | None | True | True | True | True`** —
  the classifier verdict that `INVALID_MODE` had masked is
  IDENTICAL, with modes ok now True on every row.
- Strict parser output, verbatim (`fixtures/equiv_dryread_s1.parse.txt`):

```
PARSE-PASS: 10 rows, every row IDENTICAL with within-row hits 0, outcome equal True, modes ok True, seat ok True, assert ok True
```

Committed alongside: `fixtures/equiv_dryread_s1.txt` (the full
comparison table, sha256 `55d917e79d50d18d632772a8ffbe71f37bfa308f2cc94c3e9bbade44053be95f`)
and `fixtures/equiv_dryread_s1.parse.txt` (sha256 `533893e796ee8a03d19dc3ab21f08556044dc3d6b2d634c71c2b240abd863523`),
both pulled from the box byte-for-byte (local hashes equal the
box originals).

Scope of the dry read, stated plainly: it covers seat 1 only,
on the stopped run's rows. Seat 2 has never been played; the
resumed run plays both seats fresh on the same seeds, which is
what gives the clean, complete record the ruling asks for.

## What remains

- **Claude's confirmation of this fix commit** (the reply
  approves no run; the fix comes back for a confirmation
  check).
- Then **Joe's go** for the resumed pilot (`PILOT_RESUME=equiv`):
  step-1 assertions → containment → equivalence both seats →
  registry merge → phases 4–7.
- Still owed, unchanged (ruling §4): the **one-capture-per-seed
  declaration** in the corpus launch manifest — with the
  pilot's capture kept, option (a) is the natural one (corpus
  skips 10001–10020 in the heur seat-1 stream;
  `t1_build_data.py` asserts one game id per (stream, seed)) —
  and the **sign-test fix** before the gate (dc22f1d §2). The
  corpus stays gated on Claude's review of the resumed pilot.
