#!/usr/bin/env python3
"""fx_s2_live checker: asserts the known answers for every
case the harness ran (fixtures/fx_s2_live/fx_s2_live_main.php)
against the REAL code/search_s2.php. Usage:
  check_fx_s2_live.py <workdir>
Each case dir holds out.json (the harness summary). Prints
PASS/FAIL per check; exit 1 on any failure."""
import json
import os
import sys

FAIL = 0


def check(name, cond, detail=""):
    global FAIL
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAIL = 1


def load(work, case):
    p = os.path.join(work, case, "out.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def cmap(x):
    """Per-candidate maps arrive as JSON objects (sparse keys)
    or lists (keys 0..n) depending on PHP's encoder; normalize
    to {int: value}."""
    if isinstance(x, list):
        return {i: v for i, v in enumerate(x)}
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return {}


def last_teacher_row(out):
    rows = [r for r in out.get("stat_rows", []) if r.get("teacher") == 1]
    return rows[-1] if rows else None


def main():
    work = sys.argv[1]

    # ---- (a) the live-path valuation flip ---------------------
    o = load(work, "flip0")
    check("flip0 harness ran", o is not None)
    if o:
        r = last_teacher_row(o)
        check("flip0: hv=0.0 (draw at the 0.5-equivalent) picks "
              "the draw-heavy candidate", o.get("pick") == 1,
              "pick=%r" % o.get("pick"))
        check("flip0: overturn recorded", r and r.get("overturn") == 1)
        check("flip0: means price draws at 0",
              r and cmap(r["means"]).get(0) == -1.0
              and cmap(r["means"]).get(1) == 0.0,
              "means=%r" % (r and r.get("means")))
        check("flip0: tuple stamped (name FX-HV0, pinned)",
              r and r["setting"]["name"] == "FX-HV0"
              and r["setting"]["pinned"] == 1
              and r["setting"]["horizon_value"] == 0.0)
        check("flip0: horizon tallies (25 horizon worlds, "
              "25 draws on cand 1)",
              r and cmap(r["n_horizon"]).get(1) == 25
              and cmap(r["n_draws"]).get(1) == 25
              and cmap(r["n_horizon"]).get(0) == 0)
        check("flip0: overturn snapshot captured",
              len(o.get("snap_index", [])) == 1
              and o["snap_index"][0].get("teacher_pick") == 1)
    o = load(work, "flip1")
    check("flip1 harness ran", o is not None)
    if o:
        r = last_teacher_row(o)
        check("flip1: hv=-1 rejects the draw-heavy candidate "
              "(prior pick stands)", o.get("pick") == 0,
              "pick=%r" % o.get("pick"))
        check("flip1: no overturn", r and r.get("overturn") == 0)
        check("flip1: means price draws at -1",
              r and cmap(r["means"]).get(0) == -1.0
              and cmap(r["means"]).get(1) == -1.0,
              "means=%r" % (r and r.get("means")))
        check("flip1: tuple stamped (name FX-HVm1, hv -1)",
              r and r["setting"]["name"] == "FX-HVm1"
              and r["setting"]["horizon_value"] == -1.0)
        # ---- (2, live side) life tallies on the stat row -----
        hl = cmap((r or {}).get("horizon_life", {})).get(1, {})
        check("flip1: horizon life tallies (25 behind, sums "
              "200/350)", hl.get("behind") == 25
              and hl.get("ahead") == 0 and hl.get("tied") == 0
              and hl.get("life_root_sum") == 200
              and hl.get("life_opp_sum") == 350,
              "horizon_life[1]=%r" % hl)
        check("flip1: no snapshot (no overturn)",
              len(o.get("snap_index", [])) == 0)

    # ---- unpinned == the legacy live teacher ------------------
    o = load(work, "unpinned")
    check("unpinned harness ran", o is not None)
    if o:
        r = last_teacher_row(o)
        check("unpinned: legacy behavior (win candidate "
              "overturns)", o.get("pick") == 1
              and r and r.get("overturn") == 1)
        check("unpinned: stamp names the unpinned tuple",
              r and r["setting"]["name"] == "unpinned"
              and r["setting"]["pinned"] == 0
              and r["setting"]["hooks"] == 4000
              and r["setting"]["horizon"] == 0
              and r["setting"]["k"] == 25
              and r["setting"]["margin"] == 1.5)
        check("unpinned: no horizon worlds recorded",
              r and cmap(r["n_horizon"]).get(1) == 0)

    # ---- (b) tuple pin / mismatch abort ------------------------
    for case in ("pin_bad", "pin_bad_k"):
        o = load(work, case)
        check("%s harness ran" % case, o is not None)
        if o:
            r = last_teacher_row(o)
            check("%s: Decide aborts before any decision "
                  "(pick null)" % case, o.get("pick") is None)
            check("%s: abort row written, fallback=exception, "
                  "stamp 'malformed', reason names the tuple"
                  % case,
                  r and r.get("fallback") == "exception"
                  and r["setting"]["name"] == "malformed"
                  and "teacher tuple pin malformed"
                  in str(r.get("abort_reason", "")),
                  "row=%r" % (r and {k: r.get(k) for k in
                                     ("fallback", "abort_reason")}))
            check("%s: no contested row was produced" % case,
                  not any(x.get("contested") == 1
                          for x in o.get("stat_rows", [])))

    # ---- (1) the children's hook guard reads the LIVE tuple ---
    o = load(work, "hooks_live")
    check("hooks_live harness ran", o is not None)
    if o:
        r = last_teacher_row(o)
        check("hooks_live: 6,000-hook worlds complete under "
              "the pinned 8,000 (pick = hook candidate)",
              o.get("pick") == 1 and r and r.get("overturn") == 1
              and cmap(r["n_worlds"]).get(1) == 25,
              "pick=%r n_worlds=%r" % (o.get("pick"),
                                       r and r.get("n_worlds")))
    o = load(work, "hooks_low")
    check("hooks_low harness ran", o is not None)
    if o:
        r = last_teacher_row(o)
        check("hooks_low: the same worlds abort under a 4,000 "
              "pin (prior pick stands, aborts tallied)",
              o.get("pick") == 0 and r
              and r.get("errors", 0) >= 25
              and int(r.get("abort_reasons", {}).get("abort", 0)) >= 25,
              "pick=%r errors=%r abort_reasons=%r"
              % (o.get("pick"), r and r.get("errors"),
                 r and r.get("abort_reasons")))

    # ---- (d) label-path default regression ---------------------
    o = load(work, "label_default")
    check("label_default harness ran", o is not None)
    if o:
        rows = o.get("label_rows", [])
        by = {}
        for r in rows:
            by.setdefault(int(r["cand"]), []).append(r)
        c0 = by.get(0, [])
        check("label_default: cand 0 worlds finish as losses "
              "(horizon off)", len(c0) == 3 and all(
                  x["result"].get("finished") == 1
                  and x["result"].get("outcome") == -1.0
                  and x["result"].get("horizon") == 0
                  for x in c0), "rows=%d" % len(c0))
        c1 = by.get(1, [])
        check("label_default: cand 1 (draw script) worlds do "
              "NOT finish with the horizon off, and carry no "
              "life fields", len(c1) == 3 and all(
                  x["result"].get("finished") == 0
                  and x["result"].get("horizon") == 0
                  and "life_root" not in x["result"]
                  for x in c1), "rows=%d" % len(c1))
        c2 = by.get(2, [])
        check("label_default: cand 2 (6,000-hook script) aborts "
              "at the DEFAULT 4,000 hook budget",
              len(c2) == 3 and all(
                  x["result"].get("error") == "abort"
                  for x in c2), "rows=%d" % len(c2))

    # ---- (c) life totals on planted horizon-ended worlds -------
    o = load(work, "label_horizon")
    check("label_horizon harness ran", o is not None)
    if o:
        rows = o.get("label_rows", [])
        by = {}
        for r in rows:
            by.setdefault(int(r["cand"]), []).append(r)
        c1 = by.get(1, [])
        check("label_horizon: horizon-ended worlds record "
              "life_root=8, life_opp=14 on every row",
              len(c1) == 3 and all(
                  x["result"].get("finished") == 1
                  and x["result"].get("horizon") == 1
                  and x["result"].get("life_root") == 8
                  and x["result"].get("life_opp") == 14
                  for x in c1), "rows=%d" % len(c1))
        c0 = by.get(0, [])
        check("label_horizon: non-horizon worlds carry NO life "
              "fields", len(c0) == 3 and all(
                  x["result"].get("finished") == 1
                  and x["result"].get("horizon") == 0
                  and "life_root" not in x["result"]
                  for x in c0), "rows=%d" % len(c0))

    print("FX-S2-LIVE: %s" % ("ALL PASS" if not FAIL else "FAILURES"))
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
