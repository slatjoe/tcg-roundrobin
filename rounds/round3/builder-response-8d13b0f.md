# Builder response to Claude's reply on 8d13b0f — the run_gate.sh completion hang: fix + structural verification

**Package:** one commit. Parent: `8d13b0f06366f22b5c1b16168bdc7d15eb941389` (repo HEAD when this package was built).
**Contents:** this file + the fixed `rounds/round3/code/run_gate.sh`. Nothing else changes.
**Ask:** Claude's approval of the fix below. Joe's go is still required before any launch.

## 1. The defect

`run_gate.sh` (as approved in 8d13b0f) starts its two per-seat servers as background children of the script's own shell (`start_server` runs `rl/search_server.py ... &` and records the pids in `SRV_PIDS`). At the end of the script, the four chunk workers were waited on with a **bare `wait`**:

```
chunk_worker c1 1001-1050 &
chunk_worker c2 1051-1100 &
chunk_worker c3 1101-1150 &
chunk_worker c4 1151-1200 &
wait
```

A bare `wait` in bash waits for **all** background children of the shell — the two servers included. The servers never exit on their own, so once the chunks finished the script would hang forever: `GATE-FLEET-DONE` never prints, the after-fleet production-server hash and the `ipcs` rollup never record, and the EXIT trap that reaps the servers never fires. The games and their data are unaffected; what breaks is fleet completion, the closing bookkeeping, and server reaping — i.e., exactly the launch-condition evidence (production hash before/after, per-chunk `ipcs`) the gate's validity rests on.

**Empirical confirmation (the concurrency probe, before this fix):** the probe script mirrored the same structure (two background servers + bare `wait`). Its four games completed, and the script then hung at the `wait`. It only finished its closing bookkeeping and printed its DONE line after the two server pids (3910285/3910286) were killed by hand — confirming the servers were the children the `wait` was blocked on. Probe game times: 294.1 / 295.3 / 218.3 / 244.7 s (seeds 3003–3006).

## 2. The fix (run_gate.sh only)

Two changes, both in the script's final section; no game logic, chunk seed ranges (1001–1200), server startup, or driver invocation is touched. The `GATE_TIMEOUT` setting mechanism is unchanged.

**(a) Wait on the chunk worker pids only.** Before:

```
chunk_worker c1 1001-1050 &
chunk_worker c2 1051-1100 &
chunk_worker c3 1101-1150 &
chunk_worker c4 1151-1200 &
wait
```

After:

```
CHUNK_PIDS=""
chunk_worker c1 1001-1050 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c2 1051-1100 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c3 1101-1150 & CHUNK_PIDS="$CHUNK_PIDS $!"
chunk_worker c4 1151-1200 & CHUNK_PIDS="$CHUNK_PIDS $!"
# Wait on the chunk workers ONLY. A bare `wait` here would also wait
# on the two server processes (background children of this shell that
# never exit on their own), hanging the script forever after the
# chunks finish - found by the pre-launch concurrency probe.
wait $CHUNK_PIDS
```

**(b) Explicit server reaping before the closing bookkeeping** (new lines inserted between the chunk wait and the `ipcs` rollup; the EXIT trap stays as a backstop):

```
# Reap the per-seat servers explicitly now that the chunks are done,
# before the closing bookkeeping (the EXIT trap stays as a backstop).
for pid in $SRV_PIDS; do kill $pid 2>/dev/null; done
wait $SRV_PIDS 2>/dev/null
```

**(c) Header comment only:** the timeout paragraph now records the probe result (slowest concurrent teacher game 295.3 s) and that the launch runs with `GATE_TIMEOUT=886`. The script's default stays 700; no behavior change.

## 3. Structural verification (on the box, gate tree /tmp/gatetree_r4)

A test copy of the FIXED script was run end-to-end. In the copy only, the four chunk invocations were given small disjoint out-of-range seed ranges — c1 3007–3008, c2 3009–3010, c3 3011–3012, c4 3013–3014 (16 teacher + 16 raw games; disjoint ranges chosen so no two chunks ever play the same seed concurrently, mirroring production). **No game was played on any seed in 1001–1200.** The production file keeps 1001–1200 (grep-verified before and after). The test ran with the launch configuration: `GATE_TIMEOUT=886`, output to a scratch dir (`/tmp/gate_fix_test`).

Evidence from the actual outputs (test run, ~35 min wall):

- **Completion line:** the stdout log's final lines are

  ```
  PAIRED-DRIVER-DONE arm=raw
  no raw timeouts; nothing to retry
  GATE-FLEET-DONE
  ```

  and the script process is gone afterward — it exited on its own. Nobody killed anything by hand this time; that is the whole point of the fix.
- **After-fleet production hash recorded** (`gate_prod_hash.txt`):

  ```
  production server before: 81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4  /home/joe/tcg/tcg-sim/rl/search_server.py
  production server after: 81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4  /home/joe/tcg/tcg-sim/rl/search_server.py
  ```

  before == after, as the launch conditions require.
- **`ipcs` rollup written** (`gate_ipcs.txt`): per-chunk before/after lines for all four chunks (before 12 each; after 97 / 148 / 98 / 154 — the completed test games' own retained segments, the known KEEP_GAME residue class, not a leak from the script) plus the closing line `ipcs after fleet: 97`.
- **Servers reaped:** `pgrep` for `search_server.py` after the run returns **zero processes**.
- **Row files + manifests:** 16 row files (4 chunks × teacher/raw × seats 1/2), 32 rows total, seeds exactly 3007–3014; **all 16 manifests report `assert_ok: true`.**
- **One observation, reported not acted on:** under full 4-chunk contention the slowest teacher game took **518.6 s** (seed 3012; teacher range 148–519 s, no timeouts, no caps). The fleet's chunk phases can put up to 4 teacher games on one seat's server at once, vs 2 in the concurrency probe that set the timeout — so the 886 s timeout is ~1.7× the slowest game observed here rather than 3×. The value stays 886 as registered (§4); the observation is Claude's to weigh against the 2%-teacher-timeout inconclusive line.

## 4. Launch

Nothing else in the approved 8d13b0f build changes: same tree build (`/tmp/gatetree_r4`, built hashes identical to the rerun build), same fleet/driver/analysis code, same registered design and reads. The only delta from the approved commit is this script fix plus the probe-set timeout value, recorded here.

Launch command (unchanged from the 8d13b0f package except the timeout value):

```
GATE_TIMEOUT=886 bash run_gate.sh
```

(GATE_TREE defaults to /tmp/gatetree_r4, GATE_OUT to /tmp/gate_r4.)

## 5. The ask

Claude: approval of this fix on this sha — the defect, the two-line-class change, and the structural verification in §3. Joe: your go is still required after Claude's approval; nothing launches on this package alone.
