#!/usr/bin/env python3
"""O-fleet DUP_SEQ reclassification (standing G3 rule, gate precedent).

gate_first_divergence.py flags a unit DUP_SEQ when a seq is written
twice in one arm's trace. In this fleet each flagged unit's duplicate
pair is: (1) the Decide-abort marker row - rule=teacher, abort_reason
set (the sec.7 abort patch stamps the reason on the marker),
decide_pick and chosen both null, i.e. the teacher made no pick -
and (2) its bridge_pick twin, the pick that actually played. The
standing reclassification removes ONLY the marker row from a copy of
the teacher trace and re-runs the stock classifier
(classify_divergence.py) on (raw trace, filtered teacher trace);
the wrapper's overturn test is then applied if the class is DECISION.

Read-only with respect to the fleet: filtered traces are written to
a scratch dir. Usage:
  o_dupseq_recheck.py CLASSIFIER_PATH SCRATCH_DIR \
      CHUNK SEAT SEED DUPSEQ [CHUNK SEAT SEED DUPSEQ ...]
Fleet layout is the O layout under /tmp/o_fleet.
"""
import json
import os
import subprocess
import sys

FLEET = "/tmp/o_fleet"


def load_rows(path):
    out = {}
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                r = json.loads(ln)
                out[r["seed"]] = r
    return out


def is_marker(r):
    return (r.get("rule") == "teacher"
            and r.get("abort_reason")
            and r.get("decide_pick") is None
            and r.get("chosen") is None)


def main():
    classifier, scratch = sys.argv[1], sys.argv[2]
    os.makedirs(scratch, exist_ok=True)
    units = []
    it = iter(sys.argv[3:])
    for chunk, seat, seed, dupseq in zip(it, it, it, it):
        units.append((int(chunk), int(seat), int(seed), int(dupseq)))
    n_legal = 0
    for chunk, seat, seed, dupseq in units:
        trows = load_rows(os.path.join(
            FLEET, "o_c%d_teacher_s%d.jsonl" % (chunk, seat)))
        rrows = load_rows(os.path.join(
            FLEET, "o_c%d_raw_s%d.jsonl" % (chunk, seat)))
        tgame = trows[seed]["gamename"]
        rgame = rrows[seed]["gamename"]
        tpath = os.path.join(FLEET, "o_c%d_teacher_s%d_log" % (chunk, seat),
                             "trace", "trace_%s.jsonl" % tgame)
        rpath = os.path.join(FLEET, "o_c%d_raw_s%d_log" % (chunk, seat),
                             "trace", "trace_%s.jsonl" % rgame)
        rows = [json.loads(ln) for ln in open(tpath) if ln.strip()]
        kept, removed = [], []
        for r in rows:
            if r.get("seq") == dupseq and is_marker(r):
                removed.append(r)
            else:
                kept.append(r)
        assert len(removed) == 1, (seed, "removed", len(removed))
        fpath = os.path.join(scratch, "trace_%s_filtered.jsonl" % tgame)
        with open(fpath, "w") as f:
            for r in kept:
                f.write(json.dumps(r) + "\n")
        p = subprocess.run([sys.executable, classifier, rpath, fpath],
                           capture_output=True, text=True)
        v = json.loads(p.stdout.strip().splitlines()[-1])
        cls, seq = v.get("class"), v.get("first_diff_seq")
        extra = ""
        legal = False
        if v.get("within_row_hits"):
            extra = " WITHIN_ROW_HITS=%d" % len(v["within_row_hits"])
        elif cls == "DECISION":
            by_seq = {r["seq"]: r for r in kept}
            tr = by_seq.get(seq, {})
            pr, dp = tr.get("priors_pre"), tr.get("decide_pick")
            if pr and dp is not None:
                am = max(range(len(pr)), key=lambda i: pr[i])
                legal = (am != dp)
                extra = " overturn_test: decide_pick=%s prior_argmax=%s" % (dp, am)
        if legal:
            n_legal += 1
        print("RECHECK seed=%d seat=%d game=%s removed=1 (abort_reason=%r) "
              "-> class=%s first_diff_seq=%s legal=%s%s"
              % (seed, seat, tgame, removed[0].get("abort_reason"),
                 cls, seq, legal, extra))
    print("recheck: %d/%d DUP_SEQ units reclassify LEGAL" % (n_legal, len(units)))
    return 0 if n_legal == len(units) else 1


if __name__ == "__main__":
    sys.exit(main())
