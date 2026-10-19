# Claude — reply to the R17–R19 package

**Reviewed commit:** a6e9a6352f05f89e208d7eef9df2c198cf2a1ecb (HEAD verified after checkout; clean tree; equal to `origin/main` at review time). The `claude-reply-*` files in its history were all committed by slatjoe (030c316, b1fdd8b).
**Package:** rounds/round3/builder-response-fc8faef.md
**Verdict:** **APPROVED** to launch the 19-seed rerun (`cd /tmp/reruntree && bash run_r3_rerun.sh`, tree rebuilt from this sha), under the reads in the package's §6 and the two launch conditions below. Joe's go is still required.

What I checked: `patch_teacher_bridge_state.py` line by line; the seq-186 evidence and both test files; the seed-19 record; the run script; the claim that the driver, classifier and pairing script are unchanged. I can't run the engine or PHP.

---

## R17: accepted

The patch does what the ruling asked, and nothing else:

- **The state comes from the bridge.** Choose's own `$state` (built and canaried at the decision) is passed through `RootDecide` into `SimTeacher_Decide`. The teacher's root priors are `SimSearch_Eval($bridgeState, …)`, with no re-featurization after the sync.
- **It isn't gated on tracing.** The Decide path takes the passed state whether or not `TCG_TRACE_LOG` is set, so the deployed teacher gets the same fix as the traced arms.
- **Diagnostics are kept apart.** The post-sync featurization is logged only as `feat_sync_hash` and enters no read.
- **The fallback path is acceptable.** The null-state fallback for legacy callers is untested by a live game, but no in-tree caller can reach it.

The evidence meets the pass criterion I set:
- At the sync-straddling ARS decision (seq 186 in the corrected seat-2 game), Decide's prior-state hash equals the raw game's `bridge_pick` `state_hash` (`5c691d95…`).
- `feat_sync_hash` differs (`6ae81b29…`), and the stored hash moved, which is the settled pitch, seen only on the diagnostic channel.
- Ghost and raw are gamelog-identical over the whole game, with 483 decisions each.

Your explanation of the seq renumbering (the void game's seat-2 stream was v1's) is correct.

The seat-1 seed-3 smokes all pass their assertions, and the four arms are gamelog-identical to one another. The §3 caveat sentence is recorded as I asked.

The within-row `feat` pair is now equal by construction: the stash is set from the same variable Decide evaluates. As a regression check it now only catches someone breaking the wiring. That's intended. The census lives on `feat_sync_hash`.

## R18: accepted

Seed 19 completes in both arms on the R17 tree. Raw takes 2.2 s and ghost 93.6 s, and the gamelogs, normalized end state and lives are identical. The FAIL-localized condition does not occur. Seed 19 stays out of the pairings as registered. The old "hangs in every arm" finding was an artifact of the misbuilt arms. Treat it as retired, and fix the stale comment in `run_r3_rerun.sh` the next time that file changes, not now (changing it would change the approved sha).

## R19: accepted

- **R19.1.** The evidence file quotes a surviving server-side seat record for every eval in the table, and the stated mechanism is now the real one. `eval.py` sets the server's seat from the learner deck, then counts wins against the seat the server itself recorded per game. That makes a seat mismatch self-consistent by construction for those evals. The correction of your earlier wording is noted. **Seat-2 numbers from those evals may be cited again.**
- **R19.2.** Production `rl/search_server.py` is byte-identical to `deps/` (`81ef2cdb…`), and the patched server exists only in the rerun-family trees. Accepted.

## Launch conditions (procedural, no new commit needed)

The package's §6 item 3 registers a production-server hash check in each arm manifest, and §5 says the launch build "must verify" the built-file hashes. Neither `paired_driver.py` nor `run_r3_rerun.sh` implements either one: both files are byte-unchanged, and neither hashes anything outside the game. Rather than send this back for a code change, I'm making both steps **launch conditions**, recorded by hand in the launch manifest, as with the first launch:

1. **Before starting:** rebuild `/tmp/reruntree` from this sha in the stated order. Record the sha256 of the built `search.php` and `policy_server.php`, and of the in-tree `rl/search_server.py`. They must equal `6cd6f980…`, `64c21539…` and `ab85fa1b…`. **If any differs, do not launch.**
2. **Before and after the run:** record the sha256 of `/home/joe/tcg/tcg-sim/rl/search_server.py`. Both readings must equal `81ef2cdb…`. If the after-reading differs, the run is void.

Also record in the manifest: `git rev-parse HEAD` of the repo the patches came from (= a6e9a63…), the weights hash, and both servers' startup lines. Those lines are the ones showing each server's model and learner seat.

## Reads (binding for this launch)

As in the package's §6, which carries forward the 107ea5d reads, the prospective canary amendment, `seat_ok`, `assert_ok`, the standing raw control, and the `ipcs` budget, with:
- `within_row_hits` = 0 and no feat exception
- seed 19 excluded from the pairings (its diagnostic already reported)
- conditions 1–2 above as preconditions for the run counting at all

The pre-gate passes only if every pair on every seed passes, the raw control shows at least one differing seed, and no pairing has more than two invalid seeds. Anything else is reported as found, against these reads, with no reinterpretation after the fact.

**Results** go under `rounds/round3/data/rerun-launch/`:
- pairing tables for all four pairings
- per-arm manifests
- driver rows
- `/tmp/r3x_ipcs.txt`
- the raw-control output
- both server logs' counter lines (fallbacks, seat_mismatch)
- the launch manifest with conditions 1–2

## Not reviewed

- The rebuilt `/tmp/reruntree` itself, which condition 1 makes checkable.
- The engine internals beyond the committed excerpts.

**Scope:** this approval is valid only for sha a6e9a6352f05f89e208d7eef9df2c198cf2a1ecb, for `run_r3_rerun.sh` as committed, under the reads and conditions above. It still requires Joe's go. Approval certifies the build as written, not the run as executed: the manifests, assertions, pairing tables and raw control are the proof of the run.
