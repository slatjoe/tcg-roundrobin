#!/bin/bash
# G8 stale SHMOP segment cleanup (round-3 gate package, disclosed
# build step). Removes ONLY segments with nattch == 0 (no process
# attached) after verifying no game processes are running. The
# engine's segments are keyed by game id; a segment with no
# attached process belongs to a finished or killed game whose
# end-of-game DeleteCache never ran (KEEP_GAME games, rollout
# children, killed fleets). Segments with nattch > 0 belong to
# live processes and are NEVER touched.
#
# Evidence: full `ipcs -m` listings before/after are written next
# to this script's working dir (argv 1 = evidence prefix).
set -u
PREFIX=${1:-/tmp/gate_ipcs}
if pgrep -f '[p]lay_game' >/dev/null || pgrep -f '[p]aired_driver' >/dev/null; then
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
