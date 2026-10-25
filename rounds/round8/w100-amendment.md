# Round 8 — W=100 amendment package (staged, not yet committed)

**Authority:** `claude-reply-597d181.md` §3, Option 1 — widen
the labeler to **W = 100 worlds per candidate** before the
corpus, gated on a V1 check at W=100 against the registered
threshold **V1-ov ≥ 0.50**. Joe chose Option 1 (2026-10-25
14:46 EDT). The decision rule is otherwise unchanged: the same
candidate set (the job's registered `selected`), pair `va`,
the 20-finished-worlds floor, and the 1.5 × SE overturn test.
Four files change (one of them new); unified diffs for all
four are in `fixtures/` (`distill_label_main_diff.txt`,
`label_reduce_diff.txt`, `run_label_corpus_diff.txt`,
`run_w_check_diff.txt` — the last against /dev/null, the file
is new).

## How W flowed before this amendment (file/line evidence)

- **`distill_label_main.php`** (was `4f1de80a…`): W existed
  only as a literal. Old line 64: `$W = 25;`, passed into the
  rollout config at old line 78 (`"W" => $W`). The only guard
  was old lines 56–61: a `LABEL_W` env set to anything but 25
  aborted — a prohibition, not a parameter; unset was fine.
  **Jobs carried no W** (the pilot's published job rows,
  `data/pilot/jobs_v1a_p1.jsonl`, have keys snap_dir, snap,
  game, player, branch, turn, cands, selected, priors,
  prior_pick — no W), and **the raw rows the labeler wrote
  recorded no W** (old lines 113–122 stamp prior_pick,
  selected, game, branch, player, turn, seed_base — nothing
  else).
- **`label_reduce.py`** (was `e2244fbb…`): never mentioned W
  or 25 anywhere. Its only constants are the registered
  20-finished-worlds floors. Labels carried no W.
- **The runners:** `run_pilot.sh` phase 5 invoked the labeler
  with no `LABEL_W` and jobs built by `pilot_prep.py` without
  W; `run_label_corpus.sh` (was `4983f70d…`) built its jobs
  in-script with no W field and set no `LABEL_W`.

So a label set's width was knowable only from which runner
produced it — exactly the silent-drift hazard the original
pin existed to prevent, and the thing this amendment makes
impossible: after it, the width is pinned by the run,
asserted on every job, and recorded on every raw and label
row.

## The changes

### 1. `distill_label_main.php` — `4f1de80a…` → `acf5f4bb…`

- **Pin** (new lines 64–75): `$W` = the `LABEL_W` env when
  set (validated as a positive integer; `"0100"`, `"abc"`,
  `0` abort), else 25, the registered teacher's k. This
  preserves the old tolerance for an unset env while making
  any set value a legal pin — the pin is now a parameter,
  not a prohibition.
- **Per-job assertion** (new lines 81–95): after the jobs
  load and before any labeling, every job must carry a `W`
  equal to the pin; a mismatch or a missing W aborts with
  exit 2, naming the job index, the snap, and both widths.
- **Rows record W** (new line 149): `$r["W"] = $W;` beside
  the existing stamps.
- Nothing else in the file moves: candidate set from the
  job's `selected`, pair `va`, seed arithmetic, split-cands
  mode, and the output loop are untouched (`php -l` clean;
  diff 75 lines, 3 hunks).

### 2. `label_reduce.py` — `e2244fbb…` → `25a5f4cc…`

The reduce previously hard-coded nothing about W, so the
change is only what carrying W through requires:

- While reading the raw rows (new lines 77–91): every row
  must carry an integer `W`; the first row sets the reduce's
  W and any differing row **aborts** (`mixed W in raw rows`)
  — one reduce covers one instrument.
- `"W"` is stamped on every label row (line 139) and every
  thin row (line 115), and into the counts dict (line 99).
- The Decide arithmetic is byte-identical; the 20-world
  floors are the registered floor, not W, and do not move
  (diff 73 lines; `py_compile` clean).

### 3. `run_label_corpus.sh` — `4983f70d…` → `a46dae36…`

The corpus label path runs at the amendment's width by the
same pin discipline:

- `LABEL_W=${LABEL_W:-100}` (line 47) — the run's pin;
  `LABEL_W=25` reproduces the pilot-era instrument, but only
  when set explicitly.
- The job builder takes it as an argument and stamps
  `"W": W` on every job (lines 66, 84); the labeler
  invocation passes `LABEL_W="$LABEL_W"` (line 165);
  `label_manifest.json` records `"W"` (line 189).
- Nothing else changes: capture-side untouched, sharding
  and seed bases (999001 + shard × 1000003) untouched. The
  corpus itself does **not** run in this package (diff 67
  lines; `bash -n` clean; all four embedded Python blocks
  compile).

### 4. `run_w_check.sh` — NEW, `9d982a49…` (282 lines)

The V1 check as its own runner, not a `PILOT_RESUME` mode.
Justification: the check's shape is the **corpus labeler's**,
not the pilot's — the brief requires sharding across 4
native-tree copies exactly as the corpus labeler does, while
`run_pilot.sh` labels sequentially in a single native tree
and its structure (resume-mode branch table, pilot OUT
layout, phase gates) has no place to hold 4-tree sharding
without importing a second runner into it. A separate script
modeled line-for-line on `run_label_corpus.sh`'s containment,
server, sharding and shard functions keeps both runners
auditable against the shape they claim.

What it does (and nothing else):

- **States:** the pilot's 547 V1 capture states, from the
  very job file the pilot used (`$V1_JOBS`, default
  `/tmp/distill_pilot_resume/v1_jobs.jsonl`; count asserted
  == 547; a source job already carrying W aborts), each
  stamped `"W": 100`.
- **Two runs:** A at world-seed base **555001**, B at
  **777001** — the pilot V1's registered bases — each sharded
  round-robin (job i → shard i % 4) over 4 copies of the
  native tree (`/tmp/distilltree_wcheck$s`), per-player
  groups against that seat's production server, one label
  process per tree, a (C) sweeper per tree, G8 first. The
  per-shard seed offset is the corpus runner's pattern
  applied to these bases (shard s at base + s × 1000003);
  within a file, job ji takes seedBase + ji × 100003, the
  labeler's unchanged convention. `LABEL_W=100` is passed to
  every labeler invocation, so the pin, the jobs, and the
  rows must all agree or the run aborts.
- **Grouped mode** (no `DISTILL_SPLIT_CANDS` — the corpus
  shape; the pilot's deadline accounting is not part of this
  check). Per-job timings are parsed from the labelers'
  err-log `done … secs=` lines.
- **The read:** `label_reduce.py` per run (asserts W
  uniformity from the rows), then V1-ov / V1-conf computed
  with **pilot_report.py's own arithmetic** — `wilson()` and
  `rate_line()` are imported from `pilot_report.py`, and the
  counting mirrors its V1 block (both-labeled states; A's
  overturns as the denominator for V1-ov, requiring B's
  overturn flag AND teacher pick to match; confirmations
  likewise). The finisher additionally asserts every emitted
  label row in both sets carries W == 100. Timing stats use
  pilot_report's COST formula (mean / p95 =
  secs[ceil(.95n)−1] / max over sorted secs).
