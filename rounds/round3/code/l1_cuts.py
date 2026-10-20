import json, glob

files = sorted(glob.glob('/tmp/gate_r4/gate_c*_teacher_*_log/search_stats.jsonl'))
def getf(means):
    if isinstance(means, dict):
        m = {int(k): v for k, v in means.items()}
        return lambda i: m.get(i)
    return lambda i: means[i] if i < len(means) else None

over_rows = 0
over_prior_unan = 0
over_pick_unan = 0
over_any_unan = 0
se0 = []
for f in files:
    for line in open(f):
        r = json.loads(line)
        if r.get('overturn') != 1 or 'means' not in r:
            continue
        over_rows += 1
        get = getf(r['means'])
        pp, pk = r.get('prior_pick'), r.get('pick')
        pu = get(pp) in (-1.0, 1.0)
        tu = get(pk) in (-1.0, 1.0)
        if pu: over_prior_unan += 1
        if tu: over_pick_unan += 1
        if pu or tu: over_any_unan += 1
        if r.get('se_diff') == 0.0:
            se0.append((f.split('/')[-2], r.get('game'), r.get('turn'), r.get('branch'), r.get('mean_diff')))
print(f'overturn rows: {over_rows}')
print(f'prior pick unanimous (+-1): {over_prior_unan} ({100.0*over_prior_unan/over_rows:.2f}%)')
print(f'overturn pick unanimous (+-1): {over_pick_unan} ({100.0*over_pick_unan/over_rows:.2f}%)')
print(f'either pick unanimous: {over_any_unan} ({100.0*over_any_unan/over_rows:.2f}%)')
print(f'se_diff == 0 rows: {se0}')
