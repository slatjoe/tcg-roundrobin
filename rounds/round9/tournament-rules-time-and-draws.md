# Tournament rules reference — time limits, draws, and end-of-match

**What this file is:** a working reference for the round-9 design
record, summarizing the provisions of the Flesh and Blood
**Tournament Rules and Policy (TRP)** that bear on the draw/tie
question and on search horizons. It is a summary with section
citations, not a copy of the rules — the TRP text is Legend Story
Studios' and the official documents govern. Extracted 2026-10-26.

**Sources (official):**
- TRP, chapter 3 (Tournament Logistics):
  https://rules.fabtcg.com/en/trp/03-tournament-logistics/
- TRP, appendix (incl. A.3 Time Limits):
  https://rules.fabtcg.com/en/trp/appendix/
- Full TRP PDF (2025-05-30):
  https://dhhim4ltzu1pj.cloudfront.net/media/documents/FaB_Tournament_Rules_and_Policy_2025_05_30.pdf
- FAB top-cut explainer ("Making the Cut"): https://fabtcg.com/articles/making-cut/

## 1. Structure: the clock binds Swiss only (TRP §3.1, §3.2, A.3)

- A typical tournament is timed Swiss rounds for all players,
  followed by untimed single-elimination rounds for the top 8
  ("top-cut" / "play-off" rounds).
- Recommended round times (Appendix A.3), inclusive of the
  start-of-game procedure, based on 1 game to win a match:
  **Classic Constructed 55 minutes**; Blitz 35; Sealed 35;
  Booster Draft 35.
- The start-of-game procedure itself is capped at 5 minutes for
  a match's first game (3 minutes for later games); exceeding it
  is slow play (§3.3, §5.7). Premier-event fact sheets restate
  the split directly: Swiss CC rounds 55 minutes; "Top 8 matches
  have no time limit," with slow-play penalties still enforced.
- Timed rounds: players play until someone wins the required
  games or the round time expires (§3.2). Untimed rounds are a
  best-of-N series to a majority (§3.1); in practice the top cut
  is best-of-one at premier events.

## 2. End of a timed (Swiss) game (TRP §3.4)

- When time expires with no winner determined, the turn player
  completes their turn, then **1 additional turn** is played.
  (If the turn player has no decisions remaining at expiry, their
  turn counts as complete and the opponent takes the additional
  turn.)
- If the additional turn ends with no winner, **the game is a
  draw**. The match goes to the player with more game wins; equal
  game wins = a drawn match.
- A drawn match is worth nothing in the standings (Appendix D,
  as confirmed by Joe from the current TRP: a draw scores
  **0 match points, the same as a loss**; see the round-9
  tie-value settlement, claude-reply-16f02e2 §3).

## 3. Draws and concessions in Swiss (TRP §3.5)

- Players may **intentionally draw** games or matches by mutual
  agreement at any time — **except in elimination rounds**.
- Concessions are allowed at any time in untimed play; in timed
  rounds, up to and including time expiry — once a player acts
  after expiry (or acknowledges an opponent's action), they may
  no longer concede and must play the game out.
- Asking for, or pressuring toward, a concession is prohibited;
  discussing the game state or outcomes as time expires counts
  as pressuring.

## 4. Elimination rounds: a draw is not an acceptable result (TRP §3.4)

Top-8 games are untimed, and the rules force a winner. Where a
draw is not an acceptable match result, the end-of-match
procedure is (current text; this procedure was introduced in
the 2025-01-31 TRP revision):

- **Entry points:** if a judge determines the current game is a
  stalemate, start at Step 2; if the current game is complete,
  start at Step 3.
- **Step 1:** The players are warned that if no progress is
  made, the winner of the current game will be determined by
  the **highest life total**. If no player advances the game
  state toward a result other than a draw, go to Step 2. If play
  continues, the game completes, and the match would be drawn,
  go to Step 3.
- **Step 2:** The winner of the game is the player whose hero
  has the highest life total in the current game. Tied life
  totals → Step 3.
- **Step 3:** The winner of the match is the player with more
  game wins. If neither has more, the players start a
  **tiebreaker game of 4 turns total (2 per player)**; after 4
  turns, go to Step 4.
- **Step 4:** The tiebreaker game continues until one hero has
  a higher life total; that hero's player wins the match. If the
  tiebreaker game itself ends in a draw, go to Step 5.
- **Step 5:** The winner of the match is the player with the
  **higher standing** before the match began.

The rules commentary (Back Alley Oracle #16, fabtcg.com) names
the three causes of a draw the procedure exists for:
**intentional** (players agree), **deadlock** (players will not
progress the game because progressing loses), and **stalemate**
(players cannot progress the game).

## 5. Human anchor (US Nationals 2026 top 8, stream pilot)

All seven top-8 games ended without any procedure being needed
(broadcast overlay turns; durations from the stream file):

| match | result | overlay turns | approx. minutes |
|---|---|---:|---:|
| QF1 | Eriksen (Gravy) > Gump (Fai) | 10 | ~38 |
| QF2 | Rich (Victor) > Battaglia (Gravy) | 23 | ~68 |
| QF3 | Slattery (Fai) > Grace (Oscilio) | 5 | ~31 |
| QF4 | Magnuson (Zyggy) > Majin Bae (Oscilio) | 10 | ~36 |
| SF1 | Eriksen (Gravy) > Slattery (Fai) | 12 | ~53 |
| SF2 | Rich (Victor) > Magnuson (Zyggy) | 23 | ~57 |
| F | Eriksen (Gravy) > Rich (Victor) | 18 | ~51 |

Two of these games ran past the 55-minute Swiss recommendation
— only possible because the top cut is untimed. No stall
population exists at a real top table: players steer for a
result, and §4 above is the backstop if they don't.

## 6. Bearing on the registered design (already settled)

- The tie settlement stands (claude-reply-16f02e2 §3): **draw =
  0** for the search and the reads from Stage 1 onward. Nothing
  in this reference re-opens it — a Swiss draw earns nothing,
  and an elimination draw is not a recordable result.
- What the project models is **Swiss advancement**. The clock,
  the zero-point draw, and the turn-plus-one ending all exist
  only in Swiss, and Swiss is where advancement — day 2, the top
  cut — is decided. The turn-62 horizon is a search instrument
  (a bound on non-terminating rollouts), not a model of a
  tournament clock. A turn-versus-time curve, if built,
  describes Swiss rounds; note the §5 table's turn/time points
  come from *untimed* games, so they would overstate how many
  turns fit inside a Swiss round.
- The −1 price for a horizon-ended world is **exact for
  Swiss**: a deadlocked Swiss game is a draw — 0 match points
  to both — so for the player who needed the win it prices as a
  loss. For top-cut play the same price is an approximation:
  there a deadlocked game is settled on life total (§4 Steps
  1–2), so −1 is right when the root player is behind on life
  and harsh when ahead. Stage 2's build records **both
  players' life totals on every simulation that ends at the
  turn-62 cutoff**, so a life-based price (ahead = win, behind
  = loss, tied = draw) can be reported beside the primary
  without re-running anything.

*(§6 amended 2026-10-26 on Claude's review of this file: the
original text described top-cut games as "the games the project
most wants to emulate" and −1 as a conservative simplification
of the top-8 rule. The modelled context is Swiss advancement;
the record now reads that way.)*
