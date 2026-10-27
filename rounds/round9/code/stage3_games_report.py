#!/usr/bin/env python3
"""Round-9 Stage 3 games report + pairing builder (ruling
sec.4; fork of stage2_games_report.py).

Stage 3 is the PAIRED read: calibrated teacher vs raw v10,
same seed + same seat per pair (seeds 23001-23200 x seats
{1,2} = 400 pairs, 800 games). This module:

  * builds pairing.json from the 8 block driver files
    (games_t1a/t1b/t2a/t2b.jsonl teacher, games_r1a/r1b/
    r2a/r2b.jsonl raw) plus any raw rerun files
    (games_<rblk>_rerun.jsonl). PAIRING RULES (registered):
    for each (seed, seat): teacher row = the teacher driver
    row (assert exactly one per pair in the full run); raw
    row = the raw driver row, REPLACED by its rerun row when
    one exists for that (seed, seat). Pair status:
      "scored"            both rows usable;
      "teacher_timeout"   teacher row invalid == "timeout"
                          (scored in the primary as a teacher
                          LOSS by stage3_analyze.py) unless
                          the raw row is unusable for a
                          non-timeout reason -> "excluded";
      "dropped_raw_timeout" raw row invalid == "timeout"
                          after its rerun;
      "excluded"          any row invalid for other reasons
                          (seat_mismatch, connect_failed,
                          no_result) or missing; reason
                          recorded.
    Rows are embedded in full (plus file/gamename refs) so
    pairing.json is self-contained.
  * TUPLE AUDIT (verbatim Stage 2 semantics): every teacher
    stat row (teacher blocks' search_stats.jsonl only) must
    carry "setting" == settings teacher_tuple + pinned; any
    mismatch or tuple-malformation abort row fails the
    report (exit 2) before any rate is believed.
  * band / all-rows overturn rates over completed teacher
    games only / all (Stage 2 sec.2.2 semantics);
    fallbacks; abort_reasons; R14 CANARY count as its own
    key canary_refusal_rows (stat lines lacking teacher == 1
    with fallback == "canary" -- the root-canary refusal
    records; they write no teacher row).
  * per-block + per-seat teacher W/D/L at draw 0.5 and
    draw 0; teacher timeouts counted from driver rows.
  * raw-arm accounting: raw rows completed / invalid counts
    (validity only, no rates).
  * LIFE-SCORE tallies for capped teacher games
    (ahead/behind/tied from capped rows' p1life/p2life in
    seat frame). LIFE SCORE definition (also in
    stage3_analyze.py, same words): win -> 1; capped AND
    NOT draw AND own life strictly greater than opponent's
    -> 1; else 0.

Modes:
  full (default): writes pairing.json + games_report.json.
  --pairing-only: writes pairing_draft.json only (the
  runner's RAW-RERUN pass reads it to find raw timeouts).

Usage:
  stage3_games_report.py --out-dir <games OUT>
      --settings settings_stage3.json
      --json-out games_report.json [--pairing-only]
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

BLOCKS = {  # blk -> (arm, seat)
    "t1a": ("teacher", 1), "t1b": ("teacher", 1),
    "t2a": ("teacher", 2), "t2b": ("teacher", 2),
    "r1a": ("raw", 1), "r1b": ("raw", 1),
    "r2a": ("raw", 2), "r2b": ("raw", 2),
}
OTHER_INVALID = ("seat_mismatch", "connect_failed", "no_result")


def life_score(row):
    """Life score in the row's own seat frame (see module
    docstring): win -> 1; capped AND NOT draw AND own life
    strictly greater than opponent's -> 1; else 0."""
    if not isinstance(row, dict) or "invalid" in row:
        return 0
    seat = int(row.get("seat") or 0)
    winner = int(row.get("winner") or 0)
    if seat and winner == seat:
        return 1
    if int(row.get("capped") or 0) == 1 \
            and int(row.get("draw") or 0) != 1 and winner == 0:
        own = row.get("p1life") if seat == 1 else row.get("p2life")
        opp = row.get("p2life") if seat == 1 else row.get("p1life")
        if own is not None and opp is not None and int(own) > int(opp):
            return 1
    return 0


