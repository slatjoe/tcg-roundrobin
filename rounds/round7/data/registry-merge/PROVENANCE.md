# Registry merge — the 319 recovered loose eval-only game ids

**Authority:** `rounds/round7/claude-reply-ac725a5.md` §4 item 1 (merge all 319 ids into the
do-not-train registry, eval-only, tagged by group; commit the id lists to the repo as the
durable record; record the one unrecoverable game in the registry's provenance), executed on
Joe's go in chat, 2026-10-22 05:27 EDT. This is bookkeeping, not a measurement.

**What these are.** Four groups of eval-only games that were played and owed to the
do-not-train registry but never merged into it (the standing loose end, restated in
`rounds/round7/calibration-steps12.md` §4). The merge registers the 319 recoverable ids.
None of the four groups' records lived in the 72 `/tmp/eval_v*_*` dirs deleted during the
round-7 stage-1 run; all four workdir sets survived on the box.

## The lists

| file | group | registry tag | source records |
|---|---|---|---|
| `tgate-199.txt` | Oct 18-era gate games (tgate), 200 planned | `tgate_eval` | `/tmp/tgate_c{0..3}{a,b}/traj/games_meta.jsonl` on the box (8 files, 199 rows, 199 unique) |
| `section3-40.txt` | §3 measurement games | `section3_eval` | `/tmp/meas_c{0,1}{a,b}/traj/games_meta.jsonl` on the box (4 files, 40 rows, 40 unique) |
| `census-40.txt` | round-5 (b) census games | `census_eval` | box result rows `/tmp/census/census_s{1,2}.jsonl` (26,969 decision rows, 40 unique game ids), cross-checked against the committed copies in `rounds/round5/data/census/census_s{1,2}.jsonl` — **the two sources' id sets are identical** |
| `pickflip-40.txt` | round-6 pick-flip games | `pickflip_eval` | box result rows `/tmp/pickflip/flip_s{1,2}.jsonl` (267 rows, 40 unique game ids), cross-checked against the committed copies in `rounds/round6/data/pickflip/flip_s{1,2}.jsonl` — **the two sources' id sets are identical** |

Cross-group overlaps: **none** (all six pairwise intersections empty; the union is exactly
319). Ids are one per line, sorted numerically.

## The one unrecoverable game

The tgate group is **199 registered of 200 played**. One planned game in chunk **c0b**
(25 planned, 24 ids) recorded **no game id in any surviving record** — searched across the
chunk's `games_meta.jsonl`, `traj.jsonl`, and `teacher_snaps/` (snap ids are a strict subset
of the meta ids in every chunk); the chunk summaries carry counts only, not ids. That game's
id is **unrecoverable** and is therefore not in the registry. The loose end is closed as
*319 of 320 registered; 1 unrecoverable*, not as fully open.

## Merge record

- Live registry before merge: `/tmp/harvest/do_not_train_registry.json`, 3,476 games,
  sha256 `706fa3e969cd9325ce3e0c6fd585c6bac37cc29b6ba6bb2afa1e67469e9b0f0d`
  (verified immediately before the merge).
- Pre-merge backup (persistent, on the box):
  `/home/joe/tcg/registry-vault/do_not_train_registry.bak-20261022-052925-premerge319.json`
  (sha256 equals the pre-merge live hash above).
- Collisions of the 319 against the existing 3,476: **zero** — every id was new.
- Merged registry: **3,795 games** (3,476 + 319; `n_games` field agrees), sha256
  `ae7b04b9d4f5b554f52fc443e445fa74d48ce15116516d824f15107d340addce`. Per-tag counts in
  the merged file verified after the write: `tgate_eval` 199, `section3_eval` 40,
  `census_eval` 40, `pickflip_eval` 40.
- Persistent copies of the merged registry:
  `/home/joe/tcg/registry-vault/do_not_train_registry-20261022-merged.json`
  (sha256 as above). The four id lists and this PROVENANCE were also copied to
  `/home/joe/tcg/registry-vault/registry-merge-319/`; their vault sha256s match the
  committed files.
- New entries follow the registry's existing format: `games` maps each id (string) to a
  single tag string, as with `o_fleet_eval` and `gravy_anchor_gate_eval`.
