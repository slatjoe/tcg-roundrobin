# Round 8 — W=100 V1 check: published data

The complete artifacts of the W=100 V1 check (relaunch under manifest
`rounds/round8/wcheck-launch.md`, repo 08ea4bb7; pin fix confirmed in
`rounds/round8/claude-reply-af89615.md`, repo 4d2444a4). The pilot's 547 V1
capture states were labeled twice at W=100 — **run A at world-seed base
555001, run B at world-seed base 777001** — sharded 137/137/137/136 across
the 4 native-tree labelers, player-1 jobs only (the player-2 shard files
were empty, as in the pilot: all pilot contested states are player-1
decisions). **The reads are in `rounds/round8/wcheck-report.md`** (headline:
V1-ov 29/66 = 0.439 [0.326, 0.559] — the registered threshold reads STOP).

All files were copied from the box directory `/tmp/distill_wcheck/`
(source path for every file below is `/tmp/distill_wcheck/<name>`).
`MANIFEST.sha256` in this directory hashes the files **as published**;
for the `.gz` files below, the "original sha256" is the hash of the
uncompressed box original, and each published `.gz` was verified to
decompress to exactly that hash. Raw files were gzipped with `gzip -n`
(deterministic: no stored name or timestamp).

## Files

| published file | what it is | original sha256 (box) |
|---|---|---|
| `jobs_w100.jsonl` | the 547 pilot V1 jobs stamped `"W": 100`, fed identically to both runs | `b8583d82f3f3c1d859e117efefc10b737c223c75d832fa5e4d1558bdc5562405` |
| `labels_w100_a.jsonl` | run A labels (545 labeled states; base 555001) | `d0e298ff46be2f4360658373378712046e7e9ed915473a19f9f5c545c870476e` |
| `labels_w100_b.jsonl` | run B labels (546 labeled states; base 777001) | `a6038f643eb8a763bb2665551457cd4fa9856bd7851ebb5ac300e8062f0c8ec0` |
| `thin_w100_a.jsonl` | run A thin/excluded rows (2) | `ebfe5713a91cd9c258da783c5901597bca8ad7016b7cb35c0d6cbb65fbe4db95` |
| `thin_w100_b.jsonl` | run B thin/excluded rows (1) | `cbbe7e3d5afc5e4cb3d4f3e3dce9f37beaa6b9a5df58cd72569416eeb68049f0` |
| `reduce_w100_a.json` | run A reduce summary (jobs/labels/thin/overturn/confirm counts) | `807606d37c06eb2bc987660b425d708b42c75f53a0c7e7e99f490a7ba6a5f58f` |
| `reduce_w100_b.json` | run B reduce summary | `2d5fa9a9e1d002af4a4b483839e22aeb455907f601448bd427b2797c981df1a6` |
| `wcheck_report.txt` | the check's own report (V1-ov, V1-conf, thin, cost, threshold line) | `bdf91e5f44a3e7f3e8b01d676b24fe6a979d27657fee1db290fb421365f5b558` |
| `wcheck_report.json` | the same reads in structured form | `79ced9ffc4b51b676a27f38b00388abae1104900fa9aa5d37fb0d6c35d82c05e` |
| `raw_a_shard0_p1.jsonl.gz` | run A raw per-world rows, shard 0 (115,807,135 B uncompressed) | `acbde49b9e28479e693db0bf9499b3970e3b3b4be8a484a99797e702d5571c16` |
| `raw_a_shard1_p1.jsonl.gz` | run A raw rows, shard 1 (115,060,252 B) | `06bc80ee79ccf9f9c9c0f487b980ee51841c089bb7db69637ff6e00f8d4ff406` |
| `raw_a_shard2_p1.jsonl.gz` | run A raw rows, shard 2 (114,143,927 B) | `9168b5ea423f1b0094f7e5065a2841b58fb35fed108f21ba59d3b91f7b93dbe8` |
| `raw_a_shard3_p1.jsonl.gz` | run A raw rows, shard 3 (115,431,704 B) | `178cc817e5399083991ee70f4bdd236050463c5e98e7be82278c015c142111b0` |
| `raw_b_shard0_p1.jsonl.gz` | run B raw rows, shard 0 (115,825,656 B) | `5698f9d31607226af7864f5b46f490492500484c0cfb0778714252fdec461b4a` |
| `raw_b_shard1_p1.jsonl.gz` | run B raw rows, shard 1 (115,773,479 B) | `6b4e33b1921fb53d541f5c52e721f8903397bb5b735e547527cea23e5aac9cf2` |
| `raw_b_shard2_p1.jsonl.gz` | run B raw rows, shard 2 (114,852,778 B) | `e403b2c8bcdbad9a7133e90f01f6c857de8d0184af24f9346ef0b2ad6259b50e` |
| `raw_b_shard3_p1.jsonl.gz` | run B raw rows, shard 3 (114,580,498 B) | `ecf49b4af549c8536033b61ce2264009ab2a0e63c98dfd3e40a944f778d4297d` |
| `raw_a_all.jsonl.gz` | run A raw rows, all shards concatenated (460,443,018 B) — same rows as the four A shards | `55deb993783ce65e2dcc0f01ebe4e0bcaf25c19c4521707ce7eb4e89569328d5` |
| `raw_b_all.jsonl.gz` | run B raw rows, all shards concatenated (461,032,411 B) — same rows as the four B shards | `2ec6ead74a27bb9eaeeaec32244051da6ff43ddd0629c3ff7889553b09799938` |

Every `.gz` is small (shards ≈ 2.5 MB, the two `_all` files ≈ 10.2 MB
each), so the per-shard set and the concatenated `_all` files are both
published; neither is a partial publication. Per-world outcomes in the raw
rows are what any margin recalibration recomputes from — no new labels are
needed for that.
