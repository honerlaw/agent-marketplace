---
name: a-migration-judges-done-from-the-destination
description: Use when a migration both copies files and then deletes them — decide each item's state from the destination once copied, because the deletion changes the source state the plan reads.
metadata:
  type: pattern
---

# A migration that deletes its source must judge "done" from the destination, not the source

**Date**: 2026-11-25
**Type**: pattern
**Theme**: silent-success
**Summary**: removal changed the source state the plan read; units looked in-flight forever and migration never finished
**Context**: .minerva/work/2026-11-25-lorestrom-migrate (see git history if the worktree has been cleaned up)

## Context

`lorestrom:migrate` reads each minerva unit's state (in flight or finished) from its local
files. It imports the unit, then a removal commit deletes the imported files. The plan that
decides each unit's next step runs again before every removal and on every re-run.

## Finding

The independent code review found that two paths never reached "migration complete":

- **An abandoned import stayed blocked.** A unit was imported as abandoned on the user's
  yes, but the removal planner passed no `abandon` list. It still read the unit as in flight
  and `blocked`, so the files were kept with a false reason and `unitsRemaining` never hit 0.
- **Leftover files read as live work.** After the removal took a finished unit's
  `proposal.md`, `scratchpad.md` and `archive/`, any file left behind (a script, a kept
  record) made the unit read as never promoted. Every later run asked the abandon question
  again for a unit already released.

The tests had covered each step on an untouched source tree, never a re-run after the
removal. The fix was to decide a unit from Lorestrom alone once its import gate is closed,
whatever the local files say now. A unit with no proposal left is no longer read as live
work.

## Implications

- **Once a copy is closed, the destination is the authority** for that item. Source-derived
  state is input only for items not yet copied.
- **Test the second run.** Run the migration step, apply its own deletion, then plan again.
  Every terminal state, including "taken by someone else" and "refused", must count as
  finished, or the completion counter never reaches zero.
- **What the remover gives to git must match what git can remove.** Only tracked files with
  no edits belong in the list. One untracked or edited path makes `git rm
  --pathspec-from-file` abort the whole commit.

## Related
- [[2026-11-23-pattern-a-review-fix-round-needs-its-own-re-review]] — relates to: the review that found these was the loop's own check, not the tests
- [[2026-11-25-decision-lorestrom-migrate-moves-all-of-minerva-and-init-only-links]] — relates to: the migration these defects were found in
