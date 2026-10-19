#!/usr/bin/env python3
"""Round-3 pairing (Claude R6): for each seed, map gamename -> trace
file per arm from the driver rows, run the classifier on the arm
pairs, and emit one table with outcome fields (R3) beside verdicts.

Usage: r3_pair.py <arm>=<rows.jsonl>,<logdir> [<arm>=...]
Example: r3_pair.py raw=/tmp/r3_raw_s1.jsonl,/tmp/r3_raw_s1_log \
                    ghost=/tmp/r3_ghost_s1.jsonl,/tmp/r3_ghost_s1_log
Pairs are formed against the FIRST arm listed.

Rerun additions (Claude R12/R13): each seed's verdict is gated by
seat_ok (both rows' server-reported seat equals the arm seat and
zero seat_mismatch_errors - the launch's seat-2 void is this check
failing) and by assert_ok (both arms' manifests carry assert_ok
true - the launch's capture void is this check failing). Precedence:
INVALID_ASSERT > INVALID_SEAT > INVALID_MODE > classifier verdict.

Standing control: r3_pair.py --raw-control <rowsA.jsonl> <rowsB.jsonl>
compares two raw arms run at different seats; they must differ on
at least one seed (identical raw arms at different seats is the
signature of a seat-blind server). Prints the differing-seed count
and RAW-CONTROL PASS/FAIL.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(HERE, "classify_divergence.py")
PAIRS_FIELDS = ("winner", "turns", "decisions", "p1life", "p2life",
                "gamestate_norm_sha")
MODE_PREFIX = {"raw": "policy: server", "teacher": "policy: search",
               "ghost": "policy: search", "shadow": "policy: search",
               "capture": "policy: search"}


def mode_ok(arm_name, row):
    """R11: the misbuild class we've hit twice, checked per seed -
    each arm's own mode line must match its arm, and no connect
    failures are tolerable."""
    want = MODE_PREFIX.get(arm_name)
    ml = row.get("mode_line") or ""
    return (want is not None and ml.startswith(want)
            and row.get("connect_failed", 0) == 0)


def seat_ok(row):
    """R12: the server that actually served this game must report
    the seat the arm was run at, and the game must contain zero
    seat-mismatch rejections. Rows from pre-R12 runs (no fields)
    fail: their server's seat is unverifiable."""
    return (row.get("server_seat") is not None
            and row.get("server_seat") == row.get("seat")
            and row.get("seat_mismatch_errors", 1) == 0)


def load_manifest(rows_path):
    mp = rows_path + ".manifest.json"
    if not os.path.exists(mp):
        return None
    try:
        return json.load(open(mp))
    except Exception:
        return None


def load_arm(spec):
    name, rest = spec.split("=", 1)
    rows_path, logdir = rest.split(",", 1)
    games = {}
    for ln in open(rows_path):
        r = json.loads(ln)
        if r.get("gamename"):
            games[r["seed"]] = r
    return name, games, logdir, load_manifest(rows_path)


def raw_control(path_a, path_b):
    def load(p):
        g = {}
        for ln in open(p):
            r = json.loads(ln)
            g[r["seed"]] = r
        return g
    a, b = load(path_a), load(path_b)
    fields = PAIRS_FIELDS + ("gamelog_sha",)
    diff = [s for s in sorted(a)
            if s in b and any(a[s].get(k) != b[s].get(k) for k in fields)]
    print(f"raw-control: {len(diff)}/{len(a)} seeds differ "
          f"(fields: {', '.join(fields)})")
    print("differing seeds:", diff)
    print("RAW-CONTROL:",
          "PASS" if diff else "FAIL - raw arms at different seats "
          "produced identical games (seat-blind server)")


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--raw-control":
        raw_control(sys.argv[2], sys.argv[3])
        return
    arms = [load_arm(s) for s in sys.argv[1:]]
    base_name, base_games, base_log, base_manifest = arms[0]
    print("| seed | pair | verdict | within-row hits | seq | outcome "
          "equal | modes ok | seat ok | assert ok |")
    print("|---|---|---|---|---|---|---|---|---|")
    for seed in sorted(base_games):
        brow = base_games[seed]
        btrace = os.path.join(base_log, "trace",
                              "trace_%s.jsonl" % brow["gamename"])
        for name, games, logdir, manifest in arms[1:]:
            orow = games.get(seed)
            if orow is None:
                print(f"| {seed} | {base_name} vs {name} | MISSING_GAME "
                      f"| - | - | - | - | - | - |")
                continue
            otrace = os.path.join(logdir, "trace",
                                  "trace_%s.jsonl" % orow["gamename"])
            out = subprocess.run([sys.executable, CLASSIFIER,
                                  btrace, otrace],
                                 capture_output=True, text=True)
            v = json.loads(out.stdout.strip())
            eq = all(brow.get(k) == orow.get(k) for k in PAIRS_FIELDS)
            mok = mode_ok(base_name, brow) and mode_ok(name, orow)
            sok = seat_ok(brow) and seat_ok(orow)
            aok = bool(base_manifest and base_manifest.get("assert_ok")
                       and manifest and manifest.get("assert_ok"))
            if not aok:
                verdict = "INVALID_ASSERT"
            elif not sok:
                verdict = "INVALID_SEAT"
            elif not mok:
                verdict = "INVALID_MODE"
            else:
                verdict = v["class"]
            print(f"| {seed} | {base_name} vs {name} | {verdict} "
                  f"| {len(v.get('within_row_hits', []))} "
                  f"| {v.get('first_diff_seq')} | {eq} | {mok} | {sok} "
                  f"| {aok} |")


if __name__ == "__main__":
    main()
