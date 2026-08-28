---
name: a-worktree-glob-sees-every-unit-in-the-project
description: Use when a scan globs through `.minerva/worktrees/*/` to learn something about a work unit — every linked worktree carries the whole COMMITTED `.minerva/work/` history, so reachability through a worktree is evidence about the repository, never about that worktree.
metadata:
  type: bug
---

# A glob through `.minerva/worktrees/*/` sees every unit in the project, not that worktree's unit

**Date**: 2026-08-28
**Type**: bug
**Summary**: Reachable-through-a-worktree and has-a-worktree are different questions; the first is true of everything
**Context**: .minerva/work/2026-08-28-workstream-status-skill

## The defect

`minerva:status`'s aggregator walks two roots — `.minerva/work/*` for the main-tree record and
`.minerva/worktrees/*/.minerva/work/*` for a unit that exists only on an unmerged branch. It set
each unit's `worktree_present` flag when the second glob reached it.

Against the live corpus the flag read **true for all 65 units in the project**, while exactly two
worktrees existed on disk.

## Why

A linked worktree is a full checkout of a branch. `.minerva/work/` is **committed**, so every
worktree contains the entire history of every unit the branch knows about — not just the unit it
was created for. One worktree therefore makes every unit in the project reachable through the
worktree glob.

The two questions had been conflated:

- *Is this unit's record reachable through some worktree?* — true of nearly everything, and
  useless.
- *Does `.minerva/worktrees/<slug>/` exist?* — the question the flag's name promises, and a
  one-line directory test.

## The fix

Keep the glob: it is the only way to see a unit whose branch has never merged, which has no
main-tree record at all. Derive the flag separately, from the directory:

```python
rec["worktree_present"] = (root / ".minerva" / "worktrees" / slug).is_dir()
```

## Why a fixture would not have caught it

A test corpus built by hand contains the unit under test and little else, so the glob and the
directory test agree. The signal that something was wrong was **the count**: 65 of 65. A test
asserting the flag is set somewhere passes against the bug
(`2026-08-10-pattern-presence-assertions-rot-into-green-lies`); the assertion that holds is the
negative one — a unit with no worktree of its own reads `False` — plus a live-corpus check that
the flag *discriminates* at all.

## Related
- [[2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout]] — see also: the sibling worktree trap, in path anchoring rather than glob scope; a walk needs both
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on: why the passing assertion here had to be the negative one
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also: a check whose model of its subject differs from the subject reports clean over what it cannot see
