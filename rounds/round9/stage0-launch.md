# Round 9 — Stage 0 launch manifest

**Launched:** 2026-10-25 (evening EDT), on the box, detached.
**What runs:** run_stage0_l3.sh — L3 labeling of the round-7
fleet's 118 overturn decisions (88 games) at LABEL_W=50, CRN,
against the production server serving ckpt_v10. PRIMARY pass
(byte-pristine driver, seed bases 855001 + shard x 10^8), then
the D7 HORIZON co-report pass (r9_label_main.php, LABEL_HORIZON
= 62, seed bases 875001 + shard x 10^8). No games are played;
the registry is untouched.

## Authorization chain

- Design approved in direction: c76f6856 (D1-D6 settled, D7
  proposed); D7 adopted by Joe 2026-10-25.
- Stage 0 launch package: 2db6b77f.
- Claude's code review (CHANGES REQUESTED, one blocking item):
  bf71c09a.
- Report fix (sec.2 taxonomy + sec.3 additions, fixtures all
  passing incl. FX7-ROWS 28/300 = 0.0933): a00dad50.
- Claude's confirmation of the fix: 71c91f14 — CONFIRMED, with
  one pre-launch defect named (the runner's stale report pin)
  and its remedy pre-authorized in his sec.2.
- **Joe's go: given 2026-10-25 20:29 EDT, banked against the
  confirmation; it stands for this launch.**

## The pin fix (the confirmation's sec.2 remedy, verbatim scope)

The confirmation extends to a commit whose diff against
a00dad50 is exactly one line plus round9 notes. The diff:

```
 rounds/round9/code/run_stage0_l3.sh, line 97 (the
 stage0_report.py expect_hash pin):
-  5019d94ee21c0d4b71e454b101bf2d0eff23d4749e2dd2033557fd4bd7a6ecef
+  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf
```

The new literal was machine-copied from sha256sum of the
deployed stage0_report.py (never typed); exactly one occurrence
replaced; the runner's other 20 pin literals audited — all
exactly 64 hex, no 63/65-char strings. Runner's new hash:
**4f5f818386056c4e7b6ebb71612e514414f688783b3aa624a2f3c8955c821222**.
Launched sha = the commit carrying this manifest; it differs
from the approved chain only by this pin line and round9 notes,
as the confirmation's extension specifies. Claude verifies the
diff after the fact.

## Registered with this run (claude-reply-a00dad5)

- **Sec.3 — the tie-as-loss co-reads (report-only):** after the
  run, a second version of each read (primary and horizon) is
  computed OFFLINE from the published label rows with draws
  scored as losses (world score 0 for winner == 0, finished or
  horizon == 1) instead of 0.5. No relabeling, no runner
  change. It decides nothing at Stage 0; Joe and the builder
  settle the tie value for downstream use before Stage 1 is
  designed.
- **Sec.4 — publication:** both passes' label rows, the scorer
  outputs, the (D) reports (incl. the tie-as-loss reads) and
  this manifest's run record are published under
  rounds/round9/data/stage0/ with hashes, for independent
  recomputation.
- **Interim notices carry status only.**

## Run record (filled at completion)

- OUT dir on the box: (stated in the completion report)
- Walls, row counts, fallbacks, SHM close: (completion report)
- Stage 0 report: rounds/round9/stage0-report.md (to come)
