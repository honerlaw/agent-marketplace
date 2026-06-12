---
name: ship
description: Use when the user invokes `minerva:ship`, asks to ship / push / open a PR for / merge the current work, or wants the agent to commit outstanding changes to a branch, open a pull request, watch CI, fix CI failures, and enable auto-merge. CI is watched via ScheduleWakeup polling instead of blocking. Closes the minerva lifecycle after `minerva:work` / `minerva:promote` / `minerva:review`.
---

Close the minerva lifecycle by committing outstanding work to a branch, opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop (3 iterations) via ScheduleWakeup polling, and enabling auto-merge when repo permissions allow.

## Usage

- `minerva:ship` — ships the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous, or runs in **bare mode** if no work unit is found
- `minerva:ship 005-add-payments` — ship the named unit explicitly

## Pre-flight checks

Bail with a clear, one-line message on any failure:

1. **Git repo.** `git rev-parse --is-inside-work-tree` returns true.
2. **`gh` CLI available and authenticated.** `gh auth status` exits 0.
3. **Something to ship.** At least one of:
   - `git status --porcelain` is non-empty (staged, unstaged, or untracked changes), or
   - the current branch has commits ahead of the default branch.
4. **Not a no-op.** If currently on the default branch with zero commits ahead and no local changes, there is nothing to ship — stop.

## Protocol

The full step protocols live verbatim in `references/protocol.md` — **read it now, before executing**: **Target resolution** → **Worktree entry** → **Default-branch detection** → **Branch creation** → **Commit outstanding changes** (Hard gate #1: commit message confirmation) → **Push & open PR** (Hard gate #2: PR title + body confirmation) → **CI watch & auto-fix loop** (ScheduleWakeup polling at `delaySeconds: 270`, bounded 3-iteration auto-fix) → **Auto-merge** → **Final report**, plus **Lifecycle nudges** and **Worktree handling**.

## Idempotency

Ship does not write its own metadata file or append a `## Shipped` marker to `scratchpad.md`. The PR URL lives on GitHub; nothing minerva-side needs to remember it. Re-running on a branch that already has an open PR will detect that (`gh pr view`) and pick up at the CI-watch step instead of re-creating.

Wake-ups re-invoke `minerva:ship`; the skill detects the existing PR and resumes the watch loop using the iteration count carried in the wake-up prompt.

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote`.
- **Running `minerva:promote` or `minerva:review` automatically.** Only nudges, never auto-invokes — keeps the user in control of what gets promoted and reviewed.
- **Worktree cleanup.** Owned by `minerva:cleanup`.
- **A strict mode** that turns nudges into hard blockers. Deferred; users who want strict ordering can run the skills in order themselves.
- **Replacing `ship-it` for non-minerva projects.** This skill assumes a `.minerva/` project or runs in explicit bare mode; the generic `ship-it` skill is still the right tool when the user is not in a minerva project.
