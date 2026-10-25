#!/usr/bin/env python3
"""label_reduce.py - apply the registered teacher's Decide
arithmetic to the offline labeler's raw rows and emit labels
(round 8, build-package sec.2).

The arithmetic mirrors SimTeacher_Decide (search.php, gate build
6cd6f980...) line for line:
  * a candidate's finished worlds are its rollout rows with a
    result that carries no "error" and finished == 1 (Decide's own
    collection rule); its mean is over those worlds (outcomes are
    root-perspective -1 / 0 / +1 from SimLabel_RunRollout).
  * if the PRIOR candidate finished fewer than 20 worlds, the live
    teacher falls back "thin_prior" and plays the prior. A thin
    label is EXCLUDED and counted (claude-reply-926f6c3 sec.1) -
    never emitted with the prior as a fake teacher pick.
  * best = the argmax mean over the selected set, scanned in
    ascending index order with strict > (Decide's order).
  * if best != prior: paired diffs over the worlds BOTH finished;
    with >= 20 paired worlds, mean_diff and se_diff (sample sd /
    sqrt(n), Decide's formula) and an overturn iff
    mean_diff > 1.5 * se_diff. With < 20 paired worlds the live
    teacher cannot overturn: the label is a CONFIRMATION flagged
    paired_thin (counted, not hidden).
  * if best == prior the label confirms the prior
    (mean_diff / se_diff null, exactly as Decide logs them).
  * every label row also carries the per-candidate finished-world
    MEANS and sample SDs ("means" / "sds", keyed by candidate
    index, aligned with "candidates") - the pilot's mechanism
    check (claude-reply-a076148 sec.3) reads them against the
    live stat rows' means.

Inputs: --jobs (the labeler's job file), --raw (one or more raw
row files from distill_label_main.php), --out labels file,
--thin-out thin file. Prints a counts summary.
"""
import argparse
import json
import math
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--raw", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--thin-out", required=True)
    a = ap.parse_args()

    jobs = {}
    for ln in open(a.jobs):
        ln = ln.strip()
        if ln:
            j = json.loads(ln)
            jobs[j["snap"]] = j

    # outcomes[(snap, cand)][world] = outcome, finished only
    outcomes = defaultdict(dict)
    seen_snaps = set()
    for path in a.raw:
        for ln in open(path):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            seen_snaps.add(r["snap"])
            res = r.get("result")
            if not isinstance(res, dict):
                continue
            if "error" in res or not res.get("finished"):
                continue
            outcomes[(r["snap"], int(r["cand"]))][int(r["world"])] = \
                float(res["outcome"])

    labels, thin = [], []
    counts = {"jobs": len(jobs), "no_rows": 0, "prior_not_selected": 0,
              "thin": 0, "confirm": 0, "confirm_paired_thin": 0,
              "overturn": 0, "no_overturn_tested": 0}
    for snap, j in jobs.items():
        if snap not in seen_snaps:
            counts["no_rows"] += 1
            continue
        sel = [int(x) for x in j["selected"]]
        prior = int(j["prior_pick"])
        if prior not in sel:
            counts["prior_not_selected"] += 1
            continue
        n_worlds = {ci: len(outcomes.get((snap, ci), {})) for ci in sel}
        if n_worlds.get(prior, 0) < 20:
            counts["thin"] += 1
            thin.append({"snap": snap, "game": j["game"],
                         "n_worlds": n_worlds,
                         "reason": "prior candidate finished "
                                   f"{n_worlds.get(prior, 0)} < 20 worlds"})
            continue
        means = {}
        sds = {}
        for ci in sel:
            vals = list(outcomes.get((snap, ci), {}).values())
            if vals:
                m = sum(vals) / len(vals)
                means[ci] = m
                sds[ci] = (math.sqrt(
                    sum((v - m) ** 2 for v in vals)
                    / max(1, len(vals) - 1)) if len(vals) > 1 else 0.0)
            else:
                means[ci] = None
                sds[ci] = None
        best = prior
        best_mean = means[prior]
        for ci in sel:
            if means[ci] is not None and means[ci] > best_mean:
                best_mean = means[ci]
                best = ci
        row = {"state_id": snap, "snap_dir": j["snap_dir"],
               "game": j["game"], "player": int(j["player"]),
               "branch": j["branch"], "turn": int(j.get("turn", 0)),
               "prior_pick": prior, "candidates": sel,
               "n_worlds": {str(k): v for k, v in n_worlds.items()},
               "means": {str(k): v for k, v in means.items()},
               "sds": {str(k): v for k, v in sds.items()},
               "paired_n": None, "mean_diff": None, "se_diff": None}
        if best == prior:
            counts["confirm"] += 1
            row["teacher_pick"] = prior
            row["overturn"] = 0
            labels.append(row)
            continue
        ob = outcomes.get((snap, best), {})
        op = outcomes.get((snap, prior), {})
        ds = [ob[w] - op[w] for w in ob if w in op]
        row["paired_n"] = len(ds)
        if len(ds) >= 20:
            md = sum(ds) / len(ds)
            var = sum((d - md) ** 2 for d in ds)
            se = math.sqrt(var / max(1, len(ds) - 1)) / math.sqrt(len(ds))
            row["mean_diff"] = md
            row["se_diff"] = se
            if md > 1.5 * se:
                counts["overturn"] += 1
                row["teacher_pick"] = best
                row["overturn"] = 1
            else:
                counts["no_overturn_tested"] += 1
                row["teacher_pick"] = prior
                row["overturn"] = 0
        else:
            counts["confirm_paired_thin"] += 1
            row["teacher_pick"] = prior
            row["overturn"] = 0
            row["paired_thin"] = 1
        labels.append(row)

    with open(a.out, "w") as f:
        for r in labels:
            f.write(json.dumps(r) + "\n")
    with open(a.thin_out, "w") as f:
        for r in thin:
            f.write(json.dumps(r) + "\n")
    counts["labels"] = len(labels)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
