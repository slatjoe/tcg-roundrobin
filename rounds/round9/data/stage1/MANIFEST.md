# Stage 1 data — MANIFEST

Every file published under `rounds/round9/data/stage1/` for
the round-9 Stage 1 run (launch attempt at `86de3be1`,
aborted entering eval; one-token fix confirmed at
`a13cabc5`; relaunch `PHASE=eval` 2026-10-26 07:49:24 EDT;
`PHASE=analyze` run after eval completion — see
`stage1-relaunch.md` and `stage1-report.md`). Hashes are
sha256 over the file bytes; sizes in bytes. Published files
are byte-identical copies of the box artifacts in
`/home/joe/tcg/r9s1_out/` — each file's sha256 was computed
on the box and re-verified on the transferred copy; the
runner's own `stage1_manifest.json` (published here) carries
the same hashes for the panel/evals/stats/jobs/report files.

**World rows:** the six per-setting world-row files total
**273,689,565 bytes raw (~274 MB)** — too large for the git
venue uncompressed, so they are published here
**gzip-compressed** (~8.2 MB total) as `evals_<setting>.jsonl.gz`
in the table below; each `.gz` decompresses to exactly the
raw file whose bytes + sha256 are listed in the "World rows"
table at the end of this manifest (verified by the builder
on the transferred copies, 2026-10-26: every `.gz` hash
matches the box-computed hash, and every decompressed stream
hashes to the raw sha256 below). The raw files also remain
at `/home/joe/tcg/r9s1_out/` on the sim box. No figure in
`stage1-report.md` rests on an unhashed file: every number
derived from these rows was recomputed from them by the
independent audit (`audit_stage1.py`, published here;
output `audit_stage1.json`) with full agreement against
the analyzer.

