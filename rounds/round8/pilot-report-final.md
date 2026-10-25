# Round 8 — pilot report, FINAL (report-phase re-run outputs)

**Run:** the report-phase re-run of the resumed pilot, per
`claude-reply-8f834d2.md` §3 (re-run approved in the disposition)
and Joe's go recorded 2026-10-25 14:09 EDT ("launch when the fix
is committed"). Fix package: repo sha **9093f6d1**
(`rounds/round8/report-fix.md`).

## Launch record

- **Mode:** `PILOT_RESUME=report`, `PILOT_OUT=/tmp/distill_pilot_resume`,
  setsid-detached from `/home/joe/tcg/round8_code` on the box.
- **Deployed code, verified by sha256sum on the box BEFORE launch:**
  `pilot_report.py` =
  `8255c75406e810c533d0c64cceae31f7ce3e154887624eea7d84f39b7801ab39`;
  `run_pilot.sh` =
  `620cab683b87baaa4d1c2fd5ef87c128a9b65a43196877619b22ad022b6b3559`.
  (First deployment attempt was interrupted by a runtime restart;
  box state was checked before redeploying, and the verified hashes
  above are from the box itself after the successful deploy.)
- **Run log:** `/tmp/r8_launch/pilot_report_rerun.log`, sha256
  `4b8a97adde231ced2b6284db3eea88e090603e89f76ce6d5da749c23329c5f17`.
  Its first line: `report mode: 9 report-phase inputs pinned ok in
  /tmp/distill_pilot_resume` — the nine pinned input hashes asserted
  OK; no `PILOT STOP`. Its last line: `REPORT MODE COMPLETE - reads
  in /tmp/distill_pilot_resume/pilot_report.txt and
  /tmp/distill_pilot_resume/root_census_tally.txt`. No games were
  played and nothing was labeled; the mode ran `pilot_report.py`
  and phase 7 (teacher-root census) only.
- **Outputs:** `pilot_report.txt` written 2026-10-25 14:15:51 EDT,
  6,839 bytes, sha256
  `b7fc96b2ddbed3f4294745da2171ddbacedab60deee0c97576c007cdf72fcf48`;
  `root_census_tally.txt` written 14:15:53 EDT (see §3).

