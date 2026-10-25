#!/usr/bin/env python3
"""pilot_report.py - the round-8 pilot's reads (build-package
sec.3): label-job timing (mean + p95), V1 self-consistency, V2
live-consistency, thin-label counts.

V1 (self-consistency): the same 20 snapshots labeled twice under
different world seeds (runs A and B). Reported as the overall
pick-agreement rate plus the two conditional rates the reply
asks for: agreement on overturns (of the snaps where run A
overturned, the fraction where run B overturned to the same
pick) and agreement on confirmations (of the snaps where run A
confirmed, the fraction where run B confirmed). Run B's
conditionals are printed too - the two runs are symmetric.

V2 (live-consistency): each run's picks against the LIVE teacher
picks recorded in the gate snap index. All 20 pilot snaps are
live overturns, so V2 agreement = the fraction where the label
run overturned to the live pick.

The pass read (claude-reply-926f6c3 sec.1: V2 "statistically
indistinguishable" from V1) is NOT auto-decided here. The report
prints both rates with Wilson 95% intervals and a two-proportion
z-test of the difference; the judgment is Claude's at pilot
review, and the corpus run is gated on it plus Joe's go.

Inputs (pilot out dir): labels_a.jsonl, labels_b.jsonl,
thin_a.jsonl, thin_b.jsonl, pilot_v2_truth.jsonl,
pilot_times.jsonl (one row per job-run: {snap, run, secs} -
parsed by run_pilot.sh from the label mains' own stderr lines).
"""
import argparse
import json
import math


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def z_two_prop(k1, n1, k2, n2):
    if n1 == 0 or n2 == 0:
        return float("nan")
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return float("nan")
    z = (k1 / n1 - k2 / n2) / se
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def load(path):
    return [json.loads(ln) for ln in open(path) if ln.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = a.out.rstrip("/")

    la = {r["state_id"]: r for r in load(o + "/labels_a.jsonl")}
    lb = {r["state_id"]: r for r in load(o + "/labels_b.jsonl")}
    tha = load(o + "/thin_a.jsonl")
    thb = load(o + "/thin_b.jsonl")
    truth = {r["snap"]: r for r in load(o + "/pilot_v2_truth.jsonl")}
    times = load(o + "/pilot_times.jsonl")

    snaps = sorted(set(la) | set(lb))
    lines = []
    lines.append("ROUND-8 PILOT REPORT")
    lines.append("")
    secs = sorted(t["secs"] for t in times)
    if secs:
        n = len(secs)
        mean = sum(secs) / n
        p95 = secs[min(n - 1, math.ceil(0.95 * n) - 1)]
        lines.append(f"label jobs timed: {n} job-runs "
                     f"(20 snapshots x 2 runs)")
        lines.append(f"per-job secs: mean {mean:.1f}  p95 {p95:.1f}  "
                     f"max {secs[-1]:.1f}")
        lines.append(f"corpus sizing read (10,000 labels): "
                     f"~{10000 * mean / 3600:.1f} box-hours serial at the "
                     f"mean, ~{10000 * p95 / 3600:.1f} at the p95; "
                     f"divide by the label stage's tree parallelism "
                     f"(4) for wall-clock")
    lines.append("")
    lines.append(f"thin labels (excluded, counted): run A {len(tha)}, "
                 f"run B {len(thb)} of {len(snaps)} jobs each")
    lines.append("")

    # V1: A vs B
    both = [s for s in snaps if s in la and s in lb]
    agree = sum(1 for s in both
                if la[s]["teacher_pick"] == lb[s]["teacher_pick"])
    lo, hi = wilson(agree, len(both))
    lines.append(f"V1 self-consistency: pick agreement "
                 f"{agree}/{len(both)} = {agree / len(both):.3f} "
                 f"Wilson95 [{lo:.3f}, {hi:.3f}]")

    def conditional(x, y, kind):
        # of the snaps where run x made a `kind` decision, the
        # fraction where run y made the SAME decision
        idx = [s for s in both
               if (x[s]["overturn"] == 1) == (kind == "overturn")]
        if not idx:
            return f"  {kind}: none in run"
        same = sum(1 for s in idx
                   if y[s]["teacher_pick"] == x[s]["teacher_pick"]
                   and y[s]["overturn"] == x[s]["overturn"])
        return (f"  agreement on {kind} (run of {len(idx)}): "
                f"{same}/{len(idx)} = {same / len(idx):.3f}")
    lines.append(conditional(la, lb, "overturn"))
    lines.append(conditional(la, lb, "confirm"))
    lines.append(conditional(lb, la, "overturn"))
    lines.append(conditional(lb, la, "confirm"))
    lines.append("")

    # V2: each run vs the live picks (all live decisions overturn)
    v2k = v2n = 0
    for name, lab in (("A", la), ("B", lb)):
        idx = [s for s in snaps if s in lab and s in truth]
        k = sum(1 for s in idx
                if lab[s]["teacher_pick"] == truth[s]["teacher_pick"])
        lo, hi = wilson(k, len(idx))
        lines.append(f"V2 live-consistency (run {name}): "
                     f"{k}/{len(idx)} = {k / len(idx):.3f} "
                     f"Wilson95 [{lo:.3f}, {hi:.3f}]")
        v2k += k
        v2n += len(idx)
    lo, hi = wilson(v2k, v2n)
    lines.append(f"V2 pooled: {v2k}/{v2n} = {v2k / v2n:.3f} "
                 f"Wilson95 [{lo:.3f}, {hi:.3f}]")
    p = z_two_prop(v2k, v2n, agree, len(both))
    lines.append(f"V2-pooled vs V1-overall difference: "
                 f"two-proportion z-test p = {p:.3f} "
                 f"(the indistinguishability judgment is the "
                 f"reviewer's, from these numbers)")
    lines.append("")
    lines.append("per-snap detail (snap: live / A / B picks, "
                 "A/B overturn flags):")
    for s in snaps:
        lv = truth[s]["teacher_pick"] if s in truth else "-"
        pa = la[s]["teacher_pick"] if s in la else "thin"
        pb = lb[s]["teacher_pick"] if s in lb else "thin"
        oa = la[s]["overturn"] if s in la else "-"
        ob = lb[s]["overturn"] if s in lb else "-"
        lines.append(f"  {s}: live={lv} A={pa} (ov {oa}) "
                     f"B={pb} (ov {ob})")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
