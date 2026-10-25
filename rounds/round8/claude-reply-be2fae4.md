# Claude — confirmation check on the equivalence fix

**Reviewed commit:** be2fae473656d265190b9271a521d9c91d8c5556 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-e73e682.md` hashes to `433890c2…a494e40574`, the value I gave Joe.
**Package:** `rounds/round8/equiv-fix.md`, `code/run_pilot.sh` (`0e4febca…`, verified), and the fixtures.

**Verdict: CONFIRMED, with one launch condition (§2). The resumed pilot may launch on Joe's recorded go, under that condition.**

## 1. Checks

- **The read:** `capture=` is the base arm and `raw=` the second, and the diff touches nothing else in phase 3.
- **The dry read:** I ran the committed `parse_r3_pair.py` here on `fixtures/equiv_dryread_s1.txt` and got **PARSE-PASS**. The table shows all 10 seeds as `capture vs raw | IDENTICAL | 0 | None | True | True | True | True`. **The masked classifier verdict is IDENTICAL.** Seat 1's capture play was action-identical to raw v15.
- **The resume mode:**
  - unknown modes abort
  - step 1 asserts the corpus manifest hash (`edc6e4fb…`), the corpus-tree `search.php` (`044ca8ec…`), the counts of 547 contested and 855 uncontested, and the stream's `assert_ok`, before containment or any game
  - phase 2 is skipped, phases 4–7 are unchanged, and the new games are registered under `distill_equiv_eval`

## 2. Launch condition: a fresh output directory

**As written, the resume would not re-run seat 1.** `paired_driver.py` resumes from its `--out` file: lines 256–265 skip every seed already present. The resume uses the same `$OUT` (default `/tmp/distill_pilot`), where `equiv_cap_s1.jsonl` and `equiv_raw_s1.jsonl` from the stopped run already hold seeds 12001–12010. So:
- seat 1 would play **zero** games and silently re-read the old rows
- its ids files would carry the old ids, which `merge_registry.py` counts as same-tag duplicates without comment
- only seat 2 would be fresh

That contradicts "the equivalence phase re-run in full, both seats" in my e73e682 §2 and in your equiv-fix. (The old seat-1 rows are themselves valid and read IDENTICAL, so nothing would be wrong. But the record would claim a fresh run that didn't happen.)

**Condition:** launch the resume with **`PILOT_OUT` set to a new directory that doesn't exist yet** (for example `/tmp/distill_pilot_resume`). The launch manifest records `PILOT_OUT` and shows the directory was absent before launch. Everything the resume reads (the corpus, the trees, the preserved V2 set) is outside `$OUT`, so nothing else changes. The stopped run's directory stays as its record.

**After the run, the report shows:**
- seat-1 and seat-2 game ids that are **new**: `added` = 40, `dup_same` = 0 in the merge output
- both seats' parse lines

**For the next code commit:** make resume mode refuse to start if `$OUT` already holds `equiv_*` files. That isn't needed for this launch, given the condition above.

**Scope:** this confirmation approves the resumed pilot at sha be2fae473656d265190b9271a521d9c91d8c5556, under Joe's recorded go (2026-10-25 12:09 EDT) and the §2 condition. The corpus stays gated on my pilot review, with the one-capture-per-seed declaration still owed. The sign-test fix is still owed before the gate. Approval certifies the build as written, not the run as executed.
