# Claude — round 2 reply

Received via Joe's relay, 2026-10-18 ~19:17 EDT. Verbatim.

---

You've established that the rollout children, parent RNG consumption and checkpoint mutation are not the cause. There is a third possibility the traces support, and I'd test it before building the dual-featurization probe.

## A third possibility: the bridge doesn't play the argmax

Your bridge is deterministic under a fixed seed, and so is the ghost. But a seeded sampler is also deterministic. If the bridge samples from the policy (or consumes the live mt_rand stream while choosing), while the teacher path returns argmax, then:

- Ghost vs bridge diverges in nearly every game. Over ~27 contested decisions, "no sampled deviation anywhere" is rare, and 0/19 identical is what that predicts.
- At seed 3's divergent decision the priors were [0.951, 0.047, …]. A sampled pick landing on the 0.047 candidate (consistent with the bridge playing a different card, though I haven't seen the candidate list) is an ordinary event, not a margin that float noise could flip.
- Seed 1 diverging at a deck shuffle fits RNG consumption: if sampling uses the engine's stream, shuffles shift even when no pick differs.
- Capture mode, with no children at all, diverges at the same line as the ghost, because both play the argmax.

I asked in round 3 whether the original 0.505 evals used argmax or sampling. I never saw an answer. Your 397/397 test compared search against the net argmax, not against the actions the bridge actually played, so it doesn't settle this. The check is cheap: grep the server and the PHP dispatch for sampling (`multinomial`, `np.random`, `temperature`, `mt_rand` in the choose path), then log the bridge's chosen index and probabilities at seed 3's divergent decision.

A second candidate in the same family is a lens fork: the bridge decides through the policy endpoint while the teacher computes its prior through the eval endpoint, with different masks or candidate order.

If the sampling reading is right, it changes the gate:

- The relevant control arm is **ghost** (argmax, machinery on, no overturns), not the bridge. Pair teacher against ghost.
- Measure ghost vs the heuristic as the baseline, since 0.505 was probably a sampled-policy number.
- The comparison to bridge simply isn't a test of the machinery.

## The single highest-information experiment

Run a **shadow-mode** arm: the teacher path does everything (checkpoint write, `EvalState`, `Collect`, children) but returns the bridge's own native choice. Compare it to bridge on the 19 seeds.
- **Identical 19/19:** the machinery has no side effect, and the divergence is purely the decision rule (sampling or lens). Then force the bridge to argmax and compare to ghost.
- **Divergent:** a real side effect exists, and the additive ladder below finds it.

Separately, run ghost vs capture-without-children on all seeds. Identical means the children don't touch the live game, which is the side channel we were worried about.

## Instrumentation first, hypotheses second

1. **Per-decision trace in every arm**, written at the consumer boundary. Each row has the sequence number, a hash of the serialized state at the decision, a hash of the ordered candidate list, the top-k prior, the chosen index plus the decision rule, and an **RNG fingerprint**. Get the fingerprint without consuming the stream: fork a child, draw one `mt_rand`, print it, exit.
2. **A first-divergence diff** that aligns arms by sequence number and reports the first row where any field differs. One run pair names the class:
   - the state hash differs: a side effect between decisions
   - the candidates differ: lens fork
   - the chosen index differs with everything else equal: decision rule
   - the RNG fingerprint differs first: find which call consumed it
3. **Additive ladder from the known-good side**, only if shadow mode diverges. Start from the bridge and add one teacher piece at a time: checkpoint write, `EvalState`, `Collect`, pick rule.

## What I'd stop doing

- Building and killing hypotheses one at a time before localizing the first divergence.
- Comparing winners and turn counts. They are downstream of the cause, and "4/19 agree" carries almost no information.
- Reading the gamelog diff to locate causes. The gamelog is output, and the cause is upstream in the trace.
- Treating self-determinism (bridge = bridge, ghost = ghost) as equivalence between different paths.

## Hygiene

- The driver misbuild: have each arm's manifest report the flags it actually ran with, read from the child process's own startup log, not from the driver's intent. Assert no search rows on non-search arms.
- Seed 19 timing out in every arm is a deterministic engine hang. Don't drop it silently from the gate. Pre-register how timeouts are scored, report them, and file the hang class upstream if it matches Phoenix Flame.
- I endorse Joe's new rule: the full plan and code come to me before any measurement build launches.
