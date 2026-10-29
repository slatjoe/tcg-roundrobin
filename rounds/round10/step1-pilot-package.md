# Round 10, Step 1 — the threshold teacher, pilot first

Status: STAGED for code review. Nothing in this package
has run on the box. Parent: 1aa4efb1 (the builder
response to the probe ruling). Terms:
claude-reply-243b9d8.md sec.3, which approves Step 1 in
direction, pilot-first, on the probe's sec.3
interpretation. Joe's "let's do it" (2026-10-29) adopted
the pilot-first drafting. This package implements the
sec.3 terms exactly; the pilot launches only on Joe's
go after code review.

## 1. What Step 1 is

One change on the sec.14-fixed engine: the uncontested
threshold is lifted, so every teacher decision with
>= 2 candidates is searched. The probe's final read
(cap-aligned, registered): the threshold lever is
BUILDABLE (per-game gain +0.4734 on the probe's
off-trajectory estimand, LOGO weakest-exclusion lower
bound +0.1753; the sec.3 interpretation rides with it:
the signal is real, the size is not 0.47). The margin
lever is CLOSED at this registration (+0.0076, lower
bound -0.0067). The pilot measures the lever's size on
the teacher's OWN trajectory — the estimand Step 2's
gate will measure again.

Unchanged from Stage 3's teacher: margin 1.5, k 25,
rollout bounds 8000 hooks / 180 s, horizon trigger
turn 62 at value -1 (sec.14 per-step check +
horizon-forces-draw), the candidate rule (top-3 +
prior >= 0.10, cap 4), the tuple name H8k-180+H. The
sec.14 horizon fix also differs from Stage 3's LIVE
teacher (whose engine overshot); per-class reporting
keeps the comparison honest: the contested class is
the continuity class with Stage 3's +0.0649 per-game
gain; the newly-contested class is the lever.

## 2. The build

code/step1/search_s3_thr.php (sha256 4a1936fe...) is
the sec.14-fixed search_s3.php (87779e8e...) with
EXACTLY ONE token changed, line 1017:

    --- search_s3.php
    +++ search_s3_thr.php
    @@
    -  if ($ncand <= 1 || $bp >= 0.97) {
    +  if ($ncand <= 1 || $bp >= 1.01) {

(the full 11-line unified diff is staged at
fixtures/search_s3_thr_diff.txt.)

Mechanism: the codebase expresses the threshold as
the literal in this branch condition — there is no
named constant. $bp is the top candidate's prior
probability; priors are probabilities, top prior
<= 1.0 (1.0000 recorded at max). A threshold of 1.01
is therefore UNREACHABLE for any multi-candidate
decision, so the uncontested early return never
triggers when $ncand >= 2 — which is the faithful
expression of "lifted": the branch, the stat-row
shape for genuinely single-candidate decisions
($ncand <= 1, untouched), and every other line stay
byte-identical. The alternative (deleting the branch
or restructuring the condition) would change more
than the threshold and buy nothing.

The capture hook is intact and byte-identical. Its
own gate still names 0.97 because it serves the
probe's capture arms; the pilot never sets
TEACHER_CAPTURE (sec.3), so the hook is inert in the
pilot. Overturn capture in the pilot runs through the
overturn snapshot path (TEACHER_SNAP_DIR), which the
games runner sets per block.

fixtures/gen_search_s3_thr.py regenerates the build
from the staged sec.14 file and asserts byte-identity
plus the one-line diff (PASS).

## 3. The pilot design

A live teacher run, not a fleet (sec.3.2):

- 100 teacher games vs the heuristic, Gravy mirror,
  instrument 87/62, run_pilot.sh, output root
  r10pilot_out/.
- Seed block: game seeds 25001-25050, each played at
  BOTH seats (blocks s1a 25001-25025 seat 1, s1b
  25026-25050 seat 1, s2a 25001-25025 seat 2, s2b
  25026-25050 seat 2) = 100 games. (The terms text
  said "25001-25100"; the four-block form plays the
  same 100 games as 50 seeds x 2 seats, the project's
  standard paired layout — flagged for the review.)
- The teacher arm plays search_s3_thr.php under the
  H8k-180+H tuple pin, stamped on every stat row
  (setting.pinned). Every overturn is snapshotted.
- Registry merge (tag r10_step1_pilot) runs BEFORE
  analysis, as in the probe runner.
- Timeout: GAME_TIMEOUT = 7845 s, PROVISIONAL, with
  derivation: Stage 2's maximum game wall from the
  published round-9 rows — 2143.2 s (game 888015991,
  rounds/round9/data/stage2/games_s2b.jsonl, field
  secs; the same file's mean is 503.118 s over 200
  rows) x 3.66 (the probe's measured threshold-cost
  factor) = 7844.112, ceiling 7845. (The terms'
  illustrative figure was ~7,850 s from the same
  derivation.) The pilot's own wall tail (p95/max in
  the read) sets Step 2's timeout.
- Single-shot refusal: the runner aborts if the
  games manifest, the read, or the pilot manifest
  already exists. FREE-SPACE pre-flight (8 tree
  copies) and the G8 + (C) containment pair run in
  the house style.

## 4. Labels and the seed families

L3 labeling at the REGISTERED label configuration —
LABEL_W = 50, CRN pairs, tuple L3-W50+H (hooks 8000,
deadline 180, horizon 62, value -1, k 50), production
eval server — on ALL captured overturns, both classes
(nothing is sampled in the pilot, so no sampling
weights anywhere). s2_label_main.php is byte-identical
to the round-10 file; s1_eval_main.php ships in the
package with the loud loader (sec.6).

Label seed family: MEAS_SEED = 700055001 +
shard x 10^8, 4 shards, ENFORCED cap 512 jobs/shard
(the jobs builder aborts over cap). At cap a shard's
span is 52,637,046 < 10^8, so the four shard ranges
(700M-752M, 800M-852M, 900M-952M, 1000M-1052M) are
mutually disjoint. Clearance against every prior
family is by ENUMERATION (fx_pilot_seeds.py), ranges
and seed VALUES both:

prior families checked: round-8 distill (555001,
777001), round-9 Stage 0 labels (855001), Stage 1
eval (885001), Stage 2 labels (955001), Stage 3
labels (50055001), round-10 probe eval (30055001,
3300/shard), probe labels (70055001, 256/shard),
supplementary A (970055001, 10 jobs), supplementary
B (470055001, 256/shard). The pilot family at its
512 cap is range- and value-disjoint from all of
them. NOTE on the base: the drafting brief suggested
570055001; enumeration showed that base sits INSIDE
the probe eval family's registered span (its shard 3
reaches 660,716,986 at 3300 jobs), so the family was
moved to 700055001, whose spans clear probe-eval's
top and supplementary A's range on both sides.
Capture seeds 25001-25050 and pre-gate seeds
8601-8610 are likewise enumerated disjoint from every
used block (1001-1200, 2001-2200, 8001-8200,
9001-9200 reserved, 10001-10400, 21001-21100,
22001-22100, 23001-23200, 24001-24090).

