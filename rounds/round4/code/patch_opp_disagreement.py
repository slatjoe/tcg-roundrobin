#!/usr/bin/env python3
"""patch_opp_disagreement.py - diagnostic disagreement counter for the
patched search_server.py (round-3 lineage; repo copy
rounds/round3/code/search_server.py sha256 ab85fa1b...).

Purpose (round-4 O-package, launch-phase step 0): measure each
candidate opponent's disagreement rate against v1_argmax so the
opponent can be selected mechanically by measured misspecification
dose (claude-reply-1f09c4d sec.1). The patched server built with this
patch serves the SELECTION PROBE ONLY - never the fleet or the
pre-gate (builder-response-1f09c4d sec.5).

Behavior: in answer_normal's opponent branch (the non-learner-seat
route, taken only when OPP_KIND == "net"), after the opponent model
picks, compare the picked candidate's v1_score (carried on every
request candidate; the server's own v1_argmax reads the same field)
against the maximum v1_score over the request's candidates:
  opp_picks    += 1                       (successful net picks only)
  opp_disagree += 1  iff v1_score[pick] < max v1_score   (strict)
Both counters join the existing stats line (evals=... batches=...
normal=... fallbacks=... seat_mismatch=... up=...). The stock server
prints that line only opportunistically from its accept loop (when
batches % 200 == 0) and has no shutdown print; raw probe games may
generate no eval batches at all, so the patch also registers a
SIGTERM/SIGINT handler that prints the same line once before exit -
the probe harness terminates the servers after the games and reads
the final line from each server log.

The counter changes no answer, no routing, and no timing: the added
work is one max() over the request's own candidates, on the opponent
branch only.

Usage: patch_opp_disagreement.py <path-to-search_server.py>
Applies in place; refuses if already applied. Anchor-asserted
(count == 1 per anchor).
"""
import sys

EDITS = []

# 1. import signal (for the final-line handler).
EDITS.append((
    "import queue\nimport socket",
    "import queue\nimport signal\nimport socket",
))

# 2. counters join _stats.
EDITS.append((
    '_stats = {"evals": 0, "batches": 0, "normal": 0, "fallbacks": 0,\n'
    '          "seat_mismatch": 0}',
    '_stats = {"evals": 0, "batches": 0, "normal": 0, "fallbacks": 0,\n'
    '          "seat_mismatch": 0, "opp_picks": 0, "opp_disagree": 0}',
))

# 3. the disagreement counter in answer_normal's opponent branch.
EDITS.append((
    '        if OPP_KIND == "net":\n'
    '            return net_argmax(OPP_MODEL, OPP_VOCAB, req["state"], cands)',
    '        if OPP_KIND == "net":\n'
    '            pick = net_argmax(OPP_MODEL, OPP_VOCAB, req["state"],\n'
    '                              cands)\n'
    '            _stats["opp_picks"] += 1\n'
    '            if 0 <= pick < len(cands):\n'
    '                top = max(float(c.get("v1_score", 0.0))\n'
    '                          for c in cands)\n'
    '                if float(cands[pick].get("v1_score", 0.0)) < top:\n'
    '                    _stats["opp_disagree"] += 1\n'
    '            return pick',
))

# 4a. factor the stats line into a helper and extend it with the two
# counters; the accept loop calls the helper.
EDITS.append((
    '        if _stats["batches"] % 200 == 0 and _stats["batches"]:\n'
    '            dt = time.time() - t0\n'
    '            print(f"search_server: evals={_stats[\'evals\']} "\n'
    '                  f"batches={_stats[\'batches\']} normal={_stats[\'normal\']} "\n'
    '                  f"fallbacks={_stats[\'fallbacks\']} "\n'
    '                  f"seat_mismatch={_stats[\'seat_mismatch\']} up={dt:.0f}s",\n'
    '                  flush=True)',
    '        if _stats["batches"] % 200 == 0 and _stats["batches"]:\n'
    '            _print_stats(t0)',
))

# 4b. the helper + the SIGTERM/SIGINT final-line handlers, at main().
EDITS.append((
    'def main():\n'
    '    try:\n'
    '        os.unlink(SOCK_PATH)',
    'def _print_stats(t0):\n'
    '    dt = time.time() - t0\n'
    '    print(f"search_server: evals={_stats[\'evals\']} "\n'
    '          f"batches={_stats[\'batches\']} normal={_stats[\'normal\']} "\n'
    '          f"fallbacks={_stats[\'fallbacks\']} "\n'
    '          f"seat_mismatch={_stats[\'seat_mismatch\']} "\n'
    '          f"opp_picks={_stats[\'opp_picks\']} "\n'
    '          f"opp_disagree={_stats[\'opp_disagree\']} up={dt:.0f}s",\n'
    '          flush=True)\n'
    '\n'
    '\n'
    'def main():\n'
    '    try:\n'
    '        os.unlink(SOCK_PATH)',
))
EDITS.append((
    '    t0 = time.time()\n'
    '    while True:',
    '    t0 = time.time()\n'
    '\n'
    '    def _term(signum, frame):\n'
    '        _print_stats(t0)\n'
    '        os._exit(0)\n'
    '\n'
    '    signal.signal(signal.SIGTERM, _term)\n'
    '    signal.signal(signal.SIGINT, _term)\n'
    '    while True:',
))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    src = open(path).read()
    if "opp_disagree" in src:
        print("REFUSED: counters already present (already applied?)")
        return 1
    for i, (old, new) in enumerate(EDITS, 1):
        n = src.count(old)
        if n != 1:
            print(f"ANCHOR FAIL edit {i}: count={n} (expected 1)")
            return 1
        src = src.replace(old, new)
    open(path, "w").write(src)
    print(f"applied {len(EDITS)} edits to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
