# Round 4 — O-package (DRAFT): the unmodeled-opponent measurement

**Parent:** 0d1dfcd78cdab97f259fd7679a3a740425c18bee (HEAD at writing; read via the git ref, equal to origin/main)
**Answers:** §5 of `rounds/round3/claude-reply-38dd581.md` (requirements O1–O8), plus the abort-logging requirement in its §3.
**Status: DRAFT for review. Nothing in this package is launched.** Launch requires (i) Claude's approval of this package at its committed sha and (ii) Joe's explicit go in chat — the standing hub rule. This draft was built with no commits, no tree builds on the box beyond a scratch patch check (§8), no probe games, no fleets.

**Package contents**

| File | Role |
|---|---|
| `o-package.md` | this design + registration |
| `code/run_o_fleet.sh` | the fleet runner (O1/O2/O4/O7 mechanics) |
| `code/patch_decide_abort_log.py` | the §3 abort-reason logging patch (O7) |
| `code/analyze_gate.py` + `code/test_analyze_gate.py` | primary paired analysis, unchanged from round 3 (O8) |
| `code/l1_check.py`, `code/l1_cuts.py`, `code/l1_phase.py` | L1 census (O5) |
| `code/probe_swap20.php` | L2 swap runner (O5) |
| `code/audit_overturns.py` | L3 job emission (O5) |
| `code/analyze_l3.py` | L3 scoring (O5, O8) |

The gate's `gate_raw_retry.py` is **reused unchanged** (not copied): it re-runs raw-arm timeout rows against the same per-seat sockets, and the opponent lives in the server's environment, so there is no opponent-aware retry change to make. It ships in the O tree as part of the tree copy.

---

## 1. Design (O1)

**Matchup.** Teacher vs raw v15, paired seeds, both seats, both arms against the same opponent, on the mirror Fai 60 deck (`decks/nats2026_ashlyn_fai_60.txt` both seats — the deck is held constant exactly as in the gate, so the only changed variable is the opponent).

