# Round 10 — Step 2+3 Combined Paired Fleet: Build Package

Status: STAGED for review. Parent commit `b8939397`
(claude-reply-26cc773 committed). Nothing in this
package has been launched or run on the box. Launch
requires, per the standing rule: this package
confirmed by Claude, and Joe's explicit go in chat,
with launched sha == approved sha (or differing only
under `rounds/`).

Design source: `claude-reply-26cc773.md` §3 (the
pilot ruling's forward design), the pilot package's
registered Step 2 terms (`step1-pilot-package.md` §5
and `code/step1/settings_pilot.json` read.sizing),
and round 9's fleet conventions (`rounds/round9/`).
Joe chose Δ_plan = 0.14 (chat, 2026-10-30), the
combined single fleet over the sequential
Step 2 → Step 3 path.

## 1. What this is

One paired fleet carries both remaining reads of the
threshold question:

- **PRIMARY (the Step 3 question):** does the
  threshold teacher beat raw v10 head-to-head? Paired
  Δ per (seed, seat), draw = 0, seed-clustered CI,
  round-9 verdict bands.
- **STEP 2 CO-READ (the Step 2 question):** the L3
  per-game gain of the SAME build on the fleet's own
  teacher arm, tested against Stage 3's +0.0649 under
  the registered two-sample bar. The pilot's 100 games
  are never pooled into it — the fleet's 122 teacher
  games stand alone (≥ the registered 72 minimum).

One build, one tuple, one seed block, one launch:
the two reads share the teacher arm and cannot drift
apart in configuration.

## 2. The fleet

- **Teacher arm:** the Step 1 threshold build,
  `code/step2/search_s3_thr.php` sha256 `4a1936fe…`
  (byte-identical copy of `code/step1/`'s), tuple
  H8k-180+H from `settings_fleet.json` — byte-identical
  to the pilot's and to Stage 3's teacher tuple
  (k 25, margin 1.5, hooks 8000, deadline 180,
  horizon 62 at −1).
- **Raw arm:** RAW v10 — the Gravy anchor policy
  served raw, in the Stage 3 fleet's raw-arm
  configuration: `paired_driver_gravy.py --arm raw`
  (byte-identical copy, `3389b1b9…`) on trees whose
  `search.php` is the fleet tree's own (`8f6b35da…`,
  asserted per tree, never overwritten).
- **Matchup:** Gravy Bones mirror vs heuristic, deck
  `nats2026_eriksen_gravy_60.txt` (`b8b41390…`),
  checkpoint ckpt_v10 (`44f1e5d7…`). Instrument:
  parameter 87 / draw trigger 62.
- **Layout:** 61 seeds (26001–26061) × both seats ×
  both arms = **244 games, 122 pairs**. Blocks:
  teacher t1a (seat 1, 26001–26031), t1b (seat 1,
  26032–26061), t2a (seat 2, 26001–26031), t2b
  (seat 2, 26032–26061); raw r1a/r1b/r2a/r2b mirror
  them exactly. Pairing is by (seed, seat) — never by
  gamename, which is arm-local.
- **Phase order:** the raw phase runs AFTER the
  teacher phase completes, never concurrent (Stage 3
  form).

## 3. Seed block and freshness

Fleet block **26001–26061**. Candidates checked:
every completed block in the record tops out at the
pilot's 25001–25050 (the completed list is
`fixtures/fx_fleet_seeds.py`'s USED_GAME_BLOCKS,
copied verbatim from `fx_pilot_seeds.py`); 25051–25111
is unreserved but breaks the record's x0001 block
convention (21001, 22001, 23001, 24001, 25001, …) and
sits inside the pilot decade. 26001–26061 is the next
x0001-aligned block. `fx_fleet_seeds.py` proves
disjointness against the whole completed list by
enumeration and asserts no completed block lies above
25050.

## 4. Sizing, in full

