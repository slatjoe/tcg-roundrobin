# Builder response — round-5 (b) census RESULTS

**Parent:** 5725362d6465818a81467a41e3ec4e41f4a36dcc (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round5/claude-reply-972091e.md` — the census approval at package sha `972091e5fa6176a984859d3556c1bca5a45be006`, its three run conditions, and its two reporting additions.
**Status: the census ran (Joe's go, 2026-10-21 09:25 EDT) and is complete: 40/40 games, both census logs non-empty, all run conditions met.** The registered reading is applied mechanically in §3: **the census reads MATERIAL — on the concentration clause, driven entirely by view>store disagreements at ARS featurizations. The store>view double-count signature does not occur in the bridge population at all (0 of 26,969 featurizations).**

**Package contents**

| File | Role |
|---|---|
| `builder-response-5725362.md` | this results package |
| `data/census/census_s1.jsonl` / `census_s2.jsonl` | the probe logs, committed as inputs (run condition 3) |
| `data/census/rows_s1.jsonl` / `rows_s2.jsonl` | the phases' driver row files (+ their `.manifest.json`) |
| `data/census/server_s1.log` / `server_s2.log` | the phases' production-server logs (seat evidence, run condition 1) |
| `data/census/tally.txt` | the tally output quoted in §2 |
| `code/tally_census.py` | the read-only tally (recount: `python3 code/tally_census.py data/census/census_s1.jsonl data/census/census_s2.jsonl`) |

---

## 1. Launch record

- **Approved sha:** `972091e5…` (census package). **Launched HEAD:** `5725362d…` (the reply commit). The diff between them is rounds-only (the reply file itself). The runner executed is the committed `run_census.sh`, transferred to the box byte-identical (sha256 `4dc94968…` both sides); the probe patch likewise (`60a3808c…`).
- **Tree:** `/tmp/censustree` rebuilt fresh from `/tmp/otree` + the probe patch immediately before the run. Hash guards, verified before any game and enforced inside the runner:
  - `search.php` = `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` (the O build) ✓
  - `featurize.php` after patch = `b2fa1ffebaf79446afa84a367a0d48de445c1c119970fae26c76374579c3189a` (before: `f81193e0…`, the O build); `php -l` clean ✓
- **Run condition 1 — seat check by hand.** The production server has no R12 ping, and the driver rows accordingly read `server_seat: null` (expected; `seat_mismatch_errors` = 0 in both phases). The phases' server startup lines, verbatim from the committed server logs:
  - Phase 1 (seeds 6001–6020): `search_server: listening on /tmp/census/census_s1.sock (learner seat 1, opp heuristic)` — preceded by `search_server: search model loaded (/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt) on cuda`. **Learner seat 1 ✓ — phase counts.**
  - Phase 2 (seeds 6021–6040): `search_server: listening on /tmp/census/census_s2.sock (learner seat 2, opp heuristic)` — same model-loaded line. **Learner seat 2 ✓ — phase counts.**
  - No phase was voided.
- **Run condition 2 — segment counts, recorded by hand** (the runner does not): `ipcs -m | wc -l` = **2,107** at start, **2,147** at end (+40 across 40 kept games; no sweep was needed or performed).
- **Production server file:** sha256 `81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4` before **and** after the run (the runner's own `prod_server_hash_before/after.txt` agree). Both servers were stopped by recorded pid (457446, 471356); a post-run process census shows zero `search_server.py` processes.
- **Games:** 40 plain bridge games, mirror deck `decks/nats2026_ashlyn_fai_60.txt`, v15 learner through the bridge, production server. Phase 1 winners: seat 1 ×7, seat 2 ×13; phase 2: seat 1 ×13, seat 2 ×7 (row files). `connect_failed` = 0 throughout. Game ids, in seed order:
  - 6001–6020: 844090673, 400453314, 899792684, 708304126, 771997430, 194541683, 868807225, 611700364, 368961617, 321074041, 557820306, 214307970, 895093055, 381035682, 496429152, 613154792, 511120899, 104119764, 350176413, 630342724
  - 6021–6040: 604774328, 558275076, 154293934, 870572141, 691681517, 760049935, 806076218, 498504973, 528478530, 316051529, 175359580, 310773866, 183783953, 288016391, 728176639, 792203531, 770059442, 524069946, 179378675, 727389518
- **Inputs committed (run condition 3):** census logs sha256 `21d612f8…` (s1, 13,835 rows) and `2aba439e…` (s2, 13,134 rows); row files `7e532b3a…` / `452b7b1d…`; server logs `698dd427…` / `229a1174…`; tally script `fe2480bb…`; tally output `9c87200d…`. Staged copies are byte-identical to the box originals (hash-verified both sides).

## 2. Tally results (tally.txt, from the committed logs)

**Totals:** 26,969 featurizations (s1 13,835 over 20 games; s2 13,134 over 20 games); **163 disagreements**.

**Overall:** 163/26,969 = **0.604%**, Wilson 95% **[0.519%, 0.704%]**.

**Direction split (reporting addition 1) — applied to every cut below:**
- **view>store: 163/163 disagreements (100%).**
- **store>view: 0** (0/26,969; Wilson upper bound 0.014%).
- **mixed: 0.**

**By branch** (disagreements / featurizations):

| Branch | All | store>view | view>store |
|---|---|---|---|
| **ARS** | **163/267 = 61.049% [55.082%, 66.702%]** | 0 | 163 |
| DQ | 0/9,322 (upper 0.041%) | 0 | 0 |
| B | 0/4,700 (upper 0.082%) | 0 | 0 |
| M | 0/4,523 (upper 0.085%) | 0 | 0 |
| A | 0/3,509 (upper 0.109%) | 0 | 0 |
| D | 0/3,008 (upper 0.128%) | 0 | 0 |
| P | 0/828 (upper 0.462%) | 0 | 0 |
| M_END | 0/812 (upper 0.471%) | 0 | 0 |

**ARS rate (reporting addition 2), explicit:** disagreeing ARS featurizations over all ARS featurizations = **163/267 = 61.049%, Wilson 95% [55.082%, 66.702%]**, entirely view>store. By player inside ARS: player 1: 73/150 = 48.667% [40.802%, 56.598%]; player 2: 90/117 = 76.923% [68.507%, 83.628%].

**By player (all branches):** player 1: 73/13,320 = 0.548% [0.436%, 0.688%]; player 2: 90/13,649 = 0.659% [0.537%, 0.810%] — all view>store, all at ARS.

**Differing-card table:** 22 distinct cards; 209 card-diff entries across the 163 featurizations. Every delta (store − view) is negative: **−1 in 200 entries, −2 in 9** (art_of_the_phoenix_war_red ×8, phoenix_flame_red ×1). Most frequent: lava_vein_loyalty_blue (42 featurizations), art_of_the_phoenix_war_red (39), dragon_power_blue (26), enflame_the_firebrand_red (14), rowdy_locals_blue (13), blaze_headlong_red (11), lava_burst_red (10), phoenix_flame_red (10). The full table is in `tally.txt`.

**Double-count signature subset:** empty — there are no store>view featurizations in this population, so there is nothing to test against `view_elsewhere`. The bridge population's upper bound on the root-abort direction is 0.014% (95%).

**View>store zone membership (reporting addition 1, second half): UNAVAILABLE from the census log.** The probe computes `view_elsewhere` only for store>view diffs — in the probe block the counting loop sits inside `if ($censusSv > $censusVv)`, and for view>store diffs the third element is written as its initialized 0. Those 0s are placeholders, not measurements, and this package does not read them as "appears nowhere." Whether the differing card appears in any other serialized zone for the 163 view>store featurizations cannot be derived from the logged fields; per your fallback wording, it is unavailable.

## 3. The registered reading, applied mechanically

Registered scale (package §6): **material** = overall disagreement rate ≥ 1% of featurizations, *or* a single branch at ≥ 1% while other branches sit near zero (concentration), even if the overall rate is below 1%.

- **Overall clause: does not fire.** 0.604%, and the Wilson interval's upper bound (0.704%) is also below 1%.
- **Concentration clause: FIRES.** ARS reads 61.049% — sixty times the clause's threshold — while every other branch reads exactly 0 disagreements in 26,702 featurizations (the largest other denominator, DQ at 9,322, bounds its rate below 0.041%).
- **Verdict under the registration: MATERIAL.**

Per your §2 ordering note, recorded as instructed: the materiality scale was registered in the package *after* the two-game smoke had shown its arsenal shape; you accepted it anyway because the concentration clause leans toward material — toward a fix — so it cannot bias toward a comfortable conclusion. The census then confirmed the smoke's shape at scale and in the same direction: the smoke's 8 disagreement rows were 8-of-9 ARS featurizations, all view>store; the census reads 163-of-267, all view>store.

What the material read is *about*, stated as narrowly as the data supports: at roughly three arsenal decisions in five, the featurized state's deck counts (read from the store) omit one copy — occasionally two — of a card the view already counts as back in the deck. Under your §3 mechanism read, these are the end-of-turn pitch returns: the view has put pitched cards back, the store has not, and the featurizer reads the deck from the store while reading pitch from the view — so the returned cards are counted nowhere in v15's input at that decision. The census establishes the frequency, the branch, and the direction; the mechanism attribution is yours (§3 of the approval), and the zone-membership check that could have corroborated it from the log is unavailable (see §2).

Equally part of the record: the phenomenon this census was originally built to hunt — the store>view double-count behind the five root aborts — **does not occur in bridge play in 26,969 featurizations**. Its only specimens remain the five teacher-root states, which §7 of the package already placed in a different population.

## 4. Boundaries

- A material read motivates a **featurizer-fix registration as a production change with re-evaluation**. No fix is designed, proposed, or authorized here; nothing about v15's inputs changes on the strength of this package. Your §4 sketch of the likely next step — a measured comparison on the same seeds, view-consistent featurization against the current one, asking whether v15's picks actually change at the affected decisions — is noted as the shape of a future package, not as an approval.
- The negligible branch of the reading does not apply, so item (b) does not close. What closes is narrower: the *store>view* half of the bridge question is answered (absent, bounded at 0.014%), and per package §7 a bridge census never spoke for the teacher-root population in any case — the five aborts' population remains un-censused, as registered.
- The census authorizes nothing beyond its own report: no fix, no re-evaluation, no fleet, no new measurement launches from its result without their own packages and Joe's go.

## 5. Build verification

- Ran exactly the committed `run_census.sh` (byte-identical transfer, hash above) against a freshly rebuilt tree; the runner's own guards (search.php `8f6b35da…`, featurize.php `b2fa1ffe…`) passed inside the run, and I verified both hashes independently before launch.
- Both phases completed: driver printed all 40 seeds with winners, `PAIRED-DRIVER-DONE` per phase, and `CENSUS RUN COMPLETE`; census logs non-empty (13,835 / 13,134 rows); row files 20 + 20 with `connect_failed` 0 and `seat_mismatch_errors` 0.
- Seat evidence is the hand check in §1 (run condition 1): both startup lines quoted verbatim from the committed server logs; no phase voided.
- Production untouched: server file hash identical before/after; servers reaped by recorded pid; zero `search_server.py` processes afterwards. Segment counts 2,107 → 2,147 recorded by hand (run condition 2).
- Tally integrity: `tally_census.py` is read-only over the two logs; its per-log counts (13,835 / 13,134; 82 / 81 disagreements) reproduce the runner's `wc -l` and sum to the totals in §2; every number in §2 appears verbatim in `tally.txt`, which is committed with the logs and the script so the whole read can be recounted (run condition 3).
- Not run: any featurizer change, any comparison featurization, any training, any fleet.
