# Round 7 — re-gate RUN MANIFEST (partial run — no read declared)

**Registration:** `rounds/round7/respecified-gate-registration.md`, approved at sha **2e5e4c5dd15c6aa55b5f1ab662e79de20117bbbc** (approval: `rounds/round7/claude-reply-2e5e4c5.md`).
**Launched HEAD:** a1861a19 (differs from the approved sha only by the reply commit under `rounds/`, per PROTOCOL).
**Go:** Joe, 2026-10-22 05:53 EDT. **Launch:** 2026-10-22 05:55:07 EDT. **Run complete:** 06:21:08 EDT.

## STATUS — ANOMALY: both halves truncated; NO READ IS DECLARED

The run executed as registered in script, caps, anchor, and environment, and both server logs are clean (fallbacks = 0, §4). **But neither half delivered its 200 games.** Each half's php batch was killed by `rl/eval.py`'s internal batch timeout — `timeout = args.games * 3 + 180` = **780 s for the whole 200-game batch** (eval.py line ~200, non-search branch) — with the summary error `"play_game.php timed out (partial results used)"`:

- **Half A:** 186 games counted of 200 (187 game ids recorded; the 187th was in flight when php was killed and left traj records but no result row). Batch wall 781 s.
- **Half B:** 185 games counted of 200 (186 ids; same in-flight loss). Batch wall 780 s.

**Total counted: 371 of the registered 400.** The registration specifies 400 seat-balanced games and contains no partial-completion provision, so **this manifest declares no read**: the three-way verdict (Cleared / Stall / Weak) is **not** pronounced, `GRAVY_STAGE2_CLEARED` is **not** set (it would in any case require the stage-3 alignment registration per claude-reply-2e5e4c5 §4), and the registry merge of §5 was **not** performed (§6). All quantities in §5 are **descriptive computations over the 371 counted games**, reported so the validity decision — which belongs to Claude and Joe — has the numbers in front of it.

