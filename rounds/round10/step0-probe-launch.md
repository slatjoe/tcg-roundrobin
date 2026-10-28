# Round 10 — Step 0 probe: LAUNCH RECORD (attempts 1–3)

Registered design: `step0-probe-package.md` (as amended through §11). Approved build: **5ce1f585** (Claude's confirmation, `claude-reply-5ce1f58.md`, committed 358a5a22). Launched sha for attempt 3: **358a5a22** — differing from the approved sha only under `rounds/` (the confirmation reply file). Box launch manifest: `/home/joe/tcg/r10probe_out/probe_launch_manifest.json` (final sha256 `445ec3f6…`). Deploy dir: `/home/joe/tcg/round10_code` (18 files; the 16 pinned files read back equal to the runner's `expect_hash` literals; the fixed runner at sha256 `7c7b8f80…`).

## Attempt 1 — 2026-10-28 11:01 EDT: ABORTED at the free-space pre-flight

Joe's go 09:58 CDT (with tracker). Deploy verified (16/16 pins read back). The runner passed its pin block and refused at its FREESPACE gate: required 5,858,893,850 B (468,711,508 × 10 trees × 1.25) vs 3,105,521,664 B available in /tmp. Nothing copied, no server started. Launch parameter recorded in the manifest: `GTREE=/tmp/gravytree` via the runner's own env override (its built-in default `/home/joe/tcg/gravytree` does not exist on the box; `/tmp/gravytree` is the canonical source tree every round-9 runner used).

**Remedy (Joe's direction — rehome, don't delete):** Stage 3's twelve completed-run scratch trees (`/tmp/r9s3_gm_*` ×8, `/tmp/r9s3_l3_tree_*` ×4; 5,883,555,565 B) moved to `/home/joe/tcg/tmp-archive/`, byte totals verified equal before/after; `/tmp/gravytree` and the round-8 leftovers untouched. /tmp available after: 9,680,859,136 B.

## Attempt 2 — 2026-10-28 11:59:42 EDT: LAUNCHED, KILLED AS VOID

Runner pid 3559247. First-minutes checks: pins PASS (16/16), FREESPACE PASS, containment clean, both capture servers up on `ckpt_v10`/cuda (fallbacks=0), capture games running. **Check (f) FAILED**: the snapshot index held 608 rows, **0 uncontested**. Root cause, read from the live game processes' environment and the sources: `run_probe.sh` never delivered `TEACHER_CAPTURE_UNCONTESTED`, which `search_s3.php`'s hook gates on together with `TEACHER_CAPTURE`; the fixture suite had always set the environment by hand, so the runner's own capture environment was never exercised. The builder killed the run at 12:02 EDT (50 capture games complete: seat-1 block 45/45, seat-2 5) — the capture could not serve the registered design, and every further minute was waste. No registry merge had run; no measurement was taken. Outcome recorded in the box manifest (`attempt2_outcome`, manifest sha at the time `039b2377…`).

Remediation: third fix pass (commit **5ce1f585**) — one env-prefix line in the runner, the composed-environment fixture `fx_runner_env.py`, and the full getenv audit (§11 of the package doc); Claude's confirmation (358a5a22) with the TEACHER_TUPLE_JSON flag ruled inert (documentation condition discharged in the probe report and its data MANIFEST: capture stat rows are stamped `unpinned` **by design**).

## Attempt 3 — 2026-10-28 12:32:09 EDT: RUNNING

Joe's go 11:30 CDT. Pre-launch, per the confirmation's §3: attempt 2's outputs archived under `/home/joe/tcg/r10probe_out/attempt2_void/` (nothing consumed by the relaunch); its 50 capture game ids merged into the do-not-train registry under tag `r10_probe_capture_void` (registry 7,331 → **7,381** games, sha256 `1485ef0a…`); seeds 24001–24090 reused as accepted (raw-policy deterministic games; no measurement taken from the void attempt); the fixed runner redeployed and read back at `7c7b8f80…`.

Runner pid **3604700**, log `probe_launch3.log`. **First-minutes verification — all seven checks PASS**: pins; FREESPACE; containment; servers on ckpt_v10/cuda; capture games running; **the hook check with direct evidence — `TEACHER_CAPTURE_UNCONTESTED=1` read in a live game process's environment, and uncontested snap rows flowing at ≈34.9 uncontested : ≈20.7 contested per game over the first 26 completed games** (the registered expectation ≈34:24 at EVERY=2; attempt 2's failure signature was 0); no ABORT.

Phases from here, as registered: capture (90 games) → registry merge (tag `r10_probe_capture`) → eval → jobs (class counts printed; extension rule armed) → labels → analyze → report, with publication in `data/step0/`.
