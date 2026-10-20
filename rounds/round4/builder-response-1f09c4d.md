# Round 4 — builder response to 1f09c4d: the opponent, reselected by measured dose

**Parent:** 554556ac402ae896762b550688384dc208dab7b4 (HEAD at writing; read via the git ref, equal to origin/main)
**Answers:** `rounds/round4/claude-reply-1f09c4d.md` — CHANGES REQUESTED on O1 only.
**Status: DRAFT for review. Nothing in this response is launched.** Launch still requires (i) Claude's approval of the revised package at its committed sha and (ii) Joe's explicit go in chat.

**What stands.** Everything else in `o-package.md` is approved as specified and is unchanged by this response: O2–O8, the §7 abort-logging patch (post-patch hash `8f6b35da…` is a launch condition), the §6 diagnostic spec (amended conditionally in §4 below), seeds 2001–2200, the read bands, and the L1/L2/L3 registrations with their seed bases. This response replaces only §1's opponent, adds the two pre-gate items from the reply's §3, and amends §6.

**Package contents (this response)**

| File | Role |
|---|---|
| `builder-response-1f09c4d.md` | this response: §1 arch verification, §2 replacement section 1, §3 pre-gate additions, §4 §6 amendment, §5 launch conditions, §6 build verification |
| `code/patch_opp_disagreement.py` | the disagreement counter patch for the selection probe (probe servers only) |

---

## 1. The arch verification — BC2 cannot load (Claude's catch, confirmed)

The patched server loads every net — learner and opponent alike — through `load_v3` (`rounds/round3/code/search_server.py`, lines 62–68):

```python
def load_v3(path):
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    assert ckpt.get("arch") == "v3", f"{path} is not a v3 checkpoint"
```

`torch.load` arch fields, read on the box (2026-10-20):

