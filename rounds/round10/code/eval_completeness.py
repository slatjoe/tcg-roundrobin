#!/usr/bin/env python3
"""Round-10 Step 0 probe: EVAL COMPLETENESS ASSERTION
(fix pass 5, claude-reply-9dae0e2 sec.2.2).

The eval phase's loader (s1_eval_main.php) is the
round-9 pattern that keeps only lines that json_decode
to an array -- the same silent-drop shape that ate 10
label jobs in attempt 3. probe_eval_analyze.py has no
jobs-to-states count guard, so a dropped eval job line
would have vanished from the denominators of every
tail rate without a trace.

This assertion checks, FROM THE PUBLISHED FILES, that
every eval job produced world rows for every one of
its selected candidates:

  * eval job lines (jobs in the eval jobs file);
  * states with rows / states complete;
  * missing states -- jobs with at least one selected
    candidate carrying ZERO world rows (expected 0);
  * every (job, candidate) whose row count differs
    from the job's registered world count k
    (its setting's k; 25 for the probe's eval tuple);
  * the finished / unfinished / error split over all
    eval rows (the pipeline's own taxonomy,
    stage0_report.classify; refusal-class errors are
    broken out of the error count).

Exit code: 0 iff missing states == 0 AND no
(job, candidate) count differs from k; 2 otherwise.
The recovery script runs this on the box's files
BEFORE the label merge and aborts on a nonzero exit.

Usage: eval_completeness.py --eval-jobs eval_jobs.jsonl
  --evals evals_all.jsonl[.gz] [--json-out out.json]
"""
import argparse
import gzip
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def open_text(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-jobs", required=True)
    ap.add_argument("--evals", required=True)
    ap.add_argument("--json-out")
    a = ap.parse_args()

    s0 = load_mod("stage0_report")

    jobs = []
    with open(a.eval_jobs) as f:
        for l in f:
            if l.strip():
                jobs.append(json.loads(l))
    job_by_snap = {}
    for j in jobs:
        job_by_snap[str(j["snap"])] = j

    counts = Counter()
    split = Counter()
    unknown_snaps = 0
    unselected_rows = 0
    total_rows = 0
    with open_text(a.evals) as f:
        for l in f:
            if not l.strip():
                continue
            r = json.loads(l)
            total_rows += 1
            snap = str(r.get("snap"))
            cand = int(r["cand"])
            kind, _ = s0.classify(r.get("result"))
            split[kind] += 1
            if isinstance(r.get("result"), dict) \
                    and "error" in r["result"]:
                split["error_rows"] += 1
            j = job_by_snap.get(snap)
            if j is None:
                unknown_snaps += 1
                continue
            if cand not in [int(c) for c in j["selected"]]:
                unselected_rows += 1
                continue
            counts[(snap, cand)] += 1

    missing = []          # (snap, [candidates with 0 rows])
    anomalies = []        # (snap, cand, count, expected)
    states_any = 0
    states_complete = 0
    for j in jobs:
        snap = str(j["snap"])
        k = int(j["setting"]["k"])
        sel = [int(c) for c in j["selected"]]
        zero = [c for c in sel
                if counts.get((snap, c), 0) == 0]
        if zero:
            missing.append((snap, zero))
        elif any(counts.get((snap, c), 0) > 0 for c in sel):
            states_any += 1
        ok = True
        for c in sel:
            n = counts.get((snap, c), 0)
            if n != k:
                ok = False
                anomalies.append((snap, c, n, k))
        if ok:
            states_complete += 1

    out = {"eval_job_lines": len(jobs),
           "eval_rows": total_rows,
           "states_with_rows": states_any,
           "states_complete": states_complete,
           "missing_states": len(missing),
           "missing": [{"snap": s, "candidates": cs}
                       for s, cs in missing],
           "count_anomalies": [
               {"snap": s, "cand": c, "rows": n,
                "expected": k}
               for s, c, n, k in anomalies],
           "split": {"finished": split["finished"],
                     "unfinished": split["unfinished"],
                     "refusal": split["refusal"],
                     "error_rows": split["error_rows"]},
           "unknown_snap_rows": unknown_snaps,
           "unselected_candidate_rows": unselected_rows}

    lines = ["=== EVAL COMPLETENESS (fix pass 5, "
             "claude-reply-9dae0e2 sec.2.2) ==="]
    lines.append("eval job lines: %d" % out["eval_job_lines"])
    lines.append("eval rows: %d" % out["eval_rows"])
    lines.append("states with rows: %d" % states_any)
    lines.append("states complete (every selected "
                 "candidate at exactly k rows): %d"
                 % states_complete)
    lines.append("missing states: %d" % len(missing))
    for s, cs in missing:
        lines.append("  MISSING %s: selected candidate(s) "
                     "%s produced no world rows"
                     % (s, cs))
    lines.append("(job, candidate) row counts != k: %d"
                 % len(anomalies))
    for s, c, n, k in anomalies:
        lines.append("  COUNT %s cand %d: %d rows, "
                     "expected %d" % (s, c, n, k))
    lines.append("row split: finished %d, unfinished %d, "
                 "refusal %d (error rows %d)"
                 % (out["split"]["finished"],
                    out["split"]["unfinished"],
                    out["split"]["refusal"],
                    out["split"]["error_rows"]))
    lines.append("rows for unknown snaps: %d; rows for "
                 "unselected candidates: %d"
                 % (unknown_snaps, unselected_rows))
    clean = not missing and not anomalies
    lines.append("EVAL COMPLETENESS: %s"
                 % ("CLEAN" if clean else "NOT CLEAN"))
    print("\n".join(lines))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0 if clean else 2


if __name__ == "__main__":
    sys.exit(main())
