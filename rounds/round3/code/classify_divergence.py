#!/usr/bin/env python3
"""First-divergence classifier (Claude round-2 design).

Aligns two per-decision trace files (same seed, two arms) by seq and
reports the FIRST row where any compared field differs, classified:

  STATE      - the state at the decision differs (bridge state_hash vs
               the other arm's state_hash / feat_pre_hash): a side
               effect between decisions, or divergent featurization
               input
  CANDIDATES - the ordered candidate list differs: lens fork
  DECISION   - state and candidates equal, the chosen index differs:
               decision rule (includes the eval-vs-pick endpoint fork;
               the row's priors_pre / feat_pre vs feat_post hashes say
               which component moved)
  RNG        - everything above equal at this row, but the RNG
               fingerprint differs: a consumer of the shared stream
               between the previous row and this one

(A BETWEEN class - arm B's zone_pre vs its own previous zone_post -
was in the first draft and was removed before this package shipped:
between two root decisions the engine legitimately moves the game
through dozens of untraced steps, so zone continuity across rows is
not expected and the check classified noise. The checkpoint question
it aimed at is answered inside each teacher row by feat_pre_hash vs
feat_post_hash.)

Usage: classify_divergence.py <traceA.jsonl> <traceB.jsonl>
Prints one JSON verdict line.
"""
import json
import sys


def load(path):
    rows = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    rows.sort(key=lambda r: r.get("seq", 0))
    return rows


def state_of(row):
    return row.get("feat_pre_hash") or row.get("state_hash")


def rng_of(row):
    return row.get("rng_pre") if "rng_pre" in row else row.get("rng")


def main():
    a_rows = load(sys.argv[1])
    b_rows = load(sys.argv[2])
    a = {r["seq"]: r for r in a_rows}
    b = {r["seq"]: r for r in b_rows}
    verdict = {"class": "IDENTICAL", "rows_a": len(a_rows),
               "rows_b": len(b_rows), "first_diff_seq": None}
    for seq in sorted(set(a) | set(b)):
        ra, rb = a.get(seq), b.get(seq)
        if ra is None or rb is None:
            verdict.update({"class": "MISSING_ROW", "first_diff_seq": seq,
                            "detail": "row present in one arm only"})
            break
        if state_of(ra) != state_of(rb):
            verdict.update({"class": "STATE", "first_diff_seq": seq,
                            "branch": rb.get("branch"),
                            "detail": {"a": state_of(ra), "b": state_of(rb),
                                       "b_feat_pre": rb.get("feat_pre_hash"),
                                       "b_feat_post": rb.get("feat_post_hash")}})
            break
        if ra.get("cand_hash") != rb.get("cand_hash"):
            verdict.update({"class": "CANDIDATES", "first_diff_seq": seq,
                            "branch": rb.get("branch"),
                            "detail": {"a_ncand": ra.get("ncand"),
                                       "b_ncand": rb.get("ncand")}})
            break
        if ra.get("chosen") != rb.get("chosen"):
            verdict.update({"class": "DECISION", "first_diff_seq": seq,
                            "branch": rb.get("branch"),
                            "detail": {"a_chosen": ra.get("chosen"),
                                       "b_chosen": rb.get("chosen"),
                                       "b_rule": rb.get("rule"),
                                       "b_feat_pre": rb.get("feat_pre_hash"),
                                       "b_feat_post": rb.get("feat_post_hash"),
                                       "b_priors_pre_top": (
                                           max(rb["priors_pre"])
                                           if rb.get("priors_pre") else None),
                                       "b_priors_post_top": (
                                           max(rb["priors_post"])
                                           if rb.get("priors_post") else None)}})
            break
        if rng_of(ra) != rng_of(rb):
            verdict.update({"class": "RNG", "first_diff_seq": seq,
                            "branch": rb.get("branch"),
                            "detail": {"a_rng": rng_of(ra), "b_rng": rng_of(rb)}})
            break
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