**The teacher is exactly the gate artifact:** TEACHER_MODE=1 plain — k=25 shared determinized worlds, selection top-3 by prior + any prior ≥ 0.10 (cap 4), continuation `va`, overturn iff paired mean margin > 1.5 × paired SE on ≥ 20 shared finished worlds, R17 root state (the bridge's own featurization). No parameter changes.

**The opponent is BC2:** `/home/joe/tcg/tcg-sim/bc2_out/bc_policy.pt`, sha256 **b22739d1f52862b192b0f3bc179d4027f114507773b4274ce4b950fb4cb78d0d** (read from the box at drafting). BC2 is out-of-sample to v15 and a different policy family from the heuristic — the registered primary. **The v15-mirror secondary is NOT registered.** That choice is made here, at registration, per O1: BC2 only. A mirror measurement would need its own later registration.

**Serving (O2 mechanics).** One patched server per seat (the gate pattern), started with `TCG_OPP_MIX=ckptpath:/home/joe/tcg/tcg-sim/bc2_out/bc_policy.pt:1.0` and `SEARCH_MODEL` = v15 (sha256 0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c). R12 seat checks stay in force: every bridge request names its learner seat and a mis-seated server rejects loudly.

**Why the teacher's model is misspecified by construction.** This is the point of the test, so the mechanism is stated exactly, from the gate build's code:

- *Live opponent decisions* route through the server. In a live game, both seats' candidate choices funnel through `SimPolicyServer_Choose` → `SimPolicyServer_Query` with the deciding `player` stamped on the request. The patched server's `answer_normal` routes by that field: `player == LEARNER_SEAT` → v15 argmax; otherwise, with an opponent net loaded, → **BC2 argmax**. So the live opponent across the table is BC2, for both arms, in both seats.
- *Rollout decisions never touch the opponent model.* SimTeacher_Decide runs its worlds through `SimLabel_RunRollout`; inside a child, `SimLabel_ChildChoose` decides as follows: the root (learner) seat queries `SimSearch_Eval` — `mode:"eval"` requests, which the server answers from `forward_batch`, the **learner model only** (eval requests carry no player field at all; OPP_MODEL is referenced in exactly two server code paths, its startup load and `answer_normal`). The non-root seat — the opponent inside the teacher's imagination — is played by `SimLabel_V1Argmax`: the **in-process v1 heuristic** scores. The child never issues a pick request.
- Therefore changing `TCG_OPP_MIX` changes only who actually sits across the table. The teacher keeps planning against the heuristic it has always modeled. Δ (teacher − raw, same BC2 opponent for both arms) measures how much of the teacher's edge survives a wrong opponent model.

## 2. Server manifest (O2) — the startup lines exist

O2 requires the manifest to quote both models' startup lines. **Finding: the patched server logs both.** At startup it prints, for the learner, `search_server: search model loaded (<path>) on <device>`, and — whenever `TCG_OPP_MIX` begins with `ckptpath:` — `search_server: opp net loaded (<path>)` for the opponent (gate-tree `rl/search_server.py`, the load block after the learner load). No substitute evidence is needed.

`run_o_fleet.sh` captures, before the first chunk starts, into `o_server_lines.txt`: both lines from **both** server logs, plus the sha256 of the BC2 file and of the v15 file. **The script hard-stops (exit 1) if `opp net loaded` is absent.** A missing opp line would mean the fleet is about to measure the heuristic while calling it BC2 — the silent-substitution failure this project has been burned by before; the launch does not proceed on a missing line, full stop.

## 3. Pre-gate (O3) — launch-phase step, registered here

Before any fleet game, on the launch tree (gate build + §7 patch):

- Instrument: `paired_driver.py --arm ghost` vs `--arm raw`, seeds **4001–4010** (outside every registered range), **both seats**, against per-seat servers started with the fleet's exact `TCG_OPP_MIX` — 20 (seed, seat) units, traces on.
- Comparison: `r3_pair.py` trace-level pairing, the round-3 pre-gate standard, with the standing raw-control pairing (raw vs a second raw run) to prove the comparison can see differences.
- **Pass: all 20 units trace-identical.** The one standing exception is the amended G3 marker rule from the gate: a DUP_SEQ whose extra row is the state-less teacher marker is reclassified after removing only the marker row — and under the §7 patch that marker now carries `abort_reason`, so the exception explains itself on its face. Any other divergence class, or a seat_mismatch / connect_failed anywhere, is a FAIL: no fleet, and the failure is packaged before anything else moves.

Why this gate exists: the opponent's decisions now traverse the server pick path in live games — a code path the heuristic's in-process play never exercised — so ghost==raw must be re-proven against it, not inherited from the heuristic pre-gate.

## 4. Fleet (O4)

`code/run_o_fleet.sh`: seeds **2001–2200**, four chunks of 50 (c1 2001–2050, c2 2051–2100, c3 2101–2150, c4 2151–2200), every seed at both seats and both arms — 400 (seed, seat) units, 800 games. Same discipline as the gate runner: chunk pids recorded and waited (never a bare `wait`), EXIT trap backstop, per-seat servers reaped explicitly, TEACHER_SNAP_DIR on the teacher arms (L3 snapshots), traces on both arms, `TCG_CLEAN_CHILDREN=1`, per-chunk game-id files, per-chunk manifests with `assert_ok`, `seat_ok` stamped on every row by the driver.

**Timeout:** launch-phase probe — 4 concurrent teacher games on out-of-range seeds (4011–4014) under BC2-opponent fleet contention — then `O_TIMEOUT = max(700, 3 × slowest probe game)`, the gate's §2 formula carried verbatim (the gate's 1600s was set the same way from a 518.6s probe). Scoring of timeouts follows the carried rulings: engine caps score 0.5 both seats; teacher wall-clock timeout = teacher loss (primary) with the dropped-pairs sensitivity, and teacher timeouts > 2% of teacher games make the read INCONCLUSIVE; a raw timeout is re-run once, a second hang scores raw 0.5 and keeps the pair.

## 5. Reads (O5) — registered before any game

**Primary** (`analyze_gate.py`, unchanged): paired Δ = teacher − raw per seat and pooled, bootstrap CI clustered by seed (B=10000, script seed 20261019 as coded), discordant counts with the exact sign test, per-arm timeout/cap accounting.

**Bands — the heuristic gate's, verbatim:**

| Result | Read |
|---|---|
| Δ ≥ +0.05 with CI lower > 0 | **Converts under misspecification** — the gain survives a wrong opponent model |
| CI lower > 0 but Δ < +0.05 | Real but small; reconsider cost (372 s/game) |
| CI includes 0 with upper < ~+0.10 | The heuristic Δ was exploitation of the known opponent; the general-strength claim does not survive |
| Δ > +0.20 | **IMPEACH BEFORE READING** — audit first, exactly as the gate |
| Teacher timeouts > 2% | INCONCLUSIVE regardless of Δ |

**L1, L2, L3 are standard parts of this analysis** — run with the primary, not as post-hoc audits:

