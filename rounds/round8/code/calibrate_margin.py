#!/usr/bin/env python3
"""calibrate_margin.py - round-8 option-2 margin calibration
(Joe's choice, 2026-10-25; protocol registered in
claude-reply-0140eab sec.2 BEFORE anything was computed).

A pure recomputation over the W=100 V1 check's two shipped label
files (rounds/round8/wcheck-report.md). No new labels, no games.

LABEL FIELDS USED (label_reduce.py's output schema): per state
and run, the row carries "candidates" (the selected set),
"prior_pick", per-candidate finished-world "means",
"paired_n" / "mean_diff" / "se_diff" (the paired stats of the
best-mean candidate vs the prior; null exactly when the best
candidate IS the prior, or paired_n < 20 with the stats left
null by the reducer), "teacher_pick" and "overturn" (the
shipped decision at the registered margin 1.5).

The tested candidate ("best") is not a stored field when the
test did not fire; it is recovered by the reducer's own scan:
ascending over "candidates", strict >, starting from the
prior's mean. The pair stats stored on the row are the
recovered best's by construction (the reducer computes paired
stats for no other candidate). The built-in fixture below
proves the recovery on every row of both files.

DECISION AT MARGIN m (everything else in the registered rule
unchanged): overturn(m) iff best != prior AND paired_n >= 20
AND mean_diff > m * se_diff; the pick at m is best on an
overturn, the prior otherwise.

V1 COUNTING mirrors pilot_report.py's V1 block (and
run_w_check.sh's read), parameterized by m, over a state set S:
  V1-ov(m)   = |{s in S: A overturns at m AND B overturns at m
               to the SAME candidate}| / |{s in S: A overturns
               at m}|
  V1-conf(m) = |{s in S: A confirms at m AND B confirms at m
               with the same pick}| / |{s in S: A confirms at m}|
Wilson intervals: pilot_report.wilson, imported (as
run_w_check.sh imported it).

POPULATION: the states labeled in BOTH runs (thin in either
run excluded - 544 states for the W=100 check).

SPLIT (registered; reproduce exactly): group the population by
game (the label rows' "game" field - the game id embedded in
the snapshot id, "<game>_t<n>"); sort the unique game ids as
strings (Python's default sort; the ids are all 9-digit, so
lexicographic == numeric here); shuffle the sorted list with
random.Random(20261025).shuffle; the first ceil(n_games/2)
games are H1, the rest H2. A state's half is its game's half.

SELECTION (H1 only): the smallest m in {1.5, 2.0, 2.5, 3.0}
with V1-ov_H1(m) >= 0.60. VERIFICATION (H2 only): V1-ov_H2(m*)
>= 0.50, printed with its Wilson interval. No H1 qualifier, or
an H2 miss, closes the line (option 3).

REPORT-ONLY, per m on the full set and both halves: A's
overturn rate, V1-ov, V1-conf, and the winner's-curse read
(A->B): over A's overturn-at-m states, the mean of B's
per-candidate-mean advantage for A's overturned pick,
means_B[pick] - means_B[prior] ("the mean advantage of the
overturned pick under the other run's means",
claude-reply-0140eab sec.2); a secondary paired variant (the
mean of B's stored mean_diff over the A-overturn states where
B's tested candidate is A's pick) is printed alongside, with
its coverage count.

FIXTURE (mandatory self-test, runs first, aborts loudly): at
m = 1.5 the recomputation must reproduce the check's shipped
decision on EVERY row of both files (overturn flag and
teacher_pick), and the full-set reads must equal the check's
exactly: A overturns 66, V1-ov 29/66, V1-conf 442/478.
"""
import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pilot_report import wilson  # the pilot's arithmetic

GRID = [1.5, 2.0, 2.5, 3.0]
SPLIT_SEED = 20261025
H1_BAR = 0.60
H2_BAR = 0.50
FIXTURE_EXPECT = {"A_overturns": 66, "V1-ov": (29, 66),
                  "V1-conf": (442, 478)}


def load(path):
    return [json.loads(ln) for ln in open(path) if ln.strip()]