**Mechanism.** The 780 s budget prices 3 s/game + 180 s. At the re-specified trigger (62), Gravy games run longer than at trigger 35 (counted mean_turns 42.71 / 43.52 vs the stage-2 gate's 33.16 / 33.44), ≈ 4.2 s/game, so a 200-game batch needs ≈ 840 s > 780 s. The registration's wall-time estimate (≈ 25 min for both halves; actual 26m01s) priced the total, not this per-batch budget inside the harness. The identical error string and truncation pattern appear in the Fai-era BC3 regate records (333 of 400 counted; the 150/333 = 0.450 anchor read of record) — noted as context for the validity decision, not as a claim that it settles this one.

**Selection note.** The uncounted games are of two kinds: 13 (A) / 14 (B) never started (batch order carries no outcome information that the records show) and 1 in flight per half at the kill (length-selected by construction — it was still running at 780 s — and its outcome is unrecorded). Counted halves remain near-balanced (186 / 185).

## 1. Pre-flight (2026-10-22, before launch)

| Check | Value | Required |
|---|---|---|
| Registry `/tmp/harvest/do_not_train_registry.json` | 3,795 games, sha256 `ae7b04b9d4f5b554f52fc443e445fa74d48ce15116516d824f15107d340addce` | matches the registration's pinned state ✓ |
| Anchor `gravy_bc/bc3_out/bc3_policy.pt` | sha256 `1e6e3906caa04ac7efc2f61e936fbc1057ae7fe3c5cbe56b4cc8234b48eac288` | unchanged ✓ |
| SHM segments (ipcs) | 2,193 (3,600 = do-not-launch) | ✓ (2,195 after the run) |
| /tmp free | 15 G of 20 G | ✓ |
| `GRAVY_STAGE2_CLEARED` | unset | left unset (see Status) ✓ |

## 2. The launch script

`run_regate.sh` (box: `/tmp/r7launch/run_regate.sh`; staged copy: `rounds/round7/code/run_regate.sh`), sha256 **965cdcb74ab3b938e10a582947144f5798759bcb49c959fb2c47a72ae654505a**.

Full text:

```bash
#!/bin/bash
# Round-7 stage 2 (part 2): the anchor gate - the two registered
# rl/eval.py invocations of build-package.md sec.4, run sequentially.
set -u
export TCG_MAX_DECISIONS=3000
cd /home/joe/tcg/tcg-sim
PY=/home/joe/tcg/rl-env/bin/python
G60=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
echo "=== anchor gate A (learner deck a) $(date) ==="
$PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
  --games 200 --deck-a $G60 --deck-b $G60 --learner-deck a \
  --workdir gravy_bc/anchor_regate_a --sock /tmp/gravy_regate_a.sock \
  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
echo "gate_a_exit=$?"
echo "=== anchor gate B (learner deck b) $(date) ==="
$PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
  --games 200 --deck-a $G60 --deck-b $G60 --learner-deck b \
  --workdir gravy_bc/anchor_regate_b --sock /tmp/gravy_regate_b.sock \
  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
echo "gate_b_exit=$?"
echo "=== gate runs complete $(date) ==="
```

Diff against `run_stage2_gate.sh` — exactly the three registered changes ((a) `--max-turns 87` on both calls; (b) `TCG_MAX_DECISIONS=3000` exported; (c) fresh workdir and socket names), verified before launch per claude-reply-2e5e4c5 §2.1:

```diff
--- run_stage2_gate.sh
+++ run_regate.sh
@@ -2,19 +2,20 @@
 # Round-7 stage 2 (part 2): the anchor gate - the two registered
 # rl/eval.py invocations of build-package.md sec.4, run sequentially.
 set -u
+export TCG_MAX_DECISIONS=3000
 cd /home/joe/tcg/tcg-sim
 PY=/home/joe/tcg/rl-env/bin/python
 G60=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
 echo "=== anchor gate A (learner deck a) $(date) ==="
 $PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
   --games 200 --deck-a $G60 --deck-b $G60 --learner-deck a \
-  --workdir gravy_bc/anchor_gate_a --sock /tmp/gravy_anchor_a.sock \
-  --sim-dir /home/joe/tcg/tcg-sim
+  --workdir gravy_bc/anchor_regate_a --sock /tmp/gravy_regate_a.sock \
+  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
 echo "gate_a_exit=$?"
 echo "=== anchor gate B (learner deck b) $(date) ==="
 $PY rl/eval.py --ckpt gravy_bc/bc3_out/bc3_policy.pt --opp heuristic \
   --games 200 --deck-a $G60 --deck-b $G60 --learner-deck b \
-  --workdir gravy_bc/anchor_gate_b --sock /tmp/gravy_anchor_b.sock \
-  --sim-dir /home/joe/tcg/tcg-sim
+  --workdir gravy_bc/anchor_regate_b --sock /tmp/gravy_regate_b.sock \
+  --sim-dir /home/joe/tcg/tcg-sim --max-turns 87
 echo "gate_b_exit=$?"
 echo "=== gate runs complete $(date) ==="
```

## 3. Timeline

| Event | EDT |
|---|---|
| Launch (detached, setsid) | 05:55:07 |
| Half A summary written (batch timeout at 780 s budget) | 06:08:08 |
| Half B summary written (batch timeout) | 06:21:08 |
| **Total wall time** | **26m01s** (estimate ≈ 25 min) |

## 4. Server-log validity (both halves)

Both workdir server logs (`gravy_bc/anchor_regate_a/server.log`, `gravy_bc/anchor_regate_b/server.log`) open with the anchor loaded from the registered path —

```
rollout_server: learner -> RL vNone (/home/joe/tcg/tcg-sim/gravy_bc/bc3_out/bc3_policy.pt)
```

— and every heartbeat line in both logs reports `fallbacks=0` (each log serves 95,000+ decisions; lines with `fallbacks≥1`: **0 in A, 0 in B**). The fallbacks validity condition **passes**. The run is short on game count only (§Status).

## 5. Results — DESCRIPTIVE ONLY (371 counted games; no read declared)

Per-half summaries, verbatim from the run log:

- **A:** `{"wins": 85, "games": 186, "win_rate": 0.45698924731182794, "learner_seat_wins": {"1": 85, "2": 0}, "traj_games": 187, "opp": "heuristic", "ckpt": "/home/joe/tcg/tcg-sim/gravy_bc/bc3_out/bc3_policy.pt", "learner_deck": "a", "error": "play_game.php timed out (partial results used)", "capped_games": 33, "cap_reasons": {"turns": 33}, "mean_turns": 42.70967741935484}`
- **B:** `{"wins": 65, "games": 185, "win_rate": 0.35135135135135137, "learner_seat_wins": {"1": 0, "2": 65}, "traj_games": 186, "opp": "heuristic", "ckpt": "/home/joe/tcg/tcg-sim/gravy_bc/bc3_out/bc3_policy.pt", "learner_deck": "b", "error": "play_game.php timed out (partial results used)", "capped_games": 47, "cap_reasons": {"turns": 47}, "mean_turns": 43.524324324324326}`

Computed from those counts (decided = games − capped_games; draw-score = (wins + 0.5 × capped) / games; non-win = wins / games; capped-share intervals Wilson95; draw-score intervals by the normal approximation on the mean of per-game scores in {1, 0, 0.5} with the empirical score variance — the method of claude-reply-2e5e4c5 §2.2):

| Half | games | anchor wins | heur. wins (decided) | draws (capped) | decided split | draw-score [95% CI] | non-win | capped share [Wilson95] | mean turns |
|---|---|---|---|---|---|---|---|---|---|
| A (deck a) | 186 | 85 | 68 | 33 | 85–68 | 0.54570 [0.48086, 0.61054] | 0.45699 | 0.17742 [0.12921, 0.23868] | 42.71 |
| B (deck b) | 185 | 65 | 73 | 47 | 65–73 | 0.47838 [0.41623, 0.54053] | 0.35135 | 0.25405 [0.19677, 0.32135] | 43.52 |
| **Pooled** | **371** | **150** | **141** | **80** | **150–141** | **0.51213 [0.46709, 0.55717]** | **0.40431** | **0.21563 [0.17681, 0.26028]** | 43.11 |

- **Cap reasons:** all 80 capped games are `"turns"`; **zero decision caps** — consistent with the ruling's proof that the 62 trigger fires before the 3,000-query cap (claude-reply-143968a §2(ii)). No finding about the anchor's query pattern arises.
- **Stall guard (descriptive):** pooled capped share Wilson95 **lower bound 0.17681**, against the guard bound 0.2285 — **the guard would not trip** on these counts.
- For orientation only: on the counted games the point estimate (0.51213) sits above the 0.40 line and the guard is clear — the shape of a Cleared read — **but the verdict is not pronounced**, because the run delivered 371 of the registered 400 games under a registration with no partial-completion provision. Whether a partial read can stand (the Fai-era precedent), or the gate must be re-run in a form that fits the harness's batch budget (a re-specification — e.g. more, smaller batches — would itself need review, since the registration fixes two invocations of 200), is the decision this manifest is written for.

## 6. Registry — NOT merged (withheld pending the validity decision)

- The post-run id check was performed read-only: the run's **373 unique ids** (187 A + 186 B, no duplicates, no A∩B overlap) intersect the pinned registry (3,795 games, `ae7b04b9…`) in **0** places — the collision validity condition **passes**.
- The registration requires the ids be registered under `gravy_anchor_regate_eval` **before the read is used**. Since no read is declared, **no merge was performed**: the live registry and the vault copy are unchanged (3,795 games, sha256 `ae7b04b9d4f5b554f52fc443e445fa74d48ce15116516d824f15107d340addce`; vault: `/home/joe/tcg/registry-vault/do_not_train_registry-20261022-merged.json`). The 373 ids are preserved in the workdirs' `traj/games_meta.jsonl` and listed in the Appendix, so the merge can be executed exactly as registered if the read is accepted, or as bookkeeping if it is not.

## 7. R4 table (re-specified anchor column filled descriptively, from the partial run)

| Instrument | On Fai | On the Gravy mirror | On the Gravy anchor |
|---|---|---|---|
| Fai-era (turn parameter 60 / trigger 35; decisions 3,000) | **0 of 333** capped (BC3 gate records) | H = **0.6721** [0.6530, 0.6906] | **0.72** (288/400, all turn caps) |
| Re-specified (parameter 87 / trigger 62; decisions 3,000) | — | decided-truncation **0.0151** [0.0105, 0.0216]; whole-mirror H′ **0.2117** [0.1958, 0.2285] | capped share **0.21563 [0.17681, 0.26028]** on 371 counted games (partial run, §Status); cap reasons: 80 turns, 0 decisions |

## Appendix — the run's 373 game ids (unregistered; preserved from `games_meta.jsonl`)

Half A (187): 878785813,752462551,989991581,425702674,784759505,294513206,965552975,188931295,952496597,926858857,131118337,171700119,138194054,634031595,234581840,936818207,424186831,440528463,883919384,837442086,283298674,558367261,490596425,228427830,342095826,282748286,347722913,427344475,994710477,121491696,318352861,426597260,105067140,810257705,567956634,489646338,833252458,654266795,970436275,991446855,318036811,967296774,545307265,650347212,841595652,138364567,986511276,611464293,574084763,836685314,192198368,533091252,831416407,862564691,175712449,667383993,567700662,410749965,170455852,456158763,353861389,536700946,311869940,764687062,525939969,339058765,413714083,259156303,592359281,731893993,970665998,662425398,428293247,834279491,928770773,532188654,764572104,724059274,926695613,165950107,733704587,707138145,629664296,901062087,246216405,468029371,619543821,352526070,284993642,846598903,146796086,257141123,196508051,957659267,169529580,153319462,102678949,655099828,463558473,479109539,620475006,177178197,439016809,417035591,589125869,116841241,903020751,841209749,239534212,352078882,918484258,866018124,474904014,481822167,793893912,783334546,987306509,392871467,910382568,393476785,379687779,863695874,916621003,595018922,607508786,994995878,820765027,131402017,468671393,898097800,849365969,944541281,454771479,921909488,624374930,194209766,513534329,160921131,758983309,813566986,337052157,872265869,396927403,516755178,314464515,929260228,794245376,111190814,281838517,276864124,413759431,642606156,346670536,963997530,386456386,644997886,522971646,575932132,576056084,858918109,129768166,690494622,902505318,301273701,922961204,971224962,629340617,241993250,720101775,248910028,245120349,628267574,197795173,633660895,217534323,178815858,282669788,648599934,120671090,931185940,760264150,884876807,205046037,908422680,974233216,288032269,505190481

Half B (186): 162873170,766410986,942026523,915155672,924111215,599455161,629892601,431769617,266935455,500949483,425128780,943942997,336104263,814380467,703871043,248647344,631706980,770382263,760753145,422717999,796712068,360601853,290416250,650226857,182663629,479306417,890599010,965409329,746365674,819168023,737208149,983032034,594818243,513451914,919238941,608161302,116728763,764739757,901431424,544835377,705217846,281046242,921178550,726310048,863437946,765672380,820630561,921855678,630870593,952250481,280988195,844695293,521362665,297069659,847503444,764850135,437290270,385109646,732654348,105056839,244606860,268966013,712273077,489537473,951843041,138087728,101345984,623665982,350171743,399979059,271776100,789880281,310565709,937913045,130972137,754486293,497994713,746708924,977085581,551730508,681311896,985274601,904989824,913822407,966410572,186196153,214032407,118247222,183262493,500075782,672934913,536419806,879641871,599377503,387065387,343460613,296757445,254653671,644577539,911050960,578675327,767968535,338139367,548858366,598520682,763182178,119504128,811563576,611884025,574276603,533240149,889432015,547247294,335798435,130534438,929680812,599853485,110738314,638533723,344319919,300875107,362251016,573432253,879482661,310593097,100190595,167917786,240835047,423302561,901445896,610972709,202138620,695955531,699615752,344913510,878427354,793538970,574802949,892070588,140353831,788553513,109391663,461590731,997821339,498441617,727370736,160571618,197530563,889602931,830137440,143316947,373007328,572578830,951227535,199049946,627644494,172239714,913342142,939125995,673260562,572868132,795040254,954977617,310347945,477171296,648482521,649867948,914598776,448313163,620069163,192534175,483372001,798444986,763375185,663694834,529656705,834830757,360862063,124775113,897969099,105434602,924870119,661660044,820616446,610608253,776510683
