# Round 9, Stage 2 — analyzer stamp-audit fix

**Status: FOR CLAUDE'S RULING. This fix approves nothing and runs nothing.** The Stage 2 labels are complete on the box and are NOT re-run: on Claude's ruling, the fixed analyzer runs once against the existing label files. The games, the pre-gate, and every other Stage 2 artifact are untouched.

*Why a standalone doc:* the launch package (`stage2-launch-package.md`, incl. its fix-pass amendment) is a closed review unit, confirmed at `2d64302f`. This defect surfaced after the run, at analysis time; it gets its own fix doc and its own ruling, on the `stage1-launch-fix.md` precedent.

---

## 1. The defect

The L3 run completed: **35,300 label rows** (353 jobs × 100) under `/home/joe/tcg/r9s2_out/l3/`. The analyzer then aborted before any read:

```
ABORT: 35300 label rows carry a setting stamp != the registered label tuple
```

**All 35,300 rows failed on stamp SHAPE; none failed on values.** It is a writer/reader contract mismatch between two files in this package:

- **The writer** — `code/s2_label_main.php` stamps every label row with `$SETTING` (its line 112), built from the run's env pins: exactly the six registered fields `{name, hooks, deadline_s, horizon, horizon_value, k}`.
- **The reader** — `code/stage2_analyze.py`'s label-tuple audit built its expectation as the six registered fields **plus a seventh key, `"pinned": 1`**, and projected each row's stamp on those seven keys. No label row carries `pinned`, so every row's projection mismatched.

The seventh key was invented by the analyzer, not the driver. `"pinned"` belongs to the **live** path's stamp contract: `code/search_s2.php`'s tuple resolver writes `"pinned" => 1` into the live teacher's stat-row stamps (its line 896; the unpinned default writes `0`). The analyzer's audit generalized that live-path shape onto the label rows, whose driver never wrote the key. The fix pass's §2.2 work touched this analyzer's neighbor file (`stage2_games_report.py`, which audits the live stamps — where `pinned` genuinely belongs, and which is **not** changed here); the label audit in `stage2_analyze.py` kept the wrong expectation.

**Evidence (three sources, side by side):**

| source | stamp fields |
|---|---|
| `settings_stage2.json` → `label_tuple` | `name` (L3-W50+H), `hooks` 8000, `deadline_s` 180, `horizon` 62, `horizon_value` −1, `k` 50 — six fields |
| `s2_label_main.php` `$SETTING` (every box label row, verified on the rows) | the same six fields, values exact |
| `stage2_analyze.py` audit expectation (before this fix) | the same six **+ `pinned: 1`** |

**Why the fixtures missed it.** Both suites planted the *audit's* shape instead of round-tripping the *writer's*: `fx_stage2_analyze.py` planted label rows as `dict(LT)` **plus `"pinned": 1`** — the reader's expectation, mirrored back at it. `fx_s2_label` proved the driver's rows equal the six-field tuple, but never fed those rows to the analyzer. Each file's contract was tested against itself; the cross-file contract was tested nowhere. (The standing lesson now has a second instance: a fixture must plant the counterparty's real output shape, and a writer/reader pair needs a round-trip case.)

## 2. The fix

`code/stage2_analyze.py`, the label-tuple audit block only — the full change set is `fixtures/stage2_analyze_diff.txt` (it regenerates the fixed file byte-identically from the confirmed file; both sha256s are in its header):

- The audit projects each row's stamp on **the registered `label_tuple` fields only** — the projection keys are taken from `settings["label_tuple"]` itself, so the audit can never again demand a field the registration doesn't carry.
- A row passes iff those fields equal the registered tuple exactly. **Extra keys in a stamp are ignored. A wrong value in any registered field, or a missing field, still aborts** with the same message and count behavior (`ABORT: N label rows carry a setting stamp != the registered label tuple`, exit 2), before any read.
- Nothing else in the analyzer changes: the world-count guard, the reads, the co-reports, the bands and tripwires are byte-identical. The analyzer contains **no** stamp audit of games-report rows (the games report is consumed for its rates only), so there is no second site of this defect in the file. `stage2_games_report.py`'s own audit reads the live stamps, which do carry `pinned` — correct there, untouched.

`code/run_stage2_l3.sh` changes only its `stage2_analyze.py` pin literal (machine-copied to the new hash below), so the deployed analyzer is the fixed one.

## 3. Fixtures — the counterparty's shape, plus a round-trip

Full suite re-run; transcript regenerated at `fixtures/fx_s2_outputs.txt`. **124 checks, 7 suites, ALL PASS** (was 120).

- **`fx_stage2_analyze` 16 → 18.** The planted population now carries the **real driver shape** (exactly the six fields) and the read completes with every pre-existing hand-computed expectation unchanged (primary 0.375, draw05 0.40625, lifediff 0.4375, LOGO [0.0, 0.75], sensitivity 0.364583…, tripwire ordering, negated STOP, no-shared-world). The pre-existing wrong-value case (k=25) still aborts — now planted on the real shape. Two new cases: **extra keys ignored** (`pinned: 1` on every row — the shape this fixture planted before the fix — passes, read unchanged) and **missing field aborts** (one row without `k`, exit 2).
- **`fx_s2_label` 14 → 16.** New **round-trip** case: the genuine rows the real `s2_label_main.php` produced in the harness (200 rows, the driver's own stamps) are fed unchanged through `stage2_analyze.py`; the analyzer completes (exit 0) and its `label_tuple_audit` reads `{rows: 200, bad: 0}`. The writer/reader contract is now proven on the writer's actual output.

## 4. Hashes (machine-copied)

| file | sha256 |
|---|---|
| code/stage2_analyze.py | `ee4daa887cdec3e11118adb75ddd184aa86dbcc0ede73648ed6154394c32d0ac` |
| code/run_stage2_l3.sh | `2d4e0ccd5864c7f00cfdf4437af004443d72c5a815ccc7f3d86bde5400e8e414` |
| fixtures/stage2_analyze_diff.txt | `3a7367cb396d34c98a37653113579bbd8852e08a6266d9af3baa1ae88d51b0b4` |
| fixtures/fx_stage2_analyze.py | `aae12dd1451f50b3000ecf4d441e8f0986cbd3c169fdffa53dbf8c40d6c79372` |
| fixtures/fx_s2_label/check_fx_s2_label.py | `96fcae397f1d1fdf6d07b2dee0ca883e8b30d46051e078b02ee6685d5145f8d6` |
| fixtures/fx_s2_outputs.txt | *(regenerated from the passing run; hash in the fix commit message)* |

Unchanged and still pinned: `search_s2.php` `85490e8e…`, `s2_label_main.php` `c7a76af4…`, `settings_stage2.json` `2a1634cc…`, `build_s2_jobs.py` `b91f3a6c…`, `stage2_games_report.py` `62b5b319…`, `pregate_check.py` `bc5327d3…`, runners `run_stage2_pregate.sh` `581f47aa…`, `run_stage2_games.sh` `8bb176d0…`. The superseded analyzer hash `9b1a0677…` survives only in this doc's §1 and in the diff fixture's header, as the before-state record.

## 5. Scope

The labels on the box are final and untouched — no re-labeling, no games re-run. The only box action this fix contemplates, after Claude's ruling and Joe's go, is deploying the fixed `stage2_analyze.py` (+ the L3 runner's pin) and running the analyzer once against the existing `/home/joe/tcg/r9s2_out/l3/` label files, producing the Stage 2 read for the report. **This doc approves and launches nothing.**
