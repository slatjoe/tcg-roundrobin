# Round 7 — K1/K3 fix: three-corpus probe builder + corrected pre-gate controls

**Parent:** 94518266616d2a6f7ccd47fc1f685c60ebea25f2 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-a889f39.md` §§1–2 — the two changes requested on the stage-3 follow-up. `rounds/round7/followup-k1-k5.md` is **not edited** (earlier rounds are never edited); this fix amends its §K1 and §K3 **by substitution** — §3 below replaces follow-up §K3 in full, and the updated `code/build_gravy_probe.py` replaces the a889f394 single-corpus form. **K2, K4 and K5 stand as accepted** (reply §4) and are untouched (§4 below).
**Status: DRAFT for review. Nothing launches on this fix.** Stages 0–2 continue under the dd4cb2fe approval. Stage 3 and later are requested for approval at this fix's committed sha, with the probe hash recorded as a launch-time artifact under the reply's §3 (mechanics restated at §1.5).

**Package contents**

| File | Role |
|---|---|
| `followup-k1-k3-fix.md` | this fix: §1 the K1 builder change, §2 the O pre-gate pairing finding, §3 the corrected K3 substitution text, §4 what does not change, §V build verification |
| `code/build_gravy_probe.py` | K1: the registered Gravy probe builder, extended to all three corpora (replaces the a889f394 version in place; that version is preserved in its commit) |

---

## 1. K1 — the probe is built from all three corpora

### 1.1 The correction

The follow-up's §K1 scoped the Gravy probe to the mirror corpus alone, following Claude's original K1 wording. Claude's reply corrects it, and owns the error: his K1 "named only the mirror corpus because I didn't know the recipe." With the recipe recovered (§K1.1 of the follow-up, verified again at §V.2 below), Fai's probe drew **9,000 states from each of its run's three training corpora** (mirror, cross, DAgger — 27,000 total), so "verbatim" means the same three-corpus structure for Gravy. The builder is extended accordingly. Nothing else about K1 changes: same tool, same selection rule, same cap, same consumption (the Gate's fixed 4,096 subsample, seed 20261016, anchor log-probs computed once).

### 1.2 Corpus names — verified against the driver and the box (no mismatch)

Claude's reply names `gravy_bc/data/{mirror_self, cross_self, mirror_bc}`. Those are the driver's real names, not Fai-analogy guesses:

| Corpus (build order) | Driver line (`code/gravy_corpus_driver.sh`) | Games guard |
|---|---|---|
| `gravy_bc/data/mirror_self` | batch 1: `bc2_gen.sh 6 400 $G60 $G60` (heuristic Gravy mirror) | **2,400** |
| `gravy_bc/data/cross_self` | batch 2: `bc2_gen.sh 6 125 $G60 $F60` (heuristic Gravy vs Fai) | **750** |
| `gravy_bc/data/mirror_bc` | batch 3: `bc2_gen.sh 6 250 $G60 $G60 <pass-1 clone>` (DAgger, pass-1 driven) | **1,500** |

On the box at drafting: `gravy_bc/data/` holds `mirror_self` (stage 1 still generating — **534 / 2,400 games** at 2026-10-21 15:56 EDT, read from its `games_w*.jsonl`); `cross_self` and `mirror_bc` are created by the driver in batch order. The per-corpus guards above are the reply's §1 values (2,400 / 750 / 1,500), and they are the driver's own `check_batch` values.

### 1.3 What changed in `code/build_gravy_probe.py`

Against the a889f394 form (single `--corpus`, one `--expect-games`, default 2400):

- **Corpus list, ordered, with per-corpus guards.** Defaults are the three corpora of §1.2 in driver order with guards 2400 / 750 / 1500. `--corpus` (comma-separated paths) + `--expect-games` (comma-separated counts, required with `--corpus`) exist for scratch testing.
- **One `probe_kl.py build` invocation with all three corpora** — the exact form of Fai's build (one run, corpora in argv order, `--per-corpus 9000`), producing `probe/probe_gravy_v1.jsonl`.
- **Every guard is now per-corpus:** each corpus's `games_w*.jsonl` total must equal its guard **before anything is built** (stage-1 completion check — game counts, never a DONE file); the tool's per-corpus `kept` line must equal the 9,000 cap **for every corpus**.
- **Per-corpus re-scan verification.** The output is segmented by the tool's per-corpus kept counts, in build order, and the script's independent re-scan (a second implementation of the same filter) must reproduce **each corpus's** kept `(game, decision)` sequence against its segment — not just the merged file.
- **Manifest output** gains one `PROBE_CORPUS <name> games=<counted> kept=<kept>` line per corpus; `PROBE_FILE` / `PROBE_STATES` / `PROBE_SHA256` are as before (27,000 states expected).

Unchanged from the a889f394 form: the builder still invokes the box's own `probe_kl.py` rather than re-implementing the selection for the build; refusal to overwrite an existing probe file; the ≥2-candidates check on every output record; abort-before-build ordering of the guards.

**Diff summary:** docstring rewritten for the three-corpus form (recipe + yield rule + registered invocation); `DEFAULT_CORPORA` table added; `--corpus` / `--expect-games` argument surface replaced; single-corpus guard block → per-corpus guard loop; single kept-line parse → ordered per-corpus kept parse; whole-file re-scan → segmented per-corpus re-scan; `PROBE_CORPUS` lines added. The updated file is 12,002 B, sha256 `6f5e64b691ef7e20c47ff6b11357db89d6dbea25a9f90a6955c90395e6075b05` (§V.3/V.4).

### 1.4 The yield rule

The **tool's** semantics (`probe_kl.py build`, read from source at drafting): per corpus it writes `min(cap, eligible)` records — a corpus whose eligible records exhaust below the cap yields what it has, and the tool prints the actual kept count. This builder invents no other rule: its registered guard requires kept == cap for **every** corpus and **aborts** on a short one — a short yield is a stage-1 finding, not a probe to train against (the reply's §3 names short yield a guard failure that stops stage 3). Fai's build reached the cap on all three corpora (`probe/build.log`). The Gravy corpora's record targets (design: ≈920k mirror / ≈284k cross / ≈563k DAgger records against a ≥2-candidate + 1-in-7-hash filter) make the cap reachable by wide margins on all three.

### 1.5 Registered build command; the hash as a launch-time artifact

The probe file remains a launch-time artifact (stage 1 is still generating). Registered invocation, on the box, after stage 1 completes all three corpora:

```
/home/joe/tcg/rl-env/bin/python code/build_gravy_probe.py \
    --sim-root /home/joe/tcg/tcg-sim