Δ_plan derivation (the ruling's): the pilot's L3
one-sided 95% lower bound **0.195** × Stage 3's
observed Δ-to-gain ratio **0.73** (0.0475/0.0649)
= 0.14235, registered as **Δ_plan = 0.14**.

Variance per pair ≈ (1 − p₀)·q − Δ² with
p₀ = 0.01 (the pilot's zero-fire share — 791 jobs
over 99 of its 100 games, verified from the published
jobs report and pilot read) and q = 0.324 (Stage 3's
paired dispersion input, as registered in the ruling;
cited, not re-derived):

  var = 0.99 × 0.324 − 0.0196 = **0.30116**

n = var × ((z_α + z_β)/Δ)², z_β = 0.8416 (80% power):

- two-sided (z_α = 1.96): n = 0.30116 × (2.8016/0.14)²
  = **120.61 → 121 pairs**; the layout takes whole
  seeds × both seats → **61 seeds = 122 pairs
  REGISTERED**.
- one-sided (z_α = 1.645): n = 0.30116 × (2.4866/0.14)²
  = **95.0 → ~95 pairs** (96 even).

The registered 122 is the conservative (two-sided)
figure; achieved power at 122 pairs, two-sided, is
Φ(0.858) ≈ 0.805. Cross-check at Δ = 0.10: var
0.31076, n = 243.9 → 244 pairs (the ruling prints
"about 246"; the difference is z-sum rounding,
immaterial — Joe chose 0.14). All arithmetic is
re-derived in `fixtures/fx_fleet_sizing.py`.

Cost at the ruling's price: teacher arm 122 × 1,773 s
(the pilot's realized mean — "use 1,773 s for all
future pricing") = 60.1 box-hours serial ≈ 15 h wall
at 4 concurrent blocks; raw arm minutes (Stage 3 ran
400 raw games in ≈ 6.5 min); labels ≈ 2–3 h
(§9's ~965 jobs; the pilot labeled 791 + read in
≈ 1 h 57 min).

## 5. Timeout

**GAME_TIMEOUT = 8031 s** for BOTH arms' drivers:
3 × the pilot's observed maximum game wall
3 × 2,676.8 = 8,030.4 → 8031 (ceiling). (The ruling
offered "7,845 s or re-derived from the pilot's
2,676.8 s maximum, e.g. 3 × max ≈ 8,031 s"; the
re-derived figure is registered.)

Fleet timeout SCORING (round 9, encoded in
`fleet_read.py` and planted in `fx_fleet_read.py`):
a teacher-arm timeout scores as a teacher LOSS in the
primary, with the drop-the-pair sensitivity
co-reported; teacher timeouts > 2% of teacher games
→ INCONCLUSIVE. A raw-arm timeout is rerun ONCE (the
games runner's RAW-RERUN section, Stage 3 form); a
second hang DROPS the pair. (Excluded + dropped)
> 2% of attempted pairs → INCONCLUSIVE.

## 6. Pre-gate: none fresh — a mechanical gate instead

No new pre-gate run: the build sha and tuple are
already covered by the Step 1 pre-gate attempt 2's
IDENTICAL (same build, same tuple). The fleet games
runner's **PREGATE-GATE** section refuses (exit 1,
before any spawn) unless the attempt-2
`pregate_manifest.json` (box:
`/home/joe/tcg/r10pilot_out/pregate/attempt2/pregate_manifest.json`)
reads verdict IDENTICAL, its `search_s3_thr_sha256`
equals this run's pin, and its `teacher_tuple_json`
equals the TEACHER_TUPLE_JSON this run builds from
`settings_fleet.json`.

One build finding lives here: the attempt-2 manifest
recorded `teacher_tuple_json` in json.dumps' DEFAULT
(spaced) separator form, so the fleet SETREAD builds
the tuple string in the same form — a compact-
separator build would fail the gate's string
comparison at launch. `fx_fleet_parity.py` executes
the runner's own SETREAD and string-compares its
output to the published manifest; `fx_fleet_blocks.sh`
runs the extracted gate block against the real
manifest (passes) and against verdict/sha/tuple
mutations and a missing manifest (refuses, all four).

## 7. The primary read (`fleet_read.py`, Part A)

Reconciliation before any number: pair count ==
settings (122); the games report's tuple audit ok;
teacher stat rows recounted == the games report; the
R14 root-canary refusal class counted BY NAME;
gamename uniqueness over completed rows. Scores at
draw = 0 (1 iff the arm's player won; a teacher
timeout scores the teacher 0). Δ = pooled mean paired
diff over scored pairs (statuses scored +
teacher_timeout); CI = seed-clustered bootstrap
(cluster = seed, both seats; B = 10000; rng seed
20261030, registered in settings). Co-reports: Δ at
draw = 0.5 (a teacher timeout still scores 0), the
game-level life differential (life scores from
p1life/p2life under the ONE definition,
`fleet_games_report.life_score`, imported — win → 1;
capped with own life strictly greater → 1; else 0;
the draw flag plays no part), per-seat Δs, the
drop-teacher-timeout sensitivity. IMPEACHMENT: a
primary mean > +0.25 prints, before the verdict,
(i) the leave-one-seed-out range, (ii) the
drop-teacher-timeout sensitivity, (iii) the per-seat
table, (iv) the per-block pair table.

BANDS (round 9, verbatim): **"INCONCLUSIVE iff
teacher timeout rate > 0.02 or (excluded + dropped)
rate > 0.02; CONVERTS iff CI lower > 0; HARMS iff CI
upper < 0; else DOES NOT CONVERT"** — INCONCLUSIVE
overrides. The VERDICT line prints last.

Verification anchor: run against round 9's PUBLISHED
Stage 3 pairing/games-report during the build,
`fleet_read.py --primary-only` reproduced Stage 3's
published read exactly — mean 0.0475, CI
[0.0000, 0.0950], Δ05 0.0300, life +0.0200, canary 8,
37,092 stat rows, DOES NOT CONVERT.

## 8. The Step 2 co-read (`fleet_read.py`, Part B)

L3 (W=50 CRN, production server `81ef2cdb…`, §14
label engine `search_s2.php` `1c964160…`, tuple
L3-W50+H) on ALL teacher-arm overturns (jobs built by
`build_fleet_jobs.py`, the pilot builder's fork —
pairing, classes at the 0.97 boundary, strict JSON).
Per-game gain in the pilot's registered direct form:
cap-aligned world scores (1.0 iff outcome > 0 AND the
world ended by turn 61), CRN-paired job diffs over
worlds finished in both candidates, per-game totals
over ALL completed teacher games (driver rows without
"invalid"; zero-job games contribute 0; teacher-
timeout games are excluded from the population and
counted), gain = mean of per-game totals; bounds from
ONE set of game-cluster bootstrap replicates
(B = 10000, seed 20261020 — the pilot's registered
bootstrap, cross-checked against
`analyze_l3.cluster_bootstrap`); lb = 5th percentile,
ub = 95th (one-sided 95%); SE = sd(per-game totals,
ddof=1)/√n. Per-class reads and z-band edges in the
pilot's form; LOGO range + largest share.

**The registered decision rule** (the pilot package's
two-sample bar, stated exactly): STEP 2 GATE: PASS
iff

  z = (gain_fleet − 0.0649) / sqrt(SE_fleet² + 0.0090²) ≥ 1.645

(one-sided α = 0.05), against Stage 3's per-game gain
+0.0649 (SE 0.0090). Reported as the gate co-read in
the same output as the primary; never pooled with
pilot games. If the primary verdict is INCONCLUSIVE
the co-read still prints, flagged as under an
inconclusive fleet.

**Attribution:** per-game gain (above) and the ratio
gain ÷ the fleet's paired Δ under the round-9 §4
guard, in the record's own form: the plain numeric
ratio prints ONLY when Δ > 0 AND its CI excludes 0;
Δ ≤ 0 prints "n/a (Δ ≤ 0)"; Δ > 0 with a CI including
0 prints "unstable (Δ CI includes 0)" — with Δ's CI
printed beside the label in both guarded cases and
the JSON carrying ratio_to_delta: null + ratio_note.
The Fai references (87% / 101%) print as history
beside the line, not as this run's result.

## 9. Labels: the fresh seed family

Expected volume: the pilot's realized 7.91
fires/game × 122 teacher games ≈ **965 jobs**,
sharded by sha256(game) mod 4 (the pilot's form;
realized shard shares 16–29%); enforced cap
**512 jobs/shard** (≈ 1.75× the expected largest
shard; a cap trip ABORTS by registration, never
truncates).

Family: **MEAS_SEED base 1,100,055,001 + shard × 10⁸**,
4 shards, W=50 — span per shard at cap 52,637,046
< 10⁸. The drafting candidate 800,055,001 does NOT
clear enumeration: it is exactly the pilot family's
shard-1 base (700,055,001 + 1×10⁸), inside the pilot
family's registered spans. The registered base sits
above every prior family's span; the nearest below is
the pilot family's shard-3 top at its cap,
1,052,692,047 — the fleet base sits 47,362,954 above
it. `fx_fleet_seeds.py` proves RANGES and VALUES
disjoint by enumeration against ALL prior families
(round-8 distill ×2, round-9 Stages 0/1/2/3, probe
eval, probe labels, supplementary A/B, and the pilot
family at its registered cap).

The jobs file is written strict (allow_nan=False) at
the source — the §14.6 ruling (b) form for any jobs
file a PHP process reads.

## 10. Runners and code

New directory `rounds/round10/code/step2/` (17 files;
§16). Two runners, Stage 3 / pilot forms throughout:

- **`run_fleet_games.sh`** — pins (every deployed file
  expect_hash'd) → SETREAD → TUPLE-BUILD →
  PREGATE-GATE → FREESPACE (8 trees) → G8 + SHM sweep
  → teacher servers (patched) + 4 teacher blocks
  (threshold build installed + hash-asserted per tree;
  TEACHER_SNAP_DIR per block at the pilot's
  `games_<blk>_log/snaps` layout) → raw servers + 4
  raw blocks (`--arm raw`; trees keep the fleet
  search.php, asserted) → RAW-RERUN (draft pairing;
  one rerun per raw timeout into
  `games_<rblk>_rerun.jsonl`, reusing the raw trees
  and live servers, Stage 3 form) → games report +
  registry merge (tag **r10_step2_fleet**, all
  games_*_ids.txt) → `fleet_read.py --primary-only`
  → games manifest. Single-shot: refuses if the
  fleet outputs exist.
- **`run_fleet_l3.sh`** — requires the games phase's
  fleet_read.json + games_report.json + pairing.json
  → pins → SETREAD (label parameters; LABEL_BASE
  asserted == settings) → FREESPACE (4 trees) → G8 →
  jobs build → per-shard player split (pilot form,
  snap-dir assertion) → production servers ×2 seats
  (pilot PILOT-LABEL-SRV form: 'search model loaded'
  + 'ckpt_v10' readiness) → 4 label trees (§14 engine
  installed + asserted; per-tree SHM sweepers) → label
  shards → `fleet_read.py` FULL (primary recomputed
  identically — deterministic bootstrap — plus the
  co-read) → L3 manifest. Single-shot likewise.

OUT root on the box: `/home/joe/tcg/r10fleet_out`
(games/ outputs at its root, labels under `l3/`).
Box code dir: `/home/joe/tcg/round10_code/step2`.

## 11. FREESPACE plan

Per-tree bytes are measured FRESH at runtime by each
runner's pre-flight (du -sb of the source tree; last
measured 468,711,508 B on 2026-10-27/29). Games
runner: 8 fleet trees → factored requirement at the
last measure = 468,711,508 × 8 × 1.25 =
4,687,115,080 B. L3 runner: 4 label trees →
2,343,557,540 B at the same measure. The plan assumes
/tmp also carries the pilot's scratch trees
(`/tmp/r10pilot_gm_s1a`, `_s1b`, `_s2a`, `_s2b`,
`/tmp/r10pilot_l3_tree_0..3`) — those are disposable
now that the pilot's data is published; the package
deletes nothing itself, and each runner's pre-flight
(integer form: abort when available × 4 < required
× 5) remains the mechanical guard.

## 12. Fixtures

New suite `fixtures/run_fx_fleet.sh` →
`fixtures/fx_fleet_outputs.txt`: **122 PASS, 0 FAIL**
— fx_fleet_seeds 14, fx_fleet_sizing 11,
fx_fleet_pins 13, fx_fleet_parity 12, fx_fleet_read
21, fx_fleet_blocks 46, and the bash -n trailer 5.
Two consecutive runs of the driver produce
byte-identical transcripts. Coverage:
seed freshness + label enumeration at cap; sizing
arithmetic under both conventions + the Δ = 0.10
cross-check + the timeout derivation from the
published pilot read; pin coverage of both runners
with a pin-stripped negative case; invocation parity
(driver flag sets, read flag delta, the SETREAD
executed against the real manifest); writer→reader
round trips on REAL shapes (arm-local gamenames;
pairing by seed+seat) covering every pairing status,
all four verdict bands incl. both INCONCLUSIVE
overrides at 3/122 and their boundary at 2/122, the
impeachment print, a hand-computed Step 2 gate PASS
(z = 2.1295) and FAIL plant, and all three
attribution-guard branches; verbatim block extraction
(PREGATE-GATE pass/refusals, FREESPACE seams on both
runners, RAW-RERUN spawn counts, TS/RS composed
environments incl. the emptied-tuple negative).

Regression, this run: fx_pilot suite **144 PASS**,
transcript byte-identical to the committed
`fx_pilot_outputs.txt`; fx_r10 suite **197 PASS**,
deterministic across two runs. (Transcript counts
are the suites' own PASS lines.)

## 13. Publication (stated in advance)

On completion: a fleet report
(`rounds/round10/step2-fleet-report.md`) built from
the primary files, and `rounds/round10/data/step2/`
with a MANIFEST.md (sha256 + row counts + role per
file). Label parts are stored gzip-compressed
(`labels_shard*_p*.jsonl.gz`) with their decompressed
sha256s in the MANIFEST, and labels_all.jsonl itself
is not committed if it exceeds the platform per-file
limit — the pilot's precedent, stated here in advance
rather than discovered mid-publication. Interim
notices during the run carry status + artifact paths
only, never figures.

## 14. Launch shape (what Joe's go starts)

1. Deploy `code/step2/` to the box; launch
   `run_fleet_games.sh` (setsid). Teacher arm ≈ 15 h
   wall; raw arm follows in minutes; the primary read
   prints at the end of the games phase.
2. Launch `run_fleet_l3.sh`: ≈ 2–3 h; ends with the
   full `fleet_read` (primary + co-read + Step 2 gate
   + attribution) at
   `/home/joe/tcg/r10fleet_out/fleet_read.txt`.
3. Fleet report + data/step2 publication (one commit,
   the §13 form), then Claude's ruling.
A progress-tracker artifact is offered at launch
(Joe's call, per the Stage 3 precedent) — the launch
message will ask.

## 15. Decisions the design left open (flagged)

1. **Label base moved:** 800,055,001 → 1,100,055,001
   (the candidate is the pilot family's shard-1 base;
   §9). The brief's "if enumeration clears it" did
   not clear.
2. **Sizing convention:** the two-sided convention
   yields the registered 122; the one-sided yields
   ~95 (§4). Registered: 122, conservative.
3. **Attribution guard wording:** implemented in
   round 9's exact guard language ("n/a (Δ ≤ 0)" /
   "unstable (Δ CI includes 0)") rather than a new
   "not-identified" label — the brief's substance
   (ratio withheld unless its conditions hold) is
   unchanged; the record's own terms govern.
4. **No separate Stage-3-style attribution tripwire**
   in fleet_read: the pilot's registered read form
   carries none; the primary's impeachment block and
   the co-read's LOGO cover influence.
5. **Bootstrap rng seeds:** paired primary 20261030
   (new, registered in settings bands.bootstrap);
   the co-read retains the pilot's registered
   20261020.
6. **pregate_check_pilot.py not redeployed** in
   code/step2: the fleet gate needs only the attempt-2
   manifest + the pins (no fresh pre-gate run exists
   to check).
7. **Co-read population** = completed teacher games
   (the pilot read's population form); teacher-timeout
   games are excluded and counted, and the primary's
   INCONCLUSIVE rule governs them.
8. **Box-file pins taken from the deployed record:**
   the full sha256s of the fleet tree's search.php,
   the deck, ckpt_v10, and the production server are
   pinned as they stand in the deployed round-9 /
   round-10 runners in this repo (the governing
   record), and the pins fixture verifies every
   $CODE_DIR pin against the staged files.
9. **RAW-RERUN aligned to Stage 3's exact form**
   (selector on the draft pairing's raw rows; reruns
   reuse the raw trees and the live raw servers)
   after a first draft invented a pairing status the
   report never emits — caught by the round-trip
   fixture before any launch.
10. **L3 machinery follows the pilot runner's forms**
    (jobs --stream prefix form, isdir-asserting split,
    PILOT-LABEL-SRV server block, per-tree sweepers)
    where Stage 3's L3 runner differed; the games
    runner follows Stage 3's games form.

## 16. Files and sha256

code/step2/ (new):
- settings_fleet.json — 1a8de29007a9e4f5c0e0e2ab500306b2967c0cc468e9f6ed26ebc640f088faa4
- search_s3_thr.php — 4a1936fe8e8794af1bbbc94cd982e5b897210d6e100599b9cced1a22448ccb49 (copy of step1)
- search_s3.php — 87779e8ec96935776ce35d94ae350647d8f4174c8a17ed572b1bd4887b9a7ba7 (copy)
- search_s2.php — 1c9641606144ec91bd63c19cfa6831f511d829064626a888ee366daff94767f8 (copy)
- s2_label_main.php — 1c1dfd9f9349e8db815f23e31637dee558a9ec36e09179142f71748a6bce72aa (copy)
- s1_eval_main.php — 0cb9d3c73114d5c6e54e93dd2dc122f20bd06ea8d8968fc4e703e8191b41e853 (copy)
- paired_driver_gravy.py — 3389b1b936180909b1f0c70f743ef2e6c414de933194405de344fc5abceaf359 (copy)
- build_fleet_jobs.py — c7601341302fdf43f2e6708ff2d8bd5ef5417d1c2edee9dbe45dac1ca6e3695f (fork of build_pilot_jobs.py: docstring + branding only)
- fleet_games_report.py — 62ca60b5bc289944d1a6d7e66f0567e4ffac895f0f6e9b9a876207615f4fe578 (fork of stage3_games_report.py: docstring only)
- fleet_read.py — 7370b989c36d1bac70673d4a3e16da35c6f39eb1daa425af3bb80df9d811cfdc (new)
- run_fleet_games.sh — 2a2ab08268d1c675f06cfeb635b61320712b268617f18934e47393ed9c0c2012 (new; §20 fix pass — supersedes the §19 fork rebuild 95abaa4f0fdc359f25c7c70cb5b199f6425aaec95bee390dadb23b349d36fd43; before it the §18 repair 24b2fd02b3e2ac32980ff5f6fb841865b96ae0f3c1163f8885b1b12fbd93d709; the as-approved build was 8e3c3fbd9195cf0cdfb2dd255e93584cffb805318245d7307378e8113fd79191)
- run_fleet_l3.sh — 56a0688bb6d57be977992f2e40a979286f1f79472bc06629c4eb377b31cbafd0 (new; §20 defect-9 line removal — supersedes 2f28e0cc176ba07aa5bc1c98c32e1187c42f73d5ac081c713d10d26d35e0dabb)
- merge_registry.py — 13a655e37d2d1eb04c80c8b6c1e1c8009ed2757b146f20cc7ebbcf5b9faf6bbe (copy)
- shm_sweep.py — 98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 (copy)
- g8_sweep2.sh — d49981cab7c6c3538434551ac1e837d81b781b4319abdf3b49c05ed3b524bc17 (copy)
- stage0_report.py — 5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf (copy)
- analyze_l3.py — 16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 (copy)

fixtures/ (new):
- fx_fleet_seeds.py — 563e1ebac1d0a72357b7ddad0b1d6b679e5776d665a9fbe4f49f661f20254632
- fx_fleet_sizing.py — b21bf51212002fa0683d4cd0c199ea530ca2079d7fc7b42296aa7191011a367a
- fx_fleet_pins.py — a35011820ec7c1172096956306df5baccd2d4142377b7a54c485040d43cd2ccd
- fx_fleet_parity.py — ccb47ad61e7d2be7342705aa4d5df22c1c8f024f3c08451b466ef11d027ac269
- fx_fleet_read.py — 9cce80b78cde421bbf88eb148e5a093a9c94ec18041d6bbed5577afee211105f
- fx_fleet_blocks.sh — ce698e8f479da68ffa71b95afce80a1273a8a1e44c65f21fb6dd885ab4b922d7
- run_fx_fleet.sh — d44c2ef1c53f9da3cf65a8beeb0fcb5a055d4baafb35b7028122a8599643e37b
- fx_fleet_outputs.txt — 1f149c6cb128f1e9df481d1e1e63424573499e3c8fad6d6a26de27458995252d

## 17. Amendment (2026-10-30) — the review's non-blocking items, done

Post-approval fix pass on `claude-reply-5b5ada4.md`'s
two non-blocking items. Nothing under `code/step2/`
is touched; §§12/16 stand as the as-approved record
(this amendment supersedes their suite totals).

1. **The anchor is now IN the suite.** New fixture
   `fixtures/fx_fleet_anchor.py` (sha256 dbb14e20…):
   it maps round 9's published Stage 3 flat
   `search_stats_<blk>.jsonl` files into the
   `games_<blk>_log/` layout inside a temp dir
   (removed on exit), runs `fleet_read.py
   --primary-only` on the published pairing +
   games report, and asserts the primary line
   (+0.0475, CI [0.0000, 0.0950]), the verdict
   DOES NOT CONVERT, the reconciled 37092 teacher
   stat rows, and the 8 R14 root-canary records —
   **6 checks**, all PASS. It reads only published
   data.
2. **The transcript is host-independent.**
   `run_fx_fleet.sh`'s five `bash -n` PASS lines now
   print repo-relative paths (`code/step2/…`,
   `fixtures/…`) instead of absolute ones, so
   `fx_fleet_outputs.txt` reproduces byte-identically
   on any host.

New fleet suite total: **128 PASS, 0 FAIL** (122 +
the anchor's 6), two consecutive runs byte-identical.
Regression: pilot suite 144 PASS and round-10 suite
197 PASS, both transcripts byte-identical to their
committed ones. Changed/new files: fx_fleet_anchor.py
(new, dbb14e20…), run_fx_fleet.sh (c4a94b88…),
fx_fleet_outputs.txt (8f4cda2e…), and this doc.

## 18. Repair (2026-10-30) — SEARCH_MODEL missing at both server spawn sites

Post-launch repair. The fleet was launched twice on
2026-10-30 and aborted both times before any game;
the second abort exposed a defect in
`run_fleet_games.sh` as approved (8e3c3fbd…). This
section is the repair record; the launch gate is
unchanged (relaunch only on Claude's confirmation
of this repair plus Joe's go, from the repaired
commit).

### 18.1 The defect

Both server spawn sites in `run_fleet_games.sh`
start the pinned PRODUCTION server,
`rl/search_server.py` (sha256 81ef2cdb…), whose
lines 68–69 exit when `SEARCH_MODEL` is unset or
empty. Neither spawn block set it:

- **TS-SRV** (teacher, ports 18241/18242): set only
  the PATCHED server's env names —
  `TCG_POLICY_SEARCH=1`,
  `TCG_POLICY_SEARCH_CKPT="$CKPT"`,
  `TCG_POLICY_SEARCH_DEVICE=cuda`,
  `TCG_SEARCH_SERVER=patched`. The production
  server reads none of them; its environ reads are
  `TCG_POLICY_SOCK`, `SEARCH_MODEL`, `TCG_OPP_MIX`,
  `TCG_LEARNER_SEAT`, `EVAL_BATCH`, `EVAL_WAIT_MS`,
  `TCG_TRAJ_LOG`.
- **RS-SRV** (raw, ports 18251/18252): set only
  `TCG_POLICY_SEARCH_DEVICE=cuda`.

The pilot's proven spawn form
(`code/step1/run_pilot.sh`, lines 246 and 357) sets
`SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0"`.
`run_fleet_l3.sh` was already correct (its line 207
sets `SEARCH_MODEL="$CKPT"`) and is untouched by
this repair.

### 18.2 The two aborted launches — zero consumption

- **Launch 1, 2026-10-30 13:10 EDT**: aborted at
  the FREESPACE pre-flight (`/tmp` free space below
  required × 1.25), before any spawn. Cleared by
  deleting the pilot's eight scratch trees on
  Joe's go.
- **Launch 2, 2026-10-30 13:38 EDT** (the launch
  command's own timestamp reads 13:38:14 EDT;
  `step2-fleet-launch-facts.md`'s "13:44" is
  superseded by it): passed the pin checks, the
  PREGATE-GATE, and the FREESPACE pre-flight, then
  aborted at teacher-server start —
  `srv_18241.log` reads
  `search_server: SEARCH_MODEL missing: ''`.

Both launches aborted before any game spawn: zero
games played, zero seeds consumed, zero registry
consumption. The single-shot guards
(`games_manifest.json`, `fleet_read.json`) remain
absent, so a relaunch after this repair starts
clean.

### 18.3 The fix

Two inserted lines in
`code/step2/run_fleet_games.sh` — one per spawn
block — and nothing else in the file:

```
 TS-SRV (teacher, ports 18241 18242):
     TCG_SEARCH_SERVER=patched \
+    SEARCH_MODEL="$CKPT" \
     $PY rl/search_server.py --socket /tmp/pol_$port.sock \

 RS-SRV (raw, ports 18251 18252):
   ( cd "$SIM" && TCG_POLICY_SEARCH_DEVICE=cuda \
+    SEARCH_MODEL="$CKPT" \
     $PY rl/search_server.py --socket /tmp/pol_$port.sock \
```

The inert `TCG_POLICY_SEARCH*` lines are left in
place: the pinned production server never reads
them, and removing them is not part of this
repair. No other file under `code/step2/` is
touched.

New pin: `run_fleet_games.sh` —
**24b2fd02b3e2ac32980ff5f6fb841865b96ae0f3c1163f8885b1b12fbd93d709**.
§16's pin line is updated in place to this hash,
with the as-approved hash (8e3c3fbd…) recorded
beside it. The truncated pin in
`step2-fleet-launch-facts.md` (8e3c3fbd…) is the
historical record of the build that was actually
launched and is left unchanged. No fixture pinned
the old hash (`fx_fleet_pins.py` asserts the
runner's internal expect_hash literals against the
staged files, never the runner's own hash).

### 18.4 Fixture coverage

New fixture `fixtures/fx_fleet_server_env.py`
(sha256
a255835c32ba1b059b8266fdc8b5d752662fb14124caa437ec26235c629a91a7),
wired into `run_fx_fleet.sh`. It extracts both
`search_server.py` spawn blocks VERBATIM from the
staged runner (each `for port in` header through
its spawn loop's closing `done`) and asserts
exactly 2 spawn sites, each carrying the literal
line `SEARCH_MODEL="$CKPT"`; two negative cases
(both lines stripped; only the raw block's line
stripped) must fail the affected blocks. That is
all it proves: it is a text-level guard on the
staged runner. It does NOT start a server, load a
model, or exercise the composed runtime
environment — the first runtime proof is the
relaunch's own server-ready gate.

### 18.5 Suites and changed files

Fleet suite: **135 PASS, 0 FAIL** (128 + the new
fixture's 7), two consecutive runs byte-identical.
Pilot suite 144 PASS and round-10 suite 197 PASS,
both transcripts byte-identical to their committed
ones. Changed/new files: `run_fleet_games.sh`
(24b2fd02…), `fx_fleet_server_env.py` (new,
a255835c…), `run_fx_fleet.sh`
(6899309d5514232c7ac6a92a56ea62d6ec312cef2ff15aa3493631c9a9700280),
`fx_fleet_outputs.txt`
(a5cc33768a07a550ad3b8b010bed18f74d40bf1152ba1e124a3b53268a51b549),
and this doc. §16's entries for `run_fx_fleet.sh`
and `fx_fleet_outputs.txt` are superseded by this
section (the §17 convention).

### 18.6 Relaunch condition

The fleet relaunches only when (a) Claude has
confirmed this repair package and (b) Joe has
given the go, and the launched sha is the repaired
commit (launched sha == approved sha, or differs
only under `rounds/`, per the standing launch
gate). §14's launch shape is otherwise unchanged.

## 19. The fork rebuild (reply 5ea3a72 §2) — and a failed smoke

§18's repair is NOT CONFIRMED (claude-reply-5ea3a72).
The `SEARCH_MODEL` insertion was necessary and is
retained, but the as-approved games runner's
server/driver blocks carried seven contract
defects, and the §18 suite's 135 checks passed
because every fixture stubbed the counterparty:
none composed a spawn against the real server's
environment reads, or a driver call against the
real argparse. This section records the rebuild
the reply ordered — verbatim forks, real-contract
fixtures, a runtime smoke — and the smoke's
result: **the smoke FAILED, on a defect in the
smoke switch itself (§19.4). The fleet does not
launch on this package; the rebuild returns for
review first (§19.7).**

### 19.1 The seven defects (reply §1)

1. `SEARCH_MODEL` missing at both spawns (the
   §18 defect; fixed there, kept in the fork).
2. Servers spawned with `--socket`/`--port` argv
   the server never reads — the socket is the
   `TCG_POLICY_SOCK` environment variable (default
   `/tmp/tcg_policy.sock`), so both servers would
   have bound the same default socket and the
   drivers' `--sock` paths would never have
   existed.
3. `TCG_LEARNER_SEAT` unset (default 1): the
   seat-2 blocks would silently have played the
   teacher's decisions with the heuristic — silent
   corruption of half the fleet.
4. `TCG_OPP_MIX` unset (its default happens to
   match; the fork sets it explicitly).
5. Readiness grep `'"ready": true'` occurs
   nowhere in the server, which prints
   `search model loaded (…)` — the §18 relaunch
   would have aborted at "teacher server not
   ready" even with defect 1 fixed.
6. Driver argv carried `--max-turns`/
   `--cap-trigger`, which the pinned driver's
   argparse does not define (every driver would
   exit 2), and omitted `--deck`, silently
   substituting the driver's hard-coded default
   path for the pinned tree deck.
7. The runner spawned the PRODUCTION server from
   `$SIM`; the pilot's and Stage 3's games ran
   the tree's PATCHED server
   (`$GTREE/rl/search_server.py`, pinned
   ab85fa1b…), which is the build the pre-gate
   certified.
Plus: `TCG_CLEAN_CHILDREN=1` absent per driver
invocation, and one shared sweeper loop instead
of one sweeper per tree.

### 19.2 The fork rebuild

`run_fleet_games.sh` is rebuilt so the four
server/driver sections are verbatim forks of the
blocks that have actually run — Stage 3's games
runner (`rounds/round9/code/run_stage3_games.sh`,
the pilot runner's own descendant; the server and
driver blocks are token-identical to
`run_pilot.sh`'s PILOT-SRV/PILOT-GAMES modulo the
items below):

- **TS-SRV / RS-SRV**: per-seat spawn loops of the
  tree's patched server, `TCG_POLICY_SOCK=
  "$OUT/srv_s${seat}.sock"`, `TCG_LEARNER_SEAT=
  $seat`, `SEARCH_MODEL="$CKPT"`,
  `TCG_OPP_MIX="heuristic:1.0"`, readiness greps
  for `search model loaded` and `ckpt_v10`; the
  raw phase kills the teacher servers by pid and
  restarts on the same sockets.
- **TS-TREES / RS-TREES** (tree preparation,
  previously interleaved in the driver sections):
  Stage 3's tree loops; teacher trees install the
  fleet build `search_s3_thr.php` (4a1936fe…),
  raw trees keep the fleet `search.php`
  (8f6b35da…).
- **TS-SWEEP / RS-SWEEP**: one sweeper per tree,
  Stage 3's form.
- **TS-DRIVERS / RS-DRIVERS**: the pilot/Stage 3
  spawn loops, `--deck "$tree/$DECK_REL"`,
  `TCG_CLEAN_CHILDREN=1` per invocation,
  `TEACHER_TUPLE_JSON` / `TEACHER_SNAP_DIR` on
  the teacher arm only, `--arm raw` on the raw
  arm.
- **WAIT-T / WAIT-R**: the source blocks' wait +
  abort-on-failure + sweeper stop touches.
  Driver failure now ABORTS the run (the source
  form), replacing the as-approved runner's
  non-fatal "note:" lines.
- **RAW-RERUN**: the fleet's approved draft
  report + timeout selector kept byte-identical
  (the selector text is also Stage 3's); the
  rerun driver subshell is forked to Stage 3's
  form.
- Head changes: `DECK_REL` defined with the
  fleet's deck; a PINFN pin for the tree's
  patched server (`expect_hash
  "$GTREE/rl/search_server.py"` ab85fa1b…); the
  source blocks' server/sweeper cleanup trap.
  The inert `TCG_POLICY_SEARCH*` lines and the
  port-numbered spawns are gone. Everything else
  — pin checks, the pregate gate, the freespace
  pre-flight, phase order, the single-shot
  guards, `GAME_TIMEOUT=8031`, the registry
  merge, the read and the manifest — is as
  approved, byte-untouched.

Allowed differences from the sources, exhaustive:
seeds (the fleet's settings-sourced `$BLOCK_*`
variables where Stage 3 carries literals), block
tags, paths (the `r10fleet` tree prefix), the
installed teacher build and its hash,
`--timeout "$GAME_TIMEOUT"` in the fleet's quoted
settings-sourced form (Stage 3's is unquoted;
§16's parity check (c) requires the fleet form),
`TEACHER_SNAP_DIR` in the expanded
`"$OUT/games_${blk}_log/snaps"` form (Stage 3
writes `"$logdir/snaps"`; the value is identical,
`logdir` being assigned that path two lines
above; §16's pin-site check requires the fleet
form), the tree sections' `expect_hash` in the
fleet's two-argument form (Stage 3 appends a
label and `|| exit 1`; the fleet's `expect_hash`
exits internally), `--arm raw`, and the SMOKE
skip-guard lines (§19.4, inert unless SMOKE=1).

### 19.3 The real-contract fixtures

New fixture `fixtures/fx_fleet_contract.py`
(47 checks), wired into `run_fx_fleet.sh`:

- (a) Server env: parses every `os.environ.get`
  name from the PINNED PATCHED server source —
  published in this package at
  `fixtures/ref_patched_search_server.py`,
  sha256
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c,
  a byte-identical copy of the box's
  `$GTREE/rl/search_server.py` as pinned by
  `run_pilot.sh` / `run_stage3_games.sh` (also
  byte-identical to the already-published
  `rounds/round3/code/search_server.py`); the
  fixture asserts the hash before parsing. Both
  spawn blocks must set `SEARCH_MODEL`,
  `TCG_POLICY_SOCK`, `TCG_LEARNER_SEAT`,
  `TCG_OPP_MIX`; the socket embeds `${seat}`;
  `TCG_LEARNER_SEAT` is that same `$seat`; the
  runner pins the spawned server path; the
  defect tokens of §19.1 occur nowhere in the
  runner.
- (b) Socket wiring: every driver invocation's
  `--sock` equals the spawn blocks'
  `TCG_POLICY_SOCK` template.
- (c) Readiness: `search model loaded` occurs
  literally in the pinned server source;
  `'"ready": true'` occurs nowhere in it; the
  `ckpt_v10` log grep is anchored to the
  runner's `CKPT` basename, the string the
  server prints from `SEARCH_MODEL`.
- (d) Driver argv: each invocation (TS-DRIVERS,
  RS-DRIVERS, RAW-RERUN) is extracted verbatim,
  substituted, and parsed under the REAL
  `paired_driver_gravy.py` argparse (built by
  executing the pinned driver's own
  `add_argument` statements; its sha256 is
  asserted first). All parse; `--deck` resolves
  to the tree deck. Negative cases: argv +
  `--max-turns` and argv + `--cap-trigger` must
  fail parsing (exit 2). Both do.
- (e) Parity: the forked segments equal their
  Stage 3 sources (and the server/driver blocks
  the pilot's) as token streams after ONLY the
  §19.2 enumerated normalizations.

`fx_fleet_server_env.py` is updated to the
seat-loop form (its `SEARCH_MODEL` assertions are
unchanged in substance; in the forked spawn lines
the assignment is one env token among several, so
the check is on the token). Suite totals:
**fleet 186 PASS / 0 FAIL**, transcript
deterministic across two runs
(`fixtures/fx_fleet_outputs.txt` regenerated);
pilot 144 and r10 197 unchanged, transcripts
byte-identical.

### 19.4 The smoke — FAILED (one root cause)

Registration: seed **27001**, block (27001,
27001), played at both seats in both arms (4
games) under registry tag
`r10_step2_fleet_smoke`, never analyzed.
Freshness: disjoint from every block in the
fixtures' game-block record (the D2 list,
21001–21100 incl. the reserved Stage 1
extension, 22001–22100, 23001–23200,
24001–24090, 25001–25050, 26001–26061,
13001–13010, 8601–8610, 9001–9200, the
3000-series); it continues the record's x0001
convention one step (+1000) above the fleet
block. The block is added to the record in
`fx_pilot_seeds.py` and checked in
`fx_fleet_seeds.py`. The runner's SMOKE=1 switch
changes only the output directory
(`/home/joe/tcg/r10fleet_smoke_out`) and the
seed lists (a-blocks = 27001; b-block lists
emptied, to be skipped by a guard line in each
driver loop).

Run record (box, 2026-10-30): deployed runner
read back at sha256 95abaa4f… (== staging);
pre-flight clean (no stale processes, SHM
baseline 0, /tmp available 5,844,172,800 B);
launched detached at **14:34:33 EDT**
(`SMOKE=1 bash run_fleet_games.sh`). Pins OK;
PREGATE-GATE ok; FREESPACE passed (required
3,749,692,064 B); both teacher servers loaded
`ckpt_v10.pt` and logged `listening on
…/srv_s{1,2}.sock (learner seat 1|2, opp
heuristic)` — the forked spawn side demonstrably
worked. The runner then **aborted in TS-DRIVERS
at line 297, `$3: unbound variable`**: an
emptied b-block spec (`"t1b 1 "`) word-splits to
two fields, so `seeds=$3` references an unset
positional under the runner's `set -u` — BEFORE
the skip-guard line, which sat after the
assignment. The guard's placement is the defect;
it is in the smoke switch, not in the forked
blocks, and the production path cannot reach it
(every production spec carries three fields).
The EXIT trap killed both teacher servers and
the sweepers. The already-spawned t1a driver
finished against the dead socket: its row is
`invalid: "connect_failed"` (`server_seat`
null; the game's output carried 637 "connect
failed" lines; all 116 of its stat rows are
`fallback:"eval"` / `abort_reason:
"root_eval_failed"` with the correct tuple stamp
`H8k-180+H`). The seat-2 teacher block, both
raw blocks, and RAW-RERUN never ran. SHM after
the abort: 1 leaked segment (the dead game's
cache; the containment class the sweepers
handle). All outputs are preserved under
`/home/joe/tcg/r10fleet_smoke_out/` and the
launch log at
`/home/joe/tcg/r10fleet_smoke_out.launch.log`.

Assertion read (reply §2.3): servers loaded on
the right model and seat — PASS as far as the
server logs go (both arms' spawns; the raw phase
never started). Every driver row valid with seat
and arm as specified — **FAIL** (the one row
produced is invalid; three of four games never
ran). Teacher tuple stamp `H8k-180+H` — present
on the stat rows of the invalid game; not a
passing smoke read. Raw rows carry no teacher
stat rows — not reached. **The smoke does not
pass, and the fleet does not start.**

Consumption and registry: seed 27001 is
partially consumed — one invalid game (id
776023215, seat 1, teacher arm) with its ids
file present in the smoke outdir. The registry
was NOT merged (still 7,641 games, sha256
6995d9ba653b325240b23794026b1f7117614ad7c434a16d5114ab72ab20f72e);
whether that single invalid id is merged, or
the seed retired outright, is for the reviewer
and Joe — a re-smoke cannot reuse 27001 as a
"fresh" seed without that ruling. No outcome of
any smoke game is read or reported anywhere in
this package.

Proposed minimal repair (for review, NOT
applied): in each driver loop, read the seeds as
`seeds=${3:-}` (set -u-safe) so the existing
skip-guard can fire — a one-token change per
loop, inside the SMOKE switch's own machinery,
touching no forked line's semantics. A second
smoke attempt needs the failure understood and
this repair (or its equivalent) reviewed first,
per the reply's terms.

### 19.5 An eighth defect, found in recon — the GRES merge

Outside the fork's scope and NOT fixed here:
the games runner's registry-merge invocation —
`merge_registry.py --tag "$REGISTRY_TAG"
"$OUT"/games_*_ids.txt` — exits 2 under the
pinned `merge_registry.py` (13a655e3…, identical
in step1/step2), whose argparse requires
`--registry` and `--ids` (verified against the
pinned file during this rebuild). The pilot's
working form is `merge_registry.py --registry
/home/joe/tcg/registry-vault/do_not_train_registry.json
--tag <tag> --ids <file>… --vault
/home/joe/tcg/registry-vault`. As approved, a
fleet launch would complete its games and the
draft report, then abort at the merge, before
the primary read and the manifest (the outputs
would be recoverable manually). The one-line
argv correction to the pilot form needs a
ruling before any fleet launch; the GRES
section is byte-untouched in this rebuild.

### 19.6 New pins

- `code/step2/run_fleet_games.sh` —
  95abaa4f0fdc359f25c7c70cb5b199f6425aaec95bee390dadb23b349d36fd43
  (§16's pin line is updated in place per the
  §18 convention; the deployed box copy reads
  back identical.)
- `fixtures/ref_patched_search_server.py` —
  ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c
  (new; provenance in §19.3(a))
- `fixtures/fx_fleet_contract.py` —
  80baff11e2a88aa6eefb122657445af09638838a3cab445be4215f2519281b3f
  (new)
- `fixtures/fx_fleet_server_env.py` —
  e91380e03b13cebb5eb12c41a81a577d00a34cb02bc67c2b2ddfeccd215e6c7b
  (seat-form update)
- `fixtures/fx_fleet_seeds.py` —
  e625b6415f22f6874a768052ed9eeba5cd863b0aa05bfb084cd1c012335cb27a
  (smoke registration checks)
- `fixtures/fx_pilot_seeds.py` —
  4b61431923a413eb4ad2e7c91d30df89f0ec4f90f761b29e4445fc26dc745118
  (fleet + smoke blocks added to the record)
- `fixtures/fx_fleet_blocks.sh` —
  5a437b8e324f8e16645d8e29b816e284c24c0c9f965f07ee376f2d003e9cfddc
  (DECK_REL in the extraction environments)
- `fixtures/run_fx_fleet.sh` —
  4bd8cb5bb3888de24893e44a8f1a1e278be23c5bf5e672e0562c91c912acb07a
  (fx_fleet_contract wired in)
- `fixtures/fx_fleet_outputs.txt` —
  2e6009abb010cf0a852486e65e1799065747888d90b66d77df9437f63e425683
  (regenerated transcript)
Every pin literal above is 64-hex, machine-copied.

### 19.7 The launch gate, restated

The fleet launches only after (a) Claude has
confirmed THIS rebuild package — including the
failed-smoke record in §19.4, the proposed
repair, and the GRES ruling in §19.5 — and
(b) Joe has given the go, with launched sha ==
this package's commit (or differing only under
`rounds/`, per the standing launch gate). The
§18 condition ("relaunch the §16-pinned build")
is superseded: the §16 pin now names the
rebuilt runner, and no launch of any build in
this line proceeds on the §18 package.

## 20. The fix pass (reply baf16e7) — defects 8 and 9, and the class closed

The rebuild at baf16e7f was reviewed in
claude-reply-baf16e7: the fork is ACCEPTED, and
CHANGES REQUESTED before the re-smoke — the two
rulings asked in §19 (the smoke repair; the GRES
merge correction) are both approved, a ninth
defect is added, and the pass must close the
class, not the instance: every Python invocation
in both runners checked against its real
argparse, and the smoke running through the
merge. This section is that pass. It returns for
a CONFIRMATION CHECK (§20.11); no smoke or fleet
run is made by it. One box write was authorized
and made: the seed-27001 retirement merge
(§20.7).

### 20.1 Defects 8 and 9, beside 1–7

8. **GRES merge argv.** The games runner merged
   with `merge_registry.py --tag "$REGISTRY_TAG"
   "$OUT"/games_*_ids.txt` — bare positional
   files the pinned tool's argparse rejects
   (it requires `--registry` and `--ids`; exit
   2). A fleet run would have finished its
   games and draft report, then aborted at the
   merge, before the primary read and the
   manifest. Fixed in §20.3.
9. **The prespawn sweeper call that never ran.**
   Both runners called
   `$PY "$CODE_DIR/shm_sweep.py" --once`
   (games ex-line 238, L3 ex-line 162). The
   pinned shm_sweep.py has no `--once` (it
   requires `--log --start-file --games-dir
   --stop-file`), so each call exited 2 — and
   each site ended in
   `|| echo "note: shm sweep nonzero"`, so the
   failure was swallowed on every launch. The
   pre-spawn sweep never ran; the G8 process
   guard did the cleanup the launch records
   credit. Removed in §20.4.

### 20.2 The smoke-switch repair (reply §2.1)

In each driver loop the SMOKE switch can empty
— TS-DRIVERS and RS-DRIVERS — the seeds field
is now read set -u-safely: `seeds=${3:-}` (one
token per loop; nothing else in either loop
changes). The existing skip-guard
(`[ "${SMOKE:-0}" = 1 ] && [ -z "$seeds" ] &&
continue`) now fires on emptied specs instead
of being crashed past.

RAW-RERUN determination: it does NOT share the
pattern. Its loop is `while read -r seed seat
rblk` over the computed rerun list — there is
no positional seeds read, and the SMOKE switch
does not empty rerun specs (the list is built
from the draft pairing's timeout rows). No
change; the determination is itself
fixture-checked in fx_fleet_smoke_loops.py.

Fixture (the ruling's condition): new
`fixtures/fx_fleet_smoke_loops.py` (13 checks).
It extracts each loop VERBATIM from the staged
runner and RUNS it under `set -u` with SMOKE's
emptied lists (a-blocks = the populated seed,
b-blocks empty) and a stub driver: the emptied
specs are skipped, the populated ones run
(exactly two stub invocations per arm, seats 1
and 2, no empty `--seeds`). Negative cases: the
same extracted loops with the repair reverted
(`seeds=$3`) abort with the unbound-variable
error — the §19.4 crash, reproduced. Parity
note: fx_fleet_contract.py's normalize() maps
the repaired form back to the source form, so
(e) parity continues to measure the fork; the
repair is recorded there as an enumerated
allowed difference.

### 20.3 The GRES merge correction (defect 8)

The GRES merge invocation is now the pilot's
working form (run_pilot.sh lines 304–309):

```
$PY "$CODE_DIR/merge_registry.py" \
  --registry /home/joe/tcg/registry-vault/do_not_train_registry.json \
  --tag "$REGISTRY_TAG" \
  --ids <file> (repeated per ids file) \
  --vault /home/joe/tcg/registry-vault
```

The pilot enumerates its four fixed ids files;
the fleet's ids set is the glob
`"$OUT"/games_*_ids.txt` (the eight block files
plus any rerun ids files) — the same set the
old form passed positionally, now emitted as
one `--ids` per file by a short loop ahead of
the call. The rest of GRES (the games report
call, the merge log handling, the abort shape)
is byte-untouched. The smoke tail (§20.5) uses
the identical form under the smoke tag.

### 20.4 Defect 9 removed; the tolerance sweep

Both `shm_sweep.py --once` invocation lines are
deleted outright, tolerance and all — one in
run_fleet_games.sh (G8 section), one in
run_fleet_l3.sh (G8 section). G8
(g8_sweep2.sh, invoked immediately above each
deletion site and aborting loud on a trip) is
the pre-spawn cleanup, as it in fact always
was.

Sweep: every `||` construct and every
`2>/dev/null` in both runners was enumerated
and dispositioned.

- Every remaining `||` is one of: `|| exit 1`;
  `|| { ABORT ...; exit 1; }`; a boolean guard
  whose failure aborts (`[ -f ... ] || {...}`,
  the LABEL_BASE/NSHARD equality checks); or
  `wait ... || FAIL=1` immediately followed by
  an abort on the flag. `[ -n "$seed" ] ||
  continue` in RAW-RERUN is a data skip inside
  a loop, not a step tolerance. No `|| echo`
  remains anywhere in either runner.
- Kept tolerances, each genuinely cosmetic:
  (a) `kill "$pid" 2>/dev/null` / `|| true` on
  server and sweeper stops (EXIT trap, the
  RS-SRV phase transition, WAIT-L) — the
  process may already have exited; a kill that
  mattered is backstopped by the next phase's
  readiness gate, which aborts loud if a stale
  server holds the socket. (b) The readiness
  poll greps (`grep -q ... 2>/dev/null &&
  break`): the log file may not exist yet —
  "not ready yet" is the poll's normal state,
  and the unconditional grep after the loop
  aborts loud. (c) `find ... -name __pycache__
  -exec rm -rf {} + 2>/dev/null` on freshly
  copied trees: best-effort cleanup; the
  copy's integrity is enforced immediately
  after by expect_hash pins on the installed
  files. (d) expect_hash's own
  `sha256sum "$1" 2>/dev/null`: a missing file
  yields an empty hash, which mismatches and
  aborts — the suppression cannot hide a
  failure.

### 20.5 The smoke runs through the merge (reply §4.2)

The SMOKE=1 branch (after RAW-RERUN, where the
§19 runner exited) now continues:

1. `fleet_games_report.py` in **pairing-only**
   form (`--pairing-only`, its own log), then
2. the registry merge under the smoke tag
   `r10_step2_fleet_smoke`, in the §20.3 pilot
   form (per-file `--ids` over the smoke
   outdir's `games_*_ids.txt`),

and exits BEFORE READ.G / MANIFEST, as before.
The merge argv's first runtime proof is now
the smoke, not the fleet.

Wiring choice, stated: pairing-only, because
the tool's full mode validates the pairing
against the settings' 122 registered pairs and
its argparse offers no expected-pairs override
(an `--expect-pairs` flag exists only on
fleet_read.py, which the smoke must not
reach). Pairing-only writes pairing_draft.json
in the smoke outdir, the same product the
RAW-RERUN draft call produces. The production
(non-SMOKE) flow is unchanged in phase order,
guards and read; its only change in this pass
is the §20.3 merge form inside GRES.

### 20.6 The argparse contract (reply §4.1)

New `fixtures/fx_fleet_argparse.py` (37
checks). It enumerates BY GREP every
`$PY "$CODE_DIR/<file>.py"` invocation in both
runners (continuation lines joined) and
compares the result — site identities AND full
argv templates — against its contract table:
a call site added or changed without a
contract entry fails. For each site, the argv
is parsed under that file's REAL argparse (the
parser rebuilt by AST replay of the pinned
file's own add_argument statements; each
file's sha256 asserted against its pin first;
shell variables substituted by type-valid
placeholders; the composite expansions
`${SMOKE_IDS[@]}` / `${GRES_IDS[@]}` /
`$STREAM_ARGS` / `$STAT_ARGS` each stand for
one representative option+value pair).
Negative cases: the sweeper's valid argv +
`--once` fails (defect 9's form); the merge's
old bare-files form fails (defect 8's form).

The final census (14 sites):

- run_fleet_games.sh (11): paired_driver ×3
  (TS-DRIVERS, RS-DRIVERS, RAW-RERUN);
  shm_sweep ×2 (TS-SWEEP, RS-SWEEP);
  fleet_games_report ×3 (RAW-RERUN draft,
  SMOKE report, GRES); merge_registry ×2
  (SMOKE, GRES); fleet_read ×1 (READ.G).
- run_fleet_l3.sh (3): build_fleet_jobs ×1
  (JOBS); shm_sweep ×1 (start_sweeper);
  fleet_read ×1 (READ.F).

Reconciliation with the reply's census (games:
driver ×3, shm ×3, report ×2, merge ×1, read
×1; L3: shm ×2, jobs ×1, read ×1): the reply
counted the prespawn `--once` sweep in both
runners (removed by §20.4: −1 shm each) and
predates the smoke-through-merge wiring
(§20.5: +1 report, +1 merge in games). Outside
the pattern by construction: `$PY -` heredocs
(inline code; no file invoked), the server
spawns (`$PY "$GTREE/rl/search_server.py"`,
`$PY "$PROD"` — env contract under
fx_fleet_contract (a)), and the L3 runner's
php label mains (hash-pinned at their
tree-install sites).

### 20.7 The seed-27001 retirement merge (the pass's one box write)

Executed on the box 2026-10-30 **15:28:42
EDT**, with the pinned merge tool
(/home/joe/tcg/round10_code/step2/merge_registry.py,
13a655e3…) in the §20.3 pilot form:

- argv: `--registry
  /home/joe/tcg/registry-vault/do_not_train_registry.json
  --tag r10_step2_fleet_smoke --ids
  /home/joe/tcg/r10fleet_smoke_out/games_t1a_ids.txt
  --vault /home/joe/tcg/registry-vault`
  (the ids file holds exactly the one id,
  776023215).
- Tool output: "merged: +1 new (tag
  r10_step2_fleet_smoke), 0 already under this
  tag; n_games=7642"; the tool wrote its own
  backup (do_not_train_registry.json.bak-20261030T152842)
  and vault copy
  (do_not_train_registry_20261030T152842.json).
- Registry: **7,641 → 7,642 games**; sha256
  6995d9ba653b325240b23794026b1f7117614ad7c434a16d5114ab72ab20f72e
  → **fd9172d2d50536cb974b12cdcba215d9e0b175ed2ea56bb7ec8a59c3964065dd**.
  The merged record reads
  games["776023215"] = "r10_step2_fleet_smoke".

Seed 27001 is RETIRED: consumed by the failed
smoke, its one game in the registry under the
smoke tag, never to be played again.

### 20.8 The re-smoke seed (record only)

Seed **27002** is registered for the re-smoke:
added to fx_pilot_seeds.py's USED_GAME_BLOCKS
beside 27001's entry, and in fx_fleet_seeds.py
as RESMOKE with freshness checks — disjoint
from every completed block in the record, the
fleet block (26001–26061) and the retired
smoke block (27001, 27001); it is the next
single seed above 27001 in the record's
single-seed smoke sequence. Registration only:
nothing in this pass runs it.

APPLIED at the builder's audit, before this
package was committed (the coordinator flagged
it rather than exceed its brief): the runner's
SMOKE section now names 27002 in all four seed
assignments, its comments and its echo line,
and the fx_fleet_seeds runner-text check
asserts 27002 — plus a guard that the retired
27001 appears in no SMOKE assignment. The
switch is inside this package, so the launched
sha can equal the confirmed commit with no
post-confirmation edit.

### 20.9 Suites

- Fleet suite: **239 PASS / 0 FAIL** (186 at
  §19 + 52: fx_fleet_smoke_loops 13,
  fx_fleet_argparse 37, fx_fleet_seeds +2 for
  the RESMOKE checks). Two consecutive runs
  byte-identical; transcript regenerated at
  fixtures/fx_fleet_outputs.txt.
- Pilot suite 144 PASS and round-10 suite 197
  PASS, both unchanged.
- `bash -n` clean on both runners (also
  covered by the fleet suite's tail checks).

### 20.10 New pins

- `code/step2/run_fleet_games.sh` —
  2a2ab08268d1c675f06cfeb635b61320712b268617f18934e47393ed9c0c2012
  (§16's pin line updated in place; chain
  retained there)
- `code/step2/run_fleet_l3.sh` —
  56a0688bb6d57be977992f2e40a979286f1f79472bc06629c4eb377b31cbafd0
  (§16's pin line updated in place)
- `fixtures/fx_fleet_contract.py` —
  661f73d00738c45c7accfbd34741c1a5a5649d02a1a90fa8562473366d28e7b3
  (normalize() gains the §20.2 mapping)
- `fixtures/fx_fleet_smoke_loops.py` —
  36ae5257b1f49ce99a45fcd09bafe48069a4bbe0abf37a363983e25424febc66
  (new)
- `fixtures/fx_fleet_argparse.py` —
  331845dbe45b21a18177043fa2a4329f44a9dae667cd6dee340635309ca806cc
  (new)
- `fixtures/fx_fleet_seeds.py` —
  e5fda4b9e59cce685caba2dfe2377113175572d2fca92f41574edeb468f62ed8
  (RESMOKE registration)
- `fixtures/fx_pilot_seeds.py` —
  f98bad529aaf26b577d67fd1eb1fdb060db910e559b6857235e835f95fde4443
  (record += (27002, 27002))
- `fixtures/run_fx_fleet.sh` —
  d50daab09c3ffaf099b9de10fcf6279767629a2cbcecd52e50a08d5656892615
  (both new fixtures wired in)
- `fixtures/fx_fleet_outputs.txt` —
  936ec8c04cd1e99fa0e816717129e3edb07e5a81b28fb6f1fa6d905ac0026af3
  (regenerated transcript, 239 PASS)
Every pin literal above is 64-hex, machine-copied.

### 20.11 The gate, restated

This pass returns to Claude for a CONFIRMATION
CHECK. After that confirmation, and subject to
the §20.8 open item being carried into the
confirmed state: the re-smoke (seed 27002,
both seats, both arms, through the games
report and the registry merge) runs on Joe's
go; **if it passes, the fleet launches under
that same go**, from a clean output directory,
with the single-shot guards untouched and
launched sha == the confirmed commit. If the
re-smoke fails, it stops and returns to
review. No other launch proceeds on this
pass.
