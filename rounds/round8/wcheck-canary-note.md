# Round 8 — W-check error classes: the canary explanation

**Question** (claude-reply-0140eab §1/§3): the W=100 check's raw rows carry
600 `canary_hook_failed` error rows (run A), 300 `det_persist_failed`
(run B) and 200 `abort` (100 per run), all as whole 100-world batches.
Identify the affected states, and confirm these are the known
determinization-refusal classes (excluded worlds), **not** canary
detections of a hidden-information read — "it matters because 'canary' is
in the name."

**Verdict: confirmed, with one named residual.** `canary_hook_failed` and
`det_persist_failed` are the determinization-refusal classes: worlds
excluded at child setup or at the child's first root-decision check
because the determinized copy could not be persisted, or its global card
accounting did not close. The word "canary" in `canary_hook_failed` names
the **missing-card conservation check** (`SimSearch_Canary`), not the
fair-play featurizer canary (`SimFeat_Canary`) — a different function,
whose detection has a specific signal (a `SimFeat_Canary LEAK` exception
line on stderr). **That signal appears nowhere in either run's artifacts,
and no `SimFeat_Canary` detection occurred in either run.** `abort` is a
rollout-control class (hook budget / root-key), also unrelated to either
canary. What remains unproven is narrow and stated in §4: the rows do not
record which `abort` site fired for one state, and the original runs' exact
trigger for the three setup-failure states is not recorded anywhere — the
states label cleanly on reproduction (§4), so the trigger was a property
of the original runs' execution context, not of the states.

Code cited is the code the check ran: tree `search.php` sha256
`6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a` and
`featurize.php` sha256
`f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92`
(`/tmp/distilltree_native/`), driver `distill_label_main.php` sha256
`acf5f4bb3d8b0c7dbbdb3ba1dffa18aeebbde166c07f492ac74a70411e674cc4`
(`/home/joe/tcg/round8_code/`). Row census is over the published raw rows
(`rounds/round8/data/wcheck/`, 160,200 rows per run).

## 1. The affected batches, from the raw rows

Every errored batch is complete — 100 of 100 worlds (worlds 0–99 all
present) for the candidate — and no batch is partial:

| run (base) | error | state (game, engine turn, branch, selected, prior) | cands | job wall |
|---|---|---|---|---|
| A (555001) | `canary_hook_failed` ×300 | `286996099_t12` (286996099, t2, M, [0,1,2], prior 0) | 0, 1, 2 | 0.6 s |
| A | `canary_hook_failed` ×300 | `286996099_t16` (286996099, t2, M, [0,1,2], prior 0) | 0, 1, 2 | 0.6 s |
| A | `abort` ×100 | `852109890_t72` (852109890, t15, M, [0,1,2], prior 1) | 2 only | 11.4 s |
| B (777001) | `det_persist_failed` ×300 | `286996099_t19` (286996099, t3, M, [0,1,2], prior 0) | 0, 1, 2 | 0.8 s |
| B | `abort` ×100 | `852109890_t72` | 2 only | 11 s |

(Job walls are the labelers' own `done … secs=` lines; a full 300-world
job at W=100 took ~46–100 s, mean 45.8 s — the setup failures returned in
under a second, before any substantive rollout play.) The full error
census over both runs' 320,400 rows contains **exactly these three error
strings** — no `det_verify_failed`, no `det_verify_hook_failed`, no
`timeout` (the parent deadline class, §2), and no other error text of any
kind. Cross-run: `286996099_t12`/`_t16` labeled 100/100/100 in run B and
`286996099_t19` labeled 100/100/100 in run A; `852109890_t72` candidate 2
sits at `n_worlds` 0 inside its emitted label in **both** runs.

## 2. What each class is, mechanically

The label child is `SimLabel_RunRollout` (search.php:1325). It copies the
snapshot into a private game dir (whitelist only: gamestate.txt,
GameFile.txt, the two deck lists), persists the world's determinization
into the serialized state, parses, plays the rollout with decisions routed
through `SimLabel_ChildChoose`/`SimLabel_ChildDQ`, and writes exactly one
result file per world. The parent (`SimLabel_RunForSnapshot`,
search.php:1397) forks the W=100 children of a candidate together against
a 300 s deadline; a child still running at the deadline is killed and
recorded as `{"error": "timeout"}` (search.php:1479) — **zero such rows
exist in either run**, so nothing here is a deadline artifact.

