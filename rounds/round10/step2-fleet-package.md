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
- run_fleet_games.sh — 24b2fd02b3e2ac32980ff5f6fb841865b96ae0f3c1163f8885b1b12fbd93d709 (new; §18 repair — the as-approved build was 8e3c3fbd9195cf0cdfb2dd255e93584cffb805318245d7307378e8113fd79191)
- run_fleet_l3.sh — 2f28e0cc176ba07aa5bc1c98c32e1187c42f73d5ac081c713d10d26d35e0dabb (new)
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
