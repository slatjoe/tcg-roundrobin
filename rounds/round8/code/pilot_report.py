#!/usr/bin/env python3
"""pilot_report.py - the round-8 pilot's reads, as corrected by
claude-reply-a076148 sec.3 (the fix package's restructure).

Inputs (pilot out dir): labels_v1a.jsonl / labels_v1b.jsonl (the
V1 states labeled twice), labels_v2.jsonl (the V2 gate-overturn
snapshots labeled once), thin_*.jsonl, pilot_v2_truth.jsonl (the
live picks + live per-candidate means), pilot_times.jsonl
(per-job secs), pilot_cand_times.jsonl (per-candidate batch
timings + finish counts).

Reads:
  COST    per-job secs over every pilot label job-run: mean,
          p95, MAX. The corpus estimate is computed from these
          (~1,200 pilot jobs), at the mean and at the p95.
  V1      on UNSELECTED states (the pilot capture's contested
          states, labeled twice, runs A and B):
            V1-ov   = P(B makes the same overturn | A overturned)
            V1-conf = P(B confirms | A confirmed)
          with Wilson 95% intervals. Run A's labels are ordinary
          corpus labels.
  V2      on 100 gate-fleet overturn snapshots (live-selected):
            V2 = P(labeler pick == live pick | live overturned)
          Exchangeability predicts V2 ~= V1-ov; both are printed
          with Wilson intervals and the two-proportion test of
          V2 vs V1-ov. One caveat, stated with the read: gate
          states lie on teacher trajectories and V1's on v15's;
          they are the same game up to each trajectory's first
          overturn. The judgment is the reviewer's at pilot
          review - this report carries numbers, not a verdict.
  MECH    (report-only) per-candidate z-scores on the V2
          snapshots: for candidates in the live selected set but
          NOT in the live overturn pair (prior pick, live pick -
          the selected-on side), z = (labeler mean - live mean)
          / (sd_labeler * sqrt(1/n_labeler + 1/n_live)), the
          per-world sd borrowed from the labeler's own worlds
          for that candidate (the live rows record means and
          counts, not per-world outcomes). Roughly standard
          normal is the expectation.
  DEADLINE accounting: the label path's per-candidate deadline
          is 300 s against the live teacher's 180 s. From the
          per-candidate batch timings: batches whose wall ran
          past 180 s (their finished worlds are the upper bound
          on worlds finished after 180 s - the exact per-world
          finish times are not recorded by the machinery, and
          batches at or under 180 s contribute exactly 0), and
          the worlds killed at the 300 s label deadline
          (timeout_errs) with the candidates they cut.
  THIN    labels under the 20-finished-worlds floor: excluded
          and counted, per run.

LIVE-ROW SHAPE (claude-reply-8f834d2 sec.2): the live stat
rows' means / n_worlds are keyed by candidate id - DecideInner
builds them per selected candidate id, and PHP's json_encode
emits a JSON list only when those keys are exactly 0..n-1, an
object with string keys otherwise. Every live-side read goes
through live_by_id, and assert_live_shape proves the collapse
on every list-shaped row before any read relies on it.
"""
import argparse
import json
import math
from collections import defaultdict


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
    try:
        return [json.loads(ln) for ln in open(path) if ln.strip()]
    except FileNotFoundError:
        return []


def rate_line(name, k, n):
    lo, hi = wilson(k, n)
    return (f"{name}: {k}/{n} = {k / n:.3f} "
            f"Wilson95 [{lo:.3f}, {hi:.3f}]") if n else f"{name}: n=0"


def assert_live_shape(row, row_name):
    """A list-shaped live means / n_worlds is sound only when
    the row's selected == [0..len-1] (the PHP json_encode key
    collapse, claude-reply-8f834d2 sec.2). Abort, naming the
    row, if any list-shaped field violates it."""
    sel = [int(x) for x in row["selected"]]
    for field in ("means", "n_worlds"):
        v = row[field]
        if isinstance(v, list) and sel != list(range(len(v))):
            raise SystemExit(
                f"ABORT: live {field} list-shape assert failed "
                f"for row {row_name}: selected {sel} != "
                f"list(range({len(v)}))")


