# Round 10 — DESIGN: a stronger Gravy teacher

**Status: DESIGN for Claude's review. Nothing in this
document is a registration yet; no code is written, no
run is approved. Joe chose this direction 2026-10-28
(Claude's round-9 §4, path 3) on the builder's
recommendation.**

## 1. The question

Round 9 closed with the calibrated teacher's
per-decision edge established and replicated, and its
game-level conversion unshown at the registered
precision (Stage 3: Δ +0.0475 [0.0000, 0.0950], DOES
NOT CONVERT, ~49% power at the realized Δ). Claude's
§4 named the alternative to a bigger fleet: **improve
the teacher before measuring again.** This round asks:

*Can two targeted changes — wider coverage and a
life-sensitive horizon value — raise the teacher's
per-game gain enough that a correctly sized fleet
becomes the cheap next step instead of a 950-pair
certification of the current build?*

Scope, stated plainly as in round 9: this is
teacher/pipeline work on **Gravy Bones** (mirror vs
the heuristic, Eriksen 60), not a hero-independent
policy. The standing constraints carry unchanged:
local Talishar only, observation masking, the
fair-play canary, fresh seed blocks for every
measurement, the reserved 9001–9200 block untouched,
no pooling with any earlier fleet.

## 2. The diagnosis (from round 9's primary records)

1. **The teacher fires rarely.** Stage 3: 622
   overturns over 400 games = **1.5550/game** (Stage 2:
   1.7650), out of 9,538 contested decisions
   (23.8/game) — an overturn rate of 0.0652. In games
   that run 40+ turns, the search intervenes about
   once every 15 contested decisions. Per-decision
   quality is no longer the binding constraint;
   coverage is — the same shape as round 7's null,
   which Stage 0 traced to coverage, one level down.
2. **Its per-decision edge is real but the realized
   per-game gain is modest.** L3: Stage 2 +0.0621
   [0.0440, 0.0809] (gain +0.1096); Stage 3, fresh
   seeds, +0.0417 [0.0311, 0.0527] (gain +0.0649).
   The fleet Δ (+0.0475) sits inside the range the
   Stage 3 gain predicts.
3. **Its deadlocks lose on life.** Capped games:
   teacher 82, ahead on life in **37**; raw 96,
   ahead in **48**. The life-differential read
   (+0.0200 [−0.0275, +0.0700]) is the smallest of
   the three pricings. Mechanistic candidate: inside
   the search, a horizon-ended world is worth a flat
   −1 to the root player **regardless of the life
   totals** — the search has no gradient toward
   holding a life lead in long games, and long games
   are this hero's defining population (~21% of
   raw mirror games reach the cap region at all).
4. **The search bounds are not a lever.** Stage 1:
   under the horizon the hook/deadline bounds never
   bind (max hooks used by any world 1,781 against a
   budget of 8,000). k, hooks and deadlines are
   excluded from this round's changes.

## 3. The two changes (isolated, sequential)

Each change ships as its own build (byte-derived from
`search_s2.php` 85490e8e…, with the diff regenerated
by fixture, as in rounds 8–9) and passes its own L3
gate (§4) before the next is layered on. One change
at a time is the round-7/9 discipline (Stage 0 alone
and first, D5); combined changes would confound
attribution.

**C1 — COVERAGE.** Widen how often the teacher may
act. The knobs, in the order the design proposes to
try them (one configuration, fixed in the package —
not a sweep):
- the overturn margin: 1.5 paired SE → a lower
  registered value (proposal: **1.0**);
- the candidate set: top-3 + prior ≥ 0.10, cap 4 →
  prior ≥ 0.05, cap **6**.
