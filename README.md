# tcg-roundrobin

Venue for the expert round-robin on the Flesh and Blood bot-v-bot
experiment (hero-independent player; local Talishar only, never public
queues). **This repository is public** (Joe's direction, 2026-10-18, so the
reviewers can clone it without credentials). Assume anything committed is
world-readable: no tokens, keys, credentials, or personal data, ever.

## How this venue works

- **Rounds live in `rounds/`.** Each round has the package as sent and the
  reply as received, byte for byte. Nothing here is paraphrased in transit.
- **Code under review lives in `code/`.** Standing rule (Joe, 2026-10-18):
  any build whose output will be cited as a *measurement* — gate/paired
  drivers, label fleets, scorer changes, teacher/search patches — gets
  Claude's approval of the full plan AND the code here before it launches.
  In-run verification stays mandatory regardless (control arms, arm-log
  audit before interpretation, arm manifests read from the child process's
  own startup log).
- **Issues are the working threads.** One issue per open question; the
  current one is the pre-gate ghost test.
- Outward actions under Joe's name (anything leaving this repo) require
  Joe's own explicit go-ahead. Drafts live here until he says otherwise.

## State of play (2026-10-18 evening)

- The faithful-teacher path is the live direction; the §3 measurement
  projects +0.118 WP per game gated [0.046, 0.202] and cleared its
  pre-registered bar (`rounds/round2/consolidated-update-to-claude.md` §3).
- The gate is **stopped** at its pre-registered pre-gate test: the ghost
  (teacher machinery, pick forced to the prior's) must reproduce bridge-only
  v15 action-for-action on paired seeds. It does not (0/19), against a
  bridge that reproduces itself 19/19 byte-identically. Mechanism hunt is
  the open issue.
- Labels-3 suite H (arsenal-fix corrected): ≈ 0.036 WP per selected decision.
