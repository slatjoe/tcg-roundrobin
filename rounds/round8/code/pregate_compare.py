#!/usr/bin/env python3
"""pregate_compare.py - the round-8 pre-gate's comparisons, read
strictly from the paired driver's own outputs (build-package
sec.5). Nothing here is eyeballed from packet captures: the
round-4 lesson. Two report-only checks:

1. DETERMINISM per tree: the same raw-arm run (seeds 11001-11010,
   both seats, vs heuristic) executed twice must produce
   identical per-game records - same winner, turns, decisions,
   and gamelog sha256 (the D1/D2 fields).
2. FEATURIZER-ONLY CONTROL (claude-reply-926f6c3 sec.5(3)): v15
   raw on the corrected tree vs v15 raw on the native tree,
   paired on the same seeds - the count of identical paired
   units is the read (report-only; no band is registered on it).

The R16-style seat control (the two raw seats of one tree must
differ on at least one seed) is computed from the same rows and
printed - a control that passed on both pre-restructure fleets.

Usage: pregate_compare.py --native-run1 <rows> --native-run2 <rows>
  --corr-run1 <rows> --corr-run2 <rows> --out <report json>
"""
import argparse
import json


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return {(r["seed"], r["arm"], r["learner_seat"]): r for r in rows}


def det_report(r1, r2, label):
    keys = sorted(set(r1) & set(r2))
    diffs = []
    for k in keys:
        a, b = r1[k], r2[k]
        for f in ("winner", "turns", "decisions", "gamelog_sha256"):
            if str(a.get(f)) != str(b.get(f)):
                diffs.append({"key": k, "field": f,
                              "run1": a.get(f), "run2": b.get(f)})
    missing = sorted(set(r1) ^ set(r2))
    return {"tree": label, "units": len(keys),
            "deterministic": not diffs and not missing,
            "diffs": diffs[:10], "key_mismatch": [str(k) for k in missing]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--native-run1", required=True)
    ap.add_argument("--native-run2", required=True)
    ap.add_argument("--corr-run1", required=True)
    ap.add_argument("--corr-run2", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    n1, n2 = load(a.native_run1), load(a.native_run2)
    c1, c2 = load(a.corr_run1), load(a.corr_run2)
    rep = {"determinism": [det_report(n1, n2, "native"),
                           det_report(c1, c2, "corrected")]}
    # Featurizer-only control: native run1 vs corrected run1.
    keys = sorted(set(n1) & set(c1))
    ident = sum(1 for k in keys
                if str(n1[k].get("gamelog_sha256"))
                == str(c1[k].get("gamelog_sha256")))
    wdiff = sum(1 for k in keys
                if str(n1[k].get("winner")) != str(c1[k].get("winner")))
    rep["featurizer_only_control"] = {
        "paired_units": len(keys), "identical_gamelog": ident,
        "winner_differs": wdiff,
        "note": "report-only (sec.5(3)): the featurizer "
                "correction's isolated effect on v15's play"}
    # R16-style seat control per tree (run1): seats differ somewhere.
    for rows, label in ((n1, "native"), (c1, "corrected")):
        s1 = {k[0]: v for k, v in rows.items()
              if k[1] == "raw" and k[2] == 1}
        s2 = {k[0]: v for k, v in rows.items()
              if k[1] == "raw" and k[2] == 2}
        common = sorted(set(s1) & set(s2))
        nd = sum(1 for s in common
                 if str(s1[s].get("gamelog_sha256"))
                 != str(s2[s].get("gamelog_sha256")))
        rep.setdefault("seat_control", {})[label] = {
            "seeds": len(common), "differing": nd,
            "pass": nd >= 1}
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