def live_by_id(row, field, ci, row_name):
    """ONE accessor for every live-side read of means /
    n_worlds: by candidate id in both shapes - v[ci] for a
    list (the shape assert has proved id == position there),
    v[str(ci)] for a dict."""
    assert_live_shape(row, row_name)
    v = row[field]
    if isinstance(v, list):
        return v[ci]
    return v[str(ci)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--corpus-labels", type=int, default=10000,
                    help="contested-label target the corpus "
                         "estimate is computed for")
    a = ap.parse_args()
    o = a.out.rstrip("/")

    v1a = {r["state_id"]: r for r in load(o + "/labels_v1a.jsonl")}
    v1b = {r["state_id"]: r for r in load(o + "/labels_v1b.jsonl")}
    v2 = {r["state_id"]: r for r in load(o + "/labels_v2.jsonl")}
    thin = {tag: load(o + f"/thin_{tag}.jsonl")
            for tag in ("v1a", "v1b", "v2")}
    truth = {r["snap"]: r for r in load(o + "/pilot_v2_truth.jsonl")}
    times = load(o + "/pilot_times.jsonl")
    cands = load(o + "/pilot_cand_times.jsonl")
    L = []
    L.append("ROUND-8 PILOT REPORT (corrected V1/V2 design)")
    L.append("")

    # ---- cost -------------------------------------------------
    secs = sorted(t["secs"] for t in times)
    if secs:
        n = len(secs)
        mean = sum(secs) / n
        p95 = secs[min(n - 1, math.ceil(0.95 * n) - 1)]
        L.append(f"COST: {n} label job-runs timed")
        L.append(f"  per-job secs: mean {mean:.1f}  p95 {p95:.1f}  "
                 f"max {secs[-1]:.1f}")
        tgt = a.corpus_labels
        L.append(f"  corpus estimate ({tgt} contested labels): "
                 f"{tgt * mean / 3600:.1f} box-hours serial at the "
                 f"mean, {tgt * p95 / 3600:.1f} at the p95; "
                 f"/4 label shards for wall-clock")
    L.append("")

    # ---- thin ---------------------------------------------------
    L.append("THIN (excluded, counted): "
             + ", ".join(f"{tag} {len(v)}" for tag, v in thin.items()))
    L.append("")

    # ---- V1 -----------------------------------------------------
    both = sorted(set(v1a) & set(v1b))
    a_ov = [s for s in both if v1a[s]["overturn"] == 1]
    ov_same = sum(1 for s in a_ov
                  if v1b[s]["overturn"] == 1
                  and v1b[s]["teacher_pick"] == v1a[s]["teacher_pick"])
    a_cf = [s for s in both if v1a[s]["overturn"] == 0]
    cf_same = sum(1 for s in a_cf
                  if v1b[s]["overturn"] == 0
                  and v1b[s]["teacher_pick"] == v1a[s]["teacher_pick"])
    L.append(f"V1 (unselected states, {len(both)} states labeled "
             f"twice; A overturns {len(a_ov)}, A confirmations "
             f"{len(a_cf)}):")
    L.append("  " + rate_line("V1-ov  P(B same overturn | A "
                             "overturned)", ov_same, len(a_ov)))
    L.append("  " + rate_line("V1-conf P(B confirms | A confirmed)",
                              cf_same, len(a_cf)))
    L.append("")

    # ---- V2 -----------------------------------------------------
    v2_snaps = sorted(truth)
    v2_labeled = [s for s in v2_snaps if s in v2]
    v2_hit = sum(1 for s in v2_labeled
                 if v2[s]["teacher_pick"] == truth[s]["teacher_pick"])
    L.append(f"V2 ({len(v2_snaps)} gate overturn snapshots drawn; "
             f"{len(v2_labeled)} labeled, "
             f"{len(v2_snaps) - len(v2_labeled)} thin/excluded):")
    L.append("  " + rate_line("V2  P(labeler pick == live pick | "
                              "live overturned)", v2_hit,
                              len(v2_labeled)))
    p = z_two_prop(v2_hit, len(v2_labeled), ov_same, len(a_ov))
    L.append(f"  V2 vs V1-ov: two-proportion z-test p = {p:.3f} "
             f"(exchangeability predicts V2 ~= V1-ov; caveat: "
             f"gate states lie on teacher trajectories, V1's on "
             f"v15's - the same game up to each trajectory's first "
             f"overturn. The read is the reviewer's.)")
    L.append("")

    # ---- mechanism check ---------------------------------------
    # Live-row shape proof over EVERY truth row (not only the
    # labeled ones the z-loop below touches): a list-shaped
    # means / n_worlds must satisfy selected == [0..len-1].
    for s in v2_snaps:
        assert_live_shape(truth[s], s)
    zs = []
    skipped = 0
    for s in v2_labeled:
        t, lab = truth[s], v2[s]
        pair = {int(t["prior_pick"]), int(t["teacher_pick"])}
        sel = [int(x) for x in t["selected"]]
        for ci in sel:
            if ci in pair:
                continue
            m_live = live_by_id(t, "means", ci, s)
            n_live = live_by_id(t, "n_worlds", ci, s)
            m_lab = (lab.get("means") or {}).get(str(ci))
            sd_lab = (lab.get("sds") or {}).get(str(ci))
            n_lab = (lab.get("n_worlds") or {}).get(str(ci))
            if (m_lab is None or sd_lab is None or not n_lab
                    or not sd_lab):
                skipped += 1
                continue
            denom = sd_lab * math.sqrt(1 / n_lab + 1 / n_live)
            zs.append((m_lab - m_live) / denom)
    if zs:
        mz = sum(zs) / len(zs)
        sdz = math.sqrt(sum((z - mz) ** 2 for z in zs)
                        / max(1, len(zs) - 1))
        big = sum(1 for z in zs if abs(z) > 2)
        L.append(f"MECHANISM (report-only): {len(zs)} unselected-"
                 f"candidate comparisons (skipped {skipped}): "
                 f"z mean {mz:+.2f}, sd {sdz:.2f}, "
                 f"max |z| {max(abs(z) for z in zs):.2f}, "
                 f"|z|>2: {big} ({big / len(zs):.1%}; ~5% expected "
                 f"under N(0,1))")
    else:
        L.append(f"MECHANISM: no comparable candidates "
                 f"(skipped {skipped})")
    L.append("")

    # ---- deadline accounting -------------------------------------
    batches = cands
    over180 = [c for c in batches if c["secs"] > 180]
    late_ub = sum(c["finished"] for c in over180)
    cut_worlds = sum(c["timeout_errs"] for c in batches)
    cut_cands = sum(1 for c in batches if c["timeout_errs"] > 0)
    L.append(f"DEADLINE ACCOUNTING (label deadline 300 s vs live "
             f"180 s): {len(batches)} candidate batches timed")
    L.append(f"  batches past 180 s: {len(over180)} - worlds "
             f"finished after 180 s are at most their finished "
             f"count, {late_ub} (batches at/under 180 s contribute "
             f"exactly 0; exact per-world finish times are not "
             f"recorded by the machinery)")
    L.append(f"  worlds killed at the 300 s label deadline: "
             f"{cut_worlds}, across {cut_cands} candidates")
    L.append("")

    # ---- detail ---------------------------------------------------
    L.append("V2 per-snap detail (snap: live pick / labeler pick):")
    for s in v2_snaps:
        lp = v2[s]["teacher_pick"] if s in v2 else "thin"
        L.append(f"  {s}: live={truth[s]['teacher_pick']} "
                 f"labeler={lp}")
    dis = [s for s in both
           if v1a[s]["teacher_pick"] != v1b[s]["teacher_pick"]
           or v1a[s]["overturn"] != v1b[s]["overturn"]]
    L.append(f"V1 A/B disagreements: {len(dis)} of {len(both)} "
             f"states")
    for s in dis[:40]:
        L.append(f"  {s}: A pick {v1a[s]['teacher_pick']} "
                 f"(ov {v1a[s]['overturn']}), B pick "
                 f"{v1b[s]['teacher_pick']} (ov {v1b[s]['overturn']})")
    print("\n".join(L))


if __name__ == "__main__":
    main()
