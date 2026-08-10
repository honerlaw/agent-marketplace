# Proposal: work-in-git-worktree

**Date**: 2026-05-19
**Status**: Shipped (2026-05-19)

## Goal

Every `minerva:work` invocation creates and uses an isolated git worktree for the work unit. The worktree lives at `.minerva/worktrees/NNN-slug/` on a branch named `NNN-slug`. The work unit's docs (`proposal.md`, `scratchpad.md`, any `replan.md`) are moved from `.minerva/work/NNN-slug/` on `main` into the worktree before implementation begins. On resume, the skill detects the existing worktree and enters it via `EnterWorktree` rather than creating a new one.

## Why

`minerva:work` previously ran implementation directly on `main`, meaning in-progress feature work mingled with the stable codebase. A git worktree gives each work unit a fully isolated branch and filesystem view — no stashing, no dirty working tree, no risk of accidentally committing half-finished changes to `main`. Moving the docs into the worktree keeps the work unit's full context (proposal, scratchpad, replans) co-located with the code changes on that branch, so the branch is self-describing when reviewed or merged.

## Approach

Modified `plugins/minerva/skills/work/SKILL.md` with two additions:

**1. Worktree Setup section** (inserted before the existing Setup section):
- Determines NNN-slug from the resolved target.
- Checks for an existing worktree at `.minerva/worktrees/NNN-slug/`:
  - **Exists** → calls `EnterWorktree` with `path: ".minerva/worktrees/NNN-slug"` and continues to Setup.
  - **Does not exist** → ensures `.minerva/worktrees/` is in `.gitignore` on `main` (commits if missing), runs `git worktree add -b NNN-slug .minerva/worktrees/NNN-slug`, moves the work unit docs directory into the worktree, commits the docs on the new branch, then calls `EnterWorktree` to switch the session into the worktree.
- All subsequent steps (reading docs, scratchpad, implementation) run inside the worktree session.

**2. Target resolution update**: the fallback scan now checks both `.minerva/work/` on `main` and `.minerva/worktrees/NNN-*/` — after first invocation, docs only exist in the worktree.

**Also shipped**: `.minerva/worktrees/` added to `.gitignore` on `main` (committed separately on `main` before the worktree was created).
