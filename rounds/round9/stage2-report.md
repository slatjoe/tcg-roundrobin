# Round 9 — Stage 2 REPORT (L3 on the calibrated teacher, H8k-180+H)

**VERDICT: PROCEED** — the analyzer's own word, from its
single read run under Claude's §3 conditions on
2026-10-27 (see §3). PRIMARY (horizon-aligned, draw = 0):
mean paired diff **+0.0621**, game-clustered CI
**[0.0440, 0.0809]** over the 353 labeled overturns;
per-game gain **+0.1096** at the LIVE overturn rate
(1.7650 overturns/game, 353 captured overturns over the
200 completed games). Both registered band conditions are
met: CI lower 0.0440 > 0, and per-game gain 0.1096 ≥
+0.05. **No tripwire fired** (the analyzer's tripwire
field is null; per-game gain 0.1096 < +0.25 and mean diff
0.0621 < +0.20), so no impeachment ordering applies and
the read stands as printed in §2. Full precision
(`stage2_read.json`): mean diff 0.06211481759842748, CI
[0.043972043611965314, 0.080939226519337], per-game gain
0.1096326530612245.

## 1. Provenance

- Design `8dddf387` (approved in direction `c76f6856`);
  Stage 0 POSITIVE (`16f02e2e`, ruling `8dce0fac`); the
  tie value settled for round 9 (draw = 0 primary;
  horizon-ended worlds score −1); Stage 1 calibrated the
  setting **H8k-180+H** (report `d7b92fdf`; Claude's
  ruling `508d8c4a`).
- Stage 2 package `a0599d45` → Claude's code review,
  changes requested (`ca87e0d6`) → fix pass `2d64302f` →
  **CONFIRMED** (`596baaed`): launch on Joe's go at
  launched sha == `2d64302f`.
- **Launch** (record `e8c4b7fa`): Joe's go 2026-10-26
  18:16 EDT; launched sha == approved sha `2d64302f`.
  **Pre-gate: IDENTICAL** (the checker's own
  `PREGATE: IDENTICAL` line; `pregate_manifest.json`
  records the verdict, `search_s2.php` sha256
  `85490e8e…`, and the pinned teacher tuple H8k-180+H);
  pre-gate registry merge → **6,331 games**.
- **Games:** launched 2026-10-26 19:16:39 EDT, seeds
  22001–22100 × both seats under the pinned tuple;
  completed 2026-10-27 02:26:02 EDT. **200/200 games
  completed** (50/50 × 4 blocks), invalid none,
  **teacher timeouts 0**; tuple audit OK over all 20,009
  teacher stat rows (0 bad rows, 0 malformed-pin aborts,
  every row stamped H8k-180+H); registry merge →
  **6,531 games** (sha256 `031b3c5d…`).
- **L3 jobs:** 353 captured overturns over 152 games
  (`jobs_all.jsonl` sha256 `96b62d0b…`; `jobs_report.json`).
  Labeling at LABEL_W=50, CRN, label tuple L3-W50+H
  (hooks 8000, deadline 180 s, horizon 62, horizon value
  −1, k 50), seed bases 955001 + shard×10⁸.
- **Labeling attempts 1–2 (no labels produced):**
  attempt 1 (2026-10-27 04:32 EDT) aborted at the G8
  containment sweep — the guard reported game processes
  running while process listings immediately before and
  after showed none; cause not established. Attempt 2
  (04:33 EDT) aborted on a full box /tmp (20G tmpfs) while
  copying shard trees; the runner's installed-file pin
  check caught the partial tree and aborted before any
  labeling; zero label rows. Both logs preserved in
  `/home/joe/tcg/r9s2_out/` (`l3_launch_aborted1.log`,
  `l3_launch.log`).
- **Attempt 3 — labeling completed, the read aborted:**
  relaunched 2026-10-27 04:37:17 EDT after ~3.5G of this
  stage's own completed-phase scratch trees were removed
  from /tmp. Labeling completed 05:37:47 EDT:
  **35,300 label rows** (353 jobs × 100 worlds). The
  runner's read step then ran the ORIGINAL analyzer
  (sha256 `9b1a0677…`) and it **ABORTED before any read**
  (05:37:48 EDT): `ABORT: 35300 label rows carry a
  setting stamp != the registered label tuple`. Cause:
  the analyzer's label-tuple audit demanded a seventh
  stamp key, `"pinned"`, that only the live path's stat
  rows carry; `s2_label_main.php` stamps exactly the six
  registered `label_tuple` fields, values exact on every
  row — 35,300/35,300 rows failed on shape, none on
  values. The fixtures had missed it because the planted
  rows mirrored the reader's shape and no writer→reader
  round-trip existed.
