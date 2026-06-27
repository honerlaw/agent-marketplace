# Add .minerva/worktrees/ to .gitignore before running git worktree add

**Date**: 2026-05-19
**Type**: decision
**Context**: .minerva/work/008-work-in-git-worktree

## Context

When `minerva:work` creates a worktree at `.minerva/worktrees/NNN-slug/`, the worktree directory lives inside the main repo's working tree. If `.gitignore` doesn't already exclude `.minerva/worktrees/`, git on `main` sees all the worktree's files as untracked — every file in the worktree appears in `git status` on the main branch.

## Finding

Update `.gitignore` to include `.minerva/worktrees/` and commit that change on `main` before calling `git worktree add`. The `.gitignore` commit must land first; creating the worktree directory before the ignore rule is in place is enough to surface the problem.

## Implications

- `git status` on `main` stays clean while a worktree is active.
- The `.gitignore` entry is permanent — it should not be removed after the worktree is torn down, since future work units will create the same path.
- Any skill or script that creates worktrees under `.minerva/worktrees/` must check for this entry before calling `git worktree add`.

## Related
- [[008-constraint-enter-worktree-absolute-paths]] — see also
- [[044-decision-worktree-addressing-no-enterworktree]] — see also