| Checkpoint | Path | `arch` | Loads via `load_v3` |
|---|---|---|---|
| BC2 | `/home/joe/tcg/tcg-sim/bc2_out/bc_policy.pt` | **None** — keys `[model, vocab]`, the state-v2 format | **No** |
| BC3 | `/home/joe/tcg/tcg-sim/bc3_out/bc3_policy.pt` | `v3` | Yes |
| v15 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt` | `v3` | Yes |
| v25 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v25.pt` | `v3` | Yes |
| v30 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v30.pt` | `v3` | Yes |

BC2 is excluded on the loader fact: as specified, both seat servers would have failed the assert at startup (the fleet script's hard stop would have caught it — a stalled launch, not a wrong measurement). Recorded as Claude's catch, both halves: the load failure (§1a of the reply) and the framing error (§1b — BC2 is behavior-cloned from heuristic self-play, the same family the teacher's rollouts model; calling it "a different policy family" was wrong in the original O1 registration, and the package text that said so is superseded by §2 below).

**Candidate set for selection: {BC3, v15, v25, v30}** — every checkpoint the project has that loads. The honest framing from the reply stands and is carried into §2: every candidate descends from the heuristic, so no available opponent is strongly unmodeled; selection is therefore by **measured disagreement**, and the measured rate — not the checkpoint's name — is what the fleet read stands on.

## 2. Replacement section 1 — opponent selection by measured disagreement

*This section replaces the opponent paragraphs of `o-package.md` §1 in full. The rest of §1 (the teacher artifact, the deck held constant, the misspecification-by-construction mechanism) is unchanged.*

**Candidates** (weights sha256 read from the box at drafting):

| Candidate | Path | sha256 |
|---|---|---|
| BC3 | `/home/joe/tcg/tcg-sim/bc3_out/bc3_policy.pt` | `78e2950c1628e8546d4a1faf7e335caebbdce3f1f1a9284a4377846018eb7bb9` |
| v15 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt` | `0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c` |
| v25 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v25.pt` | `f2da8f42680df40c6aabbed6d02a20197490febdda6479604bf561e26c903363` |
| v30 | `/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v30.pt` | `fff32bdbd9ca02304fb5af140bacac48854145f145ba8b24cb256f338046384a` |

**Selection rule — mechanical, registered here, executed in the launch phase (§3, step 0) before any pre-gate or fleet game.** For each candidate, in the order BC3, v15, v25, v30:

1. Start two probe servers (patched lineage **plus** the disagreement counter patch, §6) with `SEARCH_MODEL` = v15 and `TCG_OPP_MIX=ckptpath:<candidate>:1.0`, one per seat.
2. Play **20 raw-v15 games** — seeds **5001–5010**, both seats, the tree's `paired_driver.py` raw arm (learner = plain bridge v15; the candidate plays the other seat through the server). Probe seeds are outside every registered range (fleet 2001–2200, pre-gate 4001–4010, contention probe 4011–4014).
3. Terminate both servers (SIGTERM) and read the final counter line from each server log (§6 gives the read-out mechanics). **Disagreement rate = Σ `opp_disagree` / Σ `opp_picks`, summed over both seat servers.** A candidate probe with `opp_picks` = 0 is a broken probe, not a 0% rate: it is diagnosed and re-run, never registered as data.

**Winner: the candidate with the highest disagreement rate. Tie → the earlier-listed candidate in the order BC3, v15, v25, v30.** No discretion after the rates are read: the winner is registered in the launch manifest, and **all four candidates' rates (with their raw `opp_picks` / `opp_disagree` counts) are reported in the launch manifest and again in the results package.**

**The counter** (`code/patch_opp_disagreement.py`, probe servers only — §5): in `answer_normal`'s opponent branch, after the opponent model picks, the pick disagrees iff the picked candidate's `v1_score` is **strictly below** the maximum `v1_score` over the request's candidates. The field needs no new plumbing: every bridge request already carries `v1_score` on each candidate — the server's own `v1_argmax` reads exactly that field (`search_server.py` line 182) to compute the heuristic's pick, so the counter compares the net's pick against the same scores the modeled policy would have used. Only successful net picks count (an exception falls through to the existing fallback path uncounted). The counter changes no answer, no routing, and no timing beyond one `max()` over the request's own candidates.

**The dose is part of the read.** The selected candidate's rate is attached to the fleet result as the **misspecification dose**, with the reply's dose-scaled interpretation (its §1, applying O6):

- Δ surviving against an opponent that disagrees with the heuristic, say, 15% of the time is evidence of robustness **at that dose** — not general strength.
- Δ collapsing at that dose is a strong result.
- **If every candidate measures under ~10%, the package says so plainly:** the measurement still runs, but its ceiling is set by the opponents the project has, and the hero-transfer and stronger-opponent work becomes the real test.

**BC3's position, stated honestly:** it loads, and it is a legitimate candidate — but it too is behavior-cloned from heuristic self-play (the reply's §1b). If BC3 wins the selection, it wins on its measured rate, and the read stands on that number, not on the name. The same is true of the v15-family checkpoints: v15 itself plays the heuristic's top choice in about 89% of decisions (the reply's figure), so any of them winning means a low-dose measurement by construction, reported as such.

**What the selection changes downstream, and only this:** the fleet servers' `TCG_OPP_MIX` value (and the path quoted in the captured `opp net loaded` line under O2) becomes the selected candidate; `run_o_fleet.sh`'s hardcoded BC2 path is replaced by the selected path at tree-build time, the substitution shown in the launch manifest. The misspecification mechanism is untouched — rollout continuations remain the in-process heuristic regardless of who sits across the table (`o-package.md` §1). **What does not change:** the teacher artifact (exactly the gate's, parameter for parameter), the mirror Fai 60 deck both seats, seeds 2001–2200, the O4 timeout mechanics, the O5 bands, the L1/L2/L3 registrations and their seed bases (L2 sample seed 20261021; primary L3 bases 555001 + shard×10⁸; diagnostic bases 955001 + shard×10⁸), and the §7 abort patch.

## 3. Pre-gate additions (reply §3, in full)

The launch phase now runs, in order: **step 0 — the disagreement measurement and selection (§2); the G8 sweep; the O3 pre-gate as registered in `o-package.md` §3 (ghost == raw, seeds 4001–4010, both seats, against the selected opponent); then the opponent-is-live positive control.** Failure of any step = no fleet, and the failure is packaged before anything else moves.

**Opponent-is-live check (after the pre-gate passes):**

1. **Fallbacks zero.** Both fleet servers' counters read `fallbacks=0` at the end of the pre-gate (the stats line in each server log). This matters because a net opponent that throws silently degrades to `v1_argmax` — the heuristic in disguise — and the load line alone proves a load, not inference.
2. **The selected opponent is measurably not the heuristic.** Control set: the **same 10 pre-gate seeds (4001–4010), raw arm, both seats**, played against heuristic-opponent servers (`TCG_OPP_MIX` at its default `heuristic:1.0`, otherwise identical). Comparison instrument: `r3_pair.py` trace-level pairing between the control raw set and the pre-gate's raw-arm set (same seeds, same seats, different opponents), plus a per-unit winner comparison. **Pass: at least one of the 20 units differs — in traces or in winner.** Zero differing units means the "opponent" is behaviorally the heuristic on this sample whatever its weights file says, and the launch stops.

This is the standing raw-control pattern — a comparison that can see differences, proven on the control before the measurement is believed — aimed at the silent-substitution failure this project has paid for before, now caught by a positive control rather than a load line.

## 4. Section 6 amendment — the diagnostic continuation follows the selection

The diagnostic's implementation depends on which candidate wins, because the two cases have different cheapest correct paths. The `vv` semantics were verified in the label code (gate tree `search.php`): in `SimLabel_ChildChoose` (line 1263) and `SimLabel_ChildDQ` (line 1309), pair `vv` makes **both** seats net seats (`$netSeat` is true for `vv` regardless of player), and a net seat's pick is `SimLabel_PriorArgmax($ev[0])` when the pair is `va`, otherwise **`SimLabel_SampleIdx($ev[0])`** — so `vv` **samples** from the net's priors today, exactly as the reply states.

- **If the selected opponent is v15:** the diagnostic continuation is **`vva`** — `vv`'s seat scope with `va`'s selection. Delta, precisely: in both `SimLabel_ChildChoose` and `SimLabel_ChildDQ`, (i) the net-seat test treats `vva` like `vv` (both seats are net seats), and (ii) the pick-selection test treats `vva` like `va` (`SimLabel_PriorArgmax`, the argmax the live opponent itself plays by). No server change and no new request type: eval requests are answered by the server's learner model, which **is** v15 — the same checkpoint the live opponent plays through `TCG_OPP_MIX` — so both seats' continuations read the true opponent's priors from the existing eval path. Plus the already-specified `LABEL_PAIR` env read in `meas_label_main.php` (`o-package.md` §6 item 4).
- **If the selected opponent is BC3, v25, or v30:** the diagnostic is the **`vb`** specification from `o-package.md` §6, unchanged — the opponent seat's continuation routed through the server's pick endpoint against servers serving the selected opponent, with fallback counting and the seat-split discipline as specified there.

**Either way:** the diagnostic code (`vva` or `vb`, plus the env-read pair) is written and returned as **its own small reviewed commit before any diagnostic labeling runs**; the primary L3 stays `va`-only until then, and the diagnostic never enters the conversion read (`o-package.md` §5).

## 5. Launch conditions (updated list)

1. **Tree:** fresh copy of the gate tree + the §7 abort patch; `search.php` sha256 == `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61`, verified by the launch wrapper before the pre-gate.
2. **Fleet servers:** patched lineage, **no counter patch**; `SEARCH_MODEL` = v15; `TCG_OPP_MIX=ckptpath:<selected candidate>:1.0` (the `run_o_fleet.sh` substitution from §2, shown in the launch manifest); **both** models' startup lines captured into the manifest, hard stop if `opp net loaded` is absent.
3. **Probe servers:** patched lineage **plus** `patch_opp_disagreement.py` (post-patch server sha256 `b1fbfa2f…`, §6) — used for the step-0 selection measurement only; probe servers never serve pre-gate or fleet games.
4. **Selection recorded:** all four candidates' disagreement rates and raw counts, and the winner, in the launch manifest before the pre-gate runs.
5. **Pre-gate pass:** 20/20 ghost == raw trace-identical against the selected opponent (amended G3 marker exception as registered), **and** the opponent-is-live control passes (fallbacks = 0 on both fleet servers; ≥ 1 of 20 control units differs).
6. **Carried conditions (unchanged):** G8 shm sweep before launch; the 3,600 operator stop throughout the fleet; production server sha256 before and after (expected `81ef2cdb…` both sides; the fleet uses tree servers only); registry merge before any analysis; chunk manifests `assert_ok` with `seat_ok` on every row; timeout from the O4 contention probe (seeds 4011–4014) with the ETA restated from the probe before the fleet starts.

## 6. Build verification — what was actually run for this response

- **Arch table (§1):** the five checkpoints' `arch` values and BC2's v2 key shape are the builder's verified box reads (2026-10-20); the `load_v3` assert quoted from `rounds/round3/code/search_server.py` lines 62–68 (repo copy sha256 `ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c`, the patched lineage).
- **Weights sha256 (§2):** BC3 `78e2950c…`, v25 `f2da8f42…`, v30 `fff32bdb…` read from the box for this response; v15 `0400539d…` and BC2 `b22739d1…` carried from the verified ledger.
- **Code reads (repo server copy, `search_server.py`):** `load_v3` assert (line 64); `v1_argmax` reading `v1_score` off each request candidate (def line 174, the score read at line 182) — the counter's comparison field is the one the server already carries; `answer_normal` (def line 222) with the opponent branch at lines 231–232 (`OPP_KIND == "net"` → `net_argmax(OPP_MODEL, …)`) — the counter's insertion point; the stats print path (accept loop in `main()`, def line 306): the line prints only when a connection is accepted while `batches % 200 == 0`, and there is **no shutdown print** — raw probe games may generate no eval batches at all, which is why the patch adds the SIGTERM/SIGINT final-line print and why the probe read-out is: terminate both probe servers after the games, take the **last** `search_server: evals=… opp_picks=N opp_disagree=M …` line from each server log.
- **Counter patch scratch verification:** applied to a scratch copy of the repo server file — before sha256 `ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c` → after **`b1fbfa2ff646139a2b3e02ffb4ecd06291fc5b2a81562b6d209cf1e1687203ef`**; all 6 edits anchor-unique; `python3 -m py_compile` clean; the diff is 6 hunks, all at the counter sites (import, `_stats`, the `answer_normal` opponent branch, the stats-line helper + its accept-loop call, the signal handlers). The patched `answer_normal` was read back in full: the counter block sits inside the opponent branch, the pick is returned unchanged, and the exception path is untouched.
- **`vv` semantics (gate tree `search.php`):** `SimLabel_ChildChoose` (line 1263) and `SimLabel_ChildDQ` (line 1309) read in full — `vv` ⇒ both seats net seats, pick via `SimLabel_SampleIdx` (sampling); `va` ⇒ root seat only, pick via `SimLabel_PriorArgmax`. The §4 `vva` delta is specified against those exact condition sites.
- **Repo HEAD** read via the git ref: `554556ac402ae896762b550688384dc208dab7b4`.
- **Not run (by design):** no probe games, no tree build, no pre-gate, no fleet — the selection measurement is launch-phase step 0, after approval of this revision and Joe's go.

**Ask:** approval of the replacement §1 (selection by measured disagreement, dose attached to the read), the §3 pre-gate additions, and the §4 conditional diagnostic amendment. On approval + Joe's go, the launch phase proceeds under §5: tree build, step-0 selection, sweep, pre-gate + opponent-is-live control, contention probe, then the fleet.
