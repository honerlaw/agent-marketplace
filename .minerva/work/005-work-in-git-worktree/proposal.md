# Proposal: work-in-git-worktree

**Date**: 2026-05-19
**Status**: Draft

## Goal

Every `minerva:work` invocation creates and uses an isolated git worktree for the work unit. The worktree lives at `.minerva/worktrees/NNN-slug/` on a branch named `NNN-slug`. The work unit's docs (`proposal.md`, `scratchpad.md`, any `replan.md`) are moved from `.minerva/work/NNN-slug/` on `main` into the worktree before implementation begins. On resume, the skill detects the existing worktree and switches to it rather than creating a new one.

## Why

`minerva:work` currently runs implementation directly on `main`, meaning in-progress feature work mingles with the stable codebase. A git worktree gives each work unit a fully isolated branch and filesystem view — no stashing, no dirty working tree, no risk of accidentally committing half-finished changes to `main`. Moving the docs into the worktree keeps the work unit's full context (proposal, scratchpad, replans) co-located with the code changes on that branch, so the branch is self-describing when reviewed or merged.

## Approach

Modify `plugins/minerva/skills/work/SKILL.md` — insert a **Worktree Setup** section immediately before the existing **Setup** section. The new section instructs:

1. Resolve the target work unit (existing logic, unchanged).
2. Check whether `.minerva/worktrees/NNN-slug/` already exists.
   - **If not:** run `git worktree add .minerva/worktrees/NNN-slug NNN-slug`, then move the entire `.minerva/work/NNN-slug/` directory into `.minerva/worktrees/NNN-slug/.minerva/work/NNN-slug/`. Commit the removal from `main` (message: `chore: move NNN-slug work unit to worktree`). In the worktree, commit the addition (message: `chore: initialize NNN-slug work unit`).
   - **If yes:** the worktree already exists — switch to it; docs are already there.
3. Ensure `.minerva/worktrees/` is in `.gitignore` on `main` (append if missing).
4. All subsequent steps (reading docs, scratchpad maintenance, implementation) happen inside the worktree.

The existing **Setup**, **Implementation protocol**, and **Completion signal** sections are otherwise unchanged — they run in the worktree context.

## Open Questions

- `minerva:promote` is unchanged — it runs inside the worktree where docs live at the same relative paths. Promoted artifacts become part of the branch and are included when the branch is merged to `main`. No changes needed.
- Worktree teardown, PR creation, and code review are out of scope for this work unit. A future skill will handle closing the worktree, opening the PR, and the review workflow.
