#!/usr/bin/env python3
"""Round-10 Step 0 probe: the REGISTERED INFLUENCE READ
(fix pass 5, claude-reply-9dae0e2 sec.2.3).

Runs AFTER probe_report.py in the recovery. The ten
recovered jobs (z = +Infinity in attempt 3's writer
output) all come from ONE game, 540261752, at
consecutive sampled uncontested decisions t64-t73,
each with mean_diff +2.0 at k=25 -- and at the
Horvitz-Thompson weight of 2 they could dominate the
threshold lever's read. This script makes what the
read rests on visible; it changes no rule and no
registered number:

  (a) STATE INSPECTION of the game: the capture
      driver row's actual outcome; per snap -- turn,
      prior pick vs search pick (card ids), top
      prior, the eval's per-candidate finished /
      unfinished / error counts (the eval read's own
      taxonomy, cross-checked against its published
      cand_diag), and the composition of the prior
      pick's 25 worlds: horizon draws priced -1 vs
      outright losses.
      CLASSIFICATION RULE (from the rows' own
      fields): a world is a HORIZON DRAW PRICED -1
      iff result.horizon == 1 -- such rows record
      outcome 0 (a draw) and winner 0, and the
      registered horizon value (-1) is what prices
      them in the eval read (probe_eval_analyze
      substitutes the horizon value whenever
      winner == 0). A world is an OUTRIGHT LOSS iff
      it finished with outcome == -1 and
      horizon == 0. (Attempt 3's rows distinguish
      the two exactly: every horizon == 1 row in
      evals_all carries outcome 0.)
  (b) LEAVE-ONE-GAME-OUT for each lever's per-game
      gain, computed with probe_label_analyze's OWN
      machinery (job_diffs + per_game_gain, imported
      -- the weighting is reused, never reimplemented;
      per-game totals below are per_game_gain's own
      aggregation, cross-checked against its full
      read): the LOGO range, the largest single-game
      share of the gain and which game holds it, and
      the gain + one-sided 95% lower bound with that
      game excluded.
  (c) THE HOLD RULE (process, not a change to the
      decision rule): if a lever is BUILDABLE under
      the registered rule (its probe_report gain
      lower bound > 0) but its gain lower bound is
      <= 0 with any single game excluded, this read
      prints "buildable, single-game dependent" for
      that lever, in the text output and in the JSON
      (the recovery manifest carries it forward).

Sec.14 (2026-10-29, claude-reply-28c2065 sec.3.3):
with --capalign-classes <capalign_classes.json>,
the LOGO and the hold rule run on the CAP-ALIGNED
read: job_diffs scores cap-aligned (a world wins
only if outcome > 0 and it ended by turn 61), jobs
are grouped by their cap-aligned class, drop-outs
(class null) are excluded and counted, and the
report passed in --report-json is the cap-aligned
primary report -- so the hold rule evaluates the
cap-aligned numbers, as registered. The (a)
inspection is unchanged except one added line per
snap: the search pick's eval worlds split into wins
by turn 61 vs wins after turn 61 (the sec.14
question for this game). Without the flag the read
is the fix-pass-5 read, unchanged.

Usage: probe_influence.py --jobs jobs_all.jsonl
  --labels labels_merged.jsonl --capture-games
  eval_jobs_report.json --settings settings_probe.json
  --eval-jobs eval_jobs.jsonl --evals evals_all.jsonl[.gz]
  --eval-states eval_states.jsonl
  --driver-rows cap_s1_b1.jsonl cap_s2_b1.jsonl
  --report-json probe_report.json
  [--game 540261752] [--json-out probe_influence.json]
  [--capalign-classes capalign_classes.json]
  (text to stdout; the recovery saves it)
"""
import argparse
import gzip
import importlib.util
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pla = load_mod("probe_label_analyze")
stock = pla.load_mod("analyze_l3")
s0 = pla.load_mod("stage0_report")

LEVERS = (("margin", "contested_band", "margin_lever"),
          ("threshold", "uncontested", "threshold_lever"))


def pct(x):
    return "%.4f" % x if x is not None else "n/a"


def open_text(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path)


