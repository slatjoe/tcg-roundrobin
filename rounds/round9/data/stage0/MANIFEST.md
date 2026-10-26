# Stage 0 data — MANIFEST

Every file published under rounds/round9/data/stage0/ for the
round-9 Stage 0 run (launch commit 5646e695), per the sec.4
publication registration in stage0-launch.md. Hashes are
sha256 over the file bytes; sizes in bytes. The label and
report files are byte-identical copies of the box artifacts
in /home/joe/tcg/r9s0_out/ (their sha256 values also appear
in stage0_manifest.json, the runner's own run record).
tie_as_loss_*.json are the builder's offline sec.3 co-read
outputs (code/tie_as_loss.py), computed from the label
rows published here.

| file | bytes | sha256 |
|---|---:|---|
| jobs_all.jsonl | 80706 | 117792c57e41a427cd3f66c1d74fa982e66f0ec3130c1569d2b66a610d8a3124 |
| jobs_all_h.jsonl | 82476 | cf8b6bc75655efee146e5594af63a895ca747b03835a6013216f475fe87ebbdf |
| labels_horizon.jsonl | 34734677 | 79276a209d89b7b5a879e31264361409ab1f276b6e8a9a94a45dbda7bc073b20 |
| labels_primary.jsonl | 30489613 | efe1e7b3c14df977a9d69dc848e292a80bcd9f0e246796828e76a32daf551f6f |
| report_horizon.json | 1673 | aa0e1f6b95451d918db450aff2a9a8818698839cd351e8a0d15a5f462451b2c6 |
| report_horizon.txt | 1435 | 55fede53701ca122415175b6047ad1f1be5db4e86827d5928ed19729f4573ea3 |
| report_primary.json | 1675 | 6a8048d1b46104cecdc6b8eda4781097366479cf89d87665770e5a9b272f5566 |
| report_primary.txt | 1443 | 5ad69ed1051519f2b8ead2b19ee5c4157a65e80816ac336d33cf7fbc862ae93b |
| stage0_manifest.json | 8258 | a5b883c157fa83a11d82093e90915608aa3781995e0aecff386b51b124736653 |
| tie_as_loss_horizon.json | 1768 | 21d60d88e1d5bbe6eecf5c0ef13b56b44d43d2aea35d8c13ac0709b46845ae53 |
| tie_as_loss_primary.json | 1744 | 1f4bbed9f65291de0c64128d8cce9d1db223543718a9994a13fc17068196dd52 |
