#!/usr/bin/env python3
"""shim_analyze_rows.py - the sec.2.3 fixture-1 filename/arm
mapping shim.

Maps round 7's published gate rows (rounds/round7/data/rows/,
gate_c{N}_{teacher,raw}_s{S}.jsonl - the same paired driver's
output) into the round-8 analysis's fleet layout
({raw,dist}_c{N}_s{S}.jsonl): teacher files become the "dist"
arm, raw files stay "raw". The ONLY field rewritten is a
teacher row's "arm" ("teacher" -> "raw"): the analysis collects
raw-arm driver rows (both gate arms play raw; the round-8
analysis filters on arm == "raw" exactly as it will on the real
fleet). No other field is touched.

Usage: shim_analyze_rows.py <round7 rows dir> <fleet out dir>
"""
import json
import os
import sys


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    n = 0
    for chunk in ("c1", "c2", "c3", "c4"):
        for seat in (1, 2):
            for arm_in, arm_out in (("teacher", "dist"),
                                    ("raw", "raw")):
                inp = os.path.join(
                    src, f"gate_{chunk}_{arm_in}_s{seat}.jsonl")
                outp = os.path.join(
                    dst, f"{arm_out}_{chunk}_s{seat}.jsonl")
                with open(inp) as fi, open(outp, "w") as fo:
                    for ln in fi:
                        if not ln.strip():
                            continue
                        r = json.loads(ln)
                        if arm_in == "teacher":
                            assert r["arm"] == "teacher"
                            r["arm"] = "raw"
                        fo.write(json.dumps(r) + "\n")
                        n += 1
    print(f"shim wrote {n} rows into {dst}")


if __name__ == "__main__":
    main()
