#!/bin/bash
# FX7: horizon OFF-equivalence + ON mechanics on 3 real vaulted jobs.
# Build test only -- not the Stage 0 run.
set -u
FX=/tmp/r9s0_fx7
GT=/tmp/gravytree
PY=/home/joe/tcg/rl-env/bin/python
SIM=/home/joe/tcg/tcg-sim
CKPT=$SIM/rl_out/gravy_ppo_gravybc3/ckpt_v10.pt
PROD=$SIM/rl/search_server.py
DECK_REL=decks/nats2026_eriksen_gravy_60.txt
cd "$FX"

echo "== prep: select 3 jobs (first B, first P, first ARS; distinct games)"
$PY - <<'PYEOF'
import json, os
jobs = [json.loads(l) for l in open(
    "/home/joe/tcg/registry-vault/jobs_all_gravy_fleet_l3.jsonl")
    if l.strip()]
sel, games = [], set()
for want in ("B", "P", "ARS"):
    for j in jobs:
        if j["branch"] == want and str(j["game"]) not in games:
            sel.append(j); games.add(str(j["game"])); break
assert len(sel) == 3, sel
for name, stamp in (("A", None), ("Boff", 0), ("Bon", 62)):
    for p in (1, 2):
        with open(f"/tmp/r9s0_fx7/jobs{name}_p{p}.jsonl", "w") as f:
            for j in sel:
                if int(j["player"]) != p:
                    continue
                c = dict(j)
                c["snap_dir"] = "/tmp/ggate/" + j["snap_dir"]
                assert os.path.isdir(c["snap_dir"]), c["snap_dir"]
                if stamp is not None:
                    c["horizon"] = stamp
                f.write(json.dumps(c) + "\n")
for j in sel:
    print("selected:", j["snap"], "game", j["game"], "player",
          j["player"], "branch", j["branch"])
PYEOF

echo "== trees"
rm -rf treeA treeB
cp -r "$GT" treeA && cp -r "$GT" treeB || exit 1
cp stage/search_horizon.php treeB/search.php
cp stage/r9_label_main.php treeB/
cp stage/meas_label_main.php treeA/
sha256sum treeA/search.php treeB/search.php treeA/meas_label_main.php \
  treeB/r9_label_main.php

echo "== servers"
ipcs -m | grep -c '^0x' || true
for seat in 1 2; do
  TCG_POLICY_SOCK="$FX/prod_s${seat}.sock" TCG_LEARNER_SEAT=$seat \
    SEARCH_MODEL="$CKPT" TCG_OPP_MIX="heuristic:1.0" \
    setsid nohup $PY "$PROD" > "$FX/prod_s${seat}.log" 2>&1 < /dev/null &
done
SRV_PIDS=$(jobs -p)
for seat in 1 2; do
  for i in $(seq 1 60); do
    grep -q 'search model loaded' "$FX/prod_s${seat}.log" 2>/dev/null && break
    sleep 1
  done
  grep 'search model loaded' "$FX/prod_s${seat}.log" || exit 1
done

run_group() { # tree driver jobsfile outfile horizon_env player
  local tree=$1 driver=$2 jf=$3 of=$4 hz=$5 p=$6
  : > "$of"
  (cd "$tree" && MEAS_JOBS="$jf" MEAS_OUT="$of" MEAS_SEED=855001 \
     LABEL_W=50 LABEL_HORIZON="$hz" TCG_POLICY_SOCK="$FX/prod_s$p.sock" \
     php "$driver" "$tree/$DECK_REL" "$tree/$DECK_REL" \
       --policy-search --games 1 > "$of.err" 2>&1)
  echo "run $driver hz=$hz player=$p rc=$? rows=$(grep -c . "$of" || true)"
}

echo "== run A (pristine tree + pristine driver)"
for p in 1 2; do
  run_group "$FX/treeA" meas_label_main.php "$FX/jobsA_p$p.jsonl" \
    "$FX/labelsA_p$p.jsonl" off $p
done
echo "== run B-off (horizon tree + r9 driver, pin off)"
for p in 1 2; do
  run_group "$FX/treeB" r9_label_main.php "$FX/jobsBoff_p$p.jsonl" \
    "$FX/labelsBoff_p$p.jsonl" off $p
