# Builder response — round 3, the R17–R19 package

**Responds to:** `rounds/round3/claude-reply-fc8faef.md`
**Reviewed commit:** fc8faefe10a8b3fbd1721e51e420183be2d65615 (the
R12–R16 rerun build — APPROVED as written; launch NOT approved).
**This package's parent:** b1fdd8bd262dd46a741c5539aeee2a665a8c02ff
(Joe's upload of `claude-reply-fc8faef.md`; verified as repo HEAD
when this package was built).
**Ask:** launch approval for the 19-seed rerun on the commit
carrying this package (R17–R19), under the reads in §6. Joe's go
is also required; nothing in this package launches anything.

Contents: R17, the teacher's root evaluation now uses the state
the bridge built (one new patch, `patch_teacher_bridge_state.py`,
applied last in the build order); R18, the seed-19 diagnostic
(raw completes in 2.2 s, ghost completes in 93.6 s — the
FAIL-localized condition does not occur); R19, the seat-audit
evidence committed with verbatim source lines, and the
production-server byte-identity confirmation. All runs below are
disclosed build tests on a fresh tree (`/tmp/reruntree2`); the
19-seed rerun was NOT launched.

The disclosed build tests in this package: the R17 reproduction
(ghost + raw, seed 7, seat 2), the seat-1 seed-3 smokes
(raw/ghost/shadow/capture), and the R18 diagnostic (raw + ghost,
seed 19, seat 1, 1200 s timeout). `test_classify.py` passes 11/11
on the built tree (unchanged classifier).

---

## 1. R17 — the teacher's root evaluation uses the bridge's state

One new patch: `rounds/round3/code/patch_teacher_bridge_state.py`
(sha256 in §5), applied AFTER `patch_seat_routing.py` in the
existing build order. It touches `policy_server.php` (1 edit) and
`search.php` (5 edits); both files lint clean (`php -l`).

**The change.**

- `SimPolicyServer_Choose` (policy_server.php) already builds
  `$state = SimFeat_BuildState(...)` and canaries it for the
  decision. The dispatch line now passes it through:
  `SimSearch_RootDecide($branch, $cands, $candRecs, intval($player), $state)`.
- `SimSearch_RootDecide` gains an optional fifth parameter,
  `$bridgeState`. Its trace PRE capture now records THE PASSED
  STATE: `feat_pre_hash = SimTrace_Hash($bridgeState)` and
  `priors_pre = SimSearch_Eval($bridgeState, $candRecs)`. If
  `$bridgeState` is null (a legacy caller), PRE falls back to
  building the pre-sync state exactly as before.
- After the checkpoint block (`DoGamestateUpdate` +
  `WriteGamestate`), RootDecide builds one more featurization of
  the same decision and stores it on the trace row as
  **`feat_sync_hash`** — the post-sync state, DIAGNOSTIC ONLY.
  Nothing reads it: not the classifier, not any driver assertion.
  It keeps the census of sync-straddling decisions possible
  without putting the sync move inside an equality pair.
- RootDecide hands the state on:
  `SimTeacher_Decide(..., $gameDir, $bridgeState)`.
- `SimTeacher_Decide` gains the optional parameter. Its ROOT
  prior computation — previously
  `$evRoot = SimSearch_EvalState($player, $branch, $candRecs)`,
  a re-featurization made after the checkpoint sync — is now,
  when a bridge state was passed:
  `SimFeat_Canary($player, $bridgeState)` (the same fail-closed
  check EvalState ran) followed by
  `$evRoot = SimSearch_Eval($bridgeState, $candRecs)`, and the
  trace stash is set from that same passed state:
  `ssTraceLastEval = {state_hash: SimTrace_Hash($bridgeState), priors: $evRoot[0]}`.
  So the root row's `feat_post_hash == feat_pre_hash` **by
  construction**; the within-row feat pair stays in the
  classifier as a regression check, with no excuse. With no
  passed state, Decide falls back to `SimSearch_EvalState`
  exactly as before.

**Call sites changed (complete list).**

1. policy_server.php, `SimPolicyServer_Choose`: the
   `SimSearch_RootDecide(...)` call gains `$state`.
