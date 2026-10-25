#!/usr/bin/env python3
"""Round-5 (b) census tally (claude-reply-972091e sec.3 reporting additions).

Read-only over the two census logs (census_s1.jsonl, census_s2.jsonl).
Every rate is split BY DIRECTION (reporting addition 1): a disagreeing
featurization is classified
  store>view : every differing card has store count > view count
               (the root-abort double-count signature direction)
  view>store : every differing card has view count > store count
               (the smoke's arsenal / pitch-return shape)
  mixed      : both signs present in one featurization
The ARS rate is reported explicitly with its Wilson interval
(reporting addition 2).

For view>store rows, whether the differing card appears in any other
serialized zone is UNAVAILABLE from the log: the probe computes
view_elsewhere only for store>view diffs (featurize.php probe block:
$censusElse is counted inside `if ($censusSv > $censusVv)` and is
written as its initialized 0 otherwise). The tally therefore never
reads the third element for view>store diffs.

Usage: tally_census.py [log1 log2 ...]   (default: the staged logs)
Output: printed tally (redirect to tally.txt).
"""
import json
import math
import sys
from collections import Counter, defaultdict

Z = 1.959964  # 95%


def wilson(k, n):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def direction(row):
    ds = [sv - vv for (sv, vv, _e) in row["diffs"].values()]
    if all(d > 0 for d in ds):
        return "store>view"
    if all(d < 0 for d in ds):
        return "view>store"
    return "mixed"


def rate_line(label, k, n):
    lo, hi = wilson(k, n)
    return (f"{label}: {k}/{n} = {100*k/n:.3f}%  "
            f"Wilson95 [{100*lo:.3f}%, {100*hi:.3f}%]") if n else f"{label}: n=0"


def main():
    paths = sys.argv[1:] or [
        "rounds/round5/data/census/census_s1.jsonl",
        "rounds/round5/data/census/census_s2.jsonl",
    ]
    rows = []
    per_log = {}
    for p in paths:
        ls = [json.loads(l) for l in open(p) if l.strip()]
        per_log[p] = ls
        rows.extend(ls)
    dis = [r for r in rows if not r["agree"]]
    for r in dis:
        r["_dir"] = direction(r)

    print("ROUND-5 (b) CENSUS TALLY")
    print("========================")
    for p, ls in per_log.items():
        d = sum(1 for r in ls if not r["agree"])
        print(f"{p}: {len(ls)} featurizations, {d} disagreements, "
              f"{len(set(r['game'] for r in ls))} games")
    print(f"TOTAL: {len(rows)} featurizations, {len(dis)} disagreements, "
          f"{len(set(r['game'] for r in rows))} distinct games")
    print()
    print("OVERALL")
    print(rate_line("  disagreement rate", len(dis), len(rows)))
    for dname in ("store>view", "view>store", "mixed"):
        k = sum(1 for r in dis if r["_dir"] == dname)
        print(rate_line(f"  direction {dname}", k, len(rows)))
    print()
    print("BY BRANCH (each direction split)")
    branches = sorted(set(r["branch"] for r in rows))
    for b in branches:
        sub = [r for r in rows if r["branch"] == b]
        dsub = [r for r in sub if not r["agree"]]
        print(rate_line(f"  {b} all", len(dsub), len(sub)))
        for dname in ("store>view", "view>store", "mixed"):
            k = sum(1 for r in dsub if r["_dir"] == dname)
            if k:
                print(rate_line(f"    {b} {dname}", k, len(sub)))
    print()
    print("ARS RATE (explicit, reporting addition 2)")
    ars = [r for r in rows if r["branch"] == "ARS"]
    adis = [r for r in ars if not r["agree"]]
    print(rate_line("  ARS all directions", len(adis), len(ars)))
    for dname in ("store>view", "view>store", "mixed"):
        k = sum(1 for r in adis if r["_dir"] == dname)
        print(rate_line(f"  ARS {dname}", k, len(ars)))
    print()
    print("BY PLAYER (each direction split)")
    for pl in sorted(set(r["player"] for r in rows)):
        sub = [r for r in rows if r["player"] == pl]
        dsub = [r for r in sub if not r["agree"]]
        print(rate_line(f"  player {pl} all", len(dsub), len(sub)))
        for dname in ("store>view", "view>store", "mixed"):
            k = sum(1 for r in dsub if r["_dir"] == dname)
            if k:
                print(rate_line(f"    player {pl} {dname}", k, len(sub)))
    print()
    print("BY PLAYER x BRANCH=ARS")
    for pl in sorted(set(r["player"] for r in rows)):
        sub = [r for r in ars if r["player"] == pl]
        dsub = [r for r in sub if not r["agree"]]
        print(rate_line(f"  player {pl} ARS", len(dsub), len(sub)))
    print()
    print("DIFFERING-CARD TABLE (card: differing featurizations; "
          "delta (store-view) distribution)")
    card_rows = Counter()
    card_deltas = defaultdict(Counter)
    total_card_diffs = 0
    for r in dis:
        seen = set()
        for cid, (sv, vv, _e) in r["diffs"].items():
            total_card_diffs += 1
            card_deltas[cid][sv - vv] += 1
            if cid not in seen:
                card_rows[cid] += 1
                seen.add(cid)
    print(f"  distinct cards differing: {len(card_rows)}; "
          f"total card-diff entries: {total_card_diffs}")
    for cid, k in card_rows.most_common():
        dd = ", ".join(f"{d:+d} x{c}" for d, c in sorted(card_deltas[cid].items()))
        print(f"  {cid}: {k} featurizations; deltas: {dd}")
    print()
    print("DOUBLE-COUNT SIGNATURE SUBSET (store>view diffs whose excess is "
          "fully accounted by view_elsewhere)")
    sig_rows = 0
    sig_by_branch = Counter()
    sv_rows = [r for r in dis if r["_dir"] == "store>view"]
    for r in sv_rows:
        if all((sv - vv) <= e for (sv, vv, e) in r["diffs"].values()):
            sig_rows += 1
            sig_by_branch[r["branch"]] += 1
    print(f"  store>view featurizations: {len(sv_rows)}; "
          f"in signature subset: {sig_rows}; by branch: {dict(sig_by_branch)}")
    print()
    print("VIEW>STORE ZONE MEMBERSHIP (Claude reporting addition 1)")
    vs_rows = [r for r in dis if r["_dir"] == "view>store"]
    print(f"  view>store featurizations: {len(vs_rows)}. Whether a "
          "differing card appears in any other serialized zone is "
          "UNAVAILABLE from the census log for this direction: the "
          "probe computes view_elsewhere only for store>view diffs "
          "and writes its initialized 0 for view>store diffs, so the "
          "logged third element carries no zone information here.")


if __name__ == "__main__":
    main()
