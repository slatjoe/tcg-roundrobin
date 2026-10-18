#!/usr/bin/env python3
"""Arsenal rebuild v2 - the whitelist rebuild must keep the line's
TOKEN STRUCTURE. Found by the R2 canary's first production run
(2026-10-18): the parser drops empty tokens when splitting zone
lines, so clearing fields to "" collapsed the arsenal line from 7
tokens to 2 and the sampled arsenal card VANISHED from the world
(the same defect, via one cleared field, existed in the patch-1
edit - every earlier battery missed it because nothing compared the
arsenal after the step boundary).

Across 1,524 arsenal slots in the measurement snaps the structural
fields are constant: field2="1", field3="0", field4="0", field6="0";
only field5 (a subcard/identity descriptor naming the true card)
varies. A sampled slot is therefore rebuilt as:
  [sampled id, facing (public, from the true line), "1","0","0","0","0"]
A slot whose assigned id equals the true slot's id (face-up fixed
cards; a sample that happens to draw the true card) keeps its
original fields verbatim - that card's true state is the correct
state for it. Env SIM_ARS_DESC=1 instead writes field5 as a
descriptor for the SAMPLED card (reusing the true descriptor's tail
number) - an experiment arm to test whether the descriptor affects
play; default (unset) is "0" (no descriptor).
"""
import sys

path = sys.argv[1]
src = open(path).read()

old = """  // Arsenal: REBUILD each slot from a whitelist - the assigned card
  // id plus the slot's public facing field; every other field is
  // cleared (field 5 of the old patch named the true card).
  $arsIDs = array_values((array)($a["arsenal"] ?? []));
  $fields = $lines[$arsIdx] === "" ? [] : explode(" ", $lines[$arsIdx]);
  $pieces = ArsenalPieces();
  $slots = 0;
  for ($i = 0; $i + $pieces - 1 < count($fields); $i += $pieces) {
    if (($fields[$i] ?? "") !== "") ++$slots;
  }
  if (count($arsIDs) !== $slots) return false;
  for ($k = 0; $k < $slots; ++$k) {
    $base = $k * $pieces;
    $facing = strval($fields[$base + 1] ?? "DOWN");
    for ($j = 0; $j < $pieces; ++$j) $fields[$base + $j] = "";
    $fields[$base] = strval($arsIDs[$k]);
    $fields[$base + 1] = $facing;
  }"""
new = """  // Arsenal: REBUILD each sampled slot from a whitelist - the
  // assigned card id plus the slot's public facing field, with the
  // structural fields at their canonical constants (field2=1, rest
  // 0; measured constant across 1,524 snap slots). Fields must stay
  // NON-EMPTY: the parser drops empty tokens and the stride parse
  // collapses, vanishing the card. Field 5 (a descriptor naming the
  // true card) becomes "0" (none) unless SIM_ARS_DESC=1 (experiment:
  // descriptor for the sampled card). A slot whose assigned id is
  // the true card (face-up fixed, or sampled by coincidence) keeps
  // its original fields - that card's true state is correct for it.
  $arsIDs = array_values((array)($a["arsenal"] ?? []));
  $fields = $lines[$arsIdx] === "" ? [] : explode(" ", $lines[$arsIdx]);
  $pieces = ArsenalPieces();
  $slots = 0;
  for ($i = 0; $i + $pieces - 1 < count($fields); $i += $pieces) {
    if (($fields[$i] ?? "") !== "") ++$slots;
  }
  if (count($arsIDs) !== $slots) return false;
  for ($k = 0; $k < $slots; ++$k) {
    $base = $k * $pieces;
    if (strval($fields[$base] ?? "") === strval($arsIDs[$k])) continue;
    $facing = strval($fields[$base + 1] ?? "DOWN");
    $desc = "0";
    if (getenv("SIM_ARS_DESC") === "1") {
      $dp = explode(";", strval($fields[$base + 5] ?? ""));
      $desc = "2;" . strval($arsIDs[$k]) . ";" . ($dp[2] ?? "0");
    }
    $fields[$base] = strval($arsIDs[$k]);
    $fields[$base + 1] = $facing;
    $fields[$base + 2] = "1";
    $fields[$base + 3] = "0";
    $fields[$base + 4] = "0";
    $fields[$base + 5] = $desc;
    $fields[$base + 6] = "0";
  }"""
assert src.count(old) == 1, "anchor count %d" % src.count(old)
src = src.replace(old, new)
open(path, "w").write(src)
print("arsenal-rebuild2 patch applied to", path)
