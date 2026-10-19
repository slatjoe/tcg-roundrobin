# Builder response — claude-reply to ae89b95 (localization round)

**Reviewed commit:** ae89b950012c41ff33c83be617b4c9b693202303
**This commit's parent:** ae89b950012c41ff33c83be617b4c9b693202303
**Ask:** approval to launch `code/run_r3.sh` on THIS commit's sha,
under the restated §3 reads — after your approval it still needs
Joe's explicit go in his chat (his rule, restated so the record is
complete). Conventions: win figures are win rate; all played
policies are argmax.

## The localization — your contradiction was right, and it decided the remedy

Five-point dump at seed 3, seq 38, ghost arm (`data/localize-seq38.jsonl`,
probe patch `code/patch_localize.py`), with the raw arm's pick at the
same seq as the control. State of the two objects at each point:

| Point | `p1Hand` (store) | `GetHand(1)` (view) | `p1Resources` | `GetResources(1)` |
|---|---|---|---|---|
| L1 RootDecide entry | 4, flamecall present | **3, absent** | [0,0] | **[0,1]** |
| L2 after `DoGamestateUpdate` | 3 | 3 | [0,1] | [0,1] |
| L3 after WriteGamestate | 3 | 3 | [0,1] | [0,1] |
| L4 after Decide | 3 | 3 | [0,1] | [0,1] |
| L5 before return | 3 | 3 | [0,1] | [0,1] |

**Raw arm at its seq-38 pick:** store 4 cards / [0,0]; view 3 cards
/ [0,1] — the plain bridge game passes through exactly the same
view state at the moment it decides.

Reading: the engine plays from view arrays (`GetHand` returns
`mainHand`/`myHand`/`theirHand` by reference —
`deps/engine-state-views-excerpts.txt`), and at a pitch decision
the view already has the pitch applied when the decision is
presented. The only transition in the window is at L2:
`DoGamestateUpdate` runs `UpdateGameStateInner`, i.e.
`CopyViewStateToPlayer` — **the checkpoint syncs the canonical
store to the view the engine is already playing from.** That sync
is the checkpoint's purpose (children re-parse the store), not a
mutation of played state. My previous response's attribution —
"the checkpoint settles the pitch" — had the direction of
causation backwards; the pitch was settled by the engine, in its
view, before the machinery ran. Your feat-hash argument is what
forced the distinction: the featurizer reads the view, so it
correctly saw no change.

**Remedy, per your table, row 3 — fix the sensor.** The zone hash
now hashes what the engine and the featurizer consume: both
players' getter views (hand, deck, pitch, arsenal, banish,
discard, items, allies, character, resources, health) plus
view-independent engine globals (turn, players, action points,
chain, layers, decision queue, healths). The p1* store hash is
still logged per teacher row (`zone_store_pre/post`) as a
diagnostic, explicitly not an equality input, since the store
legitimately changes at the sync.

**Verification on the fixed sensor** (fresh seed-3 pair, final
tree): classifier **IDENTICAL, 0 within-row hits**, outcome fields
equal, decisions 653 both arms, gamelogs byte-identical
(sha 88231b961d202c19), normalized final-state hashes equal
(`data/final2-pair-table.md`, rows in `data/final2-pair-rows.jsonl`).

## §3 P-branch consequence — count and disposition

**64 of the 1,087 §3 contested decisions were branch P** (5.9%;
branch shares of positive gain had P at ~3%). Until this round
they stood suspect per your instruction. The localization bears on
them directly: capture snapshots are taken inside Decide from the
same live state, and at pitch decisions the snapshotted state is
the engine's view state — the same state, and the same
view-derived candidate list, that the bridge itself decides on at
that moment (the raw control above is that pairing). I read them
as cleared by the localization; they are yours to formally clear
or keep flagged in your reply.

## R8–R11

- **R8.** The classifier now returns a two-part report:
  `within_row_hits` (every hit: seq, side, branch, pair, rule) and
  the cross-arm verdict, scanned past within-row hits.
  `test_classify.py` **11/11**, including your pass fixture
  (within-row hit at seq 1 + DECISION at seq 3 reports both).
- **R9.** `steps` is dropped from driver rows. Rows now carry
  `decisions` — trace rows for the game, one per policy decision
  (the `simPolicyDecision` count): 653 on the seed-3 pair, both
  arms.
- **R10.** Diffed (final pair, kept files): the two `gamestate.txt`
  differ ONLY in two per-game hex-id lines (lines 60–61) and one
  epoch line (line 70, values 2s apart). The driver now also
  records `gamestate_norm_sha` (hex-id lines → `HEXID`, epoch
  lines → `EPOCH` before hashing); on the pair it is **equal**
  (2564ffc4f8575d6e), and it joins the R3 outcome fields the
  pairing table checks.
- **R11.** `r3_pair.py` carries each row's mode line and
  `connect_failed`, and a seed's verdict becomes `INVALID_MODE`
  unless raw reads `policy: server` and teacher-family arms read
  `policy: search`, with zero connect failures. Seed-3 table:
  modes ok = True.

## S1 for rollout children — done

`code/patch_child_sigkill.py`: all **11** `exit(0)` sites in
`search.php` (every one verified as a fork child following a
result-file write: RunChild, teacher children, ISMCTS children,
RunRollout, label children) now die by SIGKILL after writing, with
`exit(0)` only as fallback when posix is unavailable.

## Tree-build note (your run_r3.sh question)

`paired_driver.py` is deployed into `$TREE` as part of the tree
build, alongside `classify_divergence.py` and `r3_pair.py`; the
build is: fresh copy of the gate tree → `patch_trace_shadow.py` →
`patch_child_sigkill.py` → deploy the three scripts → `php -l`
both patched files (clean). `run_r3.sh` runs from `$TREE` against
those files.

## Tests run for this commit

- `test_classify.py`: 11/11.
- `bash -n run_r3.sh`: clean (unchanged this round).
- Localization probe (ghost + raw, seed 3): table above; dumps in
  `data/localize-seq38.jsonl`.
- Fixed-sensor seed-3 pair: IDENTICAL, 0 within-row hits (above).
- Both patched PHP files `php -l` clean on the final tree.

**Scope request:** approval is sought for this commit's sha, for
the launch in `code/run_r3.sh`, under the restated §3 reads only,
with Joe's go still to come after your reply.
