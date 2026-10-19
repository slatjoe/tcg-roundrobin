# Claude — reply to the round-3 launch results

**Reviewed commit:** d3095af3f85a67c7352c84b224f05bccf75d9de3 (HEAD verified after checkout; clean tree)
**Package:** rounds/round3/data/r3-launch/results-summary.md
**Verdict on the run:** the pre-gate **does not pass**, as reported. I accept the summary's reading against the registered reads. But two of the three failures are **harness defects that the reads cannot distinguish from machinery effects**. Neither failing pairing is evidence about the teacher machinery. No gate runs. The rerun needs the fixes below in one new commit, reviewed at its sha.

What I checked: the six driver row files, the four pairing tables, the manifests, and the code paths named below. I recomputed the cross-arm comparisons from the rows myself.

I also own a miss. I approved `run_r3.sh` without checking either (a) that the server's seat matched each arm's seat or (b) that the capture hook was in the built tree. Both were visible in files I had read.

---

## 1. Seat 2: the raw arm never put v15 in seat 2

**From the rows:** `r3_raw_s1` and `r3_raw_s2` are the **same 19 games**. Winner, turns, decisions, both life totals, gamelog sha and normalized final-state sha are equal on 19/19 seeds. Changing `--seat` did nothing to the raw arm.

**Mechanism:**
- The driver sets `TCG_LEARNER_SEAT` only in the PHP child's environment (`paired_driver.py:54`).
- The bridge's pick is routed by the **server's** `LEARNER_SEAT`, read once from the server process's environment at start (`search_server.py:41`, default 1, used at line 225).
- One server, started for seat 1, served every arm.
- So in both raw arms, seat 1 was v15 and seat 2 was `v1_argmax`, the heuristic. That is exactly why `a_chosen = 0` on every one of the 19 divergences: v1's top candidate is index 0.
- The ghost seat-2 arm took its root picks for seat 2 from the eval endpoint, which is net priors with no seat routing. So ghost s2 compared **net picks against heuristic picks**, and diverged on every seed at the first contested decision where they disagree.

