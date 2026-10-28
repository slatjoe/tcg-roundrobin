# Stage 3 data — MANIFEST

Every file published under `rounds/round9/data/stage3/` for
the round-9 Stage 3 run (launch record `ec5407da`;
approved sha `fdd68d64`, launched sha `3cb82748` —
rounds-only difference; games 800/800, 400/400 pairs
scored; L3 labeling complete, 62,200 label rows; see
`stage3-report.md`). Hashes are sha256 over the file
bytes; sizes in bytes; "lines" counts non-empty lines.
Published files are byte-identical copies of the box
artifacts in `/home/joe/tcg/r9s3_out/` — each file's
sha256 was computed on the box and re-verified on the
transferred copy (all 35 match). On the box,
`search_stats_<blk>.jsonl` was
`games/games_<blk>_log/search_stats.jsonl`,
`teacher_snap_index_<blk>.jsonl` was
`games/games_<blk>_log/snaps/teacher_snap_index.jsonl`,
`deployed_code_hashes_games.txt` was
`games/deployed_code_hashes.txt`,
`deployed_code_hashes_l3.txt` was
`l3/deployed_code_hashes.txt`, and
`stage3_launch_manifest.json` sat at the run root; the
rest sat under `games/` or `l3/` under the published
name.

**Label rows:** `labels_all.jsonl` totals **187,490,941
bytes raw (~187 MB)** — too large for the git venue
uncompressed, so it is published here **gzip-compressed**
(5,065,847 bytes) as `labels_all.jsonl.gz`; the raw
identity is in the table at the end of this manifest
(verified on the box and again on the transferred copy:
the decompressed stream hashes to the raw sha256 below,
which is also the sha256 recorded in `l3_manifest.json`
— the attribution read did not touch the labels). The
raw file also remains at `/home/joe/tcg/r9s3_out/l3/`
on the sim box. No figure in `stage3-report.md` rests
on an unhashed file.

