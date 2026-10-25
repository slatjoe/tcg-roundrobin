#!/usr/bin/env python3
"""Round-8 gate analysis (build-package sec.5; the bands are
claude-reply-926f6c3 sec.5's, registered before the fleet runs).

PRIMARY: the paired draw-scored delta, distilled minus v15, over
the fleet's paired units (seed x seat; both arms raw, Fai mirror
vs heuristic; pre-capped/drawn games score 0.5). Scoring mirrors
the accepted gate convention EXCEPT timeouts: a post-retry
timeout scores 0.5 for that arm (the round-7 fleet's convention -
an unrecovered timeout is a driver artifact, not a policy
outcome; the counts are reported alongside).

Reported with the primary: cluster bootstrap 95% CI (resample by
seed), normal-approximation cross-check, exact sign test,
per-seat deltas, the distilled arm's absolute score beside the
raw arm's (and, labeled historical, the Fai gate's raw 0.4500 -
the fleet's own raw arm is the contemporaneous control), and
the DIVERGENCE RATE: the share of paired units whose two arms'
gamelog hashes differ (the registered read), plus - when the
rows carry per-decision pick sequences - the mean decision
depth of the first divergence (reported as available; the rate
does not depend on it).

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
SEED_SET = set(range(9001, 9201))


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def score(pair):
    """(score_a, score_b) or None for a unit the caller must read
    on its own (a malformed row - reported, never dropped)."""
    a, b = pair
    def s(r, opp):
        w = r.get("winner")
        if w not in (1, 2):
            return None
        if r.get("capped"):
            return 0.5
        return 1.0 if int(w) == int(r["learner_seat"]) else 0.0
    # Timeout rows carry no usable winner (the driver writes
    # winner -1 / no keep flag): score 0.5 for that arm.
    def s2(r):
        if r.get("timed_out") or (r.get("winner") not in (1, 2)
                                  and not r.get("gamelog_sha256")):
            return 0.5
        return s(r, None)
    sa, sb = s2(a), s2(b)
    if sa is None or sb is None:
        return None
    return sa, sb


def collect(fleet, chunks, arm_raw, arm_dist):
    pairs = {}
    raw_rows = {arm_raw: {}, arm_dist: {}}
    for chunk in chunks:
        for arm, name in ((arm_raw, "raw"), (arm_dist, "dist")):
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


def divergence(pairs):
    units = len(pairs)
    diff_units = 0
    depths = []
    for (seed, seat), (a, b) in sorted(pairs.items()):
        if str(a.get("gamelog_sha256")) != str(b.get("gamelog_sha256")):
            diff_units += 1
            ta = a.get("trace_picks") or []
            tb = b.get("trace_picks") or []
            for i, (x, y) in enumerate(zip(ta, tb)):
                if x != y:
                    depths.append(i)
                    break
    return {"paired_units": units,
            "diverged_units": diff_units,
            "divergence_rate": (diff_units / units) if units else None,
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
    bad = {k: p for k, p in pairs.items() if score(p) is None}
    for k in bad:
        print(f"  UNUSABLE unit {k} - inspect before reading")
    usable = {k: score(p) for k, p in pairs.items()
              if score(p) is not None}
    deltas = [sb - sa for (sa, sb) in
              (usable[k] for k in sorted(usable))]
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
    div = divergence(pairs)

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
