#!/usr/bin/env python3
"""Fixture test for classify_divergence.py — pure stdlib, runs in any
sandbox: python3 test_classify.py. Builds synthetic trace pairs, one
per verdict class, and asserts the classifier names each correctly."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(HERE, "classify_divergence.py")


def row(seq, **kw):
    r = {"seq": seq, "branch": "M", "player": 1, "state_hash": "s%d" % seq,
         "cand_hash": "c%d" % seq, "ncand": 4, "chosen": 0,
         "rule": "bridge_pick", "rng": 1000 + seq}
    r.update(kw)
    return r


def trow(seq, **kw):
    """Teacher-shaped row: feat_pre_hash stands in for state_hash.
    Within-row pairs are EQUAL by default: no engine play happens
    between PRE and POST (round-3 R2 fixture fix - the first draft
    set zone_post = z(seq+1), encoding a change as normal)."""
    r = row(seq, state_hash=None, feat_pre_hash="s%d" % seq,
            feat_post_hash="s%d" % seq, zone_pre="z%d" % seq,
            zone_post="z%d" % seq, rng_pre=1000 + seq,
            rng_post=1000 + seq,
            priors_pre=[0.9, 0.1], priors_post=[0.9, 0.1],
            rule="ghost_prior")
    r.update(kw)
    return r


def run(rows_a, rows_b):
    with tempfile.TemporaryDirectory() as d:
        pa, pb = os.path.join(d, "a.jsonl"), os.path.join(d, "b.jsonl")
        with open(pa, "w") as f:
            for r in rows_a:
                f.write(json.dumps(r) + "\n")
        with open(pb, "w") as f:
            for r in rows_b:
                f.write(json.dumps(r) + "\n")
        out = subprocess.run([sys.executable, CLASSIFIER, pa, pb],
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout.strip())


def main():
    base = [row(i) for i in range(5)]
    tbase = [trow(i) for i in range(5)]

    v = run(base, [dict(r) for r in base])
    assert v["class"] == "IDENTICAL", v

    b = [trow(i) for i in range(5)]
    # Internally consistent (pre == post) but different from arm A:
    # WITHIN_ROW must NOT fire; this is a cross-arm STATE divergence.
    b[2] = trow(2, feat_pre_hash="DIFFERENT", feat_post_hash="DIFFERENT")
    v = run(base, b)
    assert v["class"] == "STATE" and v["first_diff_seq"] == 2, v

    b = [trow(i) for i in range(5)]
    b[3] = trow(3, cand_hash="OTHER", ncand=7)
    v = run(base, b)
    assert v["class"] == "CANDIDATES" and v["first_diff_seq"] == 3, v

    b = [trow(i) for i in range(5)]
    b[1] = trow(1, chosen=2)
    v = run(base, b)
    assert v["class"] == "DECISION" and v["first_diff_seq"] == 1, v

    b = [trow(i) for i in range(5)]
    # Internally consistent (pre == post), different stream position
    # than arm A: a cross-arm RNG divergence, not a within-row one.
    b[4] = trow(4, rng_pre=99999, rng_post=99999)
    v = run(base, b)
    assert v["class"] == "RNG" and v["first_diff_seq"] == 4, v

    v = run(base, tbase[:3])
    assert v["class"] == "MISSING_ROW", v

    for pair, kw in (("feat", {"feat_post_hash": "MUTATED"}),
                     ("zone", {"zone_post": "MUTATED"}),
                     ("rng", {"rng_post": 424242})):
        b = [trow(i) for i in range(5)]
        b[2] = trow(2, **kw)
        v = run(base, b)
        # Two-part report (R8): the hit is LISTED, and the cross-arm
        # verdict still scans past it (IDENTICAL here).
        assert v["class"] == "IDENTICAL", v
        assert len(v["within_row_hits"]) == 1, v
        h = v["within_row_hits"][0]
        assert h["seq"] == 2 and h["pair"] == pair, v

    b = [trow(i) for i in range(5)] + [trow(2)]
    v = run(base, b)
    assert v["class"] == "DUP_SEQ" and v["first_diff_seq"] == 2, v

    # R8 pass fixture: a within-row hit at seq 1 AND a cross-arm
    # DECISION at seq 3 - BOTH must be reported.
    a = [trow(i) for i in range(5)]
    b = [trow(i) for i in range(5)]
    b[1] = trow(1, zone_post="MUTATED")
    b[3] = trow(3, chosen=1)
    v = run(a, b)
    assert len(v["within_row_hits"]) == 1 \
        and v["within_row_hits"][0]["seq"] == 1, v
    assert v["class"] == "DECISION" and v["first_diff_seq"] == 3, v

    print("test_classify: 11/11 fixtures pass "
          "(IDENTICAL, STATE, CANDIDATES, DECISION, RNG, MISSING_ROW, "
          "WITHIN_ROW x3, DUP_SEQ, R8-both-reported)")


if __name__ == "__main__":
    main()
