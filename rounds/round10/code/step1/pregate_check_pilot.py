#!/usr/bin/env python3
"""Round-10 Step 1 pilot GHOST PRE-GATE checker
(step1-pilot-package.md sec.7; REPAIRED in fix pass 2,
2026-10-29 -- see the launch record
step1-pilot-launch.md for the three-layer diagnosis
this repair answers).

Two ghost arms (TEACHER_GHOST: the full search machinery
runs, the played pick is forced to the prior's) on the
same seeds at both seats: one under the sec.14 build
(search_s3.php), one under the threshold-lifted build
(search_s3_thr.php). Because the played pick is the
prior's in BOTH builds, the played games must be
action-identical; the search rows show where the builds
differ. The check, exactly:

  1. DETERMINISM + SEAT CONTROL (the round-9
     instruments): raw seat 1 twice agrees per seed on
     (winner, draw, capped, turns, gamelog_sha); raw
     seat 2's gamestate_norm_sha differs from seat 1's
     per seed.
  2. PLAYED-ACTION IDENTITY: per seat, ghost-sec14 vs
     ghost-thr driver rows agree per seed on (winner,
     draw, capped, turns, gamelog_sha) -- over the
     seeds where BOTH arms COMPLETED. A seed whose
     driver row in either arm is a timeout
     (invalid == "timeout") is reported as a timeout,
     by seed and arm, never as an identity failure
     (attempt 1's failures were exactly this: the
     1,200 s driver default, sized for the sec.14 arm,
     killed five + three thr games whose completed
     counterparts are all byte-identical). Under the
     repaired sizing a timeout should not occur; if
     one does, the verdict line names it.
  3. CONTESTED-CLASS IDENTITY: decisions paired BY
     SEED AND SEQUENCE ORDER. The driver rows give
     each arm's seed -> gamename mapping for completed
     games; each arm's decision rows for that seed's
     game (its arm-local instance id) are taken in
     file order and paired index by index. (Attempt
     1's checker paired by a key leading with the
     arm-local game id; the two arms' id sets are
     disjoint, so it paired ZERO decisions and counted
     every row as an "other" divergence.) For a pair
     where both arms searched and the sec.14 row's top
     prior is < 0.97 (a contested pair): the SELECTED
     candidate sets must be EXACTLY equal, and the
     priors must agree to a max-abs-difference
     tolerance of 1e-6 (PRIORS_TOL below; the observed
     instrument noise is ~1e-7 -- GPU-served float
     noise -- an order of magnitude of headroom; the
     check prints the observed maximum abs diff so the
     tolerance's adequacy is itself in the record).
     The rollout outcomes are NOT compared -- Decide's
     seed base is drawn per call, so two processes
     cannot reproduce each other's worlds.
  4. NEWLY-CONTESTED DIVERGENCE, counted not failed:
     a pair where the sec.14 arm logged an uncontested
     early-return row (contested == 0; boundary
     membership read from the thr arm's paired row:
     its top prior >= 0.97) and the thr arm logged a
     full search row -- the expected and ONLY expected
     decision-level divergence. Both-uncontested pairs
     (possible only at ncand <= 1) are skipped. ANY
     other shape is counted BY NAME as its own
     divergence class and fails: sec14-searched x
     thr-uncontested; both-searched at sec.14 top
     prior >= 0.97; sec14-uncontested x thr-searched
     with thr top prior < 0.97. If a seed's two games'
     decision counts differ, the common prefix is
     paired and the tail is counted by arm as a named
     divergence, with the reason printed (trajectory
     already diverged, or game-length difference in
     an otherwise identical game -- the played rows
     decide which). Decision pairing covers only
     seeds where both arms completed; a timed-out
     seed's partial stats are never paired.
  5. K6 per ghost arm (round-9 form): rollout rows
     without ghost == 1 must all carry
     fallback == "thin_prior" AND pick == prior_pick;
     the line (rollout, unstamped, not-thin, pick-off)
     passes iff the last two counts are 0.
  6. Each ghost arm's driver manifest checks are all
     true except possibly ghost_flag_on_all_rollouts
     (read under K6, as in round 9).

Verdict IDENTICAL iff 1, 2, 3, 5, 6 hold and 4's
divergences are all of the expected shape. Exit 0 iff
IDENTICAL, else 2.

Usage:
  pregate_check_pilot.py
      --rows raw_s1=F --rows raw2_s1=F --rows raw_s2=F
      --rows ghost14_s1=F --rows ghost14_s2=F
      --rows ghostthr_s1=F --rows ghostthr_s2=F
      --manifest ghost14_s1=F --manifest ghost14_s2=F
      --manifest ghostthr_s1=F --manifest ghostthr_s2=F
      --stats ghost14_s1=F --stats ghost14_s2=F
      --stats ghostthr_s1=F --stats ghostthr_s2=F
"""
import argparse
import json
import sys
from collections import defaultdict