Class assignment: a job's class comes from its LIVE
stat row's top prior (< 0.97 contested, >= 0.97
newly_contested), joined from the driver's index rows
to the overturn stat rows by the ORDER-AWARE key
(game, branch, player, turn, prior_pick, teacher_pick)
— the join the probe validated 975/975 against the
snap join. The stat row carries priors, not a class
field, so the class is materialized onto the job row
at build time (with top_prior, mean_diff, se_diff, z
in sentinel form, and the tuple setting stamp).

Expected volume, flagged honestly: at the probe's
implied ~8.1 fires/game the pilot yields ~810 jobs
(~203/shard). The 512 cap is ~2.5x that; a cap trip
aborts the run by registration rather than truncating
silently.

## 5. The read (all formulas registered here, pre-run)

pilot_read.py, on jobs x labels x ALL 100 game rows:

- World score (cap-aligned, registered round 9 +
  sec.14): a world scores 1.0 iff outcome > 0 AND
  the world ended by turn 61 (turns <= 61); every
  other finished world scores 0 (a horizon draw
  prices -1 in the search statistic and 0 here, the
  draw=0 read).
- Job diff: the mean over CRN-paired shared worlds
  of (teacher world score - prior world score), the
  probe's job_diffs construction verbatim at
  cap_aligned. Jobs with no shared finished world
  pair are counted (jobs_no_shared_worlds), not
  dropped silently.
- Per-game totals: for each of the 100 games (from
  the driver rows; timeouts included), the SUM of
  its jobs' diffs, per class and total; games with
  no jobs contribute 0. NO sampling weights.
- Gain: mean of the per-game totals; CI by the
  game-cluster bootstrap (analyze_l3
  .cluster_bootstrap, B = 10000, seed 20261020) —
  the gain's one-sided 95% UPPER bound is the CI's
  upper end, its LOWER bound the CI's lower end.
  The analytic clustered SE = sd(per-game totals,
  ddof=1) / sqrt(100) is reported alongside and is
  the SE the sizing rule scales.
- Fires/game by class = class job count / 100, and
  per completed game in the games report.
- Edge by class = class gain (same construction on
  class-restricted totals); edge by z-band over the
  probe report's bands [1.5, 2.0], (2.0, 2.5],
  (2.5, 3.5], > 3.5 (the z = 999.0 sentinel bands
  > 3.5, as registered).
- Wall per game: mean / p95 (nearest-rank) / max of
  driver secs over completed games; timeouts counted
  separately (a timed-out game carries no secs).
