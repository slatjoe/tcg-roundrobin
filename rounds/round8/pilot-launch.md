# Round 8 — pilot + Gravy census launch manifest

**Parent:** 0bf0ea70 (Claude's approval of the fix package).
**Approved build sha:** dc22f1d3 (approved in `claude-reply-dc22f1d.md`; the launched state differs from it only by reply/manifest files under `rounds/`, per the launch-gate rule).
**Authorization:** Joe's go, 2026-10-25 11:49 EDT, in this chat ("Launch the pilot + Gravy census pre-step").

## What launches

1. **The Gravy census pre-step** (`code/run_gravy_census.sh`, sha256 `5dd71d58…`): the round-5 census probe unchanged, 20 plain Gravy bridge games, seeds 8801–8820, production server, v10 bridge model, out `/tmp/gravy_census_diag`. Report-only; the 20 games join the do-not-train registry with the pilot's records commit.
2. **The pilot** (`code/run_pilot.sh`, sha256 `eff185fd…`), phases as registered in `build-fix.md` §4:
   - **Capture phase:** corpus capture games restricted to seeds **10001–10020** only (PILOT_CAPTURE), on the corpus tree (capture patch product asserted `044ca8ec…`). Run A's labels on these games are ordinary corpus labels.
   - **Capture-equivalence check:** corpus-tree capture vs raw v15 on the native tree, 10 seeds per seat vs the heuristic, `r3_pair.py` read through the strict parser — must be IDENTICAL. **Failure stops the pilot before any labeling.**
   - **V1:** every contested state from the capture games labeled twice (runs A/B, different world seeds); V1-ov and V1-conf with Wilson intervals.
   - **V2:** 100 gate-fleet overturn snapshots, stratified across the 8 streams, from the preserved copy `/home/joe/tcg/gate_r4_v2_preserve/`; V2 against V1-ov (two-proportion test, trajectory caveat printed); **the V2 thin count printed beside V2** (per the approval's §4).
   - **Mechanism check (report-only):** per-candidate z-scores, labeler means vs live stat means, candidates outside the live overturn pair.
   - **Deadline accounting:** label worlds finished after 180 s; candidates cut at the 300 s label deadline vs the live 180 s.
   - **Cost:** per-job mean / p95 / max over the pilot's ~1,200 label jobs; the corpus estimate derives from these.
   - **Teacher-root census** on the pilot's label roots, report-only.
   Supporting pins: `run_capture_corpus.sh` `10c4e570…`, `distill_label_main.php` `4f1de80a…`, `label_reduce.py` `e2244fbb…`, `pilot_prep.py` `3131264b…`, `pilot_report.py` `45b55741…`; corrected featurize `3dcf32c9…`; trees `/tmp/distilltree_native` (featurize `f81193e0…`) and `/tmp/distilltree_corrected` (featurize `3dcf32c9…`), differing in exactly that file.

## Conditions

- Standing pre-launch G8 sweep on the box before the first run; (C) kernel-attribution containment for production-tree teacher work, per the package.
- Local Talishar only; observation masking and the canary unchanged.
- The pilot's registered stop: equivalence failure halts before labeling. Any other stop or anomaly is reported, not improvised around.
- **Not launched:** the corpus (gated on Claude's pilot review, with the one-capture-per-seed declaration still owed), T1 training, the gate (which additionally requires the sign-test fix).
- Results are staged as a pilot report + census report for the builder's audit and a records commit; interim monitoring is not evidence.
