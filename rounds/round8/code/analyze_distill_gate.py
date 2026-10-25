#!/usr/bin/env python3
"""Round-8 gate analysis (build-package sec.5; the bands are
claude-reply-926f6c3 sec.5's, registered before the fleet runs;
the row handling is the fix package's rewrite against the
driver's real row schema, per claude-reply-a076148 sec.2.2).

PRIMARY: the paired draw-scored delta, distilled minus v15, over
the fleet's paired units (seed x seat; both arms raw, Fai mirror
vs heuristic).

ROW SCHEMA (the paired driver's own, verified against round 7's
published rows from the same driver): each row carries `seed`,
`arm`, `seat`, `winner` (0 on a draw or an engine cap), `capped`,
`draw`, `gamelog_sha`, and - on a wall-clock timeout row only -
`invalid` == "timeout".

SCORING - explicit branches, in this order (per row):
  1. invalid == "timeout"  -> 0.5 for that arm, counted as a
     timeout unit (the registered raw-arm convention: a timeout
     is a driver artifact, not a policy outcome; the stock
     gate_raw_retry.py gets one re-run at it before the fleet is
     read, and a row still standing as a timeout scores 0.5).
  2. any other `invalid`   -> the row is UNUSABLE: the unit is
     reported and excluded, never silently scored.
  3. capped or draw or winner in {0, None} -> 0.5.
  4. otherwise a win (1.0) or loss (0.0) by the row's own seat.

DIVERGENCE: a paired unit is diverged iff the two arms'
`gamelog_sha` values differ. Timeout units are counted
separately and are never counted as diverged. When the rows
carry per-decision pick sequences, the mean decision depth of
the first divergence is reported as available; the rate does
not depend on it.

Reported with the primary: cluster bootstrap 95% CI (resample
by seed), normal-approximation cross-check, exact sign test,
per-seat deltas, and the distilled arm's absolute score beside
the raw arm's (and, labeled historical, the Fai gate's raw
0.4500 - the fleet's own raw arm is the contemporaneous
control).

Bands (registered):
  CONVERTS      delta >= +0.10 AND CI lower bound > 0
  PARTIAL       CI lower > 0 AND delta < +0.10 (read with the
                divergence rate; a high-divergence partial and a
                low-divergence partial are different findings)
  DOES NOT      CI includes 0 (suspects in order: label
  CONVERT       definition, then corpus; the L3-style read
                follows only a conversion)
  IMPEACH       delta > +0.25: at the teacher's own +0.2525 the
                student cannot plausibly exceed it by retention;
                a delta above the band impeaches the measurement
                and the verdict is WITHHELD pending investigation.

Registry assertion: DISTILL_REGISTRY_SHA256 must match the
registry's current sha256 - the fleet's games are registered
before the analysis reads them (the gate runner merges and
prints the sha).

Usage: analyze_distill_gate.py --fleet DIR --arm-names raw dist
  [--chunks c1 c2 c3 c4] [--out report.json]
"""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict

REG = "/tmp/harvest/do_not_train_registry.json"


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def score_row(r):
    """One driver row -> (score, kind). kind is 'timeout',
    'invalid:<value>', 'drawn' or 'decided'. A score of None
    marks the row unusable (branch 2 only)."""
    inv = r.get("invalid")
    if inv == "timeout":
        return 0.5, "timeout"
    if inv:
        return None, "invalid:" + str(inv)
    w = r.get("winner")
    if r.get("capped") or r.get("draw") or w is None or w == 0:
        return 0.5, "drawn"
    return (1.0 if int(w) == int(r["seat"]) else 0.0), "decided"


def score(pair):
    """(score_raw, score_dist, kinds) or None if either row is
    unusable (branch 2)."""
    a, b = pair
    sa, ka = score_row(a)
    sb, kb = score_row(b)
    if sa is None or sb is None:
        return None
    return sa, sb, (ka, kb)


def collect(fleet, chunks, arm_raw, arm_dist):
    pairs = {}
    raw_rows = {arm_raw: {}, arm_dist: {}}
    for chunk in chunks:
        for arm in (arm_raw, arm_dist):
            for seat in (1, 2):
                for path in glob.glob(
                        os.path.join(fleet, f"{arm}_{chunk}_s{seat}.jsonl")):
                    for ln in open(path):
                        if not ln.strip():
                            continue
                        r = json.loads(ln)
                        if r.get("arm") != "raw":
                            continue
                        raw_rows[arm][(r["seed"], seat)] = r
    for key in sorted(set(raw_rows[arm_raw]) & set(raw_rows[arm_dist])):
        pairs[key] = (raw_rows[arm_raw][key], raw_rows[arm_dist][key])
    return pairs, raw_rows