done
echo "== run B-on (horizon tree + r9 driver, pin 62)"
for p in 1 2; do
  run_group "$FX/treeB" r9_label_main.php "$FX/jobsBon_p$p.jsonl" \
    "$FX/labelsBon_p$p.jsonl" 62 $p
done
echo "== negative: pin 62 against jobs stamped 0 (must abort, exit 2)"
(cd treeB && MEAS_JOBS="$FX/jobsBoff_p1.jsonl" \
   MEAS_OUT="$FX/labelsNeg.jsonl" MEAS_SEED=855001 LABEL_W=50 \
   LABEL_HORIZON=62 TCG_POLICY_SOCK="$FX/prod_s1.sock" \
   php r9_label_main.php "$FX/treeB/$DECK_REL" "$FX/treeB/$DECK_REL" \
     --policy-search --games 1 > "$FX/neg.err" 2>&1)
echo "negative rc=$? (want 2)"; cat "$FX/neg.err"

cat labelsA_p1.jsonl labelsA_p2.jsonl > labelsA.jsonl
cat labelsBoff_p1.jsonl labelsBoff_p2.jsonl > labelsBoff.jsonl
cat labelsBon_p1.jsonl labelsBon_p2.jsonl > labelsBon.jsonl

echo "== compare"
$PY - <<'PYEOF'
import json
def load(p):
    rows = [json.loads(l) for l in open(p) if l.strip()]
    return {(r["snap"], int(r["cand"]), int(r["world"])):
            json.dumps(r["result"], sort_keys=True) for r in rows}, rows
A, Arows = load("/tmp/r9s0_fx7/labelsA.jsonl")
B, Brows = load("/tmp/r9s0_fx7/labelsBoff.jsonl")
H, Hrows = load("/tmp/r9s0_fx7/labelsBon.jsonl")
print("rows A / B-off / B-on:", len(Arows), len(Brows), len(Hrows))
mism = [k for k in A if B.get(k) != A[k]]
extra = [k for k in B if k not in A]
print("FX7 OFF-equivalence: mismatches=%d extra=%d -> %s"
      % (len(mism), len(extra),
         "IDENTICAL" if not mism and not extra and len(A) == len(B)
         else "DIFFERS"))
for k in mism[:5]:
    print("  mismatch", k, "A:", A[k][:160], "B:", B.get(k, "")[:160])
def stats(rows, tag):
    fin = sum(1 for r in rows if isinstance(r.get("result"), dict)
              and "error" not in r["result"]
              and int(r["result"].get("finished") or 0) == 1)
    unf = sum(1 for r in rows if isinstance(r.get("result"), dict)
              and "error" not in r["result"]
              and int(r["result"].get("finished") or 0) == 0)
    err = len(rows) - fin - unf
    print("%s: finished %d unfinished %d error %d" % (tag, fin, unf, err))
    return fin, unf, err
fa = stats(Arows, "A    ")
fb = stats(Brows, "B-off")
fh = stats(Hrows, "B-on ")
hz_rows = [r for r in Hrows if isinstance(r.get("result"), dict)
           and int(r["result"].get("horizon") or 0) == 1]
bad = [r for r in hz_rows if int(r["result"].get("finished") or 0) != 1
       or float(r["result"].get("outcome")) != 0.0]
stamped = all(int(r.get("horizon", -1)) == 62 for r in Hrows)
print("FX7 ON mechanics: horizon-marked worlds=%d; marked-but-not-"
      "draw-finished=%d; all rows stamped 62: %s"
      % (len(hz_rows), len(bad), stamped))
print("FX7 finished share ON >= OFF: %s (%d vs %d finished)"
      % (fh[0] >= fb[0], fh[0], fb[0]))
turns = sorted(int(r["result"]["turns"]) for r in hz_rows
               if "turns" in r["result"])
if turns:
    print("horizon-marked worlds' exit turns: min %d max %d"
          % (turns[0], turns[-1]))
PYEOF

kill $SRV_PIDS 2>/dev/null
sleep 2
echo "shm segments after: $(ipcs -m | grep -c '^0x' || true)"
echo "FX7 DONE"
