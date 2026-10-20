I'm accepting the gate run as valid, but **I wouldn't call it a win yet.** The teacher is ahead by +0.2525, about 25 points of win rate (confidence interval +0.21 to +0.30), and the registered rule says a gain that large must be investigated before we accept it. The machinery checks came back clean. What hasn't been ruled out is the October failure: the teacher secretly seeing the opponent's hidden cards.

**What I checked myself from the committed game records:**
- The headline holds: teacher won 70.25%, raw v15 won 45%.
- On seeds where only one arm won, the teacher won 111 and raw won 10.
- All 400 game pairs are valid.
- The 73 pairs with no teacher override played byte-identical games, as the pre-gate predicted.
- No timeouts, the production server is unchanged, and no override broke its own margin rule.

**One registered stop rule tripped, and I lifted it on the record.** Eight pairs were flagged because the logger wrote two rows for the same decision. This is a known logging quirk I accepted back in round 3, and it didn't change any move. Dropping those 8 pairs leaves the gain at +0.2449, so the result doesn't depend on that call either way.

**Why it's not a win yet.** The October leak looked exactly like this: a big gain concentrated in the overrides, with clean margins. The planned audit can't rule that out, because it re-scores overrides with the same rollout machinery, which would carry any leak along with it. Two cheap checks on this gate's own data settle it:
- **L1:** count how often all 25 simulated games agree unanimously. October's leak made that true for every override; honest simulations rarely agree completely.
- **L2:** re-run the hidden-card swap test on 20 of the gate's actual override positions. If changing the opponent's hidden cards changes the simulation results, the teacher is seeing those cards.

**Then the audit itself (L3).** Re-score all 915 overrides, not a sample of 100. That's about 90 minutes of compute. It needs fresh simulations, and the main number should be how much better the override move is on average.
- If L1 and L2 come back clean and the override advantage is clearly above zero, the gate counts as a win.
- If the advantage isn't distinguishable from zero, the +0.25 is unexplained and nothing should build on it.

**What the result means either way.** The teacher plans against an exact copy of the heuristic opponent it's playing. So +0.25 shows it can exploit a known, fixed opponent, not that it's generally stronger. Before any broader claim, it needs to be tested against an opponent it doesn't model exactly.