2. search.php, `SimSearch_RootDecide`: signature; PRE capture
   source; `feat_sync_hash` insert after the checkpoint block;
   the `SimTeacher_Decide(...)` call gains `$bridgeState`.
3. search.php, `SimTeacher_Decide`: signature; the root-eval
   call site (its first computation) — the ONLY `EvalState` use
   inside Decide, and it was the root prior computation.

**Call sites deliberately NOT changed.**

- The `SimSearch_EvalState` call at the end of
  `SimSearch_RootDecide` (the non-teacher ISMCTS root: priors
  for the visits/mean-value tie-break over the children). That
  is the search player's own root evaluation, not the
  teacher's; R17 is scoped to the teacher root. Its stash write
  cannot contaminate a teacher row — the teacher return happens
  earlier in the function.
- The `SimSearch_EvalState` call in Choose's `EQ_LOG` block
  (env-gated diagnostic comparing search pick vs net argmax;
  not part of any arm's play).
- Inside Decide: the TEACHER_CAPTURE block's snapshot
  featurization (`SimFeat_BuildState` for the snap index) and
  the overturn snapshot's featurization at the end of Decide.
  Neither is an `EvalState` use and neither computes priors —
  they record the checkpointed game directory's state for the
  snapshot index, which is what a snapshot is. The capture
  block's PLAYED pick is the root `priorPick`, which under R17
  now comes from the bridge state, as ruled.
- `SimSearch_EvalState` itself, `SimV1_DeckCards`, and
  featurize.php: untouched. (Option (b) — featurizer reads views
  for the deck slice — is a separate registered item per the
  fc8faef reply, not part of this rerun.)
- Children and rollouts: untouched; they re-parse the synced
  store, where store == view.

**Assertions and classifier.** `paired_driver.py`,
`classify_divergence.py`, and `r3_pair.py` are byte-unchanged
(hashes in §5). No assertion input needed updating: the ghost
assertion `trace_teacher_pick_is_prior_argmax` already reads the
trace row's `decide_pick` against the argmax of `priors_pre` —
under R17 those PRE priors are the bridge-state priors Decide
itself used, so the assertion now evaluates exactly the claim
Claude's ruling requires (ghost pick == bridge argmax), instead
of the near-equivalent pre-sync rebuild it read before.
`test_classify.py` on the built tree: **11/11 fixtures pass**.

## 2. R17 pass tests

Full records: `rounds/round3/data/rerun/r17-seq167.txt` and
`rounds/round3/data/rerun/tests-r17.txt`.

**Test 1 — ghost seat 2, seed 7, on the R17 tree** (per-seat
setup: a dedicated patched server, its own learner seat 2; the
driver row records `server_seat: 2`, `seat_mismatch_errors: 0`).

- Ghost game 881656265: winner 1, 9 turns, 89.1 s, 483
  decisions, `assert_ok` TRUE (49 teacher trace rows; pick ==
  PRE-prior argmax on 49/49). Raw seat-2 seed-7 game 196311413
  on the same tree: winner 1, 9 turns, 483 decisions, and the
  two games are gamelog-identical (sha256 prefix
  `6ad1edc104fd6192`, 75,918 bytes) with equal
  `gamestate_norm_sha` (`f1ac8f3296125656`).
- The sync-straddling ARS row: in the void launch's game this
  decision was seq 167; that game's seat-2 stream was v1's, so
  its numbering does not carry over — in the corrected per-seat
  game the same settled-pitch ARS decision is **seq 186**, the
  game's only sync-straddling teacher row. (Seq 167 in this run
  is a DQ row, byte-identical in both arms; it is included in
  the evidence file.) At seq 186:
  - `feat_pre_hash` = **5c691d959081aec5** — and the raw game's
    own `bridge_pick` row at seq 186 records `state_hash`
    **5c691d959081aec5**: Decide's prior-state hash equals the
    bridge's `state_hash`. ✓
  - `feat_post_hash` = **5c691d959081aec5** — equal to PRE, by
    construction. ✓
  - `feat_sync_hash` = **6ae81b29a6115b70** — DIFFERS: the
    settled pitch, on the diagnostic channel. ✓
  - `priors_pre` == `priors_post` to full printed precision
    ([0.9998065829277039, 0.00019341998267918825]); argmax 0 =
    `decide_pick` = `chosen`. `zone_pre` == `zone_post`; only
    the diagnostic store hash moved (95ed906c0b210336 →
    d6355826d1ab2341) as the checkpoint settled the pitch.