BOUNDARY = 0.97
# Registered in step1-pilot-package.md sec.7 (fix
# pass 2): priors on a contested pair must agree to
# this max abs difference. Observed instrument noise
# is ~1e-7 (GPU-served floats); 1e-6 is an order of
# magnitude of headroom. `selected` stays EXACT.
PRIORS_TOL = 1e-6

PLAYED_FIELDS = ("winner", "draw", "capped", "turns",
                 "gamelog_sha")


def load_rows(path):
    out = {}
    for l in open(path):
        if l.strip():
            r = json.loads(l)
            if "seed" in r:
                out[int(r["seed"])] = r
    return out


def load_stats(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def top_prior(r):
    pv = r.get("priors")
    if isinstance(pv, dict):
        vals = [float(x) for x in pv.values()]
    elif isinstance(pv, list):
        vals = [float(x) for x in pv]
    else:
        return None
    return max(vals) if vals else None


def priors_map(r):
    """Priors as {candidate_index: probability}, or
    None when the row carries no priors array."""
    pv = r.get("priors")
    if isinstance(pv, dict):
        return {int(k): float(v) for k, v in pv.items()}
    if isinstance(pv, list):
        return {i: float(v) for i, v in enumerate(pv)}
    return None


def max_abs_diff(pa, pb):
    """Max |pa - pb| over the union of candidate
    indices (a candidate present on one side only
    counts against 0.0). None if either side is
    missing."""
    if pa is None or pb is None:
        return None
    keys = set(pa) | set(pb)
    if not keys:
        return 0.0
    return max(abs(pa.get(k, 0.0) - pb.get(k, 0.0))
               for k in keys)


def k6_line(stats):
    ro = [r for r in stats if r.get("teacher") == 1
          and ("means" in r or "n_worlds" in r)]
    un = [r for r in ro if r.get("ghost") != 1]
    not_thin = sum(1 for r in un
                   if r.get("fallback") != "thin_prior")
    pick_off = sum(1 for r in un
                   if r.get("pick") != r.get("prior_pick"))
    return len(ro), len(un), not_thin, pick_off


def decision_rows(stats):
    """Teacher rows that carry a decision: searched
    rows (priors present) and uncontested early-return
    rows (contested == 0 with ncand present)."""
    out = []
    for r in stats:
        if r.get("teacher") != 1:
            continue
        if "priors" in r or r.get("contested") == 0:
            out.append(r)
    return out


def game_decisions(stats, gamename):
    """One game's decision rows, in file (sequence)
    order, selected by its arm-local instance id."""
    return [r for r in decision_rows(stats)
            if str(r.get("game")) == str(gamename)]


def is_timeout(row):
    return row is not None \
        and row.get("invalid") == "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", action="append", required=True)
    ap.add_argument("--manifest", action="append",
                    required=True)
    ap.add_argument("--stats", action="append", required=True)
    a = ap.parse_args()
    rows, mans, stats = {}, {}, {}
    for spec in a.rows:
        t, p = spec.split("=", 1)
        rows[t] = load_rows(p)
    for spec in a.manifest:
        t, p = spec.split("=", 1)
        mans[t] = json.load(open(p))
    for spec in a.stats:
        t, p = spec.split("=", 1)
        stats[t] = load_stats(p)

    ok = True

    def verdict(name, good, detail=""):
        nonlocal ok
        print("%s %s %s" % ("PASS" if good else "FAIL",
                            name, detail))
        ok = ok and good

    r1, r2, rs2 = (rows.get("raw_s1", {}),
                   rows.get("raw2_s1", {}),
                   rows.get("raw_s2", {}))
    seeds = sorted(set(r1) & set(r2))
    same = sum(1 for s in seeds if all(
        r1[s].get(k) == r2[s].get(k) for k in
        PLAYED_FIELDS))
    verdict("determinism: raw seat-1 rerun identical",
            len(seeds) == 10 and same == len(seeds),
            "%d/%d seeds agree" % (same, len(seeds)))
    seeds = sorted(set(r1) & set(rs2))
    diff = sum(1 for s in seeds
               if r1[s].get("gamestate_norm_sha")
               != rs2[s].get("gamestate_norm_sha"))
    verdict("R16: seat-crossed raw control differs",
            len(seeds) == 10 and diff == len(seeds),
            "%d/%d seeds differ" % (diff, len(seeds)))

    for seat in (1, 2):
        g14 = rows.get("ghost14_s%d" % seat, {})
        gth = rows.get("ghostthr_s%d" % seat, {})
        seeds = sorted(set(g14) & set(gth))

        # --- leg 2: played-action identity over the
        # seeds both arms completed; timeouts named.
        timeout_seeds = []   # (seed, [arms])
        completed = []
        eq = 0
        for s in seeds:
            arms = []
            if is_timeout(g14.get(s)):
                arms.append("sec14")
            if is_timeout(gth.get(s)):
                arms.append("thr")
            if arms:
                timeout_seeds.append((s, arms))
                continue
            completed.append(s)
            if all(g14[s].get(k) == gth[s].get(k)
                   for k in PLAYED_FIELDS):
                eq += 1
        tdesc = "; ".join(
            "seed %d (%s)" % (s, "+".join(arms))
            for s, arms in timeout_seeds) or "none"
        verdict("seat %d played-action identity "
                "(ghost sec.14 vs ghost thr, completed "
                "games)" % seat,
                len(seeds) == 10 and eq == len(completed),
                "%d/%d completed seeds identical; "
                "timeouts: %d seed(s): %s"
                % (eq, len(completed),
                   len(timeout_seeds), tdesc))

        # --- legs 3+4: decision pairing by seed and
        # sequence order, over completed seed pairs.
        A_all = stats.get("ghost14_s%d" % seat, [])
        B_all = stats.get("ghostthr_s%d" % seat, [])
        contested_pairs = contested_bad = 0
        newly = both_unc = 0
        div = defaultdict(int)
        tail_by_arm = {"sec14": 0, "thr": 0}
        obs_max = 0.0
        worst = None        # (diff, seed, index)
        bad_example = None  # (seed, index, diff, sel_eq)
        pair_errors = 0
        for s in completed:
            ga, gb = g14[s].get("gamename"), \
                gth[s].get("gamename")
            if ga is None or gb is None:
                pair_errors += 1
                print("INFO seat %d seed %d: completed "
                      "driver row without gamename; "
                      "decision pairing impossible"
                      % (seat, s))
                continue
            A = game_decisions(A_all, ga)
            B = game_decisions(B_all, gb)
            m = min(len(A), len(B))
            for i in range(m):
                ra, rb = A[i], B[i]
                a_unc = ra.get("contested") == 0
                b_unc = rb.get("contested") == 0
                if a_unc and b_unc:
                    # both builds returned early: only
                    # possible at ncand <= 1 (the lifted
                    # build searches everything else)
                    both_unc += 1
                    continue
                if a_unc and not b_unc:
                    # The sec.14 uncontested early-return
                    # row carries NO priors array; the
                    # boundary membership of the pair is
                    # read from the THR arm's row, which
                    # searched the decision and logged
                    # its priors.
                    tp_b = top_prior(rb)
                    if tp_b is not None \
                            and tp_b >= BOUNDARY:
                        newly += 1
                    else:
                        div["sec14-uncontested_x_thr-"
                            "searched_below-0.97"] += 1
                    continue
                if b_unc and not a_unc:
                    div["sec14-searched_x_thr-"
                        "uncontested"] += 1
                    continue
                tp = top_prior(ra)
                if tp is not None and tp < BOUNDARY:
                    contested_pairs += 1
                    sel_eq = ra.get("selected") \
                        == rb.get("selected")
                    d = max_abs_diff(priors_map(ra),
                                     priors_map(rb))
                    if d is not None and d > obs_max:
                        obs_max = d
                        worst = (d, s, i)
                    if not sel_eq or d is None \
                            or d > PRIORS_TOL:
                        contested_bad += 1
                        if bad_example is None:
                            bad_example = (s, i, d, sel_eq)
                else:
                    # both searched a >= boundary
                    # decision: impossible for the
                    # sec.14 build
                    div["both-searched_at_>=0.97"] += 1
            if len(A) != len(B):
                tail = abs(len(A) - len(B))
                if len(A) > len(B):
                    tail_by_arm["sec14"] += tail
                else:
                    tail_by_arm["thr"] += tail
                if all(g14[s].get(k) == gth[s].get(k)
                       for k in PLAYED_FIELDS):
                    div["tail_game-length-diff_in-"
                        "identical-game"] += tail
                else:
                    div["tail_trajectory-"
                        "diverged"] += tail
        for s, arms in timeout_seeds:
            print("INFO seat %d seed %d: decision "
                  "pairing skipped (timeout: %s); "
                  "partial stats never paired"
                  % (seat, s, "+".join(arms)))
        div_total = sum(div.values())
        verdict("seat %d contested-class identity "
                "(selected exact, priors tol %.0e, "
                "seed-paired sequence order)" % (seat,
                                                 PRIORS_TOL),
                contested_bad == 0 and div_total == 0
                and pair_errors == 0,
                "%d contested pairs, %d bad, %d named "
                "divergences %s, max |dprior| %.3e "
                "(tol %.0e)"
                % (contested_pairs, contested_bad,
                   div_total, dict(div), obs_max,
                   PRIORS_TOL))
        if worst is not None:
            print("INFO seat %d max |dprior| %.3e at "
                  "seed %d decision %d (tolerance %.0e)"
                  % ((seat, worst[0], worst[1], worst[2],
                      PRIORS_TOL)))
        if bad_example is not None:
            print("INFO seat %d first contested-bad "
                  "pair: seed %d decision %d, |dprior| "
                  "%s, selected equal: %s"
                  % (seat, bad_example[0], bad_example[1],
                     ("%.3e" % bad_example[2])
                     if bad_example[2] is not None
                     else "n/a (priors missing)",
                     bad_example[3]))
        print("INFO seat %d newly-contested divergences "
              "(expected shape): %d; both-uncontested "
              "pairs skipped: %d; unpaired tail rows "
              "by arm: sec14 %d, thr %d"
              % (seat, newly, both_unc,
                 tail_by_arm["sec14"], tail_by_arm["thr"]))

        for tag in ("ghost14_s%d" % seat,
                    "ghostthr_s%d" % seat):
            man = mans.get(tag, {})
            checks = man.get("checks", {})
            others = {k: v for k, v in checks.items()
                      if k != "ghost_flag_on_all_rollouts"}
            verdict("%s manifest checks (other than the "
                    "K6-read one)" % tag,
                    bool(others) and all(others.values()),
                    json.dumps(others))
            line = k6_line(stats.get(tag, []))
            verdict("%s K6 line %d %d %d %d" % ((tag,)
                    + line),
                    line[2] == 0 and line[3] == 0,
                    "(rollout, unstamped, not-thin, "
                    "pick-off)")
    print("PREGATE: %s" % ("IDENTICAL" if ok
                           else "NOT IDENTICAL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