- Influence: LOGO (leave-one-game-out gain range)
  and the largest single-game share of the positive
  gain mass, per class and total.
- STOP evaluation, registered verbatim: STOP with
  no Step 2 iff the total gain's one-sided 95%
  UPPER bound < 0.0649 + 0.020 = 0.0849.
- Step 2 sizing, registered verbatim: two-sample
  bar vs Stage 3 (gain 0.0649, SE 0.0090);
  Delta_plan = pilot gain's one-sided 95% LOWER
  bound - 0.0649 (never the point estimate);
  SE_new(n) = SE_pilot x sqrt(100 / n); n is the
  smallest count with Delta_plan / sqrt(SE_new(n)^2
  + 0.0090^2) >= 1.645 + 0.8416 = 2.4866 (80%
  power); closed form n = ceil(100 x SE_pilot^2 /
  ((Delta_plan / 2.4866)^2 - 0.0090^2)); if
  Delta_plan <= 0 or the denominator <= 0 there is
  no finite n and the read says so. If n > 400 the
  read prints the flag: Step 2 exceeds the
  registered 400-game size and becomes Joe's cost
  decision. The pilot's games are never pooled into
  Step 2.

By-hand fixture (fx_pilot_python.py): planted jobs
with diffs +0.5 (contested, g1), +0.5 (newly, g2),
0.0 (contested, g2, teacher win at turn 70 scoring 0
cap-aligned) over 4 games give per-game totals
0.5 / 0.5 / 0 / 0, total gain 0.25, class gains
0.125 / 0.125, LOGO range [1/6, 1/3], largest share
0.5; sizing at LB 0.1649, SE 0.02 gives Delta 0.1000
and n = 27 by hand; Delta <= 0 gives no finite n.

## 6. Standing requirements (sec.3.5), each to its fixture

- sec.14 engine only: search_s3.php / search_s2.php
  in code/step1/ are byte-identical reuse copies
  (87779e8e... / 1c964160...); the build diff is the
  one token (gen_search_s3_thr.py).
- STRICT JSON job files + LOUD loaders in every PHP
  job reader shipped: s2_label_main.php is
  byte-identical to the round-10 loud form;
  s1_eval_main.php carries the same loud loader
  (counts lines, aborts exit 2 NAMING the failing
  line, count assertion) patched into the step1
  copy with a dated header note — it is the package's
  eval main (stat-row writer for any Step 1 eval
  work), included because the ruling names it. Every
  Python writer in the package dumps with
  allow_nan=False. Fixture: fx_pilot_loader.py
  (verbatim block under php8.3: strict file loads
  whole; a bare-Infinity line 2 aborts naming
  line 2).
- Composed-environment fixture: fx_pilot_env.py
  extracts BLOCK:PILOT-GAMES verbatim from
  run_pilot.sh and executes it in a stub harness;
  per block it asserts TEACHER_TUPLE_JSON composed
  from settings, TEACHER_SNAP_DIR == the block's
  logdir/snaps, GATE_GAME_IDS_FILE, TCG_CLEAN_
  CHILDREN=1, --arm teacher, --timeout 7845, the
  settings seed blocks, and TEACHER_CAPTURE ABSENT;
  negative case: without the runner's export the
  tuple check detects the gap. Env audit of the
  shipped PHP (every getenv consumer traced):
  search files — TEACHER_TUPLE_JSON (runner export,
  from settings), TEACHER_SNAP_DIR (runner, per
  block), TCG_LEARNER_SEAT / TCG_SEARCH_LOG /
  TEACHER_MODE / TEACHER_GHOST (paired driver, per
  arm; ghost only in the pre-gate), TEACHER_CAPTURE*
  (probe arms only; correctly UNSET in the pilot),
  SIM_ARS_DESC / LEAF_HARVEST_DIR / HARVEST_DIR /
  TEACHER_SHADOW / LABEL_DEBUG / ISMCTS_D /
  ISMCTS_S (unset = stock behavior); mains
  (s2_label_main.php, s1_eval_main.php) — MEAS_JOBS
  / MEAS_OUT / MEAS_SEED / EVAL_STATS /
  EVAL_SETTING_NAME / EVAL_HORIZON_VALUE /
  LABEL_HORIZON and the EVAL_* tuple family (all set
  by run_pilot.sh's label block from the L3-W50+H
  literals), LABEL_DRIVER (self-set via putenv),
  TCG_POLICY_SOCK (label block, production server).
- Writer->reader round trips on real output shapes:
  fx_pilot_python.py (jobs builder -> strict file ->
  pilot_read's job set, incl. the order-aware
  pairing on repeated keys and the z sentinel;
  games report on real driver-row shapes; the read
  end-to-end through main()).
