#!/usr/bin/env python3
"""test_vocab_assertion.py — round-7 stage 0: the LOUD vocab test.

The v3 slot encoder (bc_features_v3.py:_slot_index) maps an unknown
card id SILENTLY to the EMPTY slot index. This test makes that failure
loud: for every unique card id in the given deck files, it places the
card in each slot-bearing position (own hand, own arsenal, opponent
pitch) of a real state template and asserts, through the actual
featurize_state_v3 code path, that the slot encodes the card's own
vocab index — never the EMPTY index.

A card missing from the vocab fails by name, exit code 1.

Usage:
  test_vocab_assertion.py --vocab <card_vocab.json> \
      --features-dir <dir containing bc_features_v2.py + bc_features_v3.py> \
      --state-template <jsonl whose records carry a "state" dict> \
      --decks <deck file> [more deck files ...]

Registered expectations for the round-7 build test:
  * --vocab bc2_out/card_vocab.json (unextended, 379):
    FAIL, exit 1, exactly one problem card named: nullrune_hood
    (the Fai deck passes in full as the control).
  * --vocab <extended 380-entry vocab>: PASS, exit 0, 37/37 Gravy
    ids and 34/34 Fai ids slot-verified x3 positions each.
"""
import argparse
import copy
import json
import sys

sys.path.insert(0, ".")  # replaced below by --features-dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--features-dir", required=True)
    ap.add_argument("--state-template", required=True)
    ap.add_argument("--decks", nargs="+", required=True)
    args = ap.parse_args()

    sys.path.insert(0, args.features_dir)
    import bc_features_v3 as F3

    with open(args.vocab) as f:
        vocab = json.load(f)
    empty_idx = len(vocab)

    with open(args.state_template) as f:
        template = json.loads(f.readline())["state"]

    failures = []
    checked = {}

    def place(state, player, hand, arsenal, opp_pitch):
        s = copy.deepcopy(state)
        s["player"] = player
        s["main_player"] = player
        s["chain_attack"] = None
        s["hand"] = hand
        s["arsenal"] = arsenal
        board = s.get("board")
        opp_seat = 3 - player
        if isinstance(board, list):
            while len(board) < 2:
                board.append({})
            for i, b in enumerate(board):
                if isinstance(b, dict):
                    b["pitch"] = opp_pitch if (i + 1) == opp_seat else []
        elif isinstance(board, dict):
            for k in list(board.keys()):
                if isinstance(board[k], dict):
                    board[k]["pitch"] = (
                        opp_pitch if (int(k) + 1) == opp_seat else [])
        s["board"] = board
        return s

    for deck_path in args.decks:
        ids = []
        seen = set()
        with open(deck_path) as f:
            for tok in f.read().split():
                if tok not in seen:
                    seen.add(tok)
                    ids.append(tok)
        n_ok = 0
        for cid in ids:
            want = vocab.get(cid)
            problems = []
            # own hand (slot 0)
            s = place(template, 1, [cid], [], [])
            _, own, _ = F3.featurize_state_v3(s, vocab)
            if own[0] == empty_idx or own[0] != want:
                problems.append(f"hand slot -> {own[0]}")
            # own arsenal (slot 8)
            s = place(template, 1, [], [cid], [])
            _, own, _ = F3.featurize_state_v3(s, vocab)
            if own[8] == empty_idx or own[8] != want:
                problems.append(f"arsenal slot -> {own[8]}")
            # opponent pitch (opp slot 0)
            s = place(template, 1, [], [], [cid])
            _, _, opp = F3.featurize_state_v3(s, vocab)
            if opp[0] == empty_idx or opp[0] != want:
                problems.append(f"opp-pitch slot -> {opp[0]}")
            if problems:
                failures.append((deck_path, cid, want, problems))
            else:
                n_ok += 1
        checked[deck_path] = (n_ok, len(ids))
        print(f"{deck_path}: {n_ok}/{len(ids)} ids slot-verified "
              f"(hand + arsenal + opp-pitch)")

    if failures:
        print(f"\nFAIL: {len(failures)} card id(s) do not resolve to "
              f"their own slot index under vocab {args.vocab} "
              f"(EMPTY index = {empty_idx}):")
        for deck_path, cid, want, problems in failures:
            print(f"  {cid} (deck {deck_path}, vocab index {want}): "
                  + "; ".join(problems))
        return 1
    print(f"\nPASS: every deck card id resolves to its own slot index "
          f"under vocab {args.vocab} (EMPTY index = {empty_idx})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
