#!/usr/bin/env python3
"""Gate analysis (Claude G2/G5/G7, round-3 registration).

Unit: (seed, seat). Each unit pairs one teacher game with one raw
game on the same seed and seat, both against the heuristic.

Scoring (timeout ruling, registered before the fleet):
  - outright win for the arm's learner (winner == seat): 1
  - draw: 0.5
  - engine cap (capped row): 0.5 for that arm - caps are outcomes
  - teacher wall-clock timeout: teacher 0 (primary); the pair is
    dropped in the sensitivity table
  - raw wall-clock timeout: raw 0.5 (the fleet re-runs the game
    once; a second hang is scored 0.5 and the pair kept)
  - any other invalid row (connect_failed, seat_mismatch,
    no_result): the unit is UNSCORED - counted and reported,
    never silently dropped

Gravy fleet-alignment addition (round 7): the primary above is
unchanged. A CO-REPORT block additionally prints the paired delta
under non-win scoring (score_arm_nonwin: identical to score_arm
except an engine-capped row scores 0 for that arm instead of 0.5),
pooled and per seat, with the same cluster bootstrap. The co-report
carries no band read; the registered bands apply to the primary.

Primary: paired delta = mean(teacher score - raw score), per seat
and pooled, with a bootstrap CI clustered by seed (seeds resampled
with replacement; every unit of a drawn seed enters with its
multiplicity). Also: discordant counts (units where the teacher
score strictly exceeds the raw score, vs the reverse) with an
exact two-sided sign test (binomial, p = 0.5).

Registered bands (verbatim from the registration):
  delta >= +0.05 with CI lower > 0     -> CONVERTS
  CI lower > 0 but delta < +0.05       -> REAL BUT SMALL
  CI includes 0 with upper < +0.10     -> PROJECTION OVERSTATED
  delta > +0.20                        -> IMPEACH BEFORE READING
If teacher timeouts exceed 2% of teacher games the gate is
INCONCLUSIVE whatever delta says (timeout ruling 2).

Companion monitors:
  - G5 calibration: teacher stat rows' prior-pick rollout mean
    (rollout outcomes are +1 learner win / -1 loss / 0 unfinished,
    so the predicted win probability is (mean + 1) / 2), binned by
    the decision's ordinal among the game's contested decisions,
    against the realized outcome of that game for the learner
    (win 1 / draw 0.5 / loss 0).
  - Overturn rate: overturn rows / contested rows, per arm-seat
    file and pooled (expect ~5%).
  - G7 coverage: canary refusals per arm-seat (refusals / root
    calls, root calls = teacher rows + canary rows, the
    count_canary.py construction), branches above 5% named,
    child aborts by reason and by candidate, det_persisted
    presence on contested rows.

Registry gate (G9): refuses to run unless every gamename in the
row files is present in the do-not-train registry given with
--registry. The fleet registers all gate game ids before any
analysis runs; this check is the enforcement.

Usage:
  analyze_gate.py --rows ROWS.jsonl [ROWS.jsonl ...] \
      --stats STATS.jsonl [STATS.jsonl ...] --registry REG.json \
      [--out REPORT.txt] [--boot 10000] [--boot-seed 20261019]
Rows are paired_driver.py outputs (arm field on each row); stats
are the teacher arms' search_stats.jsonl files.
"""
import argparse
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

CAL_BINS = [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 4, "4"),
            (5, 5, "5"), (6, 10, "6-10"), (11, 20, "11-20"),
            (21, 40, "21-40"), (41, 10 ** 9, "41+")]


def load_jsonl(path):
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def score_arm(row, arm):
    """(score, flags) per the registered scoring; score None when
    the unit cannot be scored for this arm."""
    if row is None:
        return None, {"missing_row": True}
    inv = row.get("invalid")
    if inv == "timeout":
        return (0.0 if arm == "teacher" else 0.5), {"wall_timeout": True}
    if inv:
        return None, {"invalid": inv}
    if row.get("capped"):
        return 0.5, {"capped": row.get("cap_reason")}
    w = row.get("winner")
    if row.get("draw") or w in (0, None):
        return 0.5, {"draw": True}
    return (1.0 if int(w) == int(row["seat"]) else 0.0), {}


