# Round 6 — pick-flip package (DRAFT): does the ARS blind spot change v15's picks?

**Parent:** 5a26b8a18c70ba1aef8d1b862416b36b13a9f95b (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round5/claude-reply-f7e4534.md` §3 (the measurement spec and its registered reading) and §2 (the framing: a behavioral question, not a fix).
**Status: DRAFT for review. The pick-flip run does not run on this draft.** The run requires (i) Claude's approval of this package at its committed sha and (ii) Joe's explicit go in chat — the standing hub rule. What has run is disclosed in §8: the patch's scratch verification, the tally's fixture check, and a two-game smoke whose only purpose is proving the probe logs, the control behaves, and no game changes.

**Package contents**

| File | Role |
|---|---|
| `pickflip-package.md` | this design + registration |
| `code/patch_pickflip_probe.py` | the dual-featurization probe patch (two anchored edits to the O tree's `policy_server.php`) |
| `code/run_pickflip.sh` | the 40-game runner (written, syntax-checked, not run beyond the §8 smoke) |
| `code/tally_pickflip.py` | the read-only tally over the flip logs |
| `code/fixture/flip_log_fixture.jsonl` + `code/fixture/expected_tally.txt` | the tally's fixture: 2 agreeing rows, 3 disagreeing rows with 1 flip, and the tally's exact output on it |

---

## 1. The question, and where it comes from

The round-5 census (accepted, `claude-reply-f7e4534` §1) found the store/view deck-count disagreement concentrated at arsenal decisions: **163 of 267 ARS featurizations disagree (61.0%), every one view > store** — at about three arsenal decisions in five, the deck counts v15 receives omit one copy (occasionally two) of a card the view has already returned to the deck. Every other branch read exactly 0 in 26,702 featurizations.

Claude's §2 framing, which this package adopts verbatim in substance: this is a **representational blind spot, not a train/serve inconsistency**. BC3's cloning data and every PPO run were featurized through this same path, so v15 has always *seen* this omission, in training and at play alike. Correcting the featurizer for an already-trained v15 would *introduce* a train/serve mismatch at exactly these decisions — so "fix it" is not automatically an improvement for the current nets. The correction is a question for the next training run's registration. For the current nets exactly one question remains, and it is behavioral:

**Registered question:** at the ARS featurizations where the two deck pictures disagree, how often would v15's pick change if its deck picture were the view-consistent one — measured by evaluating both states through v15's eval endpoint while play continues on the current state, so no game changes?

## 2. Instrumentation site and eval shape — decided from the code

**Site: `policy_server.php`, inside `SimPolicyServer_Choose`, one probe block after the state is built and canaried and the decision counter is assigned. ARS occurs only there.** The evidence:

| Fact | Location |
|---|---|
| `SimPolicyServer_Choose` builds the state (`SimFeat_BuildState`, :359), canaries it (:360), assigns the decision counter, and — in plain bridge mode — sends the pick request via `SimPolicyServer_Query` | `policy_server.php:352–447` |
| The decision-queue funnel hardcodes branch `"DQ"` at its `BuildState` call — it can never produce an ARS featurization | `policy_server.php:448` |
| The bridge's transport choke point: `SimPolicyServer_Connect` — one persistent length-prefixed connection per worker, used by `SimPolicyServer_Query` on behalf of **both** funnels | `policy_server.php:35–47`, framing at `:49–113` |
| `SimPolicyServer_Query` is pick-shaped: it requires `action_index` in the response and returns an `int` — it cannot carry an eval | `policy_server.php:86–108` |
| The eval wire shape: `SimSearch_Eval($state, $candRecs)` sends `{"mode":"eval","state":…,"candidates":…,"learner_seat":intval(getenv("TCG_LEARNER_SEAT") ?: 0)}` over the same socket path with the same 4-byte big-endian framing, and requires `priors` + `value` in the response | `search.php:431–470` |
| `SimSearch_EvalState($player, $branch, $candRecs)` **rebuilds** the state via `BuildState` before evaluating — it cannot evaluate a variant state; the raw eval send with an explicit state is the only correct shape | `search.php:474–480` |
| The production server's eval handler: `mode == "eval"` routes to `evaluate(state, candidates)` and answers `{"priors", "value"}`. **It reads no seat field** — featurization is driven by the state dict itself (`featurize_state_v3(state)`, whose perspective is `state["player"]`), so both seats' ARS states evaluate through v15, and the payload's `learner_seat` is ignored by this handler | `search_server.py:265–268`, `:86–90`, `:159–167` |
| The pick path's learner route, `net_argmax`, takes the argmax of the same logits the eval endpoint softmaxes into priors — so for the learner seat, the current state's eval argmax *is* the played pick | `search_server.py:184–198`, `:218–235` |
| In plain bridge mode `search.php` is never loaded, so neither eval function exists in the bridge process — the probe implements the eval send itself, on the bridge's connection | `play_game.php:40`, `:100–101` vs `:114–115` |

Why this shape:

1. **One funnel, one block.** Every ARS featurization in bridge play passes through `Choose` exactly once (the DQ funnel's branch is a constant). Patching both funnels, the fallback the design allowed for, would instrument a branch that cannot occur in one of them.
2. **The transport is the shared one.** The probe's eval send (`SimFlip_Eval`) reuses `SimPolicyServer_Connect` and mirrors `SimSearch_Eval`'s framing, payload, response requirements, and two-attempt discipline — including dropping the shared socket global on a transport failure, so the next pick query reconnects transparently (the `Query` code already handles a missing global). What is new is only the response parse (priors + value instead of an action index), because the existing query helper is pick-shaped by construction.
3. **The probe sits where the registered quantities exist.** At the insertion point the function holds the built, canaried `$state`, the `$candRecs` the pick will use, `$branch`, `$player`, `$gate`, `$cands`, and the decision counter — everything the log row needs, with no plumbing. It sits before the label/search child branches; both globals are unset in plain bridge mode, and the runner sets `FLIP_LOG` only for plain bridge runs, so the probe's population is exactly the registered one.

## 3. Operational definitions

- **Store-derived deck count / view-derived deck count**: exactly the census's definitions (`census-package.md` §3), unchanged — store = `$state["deck_counts"]` verbatim (the `""` key dropped); view = `SimFeat_Counts(SimFeat_ZoneIDs(GetDeck($player), DeckPieces()))` computed in the same `Choose` call. The agree flags therefore reconcile 1:1 with census rows for the same games.
- **Variant state**: `$state` with `["deck_counts"]` replaced by the view-derived map. PHP arrays are value types, so every other field — including the embedded candidate records — is the same value by construction. The variant is built from the deciding player's **own** deck view, the same read scope as the featurizer's own; it is never canaried (it is not a game state), never played, and never written anywhere except the flip log.
- **The two eval requests**: built from one `$candRecs` array and the two state arrays. The payload fields are `mode` (`"eval"`, constant), `state` (differing **only** at `deck_counts`), `candidates` (the identical array — candidate identity is by index into this shared list, and the log row records each candidate's `card_id`/`zone`/`zone_index` so the mapping is auditable), and `learner_seat` (the same env-derived value in both; ignored by the eval handler, §2).
- **Argmax**: first strict maximum over the prior vector — the codebase's own tie-break (`v1_argmax`'s scan; the bridge's EQ_LOG argmax scan). **Flip**: `argmax(cur_priors) !== argmax(var_priors)`.
- **Chosen candidate** (for the prior shift): the current state's argmax — what v15 picks under its current inputs. For the learner seat this is the played pick itself (§2); for the other seat it is what v15 *would* pick from that seat's state, which is the registered question ("does the blind spot change v15's picks" — the eval comparison is run at every ARS featurization, for both players, exactly as the census population covers both). **Prior shift**: `|cur_priors[chosen] − var_priors[chosen]|`.
- **Pick-bearing row**: an ARS `Choose` call where the gate passed and at least one candidate exists, so a pick actually occurs. Rows failing that (pass/gate) are logged with `pick: false` and null eval fields — they enter the ARS reconciliation (§5) but no rate.
- **Control**: the agreeing pick-bearing rows. Their two eval payloads are byte-identical (the states are the same value), the games run sequentially so each eval is a singleton batch on the server, and the eval forward is deterministic — so their prior vectors must be identical and their flip count **exactly 0**. Any control flip, or any agreeing row whose two prior vectors differ at all, is a machinery defect: the results package reports the failure, not a rate.

## 4. The probe

`code/patch_pickflip_probe.py` — canonical anchor-asserted form, two edits to `policy_server.php` only:

1. **Helpers** inserted before `SimPolicyServer_Choose`: `SimFlip_Eval` (the eval round-trip of §2) and `SimFlip_Argmax` (first strict maximum).
2. **The probe block** in `Choose`, after the decision counter is assigned and before the label-child branch (the anchor includes the `ChildChoose` line, which makes it unique to `Choose` — the DQ funnel's corresponding lines name `ChildDQ`). In substance:
   - fires only when `$branch === "ARS"`; gated on `getenv("FLIP_LOG")` — unset or empty, the added work is one string comparison per `Choose` call and one `getenv` per ARS call;
   - computes the view counts, diffs them against the store map (census definitions), and, for pick-bearing calls, sends both eval requests and computes argmaxes and the flip;
   - appends one JSON row to `FLIP_LOG` (`FILE_APPEND | LOCK_EX`): `{"game", "player", "branch", "turn", "decision", "agree", "diffs": {card_id: [store, view], …}, "pick", "ncand", "candidates": [{card_id, zone, zone_index}, …], "cur_argmax", "var_argmax", "flip", "cur_priors", "var_priors", "cur_value", "var_value", "eval_error"}` — full prior vectors are logged, so the flip and every shift can be recounted from the log alone;
   - on any eval failure (transport, malformed response, or a prior vector whose length ≠ the candidate count) the row records `eval_error: true` and `flip: null` — counted as machinery trouble by the tally, never silently folded into a rate;
   - reads `$state` and engine globals only; the variant is a copy; the body is wrapped so a probe error can never reach play, and the played pick proceeds through the untouched `SimPolicyServer_Query` path.

**Non-interference** is argued three ways: the variant request is a stateless eval query on the production server (its handler keeps no per-game state; the label path has issued thousands of the same shape); the played answer comes from the original pick request, which the probe never touches, on a connection whose request/response discipline is strictly sequential (no pipelining — each eval is answered before the next send); and the §8 smoke proves it empirically — same seeds in the flip tree and the unpatched O tree produce identical winners, decision counts, and **byte-identical gamelogs**.

## 5. Sample, runner, expected counts, reconciliation

`code/run_pickflip.sh` (reviewed with this package; run only on approval + go) mirrors the census runner's discipline, with the round-5 run conditions folded in:

- **Tree**: `/tmp/fliptree` = a fresh copy of the O tree plus the probe patch and nothing else. Guards in the runner abort unless `search.php` hashes to `8f6b35da…` (O build, untouched), `featurize.php` to `f81193e0…` (O build, **unchanged this round**), and `policy_server.php` to the probe build `c00befa9…` (§8).
- **Games**: the census's own 40 plain bridge games via the tree's `paired_driver.py --arm raw` (`--policy-server`, caps 60 turns / 3,000 decisions / stuck 200, `KEEP_GAME=1`): **seeds 6001–6020 with learner seat 1, seeds 6021–6040 with learner seat 2**, mirror deck `decks/nats2026_ashlyn_fai_60.txt` (sha256 `7397684b…`), `FLIP_LOG` set per seat.
- **Server**: the production build (`/home/joe/tcg/tcg-sim/rl/search_server.py`, sha256 `81ef2cdb…` recorded before and after), one seat-stamped instance per phase, `SEARCH_MODEL` = v15 (`…/fai_ppo_bc3b_20261016/ckpt_v15.pt`, sha256 `0400539d…`). The runner records the segment count (`ipcs -m | wc -l`) at start and end **in-script** (the round-5 condition), captures each phase's server log (its startup line, learner seat included, is quoted in the results — the hand seat check), requires a non-empty flip log per phase, and stops each server by its recorded pid.
- **Expected counts, stated in advance** (from the accepted census): **267 ARS featurizations — 163 disagreeing, 104 agreeing** — and 26,969 total featurizations across the 40 games. The flip run's games must replay the census games identically; the results reconcile three ways: (i) the flip logs' ARS totals and agree split against 267 / 163 / 104 (any pass/gate ARS rows are inside those totals by construction — the probe logs every ARS `Choose` call, as the census probe logged every ARS featurization); (ii) per-game winners and decision counts against the committed census row files (`rounds/round5/data/census/rows_s1.jsonl`, `rows_s2.jsonl`); (iii) kept gamelogs byte-compared against the census run's kept games under `/tmp/census/log_s1` / `log_s2`'s trees if they persist at run time — if they do not persist, the results say so and stand on (i) and (ii). A reconciliation failure is reported as a machinery failure, not smoothed into the rates.

## 6. Report and registered reading

The results package reports, from the two flip logs (committed with it, together with both row files, both server logs, and the tally script, so every number can be recounted — the C2 lesson):

- total ARS rows, pick-bearing rows, no-pick rows, and `eval_error` rows;
- the reconciliation of §5 (ARS totals and split vs the census's 267 / 163 / 104; winners and decision counts vs the committed census rows);
- the **control**: agreeing pick-bearing rows, their flip count (must be exactly 0), and their prior-mismatch count (must be exactly 0);
- the **argmax flip rate among disagreeing pick-bearing ARS rows**, with a 95% Wilson score interval;
- the **prior-shift distribution** on the chosen candidate over disagreeing pick-bearing rows (median, p90, max — the tally's nearest-rank convention, fixture-pinned).

**Registered reading** (Claude's, `claude-reply-f7e4534` §3, carried verbatim in substance — this is the last step needed to close item (b)):

- **Flips ≤ 2%** of disagreeing ARS decisions: the blind spot is **immaterial to play** for the current nets. Item (b) closes as documented, with a featurizer correction folded into the *next* training run's registration, so that training and serving change together.
- **Flips > 2%:** the omission changes picks. Register a production change with re-evaluation (train and serve consistently), and consider a measured gate of v15 with the corrected featurization only alongside a retrained net.

Either way the run authorizes nothing beyond its own report: no featurizer change, no re-evaluation, no training-run registration is made by this package or its results.

## 7. Scope limits

- **Bridge population only, ARS only.** The probe fires at ARS featurizations in plain bridge play. Nothing here speaks to other branches (the census found no disagreement there to begin with), to search-mode featurizations, or to the teacher-root population — the five root aborts' double-count direction remains a separate, open question, exactly as registered in round 5.
- **The variant is a deck-counts-only counterfactual.** It answers "what if v15's deck picture at this decision were view-consistent" — not "what if the featurizer were fixed" in any broader sense (a real fix could change more than this one map, and its training-side half is out of scope by §1's framing).
- **Counts only, never order** — inherited from the census definitions: neither side of the comparison carries deck order.
- The probe reads the deciding player's **own** deck view only — the fair-play boundary is untouched, as in round 5.

## 8. Build verification — what was actually run for this draft

- **Patch scratch**: `patch_pickflip_probe.py` applied to a scratch copy of the O tree's `policy_server.php` — before sha256 `64c215392ddcac0dc92ce1e4a3c455969d87423e23d71be57991247ce53827b3` (the O build) → after **`c00befa98f6b4bb82318b51338f8ff86c8c74b2eb481acc8b106774c8c683fa0`**; `php -l` clean; the full-file diff is **140 added lines, 0 changed or removed**, in exactly two pure insertions (helpers at 349a350–412; the probe block at 361a425–501). One build note: the helper anchor initially omitted `, v1_score` from a comment line; the patch's own anchor assertion caught it before any application, and the anchor was corrected against the file's exact bytes.
- **Flip tree**: fresh copy of `/tmp/otree` at `/tmp/fliptree` with the patched `policy_server.php` installed; verified `policy_server.php` = `c00befa9…`, `featurize.php` unchanged at `f81193e0…`, `search.php` unchanged at `8f6b35da…`. The O tree and production were only ever read.
- **Tally fixture**: `tally_pickflip.py` on `code/fixture/flip_log_fixture.jsonl` (2 agreeing rows; 3 disagreeing rows, 1 of them a flip) reproduces `code/fixture/expected_tally.txt` exactly — flip rate 1/3 = 33.333%, Wilson [6.149%, 79.235%] (independently hand-checked), control flips 0, prior-shift median 0.100000 / p90 0.200000 / max 0.200000. A rerun diff against the expected file is clean.
- **Smoke (disclosed build tests; seeds 7001/7002, the census smoke's seeds)**: production server per seat (startup lines show v15 loaded, learner seat as stamped), one game per seat in the flip tree with `FLIP_LOG` set, and the same seed/seat in the unpatched O tree against the same server:
  - Seed 7001, learner seat 1: flip tree winner 2, 596 decisions, 11 turns — O tree **identical on all three**; kept gamelogs **byte-identical** (92,619 bytes; `cmp` clean — the same byte count as the census smoke's replay of this seed). Flip log: **5 ARS rows — exactly the census smoke's ARS count for this game** — 1 agreeing, 4 disagreeing, all pick-bearing, 0 eval errors. The first disagreeing row's diffs (`oath_of_loyalty_red [2,3]`, `rise_from_the_ashes_blue [0,1]`, player 2, turn 1) match the census smoke's quoted row for the same game state-for-state.
  - Seed 7002, learner seat 2: winner 2, 767 decisions, 18 turns — O tree identical; gamelogs **byte-identical** (123,801 bytes). Flip log: **7 ARS rows — again exactly the census smoke's count for this game** — 3 agreeing, 4 disagreeing, all pick-bearing, 0 eval errors.
  - **Control sanity**: all 4 agreeing rows across both games show `flip: false` **and byte-identical prior vectors** between the two evals (the strong form of the control). Disagreeing rows: 8, flips 0; two show prior movement without an argmax change (the tally over the smoke logs reads prior-shift median 0.000000, max 0.000014). These are machinery evidence only — two games prove the probe logs, the control behaves, and the dual eval runs; **no rate is claimed from them.**
  - Both smoke servers were reaped by exact pid afterwards (an operational note: the smoke launcher wrapped the server start in a subshell, which offset the recorded pid by one — the setsid fork — so the first kill missed; the two servers were identified from `ps` by their full command lines and reaped by their exact pids, and a final process census shows zero `search_server.py` processes. `run_pickflip.sh` does **not** wrap the start — it mirrors `run_census.sh`'s same-shell form, whose recorded pids reaped correctly in the census run); the production server's file hash verified unchanged (`81ef2cdb…`); segment count after the smoke 2,151 (the census run ended at 2,147; +1 per kept smoke/control game, no sweep needed at this scale).
- **Not run**: the 40-game pick-flip run, any analysis of flip data beyond the smoke counts above, any featurizer change.

**Ask:** approval of the site decision (§2), the definitions (§3), the probe code, the sample and runner (§5), and the registered reading (§6). On approval + Joe's go, the flip tree is rebuilt fresh from the O tree, hash-verified against §8's values, `run_pickflip.sh` runs as sketched, and the results return as a package under §6.
