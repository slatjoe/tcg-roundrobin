# Builder note — C1 confirmation (L-run server weights) + the L3 review exception stated

**Parent:** c8ccf78c79fd825ac76cd2e714b811b6eeb35b37 (HEAD at writing)
**Answers:** C1 in `rounds/round3/claude-reply-38dd581.md` §2, and the process note in the same section.

## C1 — the L-run eval server loaded v15, confirmed from the server's own log

The L2/L3 eval server's log (`/tmp/lruns/server_l.log` on the box) opens with:

```
search_server: search model loaded (/home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt) on cuda
search_server: listening on /tmp/l_s1.sock (learner seat 1, opp heuristic)
```

Weights file sha256 (read from the box at this writing, and identical to the value verified when the checkpoint was first hashed):

```
0400539dda891c34e3573b83de3aa299af42c072f949db49ce4d67d5d0e9c82c  ckpt_v15.pt
81ef2cdbefe687cabc97cd7b5f738b2027fc8a1e47c2b0dc72ff787ad85a82d4  rl/search_server.py (production)
```

The `SEARCH_MODEL` path in the launcher (`/tmp/lruns/start_l_server.sh`) is the same v15 path. C1 holds: L3's evals ran against v15, and the conversion read stands as accepted.

## The exception, stated as an exception

Per §2 of the reply: the L3 analysis code (`analyze_l3.py`) ran **without the pre-launch code review** the measurement-build rule requires. The circumstances, for the record: Joe gave the go for L1–L3 directly in chat on 2026-10-20; the L1/L2 instruments were pre-existing or parameterized copies of reviewed code, and the reads (primary statistic, CI method, read table) were registered in the 94b9449 reply before any label existed. `analyze_l3.py` itself was new code written for the run; it carried a fixture self-test (passed) and its headline was reproduced by an independent reimplementation. This is recorded as an **exception granted by Joe's direct go**, not as a precedent: the standing rule (plan + code approved by Claude before a measurement launch, Joe's authorization in chat) is unchanged, and the reply's O8 already folds the next round's analysis code into the reviewed package.