- **Outputs** in its own OUT (`/tmp/distill_wcheck`):
  `wcheck_report.json` + `wcheck_report.txt` carrying
  V1-ov, V1-conf (counts + Wilson intervals), thin counts
  per run, per-job timing mean/p95/max, and the threshold
  read as the last line.
- **Registered threshold (ruling §3):** V1-ov ≥ 0.50 reads
  `PASS — the corpus may run at W=100`; below reads `STOP —
  reported for decision; the corpus does not run at W=100`.
  The threshold is a report outcome, not a runner failure: a
  completed check exits 0 either way, with the verdict
  printed in the report and the run log.
- Plays **no games**; reads the capture snapshots in place.
  Header carries the standard gate: launches only on
  Claude's confirmation of this amendment commit AND Joe's
  go for the check (`bash -n` clean; its three embedded
  Python blocks compile).

**One consequence, stated plainly:** `run_pilot.sh`'s phase-5
label calls would now abort at the pin — its jobs carry no W
and it sets no `LABEL_W`. That is the discipline working, not
a regression: the pilot is complete, its label sets are
published (`data/pilot/`), and it is not re-run. Any future
V1-style labeling lives in `run_w_check.sh`. `run_pilot.sh`
itself is unchanged by this package.

## Verification — the smoke (box, 2026-10-25)

