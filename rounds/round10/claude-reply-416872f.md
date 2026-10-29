# Claude — review of the Step 0 probe's fix pass 6 (the influence completion)

**Reviewed commit:** 416872f5838ca512893d7de40a33b276fc5458ca (HEAD verified after checkout; clean tree; equal to `origin/main`). I also read the recovery-run record and outputs at a083f013.
- **Launched sha:** 3ef1815a, which differs from the approved d17a4540 only under `rounds/`.
- **My last reply:** the committed `claude-reply-d17a454.md` hashes to `bb3f4945…c758504`, the value I gave Joe.
- **Hashes:** `probe_influence.py` is `dc79bdad…`, `run_probe_completion.sh` is `fb7b7a02…` and the doc is `6534c75b…`.

**Verdict: CHANGES REQUESTED, one blocking item.** The fix itself is right. But **the completion script inspects the wrong game** (§2). §3 also says something about the threshold number the report printed, before it travels any further.

## 1. Checks

- **The fix.** The influence diff is the one initialization, `logo_by_lever = {}` before the LOGO loop, plus a header note. Reversing it gives the run's pinned `83f4f1d1…` exactly.
- **`fx_influence_main.py`** drives the real `main()` by subprocess in both modes. The hold rule fires through `main()` on a concentrated synthetic case, which is the composition gap closed at the level it lived at.
- **The run's outputs are as recorded.** `probe_influence.txt` is 0 bytes, with no `probe_influence.json` and no `recovery_manifest.json`. Decompressed, `labels_merged.jsonl.gz` hashes to `c2688f24…`, 71,500 rows.
- **The completion's pins:** 10 literals, every one matching a file at HEAD, except the decompressed-content hash, which I verified directly. The refusals are correct. The capture-games list is rebuilt from the published driver rows, and I verified the count of 90.
- **Fixtures, run here** on a scratch copy: **190 checks, ALL PASS.**

## 2. Blocking: the completion passes `--game 440261752`

- `run_probe_completion.sh` line 249 passes `--game 440261752`.
- The game the inspection exists for is **540261752**. That's `probe_influence.py`'s own default, and the recovery's invocation (lines 451–464) passed no `--game` and used it.
- **440261752 isn't a capture game.** It appears in neither driver file.
- So the "completion" would print a state inspection of nothing, under a registered step, while differing from the invocation the recovery registered.

**Required:**
- **Make the completion's argument list the recovery's** (lines 451–464), with paths adapted and nothing else. Drop `--game`, or pass 540261752.
- **Add a fixture** that extracts both invocations verbatim and asserts their flag sets are equal once paths are normalized. That catches any future drift, and this typo.
- **Add an in-script assertion** that the inspected game id appears in the published driver rows, aborting otherwise.

**Non-blocking:**
- `run_probe_recovery.sh` should keep the pin it **ran** with (`83f4f1d1…`): it's the record of what executed. The fixed pin belongs only in the completion script, which already carries it. Revert the one literal and note it in §15. Git history preserves the as-run file either way, so this doesn't hold the completion.

## 3. Before the threshold number travels: what +0.4734 per game is

The report's recommendation, threshold 0.97 with a lower bound of +0.2080, is the registered rule's output, and it stands as the rule's output. **But +0.47 per game is not a prediction of what a threshold teacher would gain in games, and it must not be used as one.** It's the probe's estimand taken outside its range of validity.

**I reproduced it exactly from the published rows:** 305 uncontested-class jobs, cap-aligned diffs, weight 2, over 90 games = **0.4734**.

**Why it overstates:**
1. **It's an additive sum over the raw policy's trajectory.** It's about 6.8 weighted fires a game (305 × 2 / 90), each valued as if independent. The CI's upper end, **0.86**, is more than the base win rate leaves room for, which is the giveaway: per-decision edges don't add into win probability that way.
2. **Repeated presentations of one mistake are counted every time they recur.** On the raw trajectory, an un-fixed stall re-presents itself turn after turn. A teacher that fixes it once changes the trajectory, and the later repeats never happen.
   - The 305 jobs are 276 distinct (game, prior card, teacher card) choices.
   - One game, **635852068**, carries 18 jobs summing to 6.80 in diff, about a third of the whole gain.
   - **Bounding illustrations, not registered reads:**

     | Counting | Per-game gain |
     |---|---|
     | As registered (every fire) | 0.4734 |
     | Each distinct choice once | about 0.27 |
     | Only the best single fix per game | about 0.13 |

   - All of these are still above Stage 3's whole teacher (0.065). That's why the lever's signal is real, but the size isn't 0.47.
3. **Round 9's per-game gain was a different estimand.** There, the fires sat on the teacher's **own** trajectory, already conditioned on its earlier fixes. The Step 2 gate as registered measures exactly that again: capture games played by the threshold teacher. That's the right estimand for the lever's real value.

**What follows:**
- **The influence completion still runs**, as registered: the state inspection of game 540261752, LOGO, and the hold rule. The hold rule is mechanical and will say what it says.
- **The probe report gains this interpretation** as a labeled addendum when the completion's outputs are published.
- **Any Step 1 package must not size Step 2 or a fleet from +0.47**, and the printed "power 1.000" isn't credible input. Step 2's sizing uses round-9-style live-trajectory numbers, or a conservative bound stated as such.
- **Step 2 is priced at 1,840 s per teacher game:** about **205 box-hours for 400 games, roughly 51 h of wall time.** A smaller live pilot of the threshold teacher, to see its realized fire rate and on-trajectory gain before the full gate, is worth considering in that package. It's Joe's call on cost.

## 4. Then

The §2 fix (the argument list, its fixture and the game assertion) comes back for a confirmation check. The completion then runs once on Joe's go.

**Scope:** this accepts the influence fix and the composed-path fixture at 416872f5, requests the §2 change, and records the §3 interpretation for the probe report and any Step 1 package. No run is approved yet.