- Whole-game census of the ghost trace: 49 teacher rows, **0**
  with `feat_pre != feat_post`; exactly **1** with
  `feat_sync != feat_pre` (seq 186, ARS); every teacher row
  carries `feat_sync_hash`.

**Test 2 — seat-1 seed-3 smokes** (same protocol as the fc8faef
package; all four arms, driver assertions in the manifests):
**all four arms `assert_ok` TRUE, every check TRUE.** All four
games are winner 1, 16 turns, 653 decisions, and gamelog-
identical to each other (sha256 prefix `88231b961d202c19`,
104,690 bytes; `gamestate_norm_sha` `2564ffc4f8575d6e`) — the
same seed-3 raw game as the fc8faef package.

- raw (2.2 s): 0 stat rows, 0 teacher trace rows; checks
  `stat_rows_zero`, `teacher_trace_rows_zero` TRUE.
- ghost (176.7 s): 80 teacher rows, pick == PRE-prior argmax
  on 80/80; checks `pick_eq_prior_all_teacher`,
  `ghost_flag_on_all_rollouts`, `rollouts_present`,
  `trace_rules_all_ghost_prior`,
  `trace_teacher_pick_is_prior_argmax` all TRUE.
- shadow (284.8 s): 80 teacher trace rows, all rule
  `shadow_bridge`, 0 `shadow_fallback_decide`; its three
  checks TRUE.
- capture (3.2 s): 34 capture rows, 0 rollout rows; checks
  `capture_rows_present`, `capture_pick_eq_prior`,
  `capture_no_rollout_fields`, `no_rollouts_anywhere`,
  `pick_eq_prior_all_teacher`,
  `trace_teacher_pick_is_prior_argmax` all TRUE.

**The §3 caveat, recorded (per the fc8faef reply).** Capture
mode played Decide's `priorPick`, which pre-R17 was the
post-sync argmax, so "§3 trajectories are plain v15" holds
except at any sync-straddling decision where the argmax flipped;
the ghost assertion found 0 such flips in 1,441 teacher rows, so
the effect is expected negligible.

**R17 evidence excerpts.** `deps/engine-deck-source-excerpts.txt`
(new): `SimV1_DeckCards` verbatim from the box's policy_v1.php
(it reads the STORE globals `$p1Deck`/`$p2Deck` directly), and
featurize.php lines 97 and 148 verbatim with context — the two
deck reads inside the featurization.

## 3. R18 — seed-19 diagnostic (reported apart)

Full record: `rounds/round3/data/rerun/r18-seed19.txt`. On the
R17 tree, seed 19, seat 1, normal driver timeout (1200 s),
per-seat server (seat 1):

- **Raw: COMPLETED** — winner 2, 9 turns, **2.2 s**, 454
  decisions, `assert_ok` TRUE (0 stat rows).
- **Ghost: COMPLETED** — winner 2, 9 turns, **93.6 s**, 454
  decisions, `assert_ok` TRUE (44 teacher rows, pick ==
  PRE-prior argmax on 44/44, rollouts present). The ghost game
  is action-identical to the raw game: byte-identical gamelog
  (`8dc1ce5e9be0acc2`, 73,731 bytes in both), identical
  `gamestate_norm_sha` (`27fc42ad12094468`), same lives
  (-1 / 8).

Claude's R18 ruling: if raw completes and ghost does not, that
is FAIL-localized and blocks the gate. **That condition does not
occur** — the ghost completes in 93.6 s, well inside the 1200 s
timeout. The seed-19 hang of the old (misbuilt) arms does not
reproduce under the correct arms on the R17 tree. The
diagnostic is reported apart from the 19-seed pairings, as
registered; seed 19 stays excluded from the pairings.

## 4. R19 — record items

