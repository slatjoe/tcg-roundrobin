#!/usr/bin/env python3
"""fx_merge_registry - known-answer fixture for
code/merge_registry.py (the standing registry discipline:
append-only, retag conflicts abort, atomic write + backup
+ vault copy, printed sha256 of the merged file).

Cases: (1) clean merge of 3 ids: n_games 1 -> 4, backup
file exists, vault copy exists, printed sha256 equals the
merged file's actual sha256; (2) re-merge of the same ids
under the same tag: 0 added, counted as already-present,
no error; (3) an id already registered under a DIFFERENT
tag: exit 1 with ABORT, and the registry file is byte-
identical afterwards (no partial write).
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MERGE = os.path.join(HERE, "..", "code", "merge_registry.py")
FAILS = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILS.append(name)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    tmp = tempfile.mkdtemp(prefix="fx_reg_")
    reg_path = os.path.join(tmp, "registry.json")
    reg = {"created": "2026-10-26", "games": {"g_old": "r7_fleet"},
           "n_games": 1, "rule": "do-not-train", "version": 1}
    with open(reg_path, "w") as f:
        json.dump(reg, f)
    ids_path = os.path.join(tmp, "ids.txt")
    with open(ids_path, "w") as f:
        f.write("g_a\ng_b\ng_c\n")
    vault = os.path.join(tmp, "vault")

    p = subprocess.run(
        [sys.executable, MERGE, "--registry", reg_path,
         "--tag", "r9s1_capture", "--ids", ids_path,
         "--vault", vault], capture_output=True, text=True)
    merged = json.load(open(reg_path))
    check("clean merge: +3, n_games 4, tag recorded",
          p.returncode == 0 and merged["n_games"] == 4
          and merged["games"]["g_a"] == "r9s1_capture",
          p.stdout.strip().splitlines()[0] if p.stdout else p.stderr)
    printed = [l for l in p.stdout.splitlines()
               if l.startswith("registry sha256:")]
    check("printed sha256 == merged file's sha256",
          printed and printed[0].split()[-1] == sha(reg_path))
    baks = [f for f in os.listdir(tmp) if f.startswith("registry.json.bak-")]
    check("backup written beside the registry", len(baks) == 1,
          str(baks))
    check("vault copy written",
          os.path.isdir(vault) and len(os.listdir(vault)) == 1)

    before = sha(reg_path)
    p = subprocess.run(
        [sys.executable, MERGE, "--registry", reg_path,
         "--tag", "r9s1_capture", "--ids", ids_path],
        capture_output=True, text=True)
    check("same-tag re-merge is a no-op (+0, sha stable)",
          p.returncode == 0 and "+0 new" in p.stdout
          and sha(reg_path) == before, p.stdout.strip()[:80])

    ids2 = os.path.join(tmp, "ids2.txt")
    with open(ids2, "w") as f:
        f.write("g_old\n")
    p = subprocess.run(
        [sys.executable, MERGE, "--registry", reg_path,
         "--tag", "r9s1_capture", "--ids", ids2],
        capture_output=True, text=True)
    check("retag conflict aborts (exit 1), registry unchanged",
          p.returncode == 1 and "ABORT" in p.stderr
          and sha(reg_path) == before,
          "rc=%d" % p.returncode)

    print("FX-MERGE-REGISTRY: %s"
          % ("ALL PASS" if not FAILS else "FAILURES: %s" % FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
