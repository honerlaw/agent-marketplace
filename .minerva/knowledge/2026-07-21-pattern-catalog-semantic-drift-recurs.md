# Catalog semantic drift survives active scrubbing; token-presence tests cannot catch it

**Date**: 2026-07-21
**Type**: pattern
**Context**: .minerva/work/2026-07-21-skill-best-practices-audit (see git history if the worktree has been cleaned up)

## Context
Unit 046 scrubbed stale roadmap phrases ("Phase B.3", "future migration-APPLY unit")
from skill texts. The catalog surfaces mirroring those skills were checked with a
grep whose 160-char-truncated output was misread as clean.

## Finding
Semantic drift between skill text and the catalog surfaces recurs **even during a
unit actively fixing that exact staleness**: three instances of the same retired
phrases survived in catalog surfaces (two `plugins/minerva/README.md` rows, one
`using-minerva` decision-matrix row) and were caught only by fresh-context panel
reviewers across two verification votes. The existing tests assert token *presence*
only, so a green suite is no evidence of semantic sync — the site-catalog test says
this about itself. Truncated tool output reading as clean was the proximate cause of
the false-negative check.

## Implications
Whenever a skill's description or behavior text changes meaning, sweep **all four
catalog surfaces** — `plugins/minerva/README.md`, the root `README.md`,
`pages/index.md`, and `using-minerva`'s decision matrix — using absolute paths and
untruncated output, and treat presence-test greens as irrelevant to semantic sync.
Fresh-context review catches what the editing context cannot see. Automation of the
semantic check is a followup seed in unit 046.

## Related
- [[2026-05-21-constraint-minerva-skill-catalog-sync]] — builds on
- [[2026-06-10-constraint-site-fourth-catalog-surface]] — see also
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also
