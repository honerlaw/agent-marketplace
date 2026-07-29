---
name: ship
description: Ships the current work — commits outstanding changes to a branch, opens a pull request, watches CI without blocking (a tracked watcher that resumes when checks settle, backed by a long scheduled fallback), fixes CI failures, and enables auto-merge. Use when the user asks to ship, push, open a PR for, or merge the current work — closing the minerva lifecycle after `minerva:work` / `minerva:promote` / `minerva:review` — or when they invoke `minerva:ship`.
---

Close the minerva lifecycle by committing outstanding work to a branch, opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop (3 iterations), and enabling auto-merge when repo permissions allow. The watch never blocks the agent and never guesses a polling interval: a detached `gh pr checks --watch` resumes the run when checks actually settle, and a long re-arming `ScheduleWakeup` stays armed underneath so the watch survives a dead watcher, a wedged check, or an ended session.

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

The full step protocols live verbatim in `references/protocol.md` — **read it now, before executing**: **Target resolution** → **Worktree addressing** → **Default-branch detection** → **Branch creation** → **Commit outstanding changes** (Hard gate #1: commit message confirmation) → **Push & open PR** (Hard gate #2: PR title + body confirmation) → **CI watch & auto-fix loop** (detached `gh pr checks --watch` plus an armed re-arming `ScheduleWakeup` fallback; bounded 3-iteration auto-fix) → **Auto-merge** → **Final report**, plus **Lifecycle nudges** and **Worktree handling**.

## Idempotency

Ship does not write its own metadata file or append a `## Shipped` marker to `scratchpad.md`. The PR URL lives on GitHub; nothing minerva-side needs to remember it. Re-running on a branch that already has an open PR will detect that (`gh pr view`) and pick up at the CI-watch step instead of re-creating.

Wake-ups re-invoke `minerva:ship`; the skill detects the existing PR and resumes the watch loop using the iteration count carried in the wake-up prompt.

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote`.
- **Running `minerva:promote` or `minerva:review` automatically.** Only nudges, never auto-invokes — keeps the user in control of what gets promoted and reviewed.
- **Worktree cleanup.** Owned by `minerva:cleanup`.
- **A strict mode** that turns nudges into hard blockers. Deferred; users who want strict ordering can run the skills in order themselves.
- **Replacing `ship-it` for non-minerva projects.** This skill assumes a `.minerva/` project or runs in explicit bare mode; the generic `ship-it` skill is still the right tool when the user is not in a minerva project.
