# Round 7 — sweeper fail-safe fix: confirmation (the §2 change, its two tests, the moved pins)

**Parent:** 0d4ee645304f7cc5f5e403be8269d9efa02ec050 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** `rounds/round7/claude-reply-ef34219.md` §2 — the one missing case in the (C) selector (a segment whose `ipcs -m -p` row is withheld or malformed parses to no cpid/lpid, defaulted to 0, and 0 is never a live pid, so the segment was selectable), the fail-safe fix specified there, and the re-test it requires before the pre-gate may launch.
**Status: CONFIRMATION.** The fix is exactly the §2 change and nothing else (§1); it is verified by the new canned-listing case (§3) and by the §1.4 micro-test re-run (§4); both runners' sweeper pins move with it (§5). `kernel.pid_max` is recorded at §6. Nothing launched on this package.

---

## 1. The fix — `code/shm_sweep.py` `728a0149…` → `98027a8b…`

In `select()`, a segment whose cpid or lpid is missing or ≤ 0 is now KEPT before any other rule evaluates it, and counted per pass; the PASS line carries the counter as `unattributed=N`, so a `-p` parse regression shows in the log as a rising unattributed count with selection collapsing — visible, never silent. New sha256: **`98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33`**. `py_compile` clean. The unified diff in full:

```diff
--- a/code/shm_sweep.py (728a0149)
+++ b/code/shm_sweep.py (98027a8b)
@@ -145,13 +145,23 @@
     live = live_pids()
     gkeys = game_keys(games_dir)
     chosen = []
+    unattributed = 0
     for shmid, s in sorted(segs.items()):
+        cpid = s.get("cpid")
+        lpid = s.get("lpid")
+        if cpid is None or lpid is None or cpid <= 0 or lpid <= 0:
+            # Fail-safe (claude-reply-ef34219 sec.2): a segment with
+            # no usable pid attribution - its -p row withheld or
+            # malformed - is never selected. If the -p parse ever
+            # regresses, the sweep keeps everything and the leak
+            # grows; it never deletes unattributed memory. Counted
+            # per pass so the regression is visible in the log.
+            unattributed += 1
+            continue
         if s.get("owner") != "joe":
             continue
         if s.get("nattch") != 0:
             continue
-        cpid = s.get("cpid", 0)
-        lpid = s.get("lpid", 0)
         if cpid in live or lpid in live:
             continue
         if s.get("key") in gkeys:
@@ -159,7 +169,7 @@
         if shmid in start_shmids:
             continue
         chosen.append((shmid, s))
-    return chosen
+    return chosen, unattributed
 
 def fmt_time(raw):
@@ -208,17 +218,19 @@
     pass_no = 0
     while True:
         pass_no += 1
+        unattributed = 0
         try:
             segs = parse_segments()
-            chosen = select(segs, start_shmids, a.games_dir)
+            chosen, unattributed = select(segs, start_shmids,
+                                            a.games_dir)
         except Exception as e:  # keep logging; a pass error is evidence too
             log.write("PASS %d %s ERROR %r\n"
                       % (pass_no, datetime.datetime.now().isoformat(), e))
             chosen = []
             segs = {}
-        log.write("PASS %d %s total=%d selected=%d\n"
+        log.write("PASS %d %s total=%d selected=%d unattributed=%d\n"
                   % (pass_no, datetime.datetime.now().isoformat(),
-                     len(segs), len(chosen)))
+                     len(segs), len(chosen), unattributed))
         deleted = 0
         failed = 0
         for shmid, s in chosen:
```

