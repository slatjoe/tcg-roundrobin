#!/usr/bin/env python3
"""Paired-seed game driver (Claude round-2 gate registration).

One play_game.php invocation per (seed, arm) with --games 1 --seed S -
the only mode in which the engine honors a fixed seed, so the same
seed deals the same game to every arm until play diverges.

Arms:
  raw     - plain v15 via the policy bridge (no search)
  teacher - TEACHER_MODE=1 (the deployed teacher, pair va, k=25)
  ghost   - TEACHER_MODE=1 + TEACHER_GHOST=1 (full machinery, pick
            forced to the prior's; must be action-identical to raw)

Per game the driver records: winner/draw/capped/turns from the
engine's own result JSON on stdout, the count of policy-server
"connect failed" lines (any occurrence INVALIDATES the game - a
silent heuristic fallback must never be counted), and a sha256 of
the game's gamelog (the ground-truth applied-action sequence) for
cross-arm equality checks.

Usage:
  paired_driver.py --tree /tmp/gatetree --sock /tmp/gate_c0.sock \
    --seat 1 --arm teacher --seeds 1-50 --out /tmp/gate_t_c0.jsonl \
    --logdir /tmp/gate_t_c0_log [--ghost] [--timeout 1200]
"""
import argparse, hashlib, json, os, subprocess, sys, time

