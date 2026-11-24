---
name: move-authority-with-every-writer
description: Use when phasing a migration of where records live — the release that makes the new store authoritative must also ship every skill that writes those records.
metadata:
  type: pattern
---

# Move authority over records in the same release as every skill that writes them

**Date**: 2026-11-23
**Type**: pattern
**Theme**: lifecycle
**Summary**: a store becomes authoritative only in the release shipping all its writers; nothing writes the ignored store
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

The lorestrom plugin's lifecycle phase (14 skills ported from minerva) was too large for one
reviewable PR. Splits by skill each broke something: a release with promote but without the
handover would write knowledge to Lorestrom while the repo's files were still authoritative;
review and status could not read units that exist only in Lorestrom; and handing authority over
first would leave minerva's promote writing files that Lorestrom then ignores.

## Finding

One rule ordered the phases: **authority over a linked repo's records moves in the same release
as every skill that writes them, or hands off to one that does.** No release then writes records
to the store that is not authoritative, and none leaves an auto-triggered skill writing to a
store nothing reads.

- Every writer landed with the handover (0.2.0), made reviewable by its commits rather than by
  splitting it.
- What could not fit (the two orchestrators) shipped next, and until then the text said the
  lifecycle runs skill by skill and minerva's orchestrators must not run in a linked repo.
- Reading skills that only read records went with the writers, because after the handover the
  records exist only in the new store.

## Implications

- Check each candidate split against the rule before weighing its size. Every split the builder
  proposed first failed it.
- The interim instruction ("don't run X until the next release") is a cost of the split. Keep
  the window short: merging the orchestrators into the later sweep phase would only have
  lengthened it.

## Related
- [[2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin]] — applies: the rule ordered that plugin's phases
