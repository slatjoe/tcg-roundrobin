# Claude — confirmation check on the sweeper fail-safe fix

**Reviewed commit:** a6d8442291f6d53aefcdf58daf1c8860d0ed0731 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-ef34219.md` hashes to `0fe10298…5a887453`, the value I gave Joe.
**Package:** `rounds/round7/sweeper-fix-confirmation.md`, `code/shm_sweep.py`, and the pins in both runners.
**Verdict:** **CONFIRMED. The pre-gate may launch on Joe's go.**

## Checks

| Item | Required (ef34219 §2) | Found |
|---|---|---|
| `shm_sweep.py` diff | the fail-safe only | `select()` **keeps** any segment whose cpid or lpid is missing or ≤ 0, before any other rule; it counts them, and the PASS line carries `unattributed=N`. The old `get(…, 0)` defaults are gone. Nothing else changed. sha256 **`98027a8b…d43d14f33`** ✓ |
| Pre-gate runner pin | moved | pin line only; `d519beb1…` ✓ |
| Fleet runner pin | moved | pin line only; `0ffe635b…` ✓ |
| Canned listing | the withheld `-p` row is kept | reported PASS, and **reproduced here independently**: I loaded the committed `select()` with stubbed live pids against six canned segments:<br>• a normal orphan → **selected**<br>• no pid fields → **kept**, unattributed<br>• cpid 0 → **kept**, unattributed<br>• a rule-3 game key → **kept**<br>• a live cpid → **kept**<br>• a run-start shmid → **kept**<br>Result: selected = [the orphan], `unattributed = 2` ✓ |
| §1.4 micro-test re-run | clean | dry run 0/0/0; live run deleted the 2 orphans with `unattributed=0`, kept the rule-3 segment; box back to 0 ✓ (box-side, from the record) |
| `kernel.pid_max` | report-only | 4,194,304. Pid reuse is negligible, and in any case it only ever keeps a segment ✓ |

## Joe's spot-check (ef34219 §5)

Joe checked on the box himself, independently of the builder's session:
- **9,289** SELECT lines
- **one** game capped by turns, seed 3007
- the registry at **`d5cfcf79…`** in full

All three match the probe record. Joe's two corrections to my suggested commands are right:
- the files are under `/tmp/xprobe/w1/`
- counting `"turns"` matches every row's turn-count field, so the count has to key on the `cap_reason` value

The record the pre-gate rests on is verified.

## Launch

**The pre-gate may launch on Joe's go**, as follows:
- `run_gravy_pregate.sh` at `d519beb1…`
- `GATE_TIMEOUT=3870`
- `GRAVY_MODEL` = `ckpt_v10.pt` (`44f1e5d7…`)
- `PREGATE_SWEEP=1`
- the launch step deploys `shm_sweep.py` (`98027a8b…`), `parse_r3_pair.py` and `gate_ipcs_cleanup.sh` at the tree root, and the runner's nine pins verify them

**The pre-gate report** carries:
- the determinism parse
- the R16 control
- both ghost tables, with their parse records and any K5 disposition
- the server load lines and fallbacks
- the `ipcs` series, plus the sweeper log's pass totals (`selected`, `deleted`, `failed`, `unattributed`)
- the registry merge record

All of it is cited by **path and sha256**. Joe spot-checks a few headline figures on the box before I rule on it: the parse verdicts and the registry hash at minimum.

**The fleet** comes after the pre-gate report is reviewed. It runs on its own go, with the ef34219 §4 launch condition: the standing G8 sweep immediately before `run_gravy_gate.sh` (`0ffe635b…`), with the count recorded.

**Scope:** this confirmation approves the pre-gate launch on sha a6d8442291f6d53aefcdf58daf1c8860d0ed0731 with the runner and tools named above, and requires Joe's go. Approval certifies the build as written, not the run as executed.
