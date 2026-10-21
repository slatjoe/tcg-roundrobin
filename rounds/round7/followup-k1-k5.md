# Round 7 — stage-3 follow-up: corrections K1–K5 to the build package

**Parent:** f1bed8d13a5811148dbf90df7e4262137a57b35e (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-dd4cb2f.md` §3 — the five corrections required before stage 3 can be approved. The build package it corrects is `rounds/round7/build-package.md` (commit dd4cb2fe), which is **not edited** — earlier rounds are never edited; every correction below is carried as substitution text in this follow-up.
**Status: DRAFT for review. Nothing launches on this follow-up.** Stages 0–2 are already approved (dd4cb2fe) and running. **Stage 3 and later are requested for approval at this follow-up's committed sha, once the K1 probe hash slot (§K1.4) is filled in** — the probe build runs the moment stage 1 completes the mirror corpus, inside the stages 1–2 window, so the fill-in costs no wall time.

**Package contents**

| File | Role |
|---|---|
| `followup-k1-k5.md` | this follow-up: one section per correction, each with the full substitution text |
| `code/build_gravy_probe.py` | K1: the registered Gravy probe builder (new) |
| `code/gravy_ppo_launch.sh` | K1: updated launcher — passes `--probe` explicitly, probe-existence guard (staging copy updated; the dd4cb2fe version is preserved in that commit) |
| `code/run_gravy_gate.sh` | K2: updated fleet runner — K2 tree-hash guards added (same preservation note) |
| `code/patch_trainer_launch.py` | **unchanged** — K1 needs no trainer change (see §K1.3) |

---

## K1 — a Gravy KL probe set, built by the Fai recipe

### K1.1 The Fai probe's construction recipe, as it was built

Every element below is from a primary record on the box, not from the build draft's summary of it:

| Element | Evidence |
|---|---|
| Build tool | `probe_kl.py`, subcommand `build` — sim root, sha256 `0c251521523711e33f3643846d879d78221b3f99b5587b518b3e6d332866397d` |
| Build record | `probe/build.log`, verbatim: `bc2_train_data/mirror: kept 9000` / `bc2_train_data/cross: kept 9000` / `bc2_train_data/dagger: kept 9000` / `probe set: 27000 records -> probe/probe_v1.jsonl` |
| Source corpora | the three BC2 training corpora: `bc2_train_data/{mirror, cross, dagger}` — heuristic mirror self-play, heuristic cross-matchup, and the bc-driven DAgger batch |
| Selection rule | `probe_kl.py:28–58`: scan each corpus in `os.walk` order (file names sorted per directory), records in file order; keep a record iff (i) it parses as JSON, (ii) `len(state.candidates) >= 2`, (iii) `md5(f"{game}:{decision}").digest()[0] % 7 == 0`; stop at `--per-corpus` (argparse default **9000**) |
| Result | `probe/probe_v1.jsonl` — **27,000 records**, sha256 `974fef83498b0ac6f0ebe2e774e2b73968e5675ce4d6e1b45fe26e0bf9b071db` (line count verified 27,000). Raw records written verbatim: the set is featurization-agnostic by construction |
| Consumption | `rl/trainer_v4.py` `Gate.__init__` (:180–187): loads the probe file; takes the **fixed 4,096-state subsample** — `np.random.RandomState(seed).choice(27000, size=4096, replace=False)` with **seed 20261016** (the Gate's defaults, `subset=4096, seed=20261016`, used unoverridden at the :359 call site), indices sorted; featurizes that batch once |
| Reference log-probs | `trainer_v4.py:361–362`: the anchor's (BC3's) log-probs on the probe batch are computed once at startup and never moved; every candidate's cumulative KL is measured against them under the 0.125 budget |

One note, not a gap: whether the Fai build's argv passed `--per-corpus 9000` explicitly or took the argparse default is not recorded anywhere found. It does not matter — the log shows the cap reached at exactly 9,000 on all three corpora, and the cap is the only outcome-determining element. The recipe above is complete as specified.

### K1.2 The Gravy application

Claude's K1 names the corpus: the **Gravy heuristic mirror corpus** (`gravy_bc/data/mirror_self`, stage-1 batch 1). The recipe applies verbatim — same tool, same selection rule, same per-corpus cap of 9,000 — to that one corpus:

```
probe_kl.py build --corpora gravy_bc/data/mirror_self \
    --per-corpus 9000 --out probe/probe_gravy_v1.jsonl
```

The scoping difference from the Fai file is stated plainly: the Fai probe mixed its run's three training corpora at 9,000 each (27,000 states); K1 scopes the Gravy probe to the mirror corpus at the same per-corpus cap (9,000 states). Everything downstream of the file is unchanged — the Gate loads it, takes the same fixed subsample (4,096 states, `RandomState(20261016)`, sorted indices), and the stage-2 anchor's reference log-probs are computed on that batch once, at stage-3 startup. The probe's role stays exactly as before: the KL budget's fixed instrument, nothing else.

The mirror corpus's expected yield makes the cap reachable by a wide margin (design target ≈ 920k records; the ≥2-candidate + 1-in-7-hash filter passes orders of magnitude more than 9,000). A build that keeps fewer than 9,000 is a stage-1 finding, and the builder aborts on it rather than registering a short probe (§K1.3).

### K1.3 The builder — `code/build_gravy_probe.py`

The registered builder does **not** re-implement the selection for the build itself: it invokes the box's own `probe_kl.py build` (so "verbatim" is literal), then verifies the output with an independent re-scan — a second implementation of the same filter, in the script — whose kept `(game, decision)` sequence must match the produced file exactly. Its guards, any of which aborts the build:

- the output file must not already exist (a built probe is an artifact; never silently overwritten);
- **stage-1 completion check first:** the corpus's `games_w*.jsonl` must total **2,400** games (game counts, never a DONE file — Claude's §2 condition) before anything is built;
- `probe_kl.py`'s reported kept count must equal the 9,000 cap;
- every output record parses and carries ≥ 2 candidates; the independent re-scan reproduces the file's kept sequence exactly.

On success it prints `PROBE_FILE` / `PROBE_STATES` / `PROBE_SHA256` lines for the stage-3 launch manifest.

**Registered invocation** (on the box, after stage 1 completes mirror_self):

```
/home/joe/tcg/rl-env/bin/python code/build_gravy_probe.py \
    --sim-root /home/joe/tcg/tcg-sim
```

(script deployed to the sim root's `code/` path at stage-3 launch, as with the other stage code; defaults: corpus `gravy_bc/data/mirror_self`, out `probe/probe_gravy_v1.jsonl`, expect-games 2400, per-corpus 9000.)

**Launcher repoint — and a finding on the trainer patch.** `patch_trainer_launch.py` needs **no** K1 change: the trainer already exposes `--probe PATH` (`trainer_v4.py:321–322`); only its *default* is the Fai file. The repoint therefore belongs in the launcher, where this launch already pins its paths (anchor, out-dir). The updated `code/gravy_ppo_launch.sh` adds `PROBE=$SIM/probe/probe_gravy_v1.jsonl`, an existence guard for it (after the stage-2 stop guard, before the anchor guard — so a missing probe aborts before any directory is created or any worker starts), and passes `--probe "$PROBE"` on the trainer line. That is the launcher's complete K1 diff (header note, one variable, one guard, one flag).

This supersedes build-package §5's "surfaced sub-item" (the retained Fai probe). That retention is withdrawn; the manifest records the Gravy probe's hash instead.

### K1.4 Probe hash — TO BE BUILT (the fill-in slot)

At this draft's writing, stage 1 is in its opening minutes: mirror_self stood at **285 / 2,400 games** (batch 1 started 14:59:36 EDT, count read 15:03 EDT, from `games_w*.jsonl`). The probe file therefore does not exist yet, by construction:

> **Probe file:** `probe/probe_gravy_v1.jsonl` — **sha256: TO BE BUILT** via the §K1.3 invocation when mirror_self completes. The resulting hash is recorded here by a one-line builder note and in the stage-3 launch manifest before stage 3 starts; a recomputation mismatch at manifest time voids the build and it is rebuilt, not explained.

Build-verification evidence that the builder is correct *before* the corpus exists is in §V.2.

---

## K2 — the Gravy tree CARRIES the abort-logging patch (reversal)

Build-package §6 decided the Gravy tree would not carry the abort patch, on a comparability argument. Claude's K2 reverses that decision: his round-4 reply registered, under §3, that **"for any future fleet, Decide must catch its own exceptions and log the abort reason at the marker"** — a standing registration the build draft's §6 contradicted. The patch changes no pick, margin, selection or validity logic; it is fleet-proven (the O fleet ran on it); and a new hero is where new abort classes are likeliest. **The tree is built from `/tmp/otree`.** The §6 text below replaces build-package §6 in full.

> ## 6. Stage 4 — the Gravy gate tree
>
> **Build (registered):** copy the **O tree** (the abort-patched lineage) and substitute the arm:
> ```
> cp -r /tmp/otree /tmp/gravytree
> # verify inside /tmp/gravytree:
> #   rl/search_server.py == ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c
> #   search.php          == 8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61
> #   featurize.php       == f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92
> # then ONE substitution: probe_swap20.php line 17's bootstrap deck
> #   decks/nats2026_ashlyn_fai_60.txt -> decks/nats2026_eriksen_gravy_60.txt
> # (analysis copy only; the fleet machinery takes its deck from
> #  paired_driver.py --deck, which the runner passes explicitly)
> ```
> (The three hashes above were re-verified on the box against `/tmp/otree` at follow-up drafting, 2026-10-21; `probe_swap20.php` in the O tree is sha256 `6993ece4f84bf2aea3540635c5b1cd8b2f0c9a787c0ed42cf426d4a3f8160243`, with the Fai bootstrap deck at line 17, as in the gate tree.)
>
> **The abort-logging patch is carried** (`search.php` = `8f6b35da…`, the O build): per the round-4 standing registration, Decide catches its own exceptions and logs the abort reason at the marker. This paragraph replaces the build draft's contrary decision and its justification; the registration governs. The marker rows the patch can produce are handled in the audit under the K5 rule (§K5 below).
>
> **What changes vs the Fai gate tree:** the tree's source (the O tree — gate lineage plus the abort patch — instead of `/tmp/gatetree_r4`), the served model (the C4-selected Gravy checkpoint, passed as `SEARCH_MODEL` by the runner), the deck (runner-passed), output/run names (`run_gravy_gate.sh`, out `/tmp/ggate`, sockets `/tmp/ggate_s{1,2}.sock`), the fleet seeds (§7), and the one-line L2 bootstrap deck above. **What is byte-identical to the Fai gate tree's machinery:** the patched server build (ab85fa1b…), `featurize.php` (f81193e0… — **current** featurizer; Flag 1), `paired_driver.py`, `gate_raw_retry.py`, the label machinery, and the vendor engine. The teacher's constants (k=25, overturn 1.5 paired SE, top-3 + prior ≥ 0.10 cap 4, continuation va) ride inside `search.php` as in the O build — the same file the O fleet converted on, plus no other change.
>
> **Census diagnostic (§5) is unaffected:** it scratch-copies `/tmp/gatetree_r4`, and bridge mode does not load `search.php`, so its `search.php == 6cd6f980…` tree guard stays exactly as written (per Claude's K2 note).
>
> **Runner enforcement:** the updated `code/run_gravy_gate.sh` pins the three tree hashes itself (guard block before any server starts or any output is created), so a stale or wrong tree aborts the launch mechanically.

---

## K3 — the pre-gate is ghost vs raw (replacement)

Build-package §7's pre-gate paragraph described "raw arm, Gravy tree vs the plain bridge on the production build" — a raw-vs-raw comparison across trees, which tests neither the machinery nor anything the registration asks about. The registered pre-gate (rounds 3 and 4) is **ghost vs raw**: the full teacher machinery with its pick forced to the prior's, against the plain bridge, on the same seeds. The paragraph below replaces build-package §7's pre-gate paragraph in full.

> **Pre-gate (registered):** 20 units — seeds **8501–8510 × both seats** — on the Gravy tree, against the fleet's per-seat servers (the tree's patched servers with `SEARCH_MODEL` = the C4-selected checkpoint, started by the launch wrapper before the chunks):
>
> - **Ghost arm** (`paired_driver.py --arm ghost`): the driver sets `TEACHER_MODE=1` + **`TEACHER_GHOST=1`** (`paired_driver.py:245`; arm documented at `paired_driver.py:11` — "full machinery, pick forced to the prior's; must be action-identical to raw"). Inside Decide (O build, `search.php:1029`), after the full machinery — candidate generation, rollouts, the paired overturn test — has computed its pick, the ghost block replaces it: `$pick = $priorPick; $overturn = 0;`, recording `ghost_would_pick` / `ghost_would_overturn` at the marker and stamping the stat row's rule `ghost_prior` (`search.php:1187`). Nothing else about the machinery changes.
> - **Raw arm** (`paired_driver.py --arm raw`): the plain bridge, no search.
> - **Pass = trace-level equality on all 20 units** (the round-3 standard): per unit, the ghost game's gamelog sha256 (the driver records it on every row, for exactly this cross-arm comparison) equals the raw game's, and the decision traces agree. Any non-IDENTICAL unit **stops the fleet**. The sole exception is a divergence attributable to the K5 marker class (§K5): a trace difference consisting of the pick-null abort marker row, disposed of by the K5 reclassification procedure — anything else is a stop.
> - **Raw self-pairing control (alongside, 10 units):** seeds 8501–8510, seat 1, `--arm raw` run a second time against the same server. The control pairs are expected to **differ** on all 10 units (the O pre-gate's control read 10/10 differ): the bridge's play is not a deterministic replay, so identical control traces would mean the comparison cannot see differences. An identical control pair stops the pre-gate as a machinery question — reported, not read past.
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
> # control, seat 1 only: a second raw run, same seeds
> $PY paired_driver.py --tree /tmp/gravytree --sock /tmp/ggate_s1.sock \
>   --seat 1 --arm raw --seeds 8501-8510 --timeout $GATE_TIMEOUT \
>   --deck $G60 --out /tmp/ggate/pregate_rawctl_s1.jsonl \
>   --logdir /tmp/ggate/pregate_rawctl_s1_log
> ```

---

## K4 — stop (e) restated: the calibration void pattern

Build-package §7's stop (e) read "the calibration void pattern (predicted-vs-actual empty in two or more of the top bins, as in the round-2 addendum trigger list)". That is not the registered pattern (Claude's K4). The item below replaces stop (e) in §7's stops list in full; stops (a)–(d) are unchanged.

