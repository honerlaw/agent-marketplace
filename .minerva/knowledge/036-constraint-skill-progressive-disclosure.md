# Skills keep ≤9KB SKILL.md cores with detail prose in on-demand references/

**Date**: 2026-06-11
**Type**: constraint
**Context**: .minerva/work/035-skill-progressive-disclosure

## Context
A `propose-ship-auto` run chain-loaded ~119KB of skill prose into the main-loop session, re-billed on every API call. Work unit 035 restructured the nine ≥10KB skills into thin cores plus per-skill `references/` files via verbatim moves, and froze every skill — restructured or not — at a byte budget.

## Finding
Every skill's `SKILL.md` must stay **≤9216 bytes**, with detail prose living in per-skill `references/*.md` files that the core points at through mandatory read-before-step instructions. The enumerating `tests/test_skill_budget.py` enforces the byte budget and bidirectional pointer integrity (every `references/*.md` mentioned by name from its core; every `references/` mention resolving to a real file). Contract anchors follow moved prose via the per-anchor `file` field — the mechanics are documented in `evals/README.md`; that is the source of truth, do not restate it here.

## Implications
- **Editing a skill near budget**: move detail to `references/` (verbatim where possible) instead of growing the core, and retarget affected contract anchors deliberately via `file` — never weaken or delete them.
- **using-minerva's decision matrix stays in its SKILL.md core deliberately.** `test_skill_contracts.py` hardcodes that body as the `cross_surface` surface and checks **token presence only**: a wholesale matrix move to `references/` would red ~10 skills' cross_surface checks, while the unguarded path — gutting the matrix's *guidance prose* into `references/` and leaving bare tokens behind — keeps tests green. Do neither: the matrix is the wiki's routing surface.
- The budget binds all skills, not just the restructured nine — skills already under the cap are frozen at it.

## Related
- [[012-constraint-skill-structural-contracts]] — builds on
- [[035-constraint-ci-test-enumeration-explicit]] — see also
- [[047-constraint-skill-description-house-style]] — see also
