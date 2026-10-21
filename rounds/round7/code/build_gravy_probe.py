#!/usr/bin/env python3
"""build_gravy_probe.py — round-7 follow-up K1: build the Gravy KL
probe set by applying the Fai probe's construction recipe, verbatim,
to the Gravy heuristic mirror corpus (stage-1 batch mirror_self).

THE FAI RECIPE, AS BUILT (evidence: probe/build.log +
probe_kl.py build, sim root):

  * tool: probe_kl.py `build` (sha256 0c251521523711e33f...), run
    from the sim root over the three BC2 corpora:
        bc2_train_data/mirror: kept 9000
        bc2_train_data/cross:  kept 9000
        bc2_train_data/dagger: kept 9000
        probe set: 27000 records -> probe/probe_v1.jsonl
    (probe_v1.jsonl sha256 974fef83498b0ac6f0ebe2e774e2b73968e5675
     ce4d6e1b45fe26e0bf9b071db; 27,000 records.)
  * selection (probe_kl.py:28-58): scan each corpus in os.walk
    order (file names sorted per directory), records in file
    order; keep a record iff it parses as JSON, its
    state.candidates has >= 2 entries, and
    md5(f"{game}:{decision}").digest()[0] % 7 == 0; stop at
    --per-corpus (default 9000) per corpus. Raw records are
    written verbatim (the set is featurization-agnostic).
  * consumption: rl/trainer_v4.py Gate loads the file and takes a
    FIXED subsample — np.random.RandomState(20261016).choice(
    27000, size=4096, replace=False), indices sorted (Gate
    defaults subset=4096, seed=20261016, trainer_v4.py:180-187);
    the anchor's log-probs on that batch are computed once and
    never moved. The probe's role is the KL divergence budget's
    fixed instrument; nothing else about it changes here.

K1 applies the recipe to the corpus Claude named — the Gravy
heuristic mirror corpus — at the same per-corpus cap:

    probe_kl.py build --corpora gravy_bc/data/mirror_self \
        --per-corpus 9000 --out probe/probe_gravy_v1.jsonl

This script is the registered builder. It does NOT re-implement
the selection for the build itself — it invokes the box's own
probe_kl.py, so "verbatim" is literal — and then verifies the
output with an independent re-scan (a second implementation of
the same filter, in this file) whose kept (game, decision)
sequence must match the produced file exactly.

Guards (any failure aborts, nothing is written past the failing
step's own output):
  * the output file must not already exist (a built probe is an
    artifact; it is never silently overwritten);
  * the corpus's games_w*.jsonl must total --expect-games games
    (the stage-1 completion check — game counts, never a DONE
    file) before anything is built;
  * probe_kl.py's own "kept" count must equal --per-corpus (a
    short yield is a stage-1 finding, not a probe to train
    against);
  * the independent re-scan must reproduce the file exactly.

Usage (registered invocation, on the box, after stage 1
completes mirror_self at 2,400 games):

  /home/joe/tcg/rl-env/bin/python code/build_gravy_probe.py \
      --sim-root /home/joe/tcg/tcg-sim

prints PROBE_FILE / PROBE_STATES / PROBE_SHA256 lines for the
stage-3 launch manifest.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys


def count_games(corpus):
    total = 0
    for n in sorted(os.listdir(corpus)):
        if n.startswith("games_w") and n.endswith(".jsonl"):
            with open(os.path.join(corpus, n)) as fh:
                total += sum(1 for _ in fh)
    return total


def expected_kept(corpus, per_corpus):
    """Independent re-implementation of probe_kl.py build's
    selection: same walk order (os.walk, names sorted per
    directory), same filter, same cap. Returns the (game,
    decision) sequence the build must produce."""
    files = []
    for root, _dirs, names in os.walk(corpus):
        for n in sorted(names):
            if n.endswith(".jsonl"):
                files.append(os.path.join(root, n))
    kept = []
    for f in files:
        if len(kept) >= per_corpus:
            break
        with open(f) as fh:
            for line in fh:
                if len(kept) >= per_corpus:
                    break
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                st = r.get("state", {})
                if len(st.get("candidates", [])) < 2:
                    continue
                h = hashlib.md5(
                    f"{r.get('game')}:{r.get('decision')}".encode()
                ).digest()
                if h[0] % 7 != 0:
                    continue
                kept.append((r.get("game"), r.get("decision")))
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-root", default="/home/joe/tcg/tcg-sim")
    ap.add_argument("--corpus", default=None,
                    help="default: <sim-root>/gravy_bc/data/mirror_self")
    ap.add_argument("--out", default=None,
                    help="default: <sim-root>/probe/probe_gravy_v1.jsonl")
    ap.add_argument("--expect-games", type=int, default=2400)
    ap.add_argument("--per-corpus", type=int, default=9000)
    args = ap.parse_args()

    sim = args.sim_root
    corpus = args.corpus or os.path.join(sim, "gravy_bc", "data",
                                         "mirror_self")
    out = args.out or os.path.join(sim, "probe", "probe_gravy_v1.jsonl")
    probe_kl = os.path.join(sim, "probe_kl.py")

    if os.path.exists(out):
        print(f"ABORT: {out} already exists; refusing to overwrite "
              f"a built probe artifact")
        return 1
    if not os.path.isdir(corpus):
        print(f"ABORT: corpus missing: {corpus}")
        return 1
    games = count_games(corpus)
    if games != args.expect_games:
        print(f"ABORT: corpus game count {games} != expected "
              f"{args.expect_games} (stage-1 completion check: "
              f"game counts from games_w*.jsonl, never a DONE file)")
        return 1

    cmd = [sys.executable, probe_kl, "build", "--corpora", corpus,
           "--per-corpus", str(args.per_corpus), "--out", out]
    print("running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(res.stdout)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
        print("ABORT: probe_kl.py build failed")
        return 1
    kept = None
    for line in res.stdout.splitlines():
        if ": kept " in line:
            kept = int(line.rsplit(" ", 1)[1])
    if kept != args.per_corpus:
        print(f"ABORT: probe_kl kept {kept} != per-corpus cap "
              f"{args.per_corpus} (short yield is a stage-1 "
              f"finding, not a probe to train against)")
        return 1

    recs = [json.loads(l) for l in open(out)]
    if len(recs) != kept:
        print(f"ABORT: probe file has {len(recs)} records, "
              f"build reported {kept}")
        return 1
    for r in recs:
        if len(r.get("state", {}).get("candidates", [])) < 2:
            print("ABORT: probe record with < 2 candidates")
            return 1
    want = expected_kept(corpus, args.per_corpus)
    got = [(r.get("game"), r.get("decision")) for r in recs]
    if got != want:
        print("ABORT: independent re-scan does not reproduce the "
              "probe file's kept sequence")
        return 1

    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print(f"PROBE_FILE {out}")
    print(f"PROBE_STATES {len(recs)}")
    print(f"PROBE_SHA256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
