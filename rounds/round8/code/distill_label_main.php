<?php
// distill_label_main.php - the round-8 offline labeler driver
// (build-package sec.2). Runs the registered teacher decision
// procedure OFFLINE from capture snapshots and emits RAW per-
// (candidate, world) rollout rows; label_reduce.py applies the
// Decide arithmetic to those rows and emits the labels.
//
// Modeled on snap_relabel_main.php (the gate-snapshot relabeler),
// with the registered differences:
//   * candIdx = the job's "selected" set - the teacher evaluates
//     exactly its registered candidate set (top-3 + prior >= 0.10,
//     cap 4), recorded by the capture arm at capture time. The
//     relabeler's all-candidates-up-to-cap shape is NOT the
//     teacher's procedure and is not used.
//   * W is pinned at 25 - the registered teacher's k. A LABEL_W
//     env that says anything else aborts the run: the L-era
//     LABEL_W=50 label sets are a different instrument (L3 value
//     labels), and silently relabeling at W=50 would distill a
//     different teacher (claude-reply-926f6c3 sec.1).
//   * pair "va" - the deployed teacher's continuation.
//
// Usage: php distill_label_main.php <deck> <deck> --policy-search --games 1
//   (argv mimics the label drivers so play_game loads the search
//   bootstrap and returns under LABEL_DRIVER)
// Each job: {snap_dir, snap, game, player, branch, turn, cands,
//   selected, prior_pick}
// Env: DISTILL_JOBS, DISTILL_OUT, DISTILL_SEED (world seed base;
//   job ji uses seedBase + ji * 100003, the meas convention),
//   TCG_POLICY_SOCK - the PRODUCTION server (81ef2cdb...). The
//   label path's eval requests are rejected by the patched tree
//   server (round-3 R12); label work uses the production server,
//   and this main runs in the NATIVE tree so rollout featurization
//   is the gated teacher's own (featurize f81193e0...).
//
// Concurrency: ONE label process per tree. SimLabel_RunForSnapshot
// wipes the fixed Games/label_scratch/ dir and Games/<game>/, so
// concurrent label processes in one tree collide; the corpus
// runner shards jobs across separate tree copies instead.
$jobsFile = getenv("DISTILL_JOBS"); $outFile = getenv("DISTILL_OUT");
$seedBase = intval(getenv("DISTILL_SEED") ?: 424242);
$wEnv = getenv("LABEL_W");
if ($wEnv !== false && intval($wEnv) !== 25) {
  fwrite(STDERR, "ABORT: LABEL_W=$wEnv - the registered teacher is k=25; "
    . "the round-8 labeler refuses any other W\n");
  exit(2);
}
putenv("LABEL_DRIVER=1");
include "play_game.php"; // loads vendor + search.php, returns under LABEL_DRIVER
$W = 25;
$jobs = [];
foreach (file($jobsFile) as $ln) {
  $ln = trim($ln); if ($ln === "") continue;
  $j = json_decode($ln, true); if (is_array($j)) $jobs[] = $j;
}
fwrite(STDERR, "distill label jobs=" . count($jobs) . " W=$W\n");
foreach ($jobs as $ji => $j) {
  $t0 = microtime(true);
  $meta = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]), "branch" => strval($j["branch"]),
           "cands" => $j["cands"]];
  $cfg = ["W" => $W, "cap" => count($j["cands"]),
          "seedBase" => $seedBase + $ji * 100003,
          "pair" => "va", "candIdx" => $j["selected"]];
  try {
    $rows = SimLabel_RunForSnapshot(rtrim($j["snap_dir"], "/") . "/", $meta, $cfg);
  } catch (Throwable $e) {
    fwrite(STDERR, "snap " . $j["snap"] . " failed: " . $e->getMessage() . "\n");
    continue;
  }
  $fh = fopen($outFile, "a");
  foreach ($rows as $r) {
    $r["prior_pick"] = intval($j["prior_pick"]);
    $r["selected"] = $j["selected"];
    $r["game"] = strval($j["game"]);
    $r["branch"] = strval($j["branch"]);
    $r["player"] = intval($j["player"]);
    $r["turn"] = intval($j["turn"] ?? 0);
    $r["seed_base"] = $seedBase + $ji * 100003;
    fwrite($fh, json_encode($r) . "\n");
  }
  fclose($fh);
  fwrite(STDERR, "done " . $j["snap"] . " rows=" . count($rows)
    . " secs=" . round(microtime(true) - $t0, 1) . "\n");
}
fwrite(STDERR, "DISTILL-LABEL-DONE\n");
