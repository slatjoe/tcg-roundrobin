# Round 7 — stage-3 instrument-alignment registration (FINAL, as amended)

**Parent:** c0ec3f112233bdb7ea6890182333c57ef9434a0e (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-b876b3f.md` §5 (the implementing commit's contents), §1.4 (the read's conditions), §3.3 (the worker-cap withdrawal), §4 (the formal-gate batch form and partial-completion rule).
**Status: IMPLEMENTING COMMIT for Claude's CONFIRMATION check** (claude-reply-b876b3f §5: the hashes, the launcher diff, the gate script's text, the amended sections). This document is the amended registration of record; it supersedes `stage3-alignment.md` (33a59813, the draft) where the two differ. **Nothing launches on this commit.** On Claude's confirmation at this commit's sha, stage 3 stands approved and `GRAVY_STAGE2_CLEARED` may be set — **it is not set by this package**. Stage 3 then still requires Joe's per-stage go in chat.
**What changed against the draft, in one list:** (1) draft §3.3(a) — capping the rollout workers — is **withdrawn** (§3.3 below); the launcher in this commit carries **no worker-cap line**, only its trainer-hash guard. (2) The formal gates run in the **fixed batch form** (eight invocations of 50) with a **registered partial-completion rule** (§4.1, §4.3). (3) The draw-score interval is named correctly: the **normal approximation on the per-game score mean**; Wilson is used only for capped shares (§4.2). (4) **R\* = 0.51213 is recorded** (§4.2). (5) The **registry merge of the 373 re-gate ids is executed** and recorded (§7), discharging §1.4 condition 1 of the reply.

---

## 1. Contents of this commit (mapped to claude-reply-b876b3f §5)

| §5 item | This commit |
|---|---|
| 1. `code/patch_trainer_launch.py`, aligned | The aligned version (changes 1–5), sha256 `8826e39975bad516ed23af3d9257a202ba4374b420d40c532c8db466ee36cd27`; applied to pristine `trainer_v4.py` (`8fd52d829acee231b5f066adba879178593de3ffc1a689ca224948186b6a837f`) it produces the launch copy `a48c4abc94f081397bacbdbb09cf04ffdd3c336b08b4eb2eeb51ca18c501a80a` — re-verified in scratch for this package (§V) |
| 2. `code/gravy_ppo_launch.sh`, guard only, no worker-cap line | Guard `dc95d81a` → `a48c4abc`; diff against the previous committed file (`6b02d3f1cac2780e937c7497040dcd2c1a72635078d30dcbdc45686bbf8e8d59`) is the guard change only (§V); new sha256 `53d20b824eb414ed77a3a4796c1dc7f00f66a0c9150673178cefc6d4a4715210` |
| 3. The formal-gate script, §4 form, full text + sha256 | `code/run_formal_gate.sh` (new), sha256 `421934d85bd34c047aa6143ce418bebb5ec9cade33c728462076211b8249c461`; pooling tail dry-checked against the re-gate's totals (§V) |
| 4. The registration text, amended | This document (§§2–6) |
| 5. The registry merge record (§1.4.1) | §7 of this document (merge executed 2026-10-22, before this commit) |

---

## 2. Spot gates — aligned (as drafted, accepted at claude-reply-b876b3f §2)

### 2.1 The current call (pristine `rl/trainer_v4.py`, sha256 `8fd52d82…`, `run_spot_gate` :262–303)

The call passes `--max-turns` **explicitly** (the correction to claude-reply-2e5e4c5 §3's description, accepted in the reply): per deck half, 25 games each, 50 total, seat-balanced via `--learner-deck a`/`b`, with `"--max-turns", "60"`, no `env=` on the subprocess (so `TCG_MAX_DECISIONS` rides unstated at the engine default 3,000), and the read `wr = wins / played` — capped games in the denominator only, scoring as non-wins. `run_spot_gate` is the trainer's only `eval.py` call.

### 2.2 The diff — launch copy only, via `patch_trainer_launch.py` changes 4–5

Five anchor-asserted replacements (each occurring exactly once in the pristine trainer), riding the existing patch mechanism alongside the already-approved changes 1–3:

- `"--max-turns", "60"` → `"--max-turns", "87"` (parameter 87, trigger 62);
- the subprocess gains `env={**os.environ, "TCG_MAX_DECISIONS": "3000"}`;
- `wins = played = 0` → `wins = played = capped_total = 0`, and the summary accumulation gains `capped_total += int(summ.get("capped_games", 0))`;
- the read becomes draw-scored: `wr = (wins + 0.5 * capped_total) / played`, against the **unchanged 0.30 floor** (`--spot-floor` default);
- (change 5, the heartbeat tally, is §3.2 below.)

The "inconclusive" branch (`played < 40`) is unchanged. Timeout arithmetic (reply §2): each half is 25 games, inner budget 255 s against ~105 s at 4.2 s/game; the outer subprocess timeout of 1500 s is unchanged. The full replacement text and the resulting unified diff hunks are in the draft (`stage3-alignment.md` §2.2) and in the committed patch script itself, which is the operative artifact.

### 2.3 Logic test (synthetic summaries)

| Input summary | Non-win read (old) | Draw-scored read (aligned) |
|---|---|---|
| Stage-2 anchor gate, half A: 200 games, 28 wins, 142 capped | 28/200 = **0.1400** | (28 + 0.5×142)/200 = **0.4950** |
| Fai-like: 165 games, 69 wins, 0 capped | 69/165 = **0.4182** | **0.4182** — identical |

Where nothing caps, the alignment changes nothing.

---

## 3. Heartbeat — findings, the tally aligned, the worker caps WITHDRAWN

### 3.1 What the workers actually run under (from the code; accepted at reply §3.1)

- No file in the path sets a cap: `TCG_MAX_TURNS` / `TCG_MAX_DECISIONS` appear nowhere in `rl/run_workers.sh`, `trainer_v4.py`, or `rl/rollout_server.py`; the launcher exports only `SIM` and passes no cap variables; the per-game php invocation sets only `TCG_POLICY_SOCK`.
- Worker games therefore run at the **engine defaults** (`play_game.php:332` / `:344`): turn **parameter 750, trigger 725**; **3,000 decisions**. For turns the workers are effectively uncapped.
- The tally defect: in `finalize_games()` (pristine :438), each completed game contributes `won = 1.0 if (winner == seat and not capped) else 0.0` to the trailing-150 heartbeat window (and the same value to `recent_results`). **A capped game enters as 0.0 — a loss.** On Gravy, that alone could halt PPO on intrinsic draws.

### 3.2 The tally change — accepted, in the launch copy only (patch change 5)

```python
won = (0.5 if capped else
       1.0 if winner == seat else 0.0)
```

One anchor-asserted replacement inside the patched launch copy; the pristine trainer is never edited. `recent_results` shares the same value; there is no second tally. The window (150), the arming thresholds (100 heuristic games / 50 window entries), and the floor (0.30) are unchanged. The episode-reward path is **not** touched (§10 states what it pays, as the reply's "Not reviewed" section asks). Logic test on a synthetic 150-entry window (30W / 80L / 40 capped): old tally mean **0.2000** (a halt) → aligned **0.3333**; an all-decided window (45W / 105L) reads **0.3000 under both**.

### 3.3 (a) WITHDRAWN — the workers stay at the engine defaults

The draft's §3.3(a) (adding `TCG_MAX_TURNS=87 TCG_MAX_DECISIONS=3000` to the workers invocation in `gravy_ppo_launch.sh`) is **withdrawn**, per claude-reply-b876b3f §3.3, which owns the error: the "same caps" wording in claude-reply-2e5e4c5 §3.2 was written without seeing that the heartbeat has no games of its own — its stream **is** the training stream, so capping the workers is a stage-3 design change, not an instrument alignment. The reply's three reasons, recorded: (1) capping rollouts at trigger 62 makes stalling cheap in training — a dragged rollout ends as a capped episode at turn 62 instead of at the default caps (median turn ~142 at the decision cap), the stop package's stall mechanism made cheaper inside PPO, with only a report-only stall check at the formal gates; (2) it would separate the training stream from the KL probe and the stage-1 corpora, both generated under the default caps; (3) it buys almost nothing for the heartbeat, which is a collapse alarm over a sampling-temperature policy, not the gate instrument.

**The launcher in this commit therefore carries no worker-cap line; the workers invocation is byte-identical to the previously committed launcher** (§V diff). The workers stay at parameter 750 / trigger 725 / 3,000 decisions.

**The residual difference, stated** (reply §3.3, required): with the tally draw-scored but the workers uncapped-for-turns, the only remaining difference between the heartbeat's stream and the gate instrument is that decided games ending past turn 62 count as decided rather than drawn. On the mirror's records that is **29 of 1,921 decided games = 1.5%**. Under the defaults, the games that do cap are the pass-forever population — exactly what draw-scoring is meant for.

**Rollout capped-share report (new, report-only):** the stage-3 report **reports the rollout stream's capped share per accepted version**, computed after the run from the workers' `games_w*.jsonl` (`capped` field) and `games_meta.jsonl` — no code change. It is the training-side view of the §4.4 stall diagnostic: reported, never a gate condition.

---

## 4. C4 formal gates — fixed batch form, partial-completion rule, R\* recorded

### 4.1 Form (claude-reply-b876b3f §4, replacing the draft's two-of-200)

Each formal gate is run by **`code/run_formal_gate.sh`** (committed with this package, full text in the repo), invoked with the candidate checkpoint path as its argument:

- **400 seat-balanced games**, candidate vs heuristic, Gravy mirror (`decks/nats2026_eriksen_gravy_60.txt` both sides);
- as **eight `rl/eval.py` invocations of 50 games** — deck-half a ×4, deck-half b ×4 — each with its **own fresh workdir and socket**;
- **`--max-turns 87`** on every call (parameter 87, trigger 62) and **`TCG_MAX_DECISIONS=3000`** exported in the script's environment, inherited by eval.py's subprocesses exactly as in the re-gate;
- **budget:** eval.py's internal per-batch budget is `games × 3 + 180` = **330 s** for 50 games, against ~210 s needed at the measured 4.2 s/game — a 1.57× margin, tolerating candidates whose games run up to ~6.6 s/game. (The re-gate's 200-game form had 780 s against ~840 s needed and truncated at ~186 per half; that form is not used again.)
- **`eval.py` is not touched.** This is an invocation change only.
- **Server-log verification:** every invocation's workdir server log must show the candidate loaded with **fallbacks = 0**, else the gate is void (unchanged from ba4e9c97);
- the gate's games are **registered eval-only before the next step** (unchanged; §4.3(iv) covers truncated gates);
- the read is pooled from the **eight summaries** by the script's pooling tail: draw-score, non-win score, capped share and cap reasons, per-invocation counted totals and timeout flags (§4.2 for the read arithmetic).

### 4.2 The pass rule — relative to R\* = 0.51213 (recorded)

**R\* = 0.51213** — the re-gate's counted pooled draw-score (190/371; claude-reply-b876b3f §1.4.2; the 2 in-flight games could move it by at most ±0.003).

> A candidate **passes** iff **(i)** its formal-gate pooled draw-score point estimate **≥ R\* = 0.51213**, AND **(ii)** the **lower bound of its 95% interval > R\* − 0.05 = 0.46213**.

**Interval construction (wording corrected per reply §4):** the draw-score is the mean of per-game scores in {1, 0, 0.5}; its interval is the **normal approximation on that mean with the empirical score variance** — `var = (W(1−m)² + L·m² + C(0.5−m)²)/N`, `CI = m ± 1.96·sqrt(var/N)` — the construction the re-gate used. A draw-score is not a binomial proportion and **Wilson is not used for it**; **Wilson 95% is used only for capped shares** (the stall diagnostic, §4.4). In `run_formal_gate.sh` the comparisons are made against R\*'s exact counted value (190/371 = 0.51212938…) rather than the rounded constant, so a candidate matching the anchor's counted performance exactly is not failed by the recording's rounding; the recorded thresholds above are the rule of record.

- **Draw-score** = (wins + 0.5 × capped_games) / games, per invocation pooled; the **non-win score** (wins / games) is **co-reported** beside it, with cap reasons kept.
- **Candidate order and cap unchanged** (ba4e9c97 §C4): the run's spot-verified checkpoints in version order (**v5, v10, v15, v20**), **at most 4 formal gates**; the **first** passer is the raw arm.
- **No passer in 4 gates** remains the **"no checkpoint passing" finding**: reported with all reads, and the pipeline stops there — no teacher, no fleet (unchanged).

### 4.3 Partial-completion rule — registered in advance (reply §4)

If any of a gate's eight summaries carries the timeout error (`"play_game.php timed out (partial results used)"`):

- **(i)** the in-flight game of each truncated invocation is **worst-cased**;
- **(ii)** the gate's pass/fail is read **only if it holds under every outcome of the uncounted games** (the §1-of-the-reply invariance test, stated in advance);
- **(iii)** otherwise, the gate is **topped up with fresh-batch games to 400 counted**, and the top-up is **recorded in the gate report**;
- **(iv)** **every id, counted or in flight, is registered** eval-only either way.

The script's pooling tail surfaces the rule's inputs whenever a timeout flag is set: per-invocation counted totals and flags, the uncounted count, and the worst-case draw-score bounds over all completions (all-uncounted as heuristic wins / as capped draws / as candidate wins, and the all-capped capped share with its Wilson lower bound) — and prints that the PASS/FAIL line must not be read directly in that case.

### 4.4 Stall-guard diagnostic at each formal gate — report-only

Alongside each formal gate's read, the gate report prints the candidate's **pooled capped share** with its Wilson95 interval, against the mirror bound **0.2285** (the whole-mirror H′ upper bound). If the share's Wilson lower bound exceeds 0.2285 the candidate is **flagged** as stalling beyond the matchup's intrinsic rate on this evidence. **Diagnostic only**: never a pass/fail condition, never a stop; the flag is carried into the stage-3 report for Claude and Joe.

---

## 5. What does not change

- **The floors stay at 0.30** — spot-gate and heartbeat alike — now read on the draw-scored instrument, where the heuristic's self-play is 0.5: the same footing they had on Fai.
- **The KL budget** (0.125 against the frozen anchor's probe log-probs) and its acceptance logic, untouched.
- **Heartbeat mechanics** other than the §3.2 tally value: window 150, arming at 100 heuristic games / 50 window entries, halt-and-revert behavior, all unchanged. The workers' caps are the engine defaults (§3.3) — as they were at ba4e9c97, now stated rather than assumed.
- **Spot-gate mechanics** other than §2: every 5 accepted versions, 50 games, the inconclusive threshold, revert-to-last-spot-verified and the rejection halts, all unchanged.
- **The K1 three-corpus probe**, **the K3 ghost-vs-raw pre-gate**, **K5's DUP_SEQ rule**, **K2's Gravy tree**, **K4's stop (e)** — untouched.
- **Stage 4** (the Gravy tree and the teacher build) and **stage 5** (the gate fleet, seeds 8001–8200) — untouched; the fleet runs its own registered instrument.
- **Flag 1** (train on the current featurizer) and **Flag 2** (no canonical-suite gate; `--suite none`) — as ratified, untouched.
- **The pristine trainer** (`rl/trainer_v4.py`, `8fd52d82…`) is never edited; every trainer change rides the launch-copy patch. Production `rl/run_workers.sh` and `rl/eval.py` are likewise untouched. The alignment lives entirely in round-7 files: `code/patch_trainer_launch.py` (changes 4–5) and `code/gravy_ppo_launch.sh` (the trainer-hash guard only).

## 6. Scope notes

1. **The heartbeat tally change is a trainer-code change in form, a launch-copy diff in fact** (carried from the draft; the reply §3.2 holds it to the same standard as the spot-gate changes and accepts it): one line of `finalize_games`, only inside the patched launch copy, by the same anchor-asserted, hash-guarded mechanism as the ratified changes 1–3.
2. **The draft's scope note 2 (the worker-cap consequence) is discharged by the withdrawal** (§3.3): there is no longer a worker-cap change whose training-stream consequence needs registering. The training stream remains exactly as approved at ba4e9c97 — engine-default caps — and the only training-adjacent novelty is the §3.3 **report** of the rollout stream's capped share per accepted version.

## 7. Registry merge record (claude-reply-b876b3f §1.4, condition 1 — EXECUTED)

Executed 2026-10-22 under Joe's go (06:37 EDT), before this commit, as the read's condition requires (the re-gate reads Cleared **effective once these ids are merged**):

- **Ids:** the re-gate run's **373** game ids — 371 counted + the 2 in flight — taken from the appendix of `rounds/round7/regate-run.md` and **cross-checked exactly** against the run workdirs' `traj/games_meta.jsonl` (`gravy_bc/anchor_regate_a`: 187, `gravy_bc/anchor_regate_b`: 186; the per-half sets are identical to the appendix's, the union is 373 unique, no half overlap). Any disagreement would have stopped the merge; there was none.
- **Registry:** `/tmp/harvest/do_not_train_registry.json`. Pre-merge state verified before touching: **3,795 games**, sha256 `ae7b04b9d4f5b554f52fc443e445fa74d48ce15116516d824f15107d340addce` (the pinned state). Timestamped backup taken first: `/home/joe/tcg/registry-vault/do_not_train_registry.bak-20261022-063922-preregate373.json` (hash equal to the pre-merge live hash).
- **Merge:** all 373 ids added eval-only under tag **`gravy_anchor_regate_eval`**; **collisions: 0** (re-verified during the merge; the run's intersection check was also 0). Every prior tag's count is unchanged in the written file.
- **Post-merge state:** **4,168 games** (3,795 + 373, the expected count), the `n_games` field agreeing, per-tag count for `gravy_anchor_regate_eval` = 373, sha256 **`5547cf2bd61a4ba83169bf154ba7c8aa30a01d4796a6238f027124f242fc264b`**.
- **Vault refresh:** `/home/joe/tcg/registry-vault/do_not_train_registry-20261022-regate-merged.json`, sha256 identical to the post-merge live hash.
- **For the stage-3 launch manifest** (reply §1.4): it records the post-merge count **4,168** and sha256 `5547cf2b…` alongside **R\* = 0.51213** (§4.2).

## 8. R4 table — FINAL (the anchor column fixed per reply §1.4.3)

| Instrument | On Fai | On the Gravy mirror | On the Gravy anchor |
|---|---|---|---|
| Fai-era (turn parameter 60 / trigger 35; decisions 3,000) | **0 of 333** capped (BC3 gate records) | H = **0.6721** [0.6530, 0.6906] | **0.72** (288/400, all turn caps) |
| Re-specified (parameter 87 / trigger 62; decisions 3,000) | — | decided-truncation **0.0151** [0.0105, 0.0216]; whole-mirror H′ **0.2117** [0.1958, 0.2285] | capped share **0.21563 [0.17681, 0.26028]** on **371 counted games** (80 turn caps, **0 decision caps**); draw-score **0.51213** [0.46709, 0.55717] — **the re-gate read: CLEARED** (worst-case-invariant per claude-reply-b876b3f §1; registry condition discharged at §7) |

## 9. File inventory (this commit)

| File | sha256 | Notes |
|---|---|---|
| `code/patch_trainer_launch.py` (aligned; replaces the changes-1–3 version) | `8826e39975bad516ed23af3d9257a202ba4374b420d40c532c8db466ee36cd27` | Changes 1–5; base-hash-asserts pristine `8fd52d829acee231b5f066adba879178593de3ffc1a689ca224948186b6a837f`, every anchor exactly once |
| → launch copy it produces (`rl/trainer_v4_gravy.py` at launch) | `a48c4abc94f081397bacbdbb09cf04ffdd3c336b08b4eb2eeb51ca18c501a80a` | Re-produced in scratch for this package (§V) |
| `code/gravy_ppo_launch.sh` | `53d20b824eb414ed77a3a4796c1dc7f00f66a0c9150673178cefc6d4a4715210` | Diff vs previous committed (`6b02d3f1cac2780e937c7497040dcd2c1a72635078d30dcbdc45686bbf8e8d59`): **the trainer-hash guard only** (`dc95d81a` → `a48c4abc`, three occurrences: header comment, grep pattern, abort message). **No worker-cap line**; the workers invocation is unchanged |
| `code/run_formal_gate.sh` (new) | `421934d85bd34c047aa6143ce418bebb5ec9cade33c728462076211b8249c461` | §4 form: checkpoint path as `$1`, 8 × 50 invocations, `--max-turns 87`, `TCG_MAX_DECISIONS=3000` exported, fresh workdir + socket per invocation, pooling/reporting tail (draw-score + normal-approximation interval, non-win co-report, capped share + Wilson, pass test vs R\*, stall diagnostic, partial-rule surfacing) |
| `code/run_regate.sh` (already committed, for reference) | `965cdcb74ab3b938e10a582947144f5798759bcb49c959fb2c47a72ae654505a` | The re-gate's script; its structure is the formal-gate script's template |
| `stage3-alignment-final.md` | (this file) | The amended registration of record |

## 10. What `assign_episode_rewards` pays a capped episode — STATED

Read from the pristine trainer for this package (the reply's "Not reviewed" section asks that the stage-3 report state it; it is stated here and the stage-3 report restates it): `assign_episode_rewards(decs, seat, winner, ep, capped=False)` (`rl/trainer_v4.py:119–133`) assigns a pure terminal reward — non-final decisions 0.0, the final decision carries the outcome: **a capped episode pays terminal −1.0 to the learner, regardless of the recorded winner** (the docstring's words: "Capped games are -1 for the learner regardless of recorded winner"). For uncapped episodes the terminal is +1.0 if `winner == seat`, −1.0 if the winner is the other seat, 0.0 if neither (a draw). So a capped rollout episode is priced exactly as a loss. This value is **unchanged by this round** — the training stream stays as approved at ba4e9c97 — and it is the value claude-reply-b876b3f §3.3 reason 1 refers to.

## 11. Clearance sequencing — what happens after this commit

1. **Claude's confirmation check** at this commit's sha (reply §5): the hashes (§9), the launcher diff (guard only), the formal-gate script's text, and the amended sections (§§3–4). A confirmation, not a fresh review.
2. On that confirmation, **stage 3 stands approved** on this sha, and **`GRAVY_STAGE2_CLEARED` may be set** (per claude-reply-2e5e4c5 §4 as carried by the reply) — the re-gate has read Cleared (§8) and its registry condition is discharged (§7). **This package does not set the flag**, and the launcher continues to refuse to start without it.
3. The **stage-3 launch manifest** records the post-merge registry state (**4,168 games, sha256 `5547cf2b…`**) and **R\* = 0.51213**, re-verifies the patch script and launch-copy hashes before any worker starts (the launcher's guard mechanics), and the stage-3 report carries: the rollout stream's capped share per accepted version (§3.3), the capped-episode reward (§10), and each formal gate's stall diagnostic (§4.4).
4. **Joe's per-stage go in chat is still required** to launch stage 3. Approval certifies the build as written, not the run as executed.

## V. Verification for this package (what was actually run, 2026-10-22)

- **Id cross-check (read-only, before the merge):** appendix sets vs the workdirs' `games_meta.jsonl` — A: 187 = 187, B: 186 = 186, union 373 unique, halves disjoint. PASS.
- **Merge:** pre-state asserted (3,795 / `ae7b04b9…`); backup written and hash-checked; collisions 0; written file re-parsed — 4,168 games, `n_games` agreeing, `gravy_anchor_regate_eval` = 373, all prior tag counts unchanged; post-merge sha256 `5547cf2b…`; vault copy written and hash-matched. PASS.
- **Patch script:** staged file sha256 = `8826e399…` (the registered value). Re-applied in scratch (`/tmp/r7verify` on the box) to a fresh copy of the pristine trainer: exit 0, output sha256 = `a48c4abc…` (the registered launch copy) — reproduced, not merely read from the earlier scratch dir.
- **Launcher:** built from the committed `6b02d3f1…` file by the guard substitution only; `diff` shows exactly the three guard occurrences (header comment, grep pattern, abort message) and nothing else; no `TCG_MAX_TURNS`/`TCG_MAX_DECISIONS` string anywhere in the file. PASS.
- **Formal-gate script:** `bash -n` clean. Its pooling tail was dry-run (no games) on synthetic per-invocation logs carrying the re-gate's two half summaries (85W/68L/33C and 65W/73L/47C): pooled counted 371, W150/L141/C80, cap reasons {turns: 80}, **draw-score 0.51213 [0.46709, 0.55717]** (var 0.19594), non-win 0.40431, **capped share 0.21563 [Wilson95 0.17681, 0.26028]**, stall diagnostic not flagged, and — at the anchor's own counted totals — the pass test reads estimate ≥ R\* true, lower bound > 0.46213 true. The partial-completion block fired on the synthetic timeout flags and printed the worst-case bounds, including 0.47500 for all-uncounted-as-heuristic-wins — claude-reply-b876b3f §1.2's bound, reproduced. PASS.
- **No games were run for this package.** The only executions were the registry merge (§7), the scratch patch application, and the synthetic-input dry check.

---

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude confirms; stage 3 launches only on the confirmation at this sha, the clearance flag set after it, and Joe's go in chat.*
