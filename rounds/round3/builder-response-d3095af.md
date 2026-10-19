# Builder response — round 3 rerun package (R12–R16)

**Parent sha:** d3095af3f85a67c7352c84b224f05bccf75d9de3 (repo HEAD when
built; verify before reading further — if HEAD has moved, this package's
commit names its own parent in the commit message).
**Responds to:** Claude's reply to the round-3 launch results (reviewed
commit d3095af): pairings (b) and (d) void as harness defects, §1 seat
routing, §2 capture hook, §3 canary accounting, §4 the two ARS
within-row hits, R12–R16 required for the rerun.
**Ask:** approval to launch `code/run_r3_rerun.sh` on this package's sha,
under the registered reads in §6. Joe's go is also required. No launch
has happened; every run reported in §5 is a disclosed build test (seed-3
smokes, one-game negative controls, the R14 before/after ghost set).

Your two void verdicts are confirmed from primary records, and both
defects were in my harness: the driver's seat never reached the server
(raw s1 and raw s2 row files are the same 19 games, field for field),
and the capture patch was never in the launch tree's build list
(`grep -c TEACHER_CAPTURE` on the built search.php: 0). Your §4
reproduction and census are done (§3, §4 below). The audit you ordered
in §1 is done and is §1 of this response — the short version is that
the seat defect is confined to my paired driver; every standing eval
number survives it, for reasons read from each eval's own records.

---

## §1 Seat-2 audit (your §1 consequence): all past evals CLEAN on seats

Method: for each past eval, the server's ACTUAL learner seat was read
from the eval's own server log or `games_meta.jsonl`, never from the
launcher's intent. The reason the damage is confined: `rl/eval.py`
(the harness behind every standing number) spawns a FRESH server per
chunk with `TCG_LEARNER_SEAT` set to the chunk's seat and asserts the
server's reported seat before games count. The paired driver —
written for the round-2 ghost test — was the only harness that ever
pointed games at one long-lived seat-1 server regardless of arm seat.

| eval | server's actual learner seat (source) | verdict |
|---|---|---|
| v15 vs heuristic, 400 games (the 0.505) | per-chunk servers, seat matched per chunk (eval.py server logs) | CLEAN |
| BC3 regate evals (0.505 / 0.490 era) | same eval.py mechanism | CLEAN |
| Model round-robin (v15/BC3/BC2, 1,000 games) | same eval.py mechanism | CLEAN |
| October teacher gate eval (200 games) | seat-matched servers | CLEAN on seats — the 0.832 remains impeached by the determinization defect only |
| §3 measurement harvest (40 games) | see §2 | CLEAN |
| Critic study (474 games, Phase 2a) | eval.py mechanism | CLEAN |
| Phase 3b spot gates + Phase 3 league/gate evals | eval.py mechanism | CLEAN |
| ISMCTS probe (0.530), mirror (0.525) | seat facts clean | CLEAN on seats — both stay void for determinization |

No standing number needs a seat-related retraction. The seat defect's
blast radius is exactly the round-3 launch's own seat-2 arms: pairing
(b) void, and the seat-2 half of the ghost evidence must be re-earned
by the rerun.

## §2 §3 confirmation (your §2 ask)

The §3 harvest ran on `/tmp/meastree`. Its `search.php` DOES contain
the capture hook (`grep -c TEACHER_CAPTURE`: present). From the
harvest's own `search_stats.jsonl` (chunk dirs meas_c0a/c0b/c1a/c1b):
exactly **1,087 stat rows carry `capture: 1`** (the snapshotted
decision set), and **`pick == prior_pick` on all 2,746 teacher rows,
zero exceptions**. The §3 claim — harvested trajectories are plain
v15, teacher picks snapshotted but never played — stands as stated.

## §3 Within-row census (your §4 ask)

All teacher rows in all six launch arms (`data/rerun/within-row-census.txt`):

- **5,494 teacher rows total. feat pre≠post: 2. zone: 0. rng: 0.**
- Both feat hits are branch **ARS** (2 of 64 ARS rows). No other
  branch has a hit of any kind: A 483, B 1,460, D 148, M 2,644,
  P 695 rows — all zero.

ARS is the only branch, as localized next.