- **L1 (unanimity census)** on the O fleet's teacher stat files, the gate's spec exactly: fraction of overturn rows whose prior pick / overturn pick 25 worlds are unanimous (±1), and the count of `se_diff == 0` overturns. **Fail: > 50% of overturn rows unanimous, or the zero-SE overturns not concentrated in late turns** → stop; information leak is the leading hypothesis.
- **L2 (swap test)** on 20 of the O fleet's overturn snapshots, sampled by `audit_overturns.py --sample 20 --seed 20261021` (fresh seed, registered here; the gate's was 20261019). Pass = identical rollout results on all checks (both picks run, 40 checks; an errored or empty arm is a FAIL by construction).
- **L3 (overturn audit)** on **all** O-fleet overturns, k=50 fresh worlds, CRN across the two picks, continuation **`va`** — the same misspecified continuation the teacher used, as O5 requires. Fresh seed bases registered here: **555001 + shard×10⁸** (the gate's were the 777001 family; no overlap). Primary statistic: mean paired difference (overturn − prior, win probability) with the game-clustered bootstrap CI (`analyze_l3.py`, bootstrap seed 20261020 as coded). Secondary: fraction-better. Also reported: expected per-game gain (mean difference × overturns per teacher game) against the O fleet's own Δ. **Read: L1 + L2 clean and the CI lower bound > 0 → the overturns carry real value against BC2 under the teacher's own model; CI includes 0 → the overturn signal does not survive the opponent change, whatever Δ says, and Δ is reported unexplained.**

**Diagnostic L3 (O5, diagnostic only)** — a second labeling of the same jobs with the **true opponent as continuation** (§6). It is reported alongside the primary L3 and **never** enters the conversion read. It prices the misspecification: (primary L3 mean difference) − (diagnostic mean difference) is what planning against the heuristic instead of BC2 cost the overturn evaluations, on the same snapshots and worlds discipline.

## 6. Diagnostic L3 — feasibility and specification (not built in this draft)

**Feasibility finding.** BC2 is a torch checkpoint; PHP has no way to run it in-process, so an in-process BC2 continuation (option b) does not exist. But **no new server request type is needed either**: the server's existing pick endpoint already routes by the request's `player` field to the opponent model's argmax (`answer_normal`), which is the *identical* code path the live BC2 opponent plays through in the fleet itself. The diagnostic is therefore a PHP-side labeler change only — server untouched:

1. **New pair code `vb`** (root continuation = v15 prior-argmax, as `va`; opponent continuation = BC2 argmax via the pick endpoint), alongside the existing `va`/`vv` handling in `SimLabel_ChildChoose` and `SimLabel_ChildDQ`.
2. In both functions, when the pair is `vb` and the deciding player is **not** the root player, the choice is obtained by a `SimPolicyServer_Query` pick request — payload `{v:1, game, decision, branch, player: <deciding player>, state: <the masked state already built for that player>, candidates: candRecs, gate_pass: true}` — and the returned `action_index` selects the candidate. On transport failure (null), fall back to `SimLabel_V1Argmax` **and count it** in `ssLabelFallbacks` (the counter the label rows already surface): any diagnostic job with fallbacks > 0 is tainted, counted, and reported; the diagnostic read is quoted with its tainted-job count, mirroring the fidelity rule that a nonzero fallback count invalidates a batch.
3. **Seat discipline.** Pick requests carry the R12 `learner_seat` stamp from the PHP process env, so the diagnostic labeler runs against the **patched** servers (one per seat, `TCG_OPP_MIX=ckptpath:` BC2) with jobs **split by root seat** — seat-1 snapshots labeled against the seat-1 server, seat-2 against seat-2 — the fleet's own per-seat discipline. (The gate's primary L3 used the production server because the label path's eval requests carry seat 0; the diagnostic's pick requests make the patched server mandatory, and the seat split is what keeps R12 green.)
4. **Driver:** `meas_label_main.php` currently hardcodes `"pair" => "va"` in the label config; the diagnostic build reads the pair from env (`LABEL_PAIR`, default `va`). `audit_overturns.py` jobs are pair-free and unchanged. Seed bases for the diagnostic: **955001 + shard×10⁸**, distinct from the primary's, so diagnostic worlds never coincide with primary worlds.
5. **Scope/size:** same job set as the primary L3 (all O-fleet overturns), k=50. Cost note: pick requests are single unbatched round-trips while eval requests batch, and roughly half of rollout decisions are the opponent's — expect the diagnostic to run materially slower per world than the primary (the gate's primary took ~50 minutes for 91,500 rollouts; budget 2–3× per rollout and measure at the launch timing probe).

