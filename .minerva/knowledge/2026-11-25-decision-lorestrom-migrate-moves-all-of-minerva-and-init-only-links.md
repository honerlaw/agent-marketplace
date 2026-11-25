---
name: lorestrom-migrate-moves-all-of-minerva-and-init-only-links
description: Use when changing how a repository moves from minerva to lorestrom — migrate imports all of .minerva/ (work units included) and removes it in confirmed commits; init only links.
metadata:
  type: decision
---

# lorestrom:migrate moves the whole of `.minerva/` into Lorestrom and removes it; init only links

**Date**: 2026-11-25
**Type**: decision
**Theme**: lifecycle
**Summary**: migrate imports knowledge, reference docs and work units, then removes .minerva; init became link-only
**Context**: .minerva/work/2026-11-25-lorestrom-migrate (see git history if the worktree has been cleaned up)

## Context

Lorestrom is minerva's successor. In 0.4.0, `lorestrom:init` imported knowledge and reference
docs and offered to remove those files, but it left `.minerva/work/` in the repository. A
migrated repository therefore still had a `.minerva/` tree, and its unit history was not in
Lorestrom, where every lorestrom skill reads.

## Finding

0.5.0 splits the two jobs:

- **`lorestrom:init`** only links, in any repository. When `.minerva/` still holds files, it
  names `lorestrom:migrate` and offers to continue into it. It never imports or removes
  anything itself.
- **`lorestrom:migrate`** links if needed, then imports in order:
  1. knowledge entries and reference docs (the old handover);
  2. every work unit, as a unit doc plus one `minerva:record` per markdown file, created
     under the unit's own gate. The gate is then released for a finished unit. For an
     in-flight unit the user agreed to give up, it is abandoned, which archives the records.
- **After each run,** migrate removes in a confirmed commit every file whose exact digest
  Lorestrom holds. The same commit replaces the agent file's minerva section and drops the
  `.minerva/worktrees/` ignore line.
- **What Lorestrom does not hold** goes only on a second, separate yes.

An imported unit has a released gate and reads as promoted and shipped. `status`, `cleanup`
and `lint` therefore treat it as a finished unit without any change. Records that are not
standard (`archive/scratchpad.md`, `research.md`) take path-named keys from a new
`unit_file_key`, which leaves `record_key`'s restriction on the lifecycle writers in place.

## Implications

- **Large corpora** (more than a thousand units) are imported in batches of 25 per
  confirmation. Each run removes what it finished. The next run starts from what is still on
  disk, so no local ledger is needed and re-runs stay cheap.
- **Live minerva work blocks the migration.** A minerva worktree on disk stops it, and so
  does an in-flight unit until the user says yes to importing it as abandoned. A unit is
  finished in minerva or given up, never resumed across the two plugins.
- **minerva itself is unchanged.** Disabling it for a migrated repository is the user's step,
  because a plugin never edits host settings.

## Related
- [[2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin]] — builds on: the separate plugin this makes minerva's successor
