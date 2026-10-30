# Step 1 pilot - label storage note (2026-10-30)

The eight L3 label part files are stored in this directory GZIP-COMPRESSED, as `l3/labels_shard*_p*.jsonl.gz`.
Reason: the plain parts run 16-45 MB each and the GitHub blob API rejected the largest during the publication
commit (HTTP 422, input too large); the labels_all.jsonl concatenation (241,460,621 B) exceeds the 100 MB
per-file limit outright and is not stored (it is the concatenation of these eight parts). gzip -9 compresses
each part ~40x. Every stored .gz decompresses to bytes whose sha256 EQUALS the plain file's sha256 recorded
in data/step1/MANIFEST.md and in pilot_manifest.json - verified at staging time for all eight parts.
Verify any part with:  gzip -dc labels_shardX_pY.jsonl.gz | sha256sum   (compare MANIFEST.md).

| stored file | gz sha256 | decompressed sha256 (= MANIFEST) |
|---|---|---|
| l3/labels_shard0_p1.jsonl.gz | 2372ab0666b9d648ceeb82e2cd03fbdd7e7d68d260b4eb5bf49be31f6085f83f | deefc6d3fd79b2c9bebdd7a87c7c236ca34b62e4122e967ce5cbde04986762b5 |
| l3/labels_shard0_p2.jsonl.gz | 2c8f1202d40917d0bda0de8c23acf6e27c1536c00a70f98efc10c08139ba4a76 | 5c466b5ca4274ba76d0b9600c11bc8a6d19f8fbe7d11f9375ac5112a7c4f196e |
| l3/labels_shard1_p1.jsonl.gz | ff554c13857abb2e58bf7d13260989d138a8cd3d6bdc8228026aa829b0914eb0 | f84b2fb1c48590747c5efbd1b718e1dc965f7f8f87fe9d86dbe7806ce5d95190 |
| l3/labels_shard1_p2.jsonl.gz | 5c78654e10561d3b1ea2c6feb330e3a4c652c81c6387c498d1671d65304ed93c | 9ff1a7c5474a09dfb1f4a0a49ebc1efbf631745f28719735064684f0fa94ba76 |
| l3/labels_shard2_p1.jsonl.gz | cc190de295136b73a07e9350966f22c4802ea430e7cdb487499aeda0b9acfd24 | 9b27adaa2961ab0c906e3638f50dc2620cfa10dafe08a017434be2c21b68982a |
| l3/labels_shard2_p2.jsonl.gz | 5f1301c6dc945269ff4cfacf658aa67a9d5adfdc2094a476fd12f22f6766745d | e4f299c1af8942e7d6dc2004105d519fb46182169226966c7b96949619c23af9 |
| l3/labels_shard3_p1.jsonl.gz | 3fe5b9039b8ee4a724da7c8acb24c64919b34a65b5cbabafc056d3100ccea949 | 26f9b39ecb49ba277c5bc9538933fdfb81cef30202c5594eeeb08a30c43aaf89 |
| l3/labels_shard3_p2.jsonl.gz | 65a0ba9ed37cb165dff5a85ebaf0f8177ec39150d886a17fa89ec4adfd4155e1 | e6a59ea0e047c5174ae9a3bbe2e98b24896661e26ebdd35438ea46752c011e23 |
