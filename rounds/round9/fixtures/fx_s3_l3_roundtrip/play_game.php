<?php
// Fixture stub ONLY (Stage 3 copy of fx_s2_label/play_game.php
// with ONE change): stands in for the real play_game.php so
// s2_label_main.php's pin handling, row/stat stamping, and
// life-field pass-through can be exercised without a Talishar
// tree, and so stage3_attr_analyze.py's reads are hand-
// computable. Records every cfg it was handed. Worlds with
// w % 5 == 4 are horizon-ended draws (winner 0, outcome 0.0,
// horizon 1) carrying life fields 9/12, as in the Stage 2
// stub. NON-horizon outcomes depend on CANDIDATE PARITY
// (the change): even cand -> +1 on even w, -1 on odd w;
// odd cand -> +1 on ALL non-horizon w. With jobs_ok's picks
// (fxA teacher=1 odd / prior=0 even; fxB teacher=0 even /
// prior=2 even): fxA per-world primary diffs are +1 on the
// 20 odd non-horizon worlds and 0 elsewhere -> diff 0.4;
// fxB's candidates are both even -> diff 0. Mean over the
// 2 jobs = 0.2 for primary, draw05 and lifediff alike (the
// horizon worlds score 0 / 0.5 / life-behind-0 identically
// for both candidates).
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
        if ($ci % 2 === 1) {
          $out = 1.0;
        } else {
          $out = ($w % 2 === 0) ? 1.0 : -1.0;
        }
        $rows[] = ["snap" => $snap, "cand" => $ci, "world" => $w,
                   "result" => ["finished" => 1, "outcome" => $out,
                                "winner" => ($out > 0 ? 1 : 2),
                                "horizon" => 0, "fallbacks" => 0]];
      }
    }
  }
  return $rows;
}