## §4 ARS localization (your §4 / R15): the featurizer's deck reads the store

Reproduction: ghost seat 2, seed 7, on a scratch tree (`/tmp/arstree`)
under the launch's server configuration; the game replays
deterministically and the seq-167 row reproduces. Five-point dump in
`data/rerun/ars-localize-seq167.jsonl` (game 857037000, player 2,
branch ARS). What moves, point by point:

- **The feat hash changes at exactly one point: across
  `DoGamestateUpdate`** (L0 fresh 088e6e38… → L1 be3c31e2…). It is
  stable after the write (L2), and Decide's own EvalState stash at
  L3/L4 equals the post-sync value. WriteGamestate, Decide, and the
  trace code move nothing.
- At the same point the STORE settles player 2's staged pitch:
  `p2Pitch` [rowdy_locals_blue, …] → [] and `p2Deck` 49 → 50. The
  view had already applied the pitch (the seq-38 finding); the sync
  writes view → store.
- Why the featurizer sees it: every zone in `SimFeat_BuildState`
  reads a getter VIEW — except the deck features, which come from
  `SimV1_DeckCards($player)` (`featurize.php:97`, `:148`), and
  `SimV1_DeckCards` reads the STORE globals `$p1Deck`/`$p2Deck`
  directly (`policy_v1.php:44-48`). The sync therefore changes
  exactly the deck slice of the featurized state, and the
  classifier's within-row feat pair — PRE featurization (pre-sync)
  vs Decide's EvalState featurization (post-sync) — straddles the
  sync whenever a pitch settles inside the window. Both launch
  hits (this one; capture seed 11 seq 455) are this shape.

Remedy options, following your table's logic. I am not recommending
between (a) and (c) here, and I am explicitly NOT recommending (b)
in this package:

- **(a) Sensor-side:** make the within-row feat comparison
  sync-aware — e.g., compare Decide's featurization against a
  featurization taken after the checkpoint. Cost: the PRE capture
  is also the cross-arm state witness (it must stay the bridge's
  own featurization, pre-sync, or raw-vs-teacher state equality
  stops meaning anything), so this means logging a THIRD
  featurization (post-sync) purely as the within-row baseline.
- **(b) Featurizer-side:** make `SimV1_DeckCards` read the deck
  through the getter view, one source for the whole featurizer.
  Flagged, not recommended here: this is a PRODUCTION change. The
  featurizer feeds the bridge in every game ever played on this
  box — every net pick whose decision-time store ≠ view would
  change, which is every historical eval's input distribution and
  the §3 snapshots' semantics. It needs its own registration and
  revalidation, not a ride-along in a rerun fix.
- **(c) Accept-and-bound:** register the feat within-row pair as
  sync-straddling by construction; a feat hit counts as a
  violation only when the row carries no sync witness (zone_store
  pre≠post on the same row — both observed hits have it). The
  rerun's reads in §6 are written so either ruling drops in: tell
  me which, or rule at the rerun's review.

One consequence worth naming whichever way you rule: at a
pitch-settling decision, Decide's priors are computed on the
post-sync state while the bridge's own pick (what raw plays, and
what the ghost must mirror) is computed on the pre-sync state. In
19 seat-1 ghost games the played picks never diverged, but the two
paths are not featurizing the same deck slice at those decisions.

## §5 The R12–R16 build

### Tree build (canonical, in order)

Fresh copy of the gate tree → `patch_trace_shadow.py` →
`patch_child_sigkill.py` → **`patch_teacher_capture.py`** (new in the
build; applied UNADAPTED — both of its anchors matched the traced
tree exactly; its own anchor asserts passed) → `patch_canary_sync.py`
(new) → `patch_seat_routing.py` (new) → deploy `paired_driver.py`,
`r3_pair.py`, `classify_divergence.py`, `cleanup_cache.php` → replace
`rl/search_server.py` with the patched server (§5.1) → `php -l`
clean on search.php and policy_server.php. Patch and file hashes are
in the launch-manifest table in §6.

### §5.1 R12 — seat routing, enforced mechanically

**Server** (`code/search_server.py`, the live file's lineage —
byte-identical to the box's `rl/search_server.py` before this patch;
the patch is additive for legacy callers):

