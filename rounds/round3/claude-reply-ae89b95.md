# Claude — reply to the round-3 builder response

**Reviewed commit:** ae89b950012c41ff33c83be617b4c9b693202303 (HEAD verified after checkout; clean tree)
**Package:** rounds/round3/builder-response-df64eb9.md
**Verdict:** NEEDS INFO on the remedy ruling: the finding is real, but its attribution is not established, and the trace data you already have argues against it. The R1–R7/S1–S3 build is **APPROVED WITH REQUIRED CHANGES** (R8–R11). No launch is approved.

What I ran: `test_classify.py` (10/10 pass); `bash -n run_r3.sh` (clean). I read the diff since df64eb9, the classifier, the pairing script, the probe patches, the featurizer, and the final-pair data. I can't run the engine or lint PHP.

---

## The remedy ruling: localize first, because the evidence contradicts "the checkpoint block did it"

Your finding stands: inside a single teacher row at a P decision, `p1Hand` loses a card and `p1Resources` moves `[0,0] → [0,1]`. That is the machinery writing live state, and it blocks the launch. But the attribution to `DoGamestateUpdate` is inferred from "the only writer in the window", and your own trace says otherwise.

- The classifier checks `feat` before `zone`, and it reported **zone**. So `feat_pre_hash == feat_post_hash` at seq 38.
- `feat_post_hash` is the state that `SimSearch_EvalState` built **inside `SimTeacher_Decide`, after the checkpoint block**.
- `SimFeat_BuildState` reads the own hand via `GetHand($player)` and encodes the full ID list plus `hand_size` (featurize.php lines 63–96).

If the checkpoint had removed `flamecall_awakening_red` from the hand, the post-checkpoint featurization would differ from PRE, and the verdict would be WITHIN_ROW(feat). It wasn't. So one of these is true, and each implies a different remedy:

1. **The mutation happens after Decide's `EvalState`.** On the uncontested path that leaves `SimSearch_LogStat`, the return, and the POST capture code itself. That would point at the trace patch or at something lazy in the engine, not the checkpoint.
2. **`GetHand(1)` is not the array `$GLOBALS["p1Hand"]` at that moment** (a staging copy, a `myHand`-style alias, or a pending-pitch structure). Then the zone sensor and the featurizer are watching different objects, and "hand lost a card" may mean the engine staged a pitch that it would have applied anyway.
3. **The checkpoint does it, and the featurizer misses it**, which contradicts point 2 of BuildState as written. That makes it least likely, but possible if BuildState is served from a cache.

Note also that the card left the hand but the report doesn't say it entered `p1Pitch`, which is in the key list and featurized. A real pitch moves the card to the pitch zone. Only `resources[1]` moved, and the featurizer reads only `resources[0]`. That is more consistent with a staged or pending operation than with a completed pitch.

**Ruling:** none of (a), (b) or (c) is chosen yet. Run one localization probe on seed 3 at seq 38, ghost arm. It's deterministic, takes a few minutes, and is diagnostic only, no launch. It needs:

- **Zone dumps at five points:** before `DoGamestateUpdate`, after it, after `WriteGamestate.php`, after Decide's `EvalState`, and immediately before RootDecide returns.
- **At each point, record:** `p1Hand`, `p1Pitch`, `p1Resources`, the `GetHand(1)` return, `GetResources(1)`, and `decisionQueue`/`layers`.
- **The raw arm at the same seq,** dumping the same keys at the bridge pick and right after the engine applies it. This tells us whether hand-3/resources-`[0,1]` is a state the raw game also passes through (an ordering effect) or one it never sees (a real side effect).

**How the remedy follows:**

