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
    ap.add_argument("--arm", required=True, choices=["raw", "teacher", "ghost"])
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
    env["KEEP_GAME"] = "1"  # play_game skips its end-of-game cleanup:
    # the game dir (with the full gamelog) survives for cross-arm
    # action-sequence comparison.
    if a.arm in ("teacher", "ghost"):
        env["TEACHER_MODE"] = "1"
    if a.arm == "ghost":
        env["TEACHER_GHOST"] = "1"
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
        if a.arm in ("teacher", "ghost"):
            # ONLY the teacher arms engage the search root. The raw
            # arm is the plain policy bridge (net argmax) - passing
            # --policy-search there would run the ISMCTS root, a
            # different player (caught 2026-10-18 via its stat log).
            cmd.append("--policy-search")
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
        result = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('{"winner"'):
                try:
                    result = json.loads(line)
                except Exception:
                    pass
        row = {"seed": seed, "arm": a.arm, "seat": a.seat,
               "connect_failed": cf, "secs": round(time.time() - t0, 1)}
        if cf > 0:
            row["invalid"] = "connect_failed"
        if result is None:
            row["invalid"] = row.get("invalid", "no_result")
        else:
            row.update({k: result.get(k) for k in
                        ("winner", "draw", "capped", "cap_reason",
                         "turns", "gamename", "firstPlayer", "stuck")})
            gdir = os.path.join(a.tree, "vendor", "talishar", "Games",
                                str(result.get("gamename", "")))
            glog = os.path.join(gdir, "gamelog.txt")
            if os.path.exists(glog):
                data = open(glog, "rb").read()
                row["gamelog_sha"] = hashlib.sha256(data).hexdigest()[:16]
                row["gamelog_bytes"] = len(data)
            else:
                row["gamelog_sha"] = None
        fout.write(json.dumps(row) + "\n")
        fout.flush()
        print("seed %d %s winner=%s cf=%d %.0fs" % (
            seed, a.arm, row.get("winner"), cf, row["secs"]), flush=True)
    fout.close()
    print("PAIRED-DRIVER-DONE arm=%s" % a.arm)

if __name__ == "__main__":
    main()
