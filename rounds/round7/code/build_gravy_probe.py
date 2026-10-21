#!/usr/bin/env python3
"""build_gravy_probe.py — round-7 K1 (as corrected by
claude-reply-a889f39 sec.1): build the Gravy KL probe set by
applying the Fai probe's construction recipe, verbatim, to ALL
THREE Gravy training corpora — mirror_self, cross_self and the
DAgger batch mirror_bc.

History: followup-k1-k5.md sec.K1 scoped the probe to the mirror
corpus alone, following Claude's original K1 wording (he named
one corpus before the recipe was recovered). Claude's reply to
that follow-up corrects it — his error, owned in the reply: with
the recipe in hand, "verbatim" means the same three-corpus
structure Fai's probe had. This builder is the corrected form;
the corpus directory names and game-count guards below were
verified against rounds/round7/code/gravy_corpus_driver.sh and
the box's gravy_bc/data/ (mirror_self / cross_self / mirror_bc —
the same names Claude's reply used).

THE FAI RECIPE, AS BUILT (evidence: probe/build.log +
probe_kl.py build, sim root):

  * tool: probe_kl.py `build` (sha256 0c251521523711e33f...), run
    ONCE from the sim root over the three BC2 corpora in one
    invocation:
        bc2_train_data/mirror: kept 9000
        bc2_train_data/cross:  kept 9000
        bc2_train_data/dagger: kept 9000
        probe set: 27000 records -> probe/probe_v1.jsonl
    (probe_v1.jsonl sha256 974fef83498b0ac6f0ebe2e774e2b73968e5675
     ce4d6e1b45fe26e0bf9b071db; 27,000 records.)
  * selection (probe_kl.py:28-58): for each corpus in argv
    order, scan in os.walk order (file names sorted per
    directory), records in file order; keep a record iff it
    parses as JSON, its state.candidates has >= 2 entries, and
    md5(f"{game}:{decision}").digest()[0] % 7 == 0; stop at
    --per-corpus (default 9000) per corpus. The output file is
    the concatenation, in corpus order, of the per-corpus kept
    sequences. Records are written as parsed JSON (the set is
    featurization-agnostic).
  * yield rule (the TOOL's semantics, not invented here): a
    corpus whose eligible records exhaust below the cap yields
    what it has — kept = min(cap, eligible) — and the tool
    prints the actual kept count per corpus. This builder's
    registered guard (below) then ABORTS on any short corpus:
    a short yield is a stage-1 finding, not a probe to train
    against (claude-reply-a889f39 sec.3 names short yield a
    guard failure that stops stage 3).
  * consumption: rl/trainer_v4.py Gate loads the file and takes
    a FIXED subsample — np.random.RandomState(20261016).choice(
    27000, size=4096, replace=False), indices sorted (Gate
    defaults subset=4096, seed=20261016, trainer_v4.py:180-187);
    the anchor's log-probs on that batch are computed once and
    never moved. The probe's role is the KL divergence budget's
    fixed instrument; nothing else about it changes here.

THE GRAVY BUILD (registered invocation, on the box, after
stage 1 completes all three corpora):

    /home/joe/tcg/rl-env/bin/python code/build_gravy_probe.py \
        --sim-root /home/joe/tcg/tcg-sim

which runs exactly:

    probe_kl.py build \
        --corpora gravy_bc/data/mirror_self \
                  gravy_bc/data/cross_self \
                  gravy_bc/data/mirror_bc \
        --per-corpus 9000 --out probe/probe_gravy_v1.jsonl

This script is the registered builder. It does NOT re-implement
the selection for the build itself — it invokes the box's own
probe_kl.py, so "verbatim" is literal — and then verifies the
output with an independent re-scan (a second implementation of
the same filter, in this file): the output is segmented by the
tool's per-corpus kept counts, and EACH corpus's kept (game,
decision) sequence must match its segment exactly.

Guards (any failure aborts; nothing is written past the failing
step's own output):
  * the output file must not already exist (a built probe is an
    artifact; it is never silently overwritten);
  * EVERY corpus's games_w*.jsonl must total its expected game
    count first (mirror_self 2,400 / cross_self 750 /
    mirror_bc 1,500 — the stage-1 completion check: game
    counts, never a DONE file) before anything is built;
  * probe_kl.py's reported kept count must equal the per-corpus
    cap for EVERY corpus (a short yield aborts, per above);
  * the independent re-scan must reproduce EACH corpus's kept
    sequence exactly.

On success it prints PROBE_FILE / PROBE_STATES / PROBE_SHA256
plus one PROBE_CORPUS line per corpus (name, games, kept) for
the stage-3 launch manifest. The probe hash is a launch-time
artifact (claude-reply-a889f39 sec.3): recorded in a builder
note and the stage-3 manifest; a recomputation mismatch at
manifest time voids the build.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

# The three stage-1 corpora (rounds/round7/code/
# gravy_corpus_driver.sh batch order) with their stage-1
# game-count guards (the driver's check_batch values).
DEFAULT_CORPORA = [
    ("mirror_self", 2400),
    ("cross_self", 750),
    ("mirror_bc", 1500),
]


def count_games(corpus):
    total = 0
    for n in sorted(os.listdir(corpus)):
        if n.startswith("games_w") and n.endswith(".jsonl"):
            with open(os.path.join(corpus, n)) as fh:
                total += sum(1 for _ in fh)
    return total


def expected_kept(corpus, per_corpus):
    """Independent re-implementation of probe_kl.py build's
    selection for ONE corpus: same walk order (os.walk, names
    sorted per directory), same filter, same cap. Returns the
    (game, decision) sequence the build must produce for this
    corpus."""
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


def parse_corpus_args(ns):
    """Resolve the corpus list: [(display_name, abs_path,
    expect_games), ...] in build order."""
    if ns.corpus is None:
        specs = [(name, os.path.join(ns.sim_root, "gravy_bc",
                                     "data", name), games)
                 for name, games in DEFAULT_CORPORA]
        return specs
    paths = [p.strip() for p in ns.corpus.split(",") if p.strip()]
    if ns.expect_games is None:
        print("ABORT: --expect-games is required with --corpora "
              "(one count per corpus, comma-separated)")
        return None
    counts = [int(x) for x in ns.expect_games.split(",")]
    if len(counts) != len(paths):
        print(f"ABORT: --expect-games has {len(counts)} counts "
              f"for {len(paths)} corpora")
        return None
    specs = []
    for p, g in zip(paths, counts):
        ap = p if os.path.isabs(p) else os.path.join(ns.sim_root, p)
        specs.append((os.path.basename(ap.rstrip("/")), ap, g))
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim-root", default="/home/joe/tcg/tcg-sim")
    ap.add_argument("--corpus", default=None,
                    help="comma-separated corpus paths (relative "
                         "to --sim-root unless absolute); default: "
                         "the three gravy_bc/data corpora")
    ap.add_argument("--expect-games", default=None,
                    help="comma-separated per-corpus game counts; "
                         "required with --corpus (defaults: "
                         "2400,750,1500)")
    ap.add_argument("--out", default=None,
                    help="default: <sim-root>/probe/probe_gravy_v1.jsonl")
    ap.add_argument("--per-corpus", type=int, default=9000)
    args = ap.parse_args()

    sim = args.sim_root
    out = args.out or os.path.join(sim, "probe", "probe_gravy_v1.jsonl")
    probe_kl = os.path.join(sim, "probe_kl.py")

    specs = parse_corpus_args(args)
    if specs is None:
        return 1

    if os.path.exists(out):
        print(f"ABORT: {out} already exists; refusing to overwrite "
              f"a built probe artifact")
        return 1
    for name, path, _g in specs:
        if not os.path.isdir(path):
            print(f"ABORT: corpus missing: {path}")
            return 1
    # Stage-1 completion check, per corpus, before anything is
    # built: game counts from games_w*.jsonl, never a DONE file.
    counted = []
    for name, path, want in specs:
        games = count_games(path)
        counted.append(games)
        if games != want:
            print(f"ABORT: corpus {name} game count {games} != "
                  f"expected {want} (stage-1 completion check: "
                  f"game counts from games_w*.jsonl, never a "
                  f"DONE file)")
            return 1
        print(f"corpus {name}: {games} games (guard ok)")

    cmd = [sys.executable, probe_kl, "build", "--corpora"] + \
          [path for _n, path, _g in specs] + \
          ["--per-corpus", str(args.per_corpus), "--out", out]
    print("running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(res.stdout)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
        print("ABORT: probe_kl.py build failed")
        return 1
    kept_lines = []
    for line in res.stdout.splitlines():
        if ": kept " in line:
            kept_lines.append(int(line.rsplit(" ", 1)[1]))
    if len(kept_lines) != len(specs):
        print(f"ABORT: probe_kl reported {len(kept_lines)} "
              f"per-corpus kept lines for {len(specs)} corpora")
        return 1
    for (name, _p, _g), kept in zip(specs, kept_lines):
        if kept != args.per_corpus:
            print(f"ABORT: corpus {name} kept {kept} != "
                  f"per-corpus cap {args.per_corpus} (short "
                  f"yield is a stage-1 finding, not a probe to "
                  f"train against)")
            return 1

    recs = [json.loads(l) for l in open(out)]
    total = sum(kept_lines)
    if len(recs) != total:
        print(f"ABORT: probe file has {len(recs)} records, "
              f"build reported {total}")
        return 1
    for r in recs:
        if len(r.get("state", {}).get("candidates", [])) < 2:
            print("ABORT: probe record with < 2 candidates")
            return 1
    # Per-corpus verification: segment the output by each
    # corpus's kept count, in build order, and check the
    # independent re-scan of EACH corpus against its segment.
    off = 0
    for (name, path, _g), kept in zip(specs, kept_lines):
        seg = recs[off:off + kept]
        off += kept
        want = expected_kept(path, args.per_corpus)
        got = [(r.get("game"), r.get("decision")) for r in seg]
        if got != want:
            print(f"ABORT: independent re-scan does not "
                  f"reproduce corpus {name}'s kept sequence")
            return 1
        print(f"corpus {name}: kept sequence verified "
              f"({kept} records)")

    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    for (name, _p, _w), games, kept in zip(specs, counted,
                                           kept_lines):
        print(f"PROBE_CORPUS {name} games={games} kept={kept}")
    print(f"PROBE_FILE {out}")
    print(f"PROBE_STATES {len(recs)}")
    print(f"PROBE_SHA256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
