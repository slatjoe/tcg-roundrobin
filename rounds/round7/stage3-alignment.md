# Round 7 — stage-3 instrument-alignment registration

**Parent:** a1861a1937badd41289bef058cf9fdac825d5f8f (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-2e5e4c5.md` §3 (the specification) and §4 (the amended clearance).
**Status: ALIGNMENT REGISTRATION DRAFT for review. Nothing launches on this document.** Stage 3 launches only when **all three** hold: **(a)** the re-gate (registration `2e5e4c5d`) reads **Cleared**; **(b)** this registration is approved at its committed sha; **(c)** Joe gives the per-stage go. Per claude-reply-2e5e4c5 §4, `GRAVY_STAGE2_CLEARED` is set **only when (a) and (b) both hold** — a Cleared re-gate alone does not set it.
**What this document does:** it moves stage 3's three internal instruments — the PPO **spot gates**, the **heartbeat**, and the **C4 formal gates** — onto the re-specified instrument of `respecified-gate-registration.md` (turn parameter 87 / trigger 62, decision cap 3,000, capped games scored as draws at 0.5). It changes **no policy, no threshold level, and no stage-3 design decision** from ba4e9c97. Every code fact below is read from the box's pristine sources (2026-10-22); every diff is anchor-asserted and was exercised in scratch (§V). **No games were run for this document; the logic tests use synthetic inputs only.**

---

## 1. The gap, restated from the code

The re-gate clears the stage-2 anchor on the re-specified instrument. Stage 3's own gates, as approved at ba4e9c97, still measure on the Fai-era instrument:

| Instrument | As approved (ba4e9c97) | Defect on Gravy |
|---|---|---|
| Spot gates (`trainer_v4.py` `run_spot_gate`) | `rl/eval.py` at turn parameter 60 / trigger 35, capped games counted as non-wins | The anchor itself read 0.1475 on exactly this instrument; a policy at the anchor's level reads ≈ 0.15 at every spot gate, far under the 0.30 floor — **PPO halts at its first spot gate on the artifact** |
| Heartbeat (trailing-150, floor 0.30) | Computed from rollout-worker games under caps nobody had stated, capped games tallied as losses | §3 below: the workers run at the engine defaults (parameter 750 / trigger 725), and the tally scores a capped game 0.0 |
| C4 formal gates (build-package §5) | "The §4 protocol" — the old instrument; thresholds relative to "the stage-2 anchor's gate read" | The anchor's read on the old instrument is the void 0.1475; after a clear, the reference read is the **re-gate's draw-score**, on a different instrument |

Sections 2–4 align each one. Section 5 lists what does not change. Section 6 scopes the whole.

---

## 2. Spot gates — aligned

### 2.1 The current call (pristine `rl/trainer_v4.py`, sha256 `8fd52d82…`, `run_spot_gate` :262–303)

One precision on claude-reply-2e5e4c5 §3's description: the call does not merely omit `--max-turns` — it passes the value **explicitly**. The command built per deck half (25 games each, 50 total, seat-balanced via `--learner-deck a`/`b`):

```python
cmd = [sys.executable, os.path.join(SIM_ROOT, "rl", "eval.py"),
       "--ckpt", ckpt_path, "--opp", "heuristic",
       "--games", str(per), "--deck-a", DECK_FAI,
       "--deck-b", DECK_FAI, "--workdir", workdir,
       "--sock", f"/tmp/spot_v{version}_{deck}.sock",
       "--learner-deck", deck, "--max-turns", "60",
       "--sim-dir", SIM_ROOT]
r = subprocess.run(cmd, capture_output=True, text=True,
                   cwd=SIM_ROOT, timeout=1500)
```

(In the launch copy, `DECK_FAI` is already `DECK_SPOT` — the ratified round-7 deck repoint.) The subprocess carries **no `env=`**, so it inherits the trainer's environment; nothing in that environment sets `TCG_MAX_DECISIONS`, so the decision cap rides at the engine default 3,000 by inheritance, unstated. The read: the last JSON summary line of eval.py's stdout is parsed; `wins += summ["wins"]`, `played += summ["games"]`, and the verdict read is

```python
wr = wins / played          # capped games sit in `games`, never in `wins`
return ("fail" if wr < floor else "pass"), wr, played
```

— capped games score as non-wins. `run_spot_gate` is the trainer's **only** `eval.py` call (verified: one `eval.py` reference and one `subprocess.run` in the file).

### 2.2 The diff — launch copy only, via `patch_trainer_launch.py`

The alignment rides the existing mechanism: `code/patch_trainer_launch.py` gains five anchor-asserted replacements (its changes 4–5), each verified to occur exactly once in the pristine trainer. Applied to the pristine file together with the already-approved changes 1–3, the patch produces the aligned launch copy. The spot-gate hunks of the resulting unified diff, verbatim from the scratch build (§V):

```diff
@@ -264,20 +266,22 @@
     per = max(games // 2, 1)
-    wins = played = 0
+    wins = played = capped_total = 0
     for deck in ("a", "b"):
         workdir = os.path.join(out_dir, "spot", f"v{version}_{deck}")
         os.makedirs(workdir, exist_ok=True)
         cmd = [sys.executable, os.path.join(SIM_ROOT, "rl", "eval.py"),
                "--ckpt", ckpt_path, "--opp", "heuristic",
-               "--games", str(per), "--deck-a", DECK_FAI,
-               "--deck-b", DECK_FAI, "--workdir", workdir,
+               "--games", str(per), "--deck-a", DECK_SPOT,
+               "--deck-b", DECK_SPOT, "--workdir", workdir,
                "--sock", f"/tmp/spot_v{version}_{deck}.sock",
-               "--learner-deck", deck, "--max-turns", "60",
+               "--learner-deck", deck, "--max-turns", "87",
                "--sim-dir", SIM_ROOT]
         try:
             r = subprocess.run(cmd, capture_output=True, text=True,
-                               cwd=SIM_ROOT, timeout=1500)
+                               cwd=SIM_ROOT, timeout=1500,
+                               env={**os.environ,
+                                    "TCG_MAX_DECISIONS": "3000"})
@@ -297,9 +301,12 @@
         wins += int(summ["wins"])
         played += int(summ["games"])
+        capped_total += int(summ.get("capped_games", 0))
     if played < 40:
         return "inconclusive", (wins / played if played else 0.0), played
-    wr = wins / played
+    # ROUND-7 ALIGNMENT: draw-scored read -- capped games score
+    # 0.5 (re-specified instrument; see stage3-alignment.md).
+    wr = (wins + 0.5 * capped_total) / played
     return ("fail" if wr < floor else "pass"), wr, played
```

(The `DECK_FAI → DECK_SPOT` lines in the first hunk are the pre-existing round-7 change 3, shown for context; the alignment's own changes are `--max-turns "87"`, the explicit `TCG_MAX_DECISIONS` in the subprocess environment, the `capped_games` accumulation, and the draw-scored read.) In replacement form, the patch script gains exactly:

```python
    (
        '"--learner-deck", deck, "--max-turns", "60",',
        '"--learner-deck", deck, "--max-turns", "87",',
    ),
    (
        "            r = subprocess.run(cmd, capture_output=True, text=True,\n"
        "                               cwd=SIM_ROOT, timeout=1500)",
        "            r = subprocess.run(cmd, capture_output=True, text=True,\n"
        "                               cwd=SIM_ROOT, timeout=1500,\n"
        "                               env={**os.environ,\n"
        "                                    \"TCG_MAX_DECISIONS\": \"3000\"})",
    ),
    (
        "    wins = played = 0",
        "    wins = played = capped_total = 0",
    ),
    (
        "        wins += int(summ[\"wins\"])\n"
        "        played += int(summ[\"games\"])",
        "        wins += int(summ[\"wins\"])\n"
        "        played += int(summ[\"games\"])\n"
        "        capped_total += int(summ.get(\"capped_games\", 0))",
    ),
    (
        "    wr = wins / played",
        "    # ROUND-7 ALIGNMENT: draw-scored read -- capped games score\n"
        "    # 0.5 (re-specified instrument; see stage3-alignment.md).\n"
        "    wr = (wins + 0.5 * capped_total) / played",
    ),
```

The summary field the read now consumes (`capped_games`) is already carried by every eval.py summary — verified for the re-gate registration against the stage-2 gate's summaries; no eval.py change is needed or made. **The floor is unchanged: `--spot-floor` default 0.30, the verdict compares the draw-scored read against it.** The "inconclusive" branch (`played < 40`) is unchanged, including its non-win fallback figure, which is a diagnostic return on an aborted gate, never a verdict read. The per-half eval summaries persist under `out_dir/spot/v<version>_<deck>/`, so the non-win figure for any spot gate stays recoverable from the run's own artifacts.

### 2.3 Logic test (synthetic summaries; run 2026-10-22, §V)

The read arithmetic, old vs aligned, on two stated inputs:

| Input summary | Non-win read (old) | Draw-scored read (aligned) |
|---|---|---|
| Stage-2 anchor gate, half A: 200 games, 28 wins, 142 capped | 28/200 = **0.1400** | (28 + 0.5×142)/200 = **0.4950** |
| Fai-like: 165 games, 69 wins, 0 capped | 69/165 = **0.4182** | **0.4182** — identical |

The first row is the artifact in miniature: the same games that failed every floor on the old read sit at the instrument's parity region on the aligned read. The second row is the control: **where nothing caps, the alignment changes nothing** — Fai's spot-gate history reads identically under both scorings. (These are read-arithmetic tests on stated summaries, not predictions of any Gravy spot gate: a real spot gate runs 50 fresh games under the new caps, whose capped share is its own.)

---

## 3. Heartbeat — the workers' caps stated, then aligned

### 3.1 What the workers actually run under (from the code)

- **`rl/run_workers.sh` sets no cap variables.** The string `TCG_MAX_TURNS` / `TCG_MAX_DECISIONS` appears nowhere in `run_workers.sh`, in `trainer_v4.py`, or in `rl/rollout_server.py` (grep, §V). The rollout-server launch passes only its named variables (`TCG_POLICY_SOCK`, `TCG_TRAJ_LOG`, `BC_MODEL`, `RL_MODEL`, `TCG_OPP_MIX`, `TCG_SAMPLE_TEMP`) plus any trailing `NAME=VALUE` args — and `code/gravy_ppo_launch.sh` passes none. The per-game php invocation in the worker loop sets exactly one variable, `TCG_POLICY_SOCK`.
- **The launcher adds nothing.** `gravy_ppo_launch.sh` exports only `SIM`; the workers are invoked with inline `BC_MODEL=$ANCHOR TCG_MATCHUPS=gravy:gravy:1.0` and nothing cap-shaped.
- **Therefore worker games run at the engine defaults** (`play_game.php:332` / `:344`): `TCG_MAX_TURNS ?: 750` → **parameter 750, trigger 725**; `TCG_MAX_DECISIONS ?: 3000`. For turns the workers are **effectively uncapped** — the mirror's decided games end by turn 80; the 725 trigger binds only jointly with the 3,000-decision cap on the pass-forever tail (the stage-1 corpora, generated under these same defaults, capped 479 of 2,400 games, 421 of them on decisions). This is stated plainly, per the specification: the heartbeat's games were never on the gate instrument, on either hero — on Fai the discrepancy was invisible because Fai's games end near turn 15 under any of these caps.

### 3.2 How capped games currently enter the trailing-150 rate

The trainer tails the workers' `games_w*.jsonl` result rows (`results[game] = (winner, capped)`) and `games_meta.jsonl` (opponent type). In `finalize_games()` (`trainer_v4.py`, the tally at :438 in the pristine file), each completed game with learner decisions contributes, per learner seat:

```python
won = 1.0 if (winner == seat and not capped) else 0.0
recent_results.append(won)
if game_opp.pop(game, None) == "heuristic":
    hb_total += 1
    hb_window.append(won)
```

`hb_window` is a deque of maxlen **150** (`--heartbeat-window`); `heartbeat_wr()` is its mean. The halt arms once `hb_total ≥ 100` (`--heartbeat-min`) heuristic games have completed and at least 50 window entries exist, and fires when the mean falls below **0.30** (`--heartbeat-floor`). **A capped game currently enters as 0.0 — a loss** — regardless of how the game stood when the cap fired. The same `won` value also feeds `recent_results` (status.json's `wr_recent`, trailing 200). Separately, `capped` is passed to `assign_episode_rewards` (:429–435), the PPO reward path — **that path is not part of this alignment and is not touched** (§3.4).

### 3.3 The alignment diff — two surfaces

**(a) Worker caps — `code/gravy_ppo_launch.sh` only; production `run_workers.sh` is not edited.** The workers invocation gains the two cap variables in its inline environment, whence they are inherited by `run_workers.sh`'s children, including the per-game php loop and its built-in smoke test:

```diff
-BC_MODEL=$ANCHOR TCG_MATCHUPS=gravy:gravy:1.0 \
+BC_MODEL=$ANCHOR TCG_MATCHUPS=gravy:gravy:1.0 \
+  TCG_MAX_TURNS=87 TCG_MAX_DECISIONS=3000 \
   bash "$SIM/rl/run_workers.sh" 4 "$G60" "$G60" "$OUT" \
   > "$OUT/workers_launch.log" 2>&1 &
```

**Consequence, stated plainly:** the rollout stream is simultaneously the training stream and the heartbeat's measurement stream, so this changes both. Rollout games now end as draws at trigger 62 instead of running to the 725/3,000 limits; capped episodes already have a defined path through `assign_episode_rewards(capped=True)` (unchanged), and truncated-at-62 games are exactly the population the re-specified instrument defines as draws. The alternative — aligning only the tally and leaving the workers at parameter 750 — would leave the heartbeat measuring a different instrument from the spot and formal gates, and is **not** registered: claude-reply-2e5e4c5 §3.2 asks for the same caps *and* the same scoring, and this is what that takes. No other worker behavior changes: matchup mix, opponent mix, temperature, and worker count are untouched.

**(b) The tally — one replacement in the launch-copy patch** (change 5), anchor occurring exactly once in the pristine trainer:

```diff
@@ -435,7 +447,12 @@
                                        capped=capped)
                 ep_counter += 1
                 buffer.extend(decs)
