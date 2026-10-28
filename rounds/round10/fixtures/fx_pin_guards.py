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

Second fix pass (claude-reply-af9e9f8 sec.2.2):
DEPLOY-LIST COVERAGE. The runner's deploy list is
parsed from the runner itself -- the `for f in ...;
do` loop that records deployed_code_hashes.txt is
the list the runner deploys by, so it is the parse
source -- and every file in it must carry an
expect_hash site in the header pins whose literal
equals the staged file's sha256. A NEGATIVE case
then writes a temporary copy of the runner with the
probe_report.py pin block removed and asserts the
guard FAILS on it, naming the coverage gap: a file
can no longer join the deploy list (or lose its
pin) unpinned without this fixture failing.
"""
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", "code"))
RUNNER_PATH = os.path.join(CODE, "run_probe.sh")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def deploy_list(text):
    """The runner's deploy list, parsed from the
    deployed_code_hashes.txt recording loop (the
    `for f in ...; do` whose body sha256sums
    $CODE_DIR/$f into the record)."""
    m = re.search(r"for f in (.*?); do\s*\n\s*sha256sum ",
                  text, re.S)
    if not m:
        return []
    return m.group(1).replace("\\", " ").split()


def collect(text, prefix=""):
    """Run every guard check against runner TEXT;
    returns the list of failed check names and
    prints each check line (with PREFIX, so the
    negative case's run is distinguishable in the
    transcript from the real runner's). Pure in its
    inputs so the negative case can run it against
    a mutilated copy."""
    fails = []

    def check(name, cond, extra=""):
        print("%s%s %s %s" % (prefix,
                              "PASS" if cond else "FAIL",
                              name, extra))
        if not cond:
            fails.append(name)

    # pin sites: expect_hash "$CODE_DIR/<file>" \ <nl> <hash>
    sites = re.findall(
        r'expect_hash "\$CODE_DIR/([A-Za-z0-9_.]+)" \\\n'
        r'\s+([0-9a-fA-F]+)', text)
    # tree-install sites: expect_hash "$tree/search.php" \ <hash>
    tree_sites = re.findall(
        r'expect_hash "\$tree/search\.php" \\\n\s+([0-9a-fA-F]+) \\\n'
        r'\s+"([^"]+)"', text)
    check("pin sites found", len(sites) >= 6, str(sites))
    for fname, lit in sites:
        ok_fmt = re.fullmatch(r"[0-9a-f]{64}", lit) is not None
        real = sha(os.path.join(CODE, fname))
        check("pin %s" % fname, ok_fmt and lit == real,
              "literal %s file %s" % (lit[:12], real[:12]))

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

    # deploy-list coverage (second fix pass): every
    # deployed file has a header pin site whose
    # literal equals the staged sha256.
    deploy = deploy_list(text)
    check("deploy list parsed from the recording loop",
          len(deploy) >= 10, "%d files" % len(deploy))
    pinned = {}
    for fname, lit in sites:
        pinned.setdefault(fname, set()).add(lit)
    for fname in deploy:
        real = sha(os.path.join(CODE, fname))
        check("deploy coverage: %s" % fname,
              real in pinned.get(fname, set()),
              "staged %s" % real[:12])

    st = json.load(open(os.path.join(CODE,
                                     "settings_probe.json")))
    for lit, key in (("30055001", st["eval"]["seed_base"]),
                     ("70055001", st["label"]["seed_base"])):
        check("seed literal %s in runner == settings %s"
              % (lit, key),
              ("$((%s + s * 100000000))" % lit) in text
              and int(lit) == key)
    check("capture seed strings in runner == settings",
          '"24001-24045 24046-24090"' in text
          and st["capture"]["seeds_seat1"] == "24001-24045"
          and st["capture"]["seeds_seat2"] == "24046-24090")
    check("uncontested sampling literal in settings",
          st["capture"]["uncontested_every"] == 2)
    return fails


def main():
    text = open(RUNNER_PATH).read()
    fails = collect(text)

    # negative case: a temporary copy of the runner
    # with the probe_report.py pin block removed must
    # FAIL the guard, on the coverage check naming
    # that file (the per-site checks alone cannot see
    # a missing site -- that is the gap sec.2.2
    # closes).
    pat = re.compile(
        r'expect_hash "\$CODE_DIR/probe_report\.py" \\\n'
        r'\s+[0-9a-f]{64} \\\n'
        r'\s+"[^"]*" \|\| exit 1\n')
    mut, n = pat.subn("", text)
    tmpd = tempfile.mkdtemp(prefix="fx_pin_neg_")
    mut_path = os.path.join(tmpd, "run_probe.sh")
    with open(mut_path, "w") as f:
        f.write(mut)
    neg_fails = (collect(open(mut_path).read(),
                         prefix="[negative copy] ")
                 if n == 1 else ["<pattern matched %d "
                                 "blocks>" % n])
    cov = [f for f in neg_fails
           if f == "deploy coverage: probe_report.py"]
    ok = n == 1 and len(cov) == 1
    print("%s negative: guard fails on a pin-stripped "
          "runner copy" % ("PASS" if ok else "FAIL"),
          "removed %d block(s); coverage failures on "
          "the copy: %s"
          % (n, [f for f in neg_fails
                 if f.startswith("deploy coverage")]))
    if not ok:
        fails.append("negative case")

    print("fx_pin_guards: %s"
          % ("ALL PASS" if not fails
             else "FAILURES: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
