# Builder response — claude-reply to round 3 (reviewed sha df64eb9)

**Reviewed commit:** df64eb95fca62c159a2281aa885a2428c6919bb4
**This commit's parent:** df64eb95fca62c159a2281aa885a2428c6919bb4 (the relay
message supplies this commit's own sha, per PROTOCOL.md).
**Ask — CHANGED by the R2 evidence below:** this commit does **not**
ask for launch approval. The within-row sensor caught a real
checkpoint effect at pitch decisions (§R2), and under your restated
reads a launch requires within-row checks clean. R1–R7 and S1–S3 are
delivered; the ask is your ruling on the remedy class for the pitch
finding, after which the corrected build returns for approval.
Conventions: win figures are win rate; all played policies are argmax.

## §0 consequence — done

Your instruction to mark the round-2 mechanism hunt void in its own file
header, not merely superseded: `rounds/round2/consolidated-update-to-claude.md`
now opens with a VOID banner over its §7 (this commit; the body is
untouched, per the verbatim rule — the banner is an addition above it).

## §5 condition — discharged, and the mechanism found

1. **Steps.** The driver now records `steps`, `p1life`, `p2life` (R3).
   Seed-3 values: raw `steps 1, p1life 2, p2life 0`; ghost identical.
   Caveat, reported rather than smoothed: the result JSON's `steps`
   reads 1 for a complete 16-turn game in both arms, so it is **not**
   the engine step counter your condition assumed — it is recorded and
   equal, and it cannot carry the weight the condition put on it. The
   step-count evidence that does exist is in (2).
2. **Gamelog diff, classified.** On the original smoke gamelogs: **zero
   line types exist only in the ghost log**; all 21,130 excess ghost
   lines are extra copies of lines present in the raw log (top excess:
   auto-pass lines ≈ +6,000, "The chain link was resolved." +1,405).
   The mechanism is now identified, and it is the instrumentation's
   own first version: the trace patch's RNG-fingerprint children ended
   with `exit(0)`, running inherited shutdown handlers and flushing
   inherited log buffers into the parent gamelog — repeatedly, at
   every traced decision, in every arm (the raw log was inflated
   ~175×: 18,377,142 bytes vs a clean 104,690). With S1 applied
   (fingerprint child dies by SIGKILL after writing), a fresh seed-3
   pair's gamelogs are **byte-identical** (sha 88231b961d202c19, both
   arms, 104,690 bytes). The gap was a log-only artifact of the probe,
   not of the machinery under test. Criterion stands as you ruled it.

## R1 — launch script

`rounds/round3/code/run_r3.sh` is the exact script (the `<arm>`
redirect bug is real — bash would have eaten it as a redirect —
and the script uses `$arm` throughout). `bash -n` clean. It replaces
§4's template; nothing else about the launch changes.

## R2 — WITHIN_ROW class, and what it caught

Classifier: `WITHIN_ROW` (pairs feat, zone, rng) is checked before
STATE; the `trow` fixture now encodes within-row equality as normal,
and there are fixtures for each pair (10/10 pass, below). The STATE
and RNG cross-arm fixtures were also made internally consistent —
your ordering makes an internally-inconsistent row a WITHIN_ROW case
by construction, which the first fixture draft got wrong twice.

Rerunning the new classifier on the **original** smoke traces reports
`WITHIN_ROW (zone)` at seq 38, branch P (the cross-arm field equality
across all 653 rows reported in round 3 stands behind it — the
classifier now simply reports the within-row anomaly first, as
designed). The per-key probe (diagnostic patch,
`code/patch_zoneprobe.py`, scratch tree) names **two distinct
checkpoint effects**, and they are not the same kind of thing:

1. **Seq 3, branch ARS — representation only.** `p1CharEquip` /
   `p2CharEquip` change across the checkpoint, but only by re-typing:
   the string `"0"` becomes the integer `0` at equipment sub-fields.
   Content, order, cards unchanged; the JSON encoding changes, so
   the hash moved. Response in code: the zone hash now canonicalizes
   numeric strings before hashing (sensor measures content, not
   representation). On the final pair this hit is gone — the first
   within-row report moved from seq 3 to seq 38, confirming the fix.
2. **Seq 38, branch P — real content.** Across the same window at a
   pitch decision: **`p1Hand` loses `flamecall_awakening_red`
   (4 cards → 3) and `p1Resources` goes `[0,0] → [0,1]`** — the
   pitched card leaves the hand and its resource is credited, inside
   the teacher row. The decision was **uncontested** (stat row:
   contested 0, no rollout children forked), so the only writer in
   the window is the checkpoint block itself:
   **`DoGamestateUpdate` settles the staged pitch in the parent's
   live globals before the engine's own flow applies the returned
   pick.** Every cross-check still passes — the settled card is the
   card the decision concerned, the returned pick agrees with it,
   decisions/gamelogs/outcomes are identical — but the parent state
   is mutated by the machinery at pitch decisions, and the danger
   case is plain: a teacher **overturn** at a pitch decision would
   return an index for a state that has already pitched a different
   card. (Branch P carried ~3% of the §3 positive gain, so the case
   is rare, not imaginary.)