def load_rows(out_dir):
    """Return (block_rows, rerun_rows): {(seed, seat, arm):
    (file_basename, row)} plus rerun map {(seed, seat): row}."""
    block_rows = {}
    rerun_rows = {}
    for p in sorted(glob.glob(os.path.join(out_dir, "games_*.jsonl"))):
        base = os.path.basename(p)
        if base.endswith(".manifest.json"):
            continue
        m = re.match(r"games_([tr][12][ab])\.jsonl$", base)
        mr = re.match(r"games_(r[12][ab])_rerun\.jsonl$", base)
        if not m and not mr:
            continue
        for l in open(p):
            if not l.strip():
                continue
            r = json.loads(l)
            key = (int(r["seed"]), int(r["seat"]))
            if mr:
                rerun_rows[key] = (base, r)
            else:
                arm = BLOCKS[m.group(1)][0]
                block_rows[(key[0], key[1], arm)] = (base, r)
    return block_rows, rerun_rows


def build_pairing(out_dir):
    block_rows, rerun_rows = load_rows(out_dir)
    keys = sorted({(s, st) for (s, st, _a) in block_rows}
                  | set(rerun_rows))
    pairs = []
    counts = Counter()
    for (seed, seat) in keys:
        t = block_rows.get((seed, seat, "teacher"))
        r = block_rows.get((seed, seat, "raw"))
        raw_ref = None
        if r is not None:
            raw_ref = {"file": r[0], "gamename": r[1].get("gamename"),
                       "row": r[1]}
        rr = rerun_rows.get((seed, seat))
        if rr is not None and r is not None:
            raw_ref = {"file": rr[0], "gamename": rr[1].get("gamename"),
                       "row": rr[1], "rerun_of_file": r[0],
                       "rerun_of_gamename": r[1].get("gamename")}
        trow = t[1] if t else None
        rrow = raw_ref["row"] if raw_ref else None
        status, reason = None, None
        t_inv = (trow or {}).get("invalid")
        r_inv = (rrow or {}).get("invalid")
        if trow is None:
            status, reason = "excluded", "teacher row missing"
        elif rrow is None:
            status, reason = "excluded", "raw row missing"
        elif r_inv == "timeout":
            status, reason = ("dropped_raw_timeout",
                              "raw invalid timeout after rerun")
        elif t_inv == "timeout" and r_inv is not None:
            status, reason = ("excluded",
                              "teacher timeout; raw invalid %s" % r_inv)
        elif t_inv == "timeout":
            status = "teacher_timeout"
            reason = "teacher invalid timeout (scored as teacher loss)"
        elif t_inv is not None:
            status, reason = "excluded", "teacher invalid %s" % t_inv
        elif r_inv is not None:
            status, reason = "excluded", "raw invalid %s" % r_inv
        else:
            status = "scored"
        counts[status] += 1
        pairs.append({
            "seed": seed, "seat": seat,
            "teacher": ({"file": t[0],
                         "gamename": trow.get("gamename"),
                         "row": trow} if t else None),
            "raw": raw_ref,
            "status": status, "reason": reason})
    stat_files = sorted(os.path.relpath(p, out_dir) for p in
                        glob.glob(os.path.join(
                            out_dir, "games_t*_log",
                            "search_stats.jsonl")))
    return {"pairs": pairs,
            "counts": {"pairs_attempted": len(pairs),
                       "by_status": dict(counts)},
            "stat_files": stat_files,
            "rerun_files": sorted({v[0] for v in rerun_rows.values()})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--json-out")
    ap.add_argument("--pairing-only", action="store_true")
    a = ap.parse_args()
    settings = json.load(open(a.settings))
    T = settings["teacher_tuple"]
    T_full = dict(T)
    T_full["pinned"] = 1

    pairing = build_pairing(a.out_dir)
    if a.pairing_only:
        dp = os.path.join(a.out_dir, "pairing_draft.json")
        with open(dp, "w") as f:
            json.dump(pairing, f, indent=1)
        print("pairing draft: %d pairs, statuses %s -> %s"
              % (pairing["counts"]["pairs_attempted"],
                 pairing["counts"]["by_status"], dp))
        return 0

    # ---- driver-row accounting ----------------------------
    block_rows, rerun_rows = load_rows(a.out_dir)
    t_rows = [v[1] for (s, st, arm), v in block_rows.items()
              if arm == "teacher"]
    r_rows = [v[1] for (s, st, arm), v in block_rows.items()
              if arm == "raw"]
    t_completed = [r for r in t_rows if "invalid" not in r]
    t_invalid = Counter(str(r.get("invalid")) for r in t_rows
                        if "invalid" in r)
    r_completed = [r for r in r_rows if "invalid" not in r]
    r_invalid = Counter(str(r.get("invalid")) for r in r_rows
                        if "invalid" in r)
    completed_names = {str(r["gamename"]) for r in t_completed
                       if r.get("gamename") is not None}

    def wdl(rows):
        c = Counter()
        pts05 = 0.0
        for r in rows:
            seat = int(r["seat"])
            winner = int(r.get("winner") or 0)
            if winner == 0 or int(r.get("draw") or 0) == 1:
                c["D"] += 1
                pts05 += 0.5
            elif winner == seat:
                c["W"] += 1
                pts05 += 1.0
            else:
                c["L"] += 1
        return {"W": c["W"], "D": c["D"], "L": c["L"],
                "points": pts05, "points_draw0": float(c["W"])}

    per_block, per_seat = {}, {}
    for blk, (arm, seat) in sorted(BLOCKS.items()):
        if arm != "teacher":
            continue
        rows_b = [r for (s, st, a2), (f, r) in block_rows.items()
                  if a2 == "teacher" and f == "games_%s.jsonl" % blk
                  and "invalid" not in r]
        per_block[blk] = wdl(rows_b)
    for seat in (1, 2):
        per_seat[str(seat)] = wdl(
            [r for r in t_completed if int(r["seat"]) == seat])
    teacher_outcomes = wdl(t_completed)
    gc = len(t_completed)
    teacher_outcomes["points_per_game"] = (
        teacher_outcomes["points"] / gc if gc else None)
    teacher_outcomes["points_draw0_per_game"] = (
        teacher_outcomes["points_draw0"] / gc if gc else None)

    # capped life tallies (teacher, seat frame)
    life_tally = Counter()
    for r in t_completed:
        if int(r.get("capped") or 0) == 1:
            seat = int(r["seat"])
            own = r.get("p1life") if seat == 1 else r.get("p2life")
            opp = r.get("p2life") if seat == 1 else r.get("p1life")
            if own is None or opp is None:
                life_tally["no_life_fields"] += 1
            elif int(own) > int(opp):
                life_tally["ahead"] += 1
            elif int(own) < int(opp):
                life_tally["behind"] += 1
            else:
                life_tally["tied"] += 1
            life_tally["life_score_sum"] += life_score(r)

    # ---- stat rows: tuple audit + rates (teacher only) ---
    stats = []
    for p in sorted(glob.glob(os.path.join(
            a.out_dir, "games_t*_log", "search_stats.jsonl"))):
        for l in open(p):
            if l.strip():
                stats.append(json.loads(l))
    teacher_rows = [r for r in stats if r.get("teacher") == 1]
    canary_rows = [r for r in stats if r.get("teacher") != 1
                   and r.get("fallback") == "canary"]
    contested_all = [r for r in teacher_rows if r.get("contested") == 1]
    contested = [r for r in contested_all
                 if str(r.get("game")) in completed_names]
    audit_bad = []
    for i, r in enumerate(teacher_rows):
        s = r.get("setting")
        if not isinstance(s, dict):
            audit_bad.append((i, "missing setting stamp"))
            continue
        sn = {k: s.get(k) for k in
              ("name", "hooks", "deadline_s", "horizon",
               "horizon_value", "k", "margin", "pinned")}
        if sn != dict(T_full):
            audit_bad.append((i, "setting %r != pin %r"
                              % (sn, dict(T_full))))
    malformed = [r for r in teacher_rows
                 if r.get("fallback") == "exception"
                 and "teacher tuple pin malformed"
                 in str(r.get("abort_reason", ""))]
    exceptions = [r for r in teacher_rows
                  if r.get("fallback") == "exception"]
    thin = sum(1 for r in contested if r.get("fallback") == "thin_prior")
    overturns = sum(1 for r in contested if r.get("overturn") == 1)
    thin_all = sum(1 for r in contested_all
                   if r.get("fallback") == "thin_prior")
    overturns_all = sum(1 for r in contested_all
                        if r.get("overturn") == 1)
    child_fb = sum(int(r.get("child_fallbacks") or 0)
                   for r in contested_all)
    abort_reasons = Counter()
    for r in contested_all:
        ar = r.get("abort_reasons") or {}
        if isinstance(ar, dict):
            for k, v in ar.items():
                abort_reasons[str(k)] += int(v)
    eval_fail = sum(1 for r in teacher_rows
                    if r.get("fallback") == "eval")

    with open(os.path.join(a.out_dir, "pairing.json"), "w") as f:
        json.dump(pairing, f, indent=1)
    report = {
        "games_rows": len(t_rows) + len(r_rows),
        "pairing": pairing["counts"],
        "teacher_games_rows": len(t_rows),
        "teacher_games_completed": gc,
        "teacher_games_invalid": dict(t_invalid),
        "teacher_timeouts": int(t_invalid.get("timeout", 0)),
        "games_completed": gc,
        "games_invalid": dict(t_invalid),
        "raw_games_rows": len(r_rows),
        "raw_games_completed": len(r_completed),
        "raw_games_invalid": dict(r_invalid),
        "raw_rerun_rows": len(rerun_rows),
        "teacher_outcomes_draw_scored": teacher_outcomes,
        "teacher_outcomes_per_block": per_block,
        "teacher_outcomes_per_seat": per_seat,
        "teacher_capped_life": dict(life_tally),
        "teacher_stat_rows": len(teacher_rows),
        "canary_refusal_rows": len(canary_rows),
        "rate_basis": ("band rate counts stat rows in completed "
                       "teacher games only (Stage 2 review "
                       "sec.2.2); *_all keys are the same tallies "
                       "over every stat row, co-reported"),
        "contested_rows": len(contested),
        "thin_prior_rows": thin,
        "thin_prior_rate": (thin / len(contested) if contested else None),
        "overturn_rows": overturns,
        "overturn_rate": (overturns / len(contested)
                          if contested else None),
        "overturns_per_game": (overturns / gc if gc else None),
        "contested_rows_all": len(contested_all),
        "thin_prior_rows_all": thin_all,
        "thin_prior_rate_all": (thin_all / len(contested_all)
                                if contested_all else None),
        "overturn_rows_all": overturns_all,
        "overturn_rate_all": (overturns_all / len(contested_all)
                              if contested_all else None),
        "overturns_per_game_all": (overturns_all / gc if gc else None),
        "child_fallbacks": child_fb,
        "abort_reasons": dict(abort_reasons),
        "eval_fail_rows": eval_fail,
        "exception_rows": len(exceptions),
        "tuple_audit": {
            "pin": T_full, "rows_checked": len(teacher_rows),
            "bad_rows": len(audit_bad),
            "malformed_pin_aborts": len(malformed),
            "ok": not audit_bad and not malformed},
    }
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(report, f, indent=1)
    print("pairs: %d attempted, statuses %s"
          % (pairing["counts"]["pairs_attempted"],
             pairing["counts"]["by_status"]))
    print("teacher games: %d rows, %d completed, invalid %s; "
          "teacher W/D/L %d/%d/%d = %.1f pts at draw=0.5 "
          "(%.4f/game); %.1f pts at draw=0 (W only, %.4f/game)"
          % (len(t_rows), gc, dict(t_invalid),
             teacher_outcomes["W"], teacher_outcomes["D"],
             teacher_outcomes["L"], teacher_outcomes["points"],
             teacher_outcomes["points_per_game"] or 0.0,
             teacher_outcomes["points_draw0"],
             teacher_outcomes["points_draw0_per_game"] or 0.0))
    print("raw games: %d rows, %d completed, invalid %s; "
          "rerun rows %d"
          % (len(r_rows), len(r_completed), dict(r_invalid),
             len(rerun_rows)))
    print("band rates (completed teacher games only): teacher "
          "rows %d, contested %d, thin-prior %d (%.4f), overturns "
          "%d (%.4f of contested, %.4f/game)"
          % (len(teacher_rows), len(contested), thin,
             report["thin_prior_rate"] or 0.0, overturns,
             report["overturn_rate"] or 0.0,
             report["overturns_per_game"] or 0.0))
    print("co-report (all stat rows): contested %d, thin-prior "
          "%d (%.4f), overturns %d (%.4f of contested, %.4f/game)"
          % (len(contested_all), thin_all,
             report["thin_prior_rate_all"] or 0.0, overturns_all,
             report["overturn_rate_all"] or 0.0,
             report["overturns_per_game_all"] or 0.0))
    print("capped teacher games life tallies: %s; R14 canary "
          "refusal rows %d"
          % (dict(life_tally), len(canary_rows)))
    print("tuple audit: %d rows checked, %d bad, %d malformed-"
          "pin aborts -> %s"
          % (len(teacher_rows), len(audit_bad), len(malformed),
             "OK" if report["tuple_audit"]["ok"] else "FAILED"))
    if not report["tuple_audit"]["ok"]:
        for i, why in audit_bad[:5]:
            print("  bad row %d: %s" % (i, why))
        print("ABORT: tuple audit failed - the run is not a "
              "measurement")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
