# Claude — confirmation check on the Stage 0 report fix

**Reviewed commit:** a00dad5030f058a49f1bfc9bfadf3d4e70184c3d (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-2db6b77.md` hashes to `ecb8122b…0c7459`, the value I gave Joe. `code/stage0_report.py` hashes to **`5c7e5393…bb59bf`**.

**Verdict: the fix is CONFIRMED. One defect remains before launch: the runner still pins the old report.** §2 says how to clear it without another review round.

## 1. Checks

- **The taxonomy:**
  - `REFUSAL_CLASSES` = {`canary_hook_failed`, `det_persist_failed`, `det_verify_failed`, `det_verify_hook_failed`}, excluded and tallied
  - every other error, including unlisted ones, counts as unfinished and is draw-priced in the sensitivity read
  - per-class tallies print with their tag
- **The world-count guard** aborts on a short set.
- **The fixtures, run here:** `run_fixtures.py` gives FIXTURES: ALL PASS, and `fx_report_fix.py` gives FX-R1–R5 ALL PASS, including the guard firing at the default (rc 2).
- **FX7-ROWS** ran on the box, from FX7's own rows: pooled unfinished **28/300 = 0.0933** (teacher 0.1067, prior 0.0800; 28 aborts, 0 refusals), with a sensitivity read of 0.0333 against a primary of 0.0324. That's exactly the read I asked for. Accepted from the record.
- **The disclosed deviation** (`--expect-rows` as a parameter, default 50): **accepted.** The runner passes no override, so the launched check is the literal 50. A parameter is also what lets the synthetic fixtures exist at all.

## 2. Before launch: the runner's pin

`run_stage0_l3.sh` (unchanged in this commit) still pins `stage0_report.py` at **`5019d94e…`**, the pre-fix hash (its lines 96–98). At launch, pre-flight would compare it against the deployed **`5c7e5393…`** and **abort**. It fails safe, but it wouldn't run.

**The fix:** change exactly that one pin literal to `5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf`, copied from `sha256sum`, not typed. **This confirmation extends to the commit whose diff against a00dad50 is exactly that single-line change** to `run_stage0_l3.sh`, plus any note under `rounds/round9/`. Its launch manifest records the diff and the runner's new hash. **Stage 0 may then launch on Joe's banked go** without another review round. I'll verify the diff after the fact. Any other change in that commit voids this extension.

## 3. Registered now: a tie-as-loss read for Stage 0 (report-only)

Joe raised it tonight, and it belongs on the record **before** Stage 0's numbers exist. In competition a tie is worth far less than half a win, close to a loss when advancement needs X wins. Stage 0's reads score a draw at 0.5: the instrument's price, and in the horizon pass the turn-62 draws.

**Registered:** after the run, compute a second version of each read (primary and horizon) with **draws scored as losses**. That's world score 0 for `winner == 0`, finished or horizon (`horizon == 1`), instead of 0.5. Do it **offline from the published label rows**, with no relabeling and no change to the runner. It's report-only, like the sensitivity read. It decides nothing at Stage 0, but it will matter for D7's horizon value and Stage 1's selection. **Joe and the builder settle the tie value for those before Stage 1 is designed.**

## 4. Owed with the run

- **Publish Stage 0's rows** (both passes' labels, the reports, the manifest) under `rounds/round9/data/stage0/` with hashes, so I can recompute the primary, the unfinished shares, the sensitivity read and the §3 tie-as-loss read myself.
- **Interim notices carry status only.**

**Scope:** this confirms `stage0_report.py` at `5c7e5393…`, and extends to the one-line pin commit in §2. Stage 0 launches on that commit with Joe's banked go. It plays no games and leaves the registry untouched. Approval certifies the build as written, not the run as executed.
