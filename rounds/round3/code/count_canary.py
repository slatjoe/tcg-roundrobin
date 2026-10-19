#!/usr/bin/env python3
"""Canary refusal accounting for one arm's search_stats.jsonl.

Denominator discipline (matches Claude's '16 rows of 1,354' framing):
RootDecide invocations = teacher rows (Decide ran) + canary fallback
rows (refused before Decide). The refusal rate is canary / total.
Per-branch rates use the same construction per branch. Also reports
the contested==1 subset for reference.
Usage: count_canary.py <search_stats.jsonl> <label>
"""
import collections
import json
import sys

rows = [json.loads(l) for l in open(sys.argv[1])]
label = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
teacher = [r for r in rows if r.get("teacher") == 1]
canary = [r for r in rows if r.get("fallback") == "canary"]
contested = [r for r in teacher if r.get("contested") == 1]
total = len(teacher) + len(canary)
print(f"{label}: stat_rows={len(rows)} teacher_rows={len(teacher)} "
      f"canary={len(canary)} root_calls={total} "
      f"refusal_rate={100.0 * len(canary) / max(1, total):.3f}% "
      f"contested_rows={len(contested)}")
tb = collections.Counter(r.get("branch") for r in teacher)
cb = collections.Counter(r.get("branch") for r in canary)
for b in sorted(set(tb) | set(cb)):
    d = tb.get(b, 0) + cb.get(b, 0)
    print(f"  branch {b}: canary {cb.get(b, 0)} / root calls {d} "
          f"= {100.0 * cb.get(b, 0) / max(1, d):.2f}%")