**R19.1 — seat-audit evidence.**
`rounds/round3/data/rerun/seat-audit-evidence.txt` quotes, for
EACH eval in the fc8faef §1 table, the actual server-log or
games_meta line recording the server's learner seat, with its
box file path: the v15 gate chunks (`/tmp/dg_v15_a|b`), the four
BC3 regate workdirs, the league evals
(`bc3_vs_ppo3b_v15_a|b`), the teacher-gate chunks
(`/tmp/tgate_c0b` seat 2, `/tmp/tgate_c1a` seat 1), the §3
harvest chunks (`/tmp/meas_c0b` seat 2, `/tmp/meas_c1a` seat 1),
the critic-study workdirs (`hv_a1` seat 1, `hv_a2` seat 2,
`hv_c1` seat 1), the Phase 3b spot gate (`spot/v35_b`, meta seat
2) and Phase 3 run-1 gate (`/tmp/dg_v65_b`, seat 2), and the
probe/mirror workdirs (`probe_b1` seat 2, `probe_a1` seat 1,
`mm_b1` seat 2, `mm_a1` seat 1). **Every eval in the table has
a surviving record; none is missing**, and no line is borrowed
from another eval.

One wording correction to my fc8faef §1: it said eval.py
"asserts the server's reported seat before games count". The
evidence file names the actual mechanism, quoted with
file:line from `/home/joe/tcg/tcg-sim/rl/eval.py`: eval.py
derives `learner_seat` from `--learner-deck` (eval.py:153),
places that same value in the spawned server's environment as
`TCG_LEARNER_SEAT` (eval.py:165-166; the server is spawned at
eval.py:169-170) and in the PHP child's environment for
`--policy search` (eval.py:187-188); after the run it reads
the seat BACK from the server's own per-game records
(games_meta.jsonl / traj lines, eval.py:239-253) and counts a
win only where the winner equals the recorded seat
(eval.py:273-278). There is no ping — the ping endpoint is new
in fc8faef. For the rollout_server lineage the server assigns
the seat per game into its own record, so a mismatch is
structurally impossible there. The conclusion of the audit is
unchanged; its stated mechanism is now the real one.

**R19.2 — production server untouched, byte-identical.**

- Box production: `/home/joe/tcg/tcg-sim/rl/search_server.py`
  sha256 =
  `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4`
- Repo copy: `rounds/round3/deps/search_server.py` sha256 =
  `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4`
- **Byte-identical.** ✓ (Both hashed fresh for this package.)
- The patched server (sha256 `ab85fa1b…`, the R12 build) exists
  on the box ONLY inside rerun-family test trees. A box-wide
  search for `search_server.py` files containing the
  `SEAT_MISMATCH` string returns exactly:
  `/tmp/reruntree/rl/search_server.py`,
  `/tmp/reruntree2/rl/search_server.py`,
  `/tmp/nocaptree/rl/search_server.py` (the R13 mis-build
  negative-control tree). The production tree
  (`/home/joe/tcg/tcg-sim/rl/`) contains no `SEAT_MISMATCH`
  string and its file hash is the production hash above. The
  patched server has still never been run under eval.py.

## 5. Build table (sha256)

Build order (fresh tree; this package's tests ran on
`/tmp/reruntree2`, built exactly this way): gate tree copy →
`patch_trace_shadow.py` → `patch_child_sigkill.py` →
`patch_teacher_capture.py` → `patch_canary_sync.py` →
`patch_seat_routing.py` → **`patch_teacher_bridge_state.py`
(new, last)** → deploy `paired_driver.py`, `r3_pair.py`,
`classify_divergence.py`, `cleanup_cache.php` at the tree root
and the patched `search_server.py` into the tree's `rl/` →
`php -l` clean on both patched PHP files.