- **The fix and its ruling:** fix package `40500367`
  (the audit now projects each stamp on the six
  registered fields only; extras ignored; wrong value or
  missing field still aborts; fixtures 120 → 124 incl.
  the genuine round-trip case). Claude's ruling
  (`claude-reply-4050036`, committed `7fc06c09`): **FIX
  CONFIRMED** — the fixed analyzer (`ee4daa88…`) runs
  **once** against the existing labels under his §3
  conditions; no re-labeling, no games re-run.
- **The read run:** 2026-10-27 06:57 EDT under §3 (§3
  below): exit 0; `stage2_read.json` + `stage2_read.txt`
  + `l3_manifest.json` written; the labels' sha256 after
  the run equals the pre-run record — the read did not
  touch them.

## 2. The read

The analyzer's output, exactly as printed
(`stage2_read.txt`, sha256 `205500e3…`):

```
=== STAGE 2 L3 READ (primary: horizon 62, draw = 0) ===
PRIMARY (draw = 0): jobs 353; jobs_no_shared_worlds 0 (of 353 jobs); mean paired diff 0.0621; CI [0.0440, 0.0809]
  per-game gain 0.1096 (mean diff x LIVE overturns/game 1.7650 from 353 captured overturns over 200 completed games)
CO-REPORT coreport_draw05: mean diff 0.0494; CI [0.0350, 0.0641] over 353 jobs
CO-REPORT coreport_lifediff: mean diff 0.0451; CI [0.0294, 0.0620] over 353 jobs
UNFINISHED (refusals excluded from shares): pooled share 0.0001 (finished 35296, unfinished 4, refusals 0); fallbacks 7
  abort                       4  [unfinished]
CO-REPORT live rates vs panel: thin-prior 0.0000 (panel 0.0000); overturn rate 0.0694 of contested (panel 0.0917 at draw = 0)
CO-REPORT games outcomes (draw-scored): Stage 2 teacher 87W/41D/72L = 107.5000 pts over 200 games (0.5375/game); fleet reference: teacher 216.0 (173W/86D/141L) vs raw 213.0 (163W/100D/137L), round-7 fleet, 400 paired games
BANDS: PROCEED iff CI lower > 0 AND per-game gain >= +0.05; DOES NOT PROCEED iff mean > 0 with CI including 0 or per-game < +0.05; STOP iff mean <= 0.
VERDICT: PROCEED
```

Reading against the registered bands: PROCEED iff the
game-clustered CI lower bound > 0 **and** per-game gain ≥
+0.05 at the live overturn rate. CI lower = 0.0440 > 0;
per-game gain = 0.1096 ≥ +0.05 → **PROCEED**, as printed.
Neither tripwire is near: per-game gain 0.1096 against
the +0.25 line, mean diff 0.0621 against +0.20.

Co-reports, as printed:

- **Draw = 0.5 read:** mean diff 0.0494, CI [0.0350,
  0.0641] — positive under the old tie price as well,
  smaller than the primary, as the −1 horizon pricing
  would lead one to expect.
- **Life-differential read:** mean diff 0.0451, CI
  [0.0294, 0.0620] — positive under the life-based
  pricing of horizon-ended worlds too. All three
  pricings agree in sign and exclude 0.
- **Coverage:** `jobs_no_shared_worlds` **0 of 353** —
  every job's two candidates share their worlds; no job
  rests on an unpaired comparison.
- **Unfinished / refusals:** pooled unfinished share
  **0.0001** (finished 35,296; unfinished 4 — all class
  `abort`, 2 per arm; refusal classes 0); fallbacks 7,
  as printed. The Stage 0 instrument-validity condition
  (pooled unfinished > 20%) is nowhere near firing.
- **Label tuple audit (fixed):** 35,300 rows, **0 bad** —
  the fixed audit passes on the real driver stamps.
- **Live rates vs the Stage 1 panel:** thin-prior
  **0.0000** live, 0.0000 on the panel — the calibrated
  teacher never fell back to the prior in either
  population. Live overturn rate **0.0694 of contested**
  (353 of 5,087 contested stat rows in completed games)
  against the panel's 0.0917 at draw = 0: the live games
  fired fewer overturns per contested decision than the
  panel states did, and the per-game gain is computed at
  the live rate (1.7650/game), not the panel's.
- **Games outcomes (draw-scored, from the games
  report):** Stage 2 teacher 87W/41D/72L = 107.5 pts over
  200 games (0.5375/game; 87.0 pts at draw = 0, W only).
  The analyzer's fleet reference line (round-7 fleet,
  400 paired games: teacher 216.0 vs raw 213.0) is a
  reference, not this run's comparison — Stage 2 has no
  paired raw arm; its read is the L3 valuation above.

