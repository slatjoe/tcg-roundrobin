# Claude — confirmation check on the Stage 1 launch fix

**Reviewed commit:** a13cabc5a95b2ae0d6cc9ed15a7d1bd3ecb1be23 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch-and-abort record at 2bf7639f (`stage1-launch.md`). The committed `claude-reply-86de3be.md` hashes to `a6156bd1…cf904c3`, the value I gave Joe.

**Verdict: CONFIRMED.** Stage 1 relaunches on Joe's go with launched sha == a13cabc5, **reusing the completed capture and panel**, under the conditions in §2.

## 1. Checks

- **The code diff** against the confirmed 86de3be1 is exactly one token, on runner line 343: `PIDS="" FAIL=0 pid` becomes `PIDS="" FAIL=0`. No other code file changed. The runner now hashes to **`b0b08c55…27339e6`**.
- **The diagnosis is right:** `NAME=value … word` makes the assignments environment for a command named `pid`, so `PIDS` was never set in the shell, and `set -u` aborted at the first `$PIDS` use.
- **The audit of the other four `NAME=""` initializations** found no second instance. Accepted.
- **`fx_shard_supervision.sh`** (`9fb97219…`) runs the supervision block verbatim against a stub php: the happy path covers every pid, including the slowed shard; the failure path aborts before concatenation; and the pre-fix text dies with the launch's own errors. That closes the gap that let this through. My earlier confirmations rested on fixtures that never ran the runner's shell control flow. **From now on I'll expect every runner control block that spawns or waits to have a verbatim-extraction fixture,** as the B0 gate and this block now do.

## 2. Relaunch conditions

The aborted launch completed the capture (40 games), the registry merge and the panel. B0's shard 0 ran orphaned and was stopped, and no setting completed.

1. **Reuse, don't re-capture.** Run `PHASE=eval`, then `PHASE=analyze`, **not** `PHASE=all`, which would play 40 new games against the same seeds and append to the registry again. The relaunch manifest records:
   - the `panel_jobs.jsonl` sha256 and its equality with the panel the aborted launch built
   - the registry's sha256 and count, unchanged since that launch's post-capture merge
2. **No stray processes, and SHM clean.** Before launch, record a process listing showing no labeler, eval or production-server process left over from the aborted run, then run the standing G8 sweep and record its count.
3. **Stale B0 shard outputs are reset.** The runner truncates `evals_*` and `stats_*` per shard at each setting's start (lines 363–364), so the orphan's partial B0 rows can't mix in. **Assert it anyway:** the relaunch manifest lists every pre-existing `evals_B0*` and `stats_B0*` file with its size before launch. After the run, B0's row counts must equal the registered world count exactly, and the analyzer's world-count guard enforces that.
4. **Launched sha:** a13cabc5, or differing only under `rounds/`.

**Scope:** this confirms the one-token fix and the new fixture at sha a13cabc5a95b2ae0d6cc9ed15a7d1bd3ecb1be23, and approves the Stage 1 relaunch (eval with the B0 gate, then analyze) on the reused capture and panel, under §2 and Joe's go. Approval certifies the build as written, not the run as executed.
