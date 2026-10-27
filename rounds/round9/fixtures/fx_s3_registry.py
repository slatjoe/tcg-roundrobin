#!/usr/bin/env python3
"""fx_s3_registry: the REAL merge_registry.py under the
Stage 3 tag (round9-stage3), including a raw-RERUN block's
ids file in the merge set -- the runner merges ALL
games_*_ids.txt (teacher + raw + rerun) before the games
report, and the report's pairing counts are built from the
same driver files those ids came from (chain stated in
fx_stage3_games_report.py's docstring and asserted there:
pairs attempted == distinct (seed, seat) in the files).

Cases (fx_merge_registry pattern): (1) clean merge of
teacher + raw + rerun ids files: counts add, tag recorded,
printed sha256 == the merged file's sha256; (2) re-merge
of the same ids under the same tag: dup_same path, count
unchanged; (3) an id already registered under a DIFFERENT
tag: exit 1, registry byte-identical afterwards.
Run: python3 fx_s3_registry.py (own temp dirs)."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MERGE = os.path.join(HERE, "..", "code", "merge_registry.py")
FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    tmp = tempfile.mkdtemp(prefix="fx_s3reg_")
    reg_path = os.path.join(tmp, "registry.json")
    reg = {"created": "2026-10-27", "games": {"g_old": "round9-stage2"},
           "n_games": 1, "rule": "do-not-train", "version": 1}
    json.dump(reg, open(reg_path, "w"))
    ids = {}
    for name, lines in (
            ("games_t1a_ids.txt", ["g_t1\n", "g_t2\n"]),
            ("games_r1a_ids.txt", ["g_r1\n"]),
            ("games_r1a_rerun_ids.txt", ["g_rr1\n"])):
        p = os.path.join(tmp, name)
        with open(p, "w") as f:
            f.writelines(lines)
        ids[name] = p
    args = [sys.executable, MERGE, "--registry", reg_path,
            "--tag", "round9-stage3"]
    for p in ids.values():
        args += ["--ids", p]
    p = subprocess.run(args, capture_output=True, text=True)
    merged = json.load(open(reg_path))
    check("clean merge incl. rerun ids: +4, n_games 5, tag "
          "round9-stage3",
          p.returncode == 0 and merged["n_games"] == 5
          and merged["games"]["g_rr1"] == "round9-stage3"
          and "+4 new" in p.stdout,
          p.stdout.strip().splitlines()[0] if p.stdout else p.stderr)
    printed = [l for l in p.stdout.splitlines()
               if l.startswith("registry sha256:")]
    check("printed sha256 == merged file's sha256",
          printed and printed[0].split()[-1] == sha(reg_path))
    before = sha(reg_path)
    p = subprocess.run(args, capture_output=True, text=True)
    check("second merge of same ids: dup_same path, count "
          "unchanged",
          p.returncode == 0 and "+0 new" in p.stdout
          and json.load(open(reg_path))["n_games"] == 5
          and sha(reg_path) == before, p.stdout.strip()[:80])
    ids2 = os.path.join(tmp, "ids_conflict.txt")
    with open(ids2, "w") as f:
        f.write("g_old\n")
    p = subprocess.run(
        [sys.executable, MERGE, "--registry", reg_path,
         "--tag", "round9-stage3", "--ids", ids2],
        capture_output=True, text=True)
    check("conflicting-tag id: exit 1, registry unchanged",
          p.returncode == 1 and sha(reg_path) == before)
    print("FX-S3-REGISTRY: %s"
          % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