def compute_logo(recs, cap_games, weight):
    """LOGO over cap_games for one lever's records,
    using probe_label_analyze.per_game_gain for every
    number (the full read and every exclusion read).
    Per-game totals are per_game_gain's aggregation
    (sum of diff x weight per game), cross-checked
    against the full read's gain x n_games."""
    full = pla.per_game_gain(recs, cap_games, stock,
                             weight)
    per = defaultdict(float)
    for r in recs:
        per[r["game"]] += r["diff"] * weight
    total = sum(per[g] for g in cap_games)
    if full["gain"] is not None:
        assert abs(total - full["gain"] * len(cap_games)) \
            < 1e-9, "per-game totals disagree with the " \
                    "full per_game_gain read"
    excl = {}
    for g in cap_games:
        sub_recs = [r for r in recs if r["game"] != g]
        sub_games = [x for x in cap_games if x != g]
        excl[g] = pla.per_game_gain(sub_recs, sub_games,
                                    stock, weight)
    gains = {g: e["gain"] for g, e in excl.items()}
    lbs = {g: e["lb95_1sided"] for g, e in excl.items()}
    top_game = None
    top_share = None
    if total and total > 0:
        top_game = max(cap_games, key=lambda g: per[g])
        top_share = per[top_game] / total
    min_lb_game = min(lbs, key=lambda g: lbs[g]) \
        if lbs else None
    return {"full_gain": full["gain"],
            "full_ci": full["ci"],
            "full_lb95_1sided": full["lb95_1sided"],
            "weight": weight,
            "per_game_totals": {g: per[g]
                                for g in cap_games},
            "logo_min_gain": min(gains.values())
                if gains else None,
            "logo_max_gain": max(gains.values())
                if gains else None,
            "min_lb": lbs[min_lb_game]
                if min_lb_game else None,
            "min_lb_game": min_lb_game,
            "top_game": top_game,
            "top_share": top_share,
            "top_game_excl_gain":
                gains[top_game] if top_game else None,
            "top_game_excl_lb":
                lbs[top_game] if top_game else None}


