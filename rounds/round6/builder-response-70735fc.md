# Round 6 — pick-flip results: the ARS blind spot changes zero picks in 163 disagreeing decisions

**Parent:** 70735fcf5cd5477f2e77b98979e18f1323b191cc (HEAD at launch; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round6/claude-reply-1a3267f.md` — the approval of the round-6 pick-flip package at sha 1a3267f3, with its §2 resolution note on the registered read and its §3 reporting additions.
**Status: the run is complete and reconciled. The registered read is applied in §4 in the resolution's exact recorded wording.** Nothing was launched for this package beyond the approved run: the 40 census games replayed in the flip tree with the dual-featurization probe, the updated tally, and the §3.2 consistency check over the run's own trace files. No featurizer change, no re-evaluation, no training-run registration is made here.

**Package contents**

| File | Role |
|---|---|
| `builder-response-70735fc.md` | this results package |
| `code/tally_pickflip.py` | the tally, updated at the results stage with the §3.1 by-player sections (disclosed in §5; the pooled block is byte-unchanged and the fixture still pins it) |
| `data/pickflip/flip_s1.jsonl`, `flip_s2.jsonl` | the probe logs, 135 + 132 = 267 ARS rows |
| `data/pickflip/rows_s1.jsonl`, `rows_s2.jsonl` (+ `.manifest.json`) | the driver rows for the 40 games, both manifests `assert_ok` |
| `data/pickflip/server_s1.log`, `server_s2.log` | the two production-server logs (startup lines quoted in §1) |
| `data/pickflip/tally.txt` | the tally over the two flip logs |

---

## 1. Launch record

- **Approved sha:** 1a3267f3b7af93a19dcff85ef54716b2af9a9b94 (the pick-flip package). **Launched HEAD:** 70735fcf5cd5477f2e77b98979e18f1323b191cc — the diff against the approved sha is the single reply commit (rounds-only), as the launch gate allows. **Joe's go:** 2026-10-21 10:31 EDT.
- **Tree:** `/tmp/fliptree` rebuilt fresh from `/tmp/otree` plus the committed probe patch (transferred byte-identical, sha256 `34fa0701…`; the runner likewise, `0ab440ee…`). Hash guards verified before any game: `policy_server.php` = `c00befa98f6b4bb82318b51338f8ff86c8c74b2eb481acc8b106774c8c683fa0` (probe build), `featurize.php` = `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92` (O build, unchanged), `search.php` = `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` (O build, untouched); `php -l` clean on the patched file.
- **Run:** `run_pickflip.sh` as committed, production server (`/home/joe/tcg/tcg-sim/rl/search_server.py`, sha256 `81ef2cdb…` before **and** after the run — unchanged), `SEARCH_MODEL` = v15, seeds 6001–6020 learner seat 1 and 6021–6040 learner seat 2, mirror deck. Wall clock ≈ 10:33–10:35 EDT. Both servers were reaped by their recorded pids; a final process census shows zero `search_server.py` processes.
- **Seat check by hand (approval §3 discipline carried from round 5):** each phase's server log shows the v15 loaded line followed by its listening line, verbatim —
  - phase 1: `search_server: listening on /tmp/pickflip/flip_s1.sock (learner seat 1, opp heuristic)`
  - phase 2: `search_server: listening on /tmp/pickflip/flip_s2.sock (learner seat 2, opp heuristic)`
  Both match their phases. No phase was voided. (Driver rows read `server_seat: null`, as expected against the production server, which has no seat ping.)
- **Segment counts** (recorded in-script): **2,151 at start → 2,191 at end** (+40, the known +1-per-kept-game KEEP_GAME leak; no sweep needed at this scale).
- **The 40 game ids** (this run's engine-assigned ids, seed order): seat 1 — 6001:391720669, 6002:268478653, 6003:395939944, 6004:661369327, 6005:502500933, 6006:675875853, 6007:368135810, 6008:586964821, 6009:632491310, 6010:433727660, 6011:836670743, 6012:797017613, 6013:754362348, 6014:788221810, 6015:995768614, 6016:846082739, 6017:904743759, 6018:428361323, 6019:167967986, 6020:109506363; seat 2 — 6021:390290027, 6022:853627733, 6023:670359000, 6024:597815486, 6025:959192844, 6026:490208319, 6027:820125623, 6028:383511688, 6029:693922103, 6030:223776293, 6031:559164577, 6032:595962324, 6033:189048812, 6034:651789057, 6035:231950710, 6036:569025374, 6037:174005384, 6038:443936002, 6039:615663557, 6040:889326552.

## 2. Reconciliation (registered §5 — a mismatch is a machinery failure)

| Leg | Registered expectation | Observed | Verdict |
|---|---|---|---|
| (i) Flip-log ARS totals | 267 rows: 163 disagreeing, 104 agreeing | **267 rows** (135 seat-1 phase + 132 seat-2 phase), **163 disagreeing, 104 agreeing**, every row branch ARS, every row pick-bearing, 0 `eval_error` rows | **exact** |
| (ii) Per-game winners + decision counts vs the committed census rows | 40/40 | Winners, decision counts, capped flags, turn counts, and `gamelog_sha` match the committed census row files on **all 40 seeds**; `seat_mismatch_errors` 0 throughout | **match** |
| (iii) Kept gamelogs byte-compared vs the census run's kept games | identical if they persist | The census run's kept games persist under `/tmp/censustree/vendor/talishar/Games/`; matched by seed, **40/40 gamelogs byte-identical** (`cmp`-equivalent, full bytes) | **identical** |

One transparency note on (ii): the engine-assigned `gamename` differs between the two runs on all 40 seeds. The id is a per-run label assigned at game creation — it is not seed-derived, and the gamelog does not embed it (round-3 machinery note). Game identity across the runs is carried by the content fields: identical winners, decision counts, and full-gamelog hashes on every seed, settled byte-for-byte by leg (iii). Nothing in the registration rides on the id label.

## 3. Results

### 3.1 The tally (pooled; `data/pickflip/tally.txt`)

- Rows: **267** ARS featurizations, all pick-bearing; no-pick rows **0**; `eval_error` rows **0**.
- **Control (agreeing pick-bearing rows, n = 104): control flips 0, control prior mismatches 0.** The strong form of the control holds on the full sample, not just the smoke: every agreeing row's two evaluations returned identical prior vectors.
- **Disagreeing pick-bearing rows: n = 163. Flips: 0. Flip rate 0/163 = 0.000%, Wilson 95% [0.000%, 2.303%].**
- **Prior shift on the chosen candidate** (disagreeing rows): n = 163, **median 0.000000, p90 0.000008, max 0.002363**. Half the disagreeing decisions show literally zero movement in the played candidate's prior under the corrected deck picture; the largest movement anywhere is a quarter of one percent of prior mass.

### 3.2 By player (§3 addition 1)

| Deciding player | Rows | Agreeing (control flips / mismatches) | Disagreeing | Flips | Flip rate (Wilson 95%) | Prior shift median / p90 / max |
|---|---|---|---|---|---|---|
| 1 | 150 | 77 (0 / 0) | 73 | **0** | 0.000% [0.000%, 4.999%] | 0.000000 / 0.000020 / 0.001205 |
| 2 | 117 | 27 (0 / 0) | 90 | **0** | 0.000% [0.000%, 4.094%] | 0.000000 / 0.000001 / 0.002363 |

Zero flips for each player separately, not just pooled.

### 3.3 Learner-seat consistency check (§3 addition 2)

The played index **is** available without any code change: each game's trace file (in the run's `log_s<seat>/trace/`) carries the played candidate index as `chosen` on every decision row. Method: for each phase, learner-seat flip rows (`player` = the phase's learner seat) were joined to that game's trace rows on (game, ARS, player) — the flip log's `decision` counter is the trace's `seq`, so the join is by identity, not by position; the join was validated by turn equality on every pair (128/128) and by per-game ARS counts matching in all 40 games. All 128 learner-seat trace rows carry rule `bridge_pick`.

**Result: the current-state eval argmax equals the played pick on 128/128 learner-seat ARS rows (73 seat-1 phase + 55 seat-2 phase) — agreement 100%.** The eval path and the pick path are evaluating the same thing (the pick route's `net_argmax` over the same logits the eval endpoint softmaxes), so the flip reading is not undercut by a path divergence.

## 4. The registered reading, applied

The registration (package §6, from `claude-reply-f7e4534` §3) reads on the point estimate, with the approval's §2 resolution note: at n = 163 disagreeing rows, even zero flips leaves a Wilson upper bound above the 2% line, so an estimate at or below 2% with its bound above 2% is recorded in the resolution's wording.

- Point estimate: **0.000%** — at or below the 2% line.
- Wilson 95% upper bound: **2.303%** — above the 2% line.
- **Recorded read: the blind spot is "immaterial to play at this sample's resolution."**

The prior-shift distribution carries the rest of the evidence, as the resolution anticipated: the corrected deck counts do not merely fail to change any pick — they barely move v15's priors at these decisions at all (median shift exactly 0, p90 under one hundred-thousandth, worst case 0.0024). The blind spot is real as a representation (round 5: 61% of ARS featurizations omit a returned card) and inert as behavior for the current nets.

**Boundaries.** On this read, item (b) **closes for the bridge population**, as documented: the featurizer correction is folded into the *next* training run's registration, so training and serving change together — it is not applied to the current nets, for whom it would introduce the very train/serve mismatch round 5's §2 warned against. The > 2% branch does not fire, so no production-change registration opens. The teacher-root population remains a separate, open question, exactly as registered in round 5: the double-count direction (store > view) never occurs in bridge play, and the five root aborts were post-sync teacher states, which neither the census nor this run speaks for. This results package authorizes nothing beyond its own report.

## 5. Build verification — what was actually run

- **Tree build:** fresh copy of `/tmp/otree` → `/tmp/fliptree`, patch applied (2 edits OK; before `64c21539…` → after `c00befa9…`, reproducing §8's scratch values); the three tree hashes and the production hash verified from the box before the run; production hash re-verified after (unchanged).
- **Tally additions (§3.1):** the by-player sections were added to `tally_pickflip.py` at the results stage, as the approval specifies (no code change to the run; tally additions disclosed). The pooled block is byte-unchanged: a rerun of the updated tally on `code/fixture/flip_log_fixture.jsonl` reproduces `code/fixture/expected_tally.txt` **exactly** for the pooled section, and the appended by-player fixture output matches hand computation (player 1: 1 flip in 2 disagreeing rows, shifts median 0.050000 / p90 0.200000 / max 0.200000; player 2: 0 flips in 1, shift 0.100000).
- **Consistency check (§3.3):** computed from the committed flip logs and the run's trace files on the box (`/tmp/pickflip/log_s1/trace/`, `log_s2/trace/` — 20 files per phase, per the manifests); join keys and validation counts are stated in §3.3 so the check can be rerun against those files.
- **Data files** (all pulls sha256-verified byte-identical to the box): flip_s1.jsonl `599adaec…` (61,875 B), flip_s2.jsonl `d143ba9d…` (62,311 B), rows_s1.jsonl `9eff89c6…` (10,403 B), rows_s2.jsonl `c5bc0af7…` (10,401 B), rows_s1.jsonl.manifest.json `5cce8fad…`, rows_s2.jsonl.manifest.json `e2ce19de…`, server_s1.log `fe6ba665…`, server_s2.log `e74832f8…`, tally.txt `6ce2f43d…` (1,004 B).
- **One process note, for the record:** the runner session's first completion delivery reported final line counts (152 / 115) that did not match the box — when checked, the run was still in its second phase. Every number in this package was verified from the box files directly (final counts 135 / 132, pulled and hash-matched above); the delivery discrepancy is recorded here rather than smoothed over.

**Ask:** acceptance of the reconciliation (§2), the results (§3), and the recorded read in §4 — that item (b) closes for the bridge population at this sample's resolution, with the featurizer correction carried into the next training run's registration.
