# Claude — code review of the round-9 Stage 3 launch package

**Reviewed commit:** c924b19a19f8ed2afd129f28ace70f03443d86bb (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the two Stage 2 report amendments at 6fb91542: they're text only and accepted. The committed `claude-reply-d593faf.md` hashes to `0bba75dc…ed13f9c`, the value I gave Joe. The package doc is `778823c0…`, and every new code file hashes to its §8 table.

**Verdict: CHANGES REQUESTED.** There's one real defect, found by running the package's own code over Stage 2's published rows: **the life-differential co-report can never fire** (§2.1). There are two smaller rule items (§2.2, §2.3) and one false clearance statement (§2.4). Everything else is accepted.

## 1. Checks

**The tuples and the pre-gate.**
- `settings_stage3.json`'s teacher and label tuples deep-equal Stage 2's.
- `json.dumps(teacher_tuple)` equals the `teacher_tuple_json` string in the **published** Stage 2 pre-gate manifest, whose verdict is IDENTICAL with `search_s2_sha256` `85490e8e…`.
- Every reused file is byte-identical to d593faf: `search_s2.php`, `s2_label_main.php`, `paired_driver_gravy.py`, the Stage 2 settings and analyzer, and `g8_sweep.sh`.

**G8 (homework a).**
- `diff g8_sweep.sh g8_sweep2.sh` is the header comment plus the one guard line, as stated.
- The class explanation is sound: `pgrep -f` matches its pattern anywhere in any process's command line. The fail-safe residual is stated honestly.
- The fixture uses the real `pgrep`. Accepted, with §2.3.

**Free space (homework b):** the block measures fresh, prints both sizes and aborts before the first copy. The 1.25 factor is justified. Accepted.

**The read.**
- The pairing statuses are as described.
- **Primary scoring:** at draw = 0 a win scores 1 and everything else 0, and a teacher timeout scores 0 at both prices.
- **The CI:** a seed-clustered bootstrap with B = 10,000, the registered rng seed and `analyze_l3` indexing.
- **The bands:** they're in order with the INCONCLUSIVE override, the impeachment checks print before the verdict, and the reconciliation names the R14 canary class.
- **Gamename uniqueness:** asserted, which discharges my earlier not-condition.

**Timeouts, raw reruns, concurrency and cost:** as registered.
- The raw arm is never concurrent with the teacher arm.
- RAW-RERUN gives one re-run, and a second hang drops the pair and is listed.
- Cost: 400 × 503 s ≈ 55.9 box-hours, about 14 h of wall time.

**Fixtures, run here** on a scratch copy: the **Stage 3 suite has 6 suites and 87 checks, ALL PASS**, with the PASS lines identical to `fx_s3_outputs.txt`. The **Stage 2 suite's 124 checks still pass.**

**Pins:** every literal in the two runners is 64 hex characters and traces to its file.

## 2. Blocking

### 2.1 The life score never credits a capped game

`life_score()` appears twice, identically, in `stage3_games_report.py` and `stage3_analyze.py`, and so does the rule in the settings comment. Both credit a capped game only if it's `capped AND NOT draw`. But **the paired driver marks every capped game `draw: true`.**

- In Stage 2's published rows, all 41 capped games are `(capped True, draw True, winner 0, cap_reason "turns")`.
- I loaded the package's own `life_score` and ran it over those rows: **0 of 41 capped games score 1.** The registered rule (ahead = 1) gives **25**.
- As built, the life-differential Δ would just be the primary under another name.
- The fixture missed it because its planted capped rows carry `draw: 0`, a shape the driver never writes. That's the same species as the Stage 2 stamp defect, one field over.

**Required:**
1. **The rule:** a win scores 1. A capped game (`capped`, winner 0) scores 1 iff the arm's own life is strictly greater than the opponent's. Everything else scores 0. The `draw` flag plays no part.
2. **One definition:** the analyzer imports the games report's function, or a fixture asserts the two are byte-identical. That keeps the two copies from drifting.
3. **Fixture on real rows:** run the life score over `data/stage2/games_*.jsonl`, the real driver output, and assert **25** capped games score 1 (13 behind and 3 tied score 0) and **112** life-wins in total. Re-plant the existing fixture rows in the driver's real capped shape (`draw: true`).
4. Correct the settings comment and the package text to match.

### 2.2 Excluded pairs need a limit

Teacher rows that are invalid for any reason other than a timeout (`no_result`, `connect_failed`, `seat_mismatch`), and raw rows invalid other than by a timeout, make a pair **excluded**. That's listed, but it has no bound. A teacher that dies mid-game without timing out leaves the read silently, in the teacher's favor.

**Required:**
- **INCONCLUSIVE also when excluded plus dropped pairs exceed 2% of the 400** (more than 8), on final counts, beside the registered teacher-timeout rule. Print the count and the rate on the line where the timeout rate prints.
- **Fixture:** 9 excluded pairs leads to INCONCLUSIVE overriding a CI that excludes 0, and 8 does not.

### 2.3 The G8 abort must name its match

The attempt-1 trip is unexplainable after the fact because the guard records nothing.

**Required:** on a trip, `g8_sweep2.sh` writes `pgrep -af` output for both patterns (pid and full command line) to the abort log and to stderr before exiting, so the next trip, including the stated residual, diagnoses itself. Extend `fx_g8_sweep2` so the planted mention's command line appears in the abort output. The diff-confinement check then covers the guard block rather than one line.

### 2.4 The label seed clearance statement is wrong

§4 and the settings say 1,055,001 sits "exactly +100,000,000 above the Stage 2 base at every shard". It sits **+100,000** above.

- **The families interleave:** with `seedBase = MEAS_SEED + job × 100,003` and worlds at `+ w × 31,337`, a shard spans about 13.4 M from its base. That puts Stage 0 (855,001), Stage 2 (955,001) and this base in the same span at every shard.
- **No seed value actually collides:** I enumerated 4 shards × 120 jobs × 50 worlds per family and found 0 shared values for any pair. The lattice keeps them apart, so nothing is invalid.
- **But the claim is false, and a seed registry has to state what it can prove.**

**Required:**
- **Move the base to 50,055,001 + shard × 10⁸.** That family sits about 36 M clear of every Stage 0 and Stage 2 span at every shard, and my enumeration shows 0 overlap.
- Restate the clearance as **range-disjoint**, with the span arithmetic shown.
- The literal changes in `run_stage3_l3.sh`, the settings and the round-trip fixture's `MEAS_SEED`.
- **For the record (my own miss in D2):** Stage 0 and Stage 2 interleave in exactly the same way (offset 100,000). They're value-disjoint by the same lattice, so nothing in Stages 0 to 2 is affected. Note it in the registry; no action.

## 3. Rulings on the flags

- **F-S3-1, the raw arm's price is an estimate: accepted.** The report replaces it with the measured figure.
- **F-S3-2, fixture Case B's values: accepted.** The arithmetic is right: a teacher-timeout pair can't diff +1.
- **F-S3-3, a Stage 3 tracker:** Joe's call. If built, "complete" keys on `stage3_read.json` and the L3 manifest.
- **F-S3-4, concurrent rerun appends: accepted.** These are whole-line appends, keyed on (seed, seat). Assert at most one rerun row per key, and abort otherwise.
- **F-S3-5, the `--expect-pairs` seam: accepted.** The production default is 400 from settings.

## 4. Non-blocking

**The attribution ratio:** `stage3_attr_analyze.py` divides by the fleet Δ whenever it's non-zero. When the Stage 3 Δ is ≤ 0, or its CI includes 0, print the ratio as `n/a (Δ ≤ 0)` or `unstable (Δ CI includes 0)`, with Δ's CI beside it. A ratio over a near-zero or negative denominator reads as a number when it isn't one.

**Scope:** the four §2 items, each with its fixture, come back in one commit for a confirmation check. Stage 3 then launches on Joe's go with launched sha == approved sha. No run is approved yet.
