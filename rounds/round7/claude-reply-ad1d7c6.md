# Claude — reply to the §8 launch package (the O1 stop-finding, the pre-gate runner)

**Reviewed commit:** ad1d7c6843e730faf05b4d06fa705e75e4eb4ab8 (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-51f35d9.md` hashes to `a8a26924…37dcf8cc`, the value I gave Joe.
**Package:** `rounds/round7/launch-package.md` and `code/run_gravy_pregate.sh` (sha256 `19cb3c13…2ce589ddd`, verified).

**Verdict:**
- **The stop-finding is ACCEPTED.** The build was right to stop, and the fault is in my specification, not the build (§1).
- **The fork is ruled** (§2):
  - **(C), a new route, preferred:** contain the leak by **kernel attribution** rather than by the records. A segment whose creating and last-attaching processes are both dead, and which belongs to no game directory that still exists, is garbage. That's provable outside the teacher.
  - **(A), the two-line `search.php` change:** accepted as the fallback, with conditions.
  - **(B), sweep-bounded runs:** rejected for the fleet, accepted for the pre-gate and the probe.
- **The extended probe is RELEASED now**, under quiescent sweeps between waves. Three things become possible at once: it measures the timeout, it measures the leak again, and it carries (C)'s selector as a dry run (§3).
- **The sweep and the placement are ACCEPTED** (§4).
- **The pre-gate runner: CHANGES REQUESTED**, four items (§5).
- Both report-only diagnostics are settled. The thin-prior contrast (Fai 0%, Gravy 27%) gets a reporting rule for stage 5 (§6).

## 1. The stop-finding

**It's established from the code:**
- `GamestateID(name) = name + 1000000`.
- The child's id comes from `random_int` *after* the fork (:1374), so the parent never sees it.
- The result file's fields are listed on every path, and none of them carries the id.
- The two leaking exits (the abort catch and the det-persist failure) are exactly the ones that wipe the child's directory, the id's only named trace.
- The driver's sweep based on diffing `Games/` finds only the classes that don't wipe themselves. That's the 58 it cleaned.
- `ipcs` keys are bare integers in the same numeric space as parent games.

Given a finished game's records, its errored children's keys cannot be computed.

**The fault is mine.** I specified a mechanism "keyed to that game's errored children" *from the records*, and the records were the wrong place to look. Stopping at the finding, rather than improvising a sweep while games run or touching `search.php`, was the instruction followed exactly.

## 2. The fork

### (C) Kernel attribution: preferred, to be built and verified

The kernel records what the records don't. `ipcs -m -p` gives each segment's **creator pid (cpid)** and **last attach/detach pid (lpid)**. An errored child creates its segment, attaches and detaches it, and dies, so both pids are dead. A live game's segments have a live lpid, because the game process keeps writing them. On top of that, every live game, and every child that hasn't yet wiped itself, has a directory in `Games/` whose name gives its two keys.

**The selector.** A segment is selected iff all of these hold:
1. it is owned by joe, and `nattch == 0`
2. its **cpid is not a live process** and its **lpid is not a live process**
3. its key is not in {n, n + 1,000,000} for any directory n currently present under `vendor/talishar/Games/`
4. it was created after the run began (from `ipcs -m -t` / `ipcs -m -c`, or a pre-run listing: exclude any shmid present at run start)

**Why errors only go the safe way:**
- If a dead pid has been reused, the process looks alive, so the segment is **kept**.
- A live game is protected twice: by its live lpid, and by its directory.
- Rule 3 also covers a short-lived setup process that creates a segment a live game later opens by key, because the game's directory exists from the start.

The selector never reaches into `search.php`. It runs from the runner as a periodic sweep (every 60 s, say) alongside the chunks, and calls `ipcrm -m` per selected shmid.

**Before it's approved, the builder must show on the box:**
- **(i)** that `ipcs -m -p` reports cpid and lpid for these segments, and that the PHP `shmop` calls update lpid. Quote the PHP version and the kernel's `shm_lprid` semantics, or show it empirically on one game.
- **(ii) A dry run during the extended probe** (§3). The selector runs every 60 s **without deleting** and logs, per pass, the shmids it would select, with key, cpid, lpid and attach/change times.
- **(iii) The false-positive test.** No logged shmid may show a later attach time, a later change time or a later lpid change than at its selection. Any one that does is a segment someone was still using, and that fails (C).
- **(iv) The coverage test.** At each wave's end, with everything quiescent, the selector's cumulative set must account for the wave's residue, apart from segments explicitly excluded by rule 3. Report the counts. A KEEP_GAME parent's own segments are excluded while their directories remain. State how many those are per game, from the G8 notes and the listing.

If (ii)–(iv) hold, (C) comes back as code (the selector, the runner integration and their hashes) and becomes the fleet's containment.

### (A) The two-line `search.php` change: the fallback

The localization is correct. In both leaking catches, `file_put_contents($resFile, …)` comes before the wipe, and a decision consumes nothing but that file. So a `DeleteCache($childGame)` beside the wipe runs after the child's contribution is fixed, on a path that computes nothing.

**If (C) fails, (A) is approved in principle on these conditions:**
- the diff, exactly two lines
- the new K2 pin
- the tree rebuilt from `/tmp/otree` plus the change, plus the two recorded substitutions, with the recursive diff showing three files
- the ghost pre-gate run on the rebuilt tree
- one disclosed replay: a teacher-arm game on a probe seed, run on the old and new trees, that must be **IDENTICAL** through `r3_pair.py` with within-row hits 0. That proves the change touches no decision on a real Gravy game, not only by argument.

The cost is what you say it is: the teacher stops being byte-identical to O's, and the report carries that.

### (B) Sweep-bounded runs: rejected for the fleet

From a clean baseline, the headroom is about 20 teacher games. The fleet runs four chunks continuously and is never quiescent, and its timeout was calibrated under exactly that four-way contention. Breaking it into about 20 bounded runs would change the instrument. **For sequential work, though, (B) is enough as it stands:** the pre-gate's arms run one after another, and the probe runs in waves. §3 and §5 use it there.

## 3. The extended probe: released

The box sits at a clean baseline (0 segments). At about 178 per teacher game, a wave of 4 adds about 712. So waves with a quiescent sweep between them fit easily. **I withdraw my §3 condition** ("before any further teacher game, including the extended probe") for the probe only.

**The probe runs in the registered form** (fleet-alignment §3, my 51f35d9 §2.2):
- waves of 4 concurrent teacher games, seeds from 3007
- stop at the first wave containing a game that reaches trigger 62, or after 16 games
- `GATE_TIMEOUT = max(700, 3 × the slowest game over all probe games)`

It runs **on the built `/tmp/gravytree`** with the pinned driver, using the K2 and §1.4 hash checks before the first wave. These additions apply:
- **Between waves:** the standing G8 sweep (`gate_ipcs_cleanup.sh`), whose guard checks only `play_game` and `paired_driver`, so the Python servers may stay up. (Check `search_server.py` for SHM use: the repo copy has none, so confirm on the tree's copy.) Before and after listings are kept per wave.
- **Ceiling check:** before each wave, abort if the count is above 2,800.
- **The (C) selector in dry-run mode** throughout (§2 (ii)).
- **Per game, report:** wall, turns, decisions, cap state, contested decisions, thin-prior count, the stat-row `errors` and `abort` counts, and the segment rise per wave.
- **Register all ids,** games and snapshots, as before. The probe runs on its own on Joe's go. It's not the pre-gate.

## 4. The sweep and the placement: accepted

**The sweep:**
- preconditions checked: no game, server or driver process; all segments owned by joe; 0 attached
- listing saved before, one `ipcrm` per `nattch == 0` segment from the listing, listing saved after
- **2,906 → 0**, with the attached-kept file empty

That's the standing G8 form exactly.

**The placement:**
- recursive diff with `__pycache__` and `Games` excluded: **exactly two files**, `probe_swap20.php` and `paired_driver.py` (`1e312629…` → `0a6b7a85…`)
- `gate_raw_retry.py` still `c3fb227e…`
- the `.pyc` exclusions are explained file by file, and the otree-only `Games/` entries are the four probe games

`search.php` was re-verified at `8f6b35da…`.

## 5. The pre-gate runner: changes requested

What's right:
- the pins: K2, the driver, the retry, and the **checkpoint itself**, a good addition
- `GATE_TIMEOUT` and `GRAVY_MODEL` required, with no defaults
- the arm order
- determinism read **before** the ghost tables
- the R16 control through `--raw-control` (I checked that `RAW-CONTROL: PASS` is the tool's own string)
- a fallbacks stop
- the production-server hash recorded before and after
- the ghost read left to the launch package for K5's sake

**Required:**

1. **Parse the determinism check; don't grep it.** `grep -c IDENTICAL` counts verdict cells, but the registered criterion also requires **within-row hits = 0** and **outcome equal = True**, and `r3_pair.py` prints those as **separate columns**. The verdict cell folds in only the assert, seat and mode checks. As written, a pair with outcome-equal False, or with within-row hits, would still count. Parse the table: exactly 10 data rows, each with verdict `IDENTICAL`, hits `0`, outcome `True`, modes, seat and assert `True`. Anything else stops the run. Use the same parser for the launch package's ghost read.
2. **Containment inside the run.** The ghost arms are 20 teacher-machinery games, about 3,560 segments at the probe's rate: the whole headroom. The arms run one after another, so (B) is enough:
   - **sweep with `PREGATE_SWEEP=1` at the start (required, not optional)**
   - run the standing G8 sweep after `ghost_s1` and again after `ghost_s2`; the servers may stay up under the G8 guard
   - before each arm, abort if the count is above 2,800
   - keep the listings
3. **`TCG_CLEAN_CHILDREN=1` on the ghost arms.** It's in the fleet's teacher-arm environment, but the registered pre-gate invocation omits it. That's my omission when I registered K3. It runs after each game ends, so it can't touch a trace. And it cleans the children that don't wipe themselves (the timeout-killed and Throwable classes), which also leak. **Registered now** as part of the pre-gate's form.
4. **The registry step points at snapshot indexes that won't exist.** The driver sets `TEACHER_SNAP_DIR` only for the `capture` arm (:248–250). The fleet runner sets it externally for teacher arms, but neither the registered pre-gate invocation nor this runner sets it for ghost. Capture is conditional on that variable (`patch_teacher_capture.py:39`). So the `--snap-index` paths will be missing. Either drop the `--snap-index` arguments (ghost writes no snapshots, so there's nothing to quarantine; state it), or set `TEACHER_SNAP_DIR` for ghost and keep them. **Prefer dropping:** the pre-gate's job is identity, not harvest. Also check each driver call's exit code, and stop on non-zero.

**The tags** (`gate:gate` from the tool's fallback): accepted as disclosed. The registry's job is exclusion, and the launch record lists the pre-gate's ids against their tag.

## 6. The report-only diagnostics

- **(a) Per-candidate unfinished counts:** `n_worlds` is present in all three fleets' stat rows, and the diagnostic is defined: for overturns, `25 − n_worlds[pick]` against `25 − n_worlds[prior]`. Accepted, and it ships with the fleet analysis.
- **(b) Thin prior: Fai 0/10,869, O 0/10,648, the Gravy probe 20/75.** This is a substantive finding.
  - On Fai, the teacher never fell back to the raw pick for lack of finished worlds.
  - On Gravy, about a quarter of contested decisions would. Each such decision plays the raw pick, so it contributes exactly 0 to the paired Δ.
  - So a Gravy Δ is a mix: teacher-vs-raw on the decisions the search could actually evaluate, diluted by a large share it couldn't.

  **Registered for the stage-5 report, report-only, no band attached:**
  - the fleet's thin-prior rate
  - its overturn rate among **non-thin** contested decisions, against the 12–16% null band
  - a sentence in any null or weak read saying how much of the teacher's decision surface fell back

  A Gravy null must not be read as "search doesn't help" when it may partly mean "search couldn't run". The fresh probe numbers from §3 will show whether 27% holds.

## 7. Sequence from here

1. **The extended probe** (§3) on Joe's go: the timeout restated, the leak re-measured, and the (C) dry run with its tests.
2. **(C) as code**, if (ii)–(iv) pass. Otherwise **(A)**, under §2's conditions.
3. **The pre-gate runner revised** per §5 (re-pinned if the tree moves under (A)), then the pre-gate on Joe's go.
4. **The fleet**, with the restated `GATE_TIMEOUT` and (C) or (A) in place, on Joe's go.

## Not reviewed

These are on the box, and I took them from the package:
- `SHMOPLibraries.php`
- the `search.php` line references beyond those quoted
- the stat-row census
- the sweep listings
- the placement diff

**Scope:** this reply accepts the O1 finding, rules the fork ((C) preferred, (A) as fallback, (B) for sequential work only), and releases the extended probe under §3's containment, on Joe's go. It accepts the sweep and placement records, requests four changes to the pre-gate runner, and registers the stage-5 thin-prior reporting. **It approves no pre-gate and no fleet launch.** Approval certifies the build as written, not the run as executed.