- **`det_persist_failed`** — written at search.php:1346 when
  `SimSearch_ApplyAssignmentToFile` (search.php:318) returns false,
  before `ParseGamestate`. That function's own contract (comment,
  search.php:~316): "FAIL CLOSED: returns false on any inconsistency;
  callers abort the world." It rewrites the copied gamestate.txt's hidden
  lines (opponent hand/deck, root deck, arsenal rebuild) and returns
  false on: unreadable file (323), fewer than 24 lines (325), a missing
  required line (332), the assignment's arsenal-slot count differing from
  the serialized line's slot count (353), or a failed final write. The
  world is excluded without being played. (The same tag exists at
  search.php:714 in the tree-search child — same step, not this path.)
- **`canary_hook_failed`** — the tag returned by `SimSearch_HookCheck`
  (search.php:677–685) when `SimSearch_Canary` fails, invoked once per
  child at its first gated root decision (`SimLabel_ChildChoose`,
  search.php:1273–1277: the tag is stored in `ssLabelError` and the
  resulting `SimSearchAbort` is caught at search.php:1372, which writes
  it as the world's result). `SimSearch_Canary` (search.php:243) is
  `SimSearch_MissingCards` (search.php:217): every card in both decklists
  must be accounted for in the unseen pool + public zones, or credited
  via the chain/combat-chain layer IDs; a card sitting "in a zone the
  determinizer does not model (mid-effect limbo)" (comment, search.php:
  207–213) leaves a gap and the check **fails closed** — the world is
  excluded. HookCheck is the registered "consumer-side determinization
  check (R2, second placement)" (comment, search.php:672–676): the same
  check whose first placement, in the gated teacher's Decide
  (search.php:1083–1087), refuses the decision with a stat-logged
  `fallback: "canary"` and the missing multiset — the project's known
  determinization-refusal outcome. Crucially, the check reads only the
  two decklists, the pool IDs, the public-zone counts and the chain
  credits **in the child's own determinized copy**; it makes no comparison
  against the true hidden contents, which the child never holds (the
  whitelist copy's hidden zones are overwritten by the assignment before
  parse). It cannot be a hidden-information detection.
- **`abort`** — written at search.php:1372 when a `SimSearchAbort` is
  caught with `ssLabelError` unset. The unset-throw sites in the label
  hooks are exactly three: the 4,000-hook rollout budget
  (`SimLabel_ChildChoose`, search.php:1265; `SimLabel_ChildDQ`,
  search.php:1311) and the root-key guard (`SimLabel_ChildChoose`,
  search.php:~1271: the first gated decision's key must equal the job's
  registered root key, or the child is searching the wrong decision and
  must report nothing). A rollout-control class; neither canary is
  involved.

## 3. The fair-play canary, its detection signal, and the sweep

The hidden-information canary is `SimFeat_Canary` (featurize.php:202): a
card occurrence in the featurizer's built state that exceeds
`SimFeat_LegalCounts` — the counts legally readable by that player — is a
leak ("seen[id] > legal[id] for any id => LEAK, throw loudly",
featurize.php:129). **A detection's signal is mechanical and specific:**
the function writes `SimFeat_Canary LEAK for player <N>: <card> x<n>
(legal x<m>), …` to STDERR (featurize.php:212) and throws. In the label
path a throw never becomes an error row; every route is accounted:

- at the decision hooks it is caught — `SimLabel_ChildChoose`
  (search.php:1294–1297: increments the world's `fallbacks` counter and
  decides by v1 argmax) and `SimLabel_ChildDQ` (search.php:1315: returns
  the v1 choice);
- inside evaluation it is caught by `SimSearch_EvalState`
  (search.php:474–481), which returns null, and a null eval increments the
  same `fallbacks` counter (`SimLabel_ChildChoose`, search.php:1299–1302);
- a throw escaping anywhere else in the child reaches the outer catch
  (search.php:1390), which writes the exception message verbatim as the
  world's error — i.e., an error row whose text **is** the LEAK message;
