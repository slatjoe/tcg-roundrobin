#!/bin/bash
# Round-10 Step 0 probe: the COMPLETION step
# (fix pass 6, package doc sec.15). The
# recovery run of 2026-10-29
# (step0-probe-recovery-run.md) completed every
# step through the probe report, then its
# influence step died with
#   NameError: name 'logo_by_lever' is not
#   defined
# at probe_influence.py's LOGO loop, and the
# manifest step that follows it in
# run_probe_recovery.sh never ran. The
# recovery script is single-shot and refuses
# re-invocation, so the registered read cannot
# be finished by re-running it. This script
# runs ONLY the two steps that never ran --
# the influence read and the manifest -- from
# the run's PUBLISHED outputs
# (data/step0_recovery/, data/step0/), offline,
# after the fix-pass-6 repair of
# probe_influence.py. It recomputes no eval,
# label or report row.
#
# Discipline, mirroring the recovery's:
#   * refuses if the completion's outputs
#     already exist (probe_influence.json or
#     recovery_manifest.json present, or a
#     NON-EMPTY probe_influence.txt -- the
#     run's own redirect artifact is 0 bytes
#     and is overwritten by this step's
#     redirect, exactly as the recovery's
#     would have been);
#   * refuses if any input is missing;
#   * verifies sha256 BEFORE computing: the
#     fixed probe_influence.py and the modules
#     it loads at run time, the settings, and
#     the four run inputs the registered read
#     stands on -- probe_report.json,
#     label_read.json, jobs_merged.jsonl and
#     labels_merged.jsonl.gz. The labels are
#     pinned twice: the published .gz file's
#     bytes, and the decompressed content
#     against the run record's stated raw
#     sha256 (c2688f24...) with its stated row
#     count (71,500). probe_influence.py reads
#     labels through a plain open(), so the
#     verified decompression is what it reads.
#   * the capture-games list is NOT among the
#     published outputs (the run's
#     eval_jobs_report.json never left the
#     box). It is rebuilt here from the
#     published driver rows
#     (data/step0/cap_s1_b1.jsonl +
#     cap_s2_b1.jsonl), sorted -- the order
#     build_probe_eval_jobs.py itself wrote
#     (its games_list is sorted(games)) -- and
#     the count must be 90. Every gain and
#     interval in the influence read is
#     invariant to the list's order (the
#     cluster bootstrap sorts game ids
#     internally); the list only enumerates
#     the 90 capture games.
# Runs once, on Joe's go after the fix-pass-6
# review. Outputs land in data/step0_recovery/
# beside the run's files.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CODE_DIR="$HERE"
ROOT="$(cd "$HERE/.." && pwd)"
REC="$ROOT/data/step0_recovery"
S0="$ROOT/data/step0"
PY=${PY:-python3}

echo "== completion step: influence + manifest only =="
echo "code dir: $CODE_DIR"
echo "outputs:  $REC"

# ---- 0. refuse if this completion (or the
# run's own manifest) already produced output
if [ -e "$REC/probe_influence.json" ]; then
  echo "ABORT: $REC/probe_influence.json already exists -- the influence output is already produced; refusing to overwrite."
  exit 1
fi
if [ -e "$REC/recovery_manifest.json" ]; then
  echo "ABORT: $REC/recovery_manifest.json already exists -- the manifest is already produced; refusing to overwrite."
  exit 1
fi
if [ -s "$REC/probe_influence.txt" ]; then
  echo "ABORT: $REC/probe_influence.txt exists and is non-empty -- not the run's 0-byte redirect artifact; refusing to overwrite."
  exit 1
fi

# ---- 1. every input present
for f in \
  "$REC/probe_report.json" \
  "$REC/label_read.json" \
  "$REC/jobs_merged.jsonl" \
  "$REC/labels_merged.jsonl.gz" \
  "$REC/eval_completeness.json" \
  "$REC/jobs_supp.jsonl" \
  "$REC/labels_supp.jsonl" \
  "$REC/label_stats_supp.jsonl" \
  "$REC/jobs_suppB.jsonl" \
  "$REC/labels_suppB.jsonl" \
  "$REC/label_stats_suppB.jsonl" \
  "$REC/capalign/capalign_classes.json" \
  "$REC/capalign/capalign_states.jsonl" \
  "$REC/capalign/capalign_summary.json" \
  "$REC/capalign/capalign_reclassification.json" \
  "$REC/capalign/supplementary_jobs_report.json" \
  "$S0/jobs_all.jsonl" \
  "$S0/labels_all.jsonl.gz" \
  "$S0/eval_jobs.jsonl" \
  "$S0/evals_all.jsonl.gz" \
  "$S0/eval_states.jsonl" \
  "$S0/cap_s1_b1.jsonl" \
  "$S0/cap_s2_b1.jsonl" \
  "$ROOT/step0-probe-recovery-run.md" \
  "$CODE_DIR/settings_probe.json" \
  "$CODE_DIR/probe_influence.py" \
  "$CODE_DIR/probe_label_analyze.py" \
  "$CODE_DIR/analyze_l3.py" \
  "$CODE_DIR/stage0_report.py"; do
  if [ ! -f "$f" ]; then
    echo "ABORT: required input missing: $f"
    exit 1
  fi
