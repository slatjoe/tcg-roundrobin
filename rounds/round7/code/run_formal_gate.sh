#!/bin/bash
# run_formal_gate.sh - round-7 stage 3: ONE C4 formal gate for a PPO
# checkpoint, on the re-specified instrument (stage3-alignment-final.md
# sec.4, incorporating claude-reply-b876b3f sec.4).
#
# Usage: run_formal_gate.sh <checkpoint.pt> [gate_tag]
#
# Form: 400 seat-balanced games, candidate vs heuristic, Gravy mirror,
# run as EIGHT rl/eval.py invocations of 50 games (deck-half a x4,
# deck-half b x4), each in its own fresh workdir with its own socket.
# (The re-gate's two invocations of 200 truncated at eval.py's internal
# batch budget, games*3+180 s: 780 s against ~840 s needed. A 50-game
# invocation has a 330 s budget against ~210 s needed at 4.2 s/game.)
# Each invocation: --max-turns 87 (parameter 87, trigger 62) and
# TCG_MAX_DECISIONS=3000 exported here and inherited by eval.py's
# subprocesses. eval.py itself is NOT modified.
#
# The pooling tail at the bottom reads the eight summaries and prints
# the gate read. If any invocation's summary carries the timeout error,
# the PARTIAL-COMPLETION RULE applies (stage3-alignment-final.md
# sec.4.3): the printed PASS/FAIL line must NOT be read directly; the
# tail prints the worst-case bounds the rule is executed from.
set -u
CKPT=${1:?usage: run_formal_gate.sh <checkpoint.pt> [gate_tag]}
TAG=${2:-$(basename "$CKPT" .pt | tr -cd 'A-Za-z0-9_.-')}
export TCG_MAX_DECISIONS=3000
cd /home/joe/tcg/tcg-sim
PY=/home/joe/tcg/rl-env/bin/python
G60=/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt
BASE=gravy_bc/formal_gate/$TAG
mkdir -p "$BASE"
echo "=== formal gate $TAG ckpt=$CKPT $(date) ==="
LOGS=""
for half in a b; do
  for i in 1 2 3 4; do
    WD=$BASE/${half}${i}
    LOG=$BASE/${half}${i}.log
    echo "=== invocation ${half}${i} (learner deck $half, 50 games) $(date) ==="
    start=$(date +%s)
    $PY rl/eval.py --ckpt "$CKPT" --opp heuristic \
      --games 50 --deck-a $G60 --deck-b $G60 --learner-deck $half \
      --workdir "$WD" --sock /tmp/fgate_${TAG}_${half}${i}.sock \
      --sim-dir /home/joe/tcg/tcg-sim --max-turns 87 > "$LOG" 2>&1
    echo "invocation ${half}${i} exit=$? wall=$(( $(date +%s) - start ))s log=$LOG"
    LOGS="$LOGS $LOG"
  done
done
echo "=== pooling the eight summaries $(date) ==="
$PY - $LOGS <<'PYEOF'
import json, math, sys

# C4 pass rule (stage3-alignment-final.md sec.4.2), R* = the re-gate's
# pooled draw-score (claude-reply-b876b3f sec.1.4): pass iff point
# estimate >= R* AND interval lower bound > R* - 0.05. R* is recorded
# as 0.51213; the comparisons below use its exact counted value,
# 190/371, so a candidate matching the anchor's counted performance
# exactly is not failed by the rounding of the recorded constant.
R_STAR = 190 / 371              # = 0.51212938..., recorded as 0.51213
LOWER_MARGIN = R_STAR - 0.05    # = 0.46212938..., recorded as 0.46213
STALL_BOUND = 0.2285            # mirror H' Wilson upper; DIAGNOSTIC only
Z = 1.96

def wilson(k, n):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (c - h, c + h)

rows = []
for path in sys.argv[1:]:
    summ = None
    for line in open(path):
        line = line.strip()
        if '"capped_games"' in line and '"games"' in line:
            try:
                s = json.loads(line)
            except Exception:
                continue
            if 'games' in s and 'wins' in s:
                summ = s
    if summ is None:
        rows.append({'path': path, 'games': 0, 'wins': 0, 'capped': 0,
                     'reasons': {}, 'error': 'NO_SUMMARY'})
    else:
        rows.append({'path': path, 'games': int(summ['games']),
                     'wins': int(summ['wins']),
                     'capped': int(summ.get('capped_games', 0)),
                     'reasons': summ.get('cap_reasons', {}),
                     'error': summ.get('error')})