- server-side, `policy_server.php`:360 and :449 call it uncaught ("fail
  loudly"), so a detection there lands in the eval server's log.

**Sweep of both runs' artifacts:** the string `LEAK` occurs **zero**
times in `raw_a_all.jsonl`, `raw_b_all.jsonl`, `labels_w100_a.jsonl`,
`labels_w100_b.jsonl`, the two server logs (`prod_s1.log`, `prod_s2.log`),
the run log (`/tmp/r8_launch/wcheck_run.log`), and all eight label
processes' stderr files (`label_{a,b}_shard*_p1.err`) — every sink a
detection would have written to. The closed error census (§1) separately
excludes the verbatim-message route. Finished rows do carry
`fallbacks > 0` (53 rows in run A, 252 in run B): the counter has exactly
two branches, the canary catch and eval-null, and the canary branch is
excluded by the stderr sweep (its write precedes the throw in the same
process), leaving the eval-null branch — `SimSearch_Eval` returning null
after its two socket attempts (search.php:431–470) — as the attribution,
by elimination. **No `SimFeat_Canary` detection occurred in either run.**

## 4. Why whole batches — probes, reproductions, and the residual

The failing checks sit at child setup (persist) and at the first gated
root decision (hook check), upstream of any per-world divergence in play,
which is why a failure takes the whole (state, candidate) batch with it
and why the failed jobs returned in 0.6–0.8 s. But the trigger is **not** a
property of the states:

- **Snapshot probes** (read-only; each snapshot parsed exactly as the
  label parent parses it, then the accounting run): `SimSearch_MissingCards`
  is empty — the canary **passes** — on all four affected states and on
  the clean control `286996099_t8`.
- **Post-determinization probes**: with a world-0 assignment at each run's
  own seed base (persist + re-parse + verify + accounting), all eight
  (state × run-seed) pairs pass — persist ok, `SimSearch_VerifyAssignment`
  pass, missing set empty — including the pairs whose batches failed
  (`_t12`/`_t16` at run-A seeds, `_t19` at run-B seeds) and cross-run
  controls.
- **Full serial reproductions**: both failed jobs were re-labeled with the
  check's own labeler (`acf5f4bb…`, copied into a fresh tree copy per
  run_w_check.sh:142), the runs' exact seed bases (`_t12` at 1555004,
  `_t19` at 3777010), W=100, production server up. **Both label 300/300
  finished** (23.7 s / 22.6 s; rows at `/tmp/canary_probe/repro_t12_a.jsonl`
  sha256 `81da5c0c…`, `/tmp/canary_probe/repro_t19_b.jsonl` sha256
  `d5b25f51…`; probe script `/tmp/canary_probe/canary_probe.php`).

So the setup checks pass on these states at these seeds in isolation; the
original failures arose in the original runs' execution context (four
shard processes labeling concurrently, ~100 children forked per candidate
batch). One correlation is recorded without causal weight: `_t12`, `_t16`
and `_t19` were each the **first job (ji=0) of their shard file**, in both
runs — as was the clean control `_t8` (shard 0), which passed in both
runs; `852109890_t72` was shard 1, ji=59. The label path records only the
error tag — the missing multiset `ssLastCanaryMissing` is captured only by
the parent-side Decide placement's stat log (search.php:1085), which the
label path does not write — so **which card(s) the accounting missed in
the original children, and which persist condition returned false, are not
recoverable from the artifacts**. That, and which of the two `abort` sites
fired for `852109890_t72` candidate 2 (its pattern — one candidate of
three, identical across both seed bases, 11 s job wall — fits an early
deterministic abort better than a 4,000-hook rollout, but the rows do not
prove it), are the two points this investigation cannot close from the
record. Neither affects the classification: all three classes are
established from the code paths that emit them.

## 5. Accounting in the check's reads

Nothing here reopens the check's arithmetic: the excluded worlds were
already counted as such — `_t12`/`_t16` are run A's two thin rows and
`_t19` run B's one thin row (all candidates at 0 finished worlds, "prior
candidate finished 0 < 20 worlds"), and `852109890_t72` candidate 2 is the
single zero-finished slot inside an emitted label in both runs (its
`paired_n` is null; the state contributed no overturn test). The classes
explain *why* those worlds are missing; they were never silently dropped,
and none of them is a hidden-information event.