- New `{"type":"ping"}` request → `{"learner_seat": N, "model": path}`.
- Any request carrying `"learner_seat"` unequal to the server's
  constant is rejected: a `SEAT_MISMATCH` line is printed (and
  counted), and the reply is `{"v":1, "error":"seat_mismatch",
  "learner_seat":N}` — deliberately lacking `action_index`/`priors`,
  so both PHP clients fail the query instead of playing a pick.
- Every pick and eval response now also carries `"learner_seat"`.
  Routing itself is unchanged; requests without the field (legacy
  callers, e.g. eval.py's PHP) are served exactly as before.

**Bridge** (`code/patch_seat_routing.py`):

- `SimPolicyServer_Query` — the single funnel for every normal
  bridge request (Choose, DecisionOption, and the shadow path's
  direct Query all pass through it) — stamps `learner_seat` from
  the PHP process's `TCG_LEARNER_SEAT` onto every payload. A
  `seat_mismatch` response returns null immediately (into the
  existing counted v1-fallback path) after printing
  `policy_server: SEAT_MISMATCH server_seat=<n> request_seat=<m>`
  to STDERR. `SimSearch_Eval` stamps and surfaces identically
  (`search: SEAT_MISMATCH …`, null return = eval failure, which
  Decide already handles). A PHP process with no `TCG_LEARNER_SEAT`
  stamps 0 and is rejected by any correctly seated server:
  fail-closed.

**Driver**: before each arm, ping the socket; record
`server_seat` (+ model) on EVERY row and in the manifest. Each row
counts `SEAT_MISMATCH` lines in its game output as
`seat_mismatch_errors`. Any mismatch → row `invalid: seat_mismatch`
and **outcome fields are not recorded** (gamename only): a
mis-seated game is not a measurement.

**Pairing** (`r3_pair.py`): new `seat ok` column — both rows'
`server_seat` equals the arm seat AND `seat_mismatch_errors == 0`.
Verdict precedence: INVALID_ASSERT > INVALID_SEAT > INVALID_MODE >
classifier.

**Negative control (run, output in `data/rerun/tests-r12-r13.txt`)**:
seat-1 server only; one raw game at seat 2, seed 3. The ping
identified the server (`learner_seat: 1`, arm seat 2) and the game
ran into the wall as designed: **336 SEAT_MISMATCH rejections**,
the server's log counting them (`count=1…336`), and the driver row
reads `invalid: "seat_mismatch"`, `server_seat: 1`,
`seat_mismatch_errors: 336`, with **no winner recorded**. Under the
old harness this exact configuration produced a clean-looking
heuristic game and a void pairing; now the first request fails and
the row says so.

**Positive controls**: ghost seed 3 at seat 2 against the seat-2
server completes with `server_seat: 2`, 0 mismatches, winner
recorded (201s); raw and ghost at seat 1 likewise (`server_seat: 1`).

### §5.2 R13 — capture built + per-arm stat assertions

- `patch_teacher_capture.py` is in the tree build (above); the
  built search.php contains the hook; its sha256 is in the §6
  manifest table. (Precision note: the gate tree already contains
  an unrelated snapshot block at the END of Decide, keyed on
  `TEACHER_SNAP_DIR` alone, which copies the game dir only when a
  decision OVERTURNS — a gate-era debugging aid. It changes no
  pick and is not the capture hook; it is why the launch's capture
  logdirs contained a `snaps/` dir despite the missing hook. In
  the rerun's capture arm it never fires: capture returns before
  rollouts, so no overturn is ever computed.)
- The driver computes per-arm ASSERTIONS into
  `<out>.manifest.json` (`assertions` details + `checks` +
  `assert_ok`), from the arm's own stat rows and trace rows:
  - **raw**: zero stat rows AND zero teacher trace rows.
  - **ghost**: every teacher stat row `pick == prior_pick`; every
    rollout row carries `ghost == 1`; rollouts present; every
    teacher trace row's rule is `ghost_prior`; every teacher trace
    row's played pick equals its PRE priors' argmax.
  - **capture**: capture rows present; capture rows have
    `pick == prior_pick` and NO rollout fields (`means`/`n_worlds`
    absent); NO rollout rows anywhere in the arm; every teacher
    stat row `pick == prior_pick`; every teacher trace row's played
    pick equals its PRE priors' argmax.
  - **shadow**: teacher trace rows present; every one has rule
    `shadow_bridge`; `shadow_fallback_decide` count is 0.
  - Design note, from the smoke below: the stat side is what
    convicts the launch misbuild. The trace rule label cannot —
    the trace patch labels a CORRECT capture row `"teacher"` too
    (the label names the Decide path, not the arm; the §3
    confirmation in §2 was likewise stat-side). I therefore did not
    implement any "no `teacher` rule" check; the capture checks
    above are the ones that fail on the misbuild, and the negative
    control proves it.
- `r3_pair.py` verifies both arms' manifests (`assert ok` column);
  a failed assertion makes every seed of the pairing INVALID_ASSERT.

**Seed-3 smokes on the new tree (all assertions TRUE)** — full
outputs in `data/rerun/tests-r12-r13.txt`:

- raw s1: assert_ok true (0 stat rows, 0 teacher trace rows).
- ghost s1: assert_ok true — and at 19-game scale via the R14 set
  (§5.3): all checks true, trace pick == prior argmax on
  1,441/1,441 teacher rows.
- ghost s2 (seat-2 server): assert_ok true.
- shadow s1: assert_ok true — 94 teacher trace rows, all
  `shadow_bridge`, 0 `shadow_fallback_decide`.
- capture s1: assert_ok true — 34 capture rows, 0 rollout rows,
  game completes in 8s (snapshots only, no rollouts — the launch's
  accidental full-teacher capture took ~190s per game).

**Negative control (run)**: a scratch tree built identically but
WITHOUT `patch_teacher_capture.py` (`grep -c TEACHER_CAPTURE` = 0),
capture arm, seed 3: **assert_ok FALSE** — of 80 teacher stat rows,
0 carry `capture: 1` and 32 carry rollout fields;
`capture_rows_present: false`, `no_rollouts_anywhere: false`,
`pick_eq_prior_all_teacher: false`, and
`trace_teacher_pick_is_prior_argmax: false` (the full teacher's
played picks leave the prior argmax at overturns). The game took
287.5s as a full teacher game, against 8s for the correct build.
The assertion fails the misbuild on four independent checks.

### §5.3 R14 — canary single-source

`code/patch_canary_sync.py`: in `SimSearch_RootDecide`, the canary
call moves from before the trace PRE capture to **immediately after
the checkpoint block** (`DoGamestateUpdate` + WriteGamestate
include), before the TEACHER_MODE dispatch. Refusal behavior is
unchanged (stat row with `fallback: "canary"` + the missing
multiset; return null → plain bridge path). The child hook canary
(`SimSearch_HookCheck`) is untouched.

Trace consequence, as your amendment assumes: the PRE capture now
precedes the canary, and the teacher trace row is only written after
Decide runs — so a refused decision produces **no teacher trace
row**, only the bridge's `bridge_pick` row.

**Before/after, seat-1 ghost, seeds 1–18,20** (`count_canary.py`;
denominator = root calls = teacher rows + canary rows, your
"16 of 1,354" construction):

- BEFORE (launch records): **11 refusals / 1,448 root calls =
  0.760%**. Per branch: ARS 4/24 = 16.67%, A 0.82%, M 0.59%,
  B 0.49%, D 0%, P 0% (`data/rerun/canary-before.txt`).
- AFTER (new tree, seat-1 server, same 19 seeds): **7 refusals /
  1,448 root calls = 0.483%** (`data/rerun/canary-after.txt`).
  The delta is exactly the ARS class and nothing else: **ARS
  4/24 → 0/24**, while A (1), B (2) and M (4) are count-identical
  before and after. So the sync artifact is gone, and the
  remaining 7 refusals are a pre-existing background of the
  canary's strict accounting that the move does not explain and
  this fix does not claim — consistent with your "the rate is the
  old ~1%" observation; the launch's excess over background was
  the ARS class. Teacher rows rise 1,437 → 1,441: precisely the
  4 formerly-refused ARS decisions now run the machinery. The 19
  games are identical to the launch's ghost games (winner, turns,
  decisions, 19/19) — the moved canary changed no played game.
  Under your amended rule the after-set is within caps (arm
  0.483% ≤ 2%; highest branch A at 0.82%, none above 5%).

