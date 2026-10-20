import json, glob
from collections import Counter

files = sorted(glob.glob('/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl'))
contested = 0
u1 = 0            # all candidates unanimous (every mean in {-1,0,1})
u2 = 0            # prior pick unanimous (mean in {-1,1})
over = 0
se_zero = 0
se_vals = []
any_cand_unanimous = 0
for f in files:
    for line in open(f):
        r = json.loads(line)
        if r.get('contested') != 1 or 'means' not in r:
            continue
        contested += 1
        means = r['means']
        if isinstance(means, dict):
            means = {int(k): v for k, v in means.items()}
            get = lambda i: means.get(i)
            n_means = (max(means) + 1) if means else 0
        else:
            get = lambda i: means[i] if i < len(means) else None
            n_means = len(means)
        sel = r.get('selected') or list(range(n_means))
        sel_means = [get(i) for i in sel if get(i) is not None]
        if all(m in (-1.0, 0.0, 1.0) for m in sel_means):
            u1 += 1
        if any(m in (-1.0, 1.0) for m in sel_means):
            any_cand_unanimous += 1
        pp = r.get('prior_pick')
        if pp is not None and get(pp) in (-1.0, 1.0):
            u2 += 1
        if r.get('overturn') == 1:
            over += 1
            se = r.get('se_diff')
            if se is not None:
                se_vals.append(se)
                if se == 0.0:
                    se_zero += 1
se_vals.sort()
n = len(se_vals)
print(f'contested rows: {contested}')
print(f'U1 all-candidates-unanimous: {u1} ({100.0*u1/contested:.2f}%)')
print(f'any-candidate-unanimous: {any_cand_unanimous} ({100.0*any_cand_unanimous/contested:.2f}%)')
print(f'U2 prior-pick-unanimous: {u2} ({100.0*u2/contested:.2f}%)')
print(f'overturn rows: {over}; se_diff present: {n}')
print(f'L1 paired-comparison unanimity (se_diff == 0): {se_zero} ({100.0*se_zero/max(n,1):.2f}%)')
if n:
    print(f'se_diff min={se_vals[0]:.4f} p25={se_vals[n//4]:.4f} median={se_vals[n//2]:.4f} p75={se_vals[3*n//4]:.4f} max={se_vals[-1]:.4f}')
