<?php
// Fixture stub ONLY: stands in for the real play_game.php so
// s2_label_main.php's pin handling, row/stat stamping, and
// life-field pass-through can be exercised without a Talishar
// tree. Returns synthetic label rows and records every cfg it
// was handed. Worlds with w % 5 == 4 are horizon-ended draws
// (winner 0, outcome 0.0, horizon 1) carrying life fields --
// the shape code/search_s2.php's SimLabel_RunRollout emits.
function SimLabel_RunForSnapshot($snapDir, $meta, $cfg) {
  $log = getenv("FX_CFG_LOG");
  if ($log !== false) {
    file_put_contents($log, json_encode($cfg) . "\n", FILE_APPEND);
  }
  $snap = $meta["snap"];
  $rows = [];
  $W = intval($cfg["W"]);
  foreach ($cfg["candIdx"] as $ci) {
    for ($w = 0; $w < $W; ++$w) {
      if ($w % 5 === 4) {
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["finished" => 1, "outcome" => 0.0,
                                "winner" => 0, "horizon" => 1,
                                "life_root" => 9, "life_opp" => 12,
                                "fallbacks" => 0]];
      } else {
        $out = ($w % 2 === 0) ? 1.0 : -1.0;
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["finished" => 1, "outcome" => $out,
                                "winner" => ($out > 0 ? 1 : 2),
                                "horizon" => 0, "fallbacks" => 0]];
      }
    }
  }
  return $rows;
}