| file | bytes | lines | sha256 | role |
|---|---:|---:|---|---|
| attr_read.json | 1374 | 75 | 6555c53f1f47a154658090ebb65e63ec96972772dbdfac404daaf23ea0c979cf | L3 attribution read, JSON form (box: `l3/attr_read.json`) |
| attr_read.txt | 1215 | 11 | 4016cfee353388d791a3360af627b84cff8b996e9ff2b3cccbf5fedebd763314 | L3 attribution read, text form (box: `l3/attr_read.txt`) |
| deployed_code_hashes_games.txt | 3874 | 36 | 138c3f3d9ff1ac929cec70cf017b2245ebc85a0b1826db1596014fae05bff098 | games runner's deployed-code pin record (box: `games/deployed_code_hashes.txt`) |
| deployed_code_hashes_l3.txt | 3774 | 35 | 9e62ae0a6df34636632967227f36ec65757b1c1079beaecb4c01e18f49a23dc7 | L3 runner's deployed-code pin record (box: `l3/deployed_code_hashes.txt`) |
| games_launch.log | 320 | 3 | 0e6bf695cb2275236efd523eaa178ef576bda4dca1308bd512746cf8fdc0bb36 | games attempt-1 log: PREGATE-GATE pass, then the free-space pre-flight ABORT |
| games_launch2.log | 1742 | 19 | 219234613e4ca736374c265d64c35ca6953ee4f519ea3bf556c66649714293a2 | games attempt-2 log, ending with the full paired-read text and the completion line |
| games_launch2_execfail.log | 67 | 1 | 558ddbdc415491efe6715d004f97543cba53844b889cc20bbe6fc9fbede34417 | the setsid Permission-denied record from attempt 2's first invocation (runner never started) |
| games_manifest.json | 6100 | 242 | dc6a361227c315a3a07326c1a474cc14e32abf53a30d2ffa77517c3ab2be3438 | games runner manifest: pairing summary, games report, the read, per-file row counts and sha256 map |
| games_r1a.jsonl | 53473 | 100 | f5b9486cca07d97c221f5483a636c92a6be2b85828f475f15376add208c62ba1 | raw-arm driver rows, block r1a (seeds 23001–23100, seat 1) |
| games_r1b.jsonl | 53469 | 100 | 9150853ed5c57a8d15b1869936fe50145c6062c9909149ef58892293323a86b9 | raw-arm driver rows, block r1b (seeds 23101–23200, seat 1) |
| games_r2a.jsonl | 53410 | 100 | e81a47165e20fbb25f165dd6bce0ce8277104aca3762466e3723c78f4d75aabd | raw-arm driver rows, block r2a (seeds 23001–23100, seat 2) |
| games_r2b.jsonl | 53459 | 100 | 54853d0877b70fdd029d142974473d0f473e75d088011287a6e4766241974398 | raw-arm driver rows, block r2b (seeds 23101–23200, seat 2) |
| games_report.json | 2239 | 117 | d56ffda5a1df8d773c6dd8ee98cb4906f3534b35b8008f2c14af169675cbd083 | games report, JSON form (pairing, outcomes, band rates, tuple audit) |
| games_report.txt | 724 | 7 | 4cece5314f33eecdbd967507680a86a45a1c2eb1e22b301007a80043c7fbf1cf | games report, text form |
| games_t1a.jsonl | 57746 | 100 | 19ccb4d7daf6168c4218085596383eaa1b662d55914fd7d60b652ac0add6685c | teacher-arm driver rows, block t1a (seeds 23001–23100, seat 1) |
| games_t1b.jsonl | 57752 | 100 | 965d6ddd895b612e4393383a3518e66245f28769284ecca3a2242d4286f57e2f | teacher-arm driver rows, block t1b (seeds 23101–23200, seat 1) |
| games_t2a.jsonl | 57714 | 100 | e520e6dd1ac0af898b31918e1d7f3122e42b8285b988de6fbe03f25745c30f59 | teacher-arm driver rows, block t2a (seeds 23001–23100, seat 2) |
| games_t2b.jsonl | 57731 | 100 | c45be2b36fbe35015530aa907021589736d290dcb4102923a2af96a9f3c7df42 | teacher-arm driver rows, block t2b (seeds 23101–23200, seat 2) |
| jobs_all.jsonl | 535742 | 622 | e4c03f682daa5fe46abd53ad0421ef4957ab7f254c3475c5ed6daafe2253f762 | L3 jobs: every captured teacher-arm overturn (622 over 299 games) |
| jobs_report.json | 267 | 20 | 4b3e09ee84a276ecc0aef39628e9bbcf2696d51c04c04093b2c4423cc92f6d9f | jobs builder report (shard split, label tuple) |
| l3_launch.log | 1826 | 26 | f54d3a93dac2fe3171e5780ee7f9b921f6d2fcf5fb6dbbb8c0639cf60d00e4b6 | L3 runner log, ending with the full attribution-read text and the completion line |
| l3_manifest.json | 3977 | 124 | f8d25e69eba5c146db7f78be835be0f4f083dd911999ad5deef4feed06ec1455 | L3 runner manifest: the attribution read, jobs summary, label-row count, sha256 map |
| labels_all.jsonl.gz | 5065847 | — | 2bff87d13535495ab38bd81424cc03979a42b235a56c00faa71c4348c4d1c6e0 | all L3 label rows, gzip-compressed (raw identity in the table below) |
| pairing.json | 651444 | 26417 | bbc71b8d099267b79bafebdfdfd9d72447a65f0f54c7dc8e2d6f0a58700e0ed4 | pairing builder output: all 400 pairs with both arms' driver rows and statuses |
| search_stats_t1a.jsonl | 3659111 | 9168 | b956debc1d5b87ad569d2e93a65a6b533b1d0c5ecc6f958327c64ab2cd13e38b | teacher stat log, block t1a (incl. any R14 canary-refusal records) |
| search_stats_t1b.jsonl | 3930442 | 9489 | d1ad23d8f892f0c41892cbf29acd8c1b7471c975185bb6c3c21aacf2f6de3df5 | teacher stat log, block t1b (incl. any R14 canary-refusal records) |
| search_stats_t2a.jsonl | 3668458 | 9298 | d3b02c9b0210f9337546f3aec1e223c6088fdfcf3d3c55d59323ac8f66a89dd1 | teacher stat log, block t2a (incl. any R14 canary-refusal records) |
| search_stats_t2b.jsonl | 3719369 | 9145 | d902f17a0922c410a0516c85aac7faffa1ed57bf0f1e8df1f734ac0d6390d8ee | teacher stat log, block t2b (incl. any R14 canary-refusal records) |
| stage3_launch_manifest.json | 5237 | 120 | cddb44c26e71749b56b89b45dff49bf7784d937655a0eabbf51098de168c15be | launch manifest as updated after attempt 2 (attempts record, cleanup, deployed hashes) |
| stage3_read.json | 1197 | 82 | 1c97f1dddfc876a665c26e1384d129350e8d65e6f93e0fe23e19da7eb5620c9d | the paired read, JSON form (primary, co-reports, reconciliation, verdict) |
| stage3_read.txt | 1331 | 12 | 0bb140ec7f64c4313350fe54a6521f84de6c35aca91bd4b854cda153e826e680 | the paired read, text form |
| teacher_snap_index_t1a.jsonl | 594924 | 181 | 027979b17418a536b7deb03582b5c1e6de70d879a3b49dbede3069c9fe65e19b | teacher snap index, block t1a (captured overturn states) |
| teacher_snap_index_t1b.jsonl | 544098 | 167 | 21dc63d675d4ed1ecb4397726b7e0533181d858ee30d028c296a5bf132900cfa | teacher snap index, block t1b |
| teacher_snap_index_t2a.jsonl | 492632 | 147 | 195a5d9198090d68a00b640e97a73b1580a66b61983baa5a88bcfc28034d35f1 | teacher snap index, block t2a |
| teacher_snap_index_t2b.jsonl | 421631 | 127 | e411f1449543a3c4af250ead7142bdf7795b4a61d8bb37d39ae5d7a0ad744400 | teacher snap index, block t2b |

## Label rows — raw identity (also at `/home/joe/tcg/r9s3_out/l3/` on the box)

| file | bytes | lines | sha256 |
|---|---:|---:|---|
| labels_all.jsonl | 187490941 | 62200 | 66e16f5115ae069c8808656e6d55a28b6fa5d9a32822d3b2d25ecacbdd3bd432 |