def best_candidate(row):
    """The reducer's best scan (label_reduce.py): ascending
    over the selected set, strict >, from the prior."""
    sel = [int(x) for x in row["candidates"]]
    prior = int(row["prior_pick"])
    means = row["means"]
    best_mean = means[str(prior)]
    assert best_mean is not None, \
        f"prior mean null on a label row: {row['state_id']}"
    best = prior
    for ci in sel:
        v = means[str(ci)]
        if v is not None and v > best_mean:
            best_mean = v
            best = ci
    return best


def decide_at(row, m):
    """(overturn, pick) for one run's label row at margin m."""
    prior = int(row["prior_pick"])
    best = best_candidate(row)
    if best == prior:
        return (False, prior)
    pn = row["paired_n"]
    md = row["mean_diff"]
    se = row["se_diff"]
    if pn is None or pn < 20 or md is None or se is None:
        return (False, prior)
    if md > m * se:
        return (True, best)
    return (False, prior)


def v1(A, B, states, m):
    """The pilot's V1 counting, parameterized by margin m."""
    a_ov, ov_same, a_cf, cf_same = [], 0, [], 0
    for s in states:
        a_ov_flag, a_pick = decide_at(A[s], m)
        b_ov_flag, b_pick = decide_at(B[s], m)
        if a_ov_flag:
            a_ov.append(s)
            if b_ov_flag and b_pick == a_pick:
                ov_same += 1
        else:
            a_cf.append(s)
            if not b_ov_flag and b_pick == a_pick:
                cf_same += 1
    return {"a_ov": a_ov, "ov_same": ov_same,
            "a_cf": a_cf, "cf_same": cf_same}


def rate(k, n):
    if n == 0:
        return {"k": k, "n": n, "rate": None, "wilson95": None}
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n, "wilson95": [lo, hi]}


def curse_reads(A, B, a_ov_states, m):
    """Winner's-curse reads, A->B direction, over A's
    overturn-at-m states. Primary: B's per-candidate-mean
    advantage for A's pick. Secondary (paired): B's stored
    mean_diff where B's tested candidate is A's pick."""
    prim, prim_missing = [], 0
    sec, sec_states = [], 0
    for s in a_ov_states:
        _, a_pick = decide_at(A[s], m)
        brow = B[s]
        mb = brow["means"].get(str(a_pick))
        mp = brow["means"].get(str(int(brow["prior_pick"])))
        if mb is None or mp is None:
            prim_missing += 1
        else:
            prim.append(mb - mp)
        if best_candidate(brow) == a_pick \
                and brow["mean_diff"] is not None:
            sec.append(brow["mean_diff"])
            sec_states += 1
    return {
        "primary_mean_adv_B_means":
            (sum(prim) / len(prim)) if prim else None,
        "primary_states": len(prim),
        "primary_missing": prim_missing,
        "secondary_mean_B_mean_diff_paired":
            (sum(sec) / len(sec)) if sec else None,
        "secondary_states": sec_states,
    }


def set_reads(A, B, states, m):
    v = v1(A, B, states, m)
    return {
        "states": len(states),
        "A_overturn_rate": rate(len(v["a_ov"]), len(states)),
        "V1-ov": rate(v["ov_same"], len(v["a_ov"])),
        "V1-conf": rate(v["cf_same"], len(v["a_cf"])),
        "curse_A_to_B": curse_reads(A, B, v["a_ov"], m),
    }