> - **(e)** the **calibration void pattern** — the October signature: in the G5 calibration read (the prior pick's rollout-predicted win rate against realized outcomes, binned by decision ordinal), the **prediction climbs with decision ordinal and runs *ahead of* realized outcomes**. Honest runs sit at or below outcomes, as both the Fai gate and the O fleet did. A fleet showing the climb-and-ahead pattern is void under this stop, regardless of Δ.

---

## K5 — the DUP_SEQ rule, stated precisely

Build-package §7's G3 paragraph carried the sentence "the O fleet's re-classification precedent (DUP_SEQ-class rows are legal game differences, not machinery defects) is the standing rule". That overstates the precedent (Claude's K5). The sentence is replaced by the rule below, in full:

> In the G3 first-divergence census, a unit classified **DUP_SEQ is a machinery defect unless both** of the following hold: **(1)** the unit's extra row is the **pick-null teacher marker** — a trace row with rule `teacher`, no pick (`decide_pick` / `chosen` null), carrying an `abort_reason` field (possible because the Gravy tree carries the abort-logging patch, §K2); **and (2)** removing **only** that marker row makes the stock classifier (`classify_divergence.py`) reclassify the unit as **LEGAL**, under the O fleet's recheck procedure (the `o_dupseq_recheck` pattern), whose output ships with the audit. **Any other DUP_SEQ unit is a defect under stop (a) and stops the read.** (At the Fai gate this class never arose; in the O fleet all 5 DUP_SEQ units met both conditions and reclassified LEGAL — that is the precedent, stated at its actual scope.)

---

## What changes vs dd4cb2fe (consolidated)

1. **§5 probe:** the retained Fai probe set is replaced by the Gravy probe built under the Fai recipe (K1). New code `code/build_gravy_probe.py`; `code/gravy_ppo_launch.sh` updated (probe variable + guard + `--probe` flag). `code/patch_trainer_launch.py` unchanged — the repoint is a launcher argument, not a code change.
2. **§6 tree:** source `/tmp/gatetree_r4` → `/tmp/otree`; `search.php` expectation `6cd6f980…` → `8f6b35da…` (abort patch CARRIED — the build draft's contrary decision is reversed); `code/run_gravy_gate.sh` updated (header + the K2 tree-hash guard block).
3. **§5 census diagnostic:** unchanged (its tree source and `search.php` guard stay as written, per K2's note).
4. **§7 pre-gate:** replaced — ghost vs raw, 20 units, trace-level equality, raw self-pairing control alongside (K3). The build draft's raw-vs-plain-bridge description is withdrawn.
5. **§7 stop (e):** replaced with the registered calibration void pattern (K4).
6. **§7 G3 paragraph:** the DUP_SEQ sentence replaced by the two-condition rule (K5).
7. **Nothing else changes.** C1–C5, the C4 selection protocol, the anchor stop, the stage structure, seeds, and ETAs stand as approved/drafted. `build-package.md` itself is not edited.

---

## V. Build verification (what was actually run, 2026-10-21)

**V.1 Hashes and records read from the box (read-only):**
- HEAD via the git ref: `f1bed8d13a5811148dbf90df7e4262137a57b35e`.
- `/tmp/otree`: `search.php` = `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` ✓ (the abort-patched build, as K2 requires); `featurize.php` = `f81193e0…` ✓; `rl/search_server.py` = `ab85fa1b…` ✓; `probe_swap20.php` = `6993ece4…` ✓ with the Fai bootstrap deck at line 17 ✓.
- Probe recipe records: `probe/build.log` (the four lines quoted in §K1.1); `probe_kl.py` sha256 `0c251521…`; `probe/probe_v1.jsonl` = 27,000 lines, sha256 `974fef83…` ✓; `rl/trainer_v4.py` Gate defaults `subset=4096, seed=20261016` and the unoverridden call site read directly from source.
- Ghost switch: `TEACHER_GHOST` located in `/tmp/otree/search.php:1029` (the forcing block) and `:1187` (the `ghost_prior` rule stamp), and in `/tmp/otree/paired_driver.py:11` (arm doc) + `:245` (env set for `--arm ghost`).

**V.2 K1 builder, mechanics-tested in scratch (no Gravy data touched):**
- `py_compile` clean. Run against the real Fai mirror corpus (`bc2_train_data/mirror`, read-only) with `--per-corpus 50` and scratch out: `probe_kl.py` kept 50, the script's independent re-scan reproduced the kept sequence, printed `PROBE_STATES 50` / `PROBE_SHA256 db1082e2…`. A third, hand-written filter computation in the test harness matched the file's first 3 kept records exactly — (`956417877`, decisions 5 / 27 / 59).
- Negative test: `--expect-games 999999` → aborts on the game-count guard, no file written. (The Fai-era corpus dir holds no `games_w*.jsonl` — its count reads 0 and was passed as such; the Gravy driver's batches do write `games_w*.jsonl`, and the live mirror_self count was read from them for §K1.4.)
- Refusal-to-overwrite and short-yield aborts are in the code path as written; the short-yield branch was not exercised live (no corpus in reach yields short at cap 50).

**V.3 Updated launchers, guard dry-runs (from the staging copies; no workers, servers, directories or files created in any dry-run):**
- `bash -n` clean on both updated scripts.
- `gravy_ppo_launch.sh` with no env → exit 1, "stage-2 anchor stop not cleared" (the approved guard, unchanged). With `GRAVY_STAGE2_CLEARED=1` → exit 1, "Gravy KL probe missing: …/probe/probe_gravy_v1.jsonl" (the new K1 guard, firing before the anchor guard and before `mkdir`).
- `run_gravy_gate.sh` with no env → exits naming `GRAVY_MODEL` (the registered dry-run behavior). With model/timeout set and `GATE_TREE` pointed at a scratch tree holding a wrong-hash `search.php` → exit 1, "search.php (abort-patched build, follow-up K2) hash mismatch", with the scratch `GATE_OUT` directory **not created** (guards precede `mkdir`). The guard's three expected hashes were each confirmed against the real `/tmp/otree` files in §V.1.

**V.4 Stage-1 status at drafting:** stage 1 running (driver log: batch 1 mirror_self started Wed Oct 21 14:59:36 EDT); mirror_self at **285 / 2,400 games** at 15:03 EDT. The K1 probe build is therefore pending the corpus by construction — §K1.4 is the fill-in slot, and the builder is verified ready (§V.2).

**Stated as unverifiable at draft time:** the Gravy probe file and its hash (pending mirror_self, §K1.4); the Gravy tree itself (built at stage 4 under §K2's registered text; its source hashes are verified, the copy is not yet made); the pre-gate/control behavior on Gravy (a stage-5 launch read, registered in §K3, not a build claim).

---

*Builder: Muse (for Joe Slattery), 2026-10-21. Review venue: this repository. Joe relays; Claude reviews; stage 3 and later launch only on Claude's approval of this follow-up at its committed sha (with the K1 hash filled in) plus Joe's go in chat.*
