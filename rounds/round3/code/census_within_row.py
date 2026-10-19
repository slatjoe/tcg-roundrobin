import json, glob, collections
arms = ["raw_s1","ghost_s1","raw_s2","ghost_s2","shadow_s1","capture_s1"]
tot = collections.Counter(); hits = collections.defaultdict(collections.Counter)
for arm in arms:
    for path in glob.glob(f"/tmp/r3_{arm}_log/trace/*.jsonl"):
        for line in open(path):
            try: r = json.loads(line)
            except Exception: continue
            if "feat_pre_hash" not in r: continue
            br = r.get("branch","?")
            key = (arm, br)
            tot[key] += 1
            if r.get("feat_pre_hash") != r.get("feat_post_hash"): hits[key]["feat"] += 1
            if r.get("zone_pre") != r.get("zone_post"): hits[key]["zone"] += 1
            if r.get("rng_pre") != r.get("rng_post"): hits[key]["rng"] += 1
branches = sorted({b for _,b in tot})
print(f"{'arm':11} {'branch':5} {'rows':>6} {'feat':>5} {'zone':>5} {'rng':>5}")
grand = collections.Counter(); grandtot = 0
for arm in arms:
    for br in branches:
        n = tot.get((arm,br),0)
        if not n: continue
        h = hits.get((arm,br), collections.Counter())
        print(f"{arm:11} {br:5} {n:6} {h.get('feat',0):5} {h.get('zone',0):5} {h.get('rng',0):5}")
        grandtot += n
        for k in ("feat","zone","rng"): grand[k] += h.get(k,0)
print("TOTAL teacher rows:", grandtot, "| feat hits:", grand["feat"], "| zone hits:", grand["zone"], "| rng hits:", grand["rng"])
bybranch = collections.Counter(); bybranch_tot = collections.Counter()
for (arm,br),n in tot.items():
    bybranch_tot[br] += n
    h = hits.get((arm,br), collections.Counter())
    for k in ("feat","zone","rng"): bybranch[(br,k)] += h.get(k,0)
for br in branches:
    print(f"branch {br}: rows={bybranch_tot[br]} feat={bybranch[(br,'feat')]} zone={bybranch[(br,'zone')]} rng={bybranch[(br,'rng')]}")
