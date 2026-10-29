# Claude — confirmation check on the Step 0 probe's fourth fix pass

**Reviewed commit:** 9dae0e2cf1905f76cf840849d4982b640565502b (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the launch record at 4526cc9; attempts 1–3 are recorded as my §3 asked. The committed `claude-reply-5ce1f58.md` hashes to `8589feb9…5ebc211b`, the value I gave Joe.

**Verdict: NOT YET. The recovery doesn't run until three items are done** (§2).
- **The diagnosis and both code fixes are right as far as I can check them** (§1).
- **But the evidence they rest on isn't in the repo,** so the fixture suite fails from the repo.
- **The eval phase used the same silent loader,** and nothing has checked it.
- **The ten recovered jobs could dominate the read** in a way that needs a registered look before anyone reads it.

## 1. What checks out

- **The loader fix.** `s2_label_main.php`'s change is confined to the load block. It counts non-empty lines, aborts by line number on any undecodable line, and asserts that the count matches. The pin is updated (`1c1dfd9f…`).
- **The writer fix.** `build_probe_jobs.py` writes the finite sentinel 999.0 with `z_nonfinite`, under `allow_nan=False` throughout. The sentinel bands where +inf did: class (a), in the tail.
- **The seed-shift analysis.** I agree: a seed base only has to be unique within its family and paired across a job's candidates (CRN). The compressed indices keep both. The round-9 design already shared bases across a shard's two player files.
- **The recovery's seed family.** At 970,055,001 it's interval-disjoint from every family as tabulated.
- **The recovery script's design** is right: extract the 10 by snap, rewrite them in the fixed shape, label once under the fixed loader, pre-check 50 rows per (snap, candidate), merge, then analyze and report verbatim, with a manifest and the disclosure.

## 2. Required before the recovery runs

### 2.1 Publish the attempt-3 evidence; the suite must pass from the repo

`fx_label_loader.py` N9/N10 read `rounds/round10/data/step0/jobs_all.jsonl`, but no `data/step0/` exists at 9dae0e2. Run here, the suite **fails** (FileNotFoundError, 107 of 109). The doc's evidence lives only on the box, so I can't verify any of it:
- the 10 lines with `Infinity`;
- 105 of 115 loaded;
- 63,600 label rows;
- the analyzer's abort line.

**Required:** commit attempt 3's pre-recovery artifacts under `data/step0/`, with a MANIFEST of sha256s and row counts:
- `jobs_all.jsonl` and the jobs shard files;
- the eval jobs file(s) and the eval world rows (gz if large);
- `probe_eval` states/output;
- `labels_all.jsonl.gz`;
- every `label_shard*_p*.err`;
- the aborted `label_read.txt`;
- the capture driver rows and snap index for game 540261752.

The suite must then pass from the repo alone at the reviewed sha. The standing rule hasn't changed: a fixture may read only what's published.

### 2.2 The eval phase ran on the same silent loader

`s1_eval_main.php` line 97 is the identical round-9 pattern: `json_decode(...); if (is_array($j)) $jobs[] = $j;`. `probe_eval_analyze.py` has no jobs-to-states count guard. If any eval job line failed to decode, that state vanished from the **denominators of every tail rate** without a trace, and nothing downstream would have aborted.

**Required:**
- **Before the recovery's analyze step,** assert from the published files that every eval job produced world rows for every one of its selected candidates. Print the counts: eval job lines, states with rows, and missing states (expected 0).
- The recovery script gains this assertion, run before the label merge. A non-zero missing count stops the recovery and comes back to review.
- Give `s1_eval_main.php` the same loud loader in the next package that runs an eval. It's not needed now if the count is clean.

### 2.3 A registered influence read for the ten recovered jobs, before anyone reads the gain

**What the ten jobs are:** all ten come from **one game** (540261752), **consecutive** sampled uncontested decisions t64–t73, each with z = +∞ and mean_diff = +2.0. At k = 25, the prior pick lost every world and the alternative won every one.

**Why that matters:** at the Horvitz–Thompson weight of 2, ten jobs at a labeled diff near 1 would contribute up to about 10 × 2 × 1 / 90 ≈ **0.2 per game** to the threshold lever. That's more than the whole lever was speculated to be worth, and from one game.

**What could explain it:**
- It may be a real catch. For example, raw v10 drifting toward the turn-62 cap, where the eval prices a draw at −1, while an alternative actually closes the game.
- It may be an instrument artifact, a state where one candidate's rollouts fail in a way that's scored as a loss.

That has to be **looked at and registered before the read is seen**. It changes no rule.

**Required co-reports.** The recovery runs them after the report, and they print in the published outputs:
1. **State inspection of game 540261752:**
   - the driver row's actual outcome (W/D/L, capped or not, turn count);
   - for each of the 10 snaps, the turn, prior pick against search pick (card ids), top prior;
   - the eval's per-candidate finished, unfinished and error counts;
   - how many of the prior pick's 25 worlds were horizon draws priced −1, against outright losses.
2. **Leave-one-game-out influence for each lever's per-game gain:**
   - the LOGO range;
   - the largest single-game share of the gain, and which game;
   - the gain and its lower bound with that game excluded.
3. **A hold rule (process, not a change to the decision rule):** if a lever is BUILDABLE under the registered rule but its gain lower bound is ≤ 0 with any single game excluded, the report prints "**buildable, single-game dependent**". The recommendation then goes to review before any Step 1 package is drafted.

The registered decision rule and its numbers are unchanged. These prints only make what it rests on visible.

## 3. Then

The three items come back in one commit: the published data and MANIFEST, the eval-completeness assertion, and the influence script and prints. I'll run the suite from the repo and check the evidence against the doc's claims. Then the recovery runs on Joe's go, once, under §12 as amended.

**Scope:** this accepts the defect's diagnosis and both code fixes in substance at 9dae0e2c, and requests the three §2 items. It approves no execution of `run_probe_recovery.sh` yet.