This is why the ask changed. Under your restated reads the launch
requires within-row checks clean; at pitch decisions they are not.
Remedy classes, for your ruling rather than my choice: (a) accept
pitch-settling as benign-by-construction, with the overturn-at-pitch
case explicitly registered as out of scope or handled; (b) make the
checkpoint pitch-aware (skip or restore around pitch decisions);
(c) restrict the teacher's authority at pitch decisions. The final
pair's classifier verdict is `WITHIN_ROW (zone)` at seq 38 P — see
`data/final-pair-table.md` — with gamelogs byte-identical and
outcomes equal behind it.

## R3 — outcome fields

Driver rows carry `steps`, `p1life`, `p2life` (and `gamestate_sha`,
S2). Seed-3 values in §5(1) and in the final pair's rows
(`data/final-pair-rows.jsonl`).

## R4 — DUP_SEQ

The loader now detects a duplicated seq and the classifier returns
`DUP_SEQ` before any comparison; fixture added. The underlying
double-write path you identified (Decide returns null → teacher row,
then Choose falls through to a `bridge_pick` row at the same seq) is
not restructured in this commit: under the restated reads a DUP_SEQ
verdict invalidates the seed loudly, which is the behavior the launch
needs; restructuring the fall-through is a search.php change I did
not want to bundle unreviewed.

## R5 — zone keys verified against the engine

You were right, and in the specific direction you guessed. The first
list hashed **nine keys that do not exist** under those names
(`p1Character`, `p1Graveyard`, `p1Life`, `mainPlayerActionPoints`,
`mainPlayerRemainingResources`, and mirrors). The list is rebuilt
from `ParseGamestate.php`'s assignments: `p1CharEquip`, `p1Discard`
for the graveyard, life as the `playerHealths` array, `p1Resources`/
`p2Resources`, single `actionPoints`, plus `chainLinks`,
`combatChain`, `layers`, `decisionQueue` (32 keys). Once per game the
trace logs `zone_null_keys`; on the seed-3 game it reported exactly
`["numChainLinks"]` — assigned in the parser source but absent as a
global at decision time — and that key is dropped from the list in
this commit (`chainLinks` carries the content).

## R6 — pairing script

`rounds/round3/code/r3_pair.py`: seed → gamename → trace per arm from
the driver rows, classifier per pair, one table with the R3 outcome
equality beside each verdict. Final seed-3 table:
`data/final-pair-table.md`.

## R7 — seats

`run_r3.sh` runs raw and ghost at `--seat 1` **and** `--seat 2` on
seeds 1–18,20; shadow and capture remain seat 1.

## S1–S3

- **S1** adopted for the fingerprint child (`posix_kill` SIGKILL
  after its write; §5 shows it was the pollution source). The
  teacher's rollout children still `exit(0)`. Evidence for leaving
  them: the raw arm — which forks no rollout children, only
  fingerprint children — showed the full ~175× inflation, so
  fingerprint forks suffice to explain the artifact in every arm.
  Converting the rollout children too is a one-line follow-up if you
  want it regardless.
- **S2** adopted: `gamestate_sha` per row. One observation, reported
  without a theory: on the fresh pair the final gamestate hashes
  DIFFER (raw 958bdcd3e1001d11, ghost fbc2c221711748d0) while the
  gamelogs are byte-identical — plausibly the embedded game name in
  the serialization; the two files are kept on the box if you want
  the diff chased.
- **S3** verified from `search_server.py`'s dispatch: requests are
  routed by seat, and the learner seat gets `net_argmax` regardless
  of branch — **DQ included**. The comment in `policy_server.php`
  ("the server echoes it back") describes Phase A. What "v15 plays
  DQ decisions" means in every bridge eval: the net's argmax over
  the DQ candidates under the DQ featurization; v1's pick enters
  only as a candidate feature (`v1_score`), never as the answer.

## Confirmations from your "Not reviewed"

- The box's gate-tree `search.php` sha256 begins `ca367b37c944` —
  the repo's `code/search-gate-tree.php` is the same file.
- PHP lint: both patched files pass `php -l` on the box after this
  commit's patch (patch re-applied to a fresh gate-tree copy).

## Tests run for this commit

- `test_classify.py`: **10/10** (IDENTICAL, STATE, CANDIDATES,
  DECISION, RNG, MISSING_ROW, WITHIN_ROW ×3, DUP_SEQ).
- `bash -n code/run_r3.sh`: clean.
- Fresh seed-3 pair on the final tree (raw + ghost): rows and
  pairing table in `data/`; classifier verdict `WITHIN_ROW (zone)`
  at seq 38 P (the pitch settling, §R2), gamelogs byte-identical,
  outcome fields equal.
- Original smoke traces through the new classifier: WITHIN_ROW(zone)
  seq 38 P, as reported in R2.

## §3 reads as restated — adopted verbatim

PASS = 19/19 seeds IDENTICAL by the classifier for raw vs ghost, raw
vs shadow, ghost vs capture; within-row checks clean; outcome fields
equal; the gamelog gap explained as log-only (done, §5).
FAIL-localized and FAIL-outcome as you wrote them; any
`shadow_fallback_decide` row, connect failure, canary refusal, or
MISSING_ROW invalidates that seed and is reported, not dropped.

**Scope request:** no launch is requested on this commit. Approval
is sought for the R1–R7/S1–S3 build as written, plus your ruling on
the pitch-settling remedy class (§R2). The launch in
`code/run_r3.sh` returns for approval on the corrected build, under
these reads only, and still needs Joe's go after your approval.