done

expect_hash() {
  # $1=file $2=expected sha256 $3=label
  case "$2" in
    ????????????????????????????????????????????????????????????????)
      ;;
    *)
      echo "ABORT: expected hash for $3 is not 64 hex chars: [$2]"
      exit 1 ;;
  esac
  got=$(sha256sum "$1" | awk '{print $1}')
  if [ "$got" != "$2" ]; then
    echo "ABORT: sha256 mismatch for $3"
    echo "  file:     $1"
    echo "  expected: $2"
    echo "  got:      $got"
    exit 1
  fi
  echo "hash ok: $3 $got"
}

# ---- 2. code pins (the fixed influence read
# and the modules it loads at run time)
expect_hash "$CODE_DIR/probe_influence.py" \
  dc79bdaddb30980138c3c72b8321f4fbb7ed23675911c9b835caf7d896e96a9a \
  "completion probe_influence.py (fix pass 6: logo_by_lever initialized; doc sec.15)" || exit 1
expect_hash "$CODE_DIR/probe_label_analyze.py" \
  131661e877bfd67b412b65609e74f69ad8ddfbf1dee50d5aa6fc8b19f896e927 \
  "completion probe_label_analyze.py (loaded by probe_influence.py)" || exit 1
expect_hash "$CODE_DIR/analyze_l3.py" \
  16017ffa71df0b37904a999a37fe1a8cc73a1e404b744ef9ac6c8312d66769b9 \
  "completion analyze_l3.py (loaded by probe_influence.py)" || exit 1
expect_hash "$CODE_DIR/stage0_report.py" \
  5c7e5393a3125146788626ba6293f42dd926dafad7a4c8d44e6d0b1de4bb59bf \
  "completion stage0_report.py (loaded by probe_influence.py)" || exit 1
expect_hash "$CODE_DIR/settings_probe.json" \
  5af0c715442e8d7208e89da9f197dfc458a55aef22182b551f64d7f3eedca2bb \
  "completion settings_probe.json" || exit 1

# ---- 3. the run's inputs, pinned to the run
# record's stated hashes / the published files
expect_hash "$REC/probe_report.json" \
  f2e6e9666308250a643ec23a9e03c0f891be249ec67b2aab48018f244fdfda44 \
  "run input probe_report.json (the registered report)" || exit 1
expect_hash "$REC/label_read.json" \
  85bcd08de34736c2cb343d67c1e03999cab9b343aa7298969e98af7a5e0af15b \
  "run input label_read.json" || exit 1
expect_hash "$REC/jobs_merged.jsonl" \
  78f2f2e03fba575eedcc0593a03c918bfb194f3ad5c10b031aa471fa23ef1f28 \
  "run input jobs_merged.jsonl (715 jobs)" || exit 1
expect_hash "$REC/labels_merged.jsonl.gz" \
  a5f9a6158cf6f8d03feb775cc913bd81c726c04f366ade9b07b0e5cdbbfb18ba \
  "run input labels_merged.jsonl.gz (published file bytes)" || exit 1

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# the labels' decompressed content, pinned to
# the run record's stated raw sha256 + count
gzip -dc "$REC/labels_merged.jsonl.gz" \
  > "$WORK/labels_merged.jsonl" || {
  echo "ABORT: labels_merged.jsonl.gz does not decompress."
  exit 1
}
RAW_HASH=$(sha256sum "$WORK/labels_merged.jsonl" | awk '{print $1}')
if [ "$RAW_HASH" != "c2688f24c7db2f16f4f4e515280cb24e63a4ee9dd4b699bdfe5f2adf0f0c738c" ]; then
  echo "ABORT: decompressed labels sha256 mismatch (the run record's stated raw hash)"
  echo "  expected: c2688f24c7db2f16f4f4e515280cb24e63a4ee9dd4b699bdfe5f2adf0f0c738c"
  echo "  got:      $RAW_HASH"
  exit 1
