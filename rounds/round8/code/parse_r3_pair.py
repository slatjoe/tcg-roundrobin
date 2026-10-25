#!/usr/bin/env python3
# parse_r3_pair.py - round-7 pre-gate: the strict reader for
# r3_pair.py's pairing table, per claude-reply-ad1d7c6 sec.5.1.
#
# The registered pre-gate criterion (followup-k1-k3-fix sec.3) is
# read from r3_pair.py's markdown table - never by counting
# verdict strings with grep, which cannot see the criterion's
# other columns: a pair whose outcome-equal is False, or whose
# within-row hits are nonzero, still prints IDENTICAL in its
# verdict cell if the verdict fold passed, and grep -c would
# count it. This parser checks every column the criterion names.
#
# Expected table (r3_pair.py main()):
#   | seed | pair | verdict | within-row hits | seq | outcome
#     equal | modes ok | seat ok | assert ok |
#   |---|---|---|---|---|---|---|---|---|
#   | 8501 | raw vs raw | IDENTICAL | 0 | None | True | True |
#     True | True |
#
# A read PASSES iff:
#   * a table with exactly those 9 header columns is present;
#   * it has exactly --expect-rows data rows (default 10);
#   * every data row has: seed an integer, verdict IDENTICAL,
#     within-row hits 0, outcome equal True, modes ok True,
#     seat ok True, assert ok True.
# Anything else - a missing/short table, a MISSING_GAME or
# INVALID_* row, a False in any checked column - FAILS.
#
# Usage: parse_r3_pair.py [--expect-rows N] FILE   ("-" = stdin)
# Exit 0 and a PARSE-PASS line on success; exit 1 with one
# PARSE-FAIL line per defect otherwise. Used by
# run_gravy_pregate.sh for the determinism read (a FAIL stops
# the pre-gate) and by the launch record for the ghost read
# (claude-reply-ad1d7c6 sec.5.1: the same parser for both).
import argparse
import sys

HEADER = ["seed", "pair", "verdict", "within-row hits", "seq",
          "outcome equal", "modes ok", "seat ok", "assert ok"]


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_separator(row):
    return all(c and set(c) <= set("-: ") for c in row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-rows", type=int, default=10)
    ap.add_argument("file")
    a = ap.parse_args()

    text = sys.stdin.read() if a.file == "-" \
        else open(a.file).read()
    lines = [ln for ln in text.splitlines() if ln.strip().startswith("|")]

    header_at = None
    for i, ln in enumerate(lines):
        if cells(ln) == HEADER:
            header_at = i
            break
    if header_at is None:
        print("PARSE-FAIL: no r3_pair table with the expected "
              "9-column header found")
        return 1

    rows = []
    for ln in lines[header_at + 1:]:
        row = cells(ln)
        if is_separator(row):
            continue
        rows.append(row)

    defects = []
    if len(rows) != a.expect_rows:
        defects.append("expected %d data rows, found %d"
                       % (a.expect_rows, len(rows)))
    for row in rows:
        if len(row) != len(HEADER):
            defects.append("row with %d cells (want %d): %s"
                           % (len(row), len(HEADER), " | ".join(row)))
            continue
        seed, _pair, verdict, hits, _seq, eq, mok, sok, aok = row
        where = "seed %s" % seed
        if not seed.isdigit():
            defects.append("%s: seed cell is not an integer" % where)
        if verdict != "IDENTICAL":
            defects.append("%s: verdict %s (want IDENTICAL)"
                           % (where, verdict))
        if hits != "0":
            defects.append("%s: within-row hits %s (want 0)"
                           % (where, hits))
        for label, val in (("outcome equal", eq), ("modes ok", mok),
                           ("seat ok", sok), ("assert ok", aok)):
            if val != "True":
                defects.append("%s: %s %s (want True)"
                               % (where, label, val))
    if defects:
        for d in defects:
            print("PARSE-FAIL: " + d)
        return 1
    print("PARSE-PASS: %d rows, every row IDENTICAL with "
          "within-row hits 0, outcome equal True, modes ok True, "
          "seat ok True, assert ok True" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
