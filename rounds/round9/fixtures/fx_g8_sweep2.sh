#!/bin/bash
# fx_g8_sweep2 - the hardened G8 guard (code/g8_sweep2.sh)
# against REAL pgrep semantics (no pgrep shim: the self-match
# and substring behavior under test IS pgrep's). A stub ipcs
# on PATH emits a canned segment listing (3 segments:
# id 424242 nattch=0 stale, ids 424243/424244 attached) and
# a stub ipcrm logs its args. Process-table conditions are
# created by the fixture itself with argv[0] forgery
# (exec -a), and every spawned process is killed by pid.
#   (a) CLEAN: no strays -> sweep proceeds; ipcrm called
#       with the stale id only.
#   (b) MENTION: a cmdline containing the bare token
#       play_game (no .php) -> the OLD guard (real
#       g8_sweep.sh) ABORTS, the NEW guard PROCEEDS. This is
#       the Stage 2 L3 attempt-1 vector class.
#   (c) MENTION-PHP: a cmdline containing play_game.php
#       inside a longer string -> BOTH guards abort (the
#       documented residual: the guard fails safe).
#   (d) REAL: a genuine play_game.php process -> the NEW
#       guard ABORTS. (b) vs (d) are the discriminating pair.
#   (e) DIFF: diff g8_sweep.sh g8_sweep2.sh touches ONLY the
#       header comment + the guard line.
set -u
FX="$(cd "$(dirname "$0")" && pwd)"
CODE="$FX/../code"
WORK="$(mktemp -d)"
FAIL=0
SPAWNED=""
cleanup() {
  for pid in $SPAWNED; do kill "$pid" 2>/dev/null; done
  rm -rf "$WORK"
}
trap cleanup EXIT
note() { echo "$1"; }
bad() { echo "FAIL $1"; FAIL=1; }

mkdir -p "$WORK/bin"
cat > "$WORK/bin/ipcs" <<'EOF'
#!/bin/bash
cat <<'LIST'
Shared Memory Segments --------
key        shmid      owner      perms      bytes      nattch     status
0x00000001 424242     joe        600        1024       0
0x00000002 424243     joe        600        1024       2
0x00000003 424244     joe        600        1024       1
LIST
EOF
cat > "$WORK/bin/ipcrm" <<'EOF'
#!/bin/bash
echo "ipcrm $@" >> "$FX_IPCRM_LOG"
EOF
chmod +x "$WORK/bin/ipcs" "$WORK/bin/ipcrm"
export FX_IPCRM_LOG="$WORK/ipcrm.log"

run_sweep() { # script prefix -> exit code
  : > "$FX_IPCRM_LOG"
  PATH="$WORK/bin:$PATH" bash "$1" "$WORK/$2" > "$WORK/$2.out" 2>&1
  return $?
}

spawn_forged() { # argv0-string
  bash -c 'exec -a "$1" sleep 30' _ "$1" &
  SPAWNED="$SPAWNED $!"
  sleep 0.3
}
kill_spawned() {
  for pid in $SPAWNED; do kill "$pid" 2>/dev/null; done
  SPAWNED=""
  sleep 0.3
}

# (a) CLEAN
if run_sweep "$CODE/g8_sweep2.sh" clean; then
  if grep -q "ipcrm -m 424242" "$FX_IPCRM_LOG" \
     && ! grep -q "424243\|424244" "$FX_IPCRM_LOG"; then
    note "PASS (a) CLEAN: sweep proceeds, ipcrm called with stale id 424242 only"
  else
    bad "(a) CLEAN: ipcrm calls wrong: $(cat "$FX_IPCRM_LOG")"
  fi
else
  bad "(a) CLEAN: sweep should have proceeded"; cat "$WORK/clean.out"
fi

# (b) MENTION: bare play_game token, no .php
spawn_forged "tail -f /tmp/play_game_notes.log"
if run_sweep "$CODE/g8_sweep.sh" mention_old; then
  bad "(b) MENTION: OLD guard should have aborted on the bare token"
else
  note "PASS (b) MENTION: OLD guard aborts on a bare play_game mention (the attempt-1 vector)"
fi
if run_sweep "$CODE/g8_sweep2.sh" mention_new; then
  note "PASS (b) MENTION: NEW guard proceeds past a bare play_game mention"
else
  bad "(b) MENTION: NEW guard should have proceeded"; cat "$WORK/mention_new.out"
fi
kill_spawned

# (c) MENTION-PHP: play_game.php inside a longer string
spawn_forged "vim /tmp/play_game.php.bak"
if run_sweep "$CODE/g8_sweep.sh" mph_old; then
  bad "(c) MENTION-PHP: OLD guard should have aborted"
else
  note "PASS (c) MENTION-PHP: OLD guard aborts"
fi
if run_sweep "$CODE/g8_sweep2.sh" mph_new; then
  bad "(c) MENTION-PHP: NEW guard should have aborted (fail-safe residual)"
else
  note "PASS (c) MENTION-PHP: NEW guard aborts (documented fail-safe residual)"
fi
kill_spawned

# (d) REAL: a genuine play_game.php process
mkdir -p "$WORK/real"
printf '#!/bin/bash\nsleep 30\n' > "$WORK/real/play_game.php"
bash "$WORK/real/play_game.php" &
SPAWNED="$SPAWNED $!"
sleep 0.3
if run_sweep "$CODE/g8_sweep2.sh" real_new; then
  bad "(d) REAL: NEW guard should have aborted on a real play_game.php process"
else
  note "PASS (d) REAL: NEW guard aborts on a real play_game.php process"
fi
kill_spawned

# (d2) REAL driver: a paired_driver_gravy command line
spawn_forged "python3 /home/joe/tcg/round9_code/paired_driver_gravy.py"
if run_sweep "$CODE/g8_sweep2.sh" drv_new; then
  bad "(d2) DRIVER: NEW guard should have aborted on paired_driver_gravy"
else
  note "PASS (d2) DRIVER: NEW guard aborts on a paired_driver_gravy command line"
fi
kill_spawned

# (e) DIFF confinement
changed=$(diff "$CODE/g8_sweep.sh" "$CODE/g8_sweep2.sh" | grep '^[<>]' | grep -v '^[<>] #' || true)
nchanged=$(printf '%s\n' "$changed" | grep -c .)
if [ "$nchanged" = "2" ] \
   && printf '%s\n' "$changed" | grep -qF "[p]lay_game'" \
   && printf '%s\n' "$changed" | grep -qF "[p]lay_game\\.php" \
   && printf '%s\n' "$changed" | grep -qF "[p]aired_driver_gravy"; then
  note "PASS (e) DIFF: only the guard line differs outside comments (2 changed lines)"
else
  bad "(e) DIFF: non-comment changed lines = $nchanged (want 2)"; printf '%s\n' "$changed"
fi

echo "FX-G8-SWEEP2: $([ $FAIL = 0 ] && echo ALL PASS || echo FAILURES)"
exit $FAIL