fi
echo "hash ok: labels_merged.jsonl (decompressed content) $RAW_HASH"
ROWS=$(awk 'END {print NR}' "$WORK/labels_merged.jsonl")
if [ "$ROWS" != "71500" ]; then
  echo "ABORT: labels_merged row count is $ROWS, the run record states 71500."
  exit 1
fi
echo "rows ok: labels_merged.jsonl $ROWS"

# the capture-games list, rebuilt from the
# published driver rows (sorted, as the run's
# own builder wrote it); the count must be 90
"$PY" - "$S0/cap_s1_b1.jsonl" "$S0/cap_s2_b1.jsonl" \
  "$WORK/capture_games.json" <<'PYEOF'
import json, sys
games = set()
for path in sys.argv[1:3]:
    for line in open(path):
        line = line.strip()
        if line:
            games.add(str(json.loads(line)["gamename"]))
games = sorted(games)
if len(games) != 90:
    print("ABORT: driver rows carry %d distinct capture games, expected 90" % len(games))
    sys.exit(1)
json.dump({"games_list": games}, open(sys.argv[3], "w"), indent=1)
print("capture games ok: 90 (from the published driver rows, sorted)")
PYEOF
if [ $? -ne 0 ]; then
  echo "ABORT: capture-games rebuild failed."
  exit 1
fi

RUN_RECORD_HASH=$(sha256sum "$ROOT/step0-probe-recovery-run.md" | awk '{print $1}')
SELF_HASH=$(sha256sum "$0" | awk '{print $1}')

# ---- 4. the influence step (the recovery's
# own invocation, paths adapted to the
# published tree)
"$PY" "$CODE_DIR/probe_influence.py" \
  --jobs "$REC/jobs_merged.jsonl" \
  --labels "$WORK/labels_merged.jsonl" \
  --capture-games "$WORK/capture_games.json" \
  --settings "$CODE_DIR/settings_probe.json" \
  --eval-jobs "$S0/eval_jobs.jsonl" \
  --evals "$S0/evals_all.jsonl.gz" \
  --eval-states "$S0/eval_states.jsonl" \
  --driver-rows "$S0/cap_s1_b1.jsonl" "$S0/cap_s2_b1.jsonl" \
  --report-json "$REC/probe_report.json" \
  --capalign-classes "$REC/capalign/capalign_classes.json" \
  --game 440261752 \
  --json-out "$REC/probe_influence.json" \
  > "$REC/probe_influence.txt" || {
  echo "ABORT: the influence step failed (probe_influence.py)."
  exit 1
}
echo "influence step done: probe_influence.txt + probe_influence.json in $REC"

# ---- 5. the manifest step (the recovery's
# manifest, same fields, over the published
# tree, plus the completion provenance)
REC_DIR="$REC" S0_DIR="$S0" ROOT_DIR="$ROOT" \
RAW_HASH="$RAW_HASH" ROWS="$ROWS" \
RUN_RECORD_HASH="$RUN_RECORD_HASH" \
SELF_HASH="$SELF_HASH" \
"$PY" - <<'PYEOF'
import hashlib, json, os
REC = os.environ["REC_DIR"]
S0 = os.environ["S0_DIR"]
ROOT = os.environ["ROOT_DIR"]

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

infl = json.load(open(os.path.join(REC, "probe_influence.json")))
recl = json.load(open(os.path.join(
    REC, "capalign", "capalign_reclassification.json")))
lread = json.load(open(os.path.join(REC, "label_read.json")))
supp_b = [json.loads(l)["snap"] for l in
          open(os.path.join(REC, "jobs_suppB.jsonl")) if l.strip()]

files = {}
for rel, base in [
        ("data/step0/jobs_all.jsonl", S0),
        ("data/step0/labels_all.jsonl.gz", S0),
        ("data/step0_recovery/jobs_supp.jsonl", REC),
        ("data/step0_recovery/labels_supp.jsonl", REC),
        ("data/step0_recovery/label_stats_supp.jsonl", REC),
        ("data/step0_recovery/labels_merged.jsonl.gz", REC),
        ("data/step0_recovery/label_read.json", REC),
        ("data/step0_recovery/probe_report.json", REC),
        ("data/step0_recovery/eval_completeness.json", REC),
        ("data/step0_recovery/probe_influence.json", REC),
        ("data/step0_recovery/probe_influence.txt", REC),
        ("data/step0_recovery/jobs_suppB.jsonl", REC),
        ("data/step0_recovery/labels_suppB.jsonl", REC),
        ("data/step0_recovery/label_stats_suppB.jsonl", REC),
        ("data/step0_recovery/jobs_merged.jsonl", REC),
        ("data/step0_recovery/capalign/capalign_states.jsonl", REC),
        ("data/step0_recovery/capalign/capalign_summary.json", REC),
        ("data/step0_recovery/capalign/capalign_classes.json", REC),
        ("data/step0_recovery/capalign/capalign_reclassification.json", REC),
        ("data/step0_recovery/capalign/supplementary_jobs_report.json", REC)]:
    files[rel] = sha(os.path.join(ROOT, rel))

