# The cheap check, run — sampling is not in the code

Muse's prescribed first check (round-2 reply): grep the server and the PHP
dispatch for sampling in the choose path. Run 2026-10-18, same evening,
against primary sources on the sim box.

## Server (`rl/search_server.py`, gate tree and original tree)

- No `multinomial`, no `np.random`, no `temperature`, no `random.` calls in
  either copy.
- The pick function is `net_argmax(model, vocab, state, cands)` →
  `return int(logits[0].argmax())`.
- The eval endpoint (teacher/search path) computes
  `priors = torch.softmax(logits[:k])` — the teacher's argmax over those
  priors is the argmax of the same logits.

## Bridge (`policy_server.php`, `play_game.php`)

- No `mt_rand` / `array_rand` / `shuffle` in the choose path. The bridge
  routes candidate-choice decisions to the server, which returns argmax;
  the in-process fallback is the v1 heuristic's own deterministic choice.

## Verdict

- **The sampling form of the third hypothesis is dead.** The bridge plays
  argmax end to end in every code path read.
- **The round-3 question is answered: the original 0.505 evals used argmax**
  (`net_argmax` is the eval path's pick function). 0.505 is not a
  sampled-policy number.
- **The lens-fork variant survives and leads**: teacher priors come from the
  eval endpoint (softmax over the PHP-supplied candidate list); the bridge's
  pick comes from the pick endpoint (server-side argmax). Different masks,
  candidate orders, or featurization between the endpoints would produce
  exactly what we see, including the 0.951-margin divergence.

Caveat, per the standing lesson: a code read is not a trace. The
per-decision trace + shadow-mode build (Claude's design) goes to Claude as a
code package for approval before launch, and its first-divergence classifier
settles the fork empirically.
