# Round 8 — W-check fix: the v15 pin literal (one literal) + an expect_hash length guard

**Defect:** documented in `rounds/round8/wcheck-report.md` (committed
0e4c285a). The `expect_hash "$V15" …` pin literal in
`code/run_w_check.sh` was **62 hex characters** — the `d0` at file
indices 58–59 dropped — so the pre-flight pin could never match the
checkpoint it guards and the W=100 V1 check aborted at launch before
any labeling. The box's v15 file was always the correct one. This
package makes exactly two changes to the script: the one literal,
and a guard so a malformed pin fails as a malformed pin (below).
Diff: `fixtures/run_w_check_fix_diff.txt` (2 hunks).

**File:** `code/run_w_check.sh`
`9d982a49d580a55d7e9ccb7f3c31fd939ea6765109c80ada9870990d684a82d8`
→ **`489bf8451b0976a4e0ccf023154a0885814067b2e01d4c0159eeb3b39fad425a`**

## Machine extraction — the hash was never hand-typed

The replacement value was taken from the box, into files, and the
edit was performed programmatically against those files:

```
~/workspace/tcg-sim/ops/ssh-box.sh 'sha256sum /home/joe/tcg/tcg-sim/rl_out/fai_ppo_bc3b_20261016/ckpt_v15.pt' > /tmp/v15_sha256sum.txt
awk '{print $1}' /tmp/v15_sha256sum.txt > /tmp/v15_true_hash.txt
python3 /tmp/fix_w_check.py   # asserts the extracted value matches ^[0-9a-f]{64}$,
                              # finds the 62-char literal by regex at the
                              # expect_hash "$V15" call, replaces it with the
                              # extracted value, inserts the guard; writes back
```

The fixer located the defective literal with the regex
`(expect_hash\s+"\$V15"\s*\\\s*\n\s*)(?<![0-9a-f])([0-9a-f]{62})(?![0-9a-f])`
(exactly one match) and confirmed the diagnosis in passing: the old
literal's tail from index 56 was `e9c82c`; the extracted value's is
`d0e9c82c` — the dropped pair restored at 58–59.

## Verification (programmatic, after the edit)

`bash -n` passes. A separate verification pass (re-reading the
edited file, comparing strings in code, not by eye) printed:

```
v15 literal in edited script: len=64
string equality with box-extracted hash: True
long hex literals (>=40 chars) found: 4
  len=64  head=f81193e0b8a2 tail=7a5f0b92
  len=64  head=81ef2cdbefe6 tail=d85a82d4
  len=64  head=0400539dda89 tail=d0e9c82c
  len=64  head=f81193e0b8a2 tail=7a5f0b92
62-char remnants: 0
VERDICT: v15 literal == extracted hash, len 64; audit clean (no 62-char remnants)
```

(The four long literals are the script's three pins, the featurize
pin appearing twice — top level and in `build_tree`.)

## The guard

`expect_hash()` is the script's shared pin function (four call
sites). The assertion was added at its head, before any hashing,
in the function's existing abort style — two lines:

```bash
  [[ "$2" =~ ^[0-9a-f]{64}$ ]] || {
    echo "ABORT: pin for $3 is not a 64-char sha256 (got ${#2} chars)" >&2; exit 1; }
```

So any future malformed expected-value — wrong length or non-hex —
aborts naming the pin (`$3`, e.g. `v15`) and the length it actually
carries, instead of surfacing as a hash that "disagrees with
itself". Functional tests (the function extracted from the edited
file and exercised in a subshell):

- 62-char pin → `ABORT: pin for testpin62 is not a 64-char sha256 (got 62 chars)`, exit 1
- correct 64-char pin for a known file → exit 0, silent
- 64-char pin with a non-hex character → `ABORT: pin for testpin-nonhex is not a 64-char sha256 (got 64 chars)`, exit 1

**`run_label_corpus.sh`:** the same `expect_hash` length/format
guard is **absent** there — its `expect_hash()` is the same
unguarded compare (its v15 literal itself is the full 64 chars, per
the wcheck report's audit). Not edited here; noted for a future
package if the reviewer wants the guard everywhere.

## What remains

- **Claude's confirmation of this fix commit** (the script is a
  confirmed measurement build; the correction returns for his
  confirmation, as with the equivalence fix).
- Then **the W=100 V1 check relaunches** under the existing launch
  manifest `rounds/round8/wcheck-launch.md` (08ea4bb7) on Joe's
  recorded Option-1 go — no new go needed. The check's PASS/STOP
  question (V1-ov ≥ 0.50) is untouched by this fix.
- The corpus stays gated on the check, as before.
