# Builder note — Joe's ratification of Flags 1 and 2 (round 7)

**Parent:** 7707f4cb498d1bca7bb90b82437cb1a2bbd8755b
**Records:** a decision taken in chat, for the repo's record.

On 2026-10-21 at 13:17 EDT, Joe ratified both decision flags from `rounds/round7/transfer-package.md` **as recommended**, in his own words in chat ("Ratify both flags as recommended"), following Claude's ratifications in `rounds/round7/claude-reply-3c46619.md`. The ratified positions:

- **Flag 1 — Option A.** The Gravy pipeline trains on the **current** featurizer. The (b) featurizer correction (deck counts from the view) debuts in the distillation run instead. Per Claude's §1, the build manifest records this re-timing as an **amendment to the round-6 closure**, not a silent change. The post-stage-3 report-only diagnostic (the round-5 census probe, unchanged, over 20 plain Gravy bridge games) is included.
- **Flag 2 — option (a), with Claude's added stop.** The Gravy PPO runs **without** the canonical-suite gate; the KL budget, spot gates, and heartbeat are retained. Added stop: **if the stage-2 Gravy anchor gate reads below 0.40, stop before PPO and return with a package** — the behavioral floors were tuned against a Fai anchor at 0.450.

With the design (3c466195), Claude's corrections C1–C5 (claude-reply-3c46619.md §2), and these ratifications, the basis for the round-7 **build package** is complete. The build package is being drafted under the standing measurement-build rule; nothing launches on this note.
