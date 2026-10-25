#!/usr/bin/env python3
"""patch_featurize_correction.py - the round-8 (b) featurizer
correction (design sec.4; claude-reply-926f6c3 sec.2, D1): the
featurizer's deck-count reads move from the STORE to the getter VIEW.

Base: the Fai gate tree's featurize.php,
sha256 f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92.
Product: sha256 3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a
(also shipped in full as code/featurize_corrected.php).

Exactly three edits:
  1. A helper, SimFeat_DeckIDs($player), is added before
     SimFeat_BuildState: the deck zone read through GetDeck
     (CardGetters.php - the getter family every other zone in the
     file is read through) with the featurizer's own per-zone
     treatment, SimFeat_ZoneIDs(..., DeckPieces()). This is the
     exact view-side read the round-5 census probe defined
     (patch_census_probe.py: SimFeat_Counts(SimFeat_ZoneIDs(
     GetDeck($player), DeckPieces()))).
  2. SimFeat_BuildState's "deck_counts" (line 97) reads through the
     helper instead of SimV1_DeckCards (the STORE globals
     $p1Deck/$p2Deck, policy_v1.php:44).
  3. SimFeat_LegalCounts' deck term (line 148) reads through the
     helper too. The canary's legal counts MUST move with the
     featurizer: at view>store states (the census's ARS class) a
     store-based allowance would sit below the serialized counts
     and the canary would throw on legal states.

Deliberately NOT changed:
  * SimV1_DeckCards itself - the heuristic's own deck-awareness
    (policy_v1.php pitch logic) keeps reading the store. The
    correction is featurizer-scoped; the opponent does not change.
  * The checkpoint store:=view sync (load-bearing, round-6) - it
    lives outside this file and is untouched.
  * Every other line. The product differs from the base ONLY as
    above (verified by the staged unified diff in build-package.md
    sec.1 and by the two trees' recursive diff).

Usage: patch_featurize_correction.py <tree>   (tree contains featurize.php)
Anchor-asserted (count == 1 per anchor); refuses a non-base input.
"""
import hashlib
import pathlib
import sys

BASE_SHA = "f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92"
PRODUCT_SHA = "3dcf32c9776df2fe47987a1588b5dfd719a4d697a94894b588f908eff907030a"

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/distilltree_corrected")


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


p = tree / "featurize.php"
before = sha256(p)
assert before == BASE_SHA, \
    f"refusing: {p} sha256 {before} != base {BASE_SHA}"
s = p.read_text()

EDITS = [
    # 1. the helper, inserted before SimFeat_BuildState.
    ("""function SimFeat_BuildState($player, $branch, $candidates) {""",
     """function SimFeat_DeckIDs($player) {
  // Round-8 (b) correction: the deck zone read through the getter
  // VIEW (GetDeck, CardGetters.php - the same getter family every
  // other zone in this file is read through), with the featurizer's
  // own per-zone treatment (ZoneIDs with DeckPieces()). Before this
  // correction the two deck-count reads below used SimV1_DeckCards,
  // which reads the STORE globals ($p1Deck/$p2Deck, policy_v1.php).
  // SimV1_DeckCards itself is NOT changed: the heuristic's own
  // deck-awareness (policy_v1.php) keeps reading the store; only the
  // featurizer's reads move to the view.
  $deck = &GetDeck($player);
  return SimFeat_ZoneIDs($deck, DeckPieces());
}

function SimFeat_BuildState($player, $branch, $candidates) {"""),
    # 2. BuildState's deck_counts.
    ('"deck_counts" => SimFeat_Counts(SimV1_DeckCards($player)),',
     '"deck_counts" => SimFeat_Counts(SimFeat_DeckIDs($player)),'),
    # 3. the canary's legal-count deck term.
    ('SimFeat_MergeCounts($legal, SimFeat_Counts(SimV1_DeckCards($player)));',
     'SimFeat_MergeCounts($legal, SimFeat_Counts(SimFeat_DeckIDs($player)));'),
]

for old, new in EDITS:
    assert s.count(old) == 1, f"anchor not unique: {old[:60]!r}"
    s = s.replace(old, new)
p.write_text(s)
after = sha256(p)
print(f"featurize.php: 3 edits OK")
print(f"featurize.php: sha256 before {before}")
print(f"featurize.php: sha256 after  {after}")
assert after == PRODUCT_SHA, \
    f"product sha256 {after} != registered {PRODUCT_SHA}"
print("featurize correction applied to", tree)
