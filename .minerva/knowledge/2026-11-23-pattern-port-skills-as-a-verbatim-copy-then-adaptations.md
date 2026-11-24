---
name: port-skills-as-a-verbatim-copy-then-adaptations
description: Use when copying a large set of skills from one plugin into another — commit a verbatim copy first, then a mechanical rename, then the adaptations, so review reads only what changed.
metadata:
  type: pattern
---

# Port a large skill set as a verbatim copy, then a mechanical rename, then adaptations

**Date**: 2026-11-23
**Type**: pattern
**Theme**: skills-and-catalogs
**Summary**: verbatim-copy commit with equal tree hashes, then rename, then adaptations: review reads only the diff
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

Porting minerva's lifecycle into the lorestrom plugin meant about 4,000 lines of skill text,
much of it shell snippets under the names-are-data guard. As one diff, the copied text and the
changes to it are indistinguishable, and a PR of 5,000–6,000 lines cannot be reviewed line by
line.

## Finding

Each port PR (12 skills in 0.2.0, the two orchestrators in 0.3.0) was built as:

1. **A verbatim-copy commit** touching nothing else. Its directory tree hashes equal the
   source's at that commit (`git rev-parse <commit>:<dir>`), checked mechanically by the builder,
   the Verifier and the shipper.
2. **A mechanical-rename commit** (plugin names, paths), reviewable by pattern.
3. **Adaptation commits**, which are what review reads.

Reviews then found real defects in the adaptations (a dropped user confirmation, a phase loop
that skipped work) rather than drowning in copied text, and defects inherited unchanged from the
source were easy to tell apart and record as source follow-ups.

## Implications

- Squash merging keeps `main` clean; the structure lives in the PR's commits, so say in the PR
  body which commit is the copy.
- Inherited defects found this way belong to the source plugin. Record them; do not fix them in
  the copy silently, or the two drift without a record.

## Related
- [[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]] — relates to: the copies diverge deliberately after the copy commit, so equality is checked only there
- [[2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin]] — applies: how that plugin's skills were ported
