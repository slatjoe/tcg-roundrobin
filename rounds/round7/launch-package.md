# Round 7 — the §8 package (O1 finding, the sweep, the placement, the pre-gate runner)

**Parent:** 2c3b84675f883a63ff0d860201ec9d546aa0ba54 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-51f35d9.md` §§1–5 and §8 (the four items the next package was to carry). Context: `rounds/round7/fleet-alignment.md` (the registration this package extends) and `rounds/round7/stage4-tree-build.md` (the tree build, accepted).
**Status: THE O1 MECHANISM CANNOT BE BUILT AS SPECIFIED — the escaped children's SHMOP keys are not recoverable from any record (§1). The build stopped at that finding, as instructed: no cleanup code was written, no driver revision exists, and `search.php` is byte-identical (re-verified `8f6b35da…` in the built tree after all work below).** What the package does carry: the key derivation and the records audit (§1), the ordered residue sweep with its counts (§1.6), the extended probe's status — **not run**, because the reply gates it on the mechanism (§2), the pre-gate runner as reviewed code (§3), the driver placement recorded as the tree's second change (§4), and the two report-only diagnostics settled from the code and the fleets' own stat rows (§5). The K3 pre-gate, the teacher and the stage-5 fleet remain held.

**Package contents**

| File | Role |
|---|---|
| `launch-package.md` | this document |
| `code/run_gravy_pregate.sh` | §3: the K3 pre-gate runner (full text, **not run**), sha256 `19cb3c13c92ed62182b35f676b30e600fd2b173a292b887366c247e2ce589ddd` |

`code/paired_driver_gravy.py` and `code/run_gravy_gate.sh` are **unchanged** by this package — with no mechanism there is no driver revision, so the §1 pins stand exactly as approved (`0a6b7a85…` / `0c458627…`).

---

## 1. O1 — the SHMOP key derivation, the records audit, and the stop (reply §3, §8.1)

### 1.1 How a segment key is derived (from the code)

Every game name carries two shared-memory segments, both written through `vendor/talishar/Libraries/SHMOPLibraries.php`:

- the lobby cache: `WriteCache($name, …)` opens key **`$name` itself** (:33);
- the gamestate cache: `WriteGamestateCache($name, …)` opens key **`GamestateID($name)`** (:46–48), and `GamestateID($gameName)` is **`$gameName + 1000000`** (:146–149).

`DeleteCache($name)` (:133–144) removes both. A rollout child creates its gamestate segment when it parses its copied state: `SimLabel_RunRollout` sets `$GLOBALS["gameName"] = $childGame` (search.php:1377) and calls `ParseGamestate()` (:1396), whose cache write is the `WriteGamestateCache` above. So a child's leaked segment sits at key **`$childGame + 1000000`** — *if the child's id were known*.

### 1.2 The id is random, generated inside the child, and never leaves it

`search.php:1374` (and, for the ISMCTS sibling path, :691):

```php
$childGame = (string)random_int(100000000, 999999999);
```

The fork happens in the parent (`SimTeacher_DecideInner`, :949–956); the id is drawn **after** the fork, inside the child. The parent never sees it. The only channel back is the per-world result file (`tch_res_<parentpid>_<rand>_<cand>_<world>.json` in the system temp dir), and its contents are enumerable from the code — on every path it carries either an `error` string (:1391, :1397, :1417, :1435) or the outcome payload `det_persisted / winner / outcome / finished / turns / hooks / fallbacks / child_state` (:1423–1432). **No field carries the child game id, on any path.** The parent unlinks each result file as it is read (:970–971).

### 1.3 The leaking paths are exactly the ones that erase the id

`SimLabel_RunRollout`'s exits, read in full (search.php:1370–1440):

| Exit | Result written | Dir wiped | `DeleteCache` | Segment |
|---|---|---|---|---|
| success (:1423–1433) | outcome payload | yes | **yes** (:1433) | cleaned |
| det-verify failure (:1396–1401) | `det_verify_failed` | yes | **yes** (:1399) | cleaned |
| det-persist failure (:1390–1395) | `det_persist_failed` | yes | **no** | **leaks if created** |
| `SimSearchAbort` catch (:1416–1420) | error string | yes | **no** | **leaks** |
| outer `Throwable` catch (:1440–1442) | error string | no | no | found by the driver's dir diff |
| parent SIGKILL at the 180 s deadline (parent :985–988) | none | no | no | found by the driver's dir diff |

The abort catch is the measured leak (the probe's 339 `abort` reasons; the +712 segment rise tracked the 711 errored children). The child's directory — whose *name* is the only durable form the random id ever takes — is removed by the child itself on that path (`SimSearch_WipeDir`, :652–655), before the driver's post-game diff can see it. The driver's existing cleanup (stock `paired_driver.py:407–433`, the G8 per-game child sweep) diffs `Games/` before/after each game and `DeleteCache`s the *surviving* child ids; it cleaned 58 children across the probe (`children_found == children_cleaned`) — precisely the non-self-wiping classes in the table's last two rows. The self-wiped classes are invisible to it by construction, not by oversight.

### 1.4 No other record carries the id

- **Teacher stat rows** (the `SimSearch_LogStat` record assembled in `DecideInner`, :1004–1013 and its tail): per contested decision they carry branch, player, turn, candidate set, priors, `means`, **`n_worlds`**, `canary_worlds`, `errors`, `child_fallbacks`, `abort_reasons`, `abort_by_cand`, and (in the fleet rows) `game` — the **parent's** id. Counts and reason strings only; no child id appears in any field (verified against the probe's own stat rows on the box, `/tmp/fleetprobe/*/search_stats.jsonl`).
- **Server logs:** the search server's stats lines carry aggregate counters (`fallbacks`, `seat_mismatch`); the only `STDERR` write in the child path is the seat-mismatch line (search.php:459), which carries no game id.
- **`ipcs` itself:** segment keys are bare integers. A child's key (`random id + 1,000,000`) occupies exactly the same numeric space as a parent game's, segment sizes vary (the current census: 2,192 × 32,768 B, 145 × 65,536 B, 568 × 131,072 B, 1 × 128 B), and residue shows `nattch` 0 — nothing in a listing attributes a segment to a game, a child, or a run.

### 1.5 Verdict, and what was therefore not built

**Given a finished game's records, the set of its errored children's segment keys cannot be computed.** The id is random, parent-invisible, written into no result file, stat row or log, and its only named trace (the child's directory) is deleted by the child on exactly the paths that leak. A cleanup keyed to "exactly that game's errored children" has nothing to key on. Per the build instruction for this package, the mechanism build **stopped here**: no cleanup code exists in this package, the launch-copy driver is unrevised (pin unchanged, §4), no sweep-while-running was improvised, and `search.php` was not touched.

### 1.6 The box test that could not run — and the sweep that did (reply §3, "and now")

The scoped box test (delete exactly the probe's residue, count the drop) cannot be executed: §1.4 is precisely the statement that the probe's segments are not identifiable inside the residue mass. What was executed is the order that does not depend on attribution — **the standing G8 sweep of the whole residue**, under its recorded criteria (round-3 builder-response-6a0d7d4 §3.1), on 2026-10-22:

- Preconditions verified first: no `play_game`, `search_server` or driver process on the box (only the idle spectate `php -S` from October 19); all segments joe-owned; **attached segments: 0** (nothing was kept back — there was nothing attached to keep).
- Full listing saved *before* (`/home/joe/tcg/registry-vault/ipcs-20261022-presweep.txt` on the box), then one `ipcrm -m` per segment with `nattch == 0` from that listing.
- **Counts: 2,906 segments → 0.** (2,910 in `ipcs -m | wc -l` terms, the figure the earlier packages quoted — the difference is the listing's header lines.) The probe's ~712 are inside the removed mass, along with all older residue; the post-sweep listing is saved alongside (`ipcs-20261022-postsweep.txt`, `ipcs-20261022-attached-kept.txt` — the last, empty).

The box now sits at a clean baseline. Any further teacher game re-opens the leak at the measured rate (~178 segments per teacher game) with no scoped way back — which is why §2 stands as it does.

### 1.7 The fork this leaves (for the ruling, stated from the code)

The reply named the last resort itself: a reviewed change to `search.php`'s cleanup paths, with a proof that no decision path is touched. The code localizes what that change would be, stated here as fact for the ruling, not as a proposal smuggled past it: in the two leaking catches, the result file is written **before** the wipe (`file_put_contents($resFile, …)` precedes `SimSearch_WipeDir` in both :1391–1395 and :1416–1420), and everything a decision consumes flows through that file — so a `DeleteCache($childGame)` added beside the wipe in those two catches executes after the child's result is already fixed, on a path that computes nothing. It would change two lines of the teacher's bytes (the K2 pin moves, the tree rebuilds, the ghost pre-gate re-proves identity against raw), which is exactly the cost the reply weighed. The alternative on the table is operational: bound teacher work to the headroom a pre-run sweep leaves and re-sweep between runs — from a fully swept baseline that headroom is ≈ 3,600 segments, ≈ 20 teacher games at the probe's rate before the operator stop (the reply's §3 arithmetic put it at ~8 games from the then-standing 2,194 baseline) — arithmetic, not a mechanism, and far short of a 400-game fleet in any single run. This package takes no position between them; it records that a records-keyed mechanism — the shape the reply required first — does not exist.

---

## 2. The extended probe — not run (reply §2.2, §8.2)

The extended probe is gated twice on the mechanism: the reply's §2.2 ("this must happen **after the O1 mechanism is in place**… at the measured leak rate, 16 more games would exhaust SHM") and §3 ("a leak-containment mechanism, registered and reviewed **before any further teacher game** — that includes the extended probe"). With §1's verdict, running the waves would spend ~2,800 segments of a just-swept box to calibrate a timeout for a fleet that still cannot launch. **The waves were not run.** Consequences, stated plainly:

- **`GATE_TIMEOUT` stands at 3,311 s** — the value from the original four probe games (fleet-alignment §3.2), none of which reached trigger 62. It is carried as an *unextended* value; **no launch value is claimed from it**, and the timeout question returns with the O1 ruling: if teacher work resumes, the extended probe (waves of 4 from seed 3007, stop at the first wave containing a trigger-62 game, or 16 games) runs then, under whatever containment the ruling establishes, and restates the timeout from all probe games.
- **Registry: unchanged by this package** — 4,975 games, sha256 `fdbc66bd…` (re-verified on the box at writing). No new probe games exist to register.
- **Fleet wall estimate: not redone** — no new games; the ~15–18 h planning figure (fleet-alignment §V) stands as the estimate of record.

---

## 3. The pre-gate runner (reply §5/O5, §8.3)

`code/run_gravy_pregate.sh` — 10,647 B, sha256 `19cb3c13c92ed62182b35f676b30e600fd2b173a292b887366c247e2ce589ddd`, `bash -n` clean. **Written, not run.** It implements followup-k1-k3-fix §3 as registered; the mapping:

| Registered element (§3) | Runner |
|---|---|
| 20 units, seeds 8501–8510 × both seats, on the fleet's per-seat servers with `SEARCH_MODEL` = the selected checkpoint | `SEEDS=8501-8510`; `start_server` per seat on `/tmp/ggate_s<seat>.sock` (lines 140–155); arms at lines 166–169 |
| Ghost arm `--arm ghost`, raw arm `--arm raw`, invocations in the registered shape | `run_arm` (lines 157–165) called at 166–169, then the determinism re-run (171–176) |
| (a) determinism: second raw run at seat 1, read IDENTICAL 10/10 **before** the ghost comparison; any difference stops the pre-gate | lines 181–191 (count of IDENTICAL verdicts in the `r3_pair.py` table must reach 10, else exit before any ghost read) |
| (b) standing raw control (R16): the pre-gate's own raw runs across seats must differ on ≥ 1 seed | lines 194–200 (`--raw-control`, `RAW-CONTROL: PASS` required) |
| Ghost-vs-raw pass read through `r3_pair.py` / `classify_divergence.py`, per unit | lines 203–210 (per-seat pairing tables written for the launch-package read; the K5 marker disposition stays a read-time act, as registered) |
| Tree pins before any game (K2 + §1 of the reply: *every* runner that plays games from this tree) | `expect_hash` block, lines 83–103: `search.php` `8f6b35da…`, `featurize.php` `f81193e0…`, `rl/search_server.py` `ab85fa1b…`, `paired_driver.py` `0a6b7a85…`, `gate_raw_retry.py` `c3fb227e…`, and the selected checkpoint itself `44f1e5d7…` |
| `GATE_TIMEOUT` from the probe, as a required input | `TIMEOUT=${GATE_TIMEOUT:?...}` — no default, no inherited Fai value |
| O1 surface + `ipcs` records (reply §5) | ipcs listing + count at start (lines 108–109) and end (lines 229–230); the guarded standing G8 sweep (`PREGATE_SWEEP=1`, lines 114–127: refuses while game processes live, saved listing, `nattch == 0` only). **The runner's header states the open dependency in terms: no per-game containment exists (§1), and teacher games before the O1 ruling risk the ceiling mid-pre-gate** |
| Server evidence: checkpoint loaded, fallbacks = 0 | load lines captured (lines 214–216); a nonzero `fallbacks=` in either server log stops the run (lines 217–221) |
| Register the pre-gate's ids, backup first | final step (lines 235–245): vault backup, then `register_gate_ids.py` on the shared ids file + both ghost arms' `teacher_snap_index.jsonl`. The ids files carry no `c<digit>` token, so the tool's own fallback applies — games land under `gate:gate`, snapshots under `gate_snap:gate`, stated here so the tags surprise no one |

The production server's sha256 is recorded before and after, as in the fleet runner.

---

## 4. The driver placement — the tree's second change, recorded (reply §1, §8.4)

The launch copy (`code/paired_driver_gravy.py`, `0a6b7a85…` — unchanged in this package) was placed as **`/tmp/gravytree/paired_driver.py`** on 2026-10-22, after the tree build; the on-box bytes were hash-verified before and after the copy. The recursive diff was re-run:

- **Source files: exactly two differ** between `/tmp/otree` and `/tmp/gravytree` (`diff -rq -x __pycache__ -x Games`):
  - `probe_swap20.php`: otree `6993ece4…` → gravytree `400a9215…` (the tree build's one substitution);
  - `paired_driver.py`: otree `1e312629…` (stock) → gravytree `0a6b7a85…` (the launch copy, this placement).
- **`gate_raw_retry.py` in the tree still hashes `c3fb227e…`** — unchanged stock, as the reply requires shown.
- The two excluded classes, for completeness: `__pycache__/*.pyc` (four files) differ as bytecode — their `.py` sources are byte-identical between the trees (verified file by file); and `vendor/talishar/Games/` holds runtime state, not tree content — the only otree-only entries are the four probe games' KEEP_GAME directories (`124215338`, `994878080`, `620429434`, `422680924`), created by the probe running on otree after the tree was copied.

No runner revision was needed: the fleet runner's pin already names `0a6b7a85…`, and the pre-gate runner (§3) pins the same bytes.

---

## 5. The fleet's report-only diagnostics, settled (reply §4)

**(a) Per-candidate finished counts — YES, the stat rows carry them.** `SimTeacher_DecideInner` assembles each contested decision's record with `n_worlds`: a map from candidate index to that candidate's **finished**-world count (search.php, the `$base` record at :1004–1010; worlds per candidate K = 25). The field is present in the recorded rows of all three fleets (key census over the Fai, O and probe stat files agrees). The registered diagnostic is therefore computable from the fleet's stat rows as recorded, with no code change: **for every row with `overturn = 1`, report the winning candidate's unfinished count `25 − n_worlds[pick]` against the prior's `25 − n_worlds[prior_pick]`, pooled and as a distribution** — the read that shows whether overturns lean toward stall-prone candidates, whose means are computed over fewer, finished-only worlds. Report-only; it ships with the fleet analysis.

**(b) Thin-prior rates — the Fai fleet's is recoverable, and it is zero.** Counted on the box from the fleets' own `search_stats.jsonl` (contested teacher rows; a row counts as thin-prior iff it carries `fallback = "thin_prior"` — the field the O build sets on exactly that path):

| Fleet | Contested decisions | thin_prior | Rate |
|---|---|---|---|
| Fai gate (`/tmp/gate_r4/gate_c*_teacher_*_log`) | 10,869 | 0 | **0.0%** |
| O measurement (`/tmp/o_fleet/o_c*_teacher_*_log`) | 10,648 | 0 | **0.0%** |
| Gravy probe (`/tmp/fleetprobe`) | 75 | 20 | **26.7%** |

Both earlier fleets did record errored children (1,301 and 1,576 in total) — but never enough in a prior candidate to drop it below 20 finished worlds, so the fallback never fired. The dilution the reply flagged is a Gravy-length phenomenon: on Fai the teacher's pick was never the raw pick *by fallback*; on Gravy, at the probe's rate, about a quarter of contested decisions would be. Report-only, as registered — the fleet analysis reports the Gravy fleet's own rate beside these.

---

## 6. What happens on the ruling

Nothing in this package launches. The decision it puts is the O1 fork of §1.7. If the ruling is the reviewed `search.php` cleanup change: a follow-up package carries the two-catch diff, the new K2 pins and a rebuilt tree, the ghost pre-gate re-proves the teacher against raw, the extended probe then runs (§2's registered form) and restates `GATE_TIMEOUT`, and the pre-gate (§3's runner, re-pinned if the tree moves) launches on Joe's go — the fleet separately, on Joe's go, under a launch manifest carrying the §3.2 hashes and the restated timeout. If the ruling is operational containment (sweep-bounded runs) or another shape entirely, the next package builds to that instead. Either way the pre-gate and the fleet each still need Joe's go, and approval of this package certifies the finding and the code as written — §1's verdict is a statement about the records, and it stands or falls on the code cited there.

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude reviews.*