def decide_hold(report, logo_by_lever):
    """The sec.2.3 hold rule. report is the parsed
    probe_report.json; logo_by_lever maps the lever
    name to its compute_logo result. Returns
    {lever: line-or-None} -- the line is present iff
    the lever is buildable under the registered rule
    AND its lower bound is <= 0 under some single-game
    exclusion."""
    out = {}
    for lever, _cls, rep_key in LEVERS:
        line = None
        g = ((report or {}).get(rep_key) or {}).get("gain") \
            or {}
        lb = g.get("lb95_1sided")
        buildable = lb is not None and lb > 0
        logo = logo_by_lever.get(lever) or {}
        min_lb = logo.get("min_lb")
        if buildable and min_lb is not None \
                and min_lb <= 0:
            line = "buildable, single-game dependent"
        out[lever] = {"buildable": buildable,
                      "report_lb95_1sided": lb,
                      "logo_min_lb": min_lb,
                      "hold": line}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--capture-games", required=True)
    ap.add_argument("--settings", required=True)
    ap.add_argument("--eval-jobs", required=True)
    ap.add_argument("--evals", required=True)
    ap.add_argument("--eval-states", required=True)
    ap.add_argument("--driver-rows", nargs="+",
                    required=True)
    ap.add_argument("--report-json", required=True)
    ap.add_argument("--game", default="540261752")
    ap.add_argument("--json-out")
    ap.add_argument("--capalign-classes")
    a = ap.parse_args()

    settings = json.load(open(a.settings))
    unc_every = int(settings["capture"]
                    ["uncontested_every"])
    cap_games = [str(g) for g in
                 json.load(open(a.capture_games))
                 ["games_list"]]
    jobs = [json.loads(l) for l in open(a.jobs)
            if l.strip()]
    job_by_snap = {str(j["snap"]): j for j in jobs}
    report = json.load(open(a.report_json))

    lines = ["=== ROUND-10 STEP 0 PROBE -- INFLUENCE "
             "READ (claude-reply-9dae0e2 sec.2.3) ==="]

    # ---------- (a) state inspection ----------
    game = a.game
    ten = [j for j in jobs
           if str(j["game"]) == game
           and not math.isfinite(float(j["z"]))]
    ten.sort(key=lambda j: int(j["turn"]))
    snaps = [str(j["snap"]) for j in ten]
    lines.append("\n-- (a) state inspection: game %s "
                 "(%d recovered jobs: %s)"
                 % (game, len(ten),
                    ", ".join(snaps) if snaps else "none"))
    drv = None
    for path in a.driver_rows:
        for l in open(path):
            if not l.strip():
                continue
            r = json.loads(l)
            if str(r.get("gamename")) == game:
                drv = r
    if drv is None:
        lines.append("  driver row: NOT FOUND")
    else:
        lines.append(
            "  driver row: seat %s, seed %s, winner %s, "
            "draw %s, capped %s (cap_reason %s), turns "
            "%s, p1life %s, p2life %s"
            % (drv.get("seat"), drv.get("seed"),
               drv.get("winner"), drv.get("draw"),
               drv.get("capped"), drv.get("cap_reason"),
               drv.get("turns"), drv.get("p1life"),
               drv.get("p2life")))

    eval_jobs = {}
    for l in open(a.eval_jobs):
        if l.strip():
            j = json.loads(l)
            eval_jobs[str(j["snap"])] = j
    eval_states = {}
    for l in open(a.eval_states):
        if l.strip():
            s = json.loads(l)
            eval_states[str(s["snap"])] = s
    # the 10 snaps' eval rows, deduplicated by world
    # exactly as the eval read dedups them.
    worlds = defaultdict(dict)
    want = set(snaps)
    with open_text(a.evals) as f:
        for l in f:
            if not l.strip():
                continue
            r = json.loads(l)
            snap = str(r.get("snap"))
            if snap not in want:
                continue
            key = (snap, int(r["cand"]))
            if int(r["world"]) not in worlds[key]:
                worlds[key][int(r["world"])] = r.get("result")

    snap_recs = []
    for j in ten:
        snap = str(j["snap"])
        ej = eval_jobs.get(snap) or {}
        sel = [int(c) for c in ej.get("selected", [])]
        pp = int(j["prior_pick"])
        tp = int(j["teacher_pick"])
        cands = j["cands"]
        per_cand = {}
        for ci in sel:
            kinds = Counter()
            errs = 0
            for _w, res in worlds.get((snap, ci),
                                      {}).items():
                kind, _e = s0.classify(res)
                kinds[kind] += 1
                if isinstance(res, dict) \
                        and "error" in res:
                    errs += 1
            per_cand[ci] = {
                "finished": kinds["finished"],
                "unfinished": kinds["unfinished"],
                "refusal": kinds["refusal"],
                "error_rows": errs}
        # prior pick's worlds: horizon draws priced -1
        # vs outright losses (the classification rule
        # in the header).
        pw = worlds.get((snap, pp), {})
        hor = sum(1 for res in pw.values()
                  if isinstance(res, dict)
                  and int(res.get("horizon") or 0) == 1)
        losses = sum(1 for res in pw.values()
                     if isinstance(res, dict)
                     and int(res.get("finished") or 0) == 1
                     and float(res.get("outcome")) == -1.0
                     and int(res.get("horizon") or 0) == 0)
        other = len(pw) - hor - losses
        # sec.14: the search pick's worlds split at
        # the cap -- wins recorded by turn 61 (they
        # stand under the aligned rule) vs wins
        # recorded after turn 61 (post-cap: the live
        # game would have been a draw at 62).
        tw = worlds.get((snap, tp), {})
        wins_by61 = sum(
            1 for res in tw.values()
            if isinstance(res, dict)
            and int(res.get("finished") or 0) == 1
            and float(res.get("outcome")) == 1.0
            and int(res.get("turns") or 0) <= 61)
        wins_after61 = sum(
            1 for res in tw.values()
            if isinstance(res, dict)
            and int(res.get("finished") or 0) == 1
            and float(res.get("outcome")) == 1.0
            and int(res.get("turns") or 0) > 61)
        diag = (eval_states.get(snap) or {}).get(
            "cand_diag") or {}
        diag_ok = all(
            diag.get(str(ci), {}).get("finished")
            == per_cand[ci]["finished"]
            and diag.get(str(ci), {}).get("unfinished")
            == per_cand[ci]["unfinished"]
            and diag.get(str(ci), {}).get("refusal")
            == per_cand[ci]["refusal"]
            for ci in sel)
        rec = {"snap": snap, "turn": int(j["turn"]),
               "prior_pick": pp,
               "prior_card": cands[pp]["card_id"],
               "search_pick": tp,
               "search_card": cands[tp]["card_id"],
               "top_prior": float(j["top_prior"]),
               "per_candidate": {str(k): v for k, v
                                 in per_cand.items()},
               "cand_diag_agrees": diag_ok,
               "prior_worlds": len(pw),
               "prior_horizon_draws_priced_minus1": hor,
               "prior_outright_losses": losses,
               "prior_other_worlds": other,
               "search_worlds": len(tw),
               "search_wins_by_turn61": wins_by61,
               "search_wins_after_turn61": wins_after61}
        snap_recs.append(rec)
        lines.append(
            "  %s turn %d: prior pick %d (%s) vs search "
            "pick %d (%s); top prior %s"
            % (snap, rec["turn"], pp, rec["prior_card"],
               tp, rec["search_card"],
               pct(rec["top_prior"])))
        for ci in sel:
            pc = per_cand[ci]
            lines.append(
                "    cand %d: finished %d, unfinished "
                "%d, refusal %d, error rows %d%s"
                % (ci, pc["finished"], pc["unfinished"],
                   pc["refusal"], pc["error_rows"],
                   " (pick: prior)" if ci == pp else
                   " (pick: search)" if ci == tp else ""))
        lines.append(
            "    prior pick's %d worlds: %d horizon "
            "draws priced -1, %d outright losses, %d "
            "other; eval cand_diag agrees: %s"
            % (len(pw), hor, losses, other,
               "yes" if diag_ok else "NO"))
        lines.append(
            "    search pick's %d worlds: %d wins by "
            "turn 61 (stand cap-aligned), %d wins after "
            "turn 61 (post-cap; horizon draws under "
            "the aligned rule)"
            % (len(tw), wins_by61, wins_after61))

    # ---------- (b) LOGO ----------
    rows = []
    for path in a.labels:
        for l in open(path):
            if l.strip():
                rows.append(json.loads(l))
    cap_excluded = 0
    if a.capalign_classes:
        cmap = json.load(open(a.capalign_classes))
        missing = [s for s in job_by_snap if s not in cmap]
        if missing:
            print("ABORT: %d label jobs have no entry in "
                  "the cap-aligned class map (first: %s)"
                  % (len(missing), missing[0]))
            return 2
        diff_by_snap, _dc = pla.job_diffs(
            jobs, rows, s0, cap_aligned=True)
        recs_all = []
        for snap, rec in diff_by_snap.items():
            cls = cmap[snap]
            if cls is None:
                cap_excluded += 1
                continue
            r2 = dict(rec)
            r2["probe_band"] = cls
            recs_all.append(r2)
        lines.append("\n-- (b) leave-one-game-out, per "
                     "lever (CAP-ALIGNED scoring and "
                     "classes, sec.14; %d drop-out jobs "
                     "excluded)" % cap_excluded)
    else:
        diff_by_snap, _dc = pla.job_diffs(jobs, rows, s0)
        recs_all = list(diff_by_snap.values())
        lines.append("\n-- (b) leave-one-game-out, per lever")
    for lever, cls, _rk in LEVERS:
        recs = [r for r in recs_all
                if r["probe_band"] == cls]
        w = float(unc_every) if cls == "uncontested" \
            else 1.0
        logo = compute_logo(recs, cap_games, w)
        logo_by_lever[lever] = logo
        lines.append(
            "  %s (class %s, weight %g): full gain %s "
            "(lower bound %s); LOGO range [%s, %s]; "
            "largest single-game share %s (game %s); "
            "with %s excluded: gain %s, lower bound %s; "
            "weakest exclusion: game %s (lower bound %s)"
            % (lever, cls, w, pct(logo["full_gain"]),
               pct(logo["full_lb95_1sided"]),
               pct(logo["logo_min_gain"]),
               pct(logo["logo_max_gain"]),
               pct(logo["top_share"]), logo["top_game"],
               logo["top_game"],
               pct(logo["top_game_excl_gain"]),
               pct(logo["top_game_excl_lb"]),
               logo["min_lb_game"], pct(logo["min_lb"])))

    # ---------- (c) hold rule ----------
    hold = decide_hold(report, logo_by_lever)
    lines.append("\n-- (c) hold rule (sec.2.3%s)"
                 % (", evaluated on the cap-aligned "
                    "numbers, sec.14"
                    if a.capalign_classes else ""))
    hold_lines = []
    for lever, _cls, _rk in LEVERS:
        h = hold[lever]
        if h["hold"]:
            ln = "  %s: %s" % (lever, h["hold"])
            hold_lines.append(ln)
            lines.append(ln)
        else:
            why = ("not buildable (report lower bound "
                   "%s)" % pct(h["report_lb95_1sided"])
                   ) if not h["buildable"] else \
                  ("lower bound stays > 0 under every "
                   "single-game exclusion (weakest %s)"
                   % pct(h["logo_min_lb"]))
            lines.append("  %s: hold rule not triggered "
                         "-- %s" % (lever, why))

    out = {"game_inspection": {
               "game": game,
               "driver_row": drv,
               "snaps": snap_recs},
           "logo": logo_by_lever,
           "hold": hold,
           "hold_lines": hold_lines}
    if a.capalign_classes:
        out["scoring"] = "cap_aligned (sec.14): LOGO " \
                         "and hold on the cap-aligned " \
                         "read; classes from " \
                         "capalign_eval.py"
        out["capaligned_excluded_jobs"] = cap_excluded
    print("\n".join(lines))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