- Invocation-parity fixture: fx_pilot_parity.py —
  the TUPLE-BUILD blocks of both runners are
  verbatim-identical; the pregate manifest's written
  keys cover every key run_pilot.sh's PREGATE-GATE
  reads (verdict, search_s3_thr_sha256,
  teacher_tuple_json); the ghost and games driver
  flag sets differ by exactly {--timeout}.
- expect_hash on EVERY deployed file, deploy-list
  guard enumerating the pilot's deploy list:
  fx_pilot_pins.py parses each runner's own
  deployed_code_hashes list; every non-.sh file on
  it must carry an expect_hash site whose literal is
  64-hex and equals the staged sha256 (runner scripts
  are recorded-only, the round-9 form); settings
  cross-checks pin GAME_TIMEOUT, LABEL_BASE, the
  label EVAL_* literals and block spec strings to
  settings_pilot.json; negative case: a pin-stripped
  runner copy fails coverage.
- Fixtures read only PUBLISHED data: the timeout
  derivation reads rounds/round9/data/stage2 rows;
  no fixture reads unpublished outputs.
- Status-only interim notices; publication with a
  MANIFEST: run_pilot.sh writes pilot_manifest.json
  (launched vs approved sha fields, deployed hashes,
  pins, counts, the read's STOP/sizing prints) — the
  publication step itself runs with the pilot, after
  the go.

## 7. Pre-gate (plan + checker, no games run here)

run_pilot_pregate.sh + pregate_check_pilot.py,
round-9 form (seeds 8601-8610 x both seats, five
trees, single-shot, G8 + (C) containment,
registry tag r10_step1_pilot_pregate). The checker's
exact form:

1. Raw determinism + R16 seat control (driver rows,
   played position).
2. Played-action identity, ghost-sec.14 vs ghost-thr,
   per seed/seat on (winner, draw, capped, turns,
   gamelog_sha): the builds may differ ONLY in
   decisions the sec.14 build skipped.
3. Contested-class identity over order-aware paired
   stat rows: for every pair where the sec.14 arm
   searched (contested == 1), the priors arrays are
   EXACTLY equal and the selected sets equal (the
   lifted threshold cannot change a contested
   search; rollout OUTCOMES are not compared —
   Decide's seed base is drawn per call and is
   irreproducible across processes, the round-9
   lesson).
4. The newly-contested class is the ONLY expected
   divergence: pairs where the sec.14 arm returned
   uncontested and the thr arm searched with top
   prior >= 0.97 are counted, not failed; both-
   uncontested pairs (ncand <= 1) hold identity by
   shape. Any other divergence shape fails.
5. K6 canary per ghost arm (refusals as coverage;
   > 2% of contested decisions, or any branch > 5%,
   not identical).
6. Manifest checks, minus the K6-read one (the
   round-9 form).

Verdict IDENTICAL / exit 0 iff all hold.
fx_pilot_pregate.py exercises the checker on
synthetic records: identity + one newly-contested
divergence -> IDENTICAL with the divergence counted;
a contested priors mismatch -> NOT IDENTICAL; a
sec.14 skip below the boundary (thr top prior 0.50)
-> NOT IDENTICAL. run_pilot.sh's PREGATE-GATE
refuses to run games unless the pregate manifest
says IDENTICAL with the thr build's hash and the
same tuple JSON.

## 8. Files staged (all new; nothing at 1aa4efb1 modified)

code/step1/: search_s3_thr.php (the build),
search_s3.php + search_s2.php (sec.14 reuse, pinned),
s2_label_main.php (reuse), s1_eval_main.php (loud
loader), paired_driver_gravy.py, merge_registry.py,
shm_sweep.py, g8_sweep2.sh, stage0_report.py,
analyze_l3.py (reuse copies), settings_pilot.json
(a5895a84...), build_pilot_jobs.py,
pilot_games_report.py, pilot_read.py,
pregate_check_pilot.py, run_pilot.sh,
run_pilot_pregate.sh.
fixtures/: fx_pilot_pins.py, fx_pilot_seeds.py,
fx_pilot_python.py, fx_pilot_pregate.py,
fx_pilot_loader.py, fx_pilot_env.py,
fx_pilot_parity.py, gen_search_s3_thr.py,
search_s3_thr_diff.txt, run_fx_pilot.sh,
fx_pilot_outputs.txt.
This doc.

Fixture totals: pilot suite 131 PASS / 0 FAIL
(fixtures/fx_pilot_outputs.txt); the full round-10
suite re-run 197 PASS / 0 FAIL, its transcript
byte-identical to the committed one
(fixtures/fx_r10_outputs.txt unchanged). Byte-
identity audit vs 1aa4efb1: 129 remote blobs vs the
staging tree — the only differences are the new
files above; no committed file differs.

## 9. Flags for the review

- Seed block form (sec.3): 50 seeds x 2 seats, not
  100 distinct seeds (sec.3 above).
- Label seed base moved 570055001 -> 700055001 on
  the enumeration evidence (sec.4).
- The 512 jobs/shard cap and what a trip does
  (abort, by registration) against the ~203/shard
  expectation (sec.4).
- s1_eval_main.php ships for completeness as the
  package's eval main with the loud loader; the
  pilot pipeline itself labels through
  s2_label_main.php only.
- The pilot's timeout is provisional by the terms;
  its own wall tail sets Step 2's.

## 10. Fix pass 1 (2026-10-29) — claude-reply-acc55a1 §2

Three required items; nothing ran.

**§2.1 — the seed-block list is completed and the
pre-gate block moves.** `fx_pilot_seeds.py`'s
USED_GAME_BLOCKS now carries the full record, with
sources cited in its docstring: round 9's D2 list
(rounds/round9/gravy-calibrated-search-design.md
§9 D2) — fleets 1001–1200 / 2001–2200 / 8001–8200,
the 3000-series probes (entered as 3001–3022:
3001/3002 concurrency probe, round-3 reply
6a0d7d4; 3003–3006 fleet probe, round-7
fleet-alignment; 3007–3010 extended-probe wave 1
with waves to 3022 registered, round-7
extended-probe; 3011–3014 also played by the
round-3 gate-fix test copy, reply 8d13b0f),
controls 4001–4014, smokes 5001–5010 / 7001–7002,
census 6001–6040, round-8 corpus 10001–10400,
pre-gate control 11001–11010, pilot equivalence
12001–12010, Gravy pre-gate 8501–8510, contention
probe 8601–8604, Gravy census 8801–8820, and the
reserved gate block 9001–9200 — plus every block
used since D2: 21001–21040 (Stage 0/1 capture),
22001–22100 (Stage 2), 23001–23200 (Stage 3
fleet), 24001–24090 (round-10 probe capture), and
this pilot's own capture block 25001–25050.
The first list omitted eleven of these, including
8601–8604, which the pre-gate's block overlapped.
**The pre-gate block moves to 13001–13010**
(run_pilot_pregate.sh, settings_pilot.json, and
every fixture reference; the runners' settings
pins machine-updated). The completed list proves
it fresh: its neighbors in the list are
12001–12010 and 21001–21040, and the fixture's
check runs against the whole completed list.
**The capture block 25001–25050 was re-verified
against the completed list and does NOT collide**
(nearest entries 24001–24090 below and nothing
above until the label families, which are a
different lattice) — it stays as registered.
The §3/§7 mentions of 8601–8610 above stand as
the as-built record; this note supersedes them.

**§2.2 — one-sided bounds for STOP and Δ_plan.**
As built, pilot_read.py took lb/ub from
analyze_l3.cluster_bootstrap's two-sided 95%
interval (2.5th/97.5th percentiles): conservative
for Δ_plan, permissive for STOP. The read now
draws ONE set of bootstrap replicates (B=10000,
seed 20261020 — bootstrap_means() replicates
cluster_bootstrap's algorithm on the per-game
totals and asserts its 2.5th/97.5th percentiles
equal cluster_bootstrap's on the same data) and
reports: the two-sided 95% CI (labeled, beside
them), **lb = the 5th percentile (one-sided 95%
lower bound), feeding Δ_plan**, and **ub = the
95th percentile (one-sided 95% upper bound),
feeding STOP**. The STOP line and JSON name the
basis. Fixture (fx_pilot_python.py, plant T): a
100-game population with four games at per-game
total 1.12 and 96 at 0 gives, under the
registered bootstrap, **95th percentile 0.0784
(< 0.0849) and 97.5th percentile 0.0896
(≥ 0.0849)** — the two-sided ub would not have
stopped; the read prints STOP, and the fixture
asserts both percentile values exactly.

**§2.3 — portability and determinism.**
fx_pilot_loader.py resolves php the way the
round-10 suite does (fx_label_loader.py's
find_php: $PHP, else the local php8.3 tool path,
else php/php8.3 on PATH) and, when none exists,
prints a one-line FAIL ("no php interpreter
found…") and exits 1 — no traceback. Set prints
in PASS lines are sorted: the gate-field set
(fx_pilot_parity.py) and the seed-block set
(fx_pilot_env.py). One further determinism defect
found and fixed in this pass, in fx_pilot_env.py:
its stub appended multi-line records to a shared
file from the block's four parallel invocations,
which interleaved records (corrupting parses,
intermittently) and ordered PASS lines by
completion; each invocation now writes its own
file and renames it into place atomically, and
the fixture sorts the parsed records by ARGV
(8/8 clean runs, byte-identical transcripts).
The loader fixture's abort PASS line also strips
its tempdir path from the printed excerpt, the
last run-specific string in the pilot transcript:
two consecutive full pilot-suite runs now produce
byte-identical transcripts.
The §6 table's loader row and §4's lb/ub wording
stand as the as-built record; this note
supersedes them where they differ.

Suites after the pass: pilot 134 PASS / 0 FAIL
(131 + plant T's 3); round-10 197 PASS / 0 FAIL
with its transcript reproduced byte-identical.

## 11. Fix pass 2 (2026-10-29) — the pre-gate repair

Attempt 1 ran (launch record: step1-pilot-launch.md)
and the pre-gate read NOT IDENTICAL. The diagnosis
found three independent layers, all instrument-side;
the build is not touched by this pass. §7 items 2–4
stand as the as-built record; this note supersedes
them where it says so.

**Layer A — timeouts misread as identity failures.**
Attempt 1's played-action failures were exactly the
seeds whose thr-arm driver row is a timeout: the
paired driver's 1,200 s default was sized for the
sec.14 arm. Every completed thr game is
byte-identical to its sec.14 counterpart. The thr
arm's max COMPLETED wall in attempt 1 was 1,153.3 s
(seat 2; seat 1: 980.4 s) — the default was below
even a completed game. **Repair:** the played-action
leg judges identity on the seeds both arms
completed and reports a timeout row as a timeout,
by seed and arm, never as an identity failure; the
verdict line names any timeout seeds. **Sizing:**
both ghost arms now run at **--timeout 7845**, the
pilot's registered GAME_TIMEOUT (Stage 2 max wall
2,143.2 s x 3.66), which is 6.8x the thr arm's max
completed attempt-1 wall and keeps one timeout
story across pre-gate and pilot; the sec.14 arm
takes the same value (its games finish far below
either bound; the bound only bites on a hang). The
parity fixture's registered relationship changes
with it: the two driver invocations' flag sets are
now EQUAL, and the fixture asserts the pregate
--timeout literal equals the pilot's GAME_TIMEOUT.

**Layer B — the checker paired zero decisions.**
The v1 pairing key led with the arm-local Talishar
game-instance id; the two arms create separate
instances, so the key sets were disjoint and every
row fell into the count-mismatch branch (1,697 +
1,638 "other" divergences, reproduced exactly from
the fetched stats). "0 contested pairs" meant no
decision was ever paired. **Repair — pairing by
seed and sequence order:** the driver rows give
each arm's seed -> gamename mapping for completed
games; each arm's decision rows for that seed's
game (under its own instance id) are taken in file
order and paired index by index. Classification
per pair: both-uncontested -> skipped (ncand <= 1);
sec.14-uncontested x thr-searched with thr top
prior >= 0.97 -> newly-contested (counted, the
expected shape); both-searched with sec.14 top
prior < 0.97 -> a contested pair. Any other
combination is counted BY NAME as its own
divergence class and fails (sec14-searched x
thr-uncontested; both-searched at >= 0.97;
sec14-uncontested x thr-searched below 0.97).
If a seed's two games' decision counts differ, the
common prefix is paired and the tail is counted by
arm as a named divergence, with the reason printed
(trajectory already diverged, or game-length
difference in an otherwise identical game — the
played rows decide). Decision pairing covers only
seeds both arms completed; a timed-out seed's
partial stats are never paired.

**Layer C — exact-equality priors exceeded the
instrument's reproducibility.** Order-aligned, the
contested pairs' `selected` agreed everywhere, but
priors were exactly equal in only a minority: the
rest differ at GPU-served float noise. **Repair:**
contested pairs compare `selected` EXACTLY and
priors at a registered max-abs-difference tolerance
of **1e-6** (PRIORS_TOL). The check prints the
observed maximum abs diff per seat, so the
tolerance's adequacy is itself in the record. On
the fetched attempt-1 data (below) the observed
maxima are 5.364e-07 (seat 1) and 7.153e-07
(seat 2) over 219 contested pairs: most pairs sit
at ~1e-7, but the worst pair is within a factor of
~1.4 of the tolerance — the printed-evidence rule
is what keeps that visible at every future run.

**The repaired checker on attempt 1's fetched
data** (read-only, data/step1_pregate/): **PREGATE:
IDENTICAL**, with the timeouts named — seat 1: 5/5
completed seeds identical, timeouts at 13001,
13002, 13003, 13005, 13010 (all thr); 97 contested
pairs, 0 bad, 309 newly-contested, 0 named
divergences, 0 tail rows. Seat 2: 7/7 completed
identical, timeouts at 13001, 13002, 13005 (thr);
122 contested pairs, 0 bad, 456 newly-contested.
The pairing accounts for every decision row of the
completed games (seat 1: 309 + 97 = 406 = the five
games' stat-row counts; seat 2: 456 + 122 = 578).
The launch diagnosis's hand alignment counted 85
contested pairs on seat 1 where the checker counts
97; the difference is the alignment's row filter,
not a pairing disagreement — all 97 pass
selected-exact and the tolerance. Attempt 1's
recorded verdict stands (it was produced by the
v1 checker under the 1,200 s sizing); this run is
analysis of the published outputs, not a re-run.

**Fixtures (fx_pilot_pregate.py, rewritten)** plant
the real shapes: DISJOINT game-id sets per arm with
the seed -> gamename mapping on the driver rows; a
newly-contested pair at decision index 0; a
contested pair at ~1e-7 priors noise (passes); a
pair at 1e-4 (contested_bad); an off-shape pair
(counted by name); a below-boundary skip (counted
by name); a timeout driver row (reported as a
timeout, verdict IDENTICAL on the completed
games). The same base population run against the
v1 checker (fixtures/pregate_check_pilot_v1.py,
the pre-fix bytes, 671f2c20...) FAILS with "0
contested pairs" and count-mismatch divergences —
the Layer B failure, reproduced in the suite.

**Re-run mechanics.** Attempt 1's outputs stay in
the flat layout under $PILOT_OUT/pregate/, untouched
as the record. The repaired pregate runner resolves
its attempt at launch: PREGATE_ATTEMPT if set, else
one more than the highest attempt present (the flat
attempt-1 layout counts as attempt 1), and runs in
pregate/attempt<N>/ with the per-attempt single-shot
guard unchanged; the manifest records the attempt
number. run_pilot.sh's PREGATE-GATE reads the
LATEST attempt's manifest (attempt<N> dirs in
version order; the flat path is the fallback).

## 12. Fix pass 3 (2026-10-29) — claude-reply-3955e55 §2

Claude reproduced the §11 diagnosis independently
(his own seed pairing and sequence-order alignment
of the published rows: 97 / 122 contested pairs, 0
selected diffs, maxima 5.364e-07 / 7.153e-07, 309 /
456 newly-contested, every completed thr game
byte-identical by gamelog to its sec.14 counterpart
and to the raw game) and accepted the repair's
shape. Two items were required, one cost note was
given, and one process ruling was recorded. §11
stands as the pass-2 record; this note supersedes
it where it says so.

**The process ruling (in substance).** The pass-2
checker's read-only IDENTICAL on attempt 1's
fetched data is a DIAGNOSTIC, not a gate result: a
checker revised after seeing a failure does not get
to re-read that same data as the verdict. **The
gate is attempt 2**, run fresh under the checker as
approved. Attempt 1's NOT IDENTICAL stands as
recorded. (Under the pass-3 semantics below, the
attempt-1 data reads INCONCLUSIVE -- the timeouts
gate -- which likewise changes nothing about
attempt 1's recorded verdict; it is the same data
under a third, stricter reading, quoted below as a
diagnostic.)

**§2.1 -- timeouts gate.** The pass-2 semantics let
the played-action leg judge identity over the seeds
both arms completed, so an attempt in which most
games timed out would have read IDENTICAL on the
few that finished -- a fair way to diagnose attempt
1, not a gate. Now: **IDENTICAL requires all 10
seeds at both seats to complete in EVERY arm the
checker loads** -- exactly these row files, as the
runner invokes it: `raw_s1`, `raw2_s1`, `raw_s2`
(the determinism / seat-control arms) and
`ghost14_s1`, `ghost14_s2`, `ghostthr_s1`,
`ghostthr_s2`. Any driver row with `invalid ==
"timeout"` in any of them makes the verdict line
print exactly `PREGATE: INCONCLUSIVE (timeout:
<arm> seeds <list>; ...)`, naming every timed-out
arm and its seeds, with exit 2 (non-zero). The
per-leg lines still print, as diagnostics over the
completed population; only the verdict changes.
Mechanically: the pregate runner aborts on the
non-zero exit before the registry merge and the
manifest write, so an INCONCLUSIVE attempt leaves
no manifest, and run_pilot.sh's PREGATE-GATE --
which requires the latest attempt's manifest to
read IDENTICAL -- refuses; the case returns to
review. Attempt-1 behavior of the non-ghost arms,
verified from the fetched rows: the raw arms
completed 30/30 rows (walls 1.3-4.5 s, no
timeouts) and ghost14 completed 20/20; the only
timeouts in the population were ghostthr's eight.
The updated checker, run read-only on
data/step1_pregate/, prints every identity line
PASS (97 / 122 contested pairs, 0 bad; newly 309 /
456) and then the verdict:

    PREGATE: INCONCLUSIVE (timeout: ghostthr_s1 seeds 13001, 13002, 13003, 13005, 13010; ghostthr_s2 seeds 13001, 13002, 13005)

**§2.2 -- the tolerance is 1e-5, on a stated basis,
with prior_pick exact.** PRIORS_TOL is now 1e-5,
justified on the server's arithmetic, NOT on
attempt 1's maxima: the policy server computes in
float32, about 1.2e-7 relative per ULP at 1.0, and
observed cross-process differences run a few ULPs;
1e-5 absolute is about 80 ULPs at 1.0 -- far above
serving noise, far below any difference that could
move a candidate in or out of the selection. (The
pass-2 1e-6, set with an eye on the data, sat only
~1.4-1.9x above the worst observed pair, 5.4e-07 /
7.2e-07, and could have failed a fresh attempt on
float noise alone.) Contested pairs additionally
require `prior_pick` EXACT, beside `selected`
exact; a prior_pick mismatch counts contested_bad,
with the pair identified in the first-bad-example
INFO line. The observed maximum |dprior| per seat
still prints (the attempt-1 diagnostic reads
5.364e-07 / 7.153e-07, now ~19x / ~14x inside the
bound; and prior_pick was exact on all 219 of
attempt 1's contested pairs). Fixtures
(fx_pilot_pregate.py, 9 -> 13 checks): a pair at
5e-6 PASSES; a pair at 2e-5 is counted bad; a pair
with equal priors and equal selected but a
different prior_pick is counted bad; the timeout
case now expects INCONCLUSIVE naming
ghostthr_s1/ghostthr_s2 seed 13002 with exit
non-zero, plus a companion check that the completed
population's identity lines still print.

**Cost re-price (Claude's cost note; computed from
the fetched attempt-1 driver rows, `secs` field).**
Completed-game walls: the thr ghost arm (12 games)
-- pooled mean **855.2 s**, nearest-rank p95
1,153.3 s, max 1,153.3 s (seat 1, 5 games: mean
771.2, max 980.4; seat 2, 7 games: mean 915.2, max
1,153.3). The sec.14 ghost arm (20 games) -- pooled
mean 319.1 s, p95 494.2 s, max 570.2 s (per-seat
means 367.6 / 270.7).

(a) *Pre-gate attempt 2.* The runner runs the three
raw invocations sequentially in the foreground
(attempt-1 raw total: 78.1 s -- negligible) and the
four ghost invocations CONCURRENTLY, 10 seeds
sequential inside each, so the ghost phase is the
longest single arm total. The sec.14 arm totals are
observed sums (all 10 games completed): 3,676.0 s
(seat 1), 2,707.0 s (seat 2). The thr arms at 10 x
their completed per-seat means: 7,712 s (seat 1),
9,152 s (seat 2) -- ghost phase ~9,152 s, **~2.5
h**. That mean is survivor-biased: the eight killed
games have no completed wall (each was still
running at 1,200 s when killed). Pricing only those
eight at their 1,200 s floor: thr arm totals 9,856
s (3,856.2 observed + 5 x 1,200) and 10,006 s
(6,406.3 + 3 x 1,200) -- ghost phase ~10,006 s,
**~2.8 h**. Planning figure for attempt 2: **~2.5-
2.8 h** plus the raw phase and the checker/merge
minutes. (Attempt 1's actual wall was 2 h 48 min,
consistent: its long pole was the same thr arms.)

(b) *The pilot's teacher arm.* 100 live games at
the pooled thr completed mean, 855.2 s = 85,521 s,
**~23.8 box-hours**; the pilot runs four concurrent
25-game blocks, so **~5.9 h wall**. With the eight
killed games priced at their floor the pooled
per-game figure is 993.1 s: 99,312 s, **~27.6
box-hours**, **~6.9 h wall**. Basis and its limits,
stated plainly: ghost walls are the full search
cost on RAW-policy trajectories (the played pick is
forced to the prior's, so the games' lengths are
the raw policy's -- attempt 1's thr games' turn
counts match the raw games'), while a live
teacher's own picks change the trajectory, so live
game lengths, and hence per-game search counts,
differ in a direction attempt-1 data cannot sign.
The 855-993 s/game band replaces the probe's
1,840 s/game figure for PLANNING (that figure
priced 19.5 s/search against the probe's search
counts; the measured pre-gate walls supersede it).
Nothing registered changes: the pilot's
GAME_TIMEOUT stays **7,845 s** -- verified against
the re-priced distribution, it is 6.8x the thr max
completed wall (1,153.3 s), and the pre-gate's
ghost arms carry the same value.

**Unchanged by this pass:** the build, the seeds,
the pilot design / read / sizing rules, the attempt
mechanics, and §11's repairs (seed pairing,
sequence order, named off-shape classes, the
7,845 s ghost timeout). Attempt 2 runs fresh under
this checker on Joe's go after the confirmation
check; the pilot stays behind an IDENTICAL verdict
-- INCONCLUSIVE returns to review, it does not
launch anything.