### §5.4 R16 — housekeeping in `code/run_r3_rerun.sh`

- The script starts BOTH per-seat servers itself (seat-matched env,
  distinct sockets `/tmp/r3_s1.sock` / `/tmp/r3_s2.sock`), waits for
  each server's own "listening on" line, runs the arms against their
  seat's socket, and **reaps both servers on exit (trap)**. Outputs
  use the `r3x_` prefix; the launch's `r3_` files stay untouched as
  the void run's record.
- `ipcs -m | wc -l` is recorded before and after EACH arm into
  `/tmp/r3x_ipcs.txt`, which the results package will carry.
- **Timeout path**: the driver snapshots the tree's `Games/` listing
  before each game; on a timeout kill it diffs the listing and runs
  the new `cleanup_cache.php` (tree root; includes the vendor
  SHMOP library and calls `DeleteCache` per new game id).
  **Forced-timeout test (run)**: ghost arm, seed 19, `--timeout 60`
  on the new tree. The kill fired at 60s; the Games/ diff found 66
  new game ids (the killed game's own dir plus the rollout-child
  dirs Decide spawned during the window — the actual segment
  leakers), and `cleanup_cache.php` ran `DeleteCache` on **66/66**
  (row: `invalid: "timeout"`, `timeout_cache_cleaned` ==
  `timeout_new_games`). Design note: the diff is only meaningful
  because arms run sequentially — during one game, new Games dirs
  belong to that game and its children. (Seed 19's raw arm, for the
  record, now COMPLETES on this tree in 2.8s — the hang lives in
  the teacher/search path, not the bridge game.)
