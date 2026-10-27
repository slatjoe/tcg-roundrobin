# Stage 2 data — MANIFEST

Every file published under `rounds/round9/data/stage2/` for
the round-9 Stage 2 run (launch record `e8c4b7fa`; launched
sha == approved sha `2d64302f`; pre-gate IDENTICAL; games
200/200; L3 labeling complete; the analyzer's first read
attempt ABORTED on the stamp audit, the fix was confirmed
at `7fc06c09`, and the read ran once under that ruling's §3
— see `stage2-report.md`). Hashes are sha256 over the file
bytes; sizes in bytes; "lines" counts non-empty lines.
Published files are byte-identical copies of the box
artifacts in `/home/joe/tcg/r9s2_out/` — each file's sha256
was computed on the box and re-verified on the transferred
copy (all 25 match). On the box, `search_stats_<blk>.jsonl`
was `games/games_<blk>_log/search_stats.jsonl`,
`teacher_snap_index_<blk>.jsonl` was
`games/games_<blk>_log/snaps/teacher_snap_index.jsonl`,
`pregate_manifest.json` was `pregate/pregate_manifest.json`,
and `stage2_launch_manifest.json` sat at the run root; the
rest sat under `games/` or `l3/` under the published name.

**Label rows:** `labels_all.jsonl` totals **107,974,003
bytes raw (~108 MB)** — too large for the git venue
uncompressed, so it is published here **gzip-compressed**
(2,825,890 bytes) as `labels_all.jsonl.gz`; the raw
identity is in the table at the end of this manifest
(verified on the box and again on the transferred copy:
the decompressed stream hashes to the raw sha256 below,
which is also the sha256 recorded in `pre_run_record.json`
before the read ran — the read did not touch the labels).
The raw file also remains at `/home/joe/tcg/r9s2_out/l3/`
on the sim box. No figure in `stage2-report.md` rests on an
unhashed file.

| file | bytes | lines | sha256 |
|---|---:|---:|---|
| games_manifest.json | 2535 | 73 | fb2b48c47b9b112f04b007187111bb3dd1e0c6dcd9c549792d298e1a8753219e |
| games_report.json | 1252 | 51 | 144a33d56850eda3db4d3e6f8aaf7e609cd443f03a203be498e33e75d3facb05 |
| games_report.txt | 504 | 4 | 5051cdcd9df47d05900ddabc1728f9b6e7cef1fe758ae7dfe975c6c19f5c6c5f |
| games_s1a.jsonl | 28873 | 50 | 3e71704c586c79a715c42fbbb0ea1948776e4b97c55306f3c09b93f671a896cc |
| games_s1b.jsonl | 28892 | 50 | f4933d2a8e8627c9b6f28931d573011e183deb9b06af19b3a8a110d014500521 |
| games_s2a.jsonl | 28881 | 50 | 6e44dfcecde47b108c0f148d67dae46a4ff829c3fd53e0771e0a16ed909f3a62 |
| games_s2b.jsonl | 28882 | 50 | 0df8780e1290c9d98fc172940df8e2f303f90268391ccb1dec19b670c911a973 |
| jobs_all.jsonl | 296681 | 353 | 96b62d0be7bccffbe2b1c4fa403364772f9220df84c044f0eb1f056e596dbb67 |
| jobs_report.json | 264 | 20 | 704494d5e009ddb47df7866426e4536e68c1f5f9a6f8b4633f5587cce072a920 |
| l3_manifest.json | 3689 | 113 | 2a5c1315345ed26273aca6519e056e6ebe0eb9088402b3c7d67f4f5aa40bc4b5 |
| labels_all.jsonl.gz | 2825890 | — | d5eb3914219e7d090cbda5e4342544dd8832ce51ec96c77005a9956e5fa7e201 |
| pre_run_record.json | 3989 | 101 | c4b37c23ab2c2e9dd3226c519aac6af62beb7f7e3c31f51b5ec77f53537ff80a |
| pregate_manifest.json | 2407 | 27 | ffb6b9d1c654ce621202bb47cd077d10cdc46c01b47642631f416b3106949e49 |
| search_stats_s1a.jsonl | 1971706 | 4965 | 9884755a4aa0980a8690632b75658ba3ab3e8ff8cca113fa6bd774d68c6d1c15 |
| search_stats_s1b.jsonl | 2101293 | 5180 | 32093164693f7002107f2d5b2f8548e041c5eb80e4e5cd15e283bebb31e1008a |
| search_stats_s2a.jsonl | 1929967 | 4844 | ff5a57c9da438d528fa9d9b22b0dc217c446076e5ce11685fb17c0a4da9ed420 |
| search_stats_s2b.jsonl | 2066122 | 5024 | 4b82ffa54aa1c430922e55067170615d41c628f11d615516de125e2813e10a88 |
| stage2_launch_manifest.json | 2265 | 1 | cf117f161d23af3e9c5516b256542e1e1dbeca81cd7fd3b6a94acab78c48694f |
| stage2_read.json | 1098 | 64 | 5dadbe493f7f6ab595e3a1180c12580545737b945113aba182e835f68f806264 |
| stage2_read.txt | 1130 | 11 | 205500e30475f2e57e130665ea86d5762bc9f55f3ae1eb42ace3fde74460b8c5 |
| stage2_read_aborted.txt | 76 | 1 | 712930a586ae85bc10460df18a936bdef418d64afac2be33f0f7b022f00d036f |
| teacher_snap_index_s1a.jsonl | 266923 | 82 | 4367b904361932e7cd51e737eb3426c34b7399eaf7e8f8d8afcf0f46accdb6df |
| teacher_snap_index_s1b.jsonl | 364230 | 111 | 7b1afd768329b024dada4b5d0108bec29b2372f14afde1ae7ad1da247cd6e5d7 |
| teacher_snap_index_s2a.jsonl | 233968 | 72 | 099bf2d060f0bccc9a568814831010a659760d53e46d246e8f78df4522234bc3 |
| teacher_snap_index_s2b.jsonl | 297583 | 88 | f04f664707930998cf35b5c9229156b4e3a0ba6c57db2d17fbdc4fc5786d15ef |

## Label rows — raw identity (also at `/home/joe/tcg/r9s2_out/l3/` on the box)

| file | bytes | lines | sha256 |
|---|---:|---:|---|
| labels_all.jsonl | 107974003 | 35300 | f5f1522cddbcf5d9c66d7390d47a5f69400846104d1a3fb37e4952a9c4e2fc90 |
