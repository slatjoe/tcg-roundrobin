#!/usr/bin/env python3
"""Step 1 pilot fixture: pin guards for both pilot
runners (the fx_pin_guards.py pattern, extended to
the two-runner package).

For EACH of run_pilot.sh and run_pilot_pregate.sh:
  * the deploy list is parsed from the runner's own
    deployed_code_hashes recording loop (the list
    the runner deploys by, hence the parse source);
  * every file on that list carries an expect_hash
    call site in the same runner whose literal is
    64-hex AND equals the staged file's sha256;
  * every expect_hash literal in the runner that
    names a CODE_DIR file equals that file's sha256.
Plus package-level literal checks against
settings_pilot.json (the single source):
  * run_pilot.sh GAME_TIMEOUT == settings
    games.timeout_s; LABEL_BASE == label.seed_base;
  * the label invocation's EVAL_* literals == the
    settings label tuple (name/hooks/deadline/
    horizon/horizon_value/k);
  * the games blocks' seed strings == the settings
    games blocks; the pregate seeds == settings.
Negative case: a temporary copy of run_pilot.sh with
the pilot_read.py pin block removed must FAIL the
coverage check.
"""
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.abspath(os.path.join(HERE, "..", "code",
                                  "step1"))
fails = []
checks = 0


def check(name, good, detail=""):
    global checks
    checks += 1
    print("%s %s %s" % ("PASS" if good else "FAIL",
                        name, detail))
    if not good:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def parse_deploy_list(text):
    i = text.find(': > "$OUT/deployed_code_hashes.txt"')
    if i < 0:
        return None
    m = re.search(r"for f in (.*?); do\s*\n\s*sha256sum",
                  text[i:], re.S)
    if not m:
        return None
    return m.group(1).replace("\\", " ").split()


def pin_sites(text):
    out = {}
    for m in re.finditer(
            r'expect_hash "\$CODE_DIR/([A-Za-z0-9_.\-]+)"'
            r'\s*\\\s*\n\s*([0-9a-f]{64}|[^\s\\]+)',
            text):
        out[m.group(1)] = m.group(2)
    return out


def guard(text, label):
    dl = parse_deploy_list(text)
    check("%s deploy list parses" % label, dl is not None)
    if dl is None:
        return
    sites = pin_sites(text)
    for f in dl:
        if f.endswith(".sh"):
            # the two runner scripts are recorded in
            # deployed_code_hashes but carry no pin
            # site (a script does not hash-pin itself
            # or its sibling; the round-9 form)
            continue
        lit = sites.get(f)
        check("%s pin site %s" % (label, f),
              lit is not None and re.fullmatch(
                  r"[0-9a-f]{64}", lit or "") is not None
              and lit == sha(os.path.join(S1, f)),
              (lit or "MISSING")[:16])
    for f, lit in sites.items():
        if os.path.exists(os.path.join(S1, f)):
            check("%s pin value %s" % (label, f),
                  lit == sha(os.path.join(S1, f)))


def main():
    st = json.load(open(os.path.join(S1,
                                     "settings_pilot.json")))
    rp = open(os.path.join(S1, "run_pilot.sh")).read()
    rg = open(os.path.join(S1,
                           "run_pilot_pregate.sh")).read()
    guard(rp, "run_pilot.sh")
    guard(rg, "run_pilot_pregate.sh")

    m = re.search(r"^GAME_TIMEOUT=(\d+)$", rp, re.M)
    check("GAME_TIMEOUT == settings timeout_s",
          m and int(m.group(1)) == st["games"]["timeout_s"],
          m.group(1) if m else "missing")
    m = re.search(r"^LABEL_BASE=(\d+)$", rp, re.M)
    check("LABEL_BASE == settings label.seed_base",
          m and int(m.group(1)) == st["label"]["seed_base"])
    lt = st["label"]["tuple"]
    for env, want in (("EVAL_SETTING_NAME", lt["name"]),
                      ("EVAL_HOOKS", lt["hooks"]),
                      ("EVAL_DEADLINE_S", lt["deadline_s"]),
                      ("LABEL_HORIZON", lt["horizon"]),
                      ("EVAL_HORIZON_VALUE",
                       lt["horizon_value"]),
                      ("EVAL_K", lt["k"])):
        m = re.search(env + r"=(\S+)", rp)
        check("label env %s == settings tuple" % env,
              m and m.group(1) == str(want),
              m.group(1) if m else "missing")
    for blk in st["games"]["blocks"]:
        spec = '"%s %d %s"' % (blk["tag"], blk["seat"],
                               blk["seeds"])
        check("games block %s in runner" % blk["tag"],
              spec in rp, spec)
    check("pregate seeds in pregate runner",
          "--seeds 8601-8610" in rg
          and st["pregate"]["seeds"] == "8601-8610")

    # negative case: strip the pilot_read.py pin block
    neg = re.sub(r'expect_hash "\$CODE_DIR/pilot_read\.py"'
                 r'\s*\\\s*\n\s*[0-9a-f]{64}\s*\\\s*\n\s*'
                 r'"pilot_read\.py"\n', "", rp)
    sites = pin_sites(neg)
    check("negative copy: pilot_read.py pin coverage "
          "fails", "pilot_read.py" not in sites)

    print("fx_pilot_pins: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
