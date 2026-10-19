#!/usr/bin/env python3
"""Diagnostic variant (NOT package code): on a scratch tree, extend the
round-3 trace patch so teacher rows also dump the per-key zone values
pre/post (zone_pre_keys / zone_post_keys). Names the exact global a
WITHIN_ROW(zone) hit moves. Apply AFTER patch_trace_shadow.py."""
import pathlib
import sys

tree = pathlib.Path(sys.argv[1])

pp = tree / "policy_server.php"
s = pp.read_text()
old = "function SimTrace_ZoneHash() {"
assert old in s
s = s.replace(old, """function SimTrace_ZoneDump() {
  $z = [];
  foreach (SimTrace_ZoneKeys() as $k) {
    $v = $GLOBALS[$k] ?? null;
    $z[$k] = is_array($v) ? array_slice($v, 0, 40) : $v;
  }
  return $z;
}
function SimTrace_ZoneHash() {""", 1)
pp.write_text(s)

sp = tree / "search.php"
s = sp.read_text()
old2 = '$trc["zone_post"] = SimTrace_ZoneHash();'
assert old2 in s
s = s.replace(old2, old2 + '\n      $trc["zone_post_keys"] = SimTrace_ZoneDump();', 1)
old3 = '"cand_hash" => SimTrace_CandHash($candRecs),'
assert old3 in s
s = s.replace(old3, '"zone_pre_keys" => SimTrace_ZoneDump(),\n      ' + old3, 1)
sp.write_text(s)
print("zoneprobe applied")
