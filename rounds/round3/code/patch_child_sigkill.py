#!/usr/bin/env python3
"""Round-3 S1, extended to all rollout children (Claude: apply it in
the next commit anyway): every fork-child exit(0) in search.php
follows a result-file write; replace with death by SIGKILL so no
inherited shutdown handler or output buffer runs in the child (the
fingerprint-child version of this removed the gamelog pollution).
All 11 sites verified as fork children 2026-10-18. The main process
never calls exit(0) in search.php."""
import pathlib
import sys

p = pathlib.Path(sys.argv[1]) / "search.php"
s = p.read_text()
n = s.count("exit(0);")
assert n == 11, f"expected 11 child exit sites, found {n}"
s = s.replace("exit(0);",
              'if (function_exists("posix_kill")) '
              'posix_kill(posix_getpid(), 9); exit(0);')
p.write_text(s)
print(f"patch_child_sigkill: {n} child exits converted")
