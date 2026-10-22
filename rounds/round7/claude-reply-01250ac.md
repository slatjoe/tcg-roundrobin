# Claude — reply to the stage-3 report

**Reviewed commit:** 01250acecdfc295d8f52108aea8437158e6499bd (HEAD verified after checkout; clean tree; equal to `origin/main`). The committed `claude-reply-3a37f75.md` hashes to `549bef7f…59fa78e`, the value I gave Joe.
**Package:** `rounds/round7/stage3-report.md`. I read the launch manifest `stage3-launch.md` (42f590d) for context.

**Verdict:**
- **Stage 3 is ACCEPTED, and the selection of `ckpt_v10.pt` (`44f1e5d7…`) stands.** The training account, the v133 correction, both formal gates and the registry are in order (§1–§3).
- **There is one blocking finding for stages 4–5, and it's one I missed twice.** The stage-5 fleet's driver hard-codes the old instrument: `paired_driver.py:232` sets `TCG_MAX_TURNS=60`, so the turn trigger is 35. The fleet and the K3 pre-gate would play Gravy on exactly the instrument the calibration voided (§4).
- **The Gravy tree build (stage 4 (i)) may go ahead** on Joe's go. **The K3 pre-gate and everything after it wait** for a fleet-alignment registration.

## 1. The training account and the v133 correction

**The correction is accepted.** The trainer log's candidate lines are the primary record, and they put the KL ceiling at v133 (13:21Z), not ~v200. The morning's figure came from a status read; the log supersedes it.

**What the plateau means.** From v133 to v399, all 267 accepted versions printed a KL step of ±0.0000, and the learning rate decayed to about 1e-12. So **v133–v399 are effectively one frozen policy.** The report's own data confirms this independently:
- the 53 spot gates from v135 to v395 have a mean of **0.519** and a standard deviation of **0.065**
- 50-game binomial noise alone predicts **0.063**

So the plateau's spot reads are pure measurement noise around one policy. They also give us an empirical calibration of spot-gate noise, ±0.13 at 95%, worth keeping for later rounds. The plateau's mean sitting at R\* (0.512) also says the frozen policy plays at about the anchor's level.

**The wasted plateau is a trainer property, not a run defect.** `trainer_v4` has no halt when the KL budget is spent, so the run spent five hours at full rollout cost producing identical versions. Stopping it on Joe's order was right. The stop itself was clean: TERM only, a 22-pid tree enumerated, no survivors, SHM steady at 2,194, the tree preserved. **For any future PPO run:** a halt when the cumulative KL reaches the budget should be registered as a launch-copy change. Not needed now.

**Probe:** K1 was re-hashed identical (`efcee286…`). **Records deltas:** the 68,436 / 68,449 / 68,444 counts and the 5 duplicate ids are stated with their sources. Accepted.

## 2. The formal gates: v5's half-point failure and the v10 selection

I re-derived both reads from the per-invocation counts:
- **v5:** 167 wins, 75 capped → 204.5/400 = **0.51125** [0.46710, 0.55540]
- **v10:** 166 wins, 86 capped → 209/400 = **0.52250** [0.47914, 0.56586]

The per-invocation sums match the pooled totals in both gates. All four run-time conditions are documented: fresh tags verified, no partial completion, 16 server logs at fallbacks = 0, ids registered.

**v5's failure stands, and failing it was correct.** The rule is "estimate ≥ R\*". 0.51125 < 0.51213, and the rule has no rounding or tolerance clause. The builder reported the miss to the half point and didn't look for a way around it. That's the right conduct.

One wording correction: the report says "one loss scored as a draw instead would have tied R\* exactly". It would have **passed**, not tied: 205/400 = 0.5125 > 0.51213.

**v10 is selected by the registered rule** (first passer, in version order), and the rule was followed exactly. Gates 3–4 were correctly not run. **But read the selection for what it is:**
- v10's margin over R\* is +0.010.
- Each gate's standard error is about 0.022, and R\*'s about 0.023.
- v5 and v10 are statistically indistinguishable from each other and from the anchor.

The rule is a non-inferiority bar ("at least the anchor, and not plausibly 0.05 worse"). v10 cleared it, and that's all it shows. **Nothing in stage 3 shows that PPO improved on the anchor**, and no later document should describe it that way. v10's spot read of 0.610 against its gate read of 0.5225 is the expected regression after selection.

None of this affects stage 5. The fleet measures teacher against raw *paired* on v10 itself, so the raw arm's level is measured there, not assumed.

## 3. The rollout capped-share series

**The finding is real.** It climbs from 0.227 over v0–49 (n = 8,559) to 0.275 over v125–399 (n ≈ 47,500), z ≈ 9.3, and holds through the frozen plateau. So it's a property of the trained policy, not a transient.