**Reading:** pairing (b) is void as a test of the machinery. It is the same class as the round-2 misbuild (an arm that wasn't the player it claimed), and the mode-line check can't see it because the server's seat isn't on any row.

**Consequence beyond round 3 (audit, no conclusion yet):** any past run with the learner at seat 2 and a server not started with `TCG_LEARNER_SEAT=2` had the learner's server-routed decisions played by the heuristic, and the opponent's played by the net. That covers DQ choices, single-candidate gates, and the bridge fallback after a canary refusal. Before anything cites a seat-2 number again, list each past eval (the 0.505 chunks, probe, mirror, the October gate, the §3 harvest, the critic-study games) with the server's actual learner seat. Read it from the server log or `games_meta.jsonl`, not from the launcher's intent. `rl/eval.py` may well start a server per seat, so the result may be clean, but it needs a record.

## 2. Capture arm: the hook isn't in the tree

`TEACHER_CAPTURE` exists only in `code/patch_teacher_capture.py`. It is absent from `code/search-gate-tree.php`, and the launch manifest's build list (gate tree → `patch_trace_shadow.py` → `patch_child_sigkill.py`) never applied it. The driver set the env var, nothing read it, and the "capture" arm ran the **full teacher**, with rollouts and overturns. That is why its rows carry rule `teacher`, why it diverges from ghost where an overturn fired, and why 4/19 seeds (no overturn) stayed IDENTICAL.

**Reading:** pairing (d) is void. It never tested children-versus-no-children.

**One confirmation needed:** state which tree the §3 harvest ran in, and confirm from its own `search_stats` that all 1,087 contested rows carry `capture: 1` with `pick == prior_pick`. §3's "trajectories are plain v15" claim rests on that hook having been present there.

## 3. Canary refusals: a mixed-source check, not a fair-play event

`SimSearch_Canary` runs **before** the checkpoint sync (`search-gate-tree.php`: canary at 966, `DoGamestateUpdate` at 972). It reads hidden zones through `SimSearch_ReadZone`, which prefers the `p1*`/`p2*` **store**, and public zones through the getters, the **views**. Last round established that between syncs the store lags the view. A card that has moved in the view since the last sync can then be counted in neither source, and the canary reports it missing. A card in transit at an arsenal decision (`dragon_power_blue`) fits that. I can't confirm the exact path from here, but the accounting is inconsistent by construction, and the fix doesn't depend on the path.

The rate is the old ~1%, not new (16 rows of 1,354 in ghost s2). A refusal returns null before the PRE capture, so the decision goes down the plain bridge path. The data agrees: in raw-vs-ghost and raw-vs-shadow at seat 1, every canary-invalid seed is still IDENTICAL.

**On the registered rule:** I wrote "a canary refusal invalidates the seed". Applied as registered, (a) and (c) are **inconclusive**, and I won't relabel them as passes after seeing the data. They are strong evidence, though: 19/19 IDENTICAL with zero within-row hits, including on the refused seeds. For the rerun I'm amending the rule **prospectively**, for the reason above. A refusal means the machinery did not engage on that decision, so it is a **coverage** metric, not a seed invalidator. It's reported per arm and branch, with a cap: refusals ≤ 2% of contested decisions per arm, and any branch above 5% reported by name. A seed is still invalidated by any refusal that leaves a trace row other than a plain `bridge_pick`.

## 4. Two within-row `feat` hits at ARS: open, and not explained by the defects above

- Seed 7, seq 167, ghost s2, ARS
- Seed 11, seq 455, capture (full teacher) s1, ARS

Both are within one teacher row: the featurized state changed across the checkpoint and Decide. The localization showed the featurizer reads views, and the sync writes view → store. So a featurization change means something in that window changed a **view** at an arsenal decision. This is the one finding in this run that could be a real machinery side effect, and it occurs at seat 1 too.

**The ghost s2 game is reproducible:** the ghost plays the prior, and routing is deterministic with the same server configuration. Re-run seed 7 at seat 2 under the same single-server setup and take the same five-point dump at seq 167:
- getter views and store for hand, arsenal, deck and pitch, both players
- the view build flags
- `feat` hash, at each point

Also give me a census from all existing teacher rows in all six arms: count of `feat`, `zone` and `rng` pre≠post, by branch. The classifier reports only the first hit per pair, and I want to know whether ARS is the only branch.

## Required for the rerun (one commit)

**R12. Seat routing, enforced mechanically.** Start a dedicated server per seat with `TCG_LEARNER_SEAT` set (or a per-request `learner_seat` the server routes on and asserts). Every bridge request carries the learner seat. The server rejects a mismatch as an error, so it's counted and invalidates the seed. Each driver row records the server-reported learner seat. `r3_pair.py` adds `seat_ok`: the row's server seat must equal the arm's `--seat`.
*Pass:* a negative control in which a seat-2 arm is pointed at a seat-1 server fails loudly at its first request.

**R13. Capture arm built and asserted.** Add `patch_teacher_capture.py` to the tree build and record its sha in the manifest. Add per-arm stat assertions to each arm manifest, checked by `r3_pair.py`:
- raw: 0 stat rows
- ghost: every contested row has `ghost: 1` and `pick == prior_pick`, with rollouts present
- capture: every contested row has `capture: 1`, `pick == prior_pick`, and no rollout fields
- shadow: every teacher trace row has rule `shadow_bridge`
- teacher-family: no row has rule `teacher` unless the arm is `teacher`

*Pass:* the seed-3 smoke shows each arm's assertion true. A deliberately mis-built capture arm (hook omitted) fails it.

**R14. Canary reads one source.** Run the canary after the checkpoint sync, or read hidden zones through the getters. The sync is benign by last round's localization, so running it on refused decisions is acceptable. Log the missing multiset and branch on every refusal, then report the refusal rate before and after on seat-1 ghost seeds 1–18 and 20.

**R15. ARS localization (§4)** plus the within-row census, before the rerun launches. If a view moves inside the window, the remedy follows the same table as last round.

**R16. Reads for the rerun:** as registered in my 107ea5d reply, with §3's prospective canary amendment and two additions:
- `seat_ok` (R12) and the per-arm assertions (R13) must be true on every seed, or the seed is INVALID.
- A shared-memory budget: `ipcs -m` before and after each arm, reported. The run grew 2,360 → 2,774 (+414). Make the timeout-kill path call `DeleteCache` for the killed child's game id (the parent knows it if the child writes it on start), and report the growth.

## Not blocking

- Stop the ~24 orphaned `rollout_server.py` processes before the rerun, and record that only the per-seat servers are listening.
- `raw s1 == raw s2` would have exposed the seat bug on day one. Add it as a standing control: two raw arms at different seats must produce different games on at least one seed.

**Scope:** no launch is approved by this reply. The rerun returns as a package with R12–R16 and the §4 localization, reviewed at its sha, and still needs Joe's go. Approval certifies the build as written, not the run as executed.
