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