W = sum(r['wins'] for r in rows)
C = sum(r['capped'] for r in rows)
N = sum(r['games'] for r in rows)
L = N - W - C
reasons = {}
for r in rows:
    for k, v in r['reasons'].items():
        reasons[k] = reasons.get(k, 0) + v
timed_out = [r for r in rows if r['error']]
print('per-invocation counted (timeout flag set if the summary '
      'carries the batch-timeout error):')
for r in rows:
    print(f"  {r['path']}: games={r['games']} wins={r['wins']} "
          f"capped={r['capped']} "
          f"{'TIMEOUT' if r['error'] else 'ok'}")
print(f'pooled: counted={N} candidate_wins={W} heuristic_wins={L} '
      f'capped={C} cap_reasons={reasons}')

# Draw-score: the mean of per-game scores in {1, 0, 0.5} (win / loss /
# capped-draw). Its 95% interval is the NORMAL APPROXIMATION on that
# mean with the empirical score variance:
#   var = (W(1-m)^2 + L*m^2 + C(0.5-m)^2) / N ;  CI = m +/- 1.96*sqrt(var/N)
# Wilson is used ONLY for the capped share (a true proportion).
m = (W + 0.5 * C) / N if N else 0.0
var = (W * (1 - m) ** 2 + L * m ** 2 + C * (0.5 - m) ** 2) / N if N else 0.0
se = math.sqrt(var / N) if N else 0.0
lo, hi = m - Z * se, m + Z * se
nonwin = W / N if N else 0.0
cap_share = C / N if N else 0.0
cap_lo, cap_hi = wilson(C, N)
print(f'draw-score = {m:.5f}  [95% CI {lo:.5f}, {hi:.5f}] '
      f'(normal approx on score mean, var={var:.5f})')
print(f'non-win score (co-reported) = {nonwin:.5f}')
print(f'capped share = {cap_share:.5f}  [Wilson95 {cap_lo:.5f}, '
      f'{cap_hi:.5f}]')
print(f'PASS TEST vs R*={R_STAR:.5f}: estimate {m:.5f} >= {R_STAR:.5f} '
      f'-> {m >= R_STAR}; lower bound {lo:.5f} > {LOWER_MARGIN:.5f} -> '
      f'{lo > LOWER_MARGIN}; GATE = '
      f'{"PASS" if (m >= R_STAR and lo > LOWER_MARGIN) else "FAIL"}')
print(f'STALL DIAGNOSTIC (report-only, never a gate condition): '
      f'capped-share Wilson lower {cap_lo:.5f} vs {STALL_BOUND} -> '
      f'{"FLAGGED" if cap_lo > STALL_BOUND else "not flagged"}')
if timed_out:
    U = 400 - N
    print(f'PARTIAL COMPLETION: {len(timed_out)} invocation(s) '
          f'truncated; counted {N} of 400; uncounted {U} (incl. '
          f'{len(timed_out)} in flight, one per truncated invocation).')
    print('DO NOT read the PASS/FAIL line above directly. '
          'Partial-completion rule (sec.4.3): worst-case the '
          'in-flight games; read pass/fail only if it holds under '
          'EVERY outcome of the uncounted games; otherwise top up '
          'with fresh-batch games to 400 counted and record the '
          'top-up; register every id, counted or in flight, either '
          'way. Worst-case bounds over all completions:')
    print(f'  draw-score if all {U} uncounted were heuristic wins: '
          f'{(W + 0.5 * C) / 400:.5f}')
    print(f'  draw-score if all {U} uncounted were capped draws: '
          f'{(W + 0.5 * (C + U)) / 400:.5f}')
    print(f'  draw-score if all {U} uncounted were candidate wins: '
          f'{(W + U + 0.5 * C) / 400:.5f}')
    wl, _ = wilson(C + U, 400)
    print(f'  capped share if all {U} uncounted were capped: '
          f'{(C + U) / 400:.5f} (Wilson lower {wl:.5f})')
PYEOF
echo "=== formal gate $TAG complete $(date) ==="
