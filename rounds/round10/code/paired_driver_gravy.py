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

Round-3 rerun additions (Claude R12/R13/R16):
  - Before an arm, the driver pings the server ({"type":"ping"}) and
    records its self-reported learner_seat + model on EVERY row and
    in the manifest. Per game it counts SEAT_MISMATCH lines in the
    game output; any mismatch marks the row invalid and its outcome
    fields are NOT recorded (a mis-seated game is not a measurement).
  - On timeout, the Games/ dir is diffed against its pre-game
    listing and cleanup_cache.php runs DeleteCache for each new
    game id, so a killed child does not leak SHMOP segments.
Gate additions (Claude G8/G9):
  - If env TCG_CLEAN_CHILDREN=1, after each COMPLETED teacher-family
    game the Games/ dir is diffed against its pre-game listing and
    cleanup_cache.php runs DeleteCache for each new CHILD game id
    (the finished game's own id is excluded - its segment is the
    known +1/game KEEP_GAME leak, reported via ipcs per chunk).
    The row records children_found / children_cleaned. (The timeout
    path already cleaned all new ids; this is the always-on version
    for the teacher path's rollout children.)
  - If env GATE_GAME_IDS_FILE is set, every game id the driver sees
    (completed games, seat-mismatch rows, timeout children) is
    appended to that file - the gate fleet's registry source (G9).

  - The arm manifest carries per-arm stat/trace ASSERTIONS
    (assert_ok): raw must have zero stat rows and zero teacher
    trace rows; ghost's rollout rows must all carry ghost=1 with
    pick == prior_pick and every teacher trace row must be rule
    ghost_prior; capture's snapshotted rows must carry capture=1,
    pick == prior_pick and no rollout fields, with no rollouts
    anywhere in the arm; shadow's teacher trace rows must all be
    rule shadow_bridge with zero shadow_fallback_decide; and for
    ghost and capture, every teacher trace row's played pick must
    equal the PRE-state priors' argmax (the prior pick). The stat
    side is what convicts the launch's capture misbuild; the trace
    rule label alone cannot (the trace patch labels a correct
    capture row "teacher" too - the label names the Decide path).

Usage:
  paired_driver.py --tree /tmp/gatetree --sock /tmp/gate_c0.sock \
    --seat 1 --arm teacher --seeds 1-50 --out /tmp/gate_t_c0.jsonl \
    --logdir /tmp/gate_t_c0_log [--ghost] [--timeout 1200]
"""
import argparse, hashlib, json, os, subprocess, sys, time

def ping_server(sock_path, timeout=10):
    """R12: ask the server who it is ({"type":"ping"} -> learner_seat
    + model). Returns a dict, or None when unreachable / not a
    patched server (a rerun arm against an unpatched server records
    server_seat=None and fails seat_ok in r3_pair)."""
    import socket as _s, struct as _st
    try:
        c = _s.socket(_s.AF_UNIX, _s.SOCK_STREAM)
        c.settimeout(timeout)
        c.connect(sock_path)
        payload = json.dumps({"type": "ping"}).encode()
        c.sendall(_st.pack(">I", len(payload)) + payload)
        hdr = b""
        while len(hdr) < 4:
            chunk = c.recv(4 - len(hdr))
            if not chunk:
                return None
            hdr += chunk
        (n,) = _st.unpack(">I", hdr)
        buf = b""
        while len(buf) < n:
            chunk = c.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        c.close()
        r = json.loads(buf.decode())
        return {"learner_seat": r.get("learner_seat"),
                "model": r.get("model")}
    except Exception:
        return None

def arm_assertions(arm, logdir):
    """R13: per-arm truth checks computed from the arm's OWN stat
    rows and trace rows after the arm finishes. Returns (details,
    checks, assert_ok). See the module docstring for the rules."""
    stats_path = os.path.join(logdir, "search_stats.jsonl")
    rows = []
    if os.path.exists(stats_path):
        for l in open(stats_path):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    teacher_rows = [r for r in rows if r.get("teacher") == 1]
    contested = [r for r in teacher_rows if r.get("contested") == 1]
    rollout_rows = [r for r in teacher_rows
                    if "means" in r or "n_worlds" in r]
    rules = {}
    teacher_trace_rows = 0
    trace_priors_rows = 0
    trace_argmax_agree = 0
    tdir = os.path.join(logdir, "trace")
    if os.path.isdir(tdir):
        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith(".jsonl"):
                continue
            for l in open(os.path.join(tdir, fn)):
                try:
                    tr = json.loads(l)
                except Exception:
                    continue
                rules[tr.get("rule")] = rules.get(tr.get("rule"), 0) + 1
                if "decide_pick" in tr:
                    teacher_trace_rows += 1
                    pr = tr.get("priors_pre")
                    if pr:
                        trace_priors_rows += 1
                        am = max(range(len(pr)), key=lambda i: pr[i])
                        if am == tr["decide_pick"]:
                            trace_argmax_agree += 1
    details = {"stat_rows": len(rows), "teacher_rows": len(teacher_rows),
               "contested_rows": len(contested),
               "rollout_rows": len(rollout_rows),
               "trace_rules": rules,
               "teacher_trace_rows": teacher_trace_rows,
               "teacher_trace_rows_with_priors": trace_priors_rows,
               "teacher_trace_pick_argmax_agree": trace_argmax_agree}
    checks = {}
    if arm == "raw":
        checks["stat_rows_zero"] = len(rows) == 0
        checks["teacher_trace_rows_zero"] = teacher_trace_rows == 0
    if arm == "ghost":
        checks["pick_eq_prior_all_teacher"] = all(
            r.get("pick") == r.get("prior_pick") for r in teacher_rows)
        checks["ghost_flag_on_all_rollouts"] = all(
            r.get("ghost") == 1 for r in rollout_rows)
        checks["rollouts_present"] = len(rollout_rows) > 0
        checks["trace_rules_all_ghost_prior"] = (
            rules.get("ghost_prior", 0) == teacher_trace_rows)
    if arm == "capture":
        cap = [r for r in teacher_rows if r.get("capture") == 1]
        details["capture_rows"] = len(cap)
        checks["capture_rows_present"] = len(cap) > 0
        checks["capture_pick_eq_prior"] = all(
            r.get("pick") == r.get("prior_pick") for r in cap)
        checks["capture_no_rollout_fields"] = all(
            "means" not in r and "n_worlds" not in r for r in cap)
        checks["no_rollouts_anywhere"] = len(rollout_rows) == 0
        checks["pick_eq_prior_all_teacher"] = all(
            r.get("pick") == r.get("prior_pick") for r in teacher_rows)
    if arm == "teacher":
        # Gate arm (G7): the plain teacher may overturn, so there is
        # no pick==prior constraint; the machinery checks are that
        # the arm produced teacher rows at all, that every contested
        # row carries the determinization-persistence proof (G7:
        # det_persisted on every row), and that teacher trace rows
        # were written (G3 needs them).
        checks["stat_teacher_rows_present"] = len(teacher_rows) > 0
        checks["det_persisted_all_contested"] = all(
            r.get("det_persisted") == 1 for r in contested)
        checks["trace_teacher_rows_present"] = teacher_trace_rows > 0
    if arm == "shadow":
        checks["shadow_teacher_rows_present"] = teacher_trace_rows > 0
        checks["shadow_rules_all_shadow_bridge"] = (
            rules.get("shadow_bridge", 0) == teacher_trace_rows)
        checks["shadow_fallback_decide_zero"] = (
            rules.get("shadow_fallback_decide", 0) == 0)
    if arm in ("ghost", "capture"):
        # The played pick (decide_pick on the trace row) must be the
        # PRE-state priors' argmax - the prior pick - on every
        # teacher row. (The launch's capture misbuild fails this on
        # every overturned decision, and its stat side fails the
        # rollout-field checks above.) The trace rule label is NOT
        # used: the trace patch labels capture rows "teacher" too,
        # because the label names the Decide path, not the arm.
        checks["trace_teacher_pick_is_prior_argmax"] = (
            teacher_trace_rows > 0
            and trace_priors_rows == teacher_trace_rows
            and trace_argmax_agree == teacher_trace_rows)
    return details, checks, all(checks.values()) if checks else False

def note_game_id(path, gid):
    """G9: append a game id to the fleet's registry-source file."""
    if path and gid is not None:
        try:
            with open(path, "a") as gf:
                gf.write(str(gid) + "\n")
        except Exception:
            pass

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
    ap.add_argument("--deck", default="/home/joe/tcg/tcg-sim/decks/nats2026_eriksen_gravy_60.txt")
    ap.add_argument("--timeout", type=int, default=1200)
    a = ap.parse_args()
    # This copy of the driver is the round-9 GRAVY driver's: its
    # only registered use is the Gravy mirror. A non-Gravy deck
    # here is always a mistake (the file's original default was
    # the ASHLYN FAI deck, inherited from the gate driver it was
    # copied from - a silent wrong-population capture if run
    # without --deck). Fail loud at the boundary instead.
    if "gravy" not in os.path.basename(a.deck).lower():
        print("ABORT: paired_driver_gravy.py requires the Gravy "
              "mirror deck, got %s" % a.deck, file=sys.stderr)
        sys.exit(2)
    os.makedirs(a.logdir, exist_ok=True)
    env = dict(os.environ)
    env["TCG_POLICY_SOCK"] = a.sock
    env["TCG_LEARNER_SEAT"] = str(a.seat)
    env["TCG_MAX_TURNS"] = "87"
    env["TCG_MAX_DECISIONS"] = "3000"
    env["TCG_STUCK_LIMIT"] = "200"
    env["TCG_SEARCH_LOG"] = a.logdir
    env["TCG_TRACE_LOG"] = os.path.join(a.logdir, "trace")
    env["KEEP_GAME"] = "1"  # play_game skips its end-of-game cleanup:
    # the game dir (with the full gamelog) survives for cross-arm
    # action-sequence comparison.
    clean_children = os.environ.get("TCG_CLEAN_CHILDREN") == "1"
    game_ids_file = os.environ.get("GATE_GAME_IDS_FILE") or None
    if a.arm in ("teacher", "ghost", "shadow", "capture"):
        env["TEACHER_MODE"] = "1"
    if a.arm == "ghost":
        env["TEACHER_GHOST"] = "1"
    if a.arm == "shadow":
        env["TEACHER_SHADOW"] = "1"
    if a.arm == "capture":
        env["TEACHER_CAPTURE"] = "1"
        env["TEACHER_SNAP_DIR"] = os.path.join(a.logdir, "snaps")
    server_info = ping_server(a.sock)
    server_seat = server_info.get("learner_seat") if server_info else None
    print("server identity: %s (arm seat %d)" % (server_info, a.seat),
          flush=True)
    games_dir = os.path.join(a.tree, "vendor", "talishar", "Games")
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
        before_games = (set(os.listdir(games_dir))
                        if os.path.isdir(games_dir) else set())
        try:
            p = subprocess.run(cmd, cwd=a.tree, env=env,
                               capture_output=True, text=True,
                               timeout=a.timeout)
            out, err = p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            # R16: the kill leaves the child's SHMOP segments behind.
            # Diff the Games/ dir and DeleteCache each new game id.
            after_games = (set(os.listdir(games_dir))
                           if os.path.isdir(games_dir) else set())
            new_ids = sorted(after_games - before_games)
            cleaned = []
            if new_ids:
                try:
                    cp = subprocess.run(
                        ["php", "cleanup_cache.php"] + new_ids,
                        cwd=a.tree, capture_output=True, text=True,
                        timeout=120)
                    if cp.returncode == 0:
                        cleaned = new_ids
                except Exception:
                    pass
            for gid in new_ids:
                note_game_id(game_ids_file, gid)
            fout.write(json.dumps(
                {"seed": seed, "arm": a.arm, "seat": a.seat,
                 "server_seat": server_seat, "seat_mismatch_errors": 0,
                 "invalid": "timeout", "timeout_new_games": new_ids,
                 "timeout_cache_cleaned": cleaned}) + "\n")
            fout.flush()
            print("seed %d %s TIMEOUT new_games=%s cleaned=%s" % (
                seed, a.arm, new_ids, cleaned), flush=True)
            continue
        cf = out.count("connect failed") + err.count("connect failed")
        mm = out.count("SEAT_MISMATCH") + err.count("SEAT_MISMATCH")
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
               "server_seat": server_seat, "seat_mismatch_errors": mm,
               "mode_line": mode_line,
               "connect_failed": cf, "secs": round(time.time() - t0, 1)}
        if mm > 0:
            # R12: a mis-seated game is not a measurement - record
            # the failure and the game id, never its outcome.
            row["invalid"] = "seat_mismatch"
            if result is not None:
                row["gamename"] = result.get("gamename")
                note_game_id(game_ids_file, result.get("gamename"))
            fout.write(json.dumps(row) + "\n")
            fout.flush()
            print("seed %d %s SEAT_MISMATCH errors=%d" % (
                seed, a.arm, mm), flush=True)
            continue
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
            note_game_id(game_ids_file, result.get("gamename"))
            if clean_children and a.arm in ("teacher", "ghost",
                                            "shadow", "capture"):
                # G8: the teacher path's rollout children leave SHMOP
                # segments behind (their game dirs appear in Games/
                # during the game and the children never run the
                # engine's end-of-game DeleteCache). Diff and clean
                # them now, per game, so a 400-teacher-game fleet
                # does not accumulate ~5 segments per game. The
                # finished game's OWN id is excluded: its segment is
                # the known +1/game KEEP_GAME leak, reported per
                # chunk via ipcs and cleaned post-run.
                after_games = (set(os.listdir(games_dir))
                               if os.path.isdir(games_dir) else set())
                children = sorted(after_games - before_games
                                  - {str(result.get("gamename", ""))})
                cleaned_children = []
                if children:
                    try:
                        cp = subprocess.run(
                            ["php", "cleanup_cache.php"] + children,
                            cwd=a.tree, capture_output=True, text=True,
                            timeout=120)
                        if cp.returncode == 0:
                            cleaned_children = children
                    except Exception:
                        pass
                row["children_found"] = len(children)
                row["children_cleaned"] = len(cleaned_children)
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
    details, checks, assert_ok = arm_assertions(a.arm, a.logdir)
    manifest = {"arm": a.arm, "tree": a.tree, "seat": a.seat,
                "seeds": a.seeds, "search_stats_rows": stats_rows,
                "trace_files": trace_files,
                "server": server_info,
                "assertions": details, "checks": checks,
                "assert_ok": assert_ok,
                "assert_no_search_rows": (stats_rows == 0) if a.arm == "raw" else None}
    with open(a.out + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print("PAIRED-DRIVER-DONE arm=%s" % a.arm)

if __name__ == "__main__":
    main()
