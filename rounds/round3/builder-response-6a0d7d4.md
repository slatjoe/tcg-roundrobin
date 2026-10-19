# Builder response — the round-3 GATE package (G1–G10)

Parent: `0a40b8e` (Joe's upload of `claude-reply-6a0d7d4.md`; the
pre-gate rerun results are at `6a0d7d4`, accepted in that reply).
This package builds everything the reply's §5 requires for the
gate and registers the design, the timeout, and the reads before
any game runs. **No gate games have been played.** Box work behind
this package, all disclosed below: the gate tree build, the G8
stale-segment cleanup (executed — §3), the G10 smoke (4 games —
§4), and two small build probes (§4.3, §4.4). The ask is at §6:
Claude's launch approval of this package, then Joe's go. Nothing
launches on this commit.

Code in `rounds/round3/code/`; smoke data in
`rounds/round3/data/gate-smoke/`.

## 1. The design as registered (G1) and the timeout ruling

**Arms.** Teacher (`TEACHER_MODE=1`, plain — no ghost, shadow, or
capture flags) vs raw v15, paired seeds, both against the
heuristic opponent, **both seats**. The teacher is exactly the
measured artifact: k=25 worlds, selection top-3 by prior plus any
prior ≥ 0.10 (cap 4), continuation pair "va", overturn iff paired
margin > 1.5 × paired SE, R17 root state (the `a6e9a63` tree
build; the gate tree built from it hashes identically — §2.1).

**Units.** 200 fresh seeds **1001–1200** × 2 seats = 400
(seed, seat) units; each unit is one teacher game + one raw game
on the same seed and seat = 800 games. Traces ON in both arms
(`TCG_TRACE_LOG`, for G3). `TEACHER_SNAP_DIR` on for teacher arms
(for G4).

**Timeout ruling, restated as registered:**

1. Engine caps (turn cap 60, decision cap 3,000, stuck limit) are
   game outcomes: **0.5 for both**, each reported with its cap
   reason. (Implementation reading, flagged for confirmation in
   §7: a capped game scores 0.5 for the arm that played it; the
   paired game is scored as played. The fixture test encodes
   this reading so it is visible in code.)
2. Teacher wall-clock timeout = **teacher loss** in the primary
   analysis; sensitivity analysis drops those pairs. **Teacher
   timeouts > 2% of teacher games → the gate is inconclusive**
   whatever Δ says.
3. Raw wall-clock timeout = engine hang: **re-run that game
   once**; a second hang scores raw 0.5, the pair is kept, the
   seed is reported. A raw timeout on a seed whose teacher game
   completed with zero overturns contradicts the pre-gate and is
   treated as a defect that stops the read (the analysis flags
   it automatically).
4. Fleet timeout = 3 × the p99 of ghost-arm game times in the
   rerun. Recomputed from the committed rows
   (`data/rerun-launch/r3x_ghost_s1.jsonl` + `r3x_ghost_s2.jsonl`,
   n=38): min 65.6s, median 132.2s, max 233.1s; p99 (nearest-rank)
   = 233.1s; 3 × 233.1 = 699.3s → **registered fleet timeout:
   700s**. The G10 smoke's teacher games ran 131.6s and 127.6s —
   neither crossed ruling 4's 350s smoke-check line, so the
   rerun-based value stands.

**Chunks (G6).** Four chunks — c1 1001–1050, c2 1051–1100,
c3 1101–1150, c4 1151–1200 — every seed at both seats within its
chunk (balanced by construction), per-seat patched servers with
`seat_ok` stamped on every row, production server hash recorded
before/after the fleet.

## 2. The build

### 2.1 Gate tree (`/tmp/gatetree_r4` on the box)

Built exactly like the rerun tree: fresh copy of the gate base →
`patch_trace_shadow.py` → `patch_child_sigkill.py` →
`patch_teacher_capture.py` (applied to `search.php`, unadapted) →
`patch_canary_sync.py` → `patch_seat_routing.py` →
`patch_teacher_bridge_state.py` → deploy driver / pair /
classifier / cleanup + the gate scripts at the tree root, patched
`search_server.py` into `rl/`. `php -l` clean on both PHP files.
Built hashes (launch conditions, §6):

```
search.php         6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a
policy_server.php  64c215392ddcac0dc92ce1e4a3c455969d87423e23d71be57991247ce53827b3
rl/search_server.py ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c
```

