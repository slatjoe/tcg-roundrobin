# Claude — confirmation of the W-check pin fix

**Reviewed commit:** af89615ee9071b2c63c471bd71cb620644415514 (HEAD verified after checkout; clean tree; equal to `origin/main`). This covers 0e4c285 (`wcheck-report.md`, the aborted pre-flight) and af89615 (`wcheck-fix.md`, the fix). I also read the launch manifest `wcheck-launch.md` (08ea4bb). `run_w_check.sh` hashes to **`489bf845…9fad425a`**.

**Verdict: CONFIRMED. The W-check may relaunch under manifest 08ea4bb7 on Joe's recorded Option-1 go.**

## Checks

**The diff is exactly two hunks:**
- **(1)** the v15 literal becomes `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c`. That's the value registered in build-package §1, and it's string-identical to the literal in the other six round-8 runners that pin v15.
- **(2)** a `^[0-9a-f]{64}$` guard at the head of the shared `expect_hash`, aborting with the pin's name and length

**A full literal audit, run here rather than taken from the note:**
- every hex run of 32 or more characters in `rounds/round8/code/` is **exactly 64** characters (59 occurrences)
- every **distinct** 64-character pin in the code traces to a reviewed document. The nine that appear only as prefixes in the reports (the pilot report-mode input pins in `run_pilot.sh`) match `rounds/round8/data/pilot/MANIFEST.sha256` in full.

**The abort was the guards working.** A wrong literal can only cause a false abort, never a false pass. Pin checks fail safe, and this one did: nothing ran, SHM was unchanged, and nothing was improvised. Reporting it before touching the file was right.

## My miss, and a standing addition to my checks

My a9dd40e confirmation verified file hashes and the pin design, but not the **literals inside** the files. A file hash can't see a wrong constant in the file it covers. From now on, every code confirmation of mine includes the audit above: every pin literal's length, and its match to a registered value.

## Before the corpus launch

Bring the same length/format guard into **`run_label_corpus.sh`**, as your note says, and into the other runners that still have the unguarded compare (`run_capture_corpus.sh`, `run_distill_pregate.sh`, `run_distill_gate.sh`, `run_pilot.sh`, `run_gravy_census.sh`). It's a clarity fix, not a safety one: an unguarded wrong pin still aborts, just with a less direct message. It can ride the corpus code commit, together with:
- the **option-(a) one-capture-per-seed declaration** and its duplicate assert
- the **sign-test fix**, before the gate

**Scope:** this confirmation approves `run_w_check.sh` at sha af89615ee9071b2c63c471bd71cb620644415514 (`489bf845…`) for the W = 100 V1 check under manifest 08ea4bb7, with the report-only additions from my a9dd40e reply. It plays no games. On PASS, the corpus comes to Joe's go after my review of the W-check report. On STOP, it comes back for decision. Approval certifies the build as written, not the run as executed.
