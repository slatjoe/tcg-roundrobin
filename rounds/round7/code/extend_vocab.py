#!/usr/bin/env python3
"""extend_vocab.py — round-7 stage 0: append-only card-vocab extension.

Reads the Fai lineage vocab (bc2_out/card_vocab.json: {card_id: index},
379 entries, indices 0..378), collects every card id appearing in the
given deck files (whole-file whitespace tokens, in first-appearance
order), and appends any missing id at the next free indices. Every
existing (id -> index) pair is preserved exactly; the script asserts
that property before writing and refuses to write if it would move
anything.

Usage:
  extend_vocab.py --vocab-in bc2_out/card_vocab.json \
      --vocab-out gravy_bc/card_vocab_gravy.json \
      --decks decks/nats2026_eriksen_gravy_60.txt \
              decks/nats2026_ashlyn_fai_60.txt

Prints a summary (entries before/after, appended ids with their new
indices, sha256 of both files) suitable for pasting into the build
verification record.
"""
import argparse
import hashlib
import json
import sys


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def deck_ids(path):
    ids = []
    seen = set()
    with open(path) as f:
        for tok in f.read().split():
            if tok not in seen:
                seen.add(tok)
                ids.append(tok)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vocab-in", required=True)
    ap.add_argument("--vocab-out", required=True)
    ap.add_argument("--decks", nargs="+", required=True)
    args = ap.parse_args()

    with open(args.vocab_in) as f:
        vocab = json.load(f)
    if not isinstance(vocab, dict):
        print("FAIL: vocab is not a {card_id: index} object", file=sys.stderr)
        return 1
    n0 = len(vocab)
    idxs = sorted(vocab.values())
    if idxs != list(range(n0)):
        print(f"FAIL: input vocab indices are not 0..{n0 - 1} contiguous",
              file=sys.stderr)
        return 1

    wanted = []
    seen = set()
    for d in args.decks:
        for cid in deck_ids(d):
            if cid not in seen:
                seen.add(cid)
                wanted.append(cid)

    missing = [c for c in wanted if c not in vocab]
    out = dict(vocab)
    appended = []
    for cid in missing:
        out[cid] = len(out)
        appended.append((cid, out[cid]))

    # Append-only proof obligations, checked before anything is written.
    for cid, i in vocab.items():
        if out[cid] != i:
            print(f"FAIL: existing entry moved: {cid} {i} -> {out[cid]}",
                  file=sys.stderr)
            return 1
    if sorted(out.values()) != list(range(len(out))):
        print("FAIL: output indices are not contiguous", file=sys.stderr)
        return 1

    with open(args.vocab_out, "w") as f:
        json.dump(out, f, indent=0, sort_keys=True)

    print(f"vocab in : {args.vocab_in} sha256 {sha256_of(args.vocab_in)}")
    print(f"entries  : {n0} -> {len(out)}")
    print(f"appended : {len(appended)}")
    for cid, i in appended:
        print(f"  + {cid} -> {i}")
    print(f"moved    : 0 (asserted)")
    print(f"vocab out: {args.vocab_out} sha256 {sha256_of(args.vocab_out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
