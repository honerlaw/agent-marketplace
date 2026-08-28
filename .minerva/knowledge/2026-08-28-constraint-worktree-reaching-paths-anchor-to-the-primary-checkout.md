---
name: worktree-reaching-paths-anchor-to-the-primary-checkout
description: Use when a skill snippet builds a path that reaches into `.minerva/worktrees/` — `git rev-parse --show-toplevel` returns the LINKED worktree from inside one, and the `--git-common-dir` replacement prints a relative `.` from the primary checkout unless wrapped in `cd … && pwd`.
metadata:
  type: constraint
---

# A path that reaches into `.minerva/worktrees/` anchors to the primary checkout, absolutely

**Date**: 2026-08-28
**Type**: constraint
**Summary**: `--show-toplevel` yields the linked worktree; use `cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd`
**Context**: .minerva/work/2026-08-27-deferral-cost-model (see git history if the worktree has been cleaned up)

## The rule

```bash
ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
```

Use this — not `git rev-parse --show-toplevel` — for any path that reaches **into**
`.minerva/worktrees/`. Verified identical and absolute from the primary checkout, from inside a
linked worktree, and from a nested subdirectory.

## Why `--show-toplevel` is wrong here

It resolves the **current** working tree's root, which is the *linked worktree* when invoked from
inside one. `2026-06-03-constraint-skill-wraps-script-via-importable-api` already documented this
in its Implications — and it was still shipped wrong, by an author who had read that entry during
the same work unit's review. Knowing a hazard is written down somewhere is not the same as
checking whether the path you just wrote is one of its cases.

The failure is quiet. `minerva:ship` addresses a worktree but keeps its CWD in the parent repo, so
an unanchored `.minerva/work/<slug>/proposal.md` either does not exist yet (phase 1 of a new unit:
the file lives only on the branch) or — worse — resolves to a **stale merged copy** from an
earlier phase. The stale copy parses fine and yields a wrong answer with no error.

## Why the `cd … && pwd` wrapper is load-bearing

`git rev-parse --git-common-dir` prints an **absolute** path from inside a linked worktree but a
**relative** `.git` from the primary checkout. So the bare `dirname "$(git rev-parse
--git-common-dir)"` is `.` in the ordinary case — a CWD-relative root, which is the exact
anti-pattern the importable-API constraint forbids, and it happens to work while CWD is the repo
root. A peer session proposed the unwrapped form and would have shipped it.

The property to test for is **absolute from all three positions**, not "works where I ran it".

## Scope

This is not a blanket replacement. `--show-toplevel` remains correct where per-branch semantics
are wanted — `minerva:lint` deliberately audits the corpus of the branch you are on. The
distinction is whether the path reaches *across* worktrees or stays *within* the current one.

## Related
- [[2026-08-28-constraint-a-skill-snippet-runs-the-primary-checkouts-code]] — the complementary half: this entry anchors to the primary checkout for paths reaching ACROSS worktrees; that one anchors to the current tree to identify the code being edited, which is why `plugin_guard.py` uses `--show-toplevel` and is right to
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — builds on: it documented the `--show-toplevel` hazard and forbade CWD-relative paths; this names the concrete replacement and the relative-`.` trap in it
- [[2026-05-20-constraint-enter-worktree-absolute-paths]] — see also: the sibling rule for addressing a worktree rather than entering it
- [[2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project]] — see also