def parse_seeds(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--sock", required=True)
    ap.add_argument("--seat", type=int, required=True)
    ap.add_argument("--arm", required=True,
                    choices=["raw", "teacher", "ghost", "shadow", "capture"])
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--logdir", required=True)
    ap.add_argument("--deck", default="/home/joe/tcg/tcg-sim/decks/nats2026_ashlyn_fai_60.txt")
    ap.add_argument("--timeout", type=int, default=1200)
    a = ap.parse_args()
    os.makedirs(a.logdir, exist_ok=True)
    env = dict(os.environ)
    env["TCG_POLICY_SOCK"] = a.sock
    env["TCG_LEARNER_SEAT"] = str(a.seat)
    env["TCG_MAX_TURNS"] = "60"
    env["TCG_MAX_DECISIONS"] = "3000"
    env["TCG_STUCK_LIMIT"] = "200"
    env["TCG_SEARCH_LOG"] = a.logdir
    env["TCG_TRACE_LOG"] = os.path.join(a.logdir, "trace")
    env["KEEP_GAME"] = "1"  # play_game skips its end-of-game cleanup:
    # the game dir (with the full gamelog) survives for cross-arm
    # action-sequence comparison.
    if a.arm in ("teacher", "ghost", "shadow", "capture"):
        env["TEACHER_MODE"] = "1"
    if a.arm == "ghost":
        env["TEACHER_GHOST"] = "1"
    if a.arm == "shadow":
        env["TEACHER_SHADOW"] = "1"
    if a.arm == "capture":
        env["TEACHER_CAPTURE"] = "1"
        env["TEACHER_SNAP_DIR"] = os.path.join(a.logdir, "snaps")
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            try:
                done.add(int(json.loads(l)["seed"]))
            except Exception:
                pass
    fout = open(a.out, "a")
    for seed in parse_seeds(a.seeds):
        if seed in done:
            continue
        cmd = ["php", "play_game.php", a.deck, a.deck,
               "--games", "1", "--seed", str(seed)]
        if a.arm in ("teacher", "ghost", "shadow", "capture"):
            # ONLY the teacher-family arms engage the search root.
            cmd.append("--policy-search")
        else:
            # The raw arm is the plain policy bridge (net argmax via
            # the server). It needs --policy-server: with NO policy
            # flag play_game falls back to the in-process v1
            # HEURISTIC for both seats (play_game.php: "policy: v1
            # (deck-aware)"). The first version of this driver ran
            # the raw arm flagless and its 'bridge' games were
            # heuristic mirror games - the ghost test's 0/19 was
            # net-vs-heuristic divergence, not a machinery effect
            # (caught 2026-10-18 while building the round-3 trace,
            # from play_game.php's own mode lines).
            cmd.append("--policy-server")
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=a.tree, env=env,
                               capture_output=True, text=True,
                               timeout=a.timeout)
            out, err = p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            fout.write(json.dumps({"seed": seed, "arm": a.arm,
                                   "seat": a.seat, "invalid": "timeout"}) + "\n")
            fout.flush()
            continue
        cf = out.count("connect failed") + err.count("connect failed")
        # play_game prints one mode line per include block: a search
        # game prints "policy: v1 (deck-aware)" for the base block AND
        # "policy: search (...)" for the search block. The search line
        # is the arm's defining mode; take it when present.
        mode_line = None
        for line in err.splitlines():
            if line.startswith("policy:"):
                if line.startswith("policy: search"):
                    mode_line = line.strip()
                    break
                if mode_line is None:
                    mode_line = line.strip()
        result = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('{"winner"'):
                try:
                    result = json.loads(line)
                except Exception:
                    pass
        row = {"seed": seed, "arm": a.arm, "seat": a.seat,
               "mode_line": mode_line,
               "connect_failed": cf, "secs": round(time.time() - t0, 1)}
        if cf > 0:
            row["invalid"] = "connect_failed"
        if result is None:
            row["invalid"] = row.get("invalid", "no_result")
        else:
            # R9: the result JSON's "steps" reads 1 for a full game -
            # it is not an engine step counter, so it is NOT recorded.
            # "decisions" (below) is the honest count: trace rows,
            # one per policy decision (the simPolicyDecision counter).
            row.update({k: result.get(k) for k in
                        ("winner", "draw", "capped", "cap_reason",
                         "turns", "gamename", "firstPlayer", "stuck",
                         "p1life", "p2life")})
            tpath = os.path.join(a.logdir, "trace",
                                 "trace_%s.jsonl" % result.get("gamename"))
            row["decisions"] = (sum(1 for _ in open(tpath))
                                if os.path.exists(tpath) else None)
            gdir = os.path.join(a.tree, "vendor", "talishar", "Games",
                                str(result.get("gamename", "")))
            glog = os.path.join(gdir, "gamelog.txt")
            if os.path.exists(glog):
                data = open(glog, "rb").read()
                row["gamelog_sha"] = hashlib.sha256(data).hexdigest()[:16]
                row["gamelog_bytes"] = len(data)
            else:
                row["gamelog_sha"] = None
            gs = os.path.join(gdir, "gamestate.txt")
            row["gamestate_sha"] = (
                hashlib.sha256(open(gs, "rb").read()).hexdigest()[:16]
                if os.path.exists(gs) else None)
            # R10: normalized final-state hash. On the seed-3 pair the
            # raw files differed ONLY in two per-game hex-id lines and
            # one epoch line; masking those classes makes the hash an
            # equality field for the PASS reads.
            if os.path.exists(gs):
                import re as _re
                norm = []
                for ln in open(gs, errors="replace").read().splitlines():
                    if _re.fullmatch(r"[0-9a-f]{16}", ln.strip()):
                        ln = "HEXID"
                    elif _re.fullmatch(r"\d{10}", ln.strip()):
                        ln = "EPOCH"
                    norm.append(ln)
                row["gamestate_norm_sha"] = hashlib.sha256(
                    "\n".join(norm).encode()).hexdigest()[:16]
            else:
                row["gamestate_norm_sha"] = None
        fout.write(json.dumps(row) + "\n")
        fout.flush()
        print("seed %d %s winner=%s cf=%d %.0fs" % (
            seed, a.arm, row.get("winner"), cf, row["secs"]), flush=True)
    fout.close()
    # Arm manifest (Claude round-2 hygiene): what the arm actually ran,
    # read from the child processes' own records - per-game mode lines
    # in the rows above, plus the arm's search-stat volume. A raw arm
    # must have produced ZERO search rows.
    stats_path = os.path.join(a.logdir, "search_stats.jsonl")
    stats_rows = 0
    if os.path.exists(stats_path):
        with open(stats_path) as f:
            stats_rows = sum(1 for _ in f)
    trace_dir = os.path.join(a.logdir, "trace")
    trace_files = len(os.listdir(trace_dir)) if os.path.isdir(trace_dir) else 0
    manifest = {"arm": a.arm, "tree": a.tree, "seat": a.seat,
                "seeds": a.seeds, "search_stats_rows": stats_rows,
                "trace_files": trace_files,
                "assert_no_search_rows": (stats_rows == 0) if a.arm == "raw" else None}
    with open(a.out + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print("PAIRED-DRIVER-DONE arm=%s" % a.arm)

if __name__ == "__main__":
    main()