**Audit flag (builder's operator, for the record):** an interim
completion notice delivered to the operator mid-run contained a
full set of pilot figures (per-label mean 3.318 s, V1-ov 0.6351,
V2 0.9200 with the two-proportion test "flagged", a census of
1,647 featurizations with 4 disagreements, completion at 14:28).
**None of those figures appears in any artifact on the box** —
they conflict with the primary files on every number, including
file size and completion time. This note is built solely from
`pilot_report.txt` and `root_census_tally.txt` read directly off
the box and hash-pinned above and below. The interim figures
should be treated as void.

## 1. pilot_report.txt — verbatim

```
ROUND-8 PILOT REPORT (corrected V1/V2 design)

COST: 1194 label job-runs timed
  per-job secs: mean 4.3  p95 8.6  max 52.6
  corpus estimate (10000 contested labels): 12.0 box-hours serial at the mean, 24.0 at the p95; /4 label shards for wall-clock

THIN (excluded, counted): v1a 0, v1b 0, v2 0

V1 (unselected states, 547 states labeled twice; A overturns 30, A confirmations 517):
  V1-ov  P(B same overturn | A overturned): 5/30 = 0.167 Wilson95 [0.073, 0.336]
  V1-conf P(B confirms | A confirmed): 501/517 = 0.969 Wilson95 [0.950, 0.981]

V2 (100 gate overturn snapshots drawn; 100 labeled, 0 thin/excluded):
  V2  P(labeler pick == live pick | live overturned): 22/100 = 0.220 Wilson95 [0.150, 0.311]
  V2 vs V1-ov: two-proportion z-test p = 0.528 (exchangeability predicts V2 ~= V1-ov; caveat: gate states lie on teacher trajectories, V1's on v15's - the same game up to each trajectory's first overturn. The read is the reviewer's.)

MECHANISM (report-only): 96 unselected-candidate comparisons (skipped 4): z mean -0.01, sd 0.86, max |z| 2.60, |z|>2: 3 (3.1%; ~5% expected under N(0,1))

DEADLINE ACCOUNTING (label deadline 300 s vs live 180 s): 3504 candidate batches timed
  batches past 180 s: 0 - worlds finished after 180 s are at most their finished count, 0 (batches at/under 180 s contribute exactly 0; exact per-world finish times are not recorded by the machinery)
  worlds killed at the 300 s label deadline: 0, across 0 candidates

V2 per-snap detail (snap: live pick / labeler pick):
  100538517_t2: live=4 labeler=0
  101672839_t1: live=1 labeler=0
  102504102_t1: live=5 labeler=0
  104859214_t1: live=3 labeler=0
  106180451_t1: live=2 labeler=0
  106180451_t2: live=3 labeler=0
  141439723_t1: live=3 labeler=3
  146890983_t3: live=1 labeler=0
  151376695_t4: live=2 labeler=1
  177427395_t3: live=1 labeler=0
  185089348_t1: live=3 labeler=0
  192435629_t2: live=0 labeler=0
  224184883_t2: live=0 labeler=2
  230025821_t1: live=0 labeler=1
  240699480_t2: live=0 labeler=0
  245822681_t3: live=1 labeler=0
  247713455_t1: live=3 labeler=0
  249399189_t4: live=1 labeler=1
  253515357_t1: live=4 labeler=0
  261299870_t3: live=0 labeler=0
  275555316_t2: live=1 labeler=0
  283874810_t2: live=0 labeler=2
  286622955_t1: live=1 labeler=0
  299793305_t4: live=0 labeler=0
  308506096_t3: live=4 labeler=0
  312027077_t1: live=2 labeler=0
  332939830_t1: live=7 labeler=7
  352414813_t2: live=1 labeler=0
  352414813_t4: live=0 labeler=1
  363780743_t1: live=2 labeler=1
  396482375_t1: live=1 labeler=0
  404687769_t2: live=4 labeler=4
  424953585_t2: live=2 labeler=0
  429337154_t2: live=2 labeler=1
  443377021_t2: live=0 labeler=3
  450208349_t2: live=0 labeler=3
  453780254_t1: live=4 labeler=0
  466913784_t2: live=4 labeler=4
  468256557_t3: live=3 labeler=2
  468256557_t4: live=1 labeler=0
  470809765_t2: live=3 labeler=0
  470809765_t4: live=1 labeler=0
  486188185_t3: live=0 labeler=2
  506173128_t2: live=2 labeler=3
  512508051_t3: live=2 labeler=1
  518617437_t2: live=3 labeler=0
  525257873_t5: live=1 labeler=1
  528177756_t1: live=2 labeler=2
  532678258_t1: live=1 labeler=0
  535008025_t1: live=0 labeler=4
  540196335_t5: live=1 labeler=0
  542643293_t2: live=0 labeler=1
  550671073_t1: live=1 labeler=0
  568801178_t4: live=1 labeler=5
  580293934_t3: live=1 labeler=0
  580293934_t5: live=1 labeler=0
  586772136_t5: live=0 labeler=2
  586772136_t7: live=0 labeler=0
  587070307_t3: live=3 labeler=3
  587070307_t4: live=1 labeler=1
  596519861_t6: live=5 labeler=0
  597029063_t5: live=2 labeler=1
  604327160_t6: live=1 labeler=0
  619149711_t1: live=0 labeler=1
  633135967_t1: live=1 labeler=0
  633135967_t3: live=2 labeler=0
  645230247_t1: live=0 labeler=4
  668369723_t1: live=0 labeler=1
  672873580_t1: live=2 labeler=0
  692043770_t1: live=1 labeler=0
  695077851_t1: live=2 labeler=0
  701071154_t2: live=2 labeler=0
  702248295_t4: live=4 labeler=0
  706527131_t1: live=5 labeler=5
  708457807_t2: live=0 labeler=1
  711281845_t1: live=1 labeler=0
  734279920_t3: live=1 labeler=0
  782757660_t2: live=3 labeler=2
  790539720_t2: live=1 labeler=1
  802309492_t1: live=1 labeler=0
  802309492_t4: live=2 labeler=2
  803632319_t3: live=2 labeler=2
  809926015_t2: live=3 labeler=3
  814004430_t1: live=2 labeler=2
  814004430_t2: live=3 labeler=1
  827464587_t3: live=0 labeler=2
  832322239_t2: live=1 labeler=2
  842622409_t2: live=5 labeler=0
  847636014_t3: live=1 labeler=0
  856449457_t2: live=4 labeler=0
  856449457_t4: live=0 labeler=1
  903445241_t1: live=1 labeler=0
  939758852_t1: live=5 labeler=2
  951441882_t5: live=1 labeler=0
  990737587_t1: live=1 labeler=0
  990737587_t2: live=0 labeler=1
  990737587_t4: live=2 labeler=2
  995745898_t4: live=1 labeler=1
  999410826_t3: live=0 labeler=2
  999410826_t5: live=2 labeler=0
V1 A/B disagreements: 41 of 547 states
  140079940_t18: A pick 1 (ov 1), B pick 0 (ov 0)
  169234412_t3: A pick 6 (ov 0), B pick 4 (ov 1)
  218711839_t4: A pick 0 (ov 1), B pick 2 (ov 0)
  218711839_t5: A pick 1 (ov 0), B pick 0 (ov 1)
  218711839_t9: A pick 1 (ov 1), B pick 0 (ov 0)
  220719073_t15: A pick 0 (ov 0), B pick 1 (ov 1)
  220719073_t38: A pick 2 (ov 1), B pick 3 (ov 0)
  220719073_t73: A pick 1 (ov 1), B pick 0 (ov 0)
  286996099_t19: A pick 2 (ov 1), B pick 0 (ov 0)
  286996099_t25: A pick 0 (ov 0), B pick 5 (ov 1)
  286996099_t39: A pick 2 (ov 1), B pick 1 (ov 0)
  324193875_t3: A pick 0 (ov 0), B pick 1 (ov 1)
  324193875_t32: A pick 0 (ov 1), B pick 1 (ov 0)
  324193875_t42: A pick 2 (ov 0), B pick 0 (ov 1)
  324193875_t50: A pick 1 (ov 1), B pick 0 (ov 0)
  324193875_t52: A pick 2 (ov 0), B pick 1 (ov 1)
  324193875_t53: A pick 1 (ov 1), B pick 0 (ov 0)
  324193875_t65: A pick 0 (ov 0), B pick 2 (ov 1)
  396512818_t32: A pick 0 (ov 0), B pick 2 (ov 1)
  396512818_t57: A pick 0 (ov 1), B pick 3 (ov 0)
  423095452_t42: A pick 0 (ov 0), B pick 4 (ov 1)
  423095452_t45: A pick 0 (ov 0), B pick 4 (ov 1)
  423095452_t49: A pick 0 (ov 1), B pick 1 (ov 0)
  566235298_t9: A pick 0 (ov 1), B pick 1 (ov 0)
  745681102_t60: A pick 0 (ov 0), B pick 2 (ov 1)
  831144116_t34: A pick 2 (ov 1), B pick 0 (ov 0)
  831144116_t50: A pick 1 (ov 0), B pick 2 (ov 1)
  846941112_t22: A pick 2 (ov 1), B pick 1 (ov 1)
  846941112_t54: A pick 4 (ov 0), B pick 0 (ov 1)
  846941112_t79: A pick 4 (ov 1), B pick 0 (ov 0)
  846941112_t80: A pick 2 (ov 1), B pick 3 (ov 0)
  852109890_t27: A pick 2 (ov 1), B pick 1 (ov 0)
  852109890_t42: A pick 0 (ov 1), B pick 1 (ov 0)
  852109890_t43: A pick 3 (ov 1), B pick 0 (ov 0)
  852109890_t48: A pick 3 (ov 0), B pick 0 (ov 1)
  852109890_t63: A pick 1 (ov 1), B pick 0 (ov 0)
  882717405_t21: A pick 0 (ov 1), B pick 3 (ov 0)
  945603323_t12: A pick 0 (ov 0), B pick 3 (ov 1)
  945603323_t4: A pick 0 (ov 1), B pick 1 (ov 0)
  955924560_t11: A pick 2 (ov 1), B pick 0 (ov 0)
```

## 2. Teacher-root census (phase 7) — tally verbatim

Artifact: `/tmp/distill_pilot_resume/root_census_tally.txt`,
2,038 bytes, sha256
`0d9d2bb7ec366f6790373bdf6c909e441f79f0254b8be9e1e7ab1afb614f36ae`
(source rows: `/tmp/distill_pilot_resume/root_census.jsonl`).
Report-only, as registered: **647 featurizations over the pilot's
647 label-job roots (547 V1 + 100 V2), 0 disagreements** — the
teacher-root population shows no store/view divergence at its
roots (the roots are post-sync states; the (b) correction binds at
live serving between syncs, per the build package's smoke finding).

```
ROUND-5 (b) CENSUS TALLY
========================
/tmp/distill_pilot_resume/root_census.jsonl: 647 featurizations, 0 disagreements, 106 games
TOTAL: 647 featurizations, 0 disagreements, 106 distinct games

OVERALL
  disagreement rate: 0/647 = 0.000%  Wilson95 [0.000%, 0.590%]
  direction store>view: 0/647 = 0.000%  Wilson95 [0.000%, 0.590%]
  direction view>store: 0/647 = 0.000%  Wilson95 [0.000%, 0.590%]
  direction mixed: 0/647 = 0.000%  Wilson95 [0.000%, 0.590%]

BY BRANCH (each direction split)
  A all: 0/3 = 0.000%  Wilson95 [0.000%, 56.150%]
  ARS all: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]
  B all: 0/356 = 0.000%  Wilson95 [0.000%, 1.068%]
  D all: 0/5 = 0.000%  Wilson95 [0.000%, 43.448%]
  M all: 0/226 = 0.000%  Wilson95 [0.000%, 1.671%]
  P all: 0/46 = 0.000%  Wilson95 [0.000%, 7.707%]

ARS RATE (explicit, reporting addition 2)
  ARS all directions: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]
  ARS store>view: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]
  ARS view>store: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]
  ARS mixed: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]

BY PLAYER (each direction split)
  player 1 all: 0/597 = 0.000%  Wilson95 [0.000%, 0.639%]
  player 2 all: 0/50 = 0.000%  Wilson95 [0.000%, 7.135%]

BY PLAYER x BRANCH=ARS
  player 1 ARS: 0/11 = 0.000%  Wilson95 [0.000%, 25.883%]
  player 2 ARS: n=0

DIFFERING-CARD TABLE (card: differing featurizations; delta (store-view) distribution)
  distinct cards differing: 0; total card-diff entries: 0

DOUBLE-COUNT SIGNATURE SUBSET (store>view diffs whose excess is fully accounted by view_elsewhere)
  store>view featurizations: 0; in signature subset: 0; by branch: {}

VIEW>STORE ZONE MEMBERSHIP (Claude reporting addition 1)
  view>store featurizations: 0. Whether a differing card appears in any other serialized zone is UNAVAILABLE from the census log for this direction: the probe computes view_elsewhere only for store>view diffs and writes its initialized 0 for view>store diffs, so the logged third element carries no zone information here.
```

## 3. What this completes

Every registered pilot read now exists: V1-ov, V1-conf, V2 with
its thin count (0) and the two-proportion test against V1-ov,
the mechanism z summary, the deadline accounting, the cost reads
and corpus estimate, and the teacher-root census. The pilot
awaits the reviewer's ruling on these reads; the corpus stays
gated on that ruling, with the one-capture-per-seed declaration
(option (a)) and the sign-test fix still owed.
