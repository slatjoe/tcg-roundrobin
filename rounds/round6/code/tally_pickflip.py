#!/usr/bin/env python3
"""Round-6 pick-flip tally (claude-reply-f7e4534 sec.3).

Read-only over the pick-flip probe logs (one JSON row per ARS
Choose call; see patch_pickflip_probe.py). Computes:

  rows                 every logged ARS featurization
  pick_rows            rows where a real pick existed (gate pass,
                       >= 1 candidate); no-pick rows carry null
                       eval fields and enter no rate
  eval_error           pick rows whose dual eval failed (flip is
                       null); machinery trouble, reported, and
                       excluded from the flip-rate denominator
  agreeing             rows whose store and view deck counts agree
  control_flips        agreeing pick rows with flip == true. The
                       two states are identical by construction,
                       so this must be 0; any nonzero value is a
                       machinery defect, not a rate.
  control_prior_mismatch
                       agreeing pick rows whose two prior vectors
                       differ at all (a stronger machinery check
                       than the argmax control)
  disagreeing          rows whose deck counts disagree
  flips                disagreeing pick rows (flip not null) with
                       flip == true
  flip_rate            flips / disagreeing pick rows with a flip
                       value, with a 95% Wilson score interval
  prior_shift_chosen   |cur_priors[cur_argmax] - var_priors[cur_argmax]|
                       over disagreeing pick rows: n, median, p90
                       (nearest-rank), max. The "chosen candidate"
                       is the current state's argmax - what v15
                       picks under its current inputs (for the
                       learner seat, the server's played pick: the
                       pick path takes the argmax of the same
                       logits the eval endpoint softmaxes).

Usage: tally_pickflip.py [flip_log.jsonl ...]
(default: /tmp/pickflip/flip_s1.jsonl /tmp/pickflip/flip_s2.jsonl)

Addition (results-stage, claude-reply-1a3267f sec.3 item 1,
disclosed in builder-response-70735fc): after the pooled block
above (unchanged - the fixture's expected_tally.txt still pins
it), the same quantities are reported BY PLAYER: control flips
and prior mismatches, disagreeing pick-bearing rows, flips and
flip rate with Wilson interval, and the prior-shift summary.
The registered read stays pooled.
"""
import json
import math
import sys

paths = sys.argv[1:] or [
    "/tmp/pickflip/flip_s1.jsonl",
    "/tmp/pickflip/flip_s2.jsonl",
]

rows = []
for path in paths:
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def pct(x):
    return f"{100 * x:.3f}%"


pick_rows = [r for r in rows if r.get("pick")]
no_pick = [r for r in rows if not r.get("pick")]
eval_error = [r for r in pick_rows if r.get("eval_error")]
agreeing = [r for r in rows if r.get("agree")]
disagreeing = [r for r in rows if not r.get("agree")]
agreeing_pick = [r for r in agreeing if r.get("pick")]
disagreeing_pick = [r for r in disagreeing
                    if r.get("pick") and r.get("flip") is not None]

control_flips = sum(1 for r in agreeing_pick if r.get("flip") is True)
control_prior_mismatch = sum(
    1 for r in agreeing_pick
    if r.get("cur_priors") is not None and r.get("cur_priors") != r.get("var_priors"))
flips = sum(1 for r in disagreeing_pick if r.get("flip") is True)

shifts = []
for r in disagreeing_pick:
    cp, vp = r.get("cur_priors"), r.get("var_priors")
    ca = r.get("cur_argmax")
    if cp is not None and vp is not None and ca is not None and 0 <= ca < len(cp):
        shifts.append(abs(cp[ca] - vp[ca]))
shifts.sort()

def nearest_rank(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    idx = max(1, math.ceil(q * len(sorted_vals)))
    return sorted_vals[idx - 1]

median = nearest_rank(shifts, 0.5)
p90 = nearest_rank(shifts, 0.9)
mx = shifts[-1] if shifts else 0.0

lo, hi = wilson(flips, len(disagreeing_pick))

print("tally_pickflip - round 6 pick-flip tally")
print(f"rows: {len(rows)}")
print(f"pick_rows: {len(pick_rows)} (no_pick: {len(no_pick)}, eval_error: {len(eval_error)})")
print(f"agreeing: {len(agreeing)} (pick-bearing: {len(agreeing_pick)})")
print(f"  control_flips: {control_flips}")
print(f"  control_prior_mismatch: {control_prior_mismatch}")
print(f"disagreeing: {len(disagreeing)} (pick-bearing: {len(disagreeing_pick)})")
print(f"  flips: {flips}")
print(f"  flip_rate: {flips}/{len(disagreeing_pick)} = {pct(flips / len(disagreeing_pick) if disagreeing_pick else 0)} Wilson95 [{pct(lo)}, {pct(hi)}]")
print(f"prior_shift_chosen (disagreeing pick-bearing rows): n={len(shifts)} median={median:.6f} p90={p90:.6f} max={mx:.6f}")

# --- by player (claude-reply-1a3267f sec.3 addition 1) ---
print("by player (claude-reply-1a3267f sec.3 addition 1):")
for p in sorted({r.get("player") for r in rows}):
    prows = [r for r in rows if r.get("player") == p]
    ppick = [r for r in prows if r.get("pick")]
    perr = [r for r in ppick if r.get("eval_error")]
    pagr = [r for r in prows if r.get("agree") and r.get("pick")]
    pdis = [r for r in prows
            if not r.get("agree") and r.get("pick") and r.get("flip") is not None]
    pcf = sum(1 for r in pagr if r.get("flip") is True)
    pcm = sum(1 for r in pagr
              if r.get("cur_priors") is not None
              and r.get("cur_priors") != r.get("var_priors"))
    pflips = sum(1 for r in pdis if r.get("flip") is True)
    pshifts = []
    for r in pdis:
        cp, vp = r.get("cur_priors"), r.get("var_priors")
        ca = r.get("cur_argmax")
        if cp is not None and vp is not None and ca is not None and 0 <= ca < len(cp):
            pshifts.append(abs(cp[ca] - vp[ca]))
    pshifts.sort()
    plo, phi = wilson(pflips, len(pdis))
    print(f"player {p}: rows: {len(prows)} (pick-bearing: {len(ppick)}, eval_error: {len(perr)})")
    print(f"  agreeing pick-bearing: {len(pagr)} control_flips: {pcf} control_prior_mismatch: {pcm}")
    print(f"  disagreeing pick-bearing: {len(pdis)} flips: {pflips}")
    print(f"  flip_rate: {pflips}/{len(pdis)} = {pct(pflips / len(pdis) if pdis else 0)} Wilson95 [{pct(plo)}, {pct(phi)}]")
    print(f"  prior_shift_chosen: n={len(pshifts)} median={nearest_rank(pshifts, 0.5):.6f} p90={nearest_rank(pshifts, 0.9):.6f} max={pshifts[-1] if pshifts else 0.0:.6f}")
