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
//   * W is a RUN-PINNED parameter (round-8 amendment,
//     claude-reply-597d181 sec.3, Option 1 - Joe's choice
//     2026-10-25): the run's W is pinned by the LABEL_W env
//     (the registered teacher's k = 25 when LABEL_W is unset).
//     EVERY job must carry a "W" equal to the pin; a job whose
//     W differs, or that carries no W, ABORTS the run before
//     any labeling. The L-era LABEL_W=50 label sets are a
//     different instrument (L3 value labels); the pin, the
//     per-job W, and W recorded on every raw row make which
//     instrument produced a label set auditable from the rows
//     themselves - W can never drift silently (the hazard in
//     claude-reply-926f6c3 sec.1).
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
//
// DISTILL_SPLIT_CANDS=1 (the pilot's deadline-accounting mode,
// fix package): each job's candidates are labeled in SEPARATE
// SimLabel_RunForSnapshot calls, one per candidate, with the
// SAME per-job seed base - the world seed for (candidate, world)
// is seedBase + w*31337 regardless of grouping, so the emitted
// rows are identical to the grouped call's; only the invocation
// grouping differs. Each call's wall time is that candidate
// batch's wall time (the batch forks its W children together and
// collects them against the label path's 300 s deadline), which
// is what the pilot's deadline accounting reads: a batch whose
// wall exceeds the live teacher's 180 s candidate deadline had
// worlds finishing after 180 s. Per-candidate rows {snap, cand,
// secs, worlds, finished, timeout_errs} go to the jsonl file
// named by env DISTILL_TIMINGS. The corpus runner never sets
// this mode.
$jobsFile = getenv("DISTILL_JOBS"); $outFile = getenv("DISTILL_OUT");
$seedBase = intval(getenv("DISTILL_SEED") ?: 424242);
$wEnv = getenv("LABEL_W");
$W = 25; // the registered teacher's k - the pin when LABEL_W is unset
if ($wEnv !== false) {
  if (intval($wEnv) <= 0
      || strval(intval($wEnv)) !== trim(strval($wEnv))) {
    fwrite(STDERR, "ABORT: LABEL_W=$wEnv is not a positive integer\n");
    exit(2);
  }
  $W = intval($wEnv);
}
putenv("LABEL_DRIVER=1");
include "play_game.php"; // loads vendor + search.php, returns under LABEL_DRIVER
$jobs = [];
foreach (file($jobsFile) as $ln) {
  $ln = trim($ln); if ($ln === "") continue;
  $j = json_decode($ln, true); if (is_array($j)) $jobs[] = $j;
}
// Per-job W pin: every job must carry the run's pinned W. A
// mismatch (or a missing W) aborts before any labeling - a
// label set is produced by exactly one instrument, named by
// the pin and restated on every job and every raw row.
foreach ($jobs as $ji => $j) {
  if (!isset($j["W"]) || intval($j["W"]) !== $W) {
    fwrite(STDERR, "ABORT: job $ji (snap " . ($j["snap"] ?? "?")
      . ") carries W="
      . (isset($j["W"]) ? json_encode($j["W"]) : "<missing>")
      . " - the run's pinned W is $W (LABEL_W)\n");
    exit(2);
  }
}
fwrite(STDERR, "distill label jobs=" . count($jobs) . " W=$W\n");
$splitCands = getenv("DISTILL_SPLIT_CANDS") === "1";
$timingsFile = getenv("DISTILL_TIMINGS");
foreach ($jobs as $ji => $j) {
  $t0 = microtime(true);
  $meta = ["snap" => $j["snap"], "game" => strval($j["game"]),
           "player" => intval($j["player"]), "branch" => strval($j["branch"]),
           "cands" => $j["cands"]];
  $cfg = ["W" => $W, "cap" => count($j["cands"]),
          "seedBase" => $seedBase + $ji * 100003,
          "pair" => "va", "candIdx" => $j["selected"]];
  $rows = [];
  try {
    if ($splitCands) {
      foreach ($j["selected"] as $ci) {
        $ct0 = microtime(true);
        $cfgC = $cfg; $cfgC["candIdx"] = [intval($ci)];
        $rowsC = SimLabel_RunForSnapshot(
          rtrim($j["snap_dir"], "/") . "/", $meta, $cfgC);
        $fin = 0; $toErr = 0;
        foreach ($rowsC as $r) {
          $res = $r["result"] ?? null;
          if (is_array($res) && ($res["error"] ?? null) === "timeout") {
            $toErr++;
          } elseif (is_array($res) && !isset($res["error"])
                    && !empty($res["finished"])) {
            $fin++;
          }
        }
        if ($timingsFile) {
          file_put_contents($timingsFile, json_encode([
            "snap" => $j["snap"], "cand" => intval($ci),
            "secs" => round(microtime(true) - $ct0, 2),
            "worlds" => count($rowsC), "finished" => $fin,
            "timeout_errs" => $toErr]) . "\n", FILE_APPEND);
        }
        $rows = array_merge($rows, $rowsC);
      }
    } else {
      $rows = SimLabel_RunForSnapshot(
        rtrim($j["snap_dir"], "/") . "/", $meta, $cfg);
    }
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
    $r["W"] = $W;
    fwrite($fh, json_encode($r) . "\n");
  }
  fclose($fh);
  fwrite(STDERR, "done " . $j["snap"] . " rows=" . count($rows)
    . " secs=" . round(microtime(true) - $t0, 1) . "\n");
}
fwrite(STDERR, "DISTILL-LABEL-DONE\n");
