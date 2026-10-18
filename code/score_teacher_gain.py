#!/usr/bin/env python3
"""Score Claude's pre-registered teacher-gain measurement.

Labels: every teacher-contested decision from plain v15 games, the
teacher's selected candidate set, k=25 shared determinized worlds,
pair va. For each decision, split-half pick/score in both directions:
  - ungated gain: argmax on the pick half, scored on the other half,
    minus the prior pick scored on the same half (paired worlds).
  - gated gain (k=25 only): the teacher's actual rule applied inside
    the pick half - overturn to the best challenger only when the
    paired margin clears 1.5 paired SE (n >= 10 shared pick worlds).
Headline statistic: per-GAME sum of per-decision gains (the
performance-difference-lemma quantity along the harvested trajectory),
averaged over games, cluster bootstrap by game. H(k) = mean ungated
per-decision gain using the first k worlds. All values on the +-1
outcome scale; win probability = value / 2.

Usage: score_teacher_gain.py <jobs.jsonl> <labels.jsonl> [out.json]
"""
import json, sys, random
from collections import defaultdict

def load(jobs_path, labels_path):
    jobs = {}
    for l in open(jobs_path):
        j = json.loads(l)
        jobs[j["snap"]] = j
    worlds = defaultdict(lambda: defaultdict(dict))  # snap -> cand -> w -> outcome
    for l in open(labels_path):
        r = json.loads(l)
        res = r.get("result") or {}
        if res.get("finished") and res.get("outcome") is not None:
            worlds[r["snap"]][int(r["cand"])][int(r["world"])] = float(res["outcome"])
    return jobs, worlds

def half_gain(pick_worlds, score_worlds, cands, prior, gated):
    """pick_worlds/score_worlds: cand -> {w: outcome}. Returns paired
    gain of the chosen pick over the prior on score worlds, or None."""
    def mean_on(c, ws):
        vals = [ws[c][w] for w in ws.get(c, {})]
        return (sum(vals) / len(vals)) if vals else None
    means = {c: mean_on(c, pick_worlds) for c in cands}
    if any(v is None for v in means.values()):
        return None
    pick = prior
    if gated:
        best = max((c for c in cands if c != prior),
                   key=lambda c: means[c], default=None)
        if best is not None and means[best] > means[prior]:
            shared = sorted(set(pick_worlds.get(best, {}))
                            & set(pick_worlds.get(prior, {})))
            if len(shared) >= 10:
                ds = [pick_worlds[best][w] - pick_worlds[prior][w]
                      for w in shared]
                m = sum(ds) / len(ds)
                if len(ds) > 1:
                    var = sum((d - m) ** 2 for d in ds) / (len(ds) - 1)
                    se = (var ** 0.5) / (len(ds) ** 0.5)
                else:
                    se = 0.0
                if m > 1.5 * se:
                    pick = best
    else:
        pick = max(cands, key=lambda c: means[c])
    shared = sorted(set(score_worlds.get(pick, {}))
                    & set(score_worlds.get(prior, {})))
    if len(shared) < 4:
        return None
    ds = [score_worlds[pick][w] - score_worlds[prior][w] for w in shared]
    return sum(ds) / len(ds)

def decision_gains(cand_worlds, selected, prior, k, gated):
    ws_sorted = sorted(set().union(*[set(cand_worlds.get(c, {}))
                                     for c in selected]))[:k]
    if len(ws_sorted) < k:
        return None
    half = len(ws_sorted) // 2
    A, B = ws_sorted[:half], ws_sorted[half:]
    def subset(ws):
        return {c: {w: cand_worlds[c][w] for w in ws
                    if w in cand_worlds.get(c, {})} for c in selected}
    g1 = half_gain(subset(A), subset(B), selected, prior, gated)
    g2 = half_gain(subset(B), subset(A), selected, prior, gated)
    vals = [g for g in (g1, g2) if g is not None]
    return (sum(vals) / len(vals)) if vals else None

def main():
    jobs, worlds = load(sys.argv[1], sys.argv[2])
    out_path = sys.argv[3] if len(sys.argv) > 3 else None
    per_game = defaultdict(lambda: {"ungated25": [], "gated25": []})
    h_acc = {10: [], 20: [], 25: []}
    n_usable = 0
    for snap, j in jobs.items():
        cw = worlds.get(snap)
        if not cw:
            continue
        prior = int(j["prior_pick"])
        if len(cw.get(prior, {})) < 20:
            continue
        selected = [int(c) for c in j["selected"]]
        g = per_game[str(j["game"])]
        ok = False
        for k in (10, 20, 25):
            v = decision_gains(cw, selected, prior, k, gated=False)
            if v is not None:
                h_acc[k].append(v)
                if k == 25:
                    g["ungated25"].append(v)
                    ok = True
        v = decision_gains(cw, selected, prior, 25, gated=True)
        if v is not None:
            g["gated25"].append(v)
        if ok:
            n_usable += 1
    rng = random.Random(20261018)
    def boot(per_game, key):
        games = [g for g in per_game.values() if g[key]]
        sums = [sum(g[key]) for g in games]
        if not sums:
            return None
        mean = sum(sums) / len(sums)
        reps = []
        for _ in range(4000):
            sample = [rng.choice(sums) for _ in sums]
            reps.append(sum(sample) / len(sample))
        reps.sort()
        return {"per_game_gain": mean, "ci95": [reps[100], reps[3899]],
                "per_game_gain_wp": mean / 2,
                "ci95_wp": [reps[100] / 2, reps[3899] / 2],
                "n_games": len(sums)}
    report = {
        "decisions_usable": n_usable,
        "decisions_per_game": (n_usable / len(per_game)) if per_game else 0,
        "H_ungated_per_decision": {
            str(k): (sum(v) / len(v) if v else None) for k, v in h_acc.items()},
        "ungated25": boot(per_game, "ungated25"),
        "gated25": boot(per_game, "gated25"),
    }
    print(json.dumps(report, indent=1))
    if out_path:
        json.dump(report, open(out_path, "w"), indent=1)

if __name__ == "__main__":
    main()
