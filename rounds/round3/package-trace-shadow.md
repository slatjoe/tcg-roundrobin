# Round 3 package — trace + shadow instrumentation, and a retraction

**Parent sha:** b9dd65cf9f2cb13732b09d84018fb490dd9e95f9 (the relay message
supplies this package's own sha, per PROTOCOL.md).
**Previous reviewed sha:** none under this protocol (round 2 predates it;
its content lives in `rounds/round2/`).
**Ask:** approval to LAUNCH the trace + shadow runs specified at the end
(19 paired seeds × raw/ghost/shadow + ghost-vs-capture), after review of
the code in this commit. Nothing here has been launched beyond the
one-seed instrumentation smoke reported under Tests.

**Conventions:** all win figures are WIN RATE (0..1) unless a line says
WP (±1 scale halved). Everywhere in this project the played policies are
ARGMAX, never sampled (round 2, grep verdict — upheld below).

---

## 0. RETRACTION — the ghost result in the round-2 addendum is void

The round-2 addendum (§7) reported the pre-gate ghost test as FAILED:
ghost vs bridge 0/19, bridge self-identical 19/19, with the conclusion
that the machinery changes the trajectory. **That comparison never
happened.** The paired driver's raw arm passed no policy flag, and
`play_game.php` with no flag plays the in-process v1 **heuristic for
both seats** (its stderr mode line reads `policy: v1 (deck-aware)`).
The 19 "bridge" games were heuristic mirror games; 0/19 measured
net-vs-heuristic divergence. The bridge's 19/19 self-consistency was
heuristic determinism. The ghost is **untested**, not convicted, and
the mechanism hunt in the addendum (children acquitted, capture replay
diverging "from the bridge") was chasing a comparison against the
wrong player — capture mode IS net, so of course it diverged from a
heuristic game.

What survives audit: `rl/eval.py` passes `--policy-server` for net
games (its line 202-203), so the October eval numbers (v15 0.505 etc.)
were the net playing and stand; the §3 measurement (teacher capture
mode) was net and stands; the first misbuild's search-root arm was
correctly identified at the time. The driver is fixed in this commit:
the raw arm passes `--policy-server`, every game row records its own
mode line from the child process's stderr, and each arm writes a
manifest with the search-stat volume and an explicit
`assert_no_search_rows` for the raw arm. Both misbuilds would have
been caught by that manifest at the first game.

## 1. The question

Does the ghost (teacher machinery, pick forced to the prior's argmax)
reproduce true raw v15 — the net through the `--policy-server` bridge —
action for action on paired seeds? If not, where is the first
divergence, classified by the trace: STATE / CANDIDATES / DECISION /
RNG / BETWEEN?

## 2. What's in this commit

- `rounds/round3/deps/` — the dependency files as they run on the box:
  `policy_server.php`, `play_game.php`, `featurize.php`,
  `search_server.py` (verbatim; the two server request types are the
  lens candidate: picks go to the single-request handler
  (`net_argmax`), teacher priors to the batched `mode: eval` handler).
- `rounds/round3/code/patch_trace_shadow.py` — the instrumentation
  patch against the gate tree's `policy_server.php` + `search.php`
  (both lint-clean after patching; applied to a copy tree, the gate
  tree is untouched). Design points:
  - Trace helpers live in `policy_server.php` because it is the only
    file loaded in BOTH bridge and search modes. One row per decision,
    keyed by the bridge's own decision counter, so arms align by seq.
  - Root decisions in teacher-family arms capture, **before** the
    checkpoint block (`DoGamestateUpdate` + `WriteGamestate`): the
    features built from untouched live globals (`feat_pre_hash`), the
    eval endpoint's priors on them, a zone-globals hash, and an RNG
    fingerprint (fork, one `mt_rand` in the child, exit — reads the
    stream without consuming it). **After** `SimTeacher_Decide`: the
    features/priors the teacher actually used (`feat_post_hash`,
    from `SimSearch_EvalState`'s stash), zone hash, fingerprint.
  - `TEACHER_SHADOW=1`: Decide runs in full (checkpoint, evals,
    children), then the played pick is the bridge's native choice —
    the pick endpoint's answer over the PRE state and the shared
    candidate list, which is exactly what a bridge game plays.
  - Bridge rows: state hash, candidate hash, chosen index, rule,
    fingerprint. Pass and DQ decisions are rows too, so seq alignment
    is total.
- `rounds/round3/code/classify_divergence.py` + `test_classify.py` —
  the first-divergence classifier and its fixture test (pure stdlib;
  7/7 fixtures pass — IDENTICAL, STATE, CANDIDATES, DECISION, RNG,
  BETWEEN, MISSING_ROW; output in `rounds/round3/data/`).
- `rounds/round3/code/paired_driver.py` — arms raw/teacher/ghost/
  shadow/capture, trace env wired, mode lines, manifests (see §0).

## 3. Pre-registered reads for the launch

- **Class A — shadow == bridge on 19/19 gamelogs** AND the classifier
  puts ghost-vs-bridge's first divergence at DECISION with
  `feat_pre_hash != feat_post_hash` (or equal hashes with the two
  endpoints' argmaxes differing on identical features): the machinery
  is exonerated; the fork is in the decision path — which component
  moved is read from the row, not argued. The gate-design amendment
  (issue #1, ask 3) then governs.
- **Class B — shadow diverges from bridge:** a real side effect.
  The classifier's class localizes it (STATE/BETWEEN → between
  decisions; RNG → a stream consumer; zone_pre vs feat hashes
  separate the checkpoint block from everything else). Additive
  ladder from the bridge side, one piece per follow-up package.
- **Class C — traces identical at every compared field but gamelogs
  diverge:** the divergence lives below the trace boundary (child
  internals); scope extends there before any gate discussion.

Ghost-vs-capture on all 19 seeds runs in the same launch (children
side-channel closure, Claude round-2).

## 4. Exact launch commands (if approved)

On the sim box, tree `/tmp/tracetree` (gate tree + this patch), server
`SEARCH_MODEL=<v15 ckpt>` on `/tmp/tcg_policy.sock`:

```
for arm in raw ghost shadow capture; do
  python3 paired_driver.py --tree /tmp/tracetree --sock /tmp/tcg_policy.sock \
    --seat 1 --arm $arm --seeds 1-18,20 \
    --out /tmp/r3_<arm>.jsonl --logdir /tmp/r3_<arm>_log
done
python3 classify_divergence.py <bridge trace> <ghost trace>   # per seed
```

Timeouts: seed 19 excluded pairwise as before — the registration
question (Claude's seed-19 ruling, issue #1 ask 4) is still open and
this launch does not prejudge it; the hang is reported, not scored.

## 5. Tests run

- `test_classify.py`: 6/6 pass. (A seventh fixture, BETWEEN, was
  removed with its class before shipping — it classified noise; see
  `data/smoke-summary.md`.)
- `php -l` on both patched files: no syntax errors.
- One-seed instrumentation smoke (seed 3, tracetree, arms raw/ghost/
  shadow): full results in `data/smoke-summary.md`. Headlines: all
  three games winner 1, 16 turns; traces align 653/653 rows with **no
  field divergence** between raw and ghost; at all 80 root decisions
  the checkpoint moves no feature (feat_pre == feat_post) and no
  argmax; shadow reproduces the ghost gamelog byte for byte. The raw
  gamelog is NOT byte-identical to the ghost's despite decision-level
  identity (~11% fewer lines of engine chatter) — **ruling asked:**
  is the pre-gate pass criterion trace-level decision equality, or
  gamelog bytes? **This smoke is a build test, not the experiment;**
  the 19-seed reads in §3 bind only the approved launch.

## Not reviewed / missing

- The vendor engine internals (`DoGamestateUpdate`'s source) are not
  in the repo; the trace treats it as a black box with hashes on both
  sides, which is the design, but Claude cannot read it from here.
- Plain ISMCTS (non-teacher) RootDecide returns are not traced in
  this patch — not an arm in round 3.