- **Orphan cleanup** (your not-blocking item): the 26 orphaned
  `rollout_server.py` processes are killed (census 26 → 0). The
  long-lived search server (pid 2435384) was NOT touched; my two
  test servers were retired after the tests, so the only policy
  server listening on the box now is that pre-existing one — the
  rerun starts its own per-seat pair. `ipcs -m | wc -l` as
  measured: 2,360 before the launch, 2,774 after it, 2,903 after
  today's build tests (which included two games killed mid-flight
  by session restarts, whose segments nobody cleaned — reported
  as measured; the rerun's own per-arm ipcs read is the binding
  one).
- **Standing raw control**: `r3_pair.py --raw-control <rowsA>
  <rowsB>` compares two raw arms across seats (outcome fields +
  gamelog sha per seed) and prints the differing-seed count with
  RAW-CONTROL PASS/FAIL (≥1 differing seed required). Run against
  the launch's own rows as a control on the control: **0/19 seeds
  differ — RAW-CONTROL FAIL**, the seat defect's signature, caught
  mechanically from now on.

### What is NOT tested

- The full 19-seed rerun itself (that is the launch being asked
  for). All §5 runs are seed 3 (one game per arm per control), the
  one-game seat-mismatch control, the forced-timeout game, and the
  19-game R14 ghost set.
- The patched server under eval.py (legacy callers): compatibility
  is by construction (requests without `learner_seat` are served
  unchanged, responses only gain a field both existing PHP clients
  ignore) and by the ping smoke against the old server class
  (unpatched servers simply fail the driver's ping and record
  `server_seat: null`) — but no eval.py batch has been run against
  the patched server file. The rerun does not use eval.py.
- Seat-2 shadow/capture (not in the registered layout; seat 1 only,
  as in the launch registration).
- The teacher arm (not part of the pre-gate layout).

## §6 Rerun registration

**Launch command** (exactly, after approval at this sha and Joe's go):

```
cd /tmp/reruntree && bash run_r3_rerun.sh
```

with the tree built per §5 from this package's `code/` (build inputs
and their sha256 — the launch manifest recorded at run time carries
the same table plus `git rev-parse HEAD`, the patched files'
sha256, and the weights sha256
0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c
for ckpt_v15.pt):

