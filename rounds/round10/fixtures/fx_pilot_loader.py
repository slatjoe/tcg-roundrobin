#!/usr/bin/env python3
"""Step 1 pilot fixture: STRICT job files + LOUD
loaders in every PHP job reader the package ships
(claude-reply-243b9d8 sec.3.5).

The package ships two PHP job readers:
  * s2_label_main.php -- byte-identical to the
    round-10 file whose loader fx_label_loader.py
    already covers (asserted byte-identical here);
  * s1_eval_main.php -- the round-9 form's loader
    silently dropped undecodable lines; the pilot's
    copy carries the loud form. This fixture lifts
    its load block VERBATIM from the pilot file and
    runs it under php:
      - a strict jobs file (incl. a z=999.0 sentinel
        job, the writer's real output shape) loads
        whole, count asserted;
      - a file whose line 2 is a bare-Infinity job
        (attempt 3's shape) aborts naming line 2.
Also: every Python writer in the package dumps with
allow_nan=False (source-checked), so a non-finite
value can never be serialized in the first place.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.abspath(os.path.join(HERE, ".."))
S1 = os.path.join(R10, "code", "step1")
PHP = os.path.expanduser(
    "~/workspace/tcg-sim/.tools/php83/usr/bin/php8.3")
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


def extract_loader(path):
    txt = open(path).read()
    i = txt.index("$jobs = [];")
    j = txt.index('foreach ($jobs as $j)')
    return txt[i:j]


def main():
    check("s2_label_main.php byte-identical to the "
          "round-10 file (fx_label_loader coverage)",
          sha(os.path.join(S1, "s2_label_main.php"))
          == sha(os.path.join(R10, "code",
                              "s2_label_main.php")))
    for f in ("build_pilot_jobs.py", "pilot_read.py",
              "pilot_games_report.py"):
        src = open(os.path.join(S1, f)).read()
        check("%s writes strict JSON "
              "(allow_nan=False present, no bare "
              "json.dumps to a file)" % f,
              "allow_nan=False" in src)
    block = extract_loader(os.path.join(
        S1, "s1_eval_main.php"))
    check("s1 loader block extracted verbatim "
          "(contains the loud abort)",
          "is not " in block and "valid JSON" in block
          and "line $lineNo" in block)
    harness = (
        "<?php\n"
        "function s1_abort($msg) { fwrite(STDERR, "
        "\"ABORT: $msg\\n\"); exit(2); }\n"
        "$jobsFile = $argv[1];\n"
        + block +
        "echo \"LOADED \" . count($jobs) . \"\\n\";\n")
    job = {"snap": "x_t1", "game": "g", "player": 1,
           "branch": "M",
           "setting": {"name": "L3-W50+H", "hooks": 8000,
                       "deadline_s": 180, "horizon": 62,
                       "horizon_value": -1, "k": 50},
           "z": 999.0, "z_nonfinite": True}
    with tempfile.TemporaryDirectory() as tmp:
        hp = os.path.join(tmp, "harness.php")
        open(hp, "w").write(harness)
        good = os.path.join(tmp, "jobs_good.jsonl")
        with open(good, "w") as f:
            f.write(json.dumps(job) + "\n")
            f.write(json.dumps(dict(job, snap="x_t2",
                                    z=1.5,
                                    z_nonfinite=False))
                    + "\n")
        r = subprocess.run([PHP, hp, good],
                           capture_output=True, text=True)
        check("strict jobs file loads whole (2 jobs)",
              r.returncode == 0 and "LOADED 2" in r.stdout,
              r.stderr[-200:] if r.returncode else "")
        bad = os.path.join(tmp, "jobs_bad.jsonl")
        with open(bad, "w") as f:
            f.write(json.dumps(job) + "\n")
            f.write('{"snap": "x_t3", "z": Infinity}\n')
        r = subprocess.run([PHP, hp, bad],
                           capture_output=True, text=True)
        check("bare-Infinity line aborts naming line 2",
              r.returncode == 2 and "line 2" in r.stderr,
              r.stderr.strip()[:160])
    print("fx_pilot_loader: %d checks, %d failed"
          % (checks, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
