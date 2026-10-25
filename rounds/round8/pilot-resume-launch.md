# Round 8 — resumed pilot launch manifest

**Parent:** 60b20a20 (Claude's confirmation of the equivalence fix).
**Approved build sha:** be2fae47 (fix confirmed in `claude-reply-be2fae4.md`).
**Authorization:** Joe's go, recorded 2026-10-25 12:09 EDT ("Go when ready") — banked for this launch; no re-ask per the confirmation's scope.

## What launches

`run_pilot.sh` (sha256 `0e4febca…`) in resume mode, **`PILOT_RESUME=equiv`**, on the box:

1. Step-1 assertions on the intact capture (corpus manifest `edc6e4fb…`, corpus `search.php` `044ca8ec…`, 547 contested + 855 uncontested, stream `assert_ok` true) — any mismatch stops the run.
2. Containment: standing G8 sweep (clears the 20 residual segments), then the (C) sweeper on the native tree.
3. Equivalence phase re-run **in full, both seats**, seeds 12001–12010, corrected read (`capture=` base arm); the 40 fresh game ids merged under tag `distill_equiv_eval`. The report must show the merge output **`added` = 40, `dup_same` = 0** and **both seats' parse lines**.
4. Phases 4–7 as registered: label jobs, V1 double label (V1-ov / V1-conf), V2 on 100 preserved snapshots **with the V2 thin count printed beside V2**, mechanism z-check, deadline accounting, cost reads over the pilot's label jobs, teacher-root census.

## Launch condition (confirmation §2) — PILOT_OUT

`paired_driver.py` resumes from its `--out` file and would skip seeds already present, so the resume launches with **`PILOT_OUT=/tmp/distill_pilot_resume`**, a directory that **does not exist before launch** (absence verified and recorded by the operator in the launch record). Everything the resume reads (corpus, trees, preserved V2 set) lives outside `$OUT`; the stopped run's directory `/tmp/distill_pilot` stays untouched as its record.

## Not launched

The corpus (gated on Claude's review of this pilot), T1, the gate. Queued for the next code commit (per the confirmation): resume mode refuses to start if `$OUT` already holds `equiv_*` files; the corpus one-capture-per-seed declaration (option (a)); the sign-test fix before the gate.

Results are staged as a pilot report (resumed) for the builder's audit and a records commit; interim monitoring is not evidence.
