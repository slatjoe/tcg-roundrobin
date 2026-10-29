# Claude — confirmation check on the Step 0 probe's fifth fix pass

**Reviewed commit:** 28c20655f542b44deb06a7761b2d6cab7c1440ae (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-9dae0e2.md` hashes to `1a43d45c…caaa9e`, the value I gave Joe.

**Verdict: the three items are CONFIRMED, but the recovery is ON HOLD.** Checking the published evidence surfaced an instrument defect that predates round 10: **the rollout horizon does not stop worlds at the instrument's cap** (§2). As designed, the probe read would price wins the real game can't reach, and the ten recovered jobs are where that matters most. The recovery's labeling, analysis and report don't run until §3 is registered.

## 1. The three items: verified independently from the published files

- **Item 1, the evidence.**
  - All 28 hashed files in `data/step0/MANIFEST.md` match.
  - `jobs_all.jsonl` lines **282–291** carry the bare `Infinity`, all in `jobs_shard0_p2.jsonl` (115 lines, 10 of them `Infinity`). Its `.err` says `s2 label jobs=105`. The other seven shards loaded every line.
  - `labels_all` has **63,600** rows, and `label_read.txt` is the world-count abort.
  - **The suite runs from the repo: 126 checks, ALL PASS**, with the transcript identical apart from the php binary path.
- **Item 2, eval completeness: clean, by my own code.** There are 5,253 eval job lines and 5,253 states with rows, 0 missing, 0 (job, candidate) pairs ≠ 25 and 0 extra. 381,587 worlds finished and 38 didn't. The eval's silent loader dropped nothing. `eval_completeness.py` is wired as recovery step 0.
- **Item 3, the influence script.** It's built and fixtured, and the hold rule is implemented as I specified. The state inspection matches the builder's preview:
  - game 540261752 (seed 24070, seat 2) was a **capped draw at turn 63**, life 19 against 8;
  - all ten snaps (live turns 45, 47, …, 63) are **the same choice**: candidates {0 `chum_friendly_first_mate` (Ally), 7 `loot_the_hold`, 9 `prismatic_leyline`}, prior {1.0, 0.0, 0.0};
  - the prior's and `loot`'s worlds: 248 horizon draws and 2 losses. `prismatic_leyline`'s: **250 of 250 outright wins**.

## 2. The finding: the horizon overshoots the cap

The world rows record the turn each rollout ended (`turns` = `currentTurn` at exit). Across every published label set and the probe's eval:

| Rows | Horizon worlds: end turn min / median / max | Decisive worlds ending after turn 63 |
|---|---|---|
| Probe eval (381,625) | 62 / about 96 / 268 | 9,379 of 314,030 (3.0%) |
| Probe labels | 62 / **95** / 266 | 1,532 of 47,378 (3.2%) |
| Round-9 Stage 3 labels | 62 / **93** / 268 | 676 of 48,019 (1.4%) |
| Round-9 Stage 2 labels | 62 / **93** / 268 | 532 of 27,300 (1.9%) |

**Live games never get there.** In the published Stage 3 and probe-capture driver rows, **691 decisive games all end by turn 61**, and capped games end at turns 62–71 as draws. So a rollout that's decisive after the trigger is pricing an outcome the real game scores as a draw. Horizon-flagged worlds stop, at the median, about 30 turns past 62.

**The likely mechanism, for the builder to confirm:** in `SimLabel_RunRollout` the check `currentTurn >= horizon` runs **once per outer iteration**, and each iteration runs up to 20 `PuzzleFinishStep()` calls. Late-game passing turns can carry many turns past 62 between checks.

**What it does to the ten recovered jobs.** These are the `prismatic_leyline` worlds that ended decisively by turn 61, out of 25 each:

| Snap | t64 | t65 | t66 | t67–t73 |
|---|---|---|---|---|
| Wins by turn 61 | **22** | **15** | 1 | **0 each** |

- t64 and t65 look like a genuine catch: playing the leyline instead of re-activating the ally wins.
- **t67–t73 are entirely post-cap wins.** t73 is a decision at live turn 63, in a game already past its trigger, where no win is reachable.
- Under the as-run scoring, these seven would carry about +2.0 per world into the threshold lever at weight 2. That's exactly the single-game domination §2.3 of my last check was written to catch, and it would have caught it as a symptom without naming the cause.

**What it does to round 9, recomputed from the published labels.** "Cap-aligned" means a win counts only if the world ended by turn 61; otherwise it scores 0 at draw = 0.

| Read | As run | Cap-aligned |
|---|---|---|
| Stage 2 L3 primary | +0.0621 [0.0446, 0.0808] | **+0.0565** [0.0406, 0.0737] |
| Stage 3 L3 primary | +0.0417 [0.0318, 0.0529] | **+0.0417** [0.0320, 0.0527] |

- **Round 9's conclusions stand.** Both replicate within noise.
- **Stage 3's verdict is unaffected:** DOES NOT CONVERT was read from real games.
- **The calibration finding is softer than I stated it.** "The horizon is the instrument's own draw trigger" was true of the parameter but not of the implementation. The horizon still did its job of ending stalled rollouts, just about 30 turns late on median.
- **I missed this in round 9.** I verified the check's presence and its parameter, never where the worlds actually stopped. The `turns` field was in every row I recomputed from.

## 3. Required before the probe read (a §14 horizon-alignment package)

1. **Confirm the mechanism** in code. Add a fixture rollout from a late, stalling state showing the as-built check lets a world pass turn 62.
2. **Register the cap-aligned scoring before any probe read is computed.**
   - **The rule:** a world counts as decisive only if it ended by **turn 61**, the live instrument's last decisive turn, to be confirmed from the engine's trigger semantics. Every other finished world is a horizon draw: −1 for the search statistic, 0 in the draw = 0 read.
   - **Apply it to the eval:** recompute every state's z from the published eval rows, and hence the classes and rates.
   - **Apply it to the labels.**
   - **Supplementary labeling:** states that newly qualify under cap-aligned z get labeled under a fresh, disjoint family, as in the recovery. States that drop out are excluded and listed.
3. **The registered decision rule applies to the cap-aligned read**, which is the registered intent: horizon = instrument cap. The as-run read prints beside it, labeled. This is settled now, before anything is read. The influence prints and the hold rule apply to the cap-aligned read.
4. **The code fix, for every future build and eval:** check the horizon after **each** `PuzzleFinishStep()`, plus a fixture showing no world exits decisive after turn 61 or flagged horizon after turn 62. It's required before any Step 1 build. It doesn't apply to the existing rows, which step 2 rescores.
5. **Round-9 co-report:** publish the cap-aligned Stage 2 and Stage 3 L3 reads above with committed code, as an addendum to round 9's record. No verdict changes.

The recovery script's extraction, labeling and merge of the ten jobs can be kept as one step of the §14 package. Its analysis and report steps are replaced by the cap-aligned read.

**Scope:** this confirms the fifth fix pass's three items at 28c20655. It **holds** `run_probe_recovery.sh`'s execution, Joe's earlier approval notwithstanding, until a §14 package registering the cap-aligned scoring is reviewed. No run is approved.
