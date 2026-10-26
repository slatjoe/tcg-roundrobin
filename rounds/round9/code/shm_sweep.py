#!/usr/bin/env python3
# shm_sweep.py - round-7 (C) kernel-attribution containment,
# PRODUCTION form. Derived from code/shm_selector.py (sha256
# 23f15ea7..., the dry-run selector as run in the extended probe,
# extended-probe.md sec.1/4) with the selection code carried over
# unchanged; this file adds the deletion pass and the mode flag.
# The dry-run file stays untouched as the probe's artifact.
#
# Accepted basis: claude-reply-ad1d7c6 sec.2(C) (kernel attribution
# preferred) and extended-probe.md sec.4 - the selector's tests
# (ii) dry run, (iii) false positives (zero in 584 shmids / 9,289
# observations) and (iv) coverage (exact: 584 selected + 1 rule-3
# exclusion = the wave's 585 residue) all hold, and (i) cpid/lpid
# population is shown empirically (PHP 8.5.4 shmop children).
#
# A shared-memory segment is SELECTED iff ALL of these hold:
#   (1) owner is joe AND nattch == 0
#   (2) cpid is not a live pid AND lpid is not a live pid
#       (ipcs -m -p: creator pid / last attach-detach pid)
#   (3) its key is not in {n, n + 1000000} for any directory n
#       currently present under the tree's vendor/talishar/Games/
#       (n = game id; n + 1000000 is its GamestateID segment key,
#        n itself the lobby segment key)
#   (4) its shmid was NOT present in the run-start listing
#       (i.e. it was created after the run began)
#
# MODES:
#   (default)  LIVE: each selected segment is deleted with
#              `ipcrm -m <shmid>` in the same pass that selected
#              it; every deletion's result is logged (a failed
#              ipcrm is reported, never silently passed).
#   --dry-run  the probe behavior exactly: same selection, same
#              PASS/SELECT logging, no deletion, so the same
#              binary serves the (C) tests and production.
#
# SAFETY - the selector can only over-keep, never wrongly delete:
#   * Dead-pid rule: a live game's processes are alive, so its
#     segments fail rule (2) and are kept; a live game is also
#     protected a second time by rule (3), its directory.
#   * Run-start rule (4): anything that existed before the run is
#     never selected, whatever its state.
#   * Rule (3) also covers a short-lived setup process that
#     creates a segment a live game later opens by key: the
#     game's directory exists from the game's start.
#   * Selection and deletion happen in one pass from one ipcs
#     snapshot; every borderline case resolves to KEEP.
#   * The one operational hazard is PID REUSE: if a dead child's
#     pid has been recycled by an unrelated live process, the
#     segment looks alive under rule (2) and is KEPT. That is
#     the safe direction - the leak grows by that segment, the
#     run is never harmed. (The probe's coverage test bounds the
#     effect: its selected set accounted for the residue exactly.)
#
# INTERFACE: self-looping, one pass immediately then one per
# --interval seconds, until --stop-file exists. This form is
# chosen because the runners (run_gravy_gate.sh,
# run_gravy_pregate.sh) already manage long-lived helpers with
# exactly this lifecycle - the tree's search servers are started
# in the background, tracked by pid, and reaped at the end of the
# run under the runner's trap - so the sweeper is started the
# same way after the run-start listing is saved and stopped the
# same way after the last game. A per-pass external invocation
# (cron-style) would have to re-derive the rule-(4) run-start
# set on every call and could not guarantee the pass cadence
# against the run's own chunk boundaries.
#
# Usage: shm_sweep.py --log FILE --start-file FILE --games-dir DIR
#          [--interval SECONDS] [--stop-file FILE] [--dry-run]
# start-file: one shmid per line (the run-start listing's shmids).
import argparse
import datetime
import os
import re
import subprocess
import sys
import time

TIME_RE = re.compile(
    r"(Not set|(?:[A-Z][a-z]{2} )?[A-Z][a-z]{2} +\d{1,2} "
    r"\d{2}:\d{2}:\d{2}(?: \d{4})?)")


def run_ipcs(args):
    out = subprocess.run(["ipcs", "-m"] + args, capture_output=True,
                         text=True, check=True).stdout
    return out


def parse_segments():
    """Merge ipcs -m, ipcs -m -p, ipcs -m -t into {shmid: fields}."""
    segs = {}
    for line in run_ipcs([]).splitlines():
        parts = line.split()
        if len(parts) >= 6 and parts[0].startswith("0x"):
            try:
                key = int(parts[0], 16)
                shmid = int(parts[1])
                nattch = int(parts[5])
            except ValueError:
                continue
            segs[shmid] = {"key": key, "owner": parts[2],
                           "nattch": nattch}
    for line in run_ipcs(["-p"]).splitlines():
        # rows: "shmid cpid lpid" or, on newer util-linux,
        # "shmid owner cpid lpid" - cpid/lpid are the last two fields.
        parts = line.split()
        if len(parts) in (3, 4) and parts[0].isdigit() \
                and parts[-1].isdigit() and parts[-2].isdigit():
            shmid = int(parts[0])
            if shmid in segs:
                segs[shmid]["cpid"] = int(parts[-2])
                segs[shmid]["lpid"] = int(parts[-1])
    for line in run_ipcs(["-t"]).splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            times = TIME_RE.findall(parts[1])
            if len(times) == 3:
                shmid = int(parts[0])
                if shmid in segs:
                    segs[shmid]["atime"] = times[0]
                    segs[shmid]["dtime"] = times[1]
                    segs[shmid]["ctime"] = times[2]
    return segs


