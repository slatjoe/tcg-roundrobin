#!/usr/bin/env python3
"""G3 checker: the first divergence of a differing pair must be an
overturn (Claude G3, round-3 gate registration).

The pre-gate proved the teacher machinery in ghost mode is raw v15
decision-for-decision. So in the gate, for every (seed, seat) unit
whose teacher and raw games DIFFER, the first trace divergence
must be a DECISION at a teacher trace row that is an overturn -
decide_pick != argmax(priors_pre), equivalently the teacher played
a pick other than the prior pick. Any other first divergence
(STATE, CANDIDATES, RNG, WITHIN_ROW, MISSING_ROW, DUP_SEQ, a
DECISION at a non-overturn row, or games that differ while their
traces classify IDENTICAL) is a MACHINERY DEFECT and stops the
read. Units whose games are action-identical are clean; units
with an invalid row on either side are skipped and counted (the
analysis scores those; this checker judges machinery only).

Usage:
  gate_first_divergence.py \
    --unit TEACHER_ROWS RAW_ROWS TEACHER_LOGDIR RAW_LOGDIR \
    [--unit ...]
Traces are <logdir>/trace/trace_<gamename>.jsonl, aligned by the
classifier (classify_divergence.py sits beside this script).
Exit 0 when no defect is found, 1 otherwise.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(HERE, "classify_divergence.py")
OUTCOME_FIELDS = ("winner", "turns", "decisions", "p1life", "p2life",
                  "gamestate_norm_sha")


def load_rows(path):
    out = {}
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                r = json.loads(ln)
                out[r["seed"]] = r
    return out


def load_trace(path):
    rows = {}
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                r = json.loads(ln)
                rows[r["seq"]] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", action="append", nargs=4, required=True,
                    metavar=("TEACHER_ROWS", "RAW_ROWS",
                             "TEACHER_LOGDIR", "RAW_LOGDIR"))
    a = ap.parse_args()
    identical = 0
    legal = 0
    skipped = 0
    defects = []
    for trows_p, rrows_p, tlog, rlog in a.unit:
        trows = load_rows(trows_p)
        rrows = load_rows(rrows_p)
        for seed in sorted(set(trows) & set(rrows)):
            t, r = trows[seed], rrows[seed]
            seat = t.get("seat")
            if t.get("invalid") or r.get("invalid"):
                skipped += 1
                continue
            differ = (t.get("gamelog_sha") != r.get("gamelog_sha")
                      or any(t.get(k) != r.get(k)
                             for k in OUTCOME_FIELDS))
            if not differ:
                identical += 1
                continue
            tpath = os.path.join(tlog, "trace",
                                 "trace_%s.jsonl" % t.get("gamename"))
            rpath = os.path.join(rlog, "trace",
                                 "trace_%s.jsonl" % r.get("gamename"))
            if not (os.path.exists(tpath) and os.path.exists(rpath)):
                defects.append((seed, seat, None, "TRACE_MISSING"))
                print("MACHINERY_DEFECT seed=%s seat=%s seq=None "
                      "class=TRACE_MISSING" % (seed, seat))
                continue
            p = subprocess.run([sys.executable, CLASSIFIER,
                                rpath, tpath],
                               capture_output=True, text=True)
            try:
                v = json.loads(p.stdout.strip().splitlines()[-1])
            except Exception:
                defects.append((seed, seat, None, "CLASSIFIER_ERROR"))
                print("MACHINERY_DEFECT seed=%s seat=%s seq=None "
                      "class=CLASSIFIER_ERROR (%s)"
                      % (seed, seat, p.stdout[:120] + p.stderr[:120]))
                continue
            if v.get("within_row_hits"):
                h = v["within_row_hits"][0]
                defects.append((seed, seat, h.get("seq"), "WITHIN_ROW"))
                print("MACHINERY_DEFECT seed=%s seat=%s seq=%s "
                      "class=WITHIN_ROW pair=%s branch=%s"
                      % (seed, seat, h.get("seq"), h.get("pair"),
                         h.get("branch")))
                continue
            cls = v.get("class")
            seq = v.get("first_diff_seq")
            if cls == "DECISION":
                trows_by_seq = load_trace(tpath)
                tr = trows_by_seq.get(seq, {})
                pr = tr.get("priors_pre")
                dp = tr.get("decide_pick")
                is_overturn = (pr and dp is not None
                               and max(range(len(pr)),
                                       key=lambda i: pr[i]) != dp)
                if is_overturn:
                    legal += 1
                    print("LEGAL seed=%s seat=%s seq=%s class=DECISION "
                          "overturn (decide_pick=%s, prior argmax=%s)"
                          % (seed, seat, seq, dp,
                             max(range(len(pr)), key=lambda i: pr[i])))
                else:
                    defects.append((seed, seat, seq,
                                    "DECISION_NOT_OVERTURN"))
                    print("MACHINERY_DEFECT seed=%s seat=%s seq=%s "
                          "class=DECISION_NOT_OVERTURN rule=%s"
                          % (seed, seat, seq, tr.get("rule")))
            elif cls == "IDENTICAL":
                defects.append((seed, seat, None, "TRACE_GAP"))
                print("MACHINERY_DEFECT seed=%s seat=%s seq=None "
                      "class=TRACE_GAP (games differ, traces "
                      "identical)" % (seed, seat))
            else:
                defects.append((seed, seat, seq, cls))
                print("MACHINERY_DEFECT seed=%s seat=%s seq=%s "
                      "class=%s" % (seed, seat, seq, cls))
    print("units identical=%d legal_diverged=%d skipped_invalid=%d "
          "defects=%d" % (identical, legal, skipped, len(defects)))
    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