Nothing else changed: the four selection rules, the SELECT/DELETE logging, the modes and the interface are byte-identical outside these hunks (the internal `select()` return gains the counter; the CLI surface changes only in the PASS line's added field, as specified).

## 2. What the fix closes

Before: `parse_segments()` sets cpid/lpid only when a well-formed `-p` row exists for the shmid; `select()` defaulted a missing value to 0, and `0 in live` is always False, so an unattributed segment passed the dead-pid rule and could be deleted. After: attribution is a precondition — no usable cpid AND lpid, no selection, whatever the other rules say. The failure direction inverts with the rest of the design: a parse regression now over-keeps (the leak grows, the run is unharmed, and the log says why).

## 3. The canned-listing test (the new case)

**Method.** The narrowest testable seam is the module's own two-stage path: the test monkeypatches `run_ipcs()` to serve synthetic fixtures and calls the REAL `parse_segments()` and `select()` — the same code the sweep runs, not a reimplementation. Fixture: two joe-owned, `nattch` 0 segments in `ipcs -m`; the `-p` fixture carries a row for shmid **910002 only** (cpid 3999999 / lpid 3999998, both asserted dead against the live pid set before the run); shmid **910001's `-p` row is withheld**. Games dir: an empty scratch dir (no rule-3 keys); start set: empty.

**Output (verbatim):**

```
parsed shmids: [910001, 910002]
910001 fields: {'key': 788529153, 'owner': 'joe', 'nattch': 0, 'atime': 'Not set', 'dtime': 'Not set', 'ctime': 'Not set'}
910002 fields: {'key': 788529154, 'owner': 'joe', 'nattch': 0, 'cpid': 3999999, 'lpid': 3999998, 'atime': 'Not set', 'dtime': 'Not set', 'ctime': 'Not set'}
selected: [910002]
unattributed: 1
CANNED TEST PASS: 910001 KEPT + counted unattributed=1; 910002 SELECTED
```

The withheld row parses to a segment dict with **no cpid/lpid keys at all** (asserted in the test) — the pre-fix default-0 hole in its exact shape. Post-fix: 910001 is KEPT and counted (`unattributed=1`); the normal orphan 910002 is still SELECTED. Both halves of the §2 requirement hold in one run.

## 4. The micro-test re-run (the §1.4 test, fixed sweeper, on the box, no games)

The fixed sweeper was deployed to `/tmp/shmtest2/shm_sweep.py` and hash-verified on the box before any pass: `98027a8b…` — identical to the repo file. Evidence under **`/tmp/shmtest2/`** (`baseline_ipcs.txt`, `dry.log`, `after_create_ipcs.txt`, `after_create_ipcs_p.txt`, `live.log`, `after_sweep_ipcs.txt`, `final_ipcs.txt`). One pass per run (stop-file pre-created), the runners' interpreter, scratch Games root `/tmp/shmtest2/games/` holding the fabricated directory `555000111`.

| Step | Result |
|---|---|
| Baseline | 0 segments (`ipcs -m` rows `^0x` = 0); start set empty |
| Dry pass on the baseline | `PASS 1 … total=0 selected=0 unattributed=0` |
| Segment creation | one short-lived PHP process creates 3 segments (keys 777000111 / 777000222 / 555000111, 32,768 B, nattch 0); `-p` listing shows cpid = lpid = 815349 (the PHP pid, dead on return) for all three |
| Live pass | `PASS 1 … total=3 selected=2 unattributed=0` |
| Deletions | `DELETE shmid=547192835 key=777000111 -> OK`; `DELETE shmid=547192836 key=777000222 -> OK`; `DELETED pass=1 count=2 failed=0` |
| Rule-3 keep | shmid 547192837 (key 555000111, matching the fabricated Games directory) NOT selected, still present after the sweep |
| By hand | the kept segment removed with `ipcrm -m 547192837`; final count **0** — the box is back at its baseline |

The §1.4 behavior is unchanged by the fix (withheld attribution never arises in this test, and `unattributed=0` on both PASS lines says so), and the new field reads 0 exactly where it should.

## 5. The pins move (both runners, pin-line only)

Each runner's `expect_hash "$TREE/shm_sweep.py"` pin moves `728a0149…` → `98027a8b…`. The old hash occurred exactly once per file (the pin line; neither runner carries the sweeper's hash in prose), so each diff is the single line:

**`code/run_gravy_pregate.sh`** — `ddbc9d3c…` → **`d519beb126d6c919e989a5df946c97d2c574cd7dcba5cc3d26b8a44cef8f26a5`**, `bash -n` clean. Diff:

```diff
@@ -138,7 +138,7 @@
   338183e255acfa1b8ec23fd73511e55e291b8af64686ddaf84e7ba1779e3162e \
   "gate_ipcs_cleanup.sh (standing G8 sweep, round-3 committed copy)"
 expect_hash "$TREE/shm_sweep.py" \
-  728a0149e1241079ba09898481c9cacfe6606b53c5aa3bab09b3a1009269b290 \
+  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
   "shm_sweep.py ((C) production sweeper, containment package)"
 expect_hash "$TREE/parse_r3_pair.py" \
   ed47c9cd2ac90947e0552f1c9c2959b4834ac9ac6f65bff120085c4b45701fa1 \
```

**`code/run_gravy_gate.sh`** — `49cf0d78…` → **`0ffe635b7fe81fdb41325cc55f27d1af09f3909fb4f70a65522d9655d5e453a2`**, `bash -n` clean. Diff:

```diff
@@ -98,7 +98,7 @@
   c3fb227e76084a7a9e509ca9cde38295c9f3e286ed48f79295749fd895e20a93 \
   "gate_raw_retry.py (unchanged stock copy; caps live in the driver)"
 expect_hash "$TREE/shm_sweep.py" \
-  728a0149e1241079ba09898481c9cacfe6606b53c5aa3bab09b3a1009269b290 \
+  98027a8b6f58bb06651c5b1e5203872fa2939aea464da5f180907dde43d14f33 \
   "shm_sweep.py ((C) production sweeper, containment package)"
 
 mkdir -p $OUT
```

Revision chains: pregate runner `19cb3c13…` → `ddbc9d3c…` → `d519beb1…`; fleet runner `2895c4a0…` → `0c458627…` → `49cf0d78…` → `0ffe635b…`. At any launch, the tree's deployed `shm_sweep.py` must hash `98027a8b…` or the guard aborts — the deployment copy is placed and hash-verified by the launch step, as with every pin.

## 6. Report-only: `kernel.pid_max`

Read on the box (`sysctl kernel.pid_max`) during this confirmation: **`kernel.pid_max = 4194304`**. Recorded for the pid-reuse bound (§2 of the reply): a leaked segment is wrongly kept only if its dead child's pid is recycled by an unrelated live process inside the segment's leak-to-sweep window; with a 4,194,304 pid space, the per-window collision probability is on the order of live-pids / 4.2M — and the direction is KEEP in any case. No code rides on this value.

---

**On this confirmation, the pre-gate may launch on Joe's go (with Joe's §5 spot-check requested before then), and the fleet under its §4 launch condition. Nothing in this package launches anything.**

*Builder: Muse (for Joe Slattery), 2026-10-22. Review venue: this repository. Joe relays; Claude reviews.*