The known risk is round 8's: at lower margins the
overturn labels were largely irreproducible (the
winner's curse — pilot V1-ov 0.167 at the gated
configuration's own width). C1 therefore lives or
dies on the §4 gate's joint read: **per-decision edge
× live fire rate = per-game gain** — a wider teacher
whose edge dilutes to the current gain has failed,
however often it fires.

**C2 — HORIZON LIFE-PRICING.** Replace the flat −1
for horizon-ended worlds inside the search's
candidate means with a life-sensitive value. Proposal
for Claude to shape: a horizon-ended world scores
**−1 + α · s(life_root − life_opp)** for the root
player, where s is a bounded scaling (e.g. the life
difference divided by a registered constant, clamped
to [−1, +1]) and α ∈ (0, 1) is registered (proposal:
α = 0.5). Two boundaries the design states up front:
- This changes the **teacher's internal valuation
  only**. The fleet READ still scores games at
  draw = 0 primary, exactly as registered for round
  9; no scoring rule moves.
- It departs from the pure Swiss price (−1 is the
  exact Swiss value of a never-ending game; §6 of
  the rules reference) toward the elimination
  procedure's life-total logic. The design's claim
  is narrow: as a *search heuristic* it prices the
  state the teacher actually faces at the cap — it
  is not a claim about what a capped game is worth
  in either tournament context. Claude's ruling
  decides whether that departure is acceptable and
  in what form. Life totals on horizon-ended worlds
  are already recorded (Stage 2's addition), so the
  mechanism needs no new instrumentation.
Natural draws (winner 0 away from the horizon) keep
their current pricing in this design; if Claude
wants them life-priced too, that is a third change
and should be named as one.

## 4. The measurement ladder (proposed gates — Claude registers the numbers)

- **Step 1 — integrity pre-gate (per build).** The
  round-9 machinery unchanged: with the teacher
  disabled, the new build must be action-identical
  to raw v10 (ghost/K6 form), canary and masking
  intact. A changed decision rule does not exempt
  the pipeline checks; it makes them the only thing
  standing between a build bug and a measured
  "improvement."
- **Step 2 — L3 gate (per build).** Fresh capture
  games on a fresh seed block; L3 at the registered
  label configuration (W=50, CRN, horizon-aligned,
  draw = 0 primary) over the build's live overturns,
  exactly as Stage 2/3 ran it. Proposed pass bar,
  against the current teacher's Stage 3 replication
  (edge +0.0417 [0.0311, 0.0527], gain +0.0649 at
  1.5550/game): **per-game gain's CI lower bound
  above +0.0649, with the per-decision edge's CI
  excluding 0** — i.e. the gain must grow, not just
  the fire rate, and the edge must survive widening.
  For C2, the same gate plus the life-differential
  co-report read against its Stage 3 value (+0.0381
  [0.0282, 0.0484] in the attribution; +0.0200 at
  fleet level) as the targeted diagnostic. Numbers
  are proposals; the registration fixes them.
- **Step 3 — the fleet (only for a build that
  passes Step 2).** Same form as Stage 3 (paired,
  same seed + seat, both arms, instrument 87/62,
  draw = 0 primary, the same bands and INCONCLUSIVE
  lines), sized by Claude's corrected method from
  §4 of his ruling: price the variance from a
  teacher that actually fires — Stage 3's realized
  cluster SE (0.0247 at 400 pairs) scaled to the new
  build's measured fire rate and gain, targeting
  ~80% power at the gain-implied Δ. The fleet stands
  alone; nothing pools with Stage 3. If the improved
  gain is what C1/C2 aim at, this fleet should be
  materially smaller than the ~950 pairs the current
  teacher would need — that arithmetic is part of
  what Step 2's read must show.

## 5. What stays pinned

`search_s2.php`'s tuple machinery and stamps; the
H8k-180+H search bounds (hooks 8000, deadline 180,
k 25) except where C1/C2 explicitly change the
decision rule and horizon value; the label
configuration (W=50, CRN, seed-lattice discipline
with range-disjoint families); the analyzer family
with its registered bands, tripwires and the §4
ratio guard; the games registry discipline; the
publication standard (report + data/ with MANIFEST,
every figure recomputing from the repo alone).

## 6. Risks and questions for the reviewer

1. **Margin vs winner's curse.** Is 1.0 the right
   C1 margin proposal, or does the round-8 record
   argue for 1.25 first? The design's position: the
   L3 gate is the protection, and it reads the
   joint gain — but the reviewer priced round 8's
   failure and should set this.
2. **The life-pricing form.** Stepped vs continuous;
   the α and scaling constant; whether natural
   draws join the horizon worlds. And the framing
   question: is a deliberate departure from the
   Swiss price inside the *search* acceptable while
   the *read* keeps draw = 0?
3. **The Step 2 bar.** Comparing a new build's gain
   against Stage 3's +0.0649 point estimate imports
   Stage 3's sampling noise into this round's gate.
   Alternatives (a fixed registered floor; a
   head-to-head L3 on shared states) cost more
   machinery. The design proposes the simple form
   and flags the weakness rather than hiding it.
4. **The edge declined Stage 2 → Stage 3**
   (0.0621 → 0.0417, overlapping intervals, fresh
   seeds both times). If that is regression toward
   a true ~+0.04 rather than noise, C1's dilution
   risk is higher than §2 reads it. The Step 2
   gate's edge condition is the design's answer;
   the reviewer may want the C1 gate run against
   the Stage 2 configuration's numbers as well.
5. **Fire-rate ceiling.** C1 widens the candidate
   set, but a state whose prior is concentrated
   still produces no contest. If C1's live rate
   lands under ~2.5/game, is a C1b (contested-state
   definition: the 0.97 uncontested threshold)
   in scope for this round, or a new design?

## 7. What this round is not

Not a confirmation fleet for the current teacher
(§4 path 2 — it remains available, unchosen). Not a
training run: no policy weights change anywhere in
this design; the raw arm stays v10 throughout. Not
a new hero. And not a step toward a hero-independent
policy — it deepens the Gravy teacher line that
rounds 7–9 built, on the argument that the project's
open question (does search convert at game level on
the hard hero) is cheapest to answer with a teacher
strong enough to make the answer visible.