def fmt_rate(r):
    if r["rate"] is None:
        return f"{r['k']}/{r['n']} = n/a"
    lo, hi = r["wilson95"]
    return (f"{r['k']}/{r['n']} = {r['rate']:.3f} "
            f"Wilson95 [{lo:.3f}, {hi:.3f}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels-a", required=True)
    ap.add_argument("--labels-b", required=True)
    ap.add_argument("--thin-a", required=True)
    ap.add_argument("--thin-b", required=True)
    ap.add_argument("--fixture-out", required=True)
    ap.add_argument("--results-out", required=True)
    a = ap.parse_args()

    A = {r["state_id"]: r for r in load(a.labels_a)}
    B = {r["state_id"]: r for r in load(a.labels_b)}
    thin_a = load(a.thin_a)
    thin_b = load(a.thin_b)
    for tag, S in (("a", A), ("b", B)):
        ws = {r.get("W") for r in S.values()}
        assert ws == {100}, f"labels {tag} W set {ws} != {{100}}"

    both = sorted(set(A) & set(B))
    a_only = sorted(set(A) - set(B))
    b_only = sorted(set(B) - set(A))

    # ---- fixture: per-row decision agreement at m = 1.5 ----
    fx = []
    fx.append("CALIBRATION FIXTURE - m=1.5 reproduction of the "
              "W=100 check's shipped reads")
    fx.append("")
    bad = 0
    for tag, S in (("A", A), ("B", B)):
        agree = 0
        for s, row in S.items():
            ov, pick = decide_at(row, 1.5)
            if ov == (row["overturn"] == 1) \
                    and pick == int(row["teacher_pick"]):
                agree += 1
            else:
                bad += 1
                fx.append(f"  MISMATCH {tag} {s}: recomputed "
                          f"(overturn={int(ov)}, pick={pick}) vs "
                          f"shipped (overturn={row['overturn']}, "
                          f"pick={row['teacher_pick']})")
        fx.append(f"run {tag}: per-row decision agreement at "
                  f"m=1.5: {agree}/{len(S)}")
    full15 = v1(A, B, both, 1.5)
    got = {"A_overturns": len(full15["a_ov"]),
           "V1-ov": (full15["ov_same"], len(full15["a_ov"])),
           "V1-conf": (full15["cf_same"], len(full15["a_cf"]))}
    fx.append(f"full-set ({len(both)} states) at m=1.5: "
              f"A overturns {got['A_overturns']} "
              f"(expected {FIXTURE_EXPECT['A_overturns']}); "
              f"V1-ov {got['V1-ov'][0]}/{got['V1-ov'][1]} "
              f"(expected {FIXTURE_EXPECT['V1-ov'][0]}/"
              f"{FIXTURE_EXPECT['V1-ov'][1]}); "
              f"V1-conf {got['V1-conf'][0]}/{got['V1-conf'][1]} "
              f"(expected {FIXTURE_EXPECT['V1-conf'][0]}/"
              f"{FIXTURE_EXPECT['V1-conf'][1]})")
    fixture_ok = (bad == 0 and got == FIXTURE_EXPECT)
    fx.append("FIXTURE: " + ("PASS - the m=1.5 recomputation "
              "reproduces the check's reads exactly"
              if fixture_ok else
              "FAIL - discrepancy above; NOTHING downstream of "
              "this line is a calibration result"))
    with open(a.fixture_out, "w") as f:
        f.write("\n".join(fx) + "\n")
    print("\n".join(fx))
    if not fixture_ok:
        print("ABORT: fixture failed - stopping before any "
              "calibration computation", file=sys.stderr)
        sys.exit(2)

    # ---- the split (registered algorithm) -------------------
    games = sorted({A[s]["game"] for s in both})
    order = list(games)
    random.Random(SPLIT_SEED).shuffle(order)
    n_h1 = math.ceil(len(order) / 2)
    h1_games, h2_games = order[:n_h1], order[n_h1:]
    h1 = [s for s in both if A[s]["game"] in set(h1_games)]
    h2 = [s for s in both if A[s]["game"] in set(h2_games)]
    assert len(h1) + len(h2) == len(both)

    # ---- the grid -------------------------------------------
    table = {}
    for m in GRID:
        table[str(m)] = {
            "full": set_reads(A, B, both, m),
            "H1": set_reads(A, B, h1, m),
            "H2": set_reads(A, B, h2, m),
        }

    # ---- selection + verification ---------------------------
    m_star = None
    for m in GRID:
        r = table[str(m)]["H1"]["V1-ov"]
        if r["rate"] is not None and r["rate"] >= H1_BAR:
            m_star = m
            break
    outcome = None
    ver = None
    if m_star is None:
        outcome = ("CLOSE - no margin in the grid reaches "
                   f"V1-ov >= {H1_BAR} on H1; the distillation "
                   "line closes (option 3)")
    else:
        ver = table[str(m_star)]["H2"]["V1-ov"]
        if ver["rate"] is not None and ver["rate"] >= H2_BAR:
            outcome = (f"PASS - m* = {m_star} qualifies on H1 "
                       f"and verifies on H2 (V1-ov >= {H2_BAR}); "
                       f"the corpus may be proposed at W=100 "
                       f"with margin m* = {m_star}")
        else:
            outcome = (f"CLOSE - m* = {m_star} qualified on H1 "
                       f"but the H2 verification missed "
                       f"(V1-ov < {H2_BAR} or undefined); the "
                       "distillation line closes (option 3)")

    results = {
        "protocol": "claude-reply-0140eab sec.2 (option 2)",
        "population_states": len(both),
        "A_only_states": a_only,
        "B_only_states": b_only,
        "thin_a_snaps": [r["snap"] for r in thin_a],
        "thin_b_snaps": [r["snap"] for r in thin_b],
        "split": {
            "seed": SPLIT_SEED,
            "algorithm": "unique game ids sorted as strings; "
                         "random.Random(seed).shuffle; first "
                         "ceil(n_games/2) games = H1",
            "n_games": len(games),
            "H1_games": h1_games, "H2_games": h2_games,
            "H1_states": len(h1), "H2_states": len(h2),
        },
        "grid": table,
        "selection": {"bar_H1": H1_BAR, "m_star": m_star},
        "verification": ({"bar_H2": H2_BAR, "V1-ov_H2_at_m_star": ver}
                         if m_star is not None else None),
        "outcome": outcome,
    }
    with open(a.results_out, "w") as f:
        json.dump(results, f, indent=1)

    # ---- human-readable summary ------------------------------
    L = []
    L.append("")
    L.append(f"POPULATION: {len(both)} states labeled in both "
             f"runs (A-only {a_only}; B-only {b_only}; thin A "
             f"{[r['snap'] for r in thin_a]}, thin B "
             f"{[r['snap'] for r in thin_b]})")
    L.append(f"SPLIT: {len(games)} games, seed {SPLIT_SEED}: "
             f"H1 {len(h1_games)} games / {len(h1)} states; "
             f"H2 {len(h2_games)} games / {len(h2)} states")
    L.append(f"  H1 games: {', '.join(h1_games)}")
    L.append(f"  H2 games: {', '.join(h2_games)}")
    for m in GRID:
        t = table[str(m)]
        L.append("")
        L.append(f"m = {m}:")
        for name in ("full", "H1", "H2"):
            r = t[name]
            c = r["curse_A_to_B"]
            prim = c["primary_mean_adv_B_means"]
            sec = c["secondary_mean_B_mean_diff_paired"]
            L.append(
                f"  {name:4s} ({r['states']} states): "
                f"A overturn {fmt_rate(r['A_overturn_rate'])}; "
                f"V1-ov {fmt_rate(r['V1-ov'])}; "
                f"V1-conf {fmt_rate(r['V1-conf'])}; "
                f"curse A->B primary "
                f"{prim:+.3f} over {c['primary_states']} states "
                f"(missing {c['primary_missing']})"
                if prim is not None else
                f"  {name:4s} ({r['states']} states): "
                f"A overturn {fmt_rate(r['A_overturn_rate'])}; "
                f"V1-ov {fmt_rate(r['V1-ov'])}; "
                f"V1-conf {fmt_rate(r['V1-conf'])}; "
                f"curse A->B primary n/a (no A overturns)")
            L.append(
                f"       curse secondary (paired, B mean_diff "
                f"where B tested A's pick): "
                f"{sec:+.3f} over {c['secondary_states']} states"
                if sec is not None else
                f"       curse secondary: n/a")
    L.append("")
    L.append("SELECTION (H1 only, smallest m with V1-ov >= "
             f"{H1_BAR}): m* = {m_star}")
    if ver is not None:
        L.append(f"VERIFICATION (H2 only): V1-ov at m* = "
                 f"{fmt_rate(ver)} (bar {H2_BAR})")
    L.append("")
    L.append("OUTCOME: " + outcome)
    print("\n".join(L))


if __name__ == "__main__":
    main()
