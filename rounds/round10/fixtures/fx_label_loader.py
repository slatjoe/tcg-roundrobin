#!/usr/bin/env python3
"""Round-10 Step 0 fixtures (FOURTH fix pass,
2026-10-29): the non-finite-z writer -> loader ->
analyzer round trip, and the loader's loud abort.

The attempt-3 defect, in one chain: the offline
eval emits z = +inf for a state whose paired diffs
are constant (se = 0); build_probe_jobs.py wrote
it with Python's json as the bare token Infinity
(INVALID JSON); s2_label_main.php's loader
json_decoded each line and silently kept only
array results, so 10 jobs (one invocation's lines
282-291 of jobs_all.jsonl) never loaded, their
worlds never ran, every later job in that
invocation labeled under a shifted seed base, and
the loss surfaced only downstream, as the label
analyzer's world-count guard abort.

These fixtures close the chain at both ends:

  * the WRITER's own output for an inf-z state
    (mean_diff 2.0, se_diff 0.0, fed as a state
    row in probe_eval_analyze's real shape) must
    be STRICT JSON on every line, carry the
    finite sentinel z = 999.0 + "z_nonfinite":
    true on that job (and no such field on finite
    jobs), in jobs_all AND in the shard files;
  * the PHP LOADER must load that file whole. The
    loader under test is a VERBATIM EXTRACTION of
    s2_label_main.php's jobs-load block (from
    "$jobs = [];" to the setting-audit loop),
    together with the file's own s1_abort, run
    under the local php8.3 -- the full driver
    needs the Talishar tree and a policy server,
    which is the box's job; the LOAD BLOCK is the
    code that dropped the jobs, and it is lifted
    byte for byte, never retyped;
  * the ANALYZER must band the sentinel job where
    +inf banded: inside class (a) and inside its
    z > 3.5 TAIL subset;
  * NEGATIVE: a jobs file carrying the attempt-3
    writer's REAL t64 line (data/step0/
    jobs_all.jsonl line 282, copied at runtime)
    must make the loader ABORT (exit 2), naming
    the line, and load nothing.

Every check prints PASS/FAIL; exit 1 on any FAIL.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.abspath(os.path.join(HERE, "..", "code"))
DATA = os.path.abspath(os.path.join(HERE, "..",
                                    "data", "step0"))
FAILS = []


def check(name, cond, extra=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL",
                        name, extra))
    if not cond:
        FAILS.append(name)


def run_py(args, expect_rc=0):
    p = subprocess.run([sys.executable] + args,
                       capture_output=True, text=True)
    if p.returncode != expect_rc:
        print(p.stdout[-2000:])
        print(p.stderr[-2000:])
    return p


def strict_loads(line):
    def boom(x):
        raise ValueError("non-strict constant %s" % x)
    return json.loads(line, parse_constant=boom)


def find_php():
    cands = [os.environ.get("PHP"),
             os.path.expanduser(
                 "~/workspace/tcg-sim/.tools/php83/"
                 "usr/bin/php8.3"),
             shutil.which("php"), shutil.which("php8.3")]
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="fx_loader_")
    settings = os.path.join(CODE, "settings_probe.json")
    LT = json.load(open(settings))["label"]["tuple"]

    # ---- writer: an inf-z state through the real build --------------
    def staterow(snap, game, z, unc, md=0.4, se=0.2):
        return {"snap": snap, "game": game, "player": 2,
                "branch": "M", "turn": 45,
                "uncontested": unc, "top_prior": 1.0,
                "prior_band": [0.97, 1.01], "z": z,
                "search_pick": 9, "prior_pick": 0,
                "mean_diff": md, "se_diff": se,
                "status": "ok"}

    states = [staterow("nF_t64", "nF", float("inf"), 1,
                       md=2.0, se=0.0),
              staterow("nG_t1", "nG", 2.0, 1),
              staterow("nH_t1", "nH", 1.4, 0)]
    statesf = os.path.join(tmp, "states.jsonl")
    with open(statesf, "w") as f:
        for r in states:
            # the eval's own serializer (plain
            # json.dumps) -- it emits the bare
            # Infinity token for the inf row, as
            # the production eval_states.jsonl did.
            f.write(json.dumps(r) + "\n")
    ejf = os.path.join(tmp, "eval_jobs.jsonl")
    with open(ejf, "w") as f:
        for r in states:
            f.write(json.dumps(
                {"snap": r["snap"],
                 "snap_dir": "d/" + r["snap"],
                 "cands": [{}, {}]}) + "\n")
    jobsf = os.path.join(tmp, "jobs_all.jsonl")
    jrep = os.path.join(tmp, "jobs_report.json")
    p = run_py([os.path.join(CODE, "build_probe_jobs.py"),
                "--states", statesf, "--eval-jobs", ejf,
                "--settings", settings, "--out", jobsf,
                "--shard-prefix",
                os.path.join(tmp, "jobs_shard"),
                "--report", jrep])
    check("N1: writer rc on an inf-z state", p.returncode == 0)
    raw = open(jobsf).read()
    ok_strict = True
    jobs = []
    for l in raw.splitlines():
        if l.strip():
            try:
                jobs.append(strict_loads(l))
            except ValueError:
                ok_strict = False
    check("N2: writer output is strict JSON, no bare "
          "Infinity/NaN tokens",
          ok_strict and "Infinity" not in raw
          and "NaN" not in raw)
    by_snap = {j["snap"]: j for j in jobs}
    nf = by_snap.get("nF_t64", {})
    check("N3: inf-z job carries sentinel z = 999.0 + "
          "z_nonfinite; finite jobs omit the field; "
          "report counts it",
          len(jobs) == 3
          and nf.get("z") == 999.0
          and nf.get("z_nonfinite") is True
          and nf.get("probe_band") == "uncontested"
          and "z_nonfinite" not in by_snap["nG_t1"]
          and "z_nonfinite" not in by_snap["nH_t1"]
          and json.load(open(jrep))["z_nonfinite_jobs"] == 1,
          "nF z=%s flag=%s" % (nf.get("z"),
                               nf.get("z_nonfinite")))
    shard_ok = True
    for s in range(4):
        sf = os.path.join(tmp, "jobs_shard%d.jsonl" % s)
        for l in open(sf):
            if l.strip():
                try:
                    strict_loads(l)
                except ValueError:
                    shard_ok = False
    check("N4: shard files are strict JSON too", shard_ok)

    # ---- PHP loader: verbatim extraction of the load block -----------
    php = find_php()
    check("N5: a php binary is available for the "
          "loader leg", php is not None, str(php))
    src = open(os.path.join(CODE, "s2_label_main.php")).read()
    m_abort = re.search(r"function s1_abort.*?\n\}",
                        src, re.S)
    i0 = src.find("$jobs = [];")
    i1 = src.find("foreach ($jobs as $j) {")
    block = src[i0:i1] if (i0 >= 0 and i1 > i0) else ""
    check("N6: extraction markers found; the lifted "
          "block is the FIXED loader (counted load)",
          m_abort is not None and i0 >= 0 and i1 > i0
          and "linesRead" in block
          and src.count("$jobs = [];") >= 1)
    harness = os.path.join(tmp, "loader_harness.php")
    with open(harness, "w") as f:
        f.write("<?php\n")
        f.write(m_abort.group(0) + "\n")
        f.write('$jobsFile = $argv[1];' + "\n")
        f.write(block)
        f.write('fwrite(STDERR, "LOADER-LOADED " . '
                'count($jobs) . "\\n");' + "\n")
        f.write('foreach ($jobs as $j) { echo $j["snap"]'
                ' . " z=" . json_encode($j["z"])'
                ' . (isset($j["z_nonfinite"])'
                ' ? " FLAGGED" : "") . "\\n"; }' + "\n")
    p = subprocess.run([php, harness, jobsf],
                       capture_output=True, text=True)
    check("N7: loader loads the writer's file whole "
          "(3 jobs, sentinel job present + flagged)",
          p.returncode == 0
          and "LOADER-LOADED 3" in p.stderr
          and "nF_t64" in p.stdout
          and "FLAGGED" in p.stdout
          and "999" in p.stdout,
          "rc=%d out=%s err=%s" % (p.returncode,
                                   p.stdout.strip(),
                                   p.stderr.strip()))

    # ---- analyzer: the sentinel bands in the tail ---------------------
    def fin(oc, winner=1):
        return {"outcome": oc, "winner": winner,
                "finished": 1, "horizon": 0,
                "errors": {}, "fallbacks": 0}

    lab = []
    for snap in ("nF_t64", "nG_t1", "nH_t1"):
        for w in range(50):
            lab.append({"snap": snap, "cand": 9,
                        "world": w, "pair": "va",
                        "setting": LT, "result": fin(1)})
            lab.append({"snap": snap, "cand": 0,
                        "world": w, "pair": "va",
                        "setting": LT, "result": fin(-1)})
    labf = os.path.join(tmp, "labels.jsonl")
    with open(labf, "w") as f:
        for r in lab:
            f.write(json.dumps(r) + "\n")
    capf = os.path.join(tmp, "capgames.json")
    json.dump({"games_list": ["nF", "nG", "nH"]},
              open(capf, "w"))
    lrf = os.path.join(tmp, "label_read.json")
    p = run_py([os.path.join(CODE, "probe_label_analyze.py"),
                "--jobs", jobsf, "--labels", labf,
                "--capture-games", capf,
                "--settings", settings,
                "--json-out", lrf])
    lr = json.load(open(lrf)) if p.returncode == 0 else {}
    bc = lr.get("by_class", {})
    check("N8: analyzer bands the sentinel job in "
          "class (a)'s TAIL (z > 3.5), the finite "
          "z = 2.0 job in class only",
          p.returncode == 0
          and bc.get("uncontested", {}).get("jobs") == 2
          and bc.get("uncontested_tail", {}).get("jobs") == 1
          and bc.get("contested_band", {}).get("jobs") == 1
          and lr.get("jobs_no_shared_worlds") == 0,
          str({k: v.get("jobs") for k, v in bc.items()}))

    # ---- negative: the attempt-3 writer's real t64 line ---------------
    lines = open(os.path.join(DATA, "jobs_all.jsonl")
                 ).read().splitlines()
    t64 = lines[281] if len(lines) > 281 else ""
    check("N9: the plant is attempt 3's real line 282 "
          "(snap 540261752_t64, bare Infinity)",
          "540261752_t64" in t64 and "Infinity" in t64)
    good = [l for l in raw.splitlines() if l.strip()]
    poisoned = os.path.join(tmp, "jobs_poisoned.jsonl")
    with open(poisoned, "w") as f:
        f.write(good[0] + "\n")
        f.write(t64 + "\n")
        f.write(good[1] + "\n")
    p = subprocess.run([php, harness, poisoned],
                       capture_output=True, text=True)
    check("N10: loader ABORTS on the bare-Infinity "
          "line, exit 2, naming the line; loads "
          "nothing",
          p.returncode == 2 and "ABORT" in p.stderr
          and "line 2" in p.stderr
          and "LOADER-LOADED" not in p.stderr,
          "rc=%d err=%s" % (p.returncode,
                             p.stderr.strip()
                             .replace(tmp, "<tmp>")[:160]))

    print("fx_label_loader: %s"
          % ("ALL PASS" if not FAILS else
             "FAILURES: %s" % FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