def live_pids():
    return {int(p) for p in os.listdir("/proc") if p.isdigit()}


def game_keys(games_dir):
    keys = set()
    try:
        names = os.listdir(games_dir)
    except OSError:
        return keys
    for name in names:
        if name.isdigit():
            n = int(name)
            keys.add(n)
            keys.add(n + 1000000)
    return keys


def select(segs, start_shmids, games_dir):
    live = live_pids()
    gkeys = game_keys(games_dir)
    chosen = []
    unattributed = 0
    for shmid, s in sorted(segs.items()):
        cpid = s.get("cpid")
        lpid = s.get("lpid")
        if cpid is None or lpid is None or cpid <= 0 or lpid <= 0:
            # Fail-safe (claude-reply-ef34219 sec.2): a segment with
            # no usable pid attribution - its -p row withheld or
            # malformed - is never selected. If the -p parse ever
            # regresses, the sweep keeps everything and the leak
            # grows; it never deletes unattributed memory. Counted
            # per pass so the regression is visible in the log.
            unattributed += 1
            continue
        if s.get("owner") != "joe":
            continue
        if s.get("nattch") != 0:
            continue
        if cpid in live or lpid in live:
            continue
        if s.get("key") in gkeys:
            continue
        if shmid in start_shmids:
            continue
        chosen.append((shmid, s))
    return chosen, unattributed


def fmt_time(raw):
    return " ".join(raw.split()) if raw else "?"


def delete_segment(shmid):
    """ipcrm -m one segment. Returns (ok, detail) and never raises:
    a failed deletion is a log line, not a crashed sweep."""
    try:
        r = subprocess.run(["ipcrm", "-m", str(shmid)],
                           capture_output=True, text=True)
    except Exception as e:
        return False, "exception %r" % (e,)
    if r.returncode == 0:
        return True, "ok"
    err = " ".join((r.stderr or r.stdout or "").split())
    return False, "rc=%d %s" % (r.returncode, err)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--start-file", required=True)
    ap.add_argument("--games-dir", required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--stop-file", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="the probe behavior: select and log only, "
                         "delete nothing")
    a = ap.parse_args()

    start_shmids = set()
    with open(a.start_file) as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                start_shmids.add(int(line))

    mode = "DRY-RUN" if a.dry_run else "LIVE"
    log = open(a.log, "a", buffering=1)
    log.write("# shm_sweep start %s mode=%s start_shmids=%d "
              "games_dir=%s\n"
              % (datetime.datetime.now().isoformat(), mode,
                 len(start_shmids), a.games_dir))
    pass_no = 0
    while True:
        pass_no += 1
        unattributed = 0
        try:
            segs = parse_segments()
            chosen, unattributed = select(segs, start_shmids,
                                            a.games_dir)
        except Exception as e:  # keep logging; a pass error is evidence too
            log.write("PASS %d %s ERROR %r\n"
                      % (pass_no, datetime.datetime.now().isoformat(), e))
            chosen = []
            segs = {}
        log.write("PASS %d %s total=%d selected=%d unattributed=%d\n"
                  % (pass_no, datetime.datetime.now().isoformat(),
                     len(segs), len(chosen), unattributed))
        deleted = 0
        failed = 0
        for shmid, s in chosen:
            log.write(
                "SELECT shmid=%d key=%d cpid=%s lpid=%s nattch=%s "
                "ctime=\"%s\" atime=\"%s\" dtime=\"%s\"\n"
                % (shmid, s["key"], s.get("cpid"), s.get("lpid"),
                   s.get("nattch"), fmt_time(s.get("ctime")),
                   fmt_time(s.get("atime")), fmt_time(s.get("dtime"))))
            if not a.dry_run:
                ok, detail = delete_segment(shmid)
                if ok:
                    deleted += 1
                else:
                    failed += 1
                log.write("DELETE shmid=%d key=%d -> %s\n"
                          % (shmid, s["key"],
                             "OK" if ok else "FAILED " + detail))
        if not a.dry_run:
            log.write("DELETED pass=%d count=%d failed=%d\n"
                      % (pass_no, deleted, failed))
        if os.path.exists(a.stop_file):
            log.write("# shm_sweep stop after pass %d %s\n"
                      % (pass_no, datetime.datetime.now().isoformat()))
            break
        time.sleep(a.interval)
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
