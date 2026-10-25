#!/usr/bin/env python3
"""swap_test.py - the round-8 L2-form hidden-card swap test
(build-package sec.5; claude-reply-926f6c3 sec.5(4)).

For each job snapshot and each ARM (the distilled policy served
by the corrected tree; v15 as control, served by the native
tree): snapshot B is built by swapping the ROOT PLAYER'S
OPPONENT's hand[0] with their deck[0] in gamestate.txt - two
cards that are equally hidden from the root. The arm's pick on
B must equal its pick on A, and the featurized states must be
deep-identical: a policy whose pick moves when two hidden cards
exchange places is reading information it cannot have (the
round-3 L2 definition). Invariance is required on BOTH arms
(the reply's form); a failure on either is a finding about that
arm's serving path, reported per arm.

Why this form and not probe_swap20.php's: probe_swap20 measures
forced ROLLOUT trajectories from swapped states - that is the
LABELER's surface. The arm under test here is a raw policy
whose serving path is featurize -> net -> argmax; the L2-form
test interrogates exactly that path, offline, through the
arm's own tree build (featurize_snapshot.php) and the tree's
own bc_features. The picks are computed locally with the same
masked argmax the server applies.

Line positions in gamestate.txt (0-based, from
probe_swap20.php): P1 hand 1 / deck 2; P2 hand 19 / deck 20.
Jobs whose opponent hand or deck is empty cannot be swapped;
they are counted and excluded, never scored as passes.

Usage: swap_test.py --jobs swap_jobs.jsonl --scratch DIR
  --native-tree T --corrected-tree T --v15 CKPT --distilled CKPT
  --out report.json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import torch

HAND_LINE = {1: 1, 2: 19}
DECK_LINE = {1: 2, 2: 20}


def featurize(tree, jobs, out_path, deck):
    jobs_path = out_path + ".jobs.jsonl"
    with open(jobs_path, "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    env = dict(os.environ)
    env["FEAT_JOBS"] = jobs_path
    env["FEAT_OUT"] = out_path
    p = subprocess.run(
        ["php", "featurize_snapshot.php", deck, deck,
         "--policy-search", "--games", "1"],
        cwd=tree, env=env, capture_output=True, text=True)
    if "FEATURIZE-DONE" not in p.stderr:
        raise SystemExit(f"featurize failed in {tree}: {p.stderr[-500:]}")
    states = {}
    for ln in open(out_path):
        r = json.loads(ln)
        if "state" in r:
            states[r["snap"]] = r["state"]
    return states


def make_swapped(job, dst_root):
    dst = os.path.join(dst_root, job["snap"] + "_swapB")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(job["snap_dir"], dst)
    gs_path = os.path.join(dst, "gamestate.txt")
    raw = open(gs_path, "rb").read().decode("utf-8")
    lines = raw.split("\r\n")
    opp = 3 - int(job["player"])
    hl, dl = HAND_LINE[opp], DECK_LINE[opp]
    hand = lines[hl].split()
    deck = lines[dl].split()
    if not hand or not deck:
        shutil.rmtree(dst)
        return None
    hand[0], deck[0] = deck[0], hand[0]
    lines[hl] = " ".join(hand)
    lines[dl] = " ".join(deck)
    with open(gs_path, "wb") as f:
        f.write("\r\n".join(lines).encode("utf-8"))
    return dst


def pick(state, cands, net, vocab, bc_features, bc_features_v3):
    sv, own, opp = bc_features_v3.featurize_state_v3(state, vocab)
    cf = [bc_features.featurize_candidate(c, vocab) for c in cands]
    ci = torch.tensor([[c for c, _ in cf]])
    zi = torch.tensor([[z for _, z in cf]])
    with torch.no_grad():
        logits, _ = net(torch.tensor([sv]), torch.tensor([own]),
                        torch.tensor([opp]), ci, zi)
    return int(torch.argmax(logits[0]).item())


def run_arm(name, tree, ckpt_path, jobs, swapped, scratch):
    sys.path.insert(0, tree)
    import bc_features
    import bc_features_v3
    from ppo_model_v3 import PPOPolicyV3
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    net = PPOPolicyV3(len(ck["vocab"]))
    net.load_state_dict(ck["model"], strict=True)
    net.eval()
    deck = tree.rstrip("/") + "/decks/nats2026_ashlyn_fai_60.txt"
    ja = [{"snap_dir": j["snap_dir"], "snap": j["snap"],
           "game": j["game"], "player": j["player"],
           "branch": j["branch"], "cands": j["cands"]} for j in jobs]
    st_a = featurize(tree, ja, f"{scratch}/{name}_a.jsonl", deck)
    jb = [{"snap_dir": swapped[j["snap"]],
           "snap": j["snap"] + "_swapB",
           "game": j["game"], "player": j["player"],
           "branch": j["branch"], "cands": j["cands"]} for j in jobs
          if j["snap"] in swapped]
    st_b = featurize(tree, jb, f"{scratch}/{name}_b.jsonl", deck)
    rows, fails = [], 0
    for j in jobs:
        snap = j["snap"]
        if snap not in swapped:
            rows.append({"snap": snap, "result": "unswappable"})
            continue
        a_state, b_state = st_a[snap], st_b[snap + "_swapB"]
        same_state = (json.dumps(a_state, sort_keys=True)
                      == json.dumps(b_state, sort_keys=True))
        pa = pick(a_state, j["cands"], net, ck["vocab"],
                  bc_features, bc_features_v3)
        pb = pick(b_state, j["cands"], net, ck["vocab"],
                  bc_features, bc_features_v3)
        ok = same_state and pa == pb
        fails += 0 if ok else 1
        rows.append({"snap": snap, "state_identical": same_state,
                     "pick_a": pa, "pick_b": pb, "result":
                     "PASS" if ok else "FAIL"})
    del sys.modules["bc_features"], sys.modules["bc_features_v3"]
    sys.path.remove(tree)
    return {"arm": name, "tested": len([r for r in rows
                                        if r["result"] != "unswappable"]),
            "failures": fails, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--native-tree", required=True)
    ap.add_argument("--corrected-tree", required=True)
    ap.add_argument("--v15", required=True)
    ap.add_argument("--distilled", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    swapped = {}
    for j in jobs:
        dst = make_swapped(j, a.scratch)
        if dst:
            swapped[j["snap"]] = dst
    rep = {"jobs": len(jobs), "swappable": len(swapped), "arms": []}
    rep["arms"].append(run_arm("distilled", a.corrected_tree,
                               a.distilled, jobs, swapped, a.scratch))
    rep["arms"].append(run_arm("v15_control", a.native_tree,
                               a.v15, jobs, swapped, a.scratch))
    rep["verdict"] = ("INVARIANT on both arms"
                       if all(x["failures"] == 0 for x in rep["arms"])
                       else "INVARIANCE FAILURE - see per-arm rows")
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("jobs", "swappable",
                                           "verdict")}, indent=1))
    for arm in rep["arms"]:
        print(f"{arm['arm']}: tested {arm['tested']}, "
              f"failures {arm['failures']}")


if __name__ == "__main__":
    main()
