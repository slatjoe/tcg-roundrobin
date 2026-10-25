#!/usr/bin/env python3
"""make_pregate_fixture_rows.py - build fixture 2's inputs
(sec.2.3): one rows file in pre-gate shape from round 7's
published raw rows - chunk c1, seeds 8001-8010, BOTH seats
(10 seeds x 2 seats = 20 rows), taken verbatim from
gate_c1_raw_s1.jsonl and gate_c1_raw_s2.jsonl.

pregate_compare.py is then run with this file in all four slots
(native run1/run2, corrected run1/run2): determinism must read
identical on every compared field, and the script's own
seat control (seat-1 rows vs seat-2 rows of the same file) must
differ on gamelog_sha.

Usage: make_pregate_fixture_rows.py <round7 rows dir> <out file>
"""
import json
import sys


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = []
    for seat in (1, 2):
        for ln in open(f"{src}/gate_c1_raw_s{seat}.jsonl"):
            r = json.loads(ln)
            if 8001 <= int(r["seed"]) <= 8010:
                rows.append(r)
    rows.sort(key=lambda r: (int(r["seed"]), int(r["seat"])))
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
