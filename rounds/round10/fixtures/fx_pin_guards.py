#!/usr/bin/env python3
"""Round-10 Step 0 fixture: pin guards for run_probe.sh.

For every pin site in the runner (the header pins
block and the per-tree install assertions), assert:
  * the literal is exactly 64 lowercase hex chars
    (format guard);
  * it EQUALS the sha256 of the corresponding staged
    file in rounds/round10/code/ (machine-checked --
    a composed or stale literal fails here);
  * the two 8f7be190... sites for search_s3.php and
    the 85490e8e... sites for search_s2.php agree
    with each other.
Also assert the runner's seed literals equal
settings_probe.json (eval base 30055001, label base
70055001, strides 10^8) and that the capture seed
strings in the runner match the settings' blocks.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", "code"))
RUNNER = open(os.path.join(CODE, "run_probe.sh")).read()
FAILS = []


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, extra))
    if not cond:
        FAILS.append(name)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# pin sites: expect_hash "$CODE_DIR/<file>" \ <nl> <hash>
sites = re.findall(
    r'expect_hash "\$CODE_DIR/([A-Za-z0-9_.]+)" \\\n'
    r'\s+([0-9a-fA-F]+)', RUNNER)
# tree-install sites: expect_hash "$tree/search.php" \ <hash>
tree_sites = re.findall(
    r'expect_hash "\$tree/search\.php" \\\n\s+([0-9a-fA-F]+) \\\n'
    r'\s+"([^"]+)"', RUNNER)
check("pin sites found", len(sites) >= 6, str(sites))
for fname, lit in sites:
    ok_fmt = re.fullmatch(r"[0-9a-f]{64}", lit) is not None
    real = sha(os.path.join(CODE, fname))
    check("pin %s" % fname, ok_fmt and lit == real,
          "literal %s file %s" % (lit[:12], real[:12]))

expect_by_desc = {}
for lit, desc in tree_sites:
    expect_by_desc.setdefault(desc.split("(")[-1].rstrip(")"),
                              set()).add(lit)
s3 = sha(os.path.join(CODE, "search_s3.php"))
s2 = sha(os.path.join(CODE, "search_s2.php"))
n_tree_s3 = sum(1 for lit, d in tree_sites if lit == s3)
n_tree_s2 = sum(1 for lit, d in tree_sites if lit == s2)
check("tree pins: search_s3 at capture+eval installs",
      n_tree_s3 == 2, "found %d" % n_tree_s3)
check("tree pins: search_s2 at label installs",
      n_tree_s2 == 1, "found %d" % n_tree_s2)
bad = [d for lit, d in tree_sites if lit not in (s3, s2)]
check("tree pins: no other literals", not bad, str(bad))

st = json.load(open(os.path.join(CODE, "settings_probe.json")))
for lit, key in (("30055001", st["eval"]["seed_base"]),
                 ("70055001", st["label"]["seed_base"])):
    check("seed literal %s in runner == settings %s"
          % (lit, key),
          ("$((%s + s * 100000000))" % lit) in RUNNER
          and int(lit) == key)
check("capture seed strings in runner == settings",
      '"24001-24045 24046-24090"' in RUNNER
      and st["capture"]["seeds_seat1"] == "24001-24045"
      and st["capture"]["seeds_seat2"] == "24046-24090")
check("uncontested sampling literal in settings",
      st["capture"]["uncontested_every"] == 2)

print("fx_pin_guards: %s"
      % ("ALL PASS" if not FAILS else "FAILURES: %s" % FAILS))
sys.exit(1 if FAILS else 0)
