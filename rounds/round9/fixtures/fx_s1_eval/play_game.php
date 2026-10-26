<?php
// Fixture stub ONLY: stands in for the real play_game.php so
// s1_eval_main.php's pin handling and row/stat stamping can be
// exercised without a Talishar tree. It returns synthetic label
// rows and records every cfg it was handed (the parameterization
// proof: hooks/deadline/horizon/W/seedBase forwarded intact).
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
      if ($snap === "fxB" && $w >= 22) {
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["error" => "abort"]];
      } elseif ($snap === "fxB" && $w === 21) {
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["finished" => 1, "outcome" => 0.0,
                                "winner" => 0, "fallbacks" => 0]];
      } else {
        $out = ($w % 2 === 0) ? 1.0 : -1.0;
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["finished" => 1, "outcome" => $out,
                                "winner" => ($out > 0 ? 1 : 2),
                                "fallbacks" => 0]];
      }
    }
  }
  return $rows;
}
