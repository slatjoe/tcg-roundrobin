import json, glob
from collections import defaultdict

files = sorted(glob.glob('/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl'))
buckets = defaultdict(lambda: [0, 0])
for f in files:
    for line in open(f):
        r = json.loads(line)
        if r.get('contested') != 1 or 'means' not in r:
            continue
        means = r['means']
        if isinstance(means, dict):
            means = {int(k): v for k, v in means.items()}
            get = lambda i: means.get(i)
        else:
            get = lambda i: means[i] if i < len(means) else None
        pp = r.get('prior_pick')
        if pp is None or get(pp) is None:
            continue
        t = r.get('turn', 0)
        b = 'turn 0-4' if t <= 4 else ('turn 5-9' if t <= 9 else 'turn 10+')
        buckets[b][1] += 1
        if get(pp) in (-1.0, 1.0):
            buckets[b][0] += 1
for b in ('turn 0-4', 'turn 5-9', 'turn 10+'):
    u, n = buckets[b]
    print(f'{b}: prior-pick unanimous {u}/{n} = {100.0*u/max(n,1):.1f}%')
