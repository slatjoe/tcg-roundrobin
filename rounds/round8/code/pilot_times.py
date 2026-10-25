#!/usr/bin/env python3
"""pilot_times.py - parse per-job label timings from the pilot's
label-main stderr logs ("done <snap> rows=N secs=S" lines, printed
by distill_label_main.php itself) into pilot_times.jsonl
({snap, run, secs}) for pilot_report.py.

Usage: pilot_times.py <out_dir> <run_a_errlog> <run_b_errlog>
(the run's two per-player invocations share one stderr log per run)
"""
import json
import re
import sys

pat = re.compile(r"^done (\S+) rows=(\d+) secs=([\d.]+)$")


def main():
    out_dir, log_a, log_b = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = []
    for run, path in (("A", log_a), ("B", log_b)):
        for ln in open(path, errors="replace"):
            m = pat.match(ln.strip())
            if m:
                rows.append({"snap": m.group(1), "run": run,
                             "secs": float(m.group(3))})
    with open(out_dir.rstrip("/") + "/pilot_times.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"timed job-runs: {len(rows)}")


if __name__ == "__main__":
    main()
