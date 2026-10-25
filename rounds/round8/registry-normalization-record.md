# Round 8 — registry value-shape normalization record

**What happened.** The do-not-train registry's entries carry a
plain tag string as their value (e.g. `"gravy_formal_gate_eval"`,
`"gate:c1"`). The builder's records-step merge for the stopped
pilot's 20 equivalence games (records commit e73e682d,
2026-10-25) wrote those 20 entries with a JSON **object** as the
value instead. Membership was never wrong — the 20 game ids
were present and excluded throughout — but the shape broke the
file's one convention, and it surfaced in the resumed run's
merge log, where `merge_registry.py` counted only string-valued
entries ("registry before merge: n_games=6181" against a
6,201-game file). During the builder's audit of the resumed
pilot report, before that report was committed (8f834d2c), the
20 values were rewritten to the string form. **Membership is
unchanged: 6,241 games before and after; only the 20 values'
shape changed.**

**Actor / date:** the builder, 2026-10-25, in the pilot-report
audit (disclosed in the 8f834d2c commit message; this record is
the standalone document claude-reply-8f834d2 §4 asked for).

## The 20 entries

Ids (from `rounds/round8/pilot-registry-merge.json`):

161224788, 162551813, 247018415, 250250120, 309364530,
442300910, 463606934, 479713529, 546686378, 563634276,
629867931, 647113767, 827771651, 920353282, 926661380,
938816982, 942432760, 955381062, 961006579, 989576170

**Old value (all 20, identical)** — verified by reading the 20
ids in the pre-normalization vault copy named below:

```json
{"tag": "distill_equiv_eval", "source": "round8 pilot capture-equivalence check, seeds 12001-12010"}
```

(the vault file serializes the object with its keys sorted:
`{"source": "round8 pilot capture-equivalence check, seeds 12001-12010", "tag": "distill_equiv_eval"}` — same object).

**New value (all 20):** the string `"distill_equiv_eval"`.

## Before / after

- **Before:** registry sha256
  `a921be4954c6de0804ee23a7f67a6cbc124013c614e26db1254cbec2b4bda927`
  (6,241 games; the state after the resumed run's +40 merge,
  with the 20 dict-valued entries still in it).
  Backup: `/home/joe/tcg/registry-vault/do_not_train_registry_20261025T122226.json`
  — the merge run's own vault copy, written by
  `merge_registry.py` at 12:22:26 EDT; verified to hash to
  `a921be49…` and to hold the dict values above.
- **After:** registry sha256
  `28b5acfa679eed61d4633d925909d1d832942272649c67ca2e740bebe9ffb0b8`
  (6,241 games; all values strings).
  Backup: `/home/joe/tcg/registry-vault/do_not_train_registry_2026-10-25_post-resume-normalized.json`
  — verified to hash to `28b5acfa…`, identical to the live
  registry (`/tmp/harvest/do_not_train_registry.json`) at
  verification time, and the 20 ids' current values verified to
  be the string `"distill_equiv_eval"`.

Chain for context: `95a4580a…` (after the records-step merge,
vault `do_not_train_registry_2026-10-25_post-pilot.json`) →
`a921be49…` (resumed run's +40 merge) → `28b5acfa…` (this
normalization).

## Rule going forward

**One value shape: the tag string**, as every other entry in
the file has. Merges go through `merge_registry.py`, which
writes that shape; any hand merge must match it.
