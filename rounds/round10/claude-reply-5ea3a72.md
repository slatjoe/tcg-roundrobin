# Claude — review of the Step 2+3 fleet repair (package §18)

**Reviewed commit:** 5ea3a723b93fc581b330b14c4df61c0f83df85d4 (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the non-blocking fix pass at 7f906f9b and `step2-fleet-launch-facts.md`. The committed `claude-reply-5b5ada4.md` hashes to `dd6d4a67…fb4a1807`, the value I gave Joe.

**Verdict: NOT CONFIRMED. The repair is necessary but nowhere near sufficient.**
- I checked `run_fleet_games.sh`'s server and driver blocks against the **actual** contracts of the pinned server and driver.
- **Adding `SEARCH_MODEL` fixes the first of at least five defects.** The relaunch would abort at the very next line, and every defect after it is in the same blocks.
- **The games runner was not built on the pilot's working blocks**, and it has never run a game.
- **I approved 5b5ada42 without checking this.** My review covered the build, the gate, the bands and the sizing, and I never set the spawn and driver blocks against `run_pilot.sh`, which had just run 100 games successfully. That's my miss.

## 1. The defects, each verified from the pinned sources

The pilot's games blocks (`run_pilot.sh`, lines 245–247 and the driver calls) are the working reference. The L3 runner, `run_fleet_l3.sh`, uses the same correct form.

| # | `run_fleet_games.sh` (teacher TS-SRV/TS-DRIVERS, raw RS-SRV/RS-DRIVERS) | The actual contract | Effect |
|---|---|---|---|
| 1 | No `SEARCH_MODEL` | The server requires it (`search_server.py` 81ef2cdb, l.39/68–69) | Launch 2's abort. **Fixed by §18.** |
| 2 | Server given `--socket /tmp/pol_<port>.sock --port <port>` | The server **reads no argv**. The socket is `TCG_POLICY_SOCK` (l.38), default `/tmp/tcg_policy.sock` | Both servers bind the **same default socket**, and the drivers' `--sock /tmp/pol_<port>.sock` doesn't exist |
| 3 | No `TCG_LEARNER_SEAT` | l.41, default **1**. The server answers the learner seat with v10 and the other seat with the opponent policy (l.225) | **The seat-2 blocks would play the teacher's own non-search decisions with the heuristic**, a silent corruption of half the fleet |
| 4 | No `TCG_OPP_MIX` | l.40, default `heuristic:1.0` | Happens to match, but only by default. The pilot sets it explicitly |
| 5 | Readiness: `grep '"ready": true'` | The server prints `search model loaded (…)` and `listening on …`. **The string `"ready": true` occurs nowhere in it** | **The §18 relaunch would abort at "teacher server 18241 not ready"** |
| 6 | Driver given `--max-turns`, `--cap-trigger`, and no `--deck` | `paired_driver_gravy.py`'s argparse (l.217–226) has `--tree --sock --seat --arm --seeds --out --logdir --deck --timeout` only | **Every driver exits 2 on unrecognized arguments.** The deck falls back to a hard-coded default path instead of the hash-pinned tree deck |
| 7 | `cd "$SIM" && rl/search_server.py`, the **production** server | The pilot's and Stage 3's **games** ran on the tree's **patched** server (`$GTREE/rl/search_server.py`, `ab85fa1b…`, pinned) | The games would run on a different server binary from the pre-gate's and the pilot's |

Two smaller departures from the pilot form: `TCG_CLEAN_CHILDREN=1` is absent, and the sweeper is a single loop rather than one per tree.

**Why 135 checks pass:** every fixture stubs the server and the driver. The new `fx_fleet_server_env.py` asserts a literal line, which is the text-level coverage §18.4 itself names as its limit. **No fixture composes a spawn against the real server's env reads, or a driver call against the real argparse.**

## 2. Required: rebuild the games runner's spawn and driver blocks from the working ones

1. **Fork, don't author.**
   - TS-SRV, TS-DRIVERS, RS-SRV and RS-DRIVERS become **verbatim forks** of the pilot's games-server and driver blocks: tree-local patched server, `TCG_POLICY_SOCK` per seat, `TCG_LEARNER_SEAT=$seat`, `SEARCH_MODEL="$CKPT"`, `TCG_OPP_MIX="heuristic:1.0"`, the `search model loaded` readiness check, `--deck "$tree/$DECK_REL"`, `TCG_CLEAN_CHILDREN=1`, and one sweeper per tree.
   - The raw arm's equivalent comes from Stage 3's raw phase.
   - **Allowed differences, enumerated:** seeds, block tags, paths, `--timeout 8031`, `--arm raw` for raw, and `TEACHER_TUPLE_JSON` / `TEACHER_SNAP_DIR` on the teacher arm only.
   - Remove the inert `TCG_POLICY_SEARCH*` lines.
2. **Real-contract fixtures**, which would have caught all seven:
   - **(a) Server env:** parse every `os.environ.get("…")` name from the **pinned** server file, and assert each spawn sets `SEARCH_MODEL`, `TCG_POLICY_SOCK`, `TCG_LEARNER_SEAT` and `TCG_OPP_MIX`. Seat 1's and seat 2's sockets must differ, and `TCG_LEARNER_SEAT` must equal the block's seat.
   - **(b) Socket wiring:** each driver's `--sock` equals the `TCG_POLICY_SOCK` of its seat's server.
   - **(c) Readiness:** the readiness grep string occurs literally in the pinned server's source.
   - **(d) Driver argv:** each driver invocation, extracted verbatim, parses under **the real driver's argparse** (load its parser and call `parse_args` on the extracted argv, with no game started). A negative case with `--max-turns` must fail.
   - **(e) Parity:** the fleet's blocks against the pilot's, differing only in the enumerated set above.
3. **A runtime smoke before the fleet.** This runner has never played a game.
   - Register a fresh 1-seed smoke block (proven fresh), and play it at both seats in both arms (4 games) through the **same runner blocks**, behind a `SMOKE=1` switch that changes only the seed list and output directory.
   - **Assert:** servers loaded on the right model and seat; every driver row is valid with `seat` and `arm` as specified; the teacher rows' tuple stamp is H8k-180+H; raw rows have no teacher stat rows.
   - The smoke games merge to the registry under their own tag and are **never analyzed**.
   - **The fleet starts only if the smoke passes.** Cost: about 1 h.

## 3. Then

- **The rebuild comes back for review** with §2's fixtures and smoke, and a doc section recording the seven defects.
- **The single-shot guards are untouched and no games ran,** so the relaunch starts clean. The deletions so far were Joe's approved scratch trees.
- **Joe's go is needed again** after that review.
- **A standing rule from this:** every runner block that spawns a server or calls a driver is a fork of a block that has already run, with an argparse/env-contract fixture against the pinned real files.

**Scope:** this reviews the §18 repair at 5ea3a723 and does not confirm it. The fleet stays unlaunched until the rebuilt games runner is reviewed.