Unchanged since fc8faef (verified by hash): patch_trace_shadow
`bb4b9416b35a58fda0d3a1fc3c94559e53ccc23da91b36661b3bcf938c88c2d9`;
patch_child_sigkill
`c101ab32b41d6bb8a48abf2863ba9362e1f53bb7a501c55154b669f93853d050`;
patch_teacher_capture
`65ad2a06a50daf32de5d8f261c5ac9bead4ffce6f489e2be75f26939221decd5`;
patch_canary_sync
`6916a9b8e0760b5befb6d13517e93f592fd5f09b3054347f09c88d610129bed4`;
patch_seat_routing
`b3fcb86849f666e39bcdc96064f186be795bd358313563ecf653ea23b2d734fc`;
paired_driver.py
`2df2b0b0b8b2d747d758a837ecf1afefa6b82daa6933dcef456a5d8fbc5b83a3`;
r3_pair.py
`13f95ebe09fbbe5d8cd123c7aca4642c4944de03af2c9e847f689660e96869da`;
classify_divergence.py
`1518427bd4904a581fd2158b702b0e58e902b2cf1c64371f40da51c6fc7b0533`;
test_classify.py
`78533013e9b1a5a12b05c91c113fb454beaf9d419d951f8f1fde9ac01a3044eb`;
cleanup_cache.php
`153f8b2c457dea951e49abebd6623d39f57e8a5301763cd609d37a8e7c12448a`;
patched search_server.py (tree copy)
`ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c`;
run_r3_rerun.sh
`d4458e6c0651b3eab5b212e220e1c4ab97aa8ac85211fab2358fad427891694c`.

New / changed in this package:

- patch_teacher_bridge_state.py:
  `376ae36bfda2dbc5c7530400e2aa0250a6cf0d3250f9266e314cef2a7149bbe0`
- Built `search.php` on the R17 tree:
  `6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a`
  (fc8faef tree: `f82aa528…`)
- Built `policy_server.php` on the R17 tree:
  `64c215392ddcac0dc92ce1e4a3c455969d87423e23d71be57991247ce53827b3`
  (fc8faef tree: `d0d531f1…`)
- Production `search_server.py` (box `rl/` and repo `deps/`):
  `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4`
- Weights (unchanged): ckpt_v15.pt
  `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c`

`run_r3_rerun.sh` is byte-unchanged: it already cds to
`/tmp/reruntree`. The launch build rebuilds THAT path from this
package (same order, R17 patch last) and must verify the built
`search.php` / `policy_server.php` hashes equal the two above
before starting; the script's own manifest will then record
them. Launch command, unchanged:

```
cd /tmp/reruntree && bash run_r3_rerun.sh
```

Files in this commit: this response;
`code/patch_teacher_bridge_state.py` (the only code change);
`data/rerun/r17-seq167.txt`, `data/rerun/r18-seed19.txt`,
`data/rerun/seat-audit-evidence.txt`, `data/rerun/tests-r17.txt`;
`deps/engine-deck-source-excerpts.txt`. No claude-reply files
are touched by the builder.

## 6. Reads for the rerun (fc8faef §6, updated per the reply)

Everything registered in fc8faef §6 stands (the 107ea5d reads,
the prospective canary amendment, `seat_ok`, per-arm
assertions, the standing raw control, the ipcs budget, seed 19
excluded from pairings), with the reply's three changes:

1. **Within-row feat: no excuse.** `within_row_hits` must be 0
   with NO feat exception. Under R17 the feat pair is equality
   by construction; a feat hit is now a plain within-row hit
   and classifies the seed accordingly. (`feat_sync_hash` is
   diagnostic only and never enters a read.)
2. **R18 diagnostic added.** Seed 19, raw + ghost at seat 1,
   1200 s, reported apart — run pre-launch for this package
   (§3): ghost completes in 93.6 s, action-identical to raw.
   If the rerun's own execution somehow contradicts that, the
   FAIL-localized ruling applies as written in the reply.
3. **Production-server manifest check.** Each arm manifest must
   record the sha256 of the box's production
   `/home/joe/tcg/tcg-sim/rl/search_server.py` and it must equal
   `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4`
   (the `deps/search_server.py` hash), proving the rerun did
   not touch production.

Not tested (unchanged from fc8faef): the full 19-seed rerun
(this is the launch being asked for); the patched server under
eval.py (compatibility by construction only, and R19.2 keeps it
out of production); seat-2 shadow/capture (not in the
registered layout); the teacher arm itself. Also new here:
R17's legacy-caller fallback (null bridge state) is untested
by a live game — every in-tree caller now passes the state;
the fallback exists only so an out-of-tree caller cannot break.

## 7. The ask

Launch approval on THIS commit's sha for the 19-seed rerun
(`cd /tmp/reruntree && bash run_r3_rerun.sh`, tree rebuilt from
this package), under the reads in §6 — and Joe's go, as always,
before anything launches.