-                won = 1.0 if (winner == seat and not capped) else 0.0
+                # ROUND-7 ALIGNMENT: capped games are draws (0.5)
+                # in the heartbeat / recent tallies (re-specified
+                # instrument). Episode rewards are NOT changed:
+                # they receive `capped` separately, above.
+                won = (0.5 if capped else
+                       1.0 if winner == seat else 0.0)
                 recent_results.append(won)
                 if game_opp.pop(game, None) == "heuristic":
                     hb_total += 1
```

The window (150), the arming thresholds (100 total / 50 in window), and the floor (0.30) are unchanged; only the per-game value a capped game contributes changes, from 0.0 to 0.5, in both the heartbeat window and `recent_results` (they share the one `won` value; there is no second tally to align).

### 3.4 Logic test (synthetic trailing window; run 2026-10-22, §V)

| Window (heuristic-opponent entries) | Old tally mean | Aligned tally mean |
|---|---|---|
| 150 entries: 30 learner wins, 80 losses, 40 capped | 30/150 = **0.2000** → below the 0.30 floor, **heartbeat HALT** | (30 + 0.5×40)/150 = **0.3333** → no halt |
| 150 entries: 45 wins, 105 losses, 0 capped | **0.3000** | **0.3000** — identical |

The first row is the failure the alignment removes: a window in which more than a quarter of the games are intrinsic draws reads as a dying policy under the old tally even when its decided games split 30–80 against a *sampling-temperature* rollout policy — and under the aligned caps many of those 40 would end as draws at 62 rather than at the old limits, scored 0.5 either way. The second row is the control: with no capped games the tallies coincide, so Fai-era heartbeat behavior is reproduced exactly.

---

## 4. C4 formal gates — re-based on the re-gate's read

### 4.1 Form (build-package §5, instrument replaced)

Each formal gate is the re-gate's protocol, verbatim in form (`respecified-gate-registration.md` §5, with the candidate substituted for the anchor):

- **400 seat-balanced games** through `rl/eval.py`, candidate vs heuristic, Gravy mirror — two invocations of 200, `--learner-deck a` and `--learner-deck b`, in **fresh workdirs**;
- **`--max-turns 87`** on both calls (parameter 87, trigger 62) and **`TCG_MAX_DECISIONS=3000`** set explicitly in the gate's launch environment (the inheritance path of the registration §2);
- **server-log-verified**: both halves' server logs must show the candidate loaded with **fallbacks = 0**, else the gate is void (unchanged from ba4e9c97);
- the gate's games are **registered eval-only before the next step** (unchanged);
- the read is computed from the per-half summaries exactly as the re-gate's: **draw-score = (wins + 0.5 × capped_games) / games**, per half and pooled, cap reasons kept, and the **non-win score co-reported** beside it.

### 4.2 The pass rule — relative to R*

Let **R\*** denote the **re-gate's pooled draw-score** — a value the re-gate run supplies (recorded in its run manifest and in the stage-3 launch manifest). R* is kept symbolic in this rule; nothing in the rule depends on its value, and no number is written here in its place. (This supersedes build-package §5's C4 wording, which keyed the thresholds to "the stage-2 anchor's gate read" — on the old instrument that read is the void 0.1475.)

> A candidate **passes** iff **(i)** its formal-gate pooled draw-score point estimate **≥ R\***, AND **(ii)** the **lower bound of its Wilson 95% interval > R\* − 0.05**. The interval is computed on the draw-score from the gate's three-category counts (candidate wins, heuristic wins, draws), treating the read as the mean of per-game scores in {1, 0, 0.5} — the construction of claude-reply-2e5e4c5 §2.2 — with the method stated in the gate's report.

- **Candidate order and cap unchanged** (ba4e9c97 §C4): the run's spot-verified checkpoints in version order (**v5, v10, v15, v20**), **at most 4 formal gates**; the **first** passer is the raw arm.
- **No passer in 4 gates** remains the **"no checkpoint passing" finding**: reported with all reads, and the pipeline stops there — no teacher, no fleet (unchanged).

### 4.3 Stall-guard diagnostic at each formal gate — report-only

Alongside each formal gate's read, the gate report prints the candidate's **pooled capped share** with its Wilson 95% interval, against the mirror bound **0.2285** (the whole-mirror H′ upper bound, `respecified-gate-registration.md` §3). **This is a diagnostic only**: it is never a pass/fail condition, it does not stop a gate, and it does not substitute for the re-gate's stall guard (which governed the anchor, at the re-gate, under its own registration). A candidate whose capped share's lower bound exceeds 0.2285 is **flagged in the report** as stalling beyond the matchup's intrinsic rate on this evidence, and the flag is carried into the stage-3 report for Claude and Joe — nothing more follows from it under this registration.

---

## 5. What does not change

- **The floors stay at 0.30** — spot-gate floor and heartbeat floor alike — now read on the draw-scored instrument, where the heuristic's self-play is 0.5: the same footing they had on Fai (claude-reply-2e5e4c5 §3.4).
- **The KL budget** (0.125 against the frozen anchor's probe log-probs) and the Gate's acceptance logic, untouched.
- **Heartbeat mechanics** other than §3's caps and tally value: window 150, arming at 100 heuristic games / 50 window entries, halt-and-revert behavior, all unchanged.
- **Spot-gate mechanics** other than §2: every 5 accepted versions, 50 games, the inconclusive threshold, revert-to-last-spot-verified and the rejection halts, all unchanged.
- **The K1 three-corpus probe** (27,000 states; builder, guards, and launch-time hash mechanics of ba4e9c97) — untouched.
- **The K3 ghost-vs-raw pre-gate** (seeds 8501–8510, the determinism check, the standing seat-crossed raw control, per the K1/K3 fix) — untouched.
- **K5's DUP_SEQ rule**, **K2's Gravy tree** (built from `/tmp/otree`, abort patch carried), **K4's stop (e)** — untouched.
- **Stage 4** (the Gravy tree and the teacher build) and **stage 5** (the gate fleet, seeds 8001–8200, its stops and audit) — untouched; the fleet already runs its own registered instrument.
- **Flag 1** (train on the current featurizer; the (b) correction debuts in the distillation run) and **Flag 2** (no canonical-suite gate; `--suite none`) — as ratified, untouched.
- **The pristine trainer** (`rl/trainer_v4.py`, `8fd52d82…`) is never edited; every trainer change rides the launch-copy patch, as before. Production `rl/run_workers.sh` and `rl/eval.py` are likewise untouched — the alignment lives entirely in round-7 files: `code/patch_trainer_launch.py` (changes 4–5 added) and `code/gravy_ppo_launch.sh` (the §3.3(a) env line, and its trainer-hash guard updated to the aligned launch copy, §V).

---

## 6. Scope and limits

This registration aligns instruments only. It changes no policy, no threshold **level** (0.30 floors, the R*-relative C4 rule at its registered offsets, the 0.125 KL budget), and no stage-3 design decision from ba4e9c97. Two scope notes, stated rather than absorbed:

1. **The heartbeat tally change is a trainer-code change in form, a launch-copy diff in fact.** It edits one line of `finalize_games` — but only inside the patched launch copy, by the same anchor-asserted mechanism as the ratified changes 1–3, with the pristine file hash-asserted before patching and never modified. No trainer-core file changes; if Claude wants the tally change held to a different standard than the spot-gate changes, that is his call on this text — the diff is §3.3(b) either way.
2. **The worker-cap alignment changes the rollout stream itself** (§3.3(a) consequence). That is inherent in claude-reply-2e5e4c5 §3.2's "same caps" requirement — the heartbeat has no games of its own apart from the rollout stream — and it is registered here explicitly so the consequence is reviewed, not discovered. Nothing else in stage 3 required more than the diffs shown: the spot-gate read, the tally, the worker environment, the launcher's hash guard, and the C4 rule's reference value. If review finds a further surface, it comes back as a package, not as an edit to this one.

---

## V. Build verification (what was actually run, 2026-10-22)

**V.1 HEAD:** via the git ref (`gh.py GET repos/slatjoe/tcg-roundrobin/git/ref/heads/main`): `a1861a1937badd41289bef058cf9fdac825d5f8f` — the claude-reply-2e5e4c5 commit, as this registration's parent.

**V.2 Records read (read-only):** `claude-reply-2e5e4c5.md` §§3–4; `followup-k1-k3-fix.md` (ba4e9c97) and `followup-k1-k5.md` (C4 original text); `respecified-gate-registration.md` §§2–5; build-package §5 (stage-3 configuration, C4, launch form). On the box: `rl/trainer_v4.py` (sha256 `8fd52d829acee231b5f066adba879178593de3ffc1a689ca224948186b6a837f`, matching the patch script's asserted base) — `run_spot_gate` :262–303 read in full, the heartbeat tally in `finalize_games`, the arming/halt block, and grep counts (exactly **one** `eval.py` reference, one `subprocess.run`, and each new patch anchor occurring exactly **once**: `"--max-turns", "60"`, `wins = played = 0`, the `wins += / played +=` pair, `wr = wins / played`, the `won = 1.0 if …` line); `rl/run_workers.sh` in full (no cap variables anywhere; the server-launch variable list; the php loop's single `TCG_POLICY_SOCK`); `play_game.php:332/336/344` (defaults 750 / trigger −25 / 3,000); staging `code/patch_trainer_launch.py` and `code/gravy_ppo_launch.sh` (exports: `SIM` only; the workers invocation's inline env).

**V.3 Scratch build test** (in `/tmp/r7align` on the box; nothing installed, no production file touched): the aligned `patch_trainer_launch.py` (staging file + §2.2/§3.3(b) replacements + docstring; sha256 `8826e39975bad516ed23af3d9257a202ba4374b420d40c532c8db466ee36cd27`) run against the pristine trainer: **exit 0** — base hash asserted, all eleven anchors (changes 1–5) occurring exactly once each; output **launch copy sha256 `a48c4abc94f081397bacbdbb09cf04ffdd3c336b08b4eb2eeb51ca18c501a80a`**, `py_compile` clean. The unified diff it printed is the source of the hunks quoted in §2.2 and §3.3(b). On approval, `rounds/round7/code/patch_trainer_launch.py` is replaced by this aligned version and `code/gravy_ppo_launch.sh`'s trainer-hash guard moves from `dc95d81a` to `a48c4abc` in the same commit; the stage-3 launch manifest re-verifies both hashes before any worker starts (the launcher's existing guard mechanics).

**V.4 Logic tests** (synthetic inputs only; the formulas are the patched ones): spot read — stage-2 half-A summary (28 wins / 142 capped / 200) reads 0.1400 non-win vs **0.4950** draw-scored; Fai-like summary (69 / 0 / 165) reads **0.4182 under both**. Heartbeat — a synthetic 150-entry window (30W / 80L / 40 capped) means **0.2000** under the old tally (a halt) vs **0.3333** aligned; an all-decided window (45W / 105L) means **0.3000 under both**. Stall-bound reference recomputed: mirror H′ 508/2400 = 0.2117, Wilson95 [0.1958, **0.2285**] ✓.

**Stated as unverifiable at draft time:** R* (the re-gate has not run at drafting; the C4 rule is registered symbolically, §4.2); any real Gravy spot-gate or heartbeat read under the aligned instrument (stage-3 launch reads, not build claims); the aligned launch copy's behavior in a live run (scratch-verified as a patch + compile + read arithmetic only).

---

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude reviews; stage 3 launches only on a Cleared re-gate, this registration's approval at its committed sha, and Joe's go in chat.*
