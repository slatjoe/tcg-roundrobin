#!/usr/bin/env python3
"""fx_stage1_analyze - known-answer fixture for
code/stage1_analyze.py (the clause-8 second placement, the
per-state completion metric with its candidate-level and
pooled diagnostics, the B0-control selection exclusion,
the selection rule with its tie-breaks, and the
horizon-value co-reports).

Planted truths (hand-computed; the arithmetic is inline):

Scenario A - metric discrimination + p95 tie-break + the
  horizon-value flip.
  B0: state s1's prior finishes 19/25 (thin) while every
  other candidate finishes 25/25. Per-state completion
  (the selection metric): s1 does not complete, s2-s4 do
  -> 3/4 = 0.75 (< 0.95 bar: does NOT qualify). The two
  diagnostics part company with it by construction: the
  candidate-level rate is 7/8 = 0.875 and the pooled
  finished share is 194/200 = 0.97 (>= bar) - the analyzer
  must qualify on the per-state figure alone. thin-prior
  1/4. State s2 is the valuation flip: prior 15W/10L (mean
  +0.2 under both prices); challenger 15W/5 draws/5L -
  priced draw = 0 its mean is +0.2 (ties the prior, no
  overturn); priced 0.5 its mean is +0.4 and the paired
  test over the 25 shared worlds (five +1 diffs, twenty
  0s; mean 0.2, SE 0.0816, 1.5 SE = 0.1225) overturns. So
  for s2: overturn_half True, overturn_draw0 False; B0's
  non-thin states are s2, s3, s4, so overturn_half = 1/3,
  overturn_draw0 = 0.
  P1 and P2 both complete everything and tie on mean wall
  (6.0 s); P1's p95 is 8.4 (walls 5,5,5,9), P2's is 6.0
  (walls 6,6,6,6) - selection must pick P2 on the p95
  tie-break. EXP (mean 8.0) qualifies but is dearer.

Scenario B - max tie-break. Five states; X walls (s)
  4,4,4,4,24 and Y walls 3,3,3,8,23: both mean 8.0, both
  p95 = 0.2*s[3] + 0.8*s[4] = 20.0; max 24 vs 23 - the
  selection must pick Y on the max tie-break.

Scenario C - no qualifier + the tuple audit. Setting Z
  (a +H candidate) leaves one candidate at 10/25 finished
  in one of two states: per-state completion 1/2 = 0.5,
  candidate-level 3/4 = 0.75 - verdict must be
  NO CALIBRATED SETTING. A copy with one world row's tuple
  corrupted (hooks 9999) must abort (exit 2).

Scenario D - the review's divergence case
  (claude-reply-edddf5e sec.1): candidate-level >= 0.95
  but per-state < 0.95 must NOT qualify. 20 states, 2
  candidates each. SBAD breaks candidate 1 in 2 states:
  candidate-level 38/40 = 0.95 (clears the bar as a
  diagnostic) but per-state 18/20 = 0.90 - does not
  qualify. SGOOD breaks candidate 1 in 1 state:
  candidate-level 39/40 = 0.975, per-state 19/20 = 0.95
  - qualifies. SBAD is the cheaper setting (walls 5 s vs
  9 s): if it wrongly qualified it would be selected;
  the selection must be SGOOD.

Scenario E - the control is never selected
  (claude-reply-edddf5e sec.2). B0 completes every state
  (per-state 1.0, so it meets the metric) and is by far
  the cheapest (walls 1 s vs H1's 9 s). B0 must be read
  as the control (role, its completion reported) and the
  selection must skip it and pick H1.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYZER = os.path.join(HERE, "..", "code", "stage1_analyze.py")
FAILS = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILS.append(name)


def fin(outcome):
    return {"finished": 1, "outcome": outcome,
            "winner": 1 if outcome > 0 else (2 if outcome < 0 else 0),
            "fallbacks": 0}


def wrows(tuple_, snap, cand, cells):
    """cells: 25 entries, each an outcome float or
    ('err', class)."""
    out = []
    for w, c in enumerate(cells):
        res = {"error": c[1]} if isinstance(c, tuple) else fin(c)
        out.append({"snap": snap, "cand": cand, "world": w,
                    "result": res, "setting": tuple_})
    return out


def stat(tuple_, snap, game, player, cells_by_cand, wall_ms):
    finc, rowc, errs = {}, {}, {}
    for ci, cells in cells_by_cand.items():
        rowc[str(ci)] = len(cells)
        finc[str(ci)] = sum(1 for c in cells
                            if not isinstance(c, tuple))
        for c in cells:
            if isinstance(c, tuple):
                errs[c[1]] = errs.get(c[1], 0) + 1
    return {"snap": snap, "game": game, "player": player,
            "branch": "P", "setting": tuple_, "wall_ms": wall_ms,
            "cand_finished": finc, "cand_rows": rowc,
            "errors": errs, "fallbacks": 0, "prior_pick": 0,
            "selected": sorted(cells_by_cand)}


def job(snap, game, player):
    return {"snap_dir": "/fx/" + snap, "snap": snap,
            "game": game, "player": player, "branch": "P",
            "turn": 7, "cands": [0, 1, 2], "selected": [0, 1],
            "prior_pick": 0}


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def run_analyzer(d, panel, settings, tag):
    out_json = os.path.join(d, "report_%s.json" % tag)
    p = subprocess.run(
        [sys.executable, ANALYZER, "--panel", panel,
         "--settings", settings, "--evals-dir", d,
         "--json-out", out_json],
        capture_output=True, text=True)
    rep = None
    if os.path.exists(out_json):
        rep = json.load(open(out_json))
    return p, rep


FULL0 = [1.0] * 13 + [-1.0] * 12
FULL1 = [1.0] * 12 + [-1.0] * 13
FLIP0 = [1.0] * 15 + [-1.0] * 10
FLIP1 = [1.0] * 15 + [0.0] * 5 + [-1.0] * 5
THIN0 = [1.0] * 10 + [-1.0] * 9 + [("err", "abort")] * 6

CONST = {"validity_floor": 20, "completion_bar": 0.95,
         "margin_se": 1.5, "fleet_thin_prior_ref": 0.317}


def T(name, hooks, dl, hz, hv):
    return {"name": name, "hooks": hooks, "deadline_s": dl,
            "horizon": hz, "horizon_value": hv, "k": 25}


def scenario(root, states, settings, worlds, walls):
    """worlds: {(setting_name, snap): {cand: cells}};
    walls: {(setting_name, snap): wall_ms}."""
    os.makedirs(root)
    panel = os.path.join(root, "panel.jsonl")
    write_jsonl(panel, [job(s, g, p) for s, g, p in states])
    spath = os.path.join(root, "settings.json")
    with open(spath, "w") as f:
        json.dump({"constants": CONST, "settings": settings}, f)
    for st in settings:
        nm = st["name"]
        wr, sr = [], []
        for s, g, p in states:
            cells = worlds[(nm, s)]
            for ci, cl in cells.items():
                wr += wrows(st, s, ci, cl)
            sr.append(stat(st, s, g, p, cells, walls[(nm, s)]))
        write_jsonl(os.path.join(root, "evals_%s.jsonl" % nm), wr)
        write_jsonl(os.path.join(root, "stats_%s.jsonl" % nm), sr)
    return panel, spath


def main():
    tmp = tempfile.mkdtemp(prefix="fx_s1_")
    # ---------------- Scenario A
    statesA = [("s1", "g1", 1), ("s2", "g1", 2),
               ("s3", "g2", 1), ("s4", "g2", 2)]
    settingsA = [T("B0", 4000, 180, 0, 0), T("P1", 4000, 180, 62, -1),
                 T("P2", 8000, 180, 62, -1), T("EXP", 16000, 360, 62, -1)]
    worldsA, wallsA = {}, {}
    full = {0: FULL0, 1: FULL1}
    for st in settingsA:
        for s, _, _ in statesA:
            worldsA[(st["name"], s)] = dict(full)
    worldsA[("B0", "s1")] = {0: THIN0, 1: FULL1}
    worldsA[("B0", "s2")] = {0: FLIP0, 1: FLIP1}
    for s, _, _ in statesA:
        wallsA[("B0", s)] = 10000
        wallsA[("EXP", s)] = 8000
        wallsA[("P2", s)] = 6000
    wallsA[("P1", "s1")] = 5000
    wallsA[("P1", "s2")] = 5000
    wallsA[("P1", "s3")] = 5000
    wallsA[("P1", "s4")] = 9000
    dA = os.path.join(tmp, "scA")
    panelA, setA = scenario(dA, statesA, settingsA, worldsA, wallsA)
    pA, repA = run_analyzer(dA, panelA, setA, "A")
    check("A analyzer exit 0", pA.returncode == 0,
          pA.stdout[-200:] + pA.stderr[-200:])
    b0 = repA["settings"]["B0"]
    check("A1 B0 completion == 0.75 (per-state metric)",
          abs(b0["completion"] - 0.75) < 1e-12, str(b0["completion"]))
    check("A1 B0 does not qualify", b0["qualifies"] is False)
    check("A1b B0 candidate-level == 0.875 (diagnostic)",
          abs(b0["candidate_completion"] - 0.875) < 1e-12,
          str(b0["candidate_completion"]))
    check("A2 B0 pooled share == 0.97 (diagnostic)",
          abs(b0["pooled_finished_share"] - 0.97) < 1e-12,
          str(b0["pooled_finished_share"]))
    check("A3 B0 thin-prior == 0.25",
          abs(b0["thin_prior_rate"] - 0.25) < 1e-12)
    s2 = [r for r in repA["states"]
          if r.get("snap") == "s2" and r["setting"] == "B0"][0]
    check("A4 s2 flip: overturn_draw0 False, overturn_half True",
          s2["overturn_draw0"] is False and s2["overturn_half"] is True,
          json.dumps({k: s2[k] for k in
                      ("overturn_draw0", "overturn_half")}))
    m1 = s2["means"]["1"]
    check("A5 s2 challenger means: draw0 0.2, half 0.4",
          abs(m1["draw0"] - 0.2) < 1e-9 and abs(m1["half"] - 0.4) < 1e-9,
          json.dumps(m1))
    check("A6 B0 overturn_half == 1/3, overturn_draw0 == 0",
          abs(b0["overturn_half"] - 1 / 3) < 1e-9
          and b0["overturn_draw0"] == 0.0,
          "%r %r" % (b0["overturn_half"], b0["overturn_draw0"]))
    sel = repA["selection"]
    check("A7 selection is P2 (mean tie 6.0, p95 6.0 < 8.4)",
          sel["verdict"] == "CALIBRATED SETTING"
          and sel["setting"] == "P2"
          and abs(sel["wall_s"]["mean"] - 6.0) < 1e-9
          and abs(sel["wall_s"]["p95"] - 6.0) < 1e-9,
          json.dumps(sel))

    # ---------------- Scenario B
    statesB = [("t1", "g1", 1), ("t2", "g1", 2), ("t3", "g2", 1),
               ("t4", "g2", 2), ("t5", "g3", 1)]
    settingsB = [T("X", 8000, 180, 62, -1), T("Y", 8000, 180, 62, -1)]
    worldsB, wallsB = {}, {}
    for st in settingsB:
        for s, _, _ in statesB:
            worldsB[(st["name"], s)] = dict(full)
    for i, w in enumerate([4000, 4000, 4000, 4000, 24000]):
        wallsB[("X", statesB[i][0])] = w
    for i, w in enumerate([3000, 3000, 3000, 8000, 23000]):
        wallsB[("Y", statesB[i][0])] = w
    dB = os.path.join(tmp, "scB")
    panelB, setB = scenario(dB, statesB, settingsB, worldsB, wallsB)
    pB, repB = run_analyzer(dB, panelB, setB, "B")
    check("B analyzer exit 0", pB.returncode == 0, pB.stderr[-200:])
    xw, yw = (repB["settings"]["X"]["wall_s"],
              repB["settings"]["Y"]["wall_s"])
    check("B1 X/Y tie on mean (8.0) and p95 (20.0)",
          abs(xw["mean"] - 8.0) < 1e-9 and abs(yw["mean"] - 8.0) < 1e-9
          and abs(xw["p95"] - 20.0) < 1e-9
          and abs(yw["p95"] - 20.0) < 1e-9,
          "%r %r" % (xw, yw))
    check("B2 selection is Y (max 23 < 24)",
          repB["selection"]["setting"] == "Y"
          and abs(xw["max"] - 24.0) < 1e-9
          and abs(yw["max"] - 23.0) < 1e-9,
          json.dumps(repB["selection"]))

    # ---------------- Scenario C
    statesC = [("u1", "g1", 1), ("u2", "g1", 2)]
    settingsC = [T("Z", 4000, 180, 62, -1)]
    worldsC = {("Z", "u1"): {0: [1.0] * 10 + [("err", "abort")] * 15,
                             1: FULL1},
               ("Z", "u2"): dict(full)}
    wallsC = {("Z", "u1"): 5000, ("Z", "u2"): 5000}
    dC = os.path.join(tmp, "scC")
    panelC, setC = scenario(dC, statesC, settingsC, worldsC, wallsC)
    pC, repC = run_analyzer(dC, panelC, setC, "C")
    check("C analyzer exit 0", pC.returncode == 0, pC.stderr[-200:])
    z = repC["settings"]["Z"]
    check("C0 Z per-state == 0.5, candidate-level == 0.75",
          abs(z["completion"] - 0.5) < 1e-12
          and abs(z["candidate_completion"] - 0.75) < 1e-12,
          "%r %r" % (z["completion"], z["candidate_completion"]))
    check("C1 verdict NO CALIBRATED SETTING",
          repC["selection"]["verdict"] == "NO CALIBRATED SETTING"
          and repC["selection"]["setting"] is None,
          json.dumps(repC["selection"]))
    dCb = os.path.join(tmp, "scCbad")
    shutil.copytree(dC, dCb)
    rows = [json.loads(l) for l in
            open(os.path.join(dCb, "evals_Z.jsonl"))]
    rows[0]["setting"]["hooks"] = 9999
    write_jsonl(os.path.join(dCb, "evals_Z.jsonl"), rows)
    pCb, _ = run_analyzer(dCb, panelC, setC, "Cb")
    check("C2 corrupted tuple aborts (exit 2)",
          pCb.returncode == 2 and "ABORT" in pCb.stdout,
          "rc=%d out=%s" % (pCb.returncode, pCb.stdout.strip()[:120]))

    # ---------------- Scenario D (review sec.1: the
    # candidate-level rate clears the bar, the per-state
    # rate does not -> must NOT qualify)
    statesD = [("v%d" % i, "g%d" % (1 + i % 5), 1 + i % 2)
               for i in range(1, 21)]
    settingsD = [T("SBAD", 8000, 180, 62, -1),
                 T("SGOOD", 16000, 360, 62, -1)]
    broken = [1.0] * 10 + [("err", "abort")] * 15
    worldsD, wallsD = {}, {}
    for st in settingsD:
        for s, _, _ in statesD:
            worldsD[(st["name"], s)] = dict(full)
            wallsD[(st["name"], s)] = (5000 if st["name"] == "SBAD"
                                       else 9000)
    for s in ("v1", "v2"):
        worldsD[("SBAD", s)] = {0: FULL0, 1: broken}
    worldsD[("SGOOD", "v1")] = {0: FULL0, 1: broken}
    dD = os.path.join(tmp, "scD")
    panelD, setD = scenario(dD, statesD, settingsD, worldsD, wallsD)
    pD, repD = run_analyzer(dD, panelD, setD, "D")
    check("D analyzer exit 0", pD.returncode == 0, pD.stderr[-200:])
    sb, sg = repD["settings"]["SBAD"], repD["settings"]["SGOOD"]
    check("D1 SBAD candidate-level == 0.95 (clears the bar "
          "as a diagnostic)",
          abs(sb["candidate_completion"] - 0.95) < 1e-12,
          str(sb["candidate_completion"]))
    check("D2 SBAD per-state == 0.90 and does NOT qualify",
          abs(sb["completion"] - 0.90) < 1e-12
          and sb["qualifies"] is False,
          "%r %r" % (sb["completion"], sb["qualifies"]))
    check("D3 SGOOD per-state == 0.95 and qualifies",
          abs(sg["completion"] - 0.95) < 1e-12
          and sg["qualifies"] is True,
          "%r %r" % (sg["completion"], sg["qualifies"]))
    check("D4 selection is SGOOD, not the cheaper SBAD",
          repD["selection"]["setting"] == "SGOOD",
          json.dumps(repD["selection"]))

    # ---------------- Scenario E (review sec.2: B0
    # qualifies and is cheapest -> selection must skip it)
    statesE = [("w1", "g1", 1), ("w2", "g1", 2), ("w3", "g2", 1)]
    settingsE = [T("B0", 4000, 180, 0, 0), T("H1", 4000, 180, 62, -1)]
    worldsE, wallsE = {}, {}
    for st in settingsE:
        for s, _, _ in statesE:
            worldsE[(st["name"], s)] = dict(full)
            wallsE[(st["name"], s)] = (1000 if st["name"] == "B0"
                                       else 9000)
    dE = os.path.join(tmp, "scE")
    panelE, setE = scenario(dE, statesE, settingsE, worldsE, wallsE)
    pE, repE = run_analyzer(dE, panelE, setE, "E")
    check("E analyzer exit 0", pE.returncode == 0, pE.stderr[-200:])
    eb = repE["settings"]["B0"]
    check("E1 B0 is the control and meets the metric "
          "(per-state 1.0, qualifies True)",
          eb["role"] == "control"
          and abs(eb["completion"] - 1.0) < 1e-12
          and eb["qualifies"] is True,
          "%r %r %r" % (eb["role"], eb["completion"],
                        eb["qualifies"]))
    check("E2 selection skips B0 (cheapest) and picks H1",
          repE["selection"]["setting"] == "H1",
          json.dumps(repE["selection"]))

    shutil.rmtree(tmp, ignore_errors=True)
    print("FX-STAGE1-ANALYZE: %s"
          % ("ALL PASS" if not FAILS else "FAILURES: %s" % FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
