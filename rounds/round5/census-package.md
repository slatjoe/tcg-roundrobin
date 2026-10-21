# Round 5 — (b)-census package (DRAFT): how often do the store and view deck counts disagree at bridge featurization?

**Parent:** 80b4c33a871d45740b7a6c845f68aa8359f54ecb (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round4/claude-reply-6b843d7.md` §3 (the finding and the census order) and §4 item 2 (the (b) census as the next measurement).
**Status: DRAFT for review. The census does not run on this draft.** The run requires (i) Claude's approval of this package at its committed sha and (ii) Joe's explicit go in chat — the standing hub rule. What has run is disclosed in §8: the patch's scratch verification and a two-game smoke whose only purpose is proving the probe logs and changes nothing.

**Package contents**

| File | Role |
|---|---|
| `census-package.md` | this design + registration |
| `code/patch_census_probe.py` | the probe patch (one anchored edit to the O tree's `featurize.php`) |
| `code/run_census.sh` | the 40-game census runner (written, syntax-checked, not run beyond the §8 smoke) |

---

## 1. The question, and where it comes from

In the round-4 O fleet, five teacher decisions aborted when Decide's root canary — run on the bridge state **after** the checkpoint's store:=view sync — caught the learner's own cards counted once too often: each abort names **two** of the learner's cards at exactly legal+1 (`dupseq_recheck.txt` quotes the strings in full: e.g. game 809340311, `art_of_the_phoenix_war_red x4 (legal x3), fire_that_burns_within_red x7 (legal x6)`). The same state array had passed Choose's canary moments earlier, pre-sync.

The mechanism Claude's §3 points to is the mixed-source featurization, registered in round 3 as item (b): `SimFeat_BuildState` takes the deck counts from `SimV1_DeckCards` — which reads the **store** globals directly — while every other zone is read through the CardGetters **view** family. Between syncs, a card that has just moved can sit in a view zone and still be in the store's deck, so the featurized state counts it twice. Choose's canary cannot see this class: its legal counts (`SimFeat_LegalCounts`, `featurize.php:148`) are built from the same mixed sources as the state it judges. The post-sync root canary judges against consistent sources and catches it — five times in 400 teacher games, at teacher roots only.

**The registered question:** in plain bridge play — v15 deciding through the bridge, the configuration of every eval this project has run — at the moment of featurization, **how often do the store-derived deck counts and the view-derived deck counts for the deciding player disagree**, overall and by decision branch? Until that frequency is known, nobody can say whether the double-count is a five-in-28,000 curiosity or a routine feature of the inputs v15 has been deciding on all along. If the rate is material, a featurizer fix is a production change (it alters v15's inputs everywhere) needing its own registration and re-evaluation — which is why the frequency comes first (§6).

## 2. Instrumentation site — decided from the code

**Site: `featurize.php`, inside `SimFeat_BuildState`, one block between the `$state` construction and its return.** The alternative considered was `policy_server.php`'s `SimPolicyServer_Choose`. The evidence:

| Fact | Location |
|---|---|
| `SimFeat_BuildState($player, $branch, $candidates)` — branch and player are its own arguments; `$state` carries `branch` and `turn` | `featurize.php:61`, state array `:83–110` |
| The store side is serialized at `"deck_counts" => SimFeat_Counts(SimV1_DeckCards($player))` | `featurize.php:97` |
| `SimV1_DeckCards` returns the `$p1Deck`/`$p2Deck` **store** globals verbatim | `policy_v1.php:44–48` |
| `GetDeck($player)` returns by reference the **view** deck array (`$mainDeck`/`$defDeck`, or `$myDeck`/`$theirDeck`) — the deck member of the same getter family (`GetHand`, `GetArsenal`, …) the featurizer reads every other zone through | `vendor/talishar/CardGetters.php:159–172` |
| `DeckPieces()` = 1 (one array element per deck card) | `vendor/talishar/Constants.php:25` |
| Bridge funnel 1: `SimPolicyServer_Choose` calls `SimFeat_BuildState($player, $branch, $candRecs)` then the canary | `policy_server.php:359–360` |
| Bridge funnel 2: the decision-queue path calls `SimFeat_BuildState($playerID, "DQ", $candRecs)` then the canary | `policy_server.php:448–449` |
| `--policy-server` mode loads `featurize.php` + `policy_server.php` only; `search.php` is loaded only under `--policy-search` | `play_game.php:40`, `:100–101` vs `:114–115` |

Why this site wins:

1. **It is the featurization.** The question is defined at the moment the featurizer assembles its inputs. At this site the store side needs no recomputation — the probe reads `$state["deck_counts"]`, the exact map about to be serialized to the net.
2. **Branch needs no plumbing.** The fallback the design allowed for — carrying the branch in from the bridge request — is unnecessary: `$branch` is a native `BuildState` argument and is already in `$state`, as is `turn`. The rejected site would have had to re-derive both.
3. **One site sees every bridge featurization exactly once.** In plain bridge mode `search.php` is never loaded, so the only `BuildState` callers in the process are the two bridge funnels above. Instrumenting `Choose` (site ii) would have missed the DQ funnel's featurizations entirely — in the §8 smoke, DQ is the single largest branch (228 of 596 rows in game 1).
4. **Both source families are in scope with the featurizer's own helpers** — the store map from `$state`, the view side via `GetDeck` + `SimFeat_ZoneIDs(…, DeckPieces())`, the identical treatment the featurizer gives every other view zone.

One population fact the smoke established (§8): in plain bridge mode the bridge featurizes for **both seats** — the learner seat's picks are answered by the net, the other seat's by the server's v1 route, and both funnels build the state the same way. The census population is therefore **every bridge featurization**, with the deciding player logged per row; rates are reported overall and by player (§6), never silently restricted to the learner seat.

## 3. Operational definitions

- **Store-derived deck count** (per card id, deciding player): `$state["deck_counts"]` as `SimFeat_BuildState` built it — `SimFeat_Counts(SimV1_DeckCards($player))` — with the `""` key dropped if present. Empty strings are not cards; the canary's own merge drops them too (`SimFeat_MergeCounts`). This is the count map the net actually receives.
- **View-derived deck count**: `SimFeat_Counts(SimFeat_ZoneIDs(GetDeck($player), DeckPieces()))`, computed inside the same `BuildState` call, from the view array as it stands at that moment. `ZoneIDs` drops empty slots, matching the featurizer's treatment of every other view zone.
- **Disagreement**: any card id whose store count ≠ view count at that featurization. A census row is logged per featurization either way (`agree` flag), so rates have honest denominators.
- **Double-count signature**: for a differing card with store > view, the row records `view_elsewhere` — that card's occurrences in the deciding player's *other* view zones as serialized in the same `$state` (hand, arsenal, and the player's board side: allies, auras, items, character, pitch, graveyard and banished counts). A disagreement is in the signature subset when every store>view card's excess is fully accounted by `view_elsewhere` (store − view ≤ view_elsewhere) — the §3 mechanism's fingerprint: the store still holds a card the view has already placed elsewhere. (Computed from `$state` only; no extra engine reads.)
- **Branch**: the `$branch` string as passed to `BuildState`, logged verbatim. The branch vocabulary is the engine's (observed in the smoke: `M`, `B`, `A`, `D`, `P`, `ARS`, `DQ`, `M_END`); the census reports by the strings as logged and invents no taxonomy over them.
- **Turn**: `$state["turn"]` (the engine's `currentTurn` at featurization).

## 4. The probe

`code/patch_census_probe.py` — canonical anchor-asserted form, one edit. The inserted block, in substance:

- gated on `getenv("CENSUS_LOG")` — unset or empty, the only added work in the whole run is that one `getenv` per featurization;
- computes the view counts, diffs them against the store map, and appends one JSON row to the `CENSUS_LOG` file (`FILE_APPEND | LOCK_EX`):
  `{"game", "player", "branch", "turn", "agree", "diffs": {card_id: [store, view, view_elsewhere], …}}` — `game` from `$GLOBALS["gameName"]`, the same source the bridge's own trajectory logger uses;
- reads `$state` and engine globals only; writes nothing back (the one `unset` acts on a local copy of the counts map); returns nothing; the body is wrapped so a census error is swallowed and can never reach play; a failed log write is silent by design, and the runner (§5) treats an empty census log as an abort, so silence cannot counterfeit data.

**Non-interference** is argued three ways: the block runs after `$state` is fully built and before its return, and mutates nothing the function returns; it is present only in the census tree (§5), never in production or the O tree; and the §8 smoke proves it empirically — same seeds in the census tree and the unpatched O tree produce identical winners, identical decision counts, and **byte-identical gamelogs**.

## 5. Sample and runner

`code/run_census.sh` (sketch reviewed with this package; run only on approval + go):

- **Tree**: `/tmp/censustree` = a fresh copy of the O tree plus the probe patch and nothing else. Guards in the runner abort unless the tree's `search.php` hashes to the O build (`8f6b35da…`) and its `featurize.php` to the probe build (`b2fa1ffe…`, §8).
- **Games**: 40 plain bridge games via the tree's `paired_driver.py --arm raw` (the fleet raw pattern: `--policy-server`, caps 60 turns / 3,000 decisions / stuck 200, `KEEP_GAME=1`): **seeds 6001–6020 with learner seat 1, seeds 6021–6040 with learner seat 2** — outside every registered range (fleets 1001–1200, 2001–2200; pre-gates/probes 4001–4014, 5001–5010; smoke 7001–7002).
- **Server**: the **production** build (`/home/joe/tcg/tcg-sim/rl/search_server.py`, sha256 `81ef2cdb…` recorded before and after the run), one seat-stamped instance per seat phase, `SEARCH_MODEL` = v15 (`…/fai_ppo_bc3b_20261016/ckpt_v15.pt`, sha256 `0400539d…`), exactly as ordinary evals run. Servers are stopped by recorded pid after each phase.
- **Deck**: `decks/nats2026_ashlyn_fai_60.txt` both seats (sha256 `7397684b…`), the mirror held constant as in every fleet.
- **Sanity gates**: the server's `search model loaded` line must appear before a phase's games start; each seat's census log must be non-empty after its games, else the run aborts and the failure is packaged. The run also records the segment count (`ipcs -m | wc -l`) at start and end.
- The do-not-train discipline does not apply (no fleet, no labels, no training use), but the census game ids are recorded in the results package like any other run's.

## 6. Report and registered reading

The results package reports, from the two census logs (which are committed with it, so every number can be recounted — the C2 lesson; the tally is a short read-only script shipped in the same package):

- total featurizations (rows), disagreements, and the **overall disagreement rate with a 95% Wilson score interval**;
- rate **by branch** and **by player** (each with its denominator);
- the **differing-card table**: every card id that ever differed, its total differing featurizations, and the distribution of (store − view) deltas;
- the **double-count signature subset**: how many disagreements match the §3 fingerprint, and their branch distribution.

**Registered reading — this is a frequency census, not a gate.** There is no pass/fail and no conversion at stake. The materiality scale, stated in advance in plain terms:

- **Material**: an overall disagreement rate of **≥ 1% of featurizations**, *or* disagreement **concentrated in one branch** — a single branch at ≥ 1% while other branches sit near zero is concentration, and it counts as material even if the overall rate is below 1%. A material rate motivates a featurizer-fix registration as a **production change with re-evaluation** (the fix alters v15's inputs in every configuration; nothing about the fix is designed or authorized here).
- **Negligible**: below that scale and unconcentrated — item (b) closes, and the five aborts stand as a rare, canary-caught edge of the teacher's root path.

Either way the census authorizes nothing beyond its own report: no fix, no re-eval, no fleet launches from its result without their own packages.

## 7. What the census cannot see

- **Disagreements the sync erases before featurization are definitionally out of scope.** The census measures the bridge's *actual featurization inputs* — the states v15 (and the server's v1 route) really decided on in this configuration. That is the registered question; a divergence that exists only between featurizations, or only after a sync the bridge never performs, is not an input error and is not counted.
- **Search-mode featurizations are a different population.** Rollout children and teacher roots build states under `search.php`; the five aborts were teacher roots *post-sync*. A negligible bridge census would not close the root-state question — it would bound the bridge phenomenon, and the root population would need its own registration if anyone wanted it counted.
- **Counts only, never order.** Neither side of the comparison carries deck order (the featurizer itself sends counts), so an order-only divergence is not a disagreement by definition.
- The census sees the deciding player's **own** deck only — the fair-play boundary is untouched: `GetDeck` is called for the deciding player whose state is being built, exactly as the featurizer's own reads are scoped.

## 8. Build verification — what was actually run for this draft

- **Patch scratch**: `patch_census_probe.py` applied to a scratch copy of the O tree's `featurize.php` — before sha256 `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92` (the O build, matching the tree) → after **`b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a`**; `php -l` clean; the full-file diff is **1 hunk, 56 added lines, 0 changed or removed** — the probe block only.
- **Census tree**: fresh copy of `/tmp/otree` at `/tmp/censustree` with the patched `featurize.php` installed; its `search.php` verified unchanged at `8f6b35da…`. The O tree and production were only ever read.
- **Smoke (disclosed build tests; seeds 7001/7002 are out-of-range and were chosen for this)**: production server per seat (startup line: v15 loaded on cuda, learner seat as stamped), one game per seat in the census tree with `CENSUS_LOG` set, and the same seed/seat in the unpatched O tree against the same server:
  - Seed 7001, learner seat 1: census tree winner 2, 596 decisions, 11 turns — O tree **identical on all three**; kept gamelogs **byte-identical** (92,619 bytes; `cmp` clean; neither log embeds its game id). Census log: **596 rows — exactly the game's decision count**; players {1: 264, 2: 332}; branches {DQ 228, M 102, B 94, A 81, D 66, P 16, ARS 5, M_END 4}; 592 agree, **4 disagree**.
  - Seed 7002, learner seat 2: winner 2, 767 decisions, 18 turns — O tree identical; gamelogs **byte-identical**. Census log: 767 rows (again exactly the decision count); players {1: 354, 2: 413}; 763 agree, **4 disagree**.
  - The 8 disagreement rows are machinery evidence only — two games prove the probe logs and the phenomenon exists in bridge play; **no rate is claimed from them.** For the record, their shape: all 8 are branch `ARS`, and every differing card is **view > store** (deltas +1, once +2) — e.g. game 664498687, player 2, turn 1: `oath_of_loyalty_red [2,3]`, `rise_from_the_ashes_blue [0,1]`; game 964335234, player 2, turn 6: `art_of_the_phoenix_war_red [1,3]`. That is the *reverse* direction from the root-abort signature (store ahead of view) — the store lagging the view, at arsenal decisions. Whether that shape survives a real sample is the census's business, not the smoke's.
  - Both smoke servers were reaped by exact pid afterwards; a final process census shows zero `search_server.py` processes; the production server's file hash verified unchanged (`81ef2cdb…`); segment count after the smoke 2,107 (no sweep needed at this scale).
- **Not run**: the 40-game census, any analysis of census data beyond the smoke counts above, any featurizer change.

**Ask:** approval of the site decision (§2), the definitions (§3), the probe code, the sample and runner (§5), and the registered reading (§6). On approval + Joe's go, the census tree is rebuilt fresh from the O tree, hash-verified against §8's values, `run_census.sh` runs as sketched, and the results return as a package under §6.
