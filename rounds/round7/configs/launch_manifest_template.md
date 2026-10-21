# Round-7 launch manifest (template — one per stage, filled at launch)

```
stage:            <0 vocab | 1 corpora | 2 anchor | 3 ppo | 4 tree |
                   5 fleet>
approved sha:     <sha of the commit at which Claude approved this
                   build package>
launched HEAD:    <repo HEAD at launch; diff vs approved sha must be
                   rounds-only>
joe's go:         <chat timestamp + his words>
launched at:      <timestamp EDT>
operator:         Muse (builder, for Joe Slattery)

artifact hashes (sha256, verified at launch):
  vocab in:       3592bf44196bf4d0... (bc2_out/card_vocab.json, 379)
  vocab out:      <extended, 380>  stage: 0
  gravy deck:     b8b41390c5420ab8... (decks/nats2026_eriksen_gravy_60.txt)
  fai deck:       7397684b9d07debe... (control)
  trainer base:   8fd52d829acee231... (rl/trainer_v4.py, pristine)
  trainer launch: dc95d81a7f59139a... (rl/trainer_v4_gravy.py)  stage: 3
  tree search.php:      6cd6f9802bde... (gate lineage)          stage: 4/5
  tree featurize.php:   f81193e0b8a2...                         stage: 4/5
  tree server:          ab85fa1bcf19... (patched search_server.py)
  production server:    81ef2cdb... (before == after, fleets)

stage-specific:
  stage 2 anchor gate read: <wins/games = estimate [Wilson CI]>
  stage 2 stop check:       read >= 0.40 -> CLEARED (else STOP)
  stage 3 selected checkpoint (C4): <ckpt_vN, formal read, gates used>
  stage 5 timeout (probe):  <slowest probe game, GATE_TIMEOUT>
  stage 5 ipcs before/after: <counts; G8 sweep record>
```

## Flag 1 amendment record (entered once, at the stage-1 launch manifest)

> **Amendment to the round-6 closure (claude-reply-3e2f6f1 §2), per
> claude-reply-3c46619 §1:** the (b) featurizer correction (deck
> counts taken from the view) was deferred there to "the next
> training run's registration." This run IS a training run. By
> Flag 1 as ratified by Claude (claude-reply-3c46619 §1) and by Joe
> (2026-10-21, chat), the correction is **re-timed**: the Gravy
> pipeline trains on the **current** featurizer (store deck counts),
> and the correction debuts in the **distillation run's**
> registration, on the Fai lineage where (b) was measured. This
> record is the amendment; the re-timing is not a silent change.