def bootstrap(deltas, seeds_of, iters=10000, rng_seed=20261025):
    rng = random.Random(rng_seed)
    seeds = sorted(set(seeds_of))
    by_seed = defaultdict(list)
    for d, s in zip(deltas, seeds_of):
        by_seed[s].append(d)
    means = []
    for _ in range(iters):
        tot, n = 0.0, 0
        for _ in seeds:
            ds = by_seed[rng.choice(seeds)]
            tot += sum(ds); n += len(ds)
        means.append(tot / n)
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def divergence(pairs, kinds_of):
    """Divergence on the two arms' gamelog hashes. Timeout units
    (either arm's row a timeout) are counted separately and are
    never counted as diverged."""
    units = len(pairs)
    timeout_units = 0
    diff_units = 0
    identical_units = 0
    depths = []
    for key in sorted(pairs):
        a, b = pairs[key]
        if "timeout" in kinds_of[key]:
            timeout_units += 1
            continue
        ha, hb = a.get("gamelog_sha"), b.get("gamelog_sha")
        if ha is not None and ha == hb:
            identical_units += 1
            continue
        diff_units += 1
        ta = a.get("trace_picks") or []
        tb = b.get("trace_picks") or []
        for i, (x, y) in enumerate(zip(ta, tb)):
            if x != y:
                depths.append(i)
                break
    scored = units - timeout_units
    return {"paired_units": units,
            "timeout_units": timeout_units,
            "identical_units": identical_units,
            "diverged_units": diff_units,
            "divergence_rate_of_scored_units":
                (diff_units / scored) if scored else None,
            "divergence_rate_of_all_units":
                (diff_units / units) if units else None,
            "mean_first_divergence_depth":
                (sum(depths) / len(depths)) if depths else None,
            "units_with_trace_depth": len(depths)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet", required=True)
    ap.add_argument("--arm-names", nargs=2, default=["raw", "dist"])
    ap.add_argument("--chunks", nargs="*", default=["c1", "c2", "c3", "c4"])
    ap.add_argument("--out")
    a = ap.parse_args()

    want = os.environ.get("DISTILL_REGISTRY_SHA256")
    have = hashlib.sha256(open(REG, "rb").read()).hexdigest()
    print(f"registry sha256: {have}")
    if want and want != have:
        print("ABORT: DISTILL_REGISTRY_SHA256 does not match the "
              "registry on disk - the fleet is not the registered "
              "one.", file=sys.stderr)
        sys.exit(1)
    if not want:
        print("WARNING: DISTILL_REGISTRY_SHA256 not set - the "
              "registry assertion is skipped (the gate runner "
              "prints the merged sha).", file=sys.stderr)

    raw_name, dist_name = a.arm_names
    pairs, _ = collect(a.fleet, a.chunks, raw_name, dist_name)
    print(f"paired units: {len(pairs)} (expect 400)")
    scored = {}
    bad = {}
    kinds_of = {}
    for k in sorted(pairs):
        s = score(pairs[k])
        if s is None:
            ka = score_row(pairs[k][0])[1]
            kb = score_row(pairs[k][1])[1]
            bad[k] = (ka, kb)
        else:
            scored[k] = (s[0], s[1])
            kinds_of[k] = s[2]
    for k, kinds in bad.items():
        print(f"  UNUSABLE unit {k} - row kinds {kinds}; inspect "
              f"before reading")
    n_timeout = sum(1 for k in kinds_of.values() if "timeout" in k)
    print(f"timeout units (scored 0.5 for the timed-out arm): "
          f"{n_timeout}")
    usable = scored
    deltas = [usable[k][1] - usable[k][0] for k in sorted(usable)]
    keys = sorted(usable)
    seeds_of = [k[0] for k in keys]
    n = len(deltas)
    mean = sum(deltas) / n
    var = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    se = math.sqrt(var / n)
    z = mean / se if se else float("inf")
    p_norm = 2 * (1 - norm_cdf(abs(z)))
    lo, hi = bootstrap(deltas, seeds_of)
    wins = sum(1 for d in deltas if d > 0)
    losses = sum(1 for d in deltas if d < 0)
    ties = n - wins - losses
    m = wins + losses
    sign_p = min(1.0, 2 * sum(math.comb(m, i) for i in range(wins + 1))
                 / (2 ** m)) if m and wins >= losses else (
        min(1.0, 2 * sum(math.comb(m, i) for i in range(losses + 1))
            / (2 ** m)) if m else 1.0)
    sa_mean = sum(sa for sa, _ in usable.values()) / n
    sb_mean = sum(sb for _, sb in usable.values()) / n
    per_seat = {}
    for seat in (1, 2):
        ds = [usable[k][1] - usable[k][0] for k in keys if k[1] == seat]
        if ds:
            per_seat[f"seat{seat}"] = {
                "n": len(ds), "delta": sum(ds) / len(ds)}
    div = divergence(pairs, kinds_of)

    if mean > 0.25:
        verdict = ("IMPEACH - delta exceeds +0.25, above the "
                   "teacher's own +0.2525 retention ceiling; the "
                   "verdict is WITHHELD pending investigation")
    elif mean >= 0.10 and lo > 0:
        verdict = "CONVERTS (delta >= +0.10, CI lower > 0)"
    elif lo > 0:
        verdict = ("PARTIAL (CI lower > 0, delta < +0.10) - read "
                   "with the divergence rate")
    else:
        verdict = "DOES NOT CONVERT (CI includes 0)"

    rep = {
        "paired_units": n, "unusable_units": len(bad),
        "timeout_units": n_timeout,
        "sum_paired_diffs": sum(deltas),
        "primary_delta_distilled_minus_v15": mean,
        "ci95_bootstrap_cluster_by_seed": [lo, hi],
        "normal_approx": {"se": se, "z": z, "p": p_norm},
        "sign_test": {"wins": wins, "losses": losses, "ties": ties,
                      "p": sign_p},
        "absolute_scores": {
            "distilled": sb_mean, "v15_this_fleet": sa_mean,
            "v15_historical_fai_gate": 0.4500},
        "per_seat": per_seat,
        "divergence": div,
        "verdict": verdict,
    }
    print(json.dumps(rep, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