Two absences, stated rather than filled: the analyzer
printed **no L2 sensitivity line** and **no per-game
breakdown table** in this run — its per-game output is
the gain line above. Nothing has been added to its
output here.

*(Amendment, 2026-10-27, on Claude's ruling `7e3fffbf`:
both outputs are tripwire-conditional by registration —
they print only when a tripwire fires. None fired, so
nothing is missing from the read.)*

## 3. The §3 conditions (Claude's ruling, `7fc06c09`)

1. **Pre-run record (before deploying anything):**
   `/home/joe/tcg/r9s2_out/l3/pre_run_record.json`
   (published here) records sha256, line count, and
   mtime for all eight `labels_shard*_p*.jsonl` files,
   `labels_all.jsonl`, `jobs_all.jsonl`,
   `jobs_report.json`, and `games/games_report.json`.
   Expectations met: `labels_all.jsonl` = **35,300
   lines**, sha256
   `f5f1522cddbcf5d9c66d7390d47a5f69400846104d1a3fb37e4952a9c4e2fc90`;
   every label-file mtime predates the abort reference
   (the aborted `stage2_read.txt` mtime,
   2026-10-27T05:37:48-04:00; latest label mtime
   05:37:47.255-04:00). The aborted runner never wrote
   `l3_manifest.json`, so this record is the labels'
   first hash. **Post-run check:** `labels_all.jsonl`
   re-hashed after the read — identical
   (`f5f1522c…`). The labels were untouched.
2. **Aborted read preserved:** the aborted analyzer
   output was copied verbatim to `stage2_read_aborted.txt`
   before the read ran (the read step overwrites
   `stage2_read.txt`); sha256 `712930a5…` for both the
   original and the copy; published here. Its single
   line is the ABORT — the evidence that no read existed
   before the fix.
3. **The read only, once:** the fixed
   `stage2_analyze.py` (`ee4daa88…`) and L3 runner
   (`2d4e0ccd…`) were deployed to
   `/home/joe/tcg/round9_code/` and read back matching;
   the deployed analyzer was verified through the
   runner's own `expect_hash` (the function extracted
   verbatim from the deployed runner, called with the
   runner's own arguments — exit 0). The block executed
   was extracted verbatim from the deployed runner, from
   `# --- the read` through the manifest section, run
   once with the runner's environment
   (`STAGE2_OUT=/home/joe/tcg/r9s2_out`); the whole
   runner was NOT run (it would rebuild jobs and
   re-label). Exit 0; run log at
   `/home/joe/tcg/r9s2_out/l3/read_run.log` on the box.
4. **Publication:** `data/stage2/` (this report's
   companion) carries the driver rows, stat logs, snap
   indexes, labels (gz), jobs, the pre-run record, the
   aborted read text, `stage2_read.json` / `.txt`,
   `l3_manifest.json`, the games report + manifest, the
   launch manifest, and the pre-gate manifest — see
   `data/stage2/MANIFEST.md`. The read, the per-game
   gain, and the rates are recomputable from those rows.

## 4. Correction record

The commit message of `7fc06c09` (the commit carrying
Claude's ruling on the analyzer fix) misstated the reply
file's sha256. The file's true sha256 is
`3f33507da8c7eb6b9e90afc80faa15c817cdb077ca1325f0ddd5f64f4f410a3e`;
the file itself is byte-exact as uploaded. Recorded here
so the hash chain and the record agree.

## 5. Data

All run artifacts are published under
`rounds/round9/data/stage2/` with `MANIFEST.md` (sha256 +
row counts; the labels' raw identity listed there). The
box originals remain in `/home/joe/tcg/r9s2_out/`.

One count difference, stated as counted: the four
published `search_stats_<blk>.jsonl` files total 20,013
lines, while the games report counts 20,009 teacher stat
rows. Both figures are as counted/printed and the files
are byte-exact copies of the box originals; the
difference is not explained at report time and is
visible to any recompute from the published rows.

*(Amendment, 2026-10-27, on Claude's ruling `7e3fffbf`:
explained. The four extra lines are R14 root-canary
refusal records — `{"branch":"M","fallback":"canary",
"missing":{…}}`, written by `SimSearch_RootDecide` when
the missing-card conservation check refuses a root
decision; that decision then goes down the plain bridge
(raw v10) and no teacher row is written. Four refusals in
~20,013 root decisions; the round-7 fleet logged 13
against 37,120 teacher rows — the same order of
magnitude. Immaterial and expected; future reports name
the class instead of carrying an unexplained count.)*
