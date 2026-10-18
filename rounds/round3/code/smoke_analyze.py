#!/usr/bin/env python3
"""Read-only smoke analysis: aligns raw/ghost/shadow traces by seq and
answers, per root decision: state parity (raw state_hash vs ghost
feat_pre_hash), checkpoint mutation (feat_pre vs feat_post), endpoint
agreement (priors_pre argmax vs priors_post argmax vs played pick),
and the first seq where raw and ghost picks differ."""
import json
import sys


def load(p):
    rows = [json.loads(l) for l in open(p) if l.strip()]
    return {r["seq"]: r for r in rows}


def argmax(v):
    return max(range(len(v)), key=lambda i: v[i]) if v else None


raw = load(sys.argv[1])
ghost = load(sys.argv[2])
shadow = load(sys.argv[3])

root_seqs = sorted(s for s, r in ghost.items() if r.get("feat_pre_hash"))
print("root decisions traced (ghost):", len(root_seqs))
n_state_diff = n_feat_diff = n_pre_post_argmax_diff = 0
first_pick_diff = None
for s in root_seqs:
    g, r = ghost[s], raw.get(s)
    if r is not None and r.get("state_hash") != g["feat_pre_hash"]:
        n_state_diff += 1
        if n_state_diff <= 3:
            print(f"seq {s}: STATE differs raw={r.get('state_hash')} "
                  f"ghost_pre={g['feat_pre_hash']} branch={g['branch']}")
    if g["feat_pre_hash"] != g.get("feat_post_hash"):
        n_feat_diff += 1
        if n_feat_diff <= 3:
            print(f"seq {s}: CHECKPOINT feature mutation pre={g['feat_pre_hash']} "
                  f"post={g.get('feat_post_hash')}")
    if g.get("priors_pre") and g.get("priors_post"):
        if argmax(g["priors_pre"]) != argmax(g["priors_post"]):
            n_pre_post_argmax_diff += 1
            if n_pre_post_argmax_diff <= 3:
                print(f"seq {s}: pre/post argmax differ "
                      f"{argmax(g['priors_pre'])} vs {argmax(g['priors_post'])}")
    if r is not None and first_pick_diff is None and r.get("chosen") != g.get("chosen"):
        first_pick_diff = s
        print(f"seq {s}: FIRST PICK DIVERGENCE raw_chosen={r.get('chosen')} "
              f"ghost_chosen={g.get('chosen')} decide_pick={g.get('decide_pick')} "
              f"branch={g['branch']} ncand={g.get('ncand')} "
              f"priors_pre={g.get('priors_pre')} priors_post={g.get('priors_post')} "
              f"state_raw={r.get('state_hash')} feat_pre={g['feat_pre_hash']} "
              f"feat_post={g.get('feat_post_hash')} cand={g.get('cand_hash')} "
              f"cand_raw={r.get('cand_hash')}")
print("state diffs:", n_state_diff, "| checkpoint feature mutations:",
      n_feat_diff, "| pre/post argmax flips:", n_pre_post_argmax_diff)
print("first pick divergence seq:", first_pick_diff)
# shadow agreement with ghost on picks (they produced identical gamelogs)
sd = [s for s in root_seqs if shadow[s].get("chosen") != ghost[s].get("chosen")]
print("shadow vs ghost pick diffs:", len(sd))
sr = [s for s in root_seqs
      if shadow[s].get("rule") == "shadow_bridge"]
print("shadow rows ruled shadow_bridge:", len(sr), "/", len(root_seqs))
