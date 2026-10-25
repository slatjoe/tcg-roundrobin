#!/bin/bash
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