| file | bytes | sha256 |
|---|---:|---|
| audit_stage1.json | 9184 | 34c7e6b0d235f62257181a617a485eec55fff05776f4076a36504b8ec083bb61 |
| audit_stage1.py | 7880 | ae50205fb78191d5b5721e14e1a212e1e28bb05a35e6b15e2f9f8a4902654fcc |
| b0_gate_report.json | 67126 | b41d6d578f445ce4395fbe4c7510936e09cebc644c045d3c0c194ab70c2a6750 |
| b0_gate_report.txt | 941 | 1c7dfa783bd9d54be288ed58afaa6ac619195a1532af676ec5ab74ae24320314 |
| b0_gate_settings.json | 1127 | 492c0fb3b24880bf90bffef78230befc1275e4eeb2c5427f77ff608aaf693512 |
| deployed_code_hashes.txt | 2064 | d57d8165fa0b4252d3c95fab09af3a6139bdd4d02a5cc983518b46dbaa3b74cf |
| evals_B0.jsonl.gz | 1147045 | a423e78b94cde5110ff69865900099d64607ad10ea9b758ad45d08aa96415a56 |
| evals_B0+H.jsonl.gz | 1411338 | 04471cf26db5467bc07d05807886ead6b3197575f7d26cca3a3004bdbf62bccc |
| evals_H8k-180+H.jsonl.gz | 1412124 | 744364780286296fd29b40d8b23b42e9591e684b766e7267119ec634ebad56ad |
| evals_H8k-360+H.jsonl.gz | 1411969 | a4608947aaf079970b8c9069e3a8d2167e7e2805578e3d5f604811e854c4ca90 |
| evals_H16k-180+H.jsonl.gz | 1412318 | 606895721bfd605cf0c7dfa5f22bb1bdec9c921815f2cd4531bf9d7497b98711 |
| evals_H16k-360+H.jsonl.gz | 1413141 | 753c011eb4bd62f55d6248aefce92566a04b364569020030dafdc91e149477e6 |
| jobs_B0.jsonl | 179819 | 1a24d08b675bf4c148f60f07a8d54908b80056a612fa1cf3a0ef4d2e5b3fe5c4 |
| jobs_B0+H.jsonl | 180779 | 8055e9900742260d9d865429c529ba82a03a012e2fd1100047eb892586835a80 |
| jobs_H8k-180+H.jsonl | 181979 | f4dab00b35abc036afaaf8ffb9e9218443a50cc37167ce20244ad5c3d0d615a9 |
| jobs_H8k-360+H.jsonl | 181979 | ab98795c5a6215f0723900c4bc9220816d6cdcf6cec639f571d01f680b3e6074 |
| jobs_H16k-180+H.jsonl | 182459 | 8b1dadeae3921e9ceedb0149e00cae68a31cb75b1fe8fdda545d4a89ba23c750 |
| jobs_H16k-360+H.jsonl | 182459 | ad9ed7135d7a7139e2ec44a594b6143e2d1b6a1689379428b789ad1c961ebd88 |
| panel_jobs.jsonl | 154859 | 64fac6ce6560322de6184142e4efe87fd4fd7e128da6f5bb11e481f7f40de7ad |
| panel_report.json | 832 | 30853aa2862165252ea3ec6fda2e178d40c32ac8f9d477603b69e0a2fd7dd024 |
| registry_merge_b1.txt | 325 | a30f55322c44d7397cbf0d1e70691644cf49e8247eeddc3a19ad32a66063a945 |
| stage1_analyze_run.log | 1858 | 00ec96a6d23cc83793c1b3977b34ff5de919a3a8f5501ecccf80da0523692a10 |
| stage1_launch.log | 2158 | a89954b8a105886930fb35bc774ff65cbdb8535e4cd538a469452a6a438a5cd9 |
| stage1_launch_manifest.json | 5544 | 5265d8fb913f0c11b3ec02746142f4ac55f8ce1fd07c8c5250ad55facb682dd8 |
| stage1_manifest.json | 555277 | 10439885bdcf60ba0a4c950a8a13326beae2fbb91269531ca5a42db6d3a2e13c |
| stage1_relaunch.log | 3355 | 231dbacaf6b766e21a29198b6e497493308d1575651f59a1b9709b009767244a |
| stage1_relaunch_manifest.json | 7388 | f462a24816a0aa257e89e30a0a83a88f51219633418686d249f2313b00cb45c6 |
| stage1_report.json | 507491 | 3a750c5b606ad303fea11cc6c701a20f7b0edbae5e26c3c74ed5f474b73f5b39 |
| stage1_report.txt | 1585 | 2f5e8cedfc61cab3106e80f77e701ef43051ffdc79959b4272a86f094779619d |
| stats_B0.jsonl | 75685 | 5d90642288a0bf29956d9352e2f73bd8c47b39549b69811fd1ddd87ce33871fb |
| stats_B0+H.jsonl | 74335 | a65c6a20dc6b8ec5fecdc9c93368209663313d1c6002620aebbbc283cbcd9cd2 |
| stats_H8k-180+H.jsonl | 75535 | 85ef1bf73b2204e3973f64a55fd7b57b3787caaa1bcba0034270996d196d1c4d |
| stats_H8k-360+H.jsonl | 75535 | 1422d4e8f38659e592196a1fa860b93932235cf4237de30aadb383da85005ad4 |
| stats_H16k-180+H.jsonl | 76015 | af15605cc31f56d7be318c655da99a693c7fb01bf8839419b39129355fcba09b |
| stats_H16k-360+H.jsonl | 76015 | 4ef11be563aec89f07459cf9b407a6591bae2bcf5d06a3539a4e85c697d67216 |

## World rows — raw identity (also at `/home/joe/tcg/r9s1_out/` on the box)

| file | bytes | sha256 |
|---|---:|---|
| evals_B0.jsonl | 37874065 | c0be1d299a5e2ab6c8359c06a3a739964fad409a9962337dad3e8bce5d043063 |
| evals_B0+H.jsonl | 47081380 | 50fcf6176430f6db6531c532d6d965a94713fd7ad7584c17d1c6e78c5d358138 |
| evals_H8k-180+H.jsonl | 47166505 | 41c038e6a6c2ffe428c3c2e6675c9ffbcd005ee8a7819d76004a69de2e61366f |
| evals_H8k-360+H.jsonl | 47166505 | 48c28c3f3ee29d782e340e8452e75e3f3f1bf9a53c2b1b90c1f5bf970eea6bd7 |
| evals_H16k-180+H.jsonl | 47200555 | bfa49bf8e903e7637b2cdf2bac515367911653c0cb69b04f9bf21a1ce4fdb77b |
| evals_H16k-360+H.jsonl | 47200555 | e3d058a1262d733dd2852d2c469a6261e15ccae083c9d6ae36171515e4f9f794 |
