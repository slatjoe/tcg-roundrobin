#!/usr/bin/env python3
"""Step 2+3 fleet ANCHOR: fleet_read.py --primary-only
reproduces round 9's PUBLISHED Stage 3 primary read,
from published data only (claude-reply-5b5ada4
non-blocking item 1: the anchor cited in the package
doc sec.7, committed as a fixture).

Inputs, all published: rounds/round9/data/stage3/
pairing.json + games_report.json + the four flat
search_stats_<blk>.jsonl files. The pairing's
stat_files already name the fleet layout
(games_<blk>_log/search_stats.jsonl); the published
Stage 3 tree stored those files flat, so this
fixture maps them into that layout inside a TEMP
dir (removed on exit) and runs the reader against
the copies. Nothing outside the temp dir is
written; no box file is touched.

Asserts (the values Claude's review reproduced
independently): the primary line +0.0475
[0.0000, 0.0950]; the verdict DOES NOT CONVERT;
the reconciliation recounts 37092 teacher stat
rows; the R14 root-canary class counts 8 records.
PASS lines are fixed strings (host-independent).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
STEP2 = os.path.join(R10, "code", "step2")
STAGE3 = os.path.normpath(os.path.join(
    R10, "..", "round9", "data", "stage3"))
BLOCKS = ("t1a", "t1b", "t2a", "t2b")

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def scrub(text, tmp):
    return text.replace(tmp, "<tmp>")


def main():
    tmp = tempfile.mkdtemp(prefix="fx_fleet_anchor_")
    try:
        for name in ("pairing.json", "games_report.json"):
            shutil.copyfile(os.path.join(STAGE3, name),
                            os.path.join(tmp, name))
        for blk in BLOCKS:
            logdir = os.path.join(tmp, "games_%s_log" % blk)
            os.makedirs(logdir)
            shutil.copyfile(
                os.path.join(STAGE3,
                             "search_stats_%s.jsonl" % blk),
                os.path.join(logdir, "search_stats.jsonl"))
        json_out = os.path.join(tmp, "fleet_read.json")
        proc = subprocess.run(
            [sys.executable,
             os.path.join(STEP2, "fleet_read.py"),
             "--pairing", os.path.join(tmp, "pairing.json"),
             "--games-report",
             os.path.join(tmp, "games_report.json"),
             "--settings",
             os.path.join(STEP2, "settings_fleet.json"),
             "--expect-pairs", "400",
             "--primary-only",
             "--json-out", json_out],
            capture_output=True, text=True, timeout=1200)
        txt = proc.stdout
        lines = txt.splitlines()
        check("ANCHOR fleet_read --primary-only exits 0 "
              "on the published Stage 3 inputs",
              proc.returncode == 0,
              "rc %s; tail: %s" % (
                  proc.returncode,
                  scrub((txt.strip().splitlines() or [""])[-1],
                        tmp)))
        prim = next((l for l in lines
                     if l.startswith("PRIMARY:")), "")
        check("ANCHOR primary reproduces Stage 3: mean "
              "paired diff +0.0475, CI [0.0000, 0.0950]",
              "mean paired diff 0.0475" in prim
              and "[0.0000, 0.0950]" in prim,
              "primary line: %s" % prim)
        check("ANCHOR verdict reproduces Stage 3: "
              "DOES NOT CONVERT",
              "VERDICT: DOES NOT CONVERT" in lines)
        out = {}
        if os.path.exists(json_out):
            out = json.load(open(json_out))
        rec = out.get("reconciliation") or {}
        check("ANCHOR reconciliation recounted 37092 "
              "teacher stat rows == games report",
              rec.get("teacher_stat_rows") == 37092
              and any("teacher stat rows 37092 == games "
                      "report" in l for l in lines),
              "reconciliation: %s" % (rec,))
        check("ANCHOR R14 root-canary refusal records "
              "counted by name: 8",
              rec.get("canary_refusal_rows") == 8
              and any("root-canary refusal records" in l
                      and ": 8 " in l for l in lines),
              "reconciliation: %s" % (rec,))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("ANCHOR temp dir removed on exit",
          not os.path.exists(tmp))


if __name__ == "__main__":
    main()
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
