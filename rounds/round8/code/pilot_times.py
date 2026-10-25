#!/usr/bin/env python3
"""pilot_times.py - aggregate the pilot label runs' per-candidate
timing sidecars (written by distill_label_main.php in
DISTILL_SPLIT_CANDS mode, one row per (snap, candidate) batch:
{snap, cand, secs, worlds, finished, timeout_errs}) into:

  pilot_times.jsonl      one row per job-run: {snap, run, secs}
                         (the job's secs = the sum of its
                         candidate batches' secs)
  pilot_cand_times.jsonl every candidate row, tagged with its
                         run - the deadline accounting's input
                         (pilot_report.py reads it)

Usage: pilot_times.py <out_dir> <run=timings_path> [...]
  e.g. pilot_times.py $OUT v1a=$OUT/timings_v1a.jsonl \
       v1b=$OUT/timings_v1b.jsonl v2=$OUT/timings_v2.jsonl
"""
import json
import sys


def main():
    out_dir = sys.argv[1].rstrip("/")
    job_rows, cand_rows = [], []
    for spec in sys.argv[2:]:
        run, path = spec.split("=", 1)
        per_job = {}
        for ln in open(path):
            if not ln.strip():
                continue
            r = json.loads(ln)
            r["run"] = run
            cand_rows.append(r)
            per_job[r["snap"]] = per_job.get(r["snap"], 0.0) + r["secs"]
        for snap, secs in sorted(per_job.items()):
            job_rows.append({"snap": snap, "run": run,
                             "secs": round(secs, 2)})
    with open(out_dir + "/pilot_times.jsonl", "w") as f:
        for r in job_rows:
            f.write(json.dumps(r) + "\n")
    with open(out_dir + "/pilot_cand_times.jsonl", "w") as f:
        for r in cand_rows:
            f.write(json.dumps(r) + "\n")
    print(f"timed job-runs: {len(job_rows)}; "
          f"candidate batches: {len(cand_rows)}")


if __name__ == "__main__":
    main()