| file | sha256 |
|---|---|
| patch_trace_shadow.py | bb4b9416b35a58fda0d3a1fc3c94559e53ccc23da91b36661b3bcf938c88c2d9 |
| patch_child_sigkill.py | c101ab32b41d6bb8a48abf2863ba9362e1f53bb7a501c55154b669f93853d050 |
| patch_teacher_capture.py | 65ad2a06a50daf32de5d8f261c5ac9bead4ffce6f489e2be75f26939221decd5 |
| patch_canary_sync.py | 6916a9b8e0760b5befb6d13517e93f592fd5f09b3054347f09c88d610129bed4 |
| patch_seat_routing.py | b3fcb86849f666e39bcdc96064f186be795bd358313563ecf653ea23b2d734fc |
| paired_driver.py | 2df2b0b0b8b2d747d758a837ecf1afefa6b82daa6933dcef456a5d8fbc5b83a3 |
| r3_pair.py | 13f95ebe09fbbe5d8cd123c7aca4642c4944de03af2c9e847f689660e96869da |
| classify_divergence.py | 1518427bd4904a581fd2158b702b0e58e902b2cf1c64371f40da51c6fc7b0533 |
| search_server.py (patched) | ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c |
| cleanup_cache.php | 153f8b2c457dea951e49abebd6623d39f57e8a5301763cd609d37a8e7c12448a |
| run_r3_rerun.sh | d4458e6c0651b3eab5b212e220e1c4ab97aa8ac85211fab2358fad427891694c |

Built files on the test tree (the same build the smokes ran on;
the launch manifest records these at run time):

| built file | sha256 |
|---|---|
| search.php (gate tree + all five patches) | f82aa528209cec8788b1e49aeaf3c034c41cc008e8375f67c4dd63cc94aa019b |
| policy_server.php (trace + seat patches) | d0d531f163d2989d4396e1a54acc9997f8b5a49a1e9fd2b6914ab1a88f0b8a42 |
| rl/search_server.py (patched, as deployed in-tree) | ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c |

**Registered reads** (your 107ea5d reads, with your prospective
canary amendment from the d3095af reply, plus R12/R13/R16):

For every seed in 1–18, 20, for raw vs ghost at seat 1 and seat 2,
raw vs shadow at seat 1, and ghost vs capture at seat 1:

- **PASS** requires all of: classifier IDENTICAL; `within_row_hits`
  = 0 (with the §4 feat-pair ruling applied as you direct);
  outcome fields equal (`winner`, `turns`, `decisions`, `p1life`,
  `p2life`, `gamestate_norm_sha`); modes ok with zero connect
  failures; **`seat_ok`** on both arms (server-reported seat equals
  arm seat, zero seat-mismatch errors); **`assert_ok`** on both
  arms' manifests. The pre-gate passes only if every pair on every
  seed passes.
- **Canary refusals are a coverage metric**, reported per arm and
  branch: arm refusal rate must be ≤ 2% of contested decisions,
  and any branch above 5% is reported by name. A refusal
  invalidates its seed only if it leaves a trace row other than a
  plain `bridge_pick`.
- **FAIL-localized**: any non-IDENTICAL verdict, or any within-row
  hit not excused by the §4 ruling. Report class, seq, branch,
  rule and the row. No gate runs.
- **FAIL-outcome**: IDENTICAL traces with any outcome field
  unequal.
- **INVALID**: INVALID_MODE, INVALID_SEAT, INVALID_ASSERT,
  `shadow_fallback_decide`, a canary refusal that leaves a
  non-`bridge_pick` trace row, MISSING_ROW, DUP_SEQ, or timeout
  invalidates that seed. Report it, don't drop it. More than two
  invalid seeds in any pairing means the run is inconclusive, not
  a pass.
- **Standing control**: raw s1 vs raw s2 must differ on at least
  one seed (`r3_pair.py --raw-control`); if they do not, the run
  is void regardless of the pairings.
- **Shared-memory budget**: `ipcs -m | wc -l` before/after each arm
  is reported with the results; timeout kills run the DeleteCache
  cleanup (R16).
- **Seed 19** stays excluded and reported, per its open
  registration.

**Results** will be committed under `rounds/round3/data/r3-launch/`
sibling dir `rounds/round3/data/rerun-launch/` (pairing tables for
all four pairings, per-arm manifests, driver rows, the ipcs file,
the raw-control output), with traces and gamelogs on the box,
referenced by hash.
