#!/usr/bin/env python3
"""Find the engine's real global names for zones/life/chain/queue by
scanning ParseGamestate.php and WriteGamestate.php for assignments."""
import re

for fn in ("/tmp/gatetree/vendor/talishar/ParseGamestate.php",
           "/tmp/gatetree/vendor/talishar/WriteGamestate.php"):
    try:
        src = open(fn, errors="replace").read()
    except FileNotFoundError:
        print(fn, "MISSING")
        continue
    names = set()
    for m in re.finditer(r"\$GLOBALS\[['\"]([A-Za-z0-9_]+)['\"]\]\s*=", src):
        names.add(m.group(1))
    for m in re.finditer(r"^\s*\$([A-Za-z0-9_]+)\s*=", src, re.M):
        names.add(m.group(1))
    interesting = sorted(n for n in names if re.search(
        r"hand|deck|arsenal|char|item|allies|banish|graveyard|discard|"
        r"pitch|life|health|chain|layer|decision|turn|resource|action",
        n, re.I))
    print(fn.split("/")[-1], "assignments:", len(names))
    print("  ", ", ".join(interesting))
