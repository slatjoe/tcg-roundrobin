#!/usr/bin/env python3
"""t1_trainer.py - round-8 T1: supervised distillation of the
teacher into v15 (build-package sec.4; claude-reply-926f6c3
sec.3-4).

Objective (registered): uniform cross-entropy to the teacher's
pick on contested states, plus beta * KL(v15 || student) on the
same corpus games' uncontested states, beta = 1. v15's side of
the KL is computed from the NATIVE featurization; the student's
from the CORRECTED (the data builder ships both). No value-head
training: the value head is v15's, frozen - it is excluded from
the optimizer and the saved checkpoint's value head is asserted
tensor-equal to v15's before saving.

Selection (registered): NO game-based selection. A fixed
schedule with early stopping on HELD-OUT cross-entropy (held-out
games from the data builder's by-game split): the checkpoint at
the held-out-CE minimum, with the patience stated in the config
in advance, is the ONE checkpoint written. Exactly one
checkpoint enters the gate.

Init: v15 (D2). Architecture and vocab: v15's (PPOPolicyV3).

Usage: t1_trainer.py --data <builder outdir> --config
  t1_config.json --tree <corrected tree> --out <ckpt path>
  --log <train log json>
"""
import argparse
import glob
import json
import os
import sys
import time

import torch
import torch.nn.functional as Fn

DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_shards(data, prefix):
    acc = None
    for p in sorted(glob.glob(os.path.join(data, prefix + "_*.pt"))):
        d = torch.load(p, weights_only=False)
        if acc is None:
            acc = {k: [] for k in d}
        for k in d:
            acc[k].extend(d[k])
    return acc


def batches(n, batch, rng):
    perm = torch.randperm(n, generator=rng)
    for i in range(0, n, batch):
        yield perm[i:i + batch]