| Localization | Remedy class |
|---|---|
| Checkpoint block mutates live globals | **(b)**, done generally rather than pitch-aware: snapshot the full engine globals before the checkpoint and restore them after, or produce the checkpoint file from a serialized copy without calling `DoGamestateUpdate` on live state. "The machinery never writes live state" must hold on every branch. Skipping only P leaves the same class open on the next branch with a staged operation. |
| After `EvalState`, in the trace or stat code | Fix the instrumentation. Not a machinery finding. |
| A `GetHand`/global alias or engine staging, with raw passing through the same state | Fix the sensor (hash what the engine actually plays from). Document it. Within-row equality is then measured on the right object. |

**(a) is not acceptable in any case.** "Benign because the pick agrees" fails exactly in the case the teacher exists for, an overturn. **(c) is a fallback only** if the mutation can't be removed, and it must be registered as a scope limit, not presented as a fix.

**One consequence to check regardless of the answer:** the §3 harvest copied snapshots from the checkpointed game dir. If the checkpoint settles or stages pitches, P-branch snapshots pair a post-pitch state with a pre-pitch candidate list. P carried ~3% of the §3 gain, so the effect on the headline is small. But report how many §3 decisions were branch P, and mark them suspect until the localization clears them.

## Required changes

**R8. Classifier must not stop at the first within-row hit.** As written, one WITHIN_ROW at seq 38 ends the comparison, so the launch would never see a later cross-arm divergence. Report two things separately:
- every within-row hit, with seq, branch, pair and rule
- the first cross-arm divergence, scanning past within-row hits

*Pass:* fixture with a within-row hit at seq 1 and a DECISION at seq 3 reports both.

**R9. `steps` must be the real step counter or be removed.** A field named `steps` that reads 1 for a 16-turn game will be misread later. Record the engine's actual step or decision count under a correct name (the decision counter `simPolicyDecision` at game end is available and honest), or drop the field.

**R10. Explain the final-gamestate hash difference before it becomes a PASS field.** Diff the two kept files (raw `958bdcd3…`, ghost `fbc2c221…`). If the only differences are the game name and other per-game identifiers, normalize them and add the normalized hash to the R3 outcome fields. If anything else differs, that is a FAIL-outcome observation with byte-identical gamelogs, and it goes in the next package.

**R11. Pairing table additions.** `r3_pair.py` should carry each arm's mode line and `connect_failed`, and fail a seed if either arm's mode line doesn't match its arm (raw: `policy: server`; teacher-family: `policy: search`). That is the misbuild class we've hit twice, checked per seed.

## On the rest of the response

- **§5 discharged.** The gamelog gap was the fingerprint children's `exit(0)` flushing inherited buffers into the parent log, and SIGKILL removes it: 104,690 bytes, byte-identical. Accepted. One point for the record: the 175× inflation means every round-3 smoke gamelog before this commit is unusable for line-level analysis.
- **S1 for rollout children:** apply it in the next commit anyway. Your evidence that they don't pollute is good for seed 3, but it's one line and removes the class.
- **R4 left as loud failure:** accepted. Restructure the fall-through in a later reviewed change.
- **R5:** good catch, and nine phantom keys is the reason the sensor needed checking. The canonicalization of `"0"` vs `0` is fine as long as it's applied to both sides, which it is.
- **R7 and `run_r3.sh`:** fine. Confirm `paired_driver.py` exists in `$TREE` (the script `cd`s there and calls it by bare name), or call it by its path.
- **VOID banner on round 2:** accepted.

## Not reviewed

- Vendor engine internals: `DoGamestateUpdate`, `WriteGamestate.php`, `GetHand`/`GetResources` definitions, and the pitch flow. The localization above is what substitutes for reading them. If you can commit `GetHand`, `GetResources` and `DoGamestateUpdate`'s source, I'll read them in the next round.
- The diagnostic probe output itself (per-key dumps) is described in the response but not committed. Commit the seq-38 dump with the next package.

**Scope:** approval of the R1–R7/S1–S3 build is valid only for this sha, as the base for the R8–R11 and localization work. No launch is approved. The launch returns for approval on the commit that carries the localization result and the chosen remedy, under the restated §3 reads, and still needs Joe's go. Approval certifies the build as written, not the run as executed.
