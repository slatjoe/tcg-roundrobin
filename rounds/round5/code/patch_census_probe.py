#!/usr/bin/env python3
"""Round-5 (b) census probe (claude-reply-6b843d7 sec.3): at each
bridge featurization, compare the STORE-derived deck counts the
featurizer serialized against the VIEW-derived deck counts for the
deciding player, and log the comparison to a side file.

The finding this answers (round-4 O fleet, claude-reply-6b843d7
sec.3): 5 teacher decisions aborted when Decide's post-sync root
canary caught the learner's OWN cards counted once too often in
the root state (two cards per abort, each at legal+1). The pointed
mechanism is the mixed-source featurization: SimFeat_BuildState
takes deck_counts from SimV1_DeckCards, which reads the STORE
globals ($p1Deck/$p2Deck, policy_v1.php:44), while every other
zone is read through the CardGetters VIEW family. Between syncs a
just-moved card can sit in a view zone and still be in the store's
deck, so the featurized state double-counts it. The bridge's own
canary (policy_server.php:360, on Choose's pre-sync state) cannot
see this class, so its frequency in ordinary bridge play - the
configuration of every eval this project has run - is unknown.
The census measures that frequency.

Site (decided from the code; defended in census-package.md sec.2):
featurize.php SimFeat_BuildState, one block inserted between the
$state construction and its return. BuildState is the
featurization itself; it receives ($player, $branch, $candidates)
as arguments (branch and turn need no plumbing - both are already
in $state); in plain bridge mode (play_game.php --policy-server,
search.php never loaded) its only callers are the two bridge
funnels, SimPolicyServer_Choose (policy_server.php:359) and the
DQ funnel (policy_server.php:448), so one site sees every bridge
featurization exactly once.

Definitions (operational; census-package.md sec.3):
  store side = $state["deck_counts"] verbatim - the exact map the
    featurizer serialized for the net - with the "" key dropped
    (empty strings are not cards; the canary's MergeCounts drops
    them too).
  view side  = SimFeat_Counts(SimFeat_ZoneIDs(GetDeck($player),
    DeckPieces())) - GetDeck (CardGetters.php:159) is the deck
    member of the same getter family the featurizer reads every
    other zone through, and ZoneIDs with DeckPieces()==1 applies
    the featurizer's own per-zone treatment (empty slots dropped).
  disagreement = any card id whose two counts differ. For a card
    with store > view the row also records view_elsewhere: the
    card's occurrences in the deciding player's OTHER view zones
    as serialized in $state (hand, arsenal, board allies/auras/
    items/character/pitch, graveyard/banished counts) - the
    double-count signature attribution.

Probe discipline: the block reads $state and engine globals only,
writes nothing back, and returns nothing; it is gated on the
CENSUS_LOG env var (unset => one getenv of added work); its body
is wrapped so a census error can never reach play; the log write
is a single FILE_APPEND|LOCK_EX line per featurization.

Deliberately NOT changed:
  * $state itself - the block runs after the array is built and
    before `return $state;`, and never writes to it (the unset()
    acts on a local copy of the deck_counts map).
  * SimV1_DeckCards, GetDeck, the sync discipline
    (Build*Gamestate / DoGamestateUpdate / the checkpoint's
    store:=view sync), the canary, and every caller.
  * No other file. search.php in the census tree stays at the
    O build's hash; the probe lives only in the census tree's
    featurize.php.

Applies to the O tree's featurize.php
(sha256 f81193e0b8a284c4b13a63fd36956ab29614776dd9bdd1c6462537b87a5f0b92).

Usage: patch_census_probe.py <tree>   (tree contains featurize.php)
"""
import hashlib
import pathlib
import sys

tree = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/censustree")


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def patch(fname, pairs):
    p = tree / fname
    before = sha256(p)
    s = p.read_text()
    for old, new in pairs:
        assert old in s, f"anchor missing in {fname}: {old[:70]!r}"
        assert s.count(old) == 1, \
            f"anchor not unique in {fname}: {old[:70]!r}"
        s = s.replace(old, new)
    p.write_text(s)
    print(f"{fname}: {len(pairs)} edits OK")
    print(f"{fname}: sha256 before {before}")
    print(f"{fname}: sha256 after  {sha256(p)}")


patch("featurize.php", [
    # The probe block: inserted between the $state construction and
    # its return in SimFeat_BuildState (featurize.php:110).
    ("""  ];
  return $state;
}""",
     """  ];
  // ---- (b) census probe (round 5; claude-reply-6b843d7 sec.3) ----
  // Inference-only: compare the deck counts just serialized from
  // the STORE ($state["deck_counts"], via SimV1_DeckCards) against
  // the counts the VIEW presents for the same deck (GetDeck, the
  // getter family every other zone above was read through). One
  // JSON row per featurization is appended to CENSUS_LOG. Reads
  // $state and engine globals only; writes nothing back; swallows
  // its own errors so a census can never break play. With
  // CENSUS_LOG unset the only added work is one getenv.
  $censusLog = getenv("CENSUS_LOG");
  if ($censusLog !== false && $censusLog !== "") {
    try {
      $censusStore = $state["deck_counts"] ?? [];
      unset($censusStore[""]);
      $censusDeckView = &GetDeck($player);
      $censusView = SimFeat_Counts(SimFeat_ZoneIDs($censusDeckView, DeckPieces()));
      $censusDiffs = [];
      $censusIds = array_unique(array_merge(array_keys($censusStore), array_keys($censusView)));
      foreach ($censusIds as $censusCid) {
        $censusSv = intval($censusStore[$censusCid] ?? 0);
        $censusVv = intval($censusView[$censusCid] ?? 0);
        if ($censusSv !== $censusVv) {
          $censusElse = 0;
          if ($censusSv > $censusVv) {
            foreach (($state["hand"] ?? []) as $censusH) {
              if (strval($censusH) === $censusCid) $censusElse++;
            }
            foreach (($state["arsenal"] ?? []) as $censusH) {
              if (strval($censusH) === $censusCid) $censusElse++;
            }
            $censusBoard = $state["board"][$player] ?? [];
            foreach (["allies", "auras", "items", "character", "pitch"] as $censusKey) {
              foreach (($censusBoard[$censusKey] ?? []) as $censusH) {
                if (strval($censusH) === $censusCid) $censusElse++;
              }
            }
            foreach (["graveyard", "banished"] as $censusKey) {
              $censusElse += intval(($censusBoard[$censusKey] ?? [])[$censusCid] ?? 0);
            }
          }
          $censusDiffs[$censusCid] = [$censusSv, $censusVv, $censusElse];
        }
      }
      $censusRow = [
        "game" => strval($GLOBALS["gameName"] ?? ""),
        "player" => $player,
        "branch" => strval($state["branch"] ?? $branch),
        "turn" => intval($state["turn"] ?? 0),
        "agree" => ($censusDiffs === []),
        "diffs" => $censusDiffs,
      ];
      @file_put_contents($censusLog, json_encode($censusRow) . "\\n", FILE_APPEND | LOCK_EX);
    } catch (Throwable $censusErr) {
      // A census failure must never reach play.
    }
  }
  return $state;
}"""),
])

print("census-probe patch applied to", tree)