def pad_batch(acc, idx, keys):
    """Collate records idx from an accumulator into padded tensors."""
    out = {}
    for k in ("sv", "sv_n", "sv_c"):
        if k in acc:
            out[k] = torch.as_tensor(
                [acc[k][i] for i in idx], dtype=torch.float32)
    for k in ("own", "opp", "own_n", "opp_n", "own_c", "opp_c"):
        if k in acc:
            out[k] = torch.as_tensor(
                [acc[k][i] for i in idx], dtype=torch.long)
    K = max(acc["ncand"][i] for i in idx)
    ci = torch.zeros((len(idx), K), dtype=torch.long)
    zi = torch.zeros((len(idx), K), dtype=torch.long)
    mask = torch.zeros((len(idx), K), dtype=torch.bool)
    for r, i in enumerate(idx):
        n = acc["ncand"][i]
        ci[r, :n] = torch.as_tensor(acc["ci"][i][:n], dtype=torch.long)
        zi[r, :n] = torch.as_tensor(acc["zi"][i][:n], dtype=torch.long)
        mask[r, :n] = True
    out["ci"], out["zi"], out["mask"] = ci, zi, mask
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    sys.path.insert(0, a.tree)
    from ppo_model_v3 import PPOPolicyV3

    init = torch.load(cfg["init_ckpt"], map_location="cpu",
                      weights_only=False)
    vocab = init["vocab"]
    torch.manual_seed(int(cfg["seed"]))
    rng = torch.Generator().manual_seed(int(cfg["seed"]))

    student = PPOPolicyV3(len(vocab)).to(DEV)
    student.load_state_dict(init["model"], strict=True)
    v15 = PPOPolicyV3(len(vocab)).to(DEV)
    v15.load_state_dict(init["model"], strict=True)
    v15.eval()
    for p in v15.parameters():
        p.requires_grad_(False)
    # The value head is NOT trained (registered): freeze it in the
    # student and keep it out of the optimizer.
    for name, p in student.named_parameters():
        if name.startswith("value_head"):
            p.requires_grad_(False)
    opt = torch.optim.Adam(
        [p for p in student.parameters() if p.requires_grad],
        lr=float(cfg["lr"]))
    value_head_before = {k: v.detach().clone()
                         for k, v in student.state_dict().items()
                         if k.startswith("value_head")}

    con = load_shards(a.data, "shard")
    kl = load_shards(a.data, "kl_shard")
    con_tr = [i for i, s in enumerate(con["split"]) if s == "train"]
    con_ho = [i for i, s in enumerate(con["split"]) if s == "heldout"]
    kl_tr = [i for i, s in enumerate(kl["split"]) if s == "train"]
    print(f"contested train {len(con_tr)} heldout {len(con_ho)}; "
          f"KL train {len(kl_tr)}", flush=True)
    assert con_tr and con_ho and kl_tr

    def heldout_ce():
        student.eval()
        tot, n = 0.0, 0
        with torch.no_grad():
            for idx in batches(len(con_ho), int(cfg["batch"]), rng):
                sel = [con_ho[i] for i in idx.tolist()]
                b = pad_batch(con, sel, None)
                logits, _ = student(b["sv"].to(DEV), b["own"].to(DEV),
                                    b["opp"].to(DEV), b["ci"].to(DEV),
                                    b["zi"].to(DEV))
                logits = logits.masked_fill(~b["mask"].to(DEV), -1e9)
                act = torch.as_tensor([con["action"][i] for i in sel],
                                      device=DEV)
                tot += float(Fn.cross_entropy(logits, act,
                                              reduction="sum"))
                n += len(sel)
        student.train()
        return tot / max(1, n)

    beta = float(cfg["beta"])
    best_ce, best_epoch, best_sd = float("inf"), -1, None
    stale = 0
    log = {"config": cfg, "epochs": []}
    for ep in range(int(cfg["epochs_max"])):
        t0 = time.time()
        student.train()
        kl_iter = batches(len(kl_tr), int(cfg["batch"]), rng)
        kl_buf = []
        loss_sum, seen = 0.0, 0
        for idx in batches(len(con_tr), int(cfg["batch"]), rng):
            sel = [con_tr[i] for i in idx.tolist()]
            b = pad_batch(con, sel, None)
            logits, _ = student(b["sv"].to(DEV), b["own"].to(DEV),
                                b["opp"].to(DEV), b["ci"].to(DEV),
                                b["zi"].to(DEV))
            logits = logits.masked_fill(~b["mask"].to(DEV), -1e9)
            act = torch.as_tensor([con["action"][i] for i in sel],
                                  device=DEV)
            loss = Fn.cross_entropy(logits, act)
            # KL term: one KL batch per CE batch (cycled).
            try:
                kidx = next(kl_iter)
            except StopIteration:
                kl_iter = batches(len(kl_tr), int(cfg["batch"]), rng)
                kidx = next(kl_iter)
            ksel = [kl_tr[i] for i in kidx.tolist()]
            kb = pad_batch(kl, ksel, None)
            with torch.no_grad():
                lp15, _ = v15(kb["sv_n"].to(DEV), kb["own_n"].to(DEV),
                              kb["opp_n"].to(DEV), kb["ci"].to(DEV),
                              kb["zi"].to(DEV))
            lst, _ = student(kb["sv_c"].to(DEV), kb["own_c"].to(DEV),
                             kb["opp_c"].to(DEV), kb["ci"].to(DEV),
                             kb["zi"].to(DEV))
            m = kb["mask"].to(DEV)
            lp15 = lp15.masked_fill(~m, -1e9)
            lst = lst.masked_fill(~m, -1e9)
            p15 = torch.softmax(lp15, dim=1)
            kl_term = (p15 * (torch.log_softmax(lp15, dim=1)
                              - torch.log_softmax(lst, dim=1))
                       ).sum(dim=1).mean()
            loss = loss + beta * kl_term
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_sum += float(loss) * len(sel)
            seen += len(sel)
        ce = heldout_ce()
        rec = {"epoch": ep, "train_loss": loss_sum / max(1, seen),
               "heldout_ce": ce, "secs": round(time.time() - t0, 1)}
        log["epochs"].append(rec)
        print(f"epoch {ep}: train {rec['train_loss']:.4f} "
              f"heldout CE {ce:.4f} ({rec['secs']}s)", flush=True)
        if ce < best_ce - float(cfg["min_delta"]):
            best_ce, best_epoch = ce, ep
            best_sd = {k: v.detach().cpu().clone()
                       for k, v in student.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= int(cfg["patience"]):
                print(f"early stop at epoch {ep} (patience "
                      f"{cfg['patience']}); best epoch {best_epoch}",
                      flush=True)
                break
    assert best_sd is not None
    # The frozen value head must be untouched - assert it.
    for k, v in value_head_before.items():
        assert torch.equal(best_sd[k].cpu(), v.cpu()), \
            f"value head changed during T1: {k}"
    torch.save({"model": best_sd, "vocab": vocab, "arch": "v3",
                "version": "t1-distill-r8"}, a.out)
    log["best_epoch"] = best_epoch
    log["best_heldout_ce"] = best_ce
    log["out"] = a.out
    json.dump(log, open(a.log, "w"), indent=1)
    print(f"saved ONE checkpoint {a.out} (epoch {best_epoch}, "
          f"held-out CE {best_ce:.4f}); value head verified frozen")


if __name__ == "__main__":
    main()
