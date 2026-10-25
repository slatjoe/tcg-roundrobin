# Round 7 — records commit: stop (a), the fleet's data files, and the planning lesson

**Parent:** fa4d7412 (`claude-reply-9fb0e98.md`, the transfer ruling). This commit supplies the records items the ruling's §5 requires to close round 7. Joe confirmed publication of the data files on 2026-10-25 (the repo is public; the files carry seeds, game ids, and outcomes, nothing else).

## 1. Stop (a) — overturn rows failing their own margin: NOT FIRED

Stated as the ruling requires, computed by the builder from the fleet's eight teacher `search_stats.jsonl` files (37,133 stat rows, the same files published in §2 below):

- Overturn rows (the `overturn` flag set; cross-checked `pick != prior_pick`, same population as the fleet report's §6): **118**.
- Overturn rows with `mean_diff ≤ 1.5 × se_diff`: **0**. Every overturn cleared its own registered margin (paired margin > 1.5 × paired SE).
- The two rows with `se_diff = 0` (fleet report §7.1) carry `mean_diff` values of **2** and **2** — both > 0, so each passes: an exactly-zero paired SE with a positive mean means every paired world favored the overturn, a decisive position, benign at 2 of 118, exactly as the ruling reasoned.

Stop (a) does not fire. The L1 read of no leak signature stands.

## 2. Data files published for independent recomputation

Committed under `rounds/round7/data/`. Hashes are sha256 of the file content as committed, except the stat files, where the hash is of the **uncompressed** content (the committed file is that content gzipped); every hash below matches the fleet report's §11 or the pre-gate report, as the ruling specified.

**Fleet row files** (`data/rows/`, 16 files, 800 game rows):

| file | sha256 |
|---|---|
| `gate_c1_teacher_s1.jsonl` | `12cac321c0beaf4c28885ff5a8364e526ebb720a59cdae8c5c69e91c796a4750` |
| `gate_c1_teacher_s2.jsonl` | `a23772af39f98d014c2afbd0663b938c07fd38096aba2f1c56391dbe3aa7b176` |
| `gate_c1_raw_s1.jsonl` | `04531a69b81da80439b3b1d366eab7adf44a8f5a8e7bf0ffc4ae6dbe4b6563b3` |
| `gate_c1_raw_s2.jsonl` | `78c215c3a23dc96bdb7da01638ec66fa675966e16fb13acadcbf8173e90c634d` |
| `gate_c2_teacher_s1.jsonl` | `605224c546941e60f5dfb085f9cd6830d75810e16b77788aeb127ed25e5eb9b4` |
| `gate_c2_teacher_s2.jsonl` | `de1ccc9e35a36acaf7b9d3d67ac30ed9cd100ecd3e77cf63493987756b83bf01` |
| `gate_c2_raw_s1.jsonl` | `e755b23bab82205784f3a928b11f6b77a5cb11e895c26505f05ef03fc9c75eeb` |
| `gate_c2_raw_s2.jsonl` | `ea545d62f6bf4c6ed24124807495250cf2939934b7901fe6e6fe56a592612ce7` |
| `gate_c3_teacher_s1.jsonl` | `49252c7b84a5b0e7c81ff9aa552c6f8e85241681d376d82cfdfd51176d2f9b0f` |
| `gate_c3_teacher_s2.jsonl` | `9cc99687a28e89b3acc48009b45d471869142b363cf33ca7561872c3d87b633b` |
| `gate_c3_raw_s1.jsonl` | `12c06bf017efd578831dfb4f9d3dde7eb534916b3a333d2b74c5d58bbcd4e73d` |
| `gate_c3_raw_s2.jsonl` | `04f1302c6e5696875bc3dbca9dfdc55a2ad8faf5c2344e486969ecb0f0303884` |
| `gate_c4_teacher_s1.jsonl` | `1563a9f0b1585483afb4bbf3792c9bc88d3e66afca7ab378b99dc5c78b14ed5e` |
| `gate_c4_teacher_s2.jsonl` | `e2232a5f936cc47557537078a6a3284d2c55f8b8004b25ce46e8a4435d5ba8fa` |
| `gate_c4_raw_s1.jsonl` | `3a97b84b0bb2e6cf1589b98eabed58829e2314a8b48d45fb75ab0069a0a52e3b` |
| `gate_c4_raw_s2.jsonl` | `725629dc909db06f6edb28a9bfc4075b264ed690327e03d110f95293a4b4c26d` |

**Fleet teacher stat files** (`data/stats/`, 8 files, gzipped; hash of uncompressed content):

| file (as committed) | sha256 (uncompressed) |
|---|---|
| `gate_c1_teacher_s1_log_search_stats.jsonl.gz` | `01941349eca03770faf2efae2ad3d7ea94eb27e0712ed5a316921083b673abfa` |
| `gate_c1_teacher_s2_log_search_stats.jsonl.gz` | `16c918162a7b3148534a4fc1a019cf1957c1b18fd3cc5044456f910e0c341411` |
| `gate_c2_teacher_s1_log_search_stats.jsonl.gz` | `31fd9455164bac925adc95c5d43bf54796e095996feae83f81841948ce4351ba` |
| `gate_c2_teacher_s2_log_search_stats.jsonl.gz` | `35e67c52ee1b59eebbac99eb2c98c12bf6b8041723f51472278061ba03ade87f` |
| `gate_c3_teacher_s1_log_search_stats.jsonl.gz` | `a13177c688d6ffe01c1e45e23e57183405280ef3634b8ee9cdbd5fc0e7da5566` |
| `gate_c3_teacher_s2_log_search_stats.jsonl.gz` | `98253b37cfb7c26f38d06ae4151ad931e87b580d931d8b99d392f92ec9d8ffda` |
| `gate_c4_teacher_s1_log_search_stats.jsonl.gz` | `54214c82662ca8a72ced0bf195d0b7acc31a7f2a6f8e6d00f4612927428fd87d` |
| `gate_c4_teacher_s2_log_search_stats.jsonl.gz` | `89d3988f94e0d614f3f004b2726de4a4e5712fa91fde7c9ca23c1d979e4a63a4` |

**Pre-gate ghost stat files** (`data/pregate/`; hashes match the pre-gate report's record):

| file | sha256 |
|---|---|
| `pregate_ghost_s1_search_stats.jsonl` | `57f06d103afee4213c42b0b323716420e243e3d115b450f319d020d7cac59167` |
| `pregate_ghost_s2_search_stats.jsonl` | `053c7e8de4b6f1cdd4d28aa9b7081db393a436b9d3a249b9b227e3460d7c67db` |

From these files the primary Δ, the teacher-timeout rate, the overturn and thin-prior counts, and the K6 mechanical line (`496 133 0 0`, from the two ghost files) can all be recomputed without the box. If any of them disagrees with the fleet report, the ruling reopens — that is the point of publishing them.

## 3. Planning lesson (ruling §5.3), recorded

The fleet ran **37.5 h against an 18 h estimate**. The teacher's realized mean of 1,263 s/game was about twice the 8-game extended probe's mean and close to the probe's *maximum*; GATE_TIMEOUT = 3,870 s held, but the interim timeout rate reached 2.05% and came within a few games of the INCONCLUSIVE stop before resolving to 1.75% at the final count. An 8-game probe underestimates both the mean and the tail. Any future teacher fleet derives its timeout from a larger sample, or from a tail quantile with margin — not from a probe mean scaled by a round factor.

## 4. Close

With this commit, the records the ruling asked for are complete: stop (a) stated (§1), the data published (§2), the lesson recorded (§3). **Round 7 is closed.** The L3 jobs file (`/tmp/ggate/jobs_all.jsonl` on the box, sha256 `5fe5c0d85baf09f65777124f030a852db1c58fbf4b756f6cac587fe2f120e89b`) is retained for any future Gravy-search round, per the ruling; L2 is closed as moot. No launch is approved or pending.
