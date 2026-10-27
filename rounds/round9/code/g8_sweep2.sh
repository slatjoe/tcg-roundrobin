#!/bin/bash
# g8_sweep2.sh - HARDENED G8 pre-launch sweep (round 9, Stage 3).
# Byte-derived from code/g8_sweep.sh with ONLY the guard line
# changed (plus this header). Why: the round-8 copy's bare
# '[p]lay_game' token matched the substring play_game inside
# unrelated command lines that merely MENTION a game file/path
# (play_game.php inside an ssh remote-command string, a log
# tail, an editor command) -- the vector that aborted Stage 2
# L3 attempt 1 (2026-10-27 04:32 EDT) while no game process
# existed. The hardened patterns require the executable token
# itself (play_game.php / paired_driver_gravy) so a bare
# mention no longer trips, while a real 'php play_game.php
# ...' or 'python3 .../paired_driver_gravy.py ...' command
# line still matches; bracket camouflage retained so the
# guard never matches its own text. Residual (fail-safe): any
# command line containing the literal play_game.php token --
# e.g. an editor open on the file -- still trips the guard.
#
# g8_sweep.sh - round-8 copy of the round-3 G8 stale SHMOP segment
# cleanup (rounds/round3/code/gate_ipcs_cleanup.sh, byte-identical
# below the header): the pre-launch sweep the round-7 ruling's
# L-run conditions require before any teacher work. Removes ONLY
# segments with nattch == 0 (no process attached) after verifying
# no game processes are running. Segments with nattch > 0 belong
# to live processes and are NEVER touched.
#
# Evidence: full `ipcs -m` listings before/after are written to
# files named by argv 1 (evidence prefix).
set -u
PREFIX=${1:-/tmp/gate_ipcs}
if pgrep -f '[p]lay_game\.php' >/dev/null || pgrep -f '[p]aired_driver_gravy' >/dev/null; then
  echo "ABORT: game processes are running; not cleaning." >&2
  exit 1
fi
ipcs -m > ${PREFIX}_before.txt
BEFORE=$(ipcs -m | awk '$1 ~ /^0x/ {n++} END {print n+0}')
STALE=$(ipcs -m | awk '$1 ~ /^0x/ && $6 == 0 {n++} END {print n+0}')
ATTACHED=$(ipcs -m | awk '$1 ~ /^0x/ && $6 > 0 {n++} END {print n+0}')
echo "segments before: $BEFORE (nattch=0: $STALE, attached: $ATTACHED)"
echo "kernel.shmmni: $(cat /proc/sys/kernel/shmmni)"
ipcs -m | awk '$1 ~ /^0x/ && $6 > 0 {print}' > ${PREFIX}_attached_kept.txt
ipcs -m | awk '$1 ~ /^0x/ && $6 == 0 {print $2}' > ${PREFIX}_stale_ids.txt
while read -r id; do
  [ -n "$id" ] && ipcrm -m "$id"
done < ${PREFIX}_stale_ids.txt
ipcs -m > ${PREFIX}_after.txt
AFTER=$(ipcs -m | awk '$1 ~ /^0x/ {n++} END {print n+0}')
echo "segments after: $AFTER"
ipcs -m | awk '$1 ~ /^0x/ && $6 > 0 {print}'
