#!/usr/bin/env python3
"""build_swap_jobs.py - jobs for the round-8 L2-form swap test
(build-package sec.5; claude-reply-926f6c3 sec.5(4)).

The registered form: 20 snapshots x both picks, states drawn
from the GATE's divergence decisions, for the distilled policy
and the v15 control. The gate's raw arms record no snapshots
(raw play snapshots nothing; KEEP_GAME keeps only final game
dirs), so the gate's divergence DECISIONS are not recoverable
as states - the registered substitute, stated here and in the
package: corpus snapshots where the two policies' offline picks
diverge (distilled argmax on the CORRECTED featurization !=
v15 argmax on the NATIVE one). Twenty are sampled (seeded),
spread across branches as far as the pool allows. These are
states where the two policy/build pairs actually part company -
the population the swap test exists to interrogate - and the
substitution is disclosed wherever the result is cited.

Candidate lists come from the capture corpus's snap indexes
(the same source t1_build_data.py reads); states come from the
builder's states files. Picks are recomputed here from states +
checkpoints (no builder tensors are reused).

Usage: build_swap_jobs.py --data <t1 data dir> --corpus
  <capture corpus dir> --tree <corrected tree, for bc_features>
  --v15 <ckpt> --distilled <ckpt> --out swap_jobs.jsonl
  [--n 20] [--seed 20261025]
"""
import argparse
import glob
import json
import random
import sys
from collections import defaultdict

import torch


def argmax_pick(state, cands, net, vocab, bc_features, bc_features_v3):
    sv, own, opp = bc_features_v3.featurize_state_v3(state, vocab)
    cf = [bc_features.featurize_candidate(c, vocab) for c in cands]
    ci = torch.tensor([[c for c, _ in cf]])
    zi = torch.tensor([[z for _, z in cf]])
    with torch.no_grad():
        logits, _ = net(torch.tensor([sv]), torch.tensor([own]),
                        torch.tensor([opp]), ci, zi)
    return int(torch.argmax(logits[0]).item())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--v15", required=True)
    ap.add_argument("--distilled", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261025)
    a = ap.parse_args()

    sys.path.insert(0, a.tree)
    import bc_features
    import bc_features_v3
    from ppo_model_v3 import PPOPolicyV3

    meta = {}
    for idx in sorted(glob.glob(
            a.corpus.rstrip("/") + "/*_log/snaps/teacher_snap_index.jsonl")):
        snaps_dir = idx.rsplit("/", 1)[0]
        for ln in open(idx):
            if not ln.strip():
                continue
            r = json.loads(ln)
            meta[r["snap"]] = {
                "snap_dir": snaps_dir + "/" + r["snap"],
                "game": str(r["game"]), "player": int(r["player"]),
                "branch": r["branch"], "cands": r["cands"]}
    nat, cor = {}, {}
    for fn, dst in (("states_native.jsonl", nat),
                    ("states_corrected.jsonl", cor)):
        for ln in open(a.data.rstrip("/") + "/" + fn):
            r = json.loads(ln)
            if "state" in r and r["snap"] in meta:
                dst[r["snap"]] = r["state"]

    nets = {}
    for name, path in (("v15", a.v15), ("distilled", a.distilled)):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        net = PPOPolicyV3(len(ck["vocab"]))
        net.load_state_dict(ck["model"], strict=True)
        net.eval()
        nets[name] = (net, ck["vocab"])

    divergent = []
    for snap, m in sorted(meta.items()):
        if snap not in nat or snap not in cor:
            continue
        p15 = argmax_pick(nat[snap], m["cands"], *nets["v15"],
                          bc_features, bc_features_v3)
        pdi = argmax_pick(cor[snap], m["cands"], *nets["distilled"],
                          bc_features, bc_features_v3)
        if p15 != pdi:
            divergent.append({**m, "snap": snap,
                              "v15_pick": p15, "distilled_pick": pdi})
    print(f"divergent-pick snapshots in corpus: {len(divergent)}")
    by_branch = defaultdict(list)
    for d in divergent:
        by_branch[d["branch"]].append(d)
    rng = random.Random(a.seed)
    for v in by_branch.values():
        rng.shuffle(v)
    chosen, branches = [], sorted(by_branch)
    while len(chosen) < a.n and any(by_branch.values()):
        for b in branches:
            if by_branch[b] and len(chosen) < a.n:
                chosen.append(by_branch[b].pop())
    with open(a.out, "w") as f:
        for d in chosen:
            f.write(json.dumps(d) + "\n")
    print(f"wrote {len(chosen)} swap jobs -> {a.out} "
          f"(branches: {sorted(d['branch'] for d in chosen)})")


if __name__ == "__main__":
    main()