Amended files deployed to a scratch dir on the box and
hash-verified there (`distill_label_main.php` `acf5f4bb…`,
`label_reduce.py` `25a5f4cc…`; `php -l` clean). One pilot
capture state — the pilot V1 job file's first job, snap
`286996099_t8`, selected [0, 1, 3], prior 0 — labeled in a
fresh copy of the native tree against the production server,
seed base 555001. Artifacts in `/tmp/w100_smoke/` on the box;
SHM segments 126 before, 126 after (no leak).

**Positive** (job stamped W=100, `LABEL_W=100`), verbatim:

```
distill label jobs=1 W=100
done 286996099_t8 rows=300 secs=22.3
DISTILL-LABEL-DONE
raw rows: 300
rows per candidate: {0: 100, 1: 100, 3: 100}
finished per candidate: {0: 100, 1: 100, 3: 100}
W values on raw rows: {100}
```

300 rows = 3 candidates × 100 worlds (at W=25 this job emits
75), every world finished, every row recording W=100. The
amended reduce on those rows, verbatim (counts, then the
label row):

```
{"W": 100, "jobs": 1, "no_rows": 0, "prior_not_selected": 0,
 "thin": 0, "confirm": 0, "confirm_paired_thin": 0,
 "overturn": 0, "no_overturn_tested": 1, "labels": 1}
{"state_id": "286996099_t8", ... "W": 100, ...
 "candidates": [0, 1, 3], "n_worlds": {"0": 100, "1": 100, "3": 100},
 "means": {"0": -0.48, "1": -0.48, "3": -0.36}, ...
 "paired_n": 100, "mean_diff": 0.12, "se_diff": 0.0844...,
 "teacher_pick": 0, "overturn": 0}
```

(One state, disclosed as a smoke only: candidate 3's mean
beats the prior's, but 0.12 < 1.5 × 0.0844, so the label
confirms — no overturn is claimed from it.)

**Negative A** (same job stamped W=100, run under
`LABEL_W=25`) — exit 2, no rows written, verbatim:

```
ABORT: job 0 (snap 286996099_t8) carries W=100 - the run's pinned W is 25 (LABEL_W)
```

**Negative B** (the same job with **no** W stamp, under
`LABEL_W=100`) — exit 2, no rows written, verbatim:

```
ABORT: job 0 (snap 286996099_t8) carries W=<missing> - the run's pinned W is 100 (LABEL_W)
```

## What remains

- **Claude's confirmation of this code commit** (the ruling
  approves the direction and the threshold; the
  implementation comes back for his confirmation, as with
  the equivalence fix).
- Then **the V1 check launches on Joe's go** (his Option-1
  choice is recorded): `run_w_check.sh`, ~1,094 jobs at
  ~17–22 s — order 1.3 h on the 4 trees per the ruling's
  estimate and the smoke's single job.
- **The corpus** stays gated on the check's PASS and on
  Claude's read of it, with the **option-(a)
  one-capture-per-seed declaration** still owed in the
  corpus launch manifest (the pilot capture of seeds
  10001–10020 is kept; its W=25 run-A labels are superseded
  and those states are relabeled at W=100 with the rest of
  the corpus; `t1_build_data.py` asserts one game id per
  (stream, seed)).
- **The sign-test fix** (analyze_distill_gate.py) is still
  owed before the gate. The claim the corpus would serve is
  restated per the ruling: the student distills a
  wider-search version of the gated teacher; the gate, bands
  and arms are unchanged, the +0.2525 stays the historical
  reference, and the +0.25 impeachment bound stays as a
  sanity check.
