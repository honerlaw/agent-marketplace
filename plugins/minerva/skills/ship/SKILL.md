---
name: ship
description: Ships the current work — commits outstanding changes to a branch, opens a pull request, watches CI without blocking (a tracked watcher that resumes when checks settle, backed by a long scheduled fallback), fixes CI failures, and enables auto-merge. Use when the user asks to ship, push, open a PR for, or merge the current work — closing the minerva lifecycle after `minerva:work` / `minerva:promote` / `minerva:review` — or when they invoke `minerva:ship`.
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Close the minerva lifecycle by committing outstanding work to a branch, opening a PR titled and described from the active work unit's `proposal.md`, watching CI to green with a bounded auto-fix loop (3 iterations), and enabling auto-merge when repo permissions allow. The host adapter observes CI completion; checkpointed progress supports scheduled re-entry where available and explicit manual resumption elsewhere.

## Usage

- `minerva:ship` — ships the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous, or runs in **bare mode** if no work unit is found
- `minerva:ship 005-add-payments` — ship the named unit explicitly
- `minerva:ship <date-slug> --auto=<orchestrator>` — orchestrated mode; see **Orchestrated mode** below

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator is driving this
run. Act on the argument — never on a judgment about who is calling
(`2026-06-07-decision-phase-handoff-rides-observable-intake`). It does three things:

- **Hard gates #1 and #2** (commit message, PR title + body) accept their drafts without prompting.
- **The CI-watch wake-up carries the caller**, so the orchestrator survives the wait.
- **The final report hands control back to `<orchestrator>`'s Phase 7 — but only when this run
  resumed from ship's own CI-watch wake-up**, because that is precisely when the orchestrator's turn
  already ended and its Phase 6 will never resume. On a synchronous return the orchestrator continues
  to Phase 7 itself. Exactly one of the two paths runs; doing both runs the cleanup gate twice.
  Without the wake-up path the run ends inside ship and the cleanup gate never fires — the failure
  `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` describes.

Absent the argument every gate behaves exactly as written.

## Pre-flight checks

Bail with a clear, one-line message on any failure:

1. **Git repo.** `git rev-parse --is-inside-work-tree` returns true.
2. **`gh` CLI available and authenticated.** `gh auth status` exits 0.
3. **Something to ship.** At least one of:
   - `git status --porcelain` is non-empty (staged, unstaged, or untracked changes), or
   - the current branch has commits ahead of the default branch.
4. **Not a no-op.** If currently on the default branch with zero commits ahead and no local changes, there is nothing to ship — stop.

## Protocol

The full step protocols live verbatim in `references/protocol.md` — **read it now, before executing**: **Target resolution** → **Worktree addressing** → **Phase resolution** (a unit declaring `## Phases` ships one PR per phase; unphased units — the normal case — are unaffected) → **Default-branch detection** → **Branch creation** → **Commit outstanding changes** (Hard gate #1: commit message confirmation) → **Push & open PR** (Hard gate #2: PR title + body confirmation) → **CI watch & auto-fix loop** (tracked `gh pr checks --watch` plus a capability-dependent scheduled/manual resume fallback; bounded 3-iteration auto-fix) → **Auto-merge** → **Final report**, plus **Lifecycle nudges** and **Worktree handling**.

## Idempotency

Ship keeps untracked runtime checkpoints outside the work-unit records and never appends a `## Shipped` marker to `scratchpad.md`. The checkpoint stores the PR number and retry budget; GitHub remains the source of truth for PR state. Re-running on a branch that already has an open PR will detect that (`gh pr view`) and pick up at the CI-watch step instead of re-creating.

Scheduled or manual resumes re-invoke `minerva:ship`; the skill detects the existing PR and resumes using the persisted iteration count, validated against the resume prompt.

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote`.
- **Running `minerva:promote` or `minerva:review` automatically.** Only nudges, never auto-invokes — keeps the user in control of what gets promoted and reviewed.
- **Worktree cleanup.** Owned by `minerva:cleanup`.
- **A strict mode** that turns nudges into hard blockers. Deferred; users who want strict ordering can run the skills in order themselves.
- **Replacing `ship-it` for non-minerva projects.** This skill assumes a `.minerva/` project or runs in explicit bare mode; the generic `ship-it` skill is still the right tool when the user is not in a minerva project.
