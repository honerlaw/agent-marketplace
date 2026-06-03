# Scratchpad: synthesize-skill (024)

## Panel decisions 2026-06-03

- [escalated to user → resolved] scope check (round 1): panel SPLIT 1/3 — separate the
  capability from orchestrator wiring. Re-cut to a **capability-only** unit (wiring
  deferred to a follow-up).
- [3/3 accept] scope check (round 2, revised): capability-only + first overview;
  orchestrator wiring deferred. (Skeptic residuals folded: confirm overview.md exempt
  from the index-drift check; note future entry-rewriting synthesis would reintroduce
  the 016 hazard.)
- [2/3 accept → revise] approach selection (round 1): X (separate overview.md +
  deterministic synthesis_status.py + self-gating skill) over Y (`## Themes` in
  index.md — clobbered by knowledge_fix.py) and Z (no status script — untestable gate).
  Arbiter `revise`: fold 3 must-includes.
- [3/3 accept] approach selection (round 2, X′): folded (a) mechanical fence-aware
  link-rot check into synthesis_status.py, (b) watermark `## Limitations` honesty,
  (c) test_synthesis_status.py appended to evals.yml's enumerated list.
- [2/3 accept → revise] whole-proposal (round 1): Proponent accept; Skeptic `revise` on
  2 HIGHs — (1) deliverable ambiguity (ship a real overview.md or capability-only?),
  (2) link-rot reuse claim wrong (`parse_index` returns empty on a theme-grouped
  overview → silent clean; all wikilinks are full `[[NNN-type-slug]]` stems).
- [3/3 accept] whole-proposal (round 2, X′′): resolved — (1) unit dogfoods to commit the
  first real overview.md; (2) link-rot uses `ENTRY_RE`-glob enumeration + fence-aware
  `WIKILINK_RE` scan (not parse_index). Build-time checks carried to WORK: confirm
  test_skill_contracts reads RAW SKILL.md text (anchors register); confirm
  `synthesis-watermark` doesn't trip `WATERMARK_RE` (anchored, index.md-only); ensure
  `## Limitations` documents staleness-by-1 after this unit promotes as 024.

## Notes