```

(script deployed to the sim root's `code/` path at stage-3 launch, as with the other stage code; defaults per §1.3.) Mechanics, per the reply's §3: the resulting `PROBE_SHA256` is recorded in a **builder note** and in the **stage-3 launch manifest**; a recomputation mismatch at manifest time **voids the build**, which is then rebuilt, not explained; **no re-review is needed for the hash itself**, provided the build passes every guard; a guard failure (short yield, re-scan mismatch, game count) **stops stage 3** and comes back as a package.

---

## 2. The O pre-gate pairing — what "raw-control self-pairing differed on 10/10" actually paired

Determined from primary records only. The sentence under examination is in the O results, `rounds/round4/builder-response-6d25014.md:45`: *"Pre-gate (against BC3): PASS — 20/20 trace-identical (seeds 4001–4010, both seats; raw-control self-pairing differed on 10/10 seeds, so the comparison can see differences)."*

**The evidence chain:**

1. **The registration it executed** — `rounds/round4/o-package.md` §3 (:51): *"Comparison: `r3_pair.py` trace-level pairing, the round-3 pre-gate standard, with the standing raw-control pairing (raw vs a second raw run) to prove the comparison can see differences."*
2. **The instrument's own definition** — `/tmp/otree/r3_pair.py:18–22` (module docstring): *"Standing control: `r3_pair.py --raw-control <rowsA.jsonl> <rowsB.jsonl>` compares two raw arms run at **different seats**; they must differ on at least one seed (identical raw arms at different seats is the signature of a seat-blind server). Prints the differing-seed count and RAW-CONTROL PASS/FAIL."* The implementation (`raw_control()`, :79–95) compares, per seed, the outcome fields `winner, turns, decisions, p1life, p2life, gamestate_norm_sha` plus `gamelog_sha`. Lineage: registered in round 3 after the seat-routing defect — `rounds/round3/builder-response-d3095af.md` ("Standing raw control: `r3_pair.py --raw-control <rowsA> <rowsB>` compares two raw arms **across seats** (outcome fields + gamelog sha per seed)… ≥1 differing seed required"; and the R16 text: *"raw s1 vs raw s2 must differ on at least one seed… if they do not, the run is void regardless of the pairings"*).
3. **The launch script that ran it** — `/tmp/o_stage/run_pregate.sh`, final block (also echoed in `/tmp/o_pregate/pregate_run.log`):
   ```
   echo "== raw control (raw s1 vs raw s2) =="
   $PY r3_pair.py --raw-control $OUTD/pg_raw_s1.jsonl $OUTD/pg_raw_s2.jsonl \
     > $OUTD/raw_control.txt 2>&1
   ```
4. **The two runs** — `/tmp/o_pregate/pg_raw_s1.jsonl.manifest.json`: arm `raw`, seat **1**, seeds **4001-4010**, tree `/tmp/otree` (learner v15 via the fleet servers, opponent BC3); `/tmp/o_pregate/pg_raw_s2.jsonl.manifest.json`: arm `raw`, seat **2**, seeds **4001-4010**. These are the pre-gate's own ghost-pairing raw runs — the same two files `pair_s1.txt` / `pair_s2.txt` paired against `pg_ghost_s1` / `pg_ghost_s2` for the 20/20 IDENTICAL read.
5. **The output** — `/tmp/o_pregate/raw_control.txt`: *"raw-control: 10/10 seeds differ (fields: winner, turns, decisions, p1life, p2life, gamestate_norm_sha, gamelog_sha) / differing seeds: [4001, 4002, …, 4010] / RAW-CONTROL: PASS"*.
6. **Not this control:** the `ctl_raw_s1/s2` runs (`/tmp/o_stage/run_live_control.sh`) are the separate **opponent-is-live** control — raw runs against heuristic-opponent servers, compared per-seat against the `pg_raw` runs (`live_control_s1.txt` / `live_control_s2.txt`), reported in the results separately as the 20/20-unit live control. The cited sentence sits in the pre-gate clause and its file is `raw_control.txt`.

**Finding.** The O pre-gate's "raw-control self-pairing differed on 10/10 seeds" paired the pre-gate's own raw run at **seat 1** (`pg_raw_s1.jsonl`, seeds 4001–4010, vs BC3) against the pre-gate's own raw run at **seat 2** (`pg_raw_s2.jsonl`, same seeds, vs BC3), via `r3_pair.py --raw-control` in `/tmp/o_stage/run_pregate.sh`. **It was the standing seat-crossed control (round-3 R16) — not a same-seat re-run.** "Self-pairing" in the results sentence meant the pre-gate's own two raw runs paired against each other, as opposed to against the ghost runs. No same-seat raw re-run was made at the O pre-gate, and **no determinism anomaly exists in its record: the finding is the standing control, wording only.**

Consequence for the follow-up: its §K3 "raw self-pairing control" bullet — a same-seat re-run *"expected to **differ** on all 10 units (the O pre-gate's control read 10/10 differ): the bridge's play is not a deterministic replay"* — misread the sentence and inverted the control. It is **withdrawn**. The corrected controls are registered in §3: a determinism check that must be IDENTICAL (the reply's §2), and the standing seat-crossed control under its exact name and pairing.

---

## 3. K3 corrected — substitution text (replaces follow-up §K3 in full)

> ## K3 — the pre-gate is ghost vs raw, with the determinism check and the standing raw control
>
> Build-package §7's pre-gate paragraph described "raw arm, Gravy tree vs the plain bridge" — a raw-vs-raw comparison across trees, which tests neither the machinery nor anything the registration asks about (follow-up §K3, withdrawn there). The follow-up's own raw-control bullet then misdescribed the standing control (see the K1/K3 fix §2 for the evidence); it is withdrawn by that fix. The registered pre-gate is **ghost vs raw**: the full teacher machinery with its pick forced to the prior's, against the plain bridge, on the same seeds — with a determinism check on the raw arm and the standing seat-crossed raw control alongside.
>
> **Pre-gate (registered):** 20 units — seeds **8501–8510 × both seats** — on the Gravy tree, against the fleet's per-seat servers (the tree's patched servers with `SEARCH_MODEL` = the C4-selected checkpoint, started by the launch wrapper before the chunks):
>
> - **Ghost arm** (`paired_driver.py --arm ghost`): the driver sets `TEACHER_MODE=1` + **`TEACHER_GHOST=1`** (`paired_driver.py:245`; arm documented at `paired_driver.py:11` — "full machinery, pick forced to the prior's; must be action-identical to raw"). Inside Decide (O build, `search.php:1029`), after the full machinery — candidate generation, rollouts, the paired overturn test — has computed its pick, the ghost block replaces it: `$pick = $priorPick; $overturn = 0;`, recording `ghost_would_pick` / `ghost_would_overturn` at the marker and stamping the stat row's rule `ghost_prior` (`search.php:1187`). Nothing else about the machinery changes.
> - **Raw arm** (`paired_driver.py --arm raw`): the plain bridge, no search.
> - **Pass criterion (all 20 units):** per unit, `r3_pair.py` pairs the ghost run against the raw run (rows + trace dirs) and the unit passes iff the table reads verdict **IDENTICAL** with **within-row hits = 0**, **outcome equal = True** — the outcome fields being `winner, turns, decisions, p1life, p2life, gamestate_norm_sha, gamelog_sha` — and **modes ok, seat ok, assert ok** all True. The criterion is read through the standard instruments (`r3_pair.py` / `classify_divergence.py`), never the gamelog sha alone. Any non-IDENTICAL unit **stops the fleet**. The sole exception is a divergence attributable to the K5 marker class (follow-up §K5): a trace difference consisting of the pick-null abort marker row, disposed of by the K5 reclassification procedure — anything else is a stop.
> - **(a) Determinism check (new, per claude-reply-a889f39 §2):** a **second raw run at seat 1** on seeds 8501–8510 — same seat-1 server, same configuration as the pre-gate's raw seat-1 run — paired against that first run through `r3_pair.py` under the same criterion (both arms mode-checked as raw): **IDENTICAL on all 10 units is required.** Any difference **stops the pre-gate before the ghost comparison is read**, because a ghost/raw match means something only if raw replays itself. The bridge is deterministic under a fixed seed — that is the recorded behavior, not an assumption: round 2, bridge vs bridge-repeat **19/19 byte-identical**; round 3, the rerun's per-seat games replaying exactly; round 6, the pick-flip run replaying the census games **byte for byte**.
> - **(b) Standing raw control (R16):** `r3_pair.py --raw-control <pregate_raw_s1.jsonl> <pregate_raw_s2.jsonl>` — the pre-gate's **own raw runs across seats**, on the same seeds — must report **at least 1 differing seed** of 10 (`RAW-CONTROL: PASS`). Identical raw arms at different seats are the signature of a seat-blind server; a FAIL voids the pre-gate regardless of the pairings. This uses the pre-gate's existing raw runs, so it needs **no extra games**.
> - **(c) The O precedent, stated precisely:** the O pre-gate's "raw-control self-pairing differed on 10/10 seeds" (round-4 O results) paired its raw seat-1 run (`pg_raw_s1.jsonl`, seeds 4001–4010) against its raw seat-2 run (`pg_raw_s2.jsonl`, same seeds) via `r3_pair.py --raw-control` — the standing control of (b), per `/tmp/o_stage/run_pregate.sh` and `/tmp/o_pregate/raw_control.txt` (full evidence: the K1/K3 fix §2). Control (b) above is that same control, registered under its exact pairing; no same-seat re-run figured in the O pre-gate, and none of its record shows a determinism anomaly.
>
> Registered invocations (per seat, mirroring the fleet runner's driver shape; `GATE_TIMEOUT` from the contention probe):
> ```
> $PY paired_driver.py --tree /tmp/gravytree --sock /tmp/ggate_s<seat>.sock \
>   --seat <seat> --arm ghost --seeds 8501-8510 --timeout $GATE_TIMEOUT \
>   --deck $G60 --out /tmp/ggate/pregate_ghost_s<seat>.jsonl \
>   --logdir /tmp/ggate/pregate_ghost_s<seat>_log
> $PY paired_driver.py --tree /tmp/gravytree --sock /tmp/ggate_s<seat>.sock \
>   --seat <seat> --arm raw --seeds 8501-8510 --timeout $GATE_TIMEOUT \
>   --deck $G60 --out /tmp/ggate/pregate_raw_s<seat>.jsonl \
>   --logdir /tmp/ggate/pregate_raw_s<seat>_log
> # (a) determinism check: second raw run, seat 1, same server
> $PY paired_driver.py --tree /tmp/gravytree --sock /tmp/ggate_s1.sock \
>   --seat 1 --arm raw --seeds 8501-8510 --timeout $GATE_TIMEOUT \
>   --deck $G60 --out /tmp/ggate/pregate_raw2_s1.jsonl \
>   --logdir /tmp/ggate/pregate_raw2_s1_log
> $PY r3_pair.py raw=/tmp/ggate/pregate_raw_s1.jsonl,/tmp/ggate/pregate_raw_s1_log \
>                raw=/tmp/ggate/pregate_raw2_s1.jsonl,/tmp/ggate/pregate_raw2_s1_log
> # (b) standing raw control (R16): the pre-gate's own raw runs, across seats
> $PY r3_pair.py --raw-control /tmp/ggate/pregate_raw_s1.jsonl \
>                              /tmp/ggate/pregate_raw_s2.jsonl
> ```

---

## 4. What does NOT change

- **K2** (the Gravy tree built from `/tmp/otree`, abort patch carried, hashes pinned in the runner), **K4** (stop (e) as the climb-and-ahead calibration pattern), **K5** (the two-condition DUP_SEQ rule): **accepted as written** in followup-k1-k5.md (reply §4); this fix does not touch them.
- **The ghost arm itself** (`TEACHER_MODE=1` + `TEACHER_GHOST=1`, `search.php:1029` / `:1187`): accepted in the reply §4 and restated unchanged in §3, so the substituted section is complete.
- **`code/gravy_ppo_launch.sh`**: unchanged by this fix — it already guards on and passes the probe path; the file it points at (`probe/probe_gravy_v1.jsonl`) is now the three-corpus build.
- **The probe-hash mechanics**: launch-time artifact, builder note + stage-3 manifest, mismatch voids, no re-review for the hash itself if all guards pass (reply §3) — restated at §1.5, unchanged.
- Everything else in followup-k1-k5.md (including its §K1.1 recipe recovery, which §1.1 builds on) and in build-package.md stands.

---

## V. Build verification (what was actually run, 2026-10-21)

**V.1 HEAD:** via the git ref (`gh.py GET repos/slatjoe/tcg-roundrobin/git/ref/heads/main`): `94518266616d2a6f7ccd47fc1f685c60ebea25f2` — the claude-reply-a889f39 commit, as this fix's parent.

**V.2 Records read (read-only):**
- Corpus names: `code/gravy_corpus_driver.sh` batch lines (mirror_self 6×400, cross_self 6×125, mirror_bc 6×250 + pass-1 clone) and the box's `gravy_bc/data/` listing; mirror_self at 534 / 2,400 games, 2026-10-21 15:56 EDT. `probe_kl.py` on the box: sha256 `0c251521523711e33f…` ✓ (the recipe record), and its `build` source read for the yield rule and the per-corpus `kept` lines.
- O pre-gate: `rounds/round4/o-package.md` §3; `rounds/round4/builder-response-6d25014.md:45`; `/tmp/o_stage/run_pregate.sh` (the raw-control block quoted in §2); `/tmp/o_pregate/pregate_run.log` (the "raw s1 vs raw s2" echo); `/tmp/o_pregate/raw_control.txt`; `/tmp/o_pregate/pair_s1.txt` / `pair_s2.txt` (20/20 IDENTICAL on the same raw files); the manifests `pg_raw_s1` / `pg_raw_s2` / `pg_ghost_s1` (arm, seat, seeds read directly); `/tmp/otree/r3_pair.py:18–22` (docstring), `:31–32` (outcome fields), `:79–95` (`raw_control()`), main pairing loop (verdict precedence + within-row hits); `/tmp/o_stage/run_live_control.sh` + `ctl_raw_s1` manifest (the distinct live control, §2 item 6); `rounds/round3/builder-response-d3095af.md` (the standing-control registration and R16 text).

**V.3 Builder scratch tests** (in `/tmp/r7fix` on the box; staging copy and box copy identical, sha256 `6f5e64b691ef7e20c47ff6b11357db89d6dbea25a9f90a6955c90395e6075b05`; the Fai corpora are flat `traj_w*.jsonl` dirs holding no `games_w*.jsonl`, so their game counts read 0 and were passed as `--expect-games 0,0,0` — the V.2 form of the follow-up's scratch test):
- `py_compile` clean (builder + both test scripts).
- **Positive run** — `--corpus bc2_train_data/mirror,bc2_train_data/cross,bc2_train_data/dagger --per-corpus 50 --out /tmp/r7fix/probe_scratch.jsonl`: guards ok (0 games each); `probe_kl.py` reported kept **50 / 50 / 50**, `probe set: 150 records`; the builder's re-scan verified each corpus's kept sequence; `PROBE_STATES 150`, `PROBE_SHA256 317f0cf9dcc5d962e20d3943298273f9e98bf60e644a6bcfd8e071f25260b6db`; exit 0.
- **Independent filter (third implementation)** — a separate pathlib-based filter (not the builder's re-scan code, not `probe_kl.py`) computed each corpus's kept `(game, decision)` sequence at cap 50; compared segment-by-segment against the scratch output: **MATCH on all three corpora** (`ALL_CORPORA_MATCH`).
- **Negative test 1 (game-count guard):** the same corpora with the Gravy guards `--expect-games 2400,750,1500` → abort on the first corpus (`corpus mirror game count 0 != expected 2400`), exit 1, **no output file written**.
- **Negative test 2 (overwrite refusal):** re-running the positive command against the existing scratch output → abort (`already exists; refusing to overwrite`), exit 1.
- The short-yield abort branch was not exercised live (no corpus in reach yields short at cap 50); it is the same kept != cap comparison as the a889f394 builder's, applied per corpus.

**V.4 This package's files:** `followup-k1-k3-fix.md` (this file) and `code/build_gravy_probe.py` (12,002 B, sha256 `6f5e64b691ef7e20c47ff6b11357db89d6dbea25a9f90a6955c90395e6075b05` per §V.3).

**Stated as unverifiable at draft time:** the Gravy probe file and its hash (stage 1 generating; launch-time artifact, §1.5); pre-gate / determinism / standing-control behavior on Gravy (stage-5 launch reads, registered in §3, not build claims).

---

*Builder: Muse (for Joe Slattery), 2026-10-21. Review venue: this repository. Joe relays; Claude reviews; stage 3 and later launch only on Claude's approval of this fix at its committed sha (with the probe hash recorded as a launch artifact) plus Joe's go in chat.*
