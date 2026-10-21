#!/usr/bin/env python3
"""patch_trainer_launch.py — round-7 stage 3: build the Gravy PPO
launch copy of rl/trainer_v4.py.

The pristine trainer (sha256
8fd52d829acee231b5f066adba879178593de3ffc1a689ca224948186b6a837f)
cannot express the ratified Gravy configuration through its CLI:

  * its spot-gate deck is a module constant (DECK_FAI, :259, used by
    run_spot_gate at :273-274) with no CLI override — unpatched, the
    Gravy policy's spot gates would play the FAI deck;
  * its canonical-suite gate has no off switch (Gate loads the suite
    file unconditionally; acceptance at `kl_cum <= budget and
    suite_fine`). Flag 2 (ratified) removes that gate.

This patch makes exactly those two changes and nothing else. Every
replacement is anchor-asserted (each anchor must occur exactly once);
the input file's sha256 is asserted before patching; the output's
sha256 and the full unified diff are printed for the build record.

Changes:
  1. Gate.__init__: suite_path None -> empty suite. suite_score on
     zero positions returns (0, 0, {}) and suite_ok against a (0,0,{})
     baseline is True, so acceptance reduces to the KL budget alone.
  2. main(): --suite none maps to suite_path None (with a comment).
  3. DECK_FAI -> DECK_SPOT, repointed at the Gravy deck, uses updated.

Usage:
  patch_trainer_launch.py <trainer_v4.py> <out.py>
"""
import difflib
import hashlib
import sys

EXPECTED_SHA256 = ("8fd52d829acee231b5f066adba879178593de3ffc1a689ca"
                   "224948186b6a837f")

REPLACEMENTS = [
    (
        "        suite = [json.loads(l) for l in open(suite_path)]",
        "        suite = ([] if suite_path is None else\n"
        "                 [json.loads(l) for l in open(suite_path)])",
    ),
    (
        "    gate = Gate(args.probe, args.suite, vocab, device)",
        "    # ROUND-7 (Flag 2, ratified): --suite none disables the\n"
        "    # canonical-suite gate. KL budget, spot gates and the\n"
        "    # heartbeat are unchanged.\n"
        "    gate = Gate(args.probe,\n"
        "                None if args.suite == \"none\" else args.suite,\n"
        "                vocab, device)",
    ),
    (
        'DECK_FAI = os.path.join(SIM_ROOT, "decks", '
        '"nats2026_ashlyn_fai_60.txt")',
        "# ROUND-7: spot-gate mirror deck repointed Fai -> Gravy Bones.\n"
        'DECK_SPOT = os.path.join(SIM_ROOT, "decks", '
        '"nats2026_eriksen_gravy_60.txt")',
    ),
    ('"--deck-a", DECK_FAI,', '"--deck-a", DECK_SPOT,'),
    ('"--deck-b", DECK_FAI,', '"--deck-b", DECK_SPOT,'),
]


def sha256_of_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src_path, out_path = sys.argv[1], sys.argv[2]
    with open(src_path, "rb") as f:
        raw = f.read()
    digest = sha256_of_bytes(raw)
    if digest != EXPECTED_SHA256:
        print(f"FAIL: {src_path} sha256 {digest} != expected "
              f"{EXPECTED_SHA256}; refusing to patch an unreviewed base")
        return 1
    text = raw.decode("utf-8")
    out = text
    for old, new in REPLACEMENTS:
        n = out.count(old)
        if n != 1:
            print(f"FAIL: anchor occurs {n} times (want exactly 1): "
                  f"{old[:70]!r}")
            return 1
        out = out.replace(old, new)
    with open(out_path, "w") as f:
        f.write(out)
    print(f"patched: {src_path} sha256 {digest}")
    print(f"     ->: {out_path} sha256 {sha256_of_bytes(out.encode())}")
    diff = difflib.unified_diff(
        text.splitlines(keepends=True), out.splitlines(keepends=True),
        fromfile="trainer_v4.py (pristine)", tofile="trainer_v4.py (round-7 launch copy)")
    sys.stdout.writelines(diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