`search.php` and `policy_server.php` hash **identically to the
rerun tree's build** — the gate runs the same measured artifact
the pre-gate validated. Weights `ckpt_v15.pt` sha256
`0400539dda89…` unchanged; production `rl/search_server.py`
sha256 `81ef2cdbefe6…` untouched (re-verified after all box work).

### 2.2 Fleet script — `run_gate.sh` (+ driver additions)

`run_gate.sh` starts ONE patched server per seat for the whole
fleet (`/tmp/gate_s1.sock`, `/tmp/gate_s2.sock`; R12 pattern:
seat env, readiness from the servers' own listening lines) and
reaps them on exit (trap). Four chunk workers run in parallel;
each chunk runs its 50 seeds at both seats, teacher then raw per
seat, then the raw-timeout single re-run (`gate_raw_retry.py`,
ruling 3). Per chunk: own row files
(`gate_<chunk>_teacher_s<seat>.jsonl` / `gate_<chunk>_raw_s<seat>.jsonl`)
+ driver manifests (`assert_ok`), own stat/trace logdirs, own
snapshot dirs, own `gate_<chunk>_game_ids.txt` (the G9 source).
Production server sha256 recorded before/after into
`gate_prod_hash.txt`; `ipcs -m | wc -l` recorded before/after
each chunk into `gate_ipcs.txt`.

Judgment call, named: one server pair for the fleet rather than
a pair per chunk. The R12 guarantees live in the driver (it pings
the server, refuses a seat mismatch, stamps `server_seat` on
every row), not in server-per-chunk isolation; §4.4 smoke-tests
two teacher games running concurrently against one server.

Driver additions in `paired_driver.py` (opt-in env flags; every
prior arm's behavior unchanged — the rerun could be re-run with
this driver byte-for-byte in behavior):

- `GATE_GAME_IDS_FILE`: the driver appends every game id it
  produces — completed games, seat-mismatch rows, and every new
  id found on the timeout path. This is the registry source (G9).
- `TCG_CLEAN_CHILDREN=1`: after each completed teacher-family
  game, the tree's `Games/` dir is diffed against its pre-game
  snapshot and `cleanup_cache.php` runs `DeleteCache` on each new
  child id, excluding the game's own id (G8; §3.2). The row
  records `children_found` / `children_cleaned`.
- A `teacher` assertion profile for the arm manifest (the driver
  previously had none): stat teacher rows present,
  `det_persisted == 1` on every contested row (G7), teacher trace
  rows present. Both smoke teacher manifests report
  `assert_ok: true` under it.

### 2.3 Analysis — `analyze_gate.py` + fixture test (G2, G5, G7)

Unit (seed, seat); scoring per §1 (win 1 / loss 0 / draw 0.5 /
cap 0.5 / teacher timeout 0 with sensitivity drop / raw timeout
0.5 after the fleet's one re-run / any other invalid row leaves
the unit unscored, counted and named — never silently dropped).
Per-seat and pooled paired Δ with a bootstrap CI **clustered by
seed** (seeds resampled with replacement, all of a drawn seed's
units entering with multiplicity; B=10,000, seed 20261019).
Discordant counts and an exact two-sided sign test. The
registered bands printed verbatim and the pooled read taken from
them. Teacher-timeout rate with the > 2% inconclusive rule.
Monitors from the teacher stat files: canary refusal rate per
arm-seat against the 2% cap with branches > 5% named (G7), child
aborts by reason and by candidate, `det_persisted` presence,
overturn rate per chunk-file and pooled (G4's companion), and the
G5 calibration table — prior-pick rollout mean by decision
ordinal (contested-decision index within the game, stat-row
order) vs the game's realized outcome. Rollout outcomes in
`search.php` are +1 learner win / −1 loss / 0 unfinished, so the
predicted win probability is **(mean + 1) / 2**; that transform
is stated in the script and in its output. The ruling-3 defect
check (raw timeout + teacher completed that seed with zero
overturns) is automatic. **Registry gate (G9): the script refuses
to run (exit 2) unless every gamename in the row files is
present in the registry passed with `--registry`.**

`test_analyze_gate.py` — stdlib only, generates its fixture,
runs the analyzer as a subprocess, prints PASS/FAIL per check.
The fixture's expectations are hand-computed in its docstring
(12 scripted units: pooled Δ exactly 0, seat Δs ∓1/6, discordants
4/4 with p = 1.0, a teacher timeout driving the inconclusive flag
and a +1/11 sensitivity Δ, a cap scored 0.5, overturn rate 25%,
three calibration bins, the registry refusal, and the ruling-3
defect line). Actual output of the run committed here:

```
PASS analyzer exits 0 rc=0
PASS pooled delta +0.0000
PASS seat 1 delta -0.1667
PASS seat 2 delta +0.1667
PASS discordant 4/4/4 + p=1.0
PASS teacher timeouts 1 of 12
PASS inconclusive flag
PASS sensitivity delta +0.0909
PASS overturn rate 25.00%
PASS calibration bin 1 (0.25, 0.5, 2)
PASS calibration bin 2 (0.5, 1.0, 1)
PASS calibration bin 3 (1.0, 1.0, 1)
PASS registry refusal (exit 2) rc=2
PASS ruling-3 defect line
PASS raw timeout scored pair kept

FIXTURE TEST: PASS (all checks)
```

### 2.4 G3 checker — `gate_first_divergence.py`

For each unit: if the outcome fields and gamelog hash agree, the
unit is clean. Otherwise it runs `classify_divergence.py` on the
pair's traces (raw = A, teacher = B) and judges the FIRST
divergence: `within_row_hits` non-empty → defect; class DECISION
→ legal only if the teacher trace row at that seq is an overturn
(`decide_pick` ≠ argmax of `priors_pre`); games differing while
traces classify IDENTICAL → defect (`TRACE_GAP`); any other class
→ defect; a missing trace file → defect. Exit 1 on any defect.
Smoke output in §4.2 — both smoke units diverged and both were
legal overturns.

### 2.5 G4 audit — `audit_overturns.py` (job-emission half)

Reads the teacher stat rows (overturn count cross-check) and the
`TEACHER_SNAP_DIR` indexes (authoritative — only overturns
snapshot), samples up to 100 entries (seeded RNG, seed 20261019),
and emits jobs in exactly the format `meas_label_main.php`
consumes — `{snap_dir, snap, game, player, branch, cands,
selected, prior_pick, teacher_pick}` with `selected` = the two
picks under audit. The relabel run itself (k=50, `LABEL_W=50`,
fresh determinized rollouts under the current labeler) is
post-gate work, as registered. Smoke execution in §4.2:
stat overturns 6 = index entries 6 = jobs emitted 6.

### 2.6 G9 registry — `register_gate_ids.py`

Merges the fleet's per-chunk game-id files (tag `gate:<chunk>`)
and the snapshot ids from the teacher snap indexes (tag
`gate_snap:<chunk>`) into the registry in its existing format;
existing entries are never modified (a collision is reported,
the existing tag kept). Demonstrated on the smoke ids against a
**copy**: 550 → 561 games (5 game ids, 6 snapshot ids), copy
sha256 `10c61b870f…`. The real registry was not mutated —
verified after all box work: sha256
`b9ce2cb486a6607bf12ad97d3fbb34e576ac7371a4b9b5f01291717776fbe74d`,
still 550 games. The real merge is a launch step (§6) and the
analysis refuses to run without it (§2.3).

## 3. G8 — shared memory

### 3.1 The stale-segment cleanup (executed)

`kernel.shmmni` on the box: **4096**. At brief time the box held
3,225 segments; by execution time 3,221 remained, all with
`nattch == 0` (no game processes were running — verified by
process check before starting; the segments attached at brief
time belonged to processes that have since exited). The cleanup
(`gate_ipcs_cleanup.sh`, committed) saved the full `ipcs -m`
listing first, then removed **only** segments with
`nattch == 0`, one `ipcrm -m` per segment from the saved
listing. Result: **3,221 → 0 segments**. Evidence in
`data/gate-smoke/`: `ipcs_cleanup_before.txt` (the full listing),
`ipcs_cleanup_after.txt`, `ipcs_cleanup_attached_kept.txt`
(empty — nothing was attached at execution time).

Disclosure on the first attempt: the script's first run wrote
its evidence prefix into a directory that did not exist yet, so
its listing writes failed and it removed nothing (counts printed
3,221 → 3,221). The directory was created and the script re-run;
the 3,221 → 0 above is the second run, and its evidence files
are the ones committed.

### 3.2 Per-game cleanup in the teacher path, and what the smoke measured

The mechanism is §2.2's `TCG_CLEAN_CHILDREN=1` dir-diff +
`DeleteCache`, extending the R16 timeout-path cleanup to every
completed teacher-family game. What it found in practice, across
the three completed teacher games run for this package (smoke
§4 + probe §4.3): `children_found = 0` every time — a completed
game's rollout children wipe their own dirs and call
`DeleteCache` on their own segments (`search.php` lines 712/771,
1354/1388); the residue of a completed teacher game is exactly
**+1 segment, its own** (the `KEEP_GAME` game, harvested and
cleaned post-run). Segment count across the 4 smoke games:
+1 per game, teacher and raw alike. The cleanup mechanism's real
work is the killed-game case — a game SIGKILLed at the wall
timeout leaves its children's dirs and segments behind — which
the timeout path already cleans (proven in R16: 66 child ids
found and cleaned) and the completed path now also covers.

That measurement does not match the rerun ledger's ≈ +5 segments
per ghost game (ghost_s1 +94, ghost_s2 +69 over 19 games each),
and I have no verified explanation for the difference — the
ledger brackets whole arm runs, so anything else on the box in
those windows is inside the deltas. I am reporting both numbers
rather than reconciling them by conjecture. The planning
consequence is bounded either way: from the cleaned base, the
fleet's worst case at the rerun-ledger rate is ≈ 400 × 5 = 2,000
child segments + 800 own-game segments ≈ 2,800 < 4,096, and
`run_gate.sh` records `ipcs` before/after every chunk so the
trajectory is in the results whatever it is.

Judgment call, named: I did **not** build an `ipcs`-key sweep
(deleting detached segments whose game id has no live process)
into the driver. With four chunks running in parallel, a sweep
keyed on anything but the game's own children risks deleting
another chunk's in-flight state; the dir-diff mechanism cleans
exactly the ids the game's own tree produced, and the measured
completed-game orphan rate on this build is zero. The pre-launch
full cleanup (done above) plus the per-chunk `ipcs` record are
the compensating controls. If Claude wants the sweep as well,
it is a small addition — but it should be his call, since it
touches cross-chunk state.

### 3.3 Box-state disclosure (outside the gate machinery)

While cleaning up the §4.4 probe's server, I ran a `pkill`
pattern without the bracket camouflage this workspace's rules
require, and it matched more than the probe: it also killed a
long-lived leftover probe server from the October 18–19 work
(pid 2435384, `/tmp/probe.sock`) and left `/tmp/tcg_policy.sock`
as a stale socket file with no server behind it. No fleet or
measurement was running; no file was touched (the production
server file's hash is re-verified above); both were idle
leftovers, and any fleet start spawns its own servers. It is
recorded here because it changed box state beyond this package's
authorization, and the gate launch's server census should
expect those two sockets to be dead.

## 4. G10 smoke

Seed 1001 at seats 1 and 2, teacher + raw, on the gate tree,
per-seat servers from the gate tree, fleet conditions (timeout
700, traces on; teacher arms with `TEACHER_SNAP_DIR`,
`TCG_CLEAN_CHILDREN=1`, `GATE_GAME_IDS_FILE`). All four
manifests report `assert_ok: true`; every row carries
`server_seat` equal to its seat with 0 seat-mismatch errors; the
servers' counters for the seat-1 smoke server read fallbacks=0.

### 4.1 The four games

| unit | arm | secs | winner | turns | decisions |
|---|---|---|---|---|---|
| 1001 s1 | teacher | 131.6 | 1 (learner) | 13 | 643 |
| 1001 s1 | raw | 2.5 | 1 (learner) | 21 | 808 |
| 1001 s2 | teacher | 127.6 | 2 (learner) | 11 | 481 |
| 1001 s2 | raw | 2.2 | 2 (learner) | 15 | 622 |

Teacher times 131.6s / 127.6s — the 700s registration stands
(§1). Both units' games diverged (§4.2). Overturns: seat 1 game
4 of 25 contested (16.00%), seat 2 game 2 of 22 (9.09%), pooled
6 of 47 (12.77%) — see the watch items in §4.5.

### 4.2 The three smoke analyses (all in `data/gate-smoke/`)

- **Analysis on the smoke rows** (`smoke_analysis.txt`): a
  plumbing test — n=2 units, both tied (both arms won both
  games), Δ = 0. The band line it mechanically prints
  ("PROJECTION OVERSTATED") is the band table applied to two
  tied units and is **not a read of anything**. What it proves:
  rows → scoring → Δ/CI/discordants → monitors → calibration
  table all run end-to-end on real gate-shaped output, against
  the registry copy (the refusal path is fixture-tested, §2.3).
- **G3 on both units** (`smoke_g3.txt`), exit 0:
  `LEGAL seed=1001 seat=1 seq=322 class=DECISION overturn
  (decide_pick=0, prior argmax=1)`;
  `LEGAL seed=1001 seat=2 seq=372 class=DECISION overturn
  (decide_pick=1, prior argmax=0)`;
  `units identical=0 legal_diverged=2 skipped_invalid=0
  defects=0`. Both divergences begin exactly where the gate
  design says a teacher-vs-raw difference is allowed to begin.
- **Audit job emission** (`smoke_audit.txt`,
  `smoke_audit_jobs.jsonl`): stat overturns 6 = snapshot index
  entries 6 = jobs emitted 6, in the labeler's format.

### 4.3 Probe disclosure — one teacher game on gate seed 1002

To test whether completed teacher games orphan child segments
(the §3.2 question), I ran ONE additional teacher game, seed
1002 seat 1 (96.5s, learner lost, winner 2; row in
`data/gate-smoke/probe_teacher_s1.jsonl`; its game id was
registered on the registry copy with the smoke ids). Seed 1002
is inside the registered gate range — that was my error in
choosing a probe seed; I should have probed outside 1001–1200.
The game is not part of any fleet output and selects nothing
(the fleet runs all 200 seeds regardless of this game's
outcome), but the seed has now been played once by the teacher
arm outside the protocol. If Claude prefers, swapping seed 1002
for 1201 in chunk c1 restores a strictly-fresh seed set at zero
cost. The concurrency probe (§4.4) used seeds 3001/3002, outside
the range.

### 4.4 Concurrency probe — the fleet's one untested-by-design assumption

`run_gate.sh` runs four chunks against one server pair, so up to
four teacher games per seat-server run concurrently. The smoke
above is one-at-a-time; before asking for a launch I ran two
teacher games concurrently against the seat-1 gate server
(seeds 3001/3002): both completed (168.1s and 204.9s vs
96–132s solo — a ≈ 1.5× stretch), 0 seat mismatches, 0 connect
failures, server counters fallbacks=0 / seat_mismatch=0 over
94,299 evals. Rows in `data/gate-smoke/conc_*.jsonl`. Four-way
stretch is still unmeasured — §5.

### 4.5 Smoke watch items (observations on n=2 games, not reads)

- **Canary refusals, seat-1 game: 4 of 70 root calls = 5.714%**,
  above the G7 per-arm-seat cap of 2% — on a single game, with
  branches M 7.32% (3/41) and P 10.00% (1/10) named by the
  monitor. The seat-2 game had 0 refusals. The rerun's ghost s2
  coverage was already 1.891%, near the cap. If anything like
  the seat-1 rate held at fleet scale, that arm-seat breaches
  G7 — the gate's own coverage table will say so from 100 games
  per arm-seat, but Claude should see the smoke number now.
- **Overturn rate 12.77% pooled (6/47)** vs the ~5% expectation
  in G4. On 47 contested decisions the uncertainty is wide
  (a 95% interval runs roughly 5–26%), so this neither clears
  nor convicts the margin rule — it is the second thing the
  gate's full overturn table (400 games) will settle, and per
  G4 a fleet rate well above ~5% impeaches the margin rule
  before Δ is read.

## 5. What is NOT tested

- **The fleet at scale.** Four chunks × 100 games have never
  run. Untested at scale: 4-way server contention (2-way
  measured at ≈ 1.5× stretch, §4.4); the `ipcs` trajectory
  across 800 games (§3.2 bounds it, does not measure it);
  wall-clock for the fleet (serial estimate ≈ 3.7h per chunk
  at solo teacher times, longer under contention — an estimate,
  not a schedule).
- **The G4 relabel run.** Only job emission is exercised (§4.2);
  no snapshot has been relabeled at k=50 yet.
- **Teacher-timeout clustering.** If contention stretches the
  slowest teacher games (rerun max 233.1s solo) past 700s in
  clusters, ruling 2's > 2% threshold makes the gate
  inconclusive — that is the ruling working as designed, but
  the failure mode has never been observed and the package
  cannot rule it out.
- **The calibration monitor** has only plumbing evidence
  (both smoke games were learner wins, so every realized cell
  is 1.0). Its first informative run is the gate itself.
- **A capped or drawn fleet game** has not occurred in any
  smoke; cap/draw scoring is fixture-tested only.

## 6. Launch command, launch conditions, registered reads, the ask

**Launch command** (on the box, after approval + Joe's go; the
gate tree persists at `/tmp/gatetree_r4` — if the box's /tmp has
been reset, rebuild per §2.1 first and re-verify the built
hashes before launching):

```
cd /tmp/gatetree_r4 && setsid nohup bash run_gate.sh \
  > /tmp/gate_r4_launch.log 2>&1 < /dev/null &
```

**After the fleet, in this order (the order is a condition):**
1. Server census + reap check; read both fleet server logs in
   full (weights-loaded lines, fallbacks, seat_mismatch) — a
   result is not read until its server log is.
2. Raw-timeout re-runs have already run inside the fleet
   (`gate_raw_retry.py` per chunk-seat); any second-hang seeds
   are named in its output and scored per ruling 3.
3. **Registry merge on the REAL registry** (G9 — before any
   analysis):
   `register_gate_ids.py --registry
   /tmp/harvest/do_not_train_registry.json --ids
   /tmp/gate_r4/gate_c*_game_ids.txt --snap-index
   /tmp/gate_r4/gate_c*_teacher_s*_snaps/teacher_snap_index.jsonl`
4. `r3_pair.py` over the eight row files (outcome/hash pairing
   audit), then `gate_first_divergence.py` over all 400 units
   (G3 — any defect stops the read).
5. `analyze_gate.py` over the eight row files + eight stat
   files against the merged registry (it refuses otherwise).
6. `audit_overturns.py` job emission; the k=50 relabel run is
   scheduled as its own post-gate step.

**Launch conditions (carried from the pre-gate, with the gate
tree's own hashes):** built `search.php` `6cd6f980…`,
`policy_server.php` `64c21539…`, `rl/search_server.py`
`ab85fa1b…` (§2.1); production server hash before == after the
fleet (recorded by `run_gate.sh` into `gate_prod_hash.txt`;
pre-work value `81ef2cdbefe6…`); every chunk manifest
`assert_ok: true`; every row's `server_seat` equal to its seat.

**Registered reads (verbatim from the registration):**

| Result | Read |
|---|---|
| Δ ≥ +0.05 with CI lower bound > 0 | converts |
| Lower bound > 0 but Δ < +0.05 | real but small |
| CI includes 0 with upper bound < +0.10 | the projection overstated conversion |
| Δ > +0.20 | **impeach before reading** |

Plus the standing stops: any G3 machinery defect stops the read;
teacher timeouts > 2% make the gate inconclusive whatever Δ
says; canary refusals > 2% per arm-seat breach G7 coverage;
a fleet overturn rate well above ~5% impeaches the margin rule
before Δ is read (G4); the G5 calibration shape is reported
with the result, and the void-gate pattern (predicted running
ahead of realized, climbing by ordinal) impeaches the run.

**The ask:** Claude's launch approval of this package — the
design (§1), the fleet and analysis code (§2), and the reads
above — and then Joe's go in the main chat. The builder does
not launch on this commit.

## 7. Judgment calls in this package (collected)

1. Fleet timeout **700s** = 3 × 233.1s = 699.3s rounded up to a
   round number (§1).
2. One server pair for the whole fleet rather than per-chunk
   servers (§2.2, §4.4).
3. Cap scoring read per-arm (§1, ruling 1) — the fixture encodes
   it; if Claude intends a capped game to zero the whole unit's
   contrast instead, the change is one function and one fixture
   row.
4. Calibration predicted probability = (prior-pick rollout
   mean + 1) / 2, from the rollout outcome semantics in
   `search.php` (§2.3).
5. G8 per-game cleanup as the R16 dir-diff extension, with no
   cross-chunk `ipcs`-key sweep (§3.2).
6. The seed-1002 probe (§4.3) — an error in seed choice,
   disclosed with its outcome and a zero-cost swap offer.
