# Scratchpad: reference-is-a-fifth-entry-type

## Quick decisions 2026-08-09
- [decided] seed: "the followups" = unit 051's three, in this repo. seekless's F1 was already
  routed to propose-ship-auto by owner decision, so it is not this run's.
- [decided] followup 1 investigated BEFORE deciding, and the investigation moved it twice.
  First: seekless does not wire knowledge_lint into CI (agent-marketplace does, and its own
  corpus is clean), and ZERO supersedes edges touch a shared NNN — so the 63 errors gate
  nothing and have no live consequence, which looked like "downgrade to warning, dominant".
  Then reading the linter itself refuted that: it keys `entries` by NNN and explicitly
  quarantines duplicate ids from every per-entry check, so ~130 entries are invisible to it.
  While that holds, a shared NNN DOES degrade linting and `error` is arguably right —
  downgrading first would hide a real blind spot. Correct order is identity, then severity.
- [decided] scope check: DECOMPOSE, and run one sub-unit. The lint stem-keying refactor is
  threaded through ~10 call sites plus `parse_index`'s NNN-keyed catalog — not small, and not
  the same shape as the fixer change it mirrors. This unit is followup 2 only; followup 1 is
  re-scoped in followups.md recommending propose-ship-balanced.
- [escalated to user] followup 2: `reference` as a fifth type vs. keeping four and treating
  the entries as misfiled. Escalated because it changes the type vocabulary every consumer
  repo inherits, and `.minerva/reference/` is a documented alternative home — a model call,
  not a bug fix. Owner chose: add the fifth `## References` section.
- [decided] followup 3 (10 entries with the type only in a prose H1): CLOSED, no action. The
  filename fallback resolves them; writing a field by parsing a title is the guesswork unit
  051 declined. Recorded rather than left dangling.
- [decided] approach: append `## References` to SECTION_ORDER rather than interleaving it.
  Appending is the only position that leaves every existing index's line order untouched.
- [decided] whole-proposal soundness: additive. A corpus with no `reference` entries gains one
  inert header at its next reconcile and nothing else.
