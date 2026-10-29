# data/step0 — MANIFEST (attempt 3, pre-recovery artifacts)

Attempt 3 of the Step 0 probe (launched 2026-10-28 12:32:09 EDT at launched sha
358a5a22; box OUT `/home/joe/tcg/r10probe_out`). Every file below was fetched
from the box and verified byte-identical against the box copy by sha256
(2026-10-29). Row counts are line counts for `.jsonl` files; for the two `.gz`
files the count is the decompressed row count and both the published `.gz`
sha256 and the decompressed (raw) sha256 are given.

## Capture

| file | rows | sha256 |
|---|---|---|
| cap_s1_b1.jsonl | 45 | `2c12839fb671338aa35287281259f5bdd46c40982e27f0d8a4331de156349c5e` |
| cap_s2_b1.jsonl | 45 | `e3cbbdc6064e00f9ede7f60aa1dd313e56515ef58fb8baf72c93fa8816ae3d96` |
| teacher_snap_index_s1.jsonl | 2,565 | `eb9791e8aa4d150b77a83870923ce2be993a09d3ebc9c70c9dfc012d6a0b9528` |
| teacher_snap_index_s2.jsonl | 2,688 | `7022650c614bac17aa6bc64900b492e9fd6588aacd580a076349cdd7667e4bca` |

## Eval

| file | rows | sha256 |
|---|---|---|
| eval_jobs.jsonl | 5,253 | `350f071d52a24fc11259e904b4d871b9dcc65dc569cb3310a80dae4544706d6a` |
| evals_all.jsonl.gz | 381,625 (decompressed) | gz `394bec5d663d28944b1703a2f55363bdc71b6ea4e540cc04c3ad1e3ce3a5265c`; raw `14cfdd35b4657e50a8f872ee6b631e7fa18f78e2d889e7044a247bee838d2650` (raw 1,171,452,622 B; gz 27,333,659 B) |
| eval_states.jsonl | 5,253 | `32cd82c873a501c1a9be3ac7b9e7f65826d7e6dc8ca9efa4d12419357faf6c60` |
| eval_summary.json | JSON document | `c9bf642114fe99b6a4ae556bce393940dfb85501ac1c2abfbd54b95804ed1f9d` |

## Label jobs (as the labeler consumed them)

| file | rows | sha256 |
|---|---|---|
| jobs_all.jsonl | 646 | `ab3297e80a64959800eb493e6088f46a66fd86ea2b8bc4f7b83a20d1efb44d4b` |
| jobs_report.json | JSON document | `53f135bb63185e51440f52adedb60308c18b6d1c0b0a7e6f0a9672cd359d2586` |
| jobs_shard0_p1.jsonl | 80 | `ddbde3a871eb4f2e84ea6688135ab2c79fcbe878c4e7d915f2cedecbaab39dcb` |
| jobs_shard0_p2.jsonl | 115 | `608169fc829238624abb03441cad7ce5adef492261f579aac679ce8ba05d276e` |
| jobs_shard1_p1.jsonl | 103 | `0fbffe65ec8de14de8044280f2d3d970e493db255dfb15e2e1fdcc48e9043f90` |
| jobs_shard1_p2.jsonl | 56 | `b7ea352fa82cd78b6d6bb21a1a2a74baaf49f5ead32a86ce21dc78cdac49c5f8` |
| jobs_shard2_p1.jsonl | 115 | `38af10e1f2fb448746bb34469d00240354ebbf884f212cb149e08546db221cfb` |
| jobs_shard2_p2.jsonl | 75 | `972f795b60abd8b987832d92dd9c8afd5b66c53bb6811421e07def16b21b4843` |
| jobs_shard3_p1.jsonl | 20 | `6c3fe4bb58bf40a830c72b6d388827771c097792e417a10d197d7d9493364687` |
| jobs_shard3_p2.jsonl | 82 | `7f0fb70ceba98e709597b31ce8d790a0ed22c8750dbae5511485926f9cf61dbf` |

Shard row counts sum to 646 = `jobs_all.jsonl`. `jobs_shard0_p2.jsonl` (115
lines) is the shard the attempt-3 labeler loaded as 105 jobs — the 10 dropped
`Infinity` lines are snaps `540261752_t64`–`t73` (jobs_all lines 282–291).

## Labels

| file | rows | sha256 |
|---|---|---|
| labels_all.jsonl.gz | 63,600 (decompressed) | gz `222d148ca9bf29d25710d9cf7f8377f0b9d8e5e0fb58966e7e80116d9ad3f87d`; raw `d4523e530c624fc42d04acf4ed8447a5db3647e1ac7939098170644b3df241d1` (raw 195,670,422 B) |
| label_read.txt | 1 (the analyzer's abort record) | `89c152c377e5e02656ce3dd3eae6d9e80e27bcd0c073fd8fefb2a5549194d6d1` |
| label_shard0_p1.err | 84 lines | `21408129cdd1ae30515e7035920bfb08c1c3719e686f3c3efbe532bc01d8b6bc` |
| label_shard0_p2.err | 109 lines | `c7e456131f589ad8fb0a0a456ef4835e607db82352bda4557bc4ee531f97fc64` |
| label_shard1_p1.err | 107 lines | `b772d604d92fc11f59ce20a36eded6d3088e93102dbc91e15de276c7cee0a06d` |
| label_shard1_p2.err | 60 lines | `bfea582349ce2b4dcd3ba7191e3ab29f40b80abefe63b1d29d1492b256c5af72` |
| label_shard2_p1.err | 119 lines | `b18235975b7c6d511b33c4bbd6f28d45f924077fffa75e922425a4f8078307ba` |
| label_shard2_p2.err | 79 lines | `fe04758936b23940636622a07bc36530446e095839c43ac086452b74be57d35a` |
| label_shard3_p1.err | 24 lines | `1d88a14f92f27f807d104e87e972f99ce9f364313e97fc670e00fb9b4d9d6d01` |
| label_shard3_p2.err | 86 lines | `8952f9a602a52acc75585712403ba7325650aad45200cbe342e7f49f13aba90e` |

`label_shard0_p2.err` line 3 (`s2 label jobs=105`) is the fingerprint of the
silent drop: 115 lines in the shard file, 105 loaded.

## Run records

| file | rows | sha256 |
|---|---|---|
| probe_launch_manifest.json | JSON document | `445ec3f607d5f2fe27e95f2f01df5c9ba91573c07fe83df38e531d73e0df683b` |
| registry_merge_b1.txt | 4 lines | `ad43d0ae352b336625651bc8075a43c160444acbc27807703e1c34030365f555` |

Not published: the snapshot state directories (only the two index files
above), per-shard eval/label row files (the merged `*_all` files are the
publication form), server logs, and containment/sweep logs.
