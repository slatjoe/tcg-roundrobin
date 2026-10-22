#!/usr/bin/env python3
# shm_selector.py - round-7 extended probe: the (C) kernel-attribution
# selector of claude-reply-ad1d7c6 sec.2(C), in DRY-RUN form.
#
# A shared-memory segment is SELECTED (would be deleted by the live
# form) iff ALL of these hold:
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
# DRY RUN: this script DELETES NOTHING. It only logs, every pass, the
# segments it would select, with the fields the (C) tests need:
# shmid, key, cpid, lpid, nattch, create time, last attach time,
# last change time (from ipcs -m / -p / -t). The log is the evidence
# for claude-reply-ad1d7c6 sec.2 (i), (iii) and (iv).
#
# Usage: shm_selector.py --log FILE --start-file FILE --games-dir DIR
#          [--interval SECONDS] [--stop-file FILE]
# start-file: one shmid per line (the run-start listing's shmids).
# The loop runs one pass immediately, then one per interval, until
# the stop file exists.
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
    for shmid, s in sorted(segs.items()):
        if s.get("owner") != "joe":
            continue
        if s.get("nattch") != 0:
            continue
        cpid = s.get("cpid", 0)
        lpid = s.get("lpid", 0)
        if cpid in live or lpid in live:
            continue
        if s.get("key") in gkeys:
            continue
        if shmid in start_shmids:
            continue
        chosen.append((shmid, s))
    return chosen


def fmt_time(raw):
    return " ".join(raw.split()) if raw else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--start-file", required=True)
    ap.add_argument("--games-dir", required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--stop-file", required=True)
    a = ap.parse_args()

    start_shmids = set()
    with open(a.start_file) as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                start_shmids.add(int(line))

    log = open(a.log, "a", buffering=1)
    log.write("# selector start %s start_shmids=%d games_dir=%s\n"
              % (datetime.datetime.now().isoformat(), len(start_shmids),
                 a.games_dir))
    pass_no = 0
    while True:
        pass_no += 1
        try:
            segs = parse_segments()
            chosen = select(segs, start_shmids, a.games_dir)
        except Exception as e:  # keep logging; a pass error is evidence too
            log.write("PASS %d %s ERROR %r\n"
                      % (pass_no, datetime.datetime.now().isoformat(), e))
            chosen = []
            segs = {}
        log.write("PASS %d %s total=%d selected=%d\n"
                  % (pass_no, datetime.datetime.now().isoformat(),
                     len(segs), len(chosen)))
        for shmid, s in chosen:
            log.write(
                "SELECT shmid=%d key=%d cpid=%s lpid=%s nattch=%s "
                "ctime=\"%s\" atime=\"%s\" dtime=\"%s\"\n"
                % (shmid, s["key"], s.get("cpid"), s.get("lpid"),
                   s.get("nattch"), fmt_time(s.get("ctime")),
                   fmt_time(s.get("atime")), fmt_time(s.get("dtime"))))
        if os.path.exists(a.stop_file):
            log.write("# selector stop after pass %d %s\n"
                      % (pass_no, datetime.datetime.now().isoformat()))
            break
        time.sleep(a.interval)
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