def score_arm_nonwin(row, arm):
    """Non-win variant of score_arm (fleet-alignment co-report):
    identical in every branch except the engine-cap branch, which
    scores 0 for that arm instead of 0.5. Draws without a cap keep
    0.5; the timeout rulings are unchanged."""
    if row is None:
        return None, {"missing_row": True}
    inv = row.get("invalid")
    if inv == "timeout":
        return (0.0 if arm == "teacher" else 0.5), {"wall_timeout": True}
    if inv:
        return None, {"invalid": inv}
    if row.get("capped"):
        return 0.0, {"capped": row.get("cap_reason")}
    w = row.get("winner")
    if row.get("draw") or w in (0, None):
        return 0.5, {"draw": True}
    return (1.0 if int(w) == int(row["seat"]) else 0.0), {}


def learner_result(row):
    """Realized game outcome for the learner: win 1, draw 0.5,
    loss 0 (calibration target). None when unscorable."""
    s, _ = score_arm(row, row.get("arm", "teacher"))
    return s


def binom_two_sided(b, c):
    """Exact two-sided sign test: b successes in b+c trials, p=.5."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def bootstrap_ci(deltas_by_seed, boot, rng):
    """Cluster bootstrap by seed. deltas_by_seed: {seed: [deltas]}.
    Returns (lo, hi) percentile 2.5/97.5 of the resampled mean."""
    seeds = sorted(deltas_by_seed)
    if not seeds:
        return (float("nan"), float("nan"))
    means = []
    for _ in range(boot):
        tot, cnt = 0.0, 0
        for _ in range(len(seeds)):
            s = seeds[rng.randrange(len(seeds))]
            for d in deltas_by_seed[s]:
                tot += d
                cnt += 1
        means.append(tot / cnt if cnt else float("nan"))
    means.sort()
    lo = means[int(0.025 * (boot - 1))]
    hi = means[int(0.975 * (boot - 1))]
    return lo, hi


def band_read(delta, lo, hi):
    if delta != delta or lo != lo:
        return "NO READ (no scored units)"
    if delta > 0.20:
        return "IMPEACH BEFORE READING (delta > +0.20)"
    if lo > 0 and delta >= 0.05:
        return "CONVERTS (delta >= +0.05, CI lower > 0)"
    if lo > 0:
        return "REAL BUT SMALL (CI lower > 0, delta < +0.05)"
    if lo <= 0 <= hi and hi < 0.10:
        return "PROJECTION OVERSTATED (CI includes 0, upper < +0.10)"
    return "NO REGISTERED BAND (CI includes 0, upper >= +0.10)"


def stat_mean(means, idx):
    """Teacher stat means: a list indexed by candidate, or a dict
    with string keys when sparse (PHP assoc encoding)."""
    if means is None:
        return None
    if isinstance(means, dict):
        v = means.get(str(idx))
        return None if v is None else float(v)
    if isinstance(means, list) and 0 <= idx < len(means):
        v = means[idx]
        return None if v is None else float(v)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", required=True)
    ap.add_argument("--stats", nargs="+", default=[])
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--boot-seed", type=int, default=20261019)
    a = ap.parse_args()

    lines = []

    def emit(s=""):
        lines.append(s)

    # ---- registry gate (G9) ------------------------------------
    reg = {}
    with open(a.registry) as f:
        reg = json.load(f).get("games", {})
    units = {}
    game_names = set()
    for path in a.rows:
        for r in load_jsonl(path):
            key = (r.get("seed"), r.get("seat"))
            units.setdefault(key, {})[r.get("arm")] = r
            if r.get("gamename") is not None:
                game_names.add(str(r["gamename"]))
    missing = sorted(g for g in game_names if g not in reg)
    if missing:
        emit("REGISTRY GATE: REFUSING TO ANALYZE - %d game id(s) "
             "not in the registry (first: %s). Register all gate "
             "game ids before analysis (G9)." % (len(missing), missing[0]))
        text = "\n".join(lines) + "\n"
        if a.out:
            open(a.out, "w").write(text)
        print(text)
        return 2

    # ---- scoring ------------------------------------------------
    scored = []
    unscored = []
    teacher_timeouts = 0
    teacher_games = 0
    raw_timeout_units = []
    for key in sorted(units):
        t = units[key].get("teacher")
        r = units[key].get("raw")
        if t is not None:
            teacher_games += 1
            if t.get("invalid") == "timeout":
                teacher_timeouts += 1
        ts, tf = score_arm(t, "teacher")
        rs, rf = score_arm(r, "raw")
        if ts is None or rs is None:
            unscored.append((key, tf, rf))
            continue
        tn, _ = score_arm_nonwin(t, "teacher")
        rn, _ = score_arm_nonwin(r, "raw")
        scored.append({"seed": key[0], "seat": key[1], "t": ts,
                       "r": rs, "d": ts - rs, "tflags": tf,
                       "rflags": rf, "trow": t, "rrow": r,
                       "tn": tn, "rn": rn, "dn": tn - rn})
        if rf.get("wall_timeout"):
            raw_timeout_units.append(key)

    emit("=" * 72)
    emit("GATE ANALYSIS - unit (seed, seat); paired teacher vs raw")
    emit("=" * 72)
    emit("units total: %d | scored: %d | unscored: %d"
         % (len(units), len(scored), len(unscored)))
    for key, tf, rf in unscored:
        emit("  UNSCORED unit seed=%s seat=%s teacher=%s raw=%s"
             % (key[0], key[1], tf, rf))
    n_capped = sum(1 for s in scored
                   if s["tflags"].get("capped") or s["rflags"].get("capped"))
    emit("capped games among scored units: %d (scored 0.5 per ruling)"
         % n_capped)
    emit("")

    def delta_block(sel, label, dkey="d", tkey="t", rkey="r"):
        sub = [s for s in scored if sel(s)]
        if not sub:
            emit("%s: no scored units" % label)
            return None
        d = sum(s[dkey] for s in sub) / len(sub)
        by_seed = defaultdict(list)
        for s in sub:
            by_seed[s["seed"]].append(s[dkey])
        rng = random.Random(a.boot_seed)
        lo, hi = bootstrap_ci(by_seed, a.boot, rng)
        tw = sum(s[tkey] for s in sub) / len(sub)
        rw = sum(s[rkey] for s in sub) / len(sub)
        emit("%s: n=%d units, %d seeds | teacher %.4f - raw %.4f "
             "= delta %+.4f | bootstrap CI (clustered by seed, "
             "B=%d) [%+.4f, %+.4f]"
             % (label, len(sub), len(by_seed), tw, rw, d, a.boot,
                lo, hi))
        return d, lo, hi

    emit("PRIMARY - paired delta (teacher score - raw score)")
    pooled = delta_block(lambda s: True, "pooled      ")
    delta_block(lambda s: s["seat"] == 1, "seat 1      ")
    delta_block(lambda s: s["seat"] == 2, "seat 2      ")
    emit("")
    emit("CO-REPORT - paired delta under NON-WIN scoring (capped = 0 "
         "for both arms; draws and timeout rulings unchanged; no "
         "band read attaches to the co-report)")
    delta_block(lambda s: True, "pooled      ", "dn", "tn", "rn")
    delta_block(lambda s: s["seat"] == 1, "seat 1      ",
                "dn", "tn", "rn")
    delta_block(lambda s: s["seat"] == 2, "seat 2      ",
                "dn", "tn", "rn")
    emit("")

    b = sum(1 for s in scored if s["t"] > s["r"])
    c = sum(1 for s in scored if s["t"] < s["r"])
    ties = sum(1 for s in scored if s["t"] == s["r"])
    p = binom_two_sided(b, c)
    emit("DISCORDANT: teacher>raw %d | teacher<raw %d | tied %d | "
         "exact sign test (two-sided) p = %.4f" % (b, c, ties, p))
    emit("")

    emit("REGISTERED BANDS:")
    emit("  delta >= +0.05 with CI lower bound > 0 -> converts")
    emit("  lower bound > 0 but delta < +0.05      -> real but small")
    emit("  CI includes 0 with upper bound < +0.10 -> the projection "
         "overstated conversion")
    emit("  delta > +0.20                          -> impeach before "
         "reading")
    if pooled:
        emit("READ (pooled): %s" % band_read(*pooled))
    emit("")

    # ---- teacher timeouts + sensitivity -------------------------
    trate = (100.0 * teacher_timeouts / teacher_games
             if teacher_games else 0.0)
    emit("TEACHER TIMEOUTS: %d of %d teacher games (%.2f%%)"
         % (teacher_timeouts, teacher_games, trate))
    if teacher_games and teacher_timeouts / teacher_games > 0.02:
        emit("  ** GATE INCONCLUSIVE per timeout ruling 2 (teacher "
             "timeouts > 2%%), whatever delta says. **")
    sens = [s for s in scored if not s["tflags"].get("wall_timeout")]
    if len(sens) != len(scored):
        d = sum(s["d"] for s in sens) / len(sens) if sens else float("nan")
        by_seed = defaultdict(list)
        for s in sens:
            by_seed[s["seed"]].append(s["d"])
        rng = random.Random(a.boot_seed)
        lo, hi = bootstrap_ci(by_seed, a.boot, rng)
        emit("SENSITIVITY (teacher-timeout pairs dropped): n=%d "
             "delta %+.4f CI [%+.4f, %+.4f]" % (len(sens), d, lo, hi))
    emit("")

    # ---- raw-timeout defect check (ruling 3) --------------------
    if raw_timeout_units:
        emit("RAW TIMEOUTS (scored 0.5 after one re-run): %s"
             % (raw_timeout_units,))
    emit("")

    # ---- stat-file monitors (coverage, overturns, calibration) --
    emit("TEACHER STAT MONITORS")
    game_result = {}
    for key, arms in units.items():
        t = arms.get("teacher")
        if t is not None and t.get("gamename") is not None:
            lr = learner_result(t)
            if lr is not None:
                game_result[str(t["gamename"])] = lr
    tot_contested = 0
    tot_overturns = 0
    cal = defaultdict(lambda: [0.0, 0.0, 0])
    raw_timeout_games = {str(units[k]["raw"].get("gamename"))
                         for k in raw_timeout_units
                         if units[k].get("raw") is not None}
    teacher_game_overturns = Counter()
    for path in a.stats:
        rows = load_jsonl(path)
        teacher_rows = [r for r in rows if r.get("teacher") == 1]
        canary_rows = [r for r in rows if r.get("fallback") == "canary"]
        contested = [r for r in teacher_rows if r.get("contested") == 1]
        overturns = [r for r in contested
                     if r.get("overturn") == 1
                     or (r.get("pick") is not None
                         and r.get("prior_pick") is not None
                         and r.get("pick") != r.get("prior_pick"))]
        root_calls = len(teacher_rows) + len(canary_rows)
        rate = 100.0 * len(canary_rows) / max(1, root_calls)
        tb = Counter(r.get("branch") for r in teacher_rows)
        cb = Counter(r.get("branch") for r in canary_rows)
        hot = []
        for br in sorted(set(tb) | set(cb), key=str):
            d = tb.get(br, 0) + cb.get(br, 0)
            br_rate = 100.0 * cb.get(br, 0) / max(1, d)
            if br_rate > 5.0:
                hot.append("%s %.2f%% (%d/%d)" % (br, br_rate,
                                                  cb.get(br, 0), d))
        abort_reasons = Counter()
        abort_by_cand = Counter()
        for r in contested:
            ar = r.get("abort_reasons")
            if isinstance(ar, dict):
                abort_reasons.update({k: int(v) for k, v in ar.items()})
            elif isinstance(ar, list):
                abort_reasons.update(ar)
            ac = r.get("abort_by_cand")
            if isinstance(ac, dict):
                abort_by_cand.update({k: int(v) for k, v in ac.items()})
            elif isinstance(ac, list):
                abort_by_cand.update(ac)
        det_missing = sum(1 for r in contested
                          if r.get("det_persisted") != 1)
        child_fb = sum(int(r.get("child_fallbacks") or 0)
                       for r in contested)
        label = os.path.basename(os.path.dirname(path)) or os.path.basename(path)
        emit("  [%s] root_calls=%d canary=%d refusal_rate=%.3f%% "
             "(cap 2%%) | contested=%d overturns=%d overturn_rate=%.2f%%"
             % (label, root_calls, len(canary_rows), rate,
                len(contested), len(overturns),
                100.0 * len(overturns) / max(1, len(contested))))
        if hot:
            emit("    branches > 5%% refusals: %s" % "; ".join(hot))
        emit("    abort_reasons=%s abort_by_cand=%s child_fallbacks=%d "
             "det_persisted_missing=%d"
             % (dict(abort_reasons), dict(abort_by_cand), child_fb,
                det_missing))
        tot_contested += len(contested)
        tot_overturns += len(overturns)
        for r in overturns:
            teacher_game_overturns[str(r.get("game"))] += 1
        # calibration: contested rows in file order within each game
        by_game = defaultdict(list)
        for r in rows:
            if r.get("teacher") == 1 and r.get("contested") == 1:
                by_game[str(r.get("game"))].append(r)
        for g, grows in by_game.items():
            realized = game_result.get(g)
            if realized is None:
                continue
            for i, r in enumerate(grows, start=1):
                m = stat_mean(r.get("means"), r.get("prior_pick"))
                if m is None:
                    continue
                pred = (m + 1.0) / 2.0
                for blo, bhi, blabel in CAL_BINS:
                    if blo <= i <= bhi:
                        cal[blabel][0] += pred
                        cal[blabel][1] += realized
                        cal[blabel][2] += 1
                        break
    if a.stats:
        emit("  POOLED: contested=%d overturns=%d overturn_rate=%.2f%% "
             "(expect ~5%%)" % (tot_contested, tot_overturns,
                                100.0 * tot_overturns / max(1, tot_contested)))
    emit("")
    # ruling 3 defect: raw hang, teacher finished the same seed's
    # game with no overturn at all -> contradicts the pre-gate.
    defect = False
    for key in raw_timeout_units:
        t = units[key].get("teacher")
        if t is not None and t.get("invalid") != "timeout":
            g = str(t.get("gamename"))
            if teacher_game_overturns.get(g, 0) == 0:
                emit("  ** DEFECT (ruling 3): raw timed out on seed=%s "
                     "seat=%s while the teacher completed that game "
                     "with zero overturns. Stop and treat as a "
                     "machinery defect. **" % (key[0], key[1]))
                defect = True
    emit("G5 CALIBRATION - prior-pick rollout mean by decision ordinal")
    emit("  predicted = (prior-pick rollout mean + 1) / 2 (rollout "
         "outcomes are +1/-1/0); realized = the game's outcome for "
         "the learner (win 1 / draw 0.5 / loss 0)")
    emit("  %-6s %10s %10s %8s" % ("bin", "pred", "realized", "n"))
    for _, _, blabel in CAL_BINS:
        sp, sr, n = cal[blabel]
        if n:
            emit("  %-6s %10.4f %10.4f %8d"
                 % (blabel, sp / n, sr / n, n))
    if defect:
        emit("")
        emit("RESULT: DEFECT FLAGGED (see ruling-3 line above)")
    text = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
