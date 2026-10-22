# Round 7 — stage 4 (i): the Gravy tree build record

**Parent:** c59a133dadc7d46bb6f7349b7f73bfa12fa027f5 (HEAD at writing; read via the git ref, equal to `origin/main`)
**Answers:** K2 of `rounds/round7/followup-k1-k5.md` (the tree built from `/tmp/otree`, abort-logging patch carried, hashes pinned), standing as accepted through the ba4e9c97 fix and the ff69da96 approval; cleared to proceed in `claude-reply-01250ac.md` §4(i); Joe's go 2026-10-22 15:55 EDT.
**Status: TREE BUILT AND LOAD-VERIFIED.** This record covers the tree only. No pre-gate games, no teacher games, no fleet games were played; the K3 pre-gate remains **HELD** pending the fleet-alignment registration's approval (claude-reply-01250ac §4).

---

## 1. Build method

The registered build (followup-k1-k5 §K2, replacing build-package §6) was executed verbatim:

```
cp -r /tmp/otree /tmp/gravytree
# verify inside /tmp/gravytree: rl/search_server.py, search.php, featurize.php (hashes, §2)
# then ONE substitution: probe_swap20.php line 17's bootstrap deck
#   decks/nats2026_ashlyn_fai_60.txt -> decks/nats2026_eriksen_gravy_60.txt
```

`/tmp/otree` itself was constructed as a fresh copy of the gate tree plus the §7 abort-logging patch (round-4 run record), so building from it carries the abort patch by construction; the §2 hashes prove it landed. `/tmp/otree` contains no symlinks, so the plain `cp -r` copies every file byte-for-byte. One path note: in this tree lineage the load-bearing `search.php` sits at the **tree root** (the `vendor/talishar/` subtree under it is the engine); the hash pins the file itself.

## 2. Hash table (full sha256, verified inside `/tmp/gravytree` after the copy)

| File | sha256 | Against |
|---|---|---|
| `search.php` | `8f6b35da23f4e5fc7f5fda2ede2d65ba330f9f3eb463e3377978ded1f5d7fa61` | registered (the O build WITH abort logging) ✓ |
| `rl/search_server.py` | `ab85fa1bcf19b41c7d48db642a2fd93d211e826b9f684594cefa5a1100f3c52c` | registered (patched server) ✓ |
| `featurize.php` | `f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92` | registered ✓ |
| `probe_swap20.php` (as copied) | `6993ece4f84bf2aea3540635c5b1cd8b2f0c9a787c0ed42cf426d4a3f8160243` | the O tree's file, Fai bootstrap deck at line 17 ✓ |
| `probe_swap20.php` (after the one substitution) | `400a921567b8739c8d88387e12ef75d2fb42587a53c1d5762b2db200a0bc5c2c` | line 17 now `decks/nats2026_eriksen_gravy_60.txt` (the file's only Fai-deck reference) |
| checkpoint `rl_out/gravy_ppo_gravybc3/ckpt_v10.pt` | `44f1e5d7320e32e7d95186a79155f5f97164e54592ce763d4652778d43495ca3` | the selected stage-3 checkpoint ✓ |
| deck `decks/nats2026_eriksen_gravy_60.txt` | `b8b41390c5420ab83cb80c7e20457cab948f62d113efb4900db52cf490bf11ed` | identical in the tree copy and the sim-tree copy ✓ |
| vocab `gravy_bc/card_vocab_gravy.json` | `361b1a871808465fdc6105aedeaf875761e42aa925b227429ace05c312f60f20` | the extended 380-entry vocab ✓ |

**Vocab consistency, checked directly:** `ckpt_v10.pt` is a v3 checkpoint (`arch: v3`) whose embedded `vocab` has exactly **380** entries and whose mapping is **identical** to `card_vocab_gravy.json` (including `nullrune_hood`). The server's `load_v3` reads the vocab from the checkpoint itself, so the tree serves the extended Gravy vocab by construction.

**PHP lint:** `php -l` clean on `search.php`, `featurize.php` and `probe_swap20.php` in the built tree (the gate-tree build's practice).

## 3. Diff against `/tmp/otree`

Full recursive diff (`diff -rq /tmp/otree /tmp/gravytree`), run after the copy and substitution, before any code executed from the tree:

```
Files /tmp/otree/probe_swap20.php and /tmp/gravytree/probe_swap20.php differ
```

**Exactly one file differs — the one registered substitution.** No other differences, no missing or extra files.

## 4. How the tree serves the selected arm (configuration pins)

Following the fleet-runner pattern (`run_o_fleet.sh`: cwd = tree root, one server per seat, readiness grepped from the server's own listening line):

- **Checkpoint:** environment `SEARCH_MODEL=/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt` (sha §2) on `rl/search_server.py` (sha §2). The v3 load reads the embedded 380-entry vocab from the checkpoint (verified identical to the extended vocab file, §2).
- **Socket / seat:** `TCG_POLICY_SOCK=<per-run socket>`, `TCG_LEARNER_SEAT=<seat>`; the pre-gate registration passes `/tmp/ggate_s<seat>.sock`.
- **Deck:** not a server setting — the fleet machinery takes its deck from `paired_driver.py --deck` (the Gravy deck, sha §2). The only in-tree deck reference changed is `probe_swap20.php` line 17's bootstrap deck (analysis copy only), now the Gravy deck.
- **Opponent net:** `TCG_OPP_MIX` left at its default (heuristic) for this load check; no opponent checkpoint is part of the tree build.

## 5. Construction verification (load check — not a measurement, no games)

The tree's search server was started **once** from `/tmp/gravytree`, exactly as configured in §4 (`SEARCH_MODEL=ckpt_v10.pt`, `TCG_POLICY_SOCK=/tmp/gravytree_check.sock`, `TCG_LEARNER_SEAT=1`, rl-env python, detached). Server pid **772885**. Its complete log is two lines:

```
search_server: search model loaded (/home/joe/tcg/tcg-sim/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt) on cuda
search_server: listening on /tmp/gravytree_check.sock (learner seat 1, opp heuristic)
```

The v10 weights loaded and the server reached listening. **Fallbacks:** the server's `_stats` counter starts at `fallbacks: 0` and increments only in the request-handling path; **no request was ever sent** (no client connected, zero evals), and the log contains no fallback, error or seat-mismatch line — fallbacks = 0 for this check by the code path, stated as such. No standalone health-check tool exists in the tree tooling (the driver's seat-ping is the instrument check, and it belongs to the held pre-gate), so the log-evidence form used for every prior tree's readiness is the check here.

The server was then stopped with `TERM` to its exact pid (772885) and verified gone; the socket and pid files were removed. The three pinned source files were **re-hashed after the launch** and are unchanged (probe_swap20.php at its substituted hash). Running the server created `__pycache__` bytecode under the tree at most — no source file changed.

## 6. SHM and /tmp state

| | Before | After |
|---|---|---|
| SHM segments (`ipcs -m` count) | 2,194 | 2,194 |
| /tmp free | 15G (20G tmpfs, 4.9G used) | 15G (5.1G used — the 203M tree itself) |

No SHM movement from the build or the load check; /tmp holds the new 203M tree comfortably (the stage-1 errno-28 lesson noted: the tree is a copy, its growth surface is game state under the held stages, not the build).

---

**The tree is built and load-verified; the K3 pre-gate remains HELD pending the fleet-alignment registration's approval.**