manifest = {
  "supplementary_meas_seed": 970055001,
  "supplementary_jobs": [
    "540261752_t64", "540261752_t65", "540261752_t66",
    "540261752_t67", "540261752_t68", "540261752_t69",
    "540261752_t70", "540261752_t71", "540261752_t72",
    "540261752_t73"],
  "disclosure": ("Supplementary jobs (sec.12): (i) the jobs file these labels were computed from carries the recovered jobs' z as the strict-JSON 999.0 sentinel, not the true non-finite value -- the sentinel is file representation only; at analysis time the raw non-finite z is restored from jobs_all.jsonl (which the labeler never reads) before banding, diffing and weighting, so every reported number is computed from the true z. (ii) The capture driver rows and stat rows carry unpinned-code stamps because the capture ran under the pre-pin build; the labels and gains do not depend on driver code."),
  "eval_completeness": json.load(open(os.path.join(
      REC, "eval_completeness.json")))["missing_states"],
  "influence_hold_lines": infl["hold_lines"],
  "single_game_dependent": [
      k for k, v in infl["hold"].items() if v.get("hold")],
  "sec14": {
    "scoring": ("Cap-aligned scoring (sec.14): a finished teacher/prior world decided after turn 61 scores 0 (it is a horizon draw under the aligned rule); the cap-aligned read is registered and decides the recommendation; the as-run read is co-reported. Drop-out jobs (their game's outcome arrived after the turn-62 cap) are excluded from the cap-aligned read and counted."),
    "supplementary_meas_seed_b": 470055001,
    "supplementary_jobs_b": supp_b,
    "supplementary_jobs_b_count": len(supp_b),
    "dropped_jobs": recl["dropouts"],
    "dropped_jobs_count": recl["dropout_count"],
    "capaligned_excluded_jobs": lread["capaligned"]["excluded_jobs"],
    "disclosure": ("Sec.14 supplementary family B: job-side rows only (game, turn, selected candidates, priors) -- the family-B states' eval-side detail (candidate diagnostics and per-world eval rows) does not leave the box; the cap-aligned rescoring of those states was computed on the box by code/capalign_eval.py from the published data/step0/ eval rows. The round-9 engine files are read-only inputs to the cap alignment; rounds/round9/code/search_s2.php is byte-identical to its published form."),
  },
  "completion": {
    "produced_by": "rounds/round10/code/run_probe_completion.sh",
    "script_sha256": os.environ["SELF_HASH"],
    "probe_influence_sha256": "dc79bdaddb30980138c3c72b8321f4fbb7ed23675911c9b835caf7d896e96a9a",
    "reason": ("The influence and manifest steps of the 2026-10-29 recovery run never ran: the influence step died with NameError: name 'logo_by_lever' is not defined (probe_influence.py, LOGO loop) after the run had written its report, and the recovery script is single-shot. This manifest and probe_influence.{txt,json} were produced by the completion step (fix pass 6, package doc sec.15) from the run's published outputs, after the one-line repair; no eval, label or report row was recomputed."),
    "run_record": "rounds/round10/step0-probe-recovery-run.md",
    "run_record_sha256": os.environ["RUN_RECORD_HASH"],
    "labels_merged_raw_sha256": os.environ["RAW_HASH"],
    "labels_merged_rows": int(os.environ["ROWS"]),
    "games_list_source": ("The run's capture-games file (eval_jobs_report.json) was not published; the 90 capture game ids were rebuilt from the published driver rows (data/step0/cap_s1_b1.jsonl + cap_s2_b1.jsonl), sorted, as build_probe_eval_jobs.py wrote them. Every gain and interval in the influence read is invariant to the list's order (the cluster bootstrap sorts game ids internally)."),
    "files_note": ("The files map below covers the same artifacts as the recovery script's manifest step, keyed by their published paths under rounds/round10/; the two label artifacts the run's box held uncompressed are published gzipped (labels_all.jsonl.gz, labels_merged.jsonl.gz) and are hashed as published, with the labels_merged decompressed-content hash recorded above."),
  },
  "files": files,
}
with open(os.path.join(REC, "recovery_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("manifest written: recovery_manifest.json")
PYEOF
if [ $? -ne 0 ]; then
  echo "ABORT: the manifest step failed."
  exit 1
fi

echo "== completion done: the probe's registered read is complete =="