**Not built here.** The two small patch scripts this needs (`patch_label_opp_continuation.py` for the `vb` branches; `patch_meas_label_pair.py` for the env pair) are specified above, not written. Reason: they touch `SimLabel_ChildChoose`/`ChildDQ` — the same functions the *primary* L3 runs on. Building them unreviewed inside this draft would put unreviewed code one env flag away from the primary measurement. They belong in the launch-phase tree build, reviewed with this package's approval, where the primary path stays `va`-only until they land.

## 7. Abort-reason logging (O7 carry-over; reply §3 requirement)

`code/patch_decide_abort_log.py`, in canonical patch form (anchor-asserted, count==1 per anchor). It applies to the gate build's `search.php` (sha256 6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a) and is the **only** code delta between the gate tree and the O tree.

What it does (detail in the script's docstring):

- `SimTeacher_Decide` becomes a thin wrapper; the gate body is renamed `SimTeacher_DecideInner`, byte-identical. The wrapper resets a reason global, and on any escaping Throwable records `exception:<class>:<message>`, writes a stat row for the aborted decision (reason, branch, player, turn, **game**), and returns null — the registered bridge fall-through.
- The root-eval canary throw inside Decide gets its own reason (`root_eval_canary:…`), distinct from an eval transport failure (`root_eval_failed`).
- The eval-null stat row — which in the gate build carried only `{teacher, fallback, branch}` — gains `abort_reason`, `player`, `turn`, `game`.
- `SimSearch_RootDecide` stamps `abort_reason` on the marker trace row (rule=teacher, pick null).

The motivating record, from the fleet's own files (game 397753742, seq 33): RootDecide's eval of the bridge state succeeded (priors_pre present); Decide's eval of the *same* state returned null (priors_post null, feat_post_hash == feat_pre_hash, so the trace stash was set before the eval); and the stat row the null exit wrote was anonymous — no game, no turn, no cause. Eight such decisions occurred; the accepted explanation (eval/child timeouts under 4-way contention) is consistent with that anatomy — two evals of one state, back to back, the second failing — and the patch is what makes the next occurrence self-explaining instead of consistent-after-the-fact.

No pick, margin, selection, or validity logic changes. The canary doctrine is untouched: Choose's own canary on the same state runs uncaught before RootDecide, and the R14 root canary runs before Decide — both still fail loud exactly as before; the wrapper only sees exceptions from code Decide itself runs.

**Scratch verification (this draft, on the box):** patch applied to a fresh copy of the gate `search.php` in a scratch dir — before sha256 6cd6f9802bde5f40631131d2f98af110978a761f9dacf423622f92d7ca55067a → after **8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61**; `php -l` clean; the full-file diff against the gate build is **5 hunks / 49 changed lines**, all at the four patch sites; the gate tree and the production server were re-hashed afterward and are unchanged (6cd6f980… and 81ef2cdb…). The O tree at launch = fresh copy of the gate tree + this patch, and the launch wrapper verifies `search.php` == 8f6b35da… before the pre-gate.

## 8. Carry-overs (O7) and cost

- **G8 sweep before launch.** Box shared-memory count at drafting: **1,816 segments** (`ipcs -m | wc -l`, read 2026-10-20; kernel.shmmni = 4096). The launch phase sweeps stale segments under the gate's criteria (nattch=0, no live process) before the pre-gate, and the **3,600 operator stop** applies throughout the fleet: the operator reads the count at least hourly; above 3,600 the fleet is stopped and the run is INCONCLUSIVE, not partially readable.
- **Production integrity:** `rl/search_server.py` sha256 recorded before and after the fleet by the runner (expected 81ef2cdb… both sides; the fleet uses tree servers only).
- **Registry before analysis:** per-chunk game-id files are merged into the do-not-train registry before any analysis runs; `analyze_gate.py` refuses to run on unregistered games (its G9 gate). The L3 snapshots are registered eval-only with the same merge, as in the gate.
- **Manifests:** every chunk manifest must read `assert_ok` TRUE and every row carry `seat_ok`; any exception stops the read, per the gate's discipline.
- **Cost (gate record):** teacher 372.1 s mean per game (median 370.7) vs raw 3.8 s against the heuristic; the gate fleet ran 800 games in ~10.6 h (17:01 → 03:40 EDT). Against BC2 the game lengths will move — BC2 held v15 to 0.490 in the round-robin (vs 0.505 against the heuristic) and its games have a different shape — so **~10.6 h is a planning anchor only**; the binding ETA is re-measured by the O4 contention probe at launch, and the fleet estimate is restated from the probe before the go/no-go, per the calibration lesson the gate's first ETA taught.

## 9. Analysis code inventory (O8)

Byte-identical copies of the round-3 files unless flagged; roles and the deltas the O analysis needs:

- **`analyze_gate.py`** — primary paired analysis. **Verified opponent-agnostic by full read:** pairing, scoring, the timeout rulings, the bootstrap and the bands key only on row fields (seed, seat, arm, winner, invalid, capped); nothing in the computation names the opponent. Two cosmetic flags: the docstring says "both against the heuristic" and the overturn-rate monitor prints "(expect ~5%)" (the gate's heuristic-era rate; against BC2 the rate is whatever it is — the number is reported, the expectation is not a check). The report header will read "GATE ANALYSIS" — cosmetic. Copy is byte-identical to the reviewed round-3 file (sha256 a5e2086677a69c6055a4…, both copies).
- **`test_analyze_gate.py`** — its fixture test. Passes on this copy (§10).
- **`l1_check.py` / `l1_cuts.py` / `l1_phase.py`** — L1 census. **Flag:** each globs the gate's output path (`/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl`). At O analysis time the glob becomes `/tmp/o_fleet/o_c*_teacher_*_log/search_stats.jsonl` — a one-line path edit per script, made then and disclosed in the results package; the census logic is untouched.
- **`probe_swap20.php`** — L2 runner, env-parameterized already (SWAP_JOBS / SWAP_IDX / SWAP_OUT); no changes. Its `DeleteCache` guard and errored-arm-is-FAIL rule carry over.
- **`audit_overturns.py`** — L3 job emission from the O fleet's stat files + snapshot indexes. Registered uses: primary emission with cap 100000 (all overturns); L2 sample `--sample 20 --seed 20261021`; diagnostic emission = the same full job file as the primary.
- **`analyze_l3.py`** — L3 scoring. Self-test passes (§10). **Flag:** its `DELTA` constant (0.2525) and the printed read block are the *heuristic gate's* — for the O fleet, read `mean_diff`, its CI, the fractions, and `per_game_gain` from the JSON output and apply §5's reads with the O fleet's own Δ; the constant does not enter the computation (the aggregation, pairing and bootstrap are what the self-test covers, and they are Δ-free). `TEACHER_GAMES = 400` matches the O fleet's teacher game count (200 seeds × 2 seats) by design. Its bootstrap seed (20261020) stands.

## 10. Build verification — what was actually run for this draft

- **Abort patch:** applied to a scratch copy of the gate `search.php` on the box; 4 edits, all anchors unique; `php -l` — no syntax errors; full-file diff vs the gate build = 5 hunks / 49 lines at the patch sites only; post-patch sha256 8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61. Gate tree re-hashed unchanged (6cd6f980…); production server re-hashed unchanged (81ef2cdb…).
- **Server code reads** (gate tree, for §§1–2 and §6): the `TCG_OPP_MIX` parse and the `opp net loaded` startup print; `answer_normal`'s player-field routing to OPP_MODEL; `forward_batch` answering evals from the learner model only; the R12 seat assertion in the connection handler.
- **PHP code reads** (gate tree): `SimPolicyServer_Choose`/`SimPolicyServer_Query` (player stamp, R12 stamp, bridge fall-through on null); `SimSearch_RootDecide`'s teacher dispatch and marker row; `SimTeacher_Decide` end-to-end; `SimLabel_ChildChoose`/`SimLabel_ChildDQ` pair semantics (`va`: root seat net-argmax via eval, non-root seats `SimLabel_V1Argmax`); one real marker row read from the gate traces (game 397753742, seq 33).
- **Fixture tests on the staging copies (local):** `python3 test_analyze_gate.py` → **FIXTURE TEST: PASS (all checks)**, exit 0. `python3 analyze_l3.py --self-test` → **SELF-TEST PASS**, exit 0. `bash -n run_o_fleet.sh` → syntax OK.
- **Direct reads:** BC2 weights sha256 b22739d1f52862b192b0f3bc179d4027f114507773b4274ce4b950fb4cb78d0d; v15 weights sha256 0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c; box `ipcs -m | wc -l` = 1,816; repo HEAD 0d1dfcd78cdab97f259fd7679a3a740425c18bee.
- **Not run (by design):** no O tree build, no pre-gate, no contention probe, no diagnostic patch scripts (§6 spec only), no games of any kind.

**Ask:** approval of the design and registrations above (O1–O8 as instantiated), including the §6 diagnostic specification and the §9 flags; on approval + Joe's go, the launch phase builds the O tree (gate copy + §7 patch, hash-verified), runs the G8 sweep, the O3 pre-gate and the O4 probe, restates the timeout and ETA from the probe, and only then starts the fleet.
