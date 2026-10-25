#!/usr/bin/env python3
"""t1_build_data.py - build the T1 training tensors from the
round-8 corpus (build-package sec.4).

Inputs: the capture corpus (snap indexes per stream), the label
stage's labels.jsonl, both trees. For every usable snapshot the
state is featurized TWICE - through the native tree's
featurize.php and through the corrected tree's (batch runs of
featurize_snapshot.php, deployed at each tree root) - because the
T1 loss reads the two builds differently (claude-reply-926f6c3
sec.2/3):
  * the STUDENT's tensors come from the CORRECTED featurization;
  * v15's KL-side tensors come from the NATIVE featurization.

Datasets written:
  * contested shards (shard_*.pt): labeled contested states -
    corrected tensors + the teacher pick as the action. Thin
    labels are absent from labels.jsonl by construction and are
    never trained on.
  * KL shards (kl_shard_*.pt): uncontested states from the same
    corpus games - native AND corrected tensors paired. States
    with a single candidate (ncand <= 1) are DROPPED from the KL
    set and counted: a single legal move gives a KL of exactly
    0, so the state carries no anchoring signal
    (claude-reply-a076148 sec.4.3).
  * states_index.jsonl + split.json: every used state, and the
    held-out split (~10% of corpus GAMES, split by game, seeded;
    the trainer's early stopping reads held-out CE only).
  * build_report.json: counts, the featurization assertion, and
    the input hashes (labels.jsonl, corpus_manifest.json).

Registry assertion (sec.4.3): the corpus's game ids must be
disjoint from the do-not-train registry - the corpus is fresh
games by construction, and this assert is what keeps an
accident (a corpus dir pointed at gate outputs) from training
on registered eval games. The build ABORTS on any overlap.

The assertion: for every snapshot whose capture index row stored
the LIVE state, the offline native featurization must equal it
(the package's smoke verified this on 40 gate snapshots: 40/40
equal). A mismatch means the offline path does not reproduce the
live root for that state; mismatched states are DROPPED from
both datasets and listed - never silently trained on.

Tensor encoding is the trees' own (bc_features_v3 +
bc_features.featurize_candidate, hash-pinned; identical in both
trees), with the vocab from the v15 checkpoint.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import subprocess
import sys

import torch


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def deep_equal(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


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
        raise SystemExit(f"featurize_snapshot failed in {tree}: "
                         f"{p.stderr[-800:]}")
    states = {}
    for ln in open(out_path):
        r = json.loads(ln)
        if "state" in r:
            states[r["snap"]] = r["state"]
        else:
            raise SystemExit(f"featurization error for {r['snap']}: "
                             f"{r.get('error')}")
    return states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--native-tree", required=True)
    ap.add_argument("--corrected-tree", required=True)
    ap.add_argument("--v15", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--holdout-frac", type=float, default=0.10)
    ap.add_argument("--split-seed", type=int, default=20261025)
    ap.add_argument("--registry",
                    default="/tmp/harvest/do_not_train_registry.json")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    labels = {}
    for ln in open(a.labels):
        r = json.loads(ln)
        labels[r["state_id"]] = r
    input_hashes = {"labels": {"path": a.labels,
                               "sha256": sha256_file(a.labels)}}
    manifest_path = a.corpus.rstrip("/") + "/corpus_manifest.json"
    assert os.path.exists(manifest_path), \
        f"corpus manifest missing: {manifest_path}"
    input_hashes["corpus_manifest"] = {
        "path": manifest_path, "sha256": sha256_file(manifest_path)}

    # ---- gather snapshots -------------------------------------
    contested, uncontested = {}, {}
    stored_state = {}
    for idx in sorted(glob.glob(
            a.corpus.rstrip("/") + "/*_log/snaps/teacher_snap_index.jsonl")):
        snaps_dir = idx.rsplit("/", 1)[0]
        for ln in open(idx):
            if not ln.strip():
                continue
            r = json.loads(ln)
            rec = {"snap": r["snap"], "snap_dir": snaps_dir + "/" + r["snap"],
                   "game": str(r["game"]), "player": int(r["player"]),
                   "branch": r["branch"], "cands": r["cands"]}
            if r.get("state") is not None:
                stored_state[r["snap"]] = r["state"]
            if r.get("uncontested"):
                uncontested[r["snap"]] = rec
            else:
                contested[r["snap"]] = rec
    print(f"corpus snapshots: contested {len(contested)}, "
          f"uncontested {len(uncontested)}, labeled {len(labels)}")

    # ---- split by game -----------------------------------------
    games = sorted({rec["game"] for rec in
                    list(contested.values()) + list(uncontested.values())})

    # Registry assertion: corpus game ids must not intersect the
    # do-not-train registry (sec.4.3).
    reg = json.load(open(a.registry))
    reg_ids = {str(g) for g in reg["games"]}
    overlap = sorted(set(games) & reg_ids)
    assert not overlap, (
        f"corpus game ids intersect the do-not-train registry: "
        f"{overlap[:10]} ({len(overlap)} total) - the corpus must "
        f"be fresh games only")
    print(f"registry assertion: {len(games)} corpus games, "
          f"0 in the registry ({len(reg_ids)} registered)")

    rng = random.Random(a.split_seed)
    shuffled = games[:]
    rng.shuffle(shuffled)
    n_hold = max(1, int(math.ceil(a.holdout_frac * len(games))))
    heldout = set(shuffled[:n_hold])
    json.dump({"heldout_games": sorted(heldout),
               "train_games": sorted(set(games) - heldout),
               "holdout_frac": a.holdout_frac, "split_seed": a.split_seed},
              open(a.outdir + "/split.json", "w"), indent=1)
    print(f"games {len(games)}: held out {len(heldout)}")

    # ---- dual featurization -------------------------------------
    jobs = []
    for rec in list(contested.values()) + list(uncontested.values()):
        jobs.append({"snap_dir": rec["snap_dir"], "snap": rec["snap"],
                     "game": rec["game"], "player": rec["player"],
                     "branch": rec["branch"], "cands": rec["cands"]})
    deck = a.native_tree.rstrip("/") + "/decks/nats2026_ashlyn_fai_60.txt"
    nat = featurize(a.native_tree, jobs, a.outdir + "/states_native.jsonl",
                    deck)
    cor = featurize(a.corrected_tree, jobs,
                    a.outdir + "/states_corrected.jsonl", deck)
    print(f"featurized: native {len(nat)}, corrected {len(cor)}")

    mismatched = []
    for snap, st in stored_state.items():
        if snap in nat and not deep_equal(st, nat[snap]):
            mismatched.append(snap)
    print(f"offline-native vs stored-live mismatches: {len(mismatched)}")
    drop = set(mismatched)

    # ---- encode --------------------------------------------------
    sys.path.insert(0, a.corrected_tree)
    import bc_features
    import bc_features_v3
    ckpt = torch.load(a.v15, map_location="cpu", weights_only=False)
    vocab = ckpt["vocab"]

    def encode(state, cands):
        sv, own, opp = bc_features_v3.featurize_state_v3(state, vocab)
        cf = [bc_features.featurize_candidate(c, vocab) for c in cands]
        return sv, own, opp, [c for c, _ in cf], [z for _, z in cf]

    def new_acc():
        return {k: [] for k in ("sv", "own", "opp", "ci", "zi",
                                "ncand", "game", "split")}

    con = new_acc()
    con["action"] = []
    con["prior_pick"] = []
    con["overturn"] = []
    kl = {k: [] for k in ("sv_n", "own_n", "opp_n", "sv_c", "own_c",
                          "opp_c", "ci", "zi", "ncand", "game", "split")}
    index_rows = []
    n_thin_dropped = 0
    for snap, rec in contested.items():
        if snap in drop:
            continue
        lab = labels.get(snap)
        if lab is None:
            n_thin_dropped += 1
            continue
        sv, own, opp, ci, zi = encode(cor[snap], rec["cands"])
        con["sv"].append(sv); con["own"].append(own); con["opp"].append(opp)
        con["ci"].append(ci); con["zi"].append(zi)
        con["ncand"].append(len(ci)); con["game"].append(rec["game"])
        con["split"].append("heldout" if rec["game"] in heldout else "train")
        con["action"].append(int(lab["teacher_pick"]))
        con["prior_pick"].append(int(lab["prior_pick"]))
        con["overturn"].append(int(lab["overturn"]))
        index_rows.append({"snap": snap, "game": rec["game"],
                           "kind": "contested",
                           "split": con["split"][-1],
                           "snap_dir": rec["snap_dir"]})
    n_kl_single_dropped = 0
    for snap, rec in uncontested.items():
        if snap in drop:
            continue
        if len(rec["cands"]) <= 1:
            # A single legal move gives a KL of exactly 0 - no
            # anchoring signal (sec.4.3). Dropped and counted.
            n_kl_single_dropped += 1
            continue
        svn, ownn, oppn, ci, zi = encode(nat[snap], rec["cands"])
        svc, ownc, oppc, _, _ = encode(cor[snap], rec["cands"])
        kl["sv_n"].append(svn); kl["own_n"].append(ownn)
        kl["opp_n"].append(oppn)
        kl["sv_c"].append(svc); kl["own_c"].append(ownc)
        kl["opp_c"].append(oppc)
        kl["ci"].append(ci); kl["zi"].append(zi)
        kl["ncand"].append(len(ci)); kl["game"].append(rec["game"])
        kl["split"].append("heldout" if rec["game"] in heldout else "train")
        index_rows.append({"snap": snap, "game": rec["game"],
                           "kind": "uncontested",
                           "split": kl["split"][-1],
                           "snap_dir": rec["snap_dir"]})

    def save_shards(acc, prefix, shard_size=50000):
        n = len(acc["game"])
        files = []
        for s in range(0, n, shard_size):
            d = {k: v[s:s + shard_size] for k, v in acc.items()}
            path = f"{a.outdir}/{prefix}_{len(files)}.pt"
            torch.save(d, path)
            files.append(path)
        return files

    con_files = save_shards(con, "shard")
    kl_files = save_shards(kl, "kl_shard")
    with open(a.outdir + "/states_index.jsonl", "w") as f:
        for r in index_rows:
            f.write(json.dumps(r) + "\n")
    report = {"contested_records": len(con["game"]),
              "kl_records": len(kl["game"]),
              "kl_single_candidate_dropped": n_kl_single_dropped,
              "thin_or_unlabeled_dropped": n_thin_dropped,
              "stored_state_mismatches_dropped": len(mismatched),
              "mismatched_snaps": mismatched[:50],
              "heldout_games": len(heldout),
              "input_hashes": input_hashes,
              "registry_assertion": {
                  "corpus_games": len(games),
                  "registry_games": len(reg_ids), "overlap": 0},
              "shards": con_files, "kl_shards": kl_files}
    json.dump(report, open(a.outdir + "/build_report.json", "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
