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
    seen = set()
    dup = None
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                r = json.loads(ln)
                if r.get("seq") in seen and dup is None:
                    dup = r.get("seq")
                seen.add(r.get("seq"))
                rows.append(r)
    rows.sort(key=lambda r: r.get("seq", 0))
    return rows, dup


WITHIN_PAIRS = [("feat", "feat_pre_hash", "feat_post_hash"),
                ("zone", "zone_pre", "zone_post"),
                ("rng", "rng_pre", "rng_post")]


def within_row_diff(row):
    """No engine play happens between a teacher row's PRE and POST
    captures, so each pair must be equal. A difference convicts the
    checkpoint block or SimTeacher_Decide directly (round-3 R2)."""
    for name, pre, post in WITHIN_PAIRS:
        if row.get(pre) is not None and row.get(post) is not None \
                and row.get(pre) != row.get(post):
            return name
    return None


def state_of(row):
    return row.get("feat_pre_hash") or row.get("state_hash")


def rng_of(row):
    return row.get("rng_pre") if "rng_pre" in row else row.get("rng")


def main():
    a_rows, dup_a = load(sys.argv[1])
    b_rows, dup_b = load(sys.argv[2])
    a = {r["seq"]: r for r in a_rows}
    b = {r["seq"]: r for r in b_rows}
    # Two-part report (round-3 R8): EVERY within-row hit is listed,
    # and the cross-arm scan continues past them - one within-row
    # alarm must never hide a later cross-arm divergence.
    hits = []
    for seq in sorted(set(a) & set(b)):
        for side, r in (("A", a[seq]), ("B", b[seq])):
            wr = within_row_diff(r)
            if wr is not None:
                hits.append({"seq": seq, "side": side,
                             "branch": r.get("branch"), "pair": wr,
                             "rule": r.get("rule")})
    verdict = {"class": "IDENTICAL", "rows_a": len(a_rows),
               "rows_b": len(b_rows), "first_diff_seq": None,
               "within_row_hits": hits}
    if dup_a is not None or dup_b is not None:
        # A seq written twice (e.g. RootDecide logs a teacher row for
        # an eval-fallback null, then Choose falls through and logs a
        # bridge_pick row with the same seq) must fail loudly, not be
        # silently collapsed by the dict (round-3 R4).
        verdict.update({"class": "DUP_SEQ",
                        "first_diff_seq": dup_a if dup_a is not None else dup_b,
                        "detail": "duplicate seq in arm A" if dup_a is not None
                                  else "duplicate seq in arm B"})
        print(json.dumps(verdict))
        return
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