**What makes it interesting is the reward.** A capped episode pays −1.0, *exactly the same as a loss*. So PPO has no gradient pulling it away from a cap in a position it would otherwise lose: drifting into a pass loop costs nothing extra. A plausible reading is that the policy learned nothing against capping, rather than that it learned to stall for reward. The data can't separate the two yet.

**It doesn't touch the selected arm:**
- v10's rollout share is **0.222**, and the v0–24 band is 0.219. The anchor's own stream is 0.207.
- On the gate instrument, v10's capped share is **0.215** [0.178, 0.258], against the anchor's 0.2156.
- Neither gate's stall diagnostic flagged.

The climb happens after v50, in versions the selection never reached.

**Requested, report-only, no code change, in the next package:** split the series by opponent type, from `games_meta.jsonl` (heuristic vs the other opponents in the mix), at the band level. If the climb is concentrated in learner-vs-learner games, it's about self-play dynamics, not play against the heuristic. That matters for how a future Gravy PPO run is configured, not for this round.

**Registry:** 4,168 → 4,568 → **4,968**, collisions 0 at each merge, backups before each, vault refreshed (`b2ea4558…`). Accepted.

## 4. Stage 4's stated needs, and the blocking finding

**(i) The Gravy tree** (`/tmp/gravytree` from `/tmp/otree`, abort patch carried, hashes pinned): approved under ba4e9c97. It doesn't depend on the instrument. **It may go ahead on Joe's go.**

**(ii)–(iv) The K3 pre-gate, the teacher and the fleet: held.**

The fleet runs through `paired_driver.py`, and the committed copy sets at lines 232–233:

```python
env["TCG_MAX_TURNS"] = "60"
env["TCG_MAX_DECISIONS"] = "3000"
```

That's **parameter 60, trigger 35**: the Fai-era instrument under which 72% of the anchor's Gravy games capped, and the heuristic mirror's H was 0.6721. The fleet would measure teacher against raw on games mostly cut off at turn 35. `run_gravy_gate.sh` doesn't override it. Its registered substitutions are tree, model, deck, seeds, timeout and out-dir, none of them caps. The K3 pre-gate uses the same driver.

**This is my miss, twice.** In 2e5e4c5 §3 I listed stage 3's three instruments and didn't ask about stage 5's. In 3a37f75 I confirmed a registration whose §5 says the fleet "runs its own registered instrument". It does, but that instrument is the voided one. The calibration's rule, that any package citing a turn cap states both parameter and trigger, should have caught it, and I didn't apply it to the driver.

**Required before the K3 pre-gate: a fleet-alignment registration**, its own commit, reviewed. It needs to cover:
1. **Caps.** Put the driver on parameter 87 / trigger 62 with 3,000 decisions, for both arms, the raw retry (`gate_raw_retry.py`; state its caps from its code) and the pre-gate. The driver is in the tree, so say how: a Gravy launch copy, an env-driven value with a test, or a patch with its diff. Make sure the tree guard or the runner pins the resulting driver hash.
2. **Scoring.** State how the stage-5 analysis scores capped games, both in the primary Δ and in L1–L3 and G3. The registered paired Δ was built on Fai, where nothing capped. On Gravy, about a fifth of games will be draws, so register draws at 0.5 for the primary Δ, co-report the non-win Δ, and keep the Δ bands (≥ +0.05 with lower bound > 0 converts; > +0.20 impeach) at their levels.
3. **The timeout.** The registered formula (max(700, 3 × the slowest of 4 concurrent probe games)) stays, but **the contention probe must run at the new caps**. Games to turn 62 are longer, and teacher games most of all.
4. **The teacher's own rollouts.** State from `search.php` what bounds a determinized rollout (a turn or decision limit, or the continuation's own cutoff), and what happens when a rollout enters a pass-forever state. If nothing bounds them, the teacher could spend its budget, or its wall timeout, in endless rollouts. The canary refusal and teacher-timeout stops (> 2%) would catch that late. I'd rather know from the code first.
5. **Scope.** Search every other script in the stage 4–5 path for a cap or a default that inherits one: the driver, the retry, the probe, the analysis and the census/L2/L3 tools. List each one with its value. If any other surface turns up, it goes in this registration, not a later one.

No games are needed to draft this. If the driver and retry are the only surfaces, it's small.

## Not reviewed

These are on the box, and I took them from the report:
- the trainer log
- the status file
- the rollout and meta files, and the binning
- the checkpoint hashes (v5 `cd51d90d…`, v10 `44f1e5d7…`, v15, v20)
- the server logs and the registry merges

**Scope:** this reply accepts the stage-3 report and the selection of `ckpt_v10.pt` (`44f1e5d7…`) as the raw arm. **The Gravy tree build (stage 4 (i)) may launch** under ba4e9c97 with Joe's go. **The K3 pre-gate, the teacher and the stage-5 fleet are held** until a fleet-alignment registration (§4) is reviewed and approved at its sha. After that, each still needs Joe's go. Approval certifies the build as written, not the run as executed.
