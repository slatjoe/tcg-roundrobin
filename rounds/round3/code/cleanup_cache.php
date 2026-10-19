<?php
// R16 cleanup helper (round-3 rerun): delete the SHMOP cache segments
// for one or more game ids. The paired driver calls this after a
// timeout kill for each game dir that appeared during the killed
// game, so a killed child's parsed-gamestate segment does not leak
// (the launch grew ipcs by +414 segments; killed children never run
// the engine's own end-of-game DeleteCache).
//
// The segments are keyed by the game name and by GamestateID(name);
// DeleteCache (vendor SHMOPLibraries) removes both. This file lives
// at the tree root and includes the vendor library directly - the
// library is self-contained function definitions plus constants.
//
// Usage: php cleanup_cache.php <gameid> [<gameid> ...]
// Exit 0 on success (missing segments are a no-op), 2 on usage.
if ($argc < 2) {
  fwrite(STDERR, "usage: cleanup_cache.php <gameid> [<gameid> ...]\n");
  exit(2);
}
require __DIR__ . "/vendor/talishar/Libraries/SHMOPLibraries.php";
foreach (array_slice($argv, 1) as $g) {
  $g = strval($g);
  if ($g === "") continue;
  DeleteCache($g);
  echo "DeleteCache($g) done\n";
}
