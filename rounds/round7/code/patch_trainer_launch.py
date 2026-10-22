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

STAGE-3 INSTRUMENT ALIGNMENT (claude-reply-2e5e4c5 sec.3; added by
the alignment registration, rounds/round7/stage3-alignment.md):
  4. run_spot_gate: --max-turns 60 -> 87 (parameter; trigger 62),
     TCG_MAX_DECISIONS=3000 set explicitly in the eval subprocess
     environment, capped_games accumulated from the eval summaries,
     and the read draw-scored: (wins + 0.5*capped) / played against
     the unchanged 0.30 floor.
  5. finalize_games heartbeat tally: a capped game contributes 0.5
     (a draw) to the heartbeat window and the recent-results tally
     instead of 0.0. Episode rewards are NOT changed (they receive
     `capped` separately in assign_episode_rewards).

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
    # --- stage-3 instrument alignment (changes 4-5 in the docstring)
    (
        '"--learner-deck", deck, "--max-turns", "60",',
        '"--learner-deck", deck, "--max-turns", "87",',
    ),
    (
        "            r = subprocess.run(cmd, capture_output=True, text=True,\n"
        "                               cwd=SIM_ROOT, timeout=1500)",
        "            r = subprocess.run(cmd, capture_output=True, text=True,\n"
        "                               cwd=SIM_ROOT, timeout=1500,\n"
        "                               env={**os.environ,\n"
        "                                    \"TCG_MAX_DECISIONS\": \"3000\"})",
    ),
    (
        "    wins = played = 0",
        "    wins = played = capped_total = 0",
    ),
    (
        "        wins += int(summ[\"wins\"])\n"
        "        played += int(summ[\"games\"])",
        "        wins += int(summ[\"wins\"])\n"
        "        played += int(summ[\"games\"])\n"
        "        capped_total += int(summ.get(\"capped_games\", 0))",
    ),
    (
        "    wr = wins / played",
        "    # ROUND-7 ALIGNMENT: draw-scored read -- capped games score\n"
        "    # 0.5 (re-specified instrument; see stage3-alignment.md).\n"
        "    wr = (wins + 0.5 * capped_total) / played",
    ),
    (
        "                won = 1.0 if (winner == seat and not capped) else 0.0",
        "                # ROUND-7 ALIGNMENT: capped games are draws (0.5)\n"
        "                # in the heartbeat / recent tallies (re-specified\n"
        "                # instrument). Episode rewards are NOT changed:\n"
        "                # they receive `capped` separately, above.\n"
        "                won = (0.5 if capped else\n"
        "                       1.0 if winner == seat else 0.0)",
    ),
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
