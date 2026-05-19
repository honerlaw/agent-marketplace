---
name: work
description: Use when the user invokes `minerva:work`, asks to implement or resume a minerva work unit, or is ready to start coding on a proposed feature. Reads the proposal and any replans, maintains a live scratchpad, and auto-invokes the minerva:replan protocol when reality drifts in a load-bearing way.
---

Implement the active work unit while maintaining the scratchpad and honoring the persistence hierarchy.

## Usage

- `minerva:work` — resume the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous

## Target resolution

1. Check current-session chat history for a mentioned work unit (e.g. a unit name, slug, or path that appeared in conversation). If one is clearly referenced, use it.
2. Fall back to the most-recently-modified `.minerva/work/NNN-*/` by directory mtime — check **both** `.minerva/work/` on `main` and `.minerva/worktrees/NNN-*/` (docs move to the worktree on first invocation).
3. If multiple candidates exist and context is ambiguous, list them and ask the user which to target.
4. `.minerva/work/` missing or empty and no worktrees exist → report "no work units found — run `minerva:propose` first" and stop.

## Worktree setup (run once per work unit, before Setup)

Every work unit runs in an isolated git worktree. This section runs **before** reading docs.

1. **Determine NNN-slug** from the resolved target (e.g. `005-work-in-git-worktree`).

2. **Check for an existing worktree** at `.minerva/worktrees/NNN-slug/`.
   - **Exists** → the worktree is already initialized. Switch to it (treat it as the working directory for all subsequent steps) and continue to Setup.
   - **Does not exist** → proceed with steps 3–6.

3. **Ensure `.minerva/worktrees/` is gitignored** on `main`. If `.gitignore` does not already contain `.minerva/worktrees/`, append it and commit:
   ```
   git add .gitignore
   git commit -m "chore: ignore .minerva/worktrees/ directory"
   ```

4. **Create the worktree and branch:**
   ```
   git worktree add -b NNN-slug .minerva/worktrees/NNN-slug
   ```

5. **Move the work unit docs** from `.minerva/work/NNN-slug/` into the worktree:
   ```
   mkdir -p .minerva/worktrees/NNN-slug/.minerva/work
   mv .minerva/work/NNN-slug .minerva/worktrees/NNN-slug/.minerva/work/NNN-slug
   ```

6. **Commit the docs on the branch** (inside the worktree):
   ```
   git -C .minerva/worktrees/NNN-slug add .minerva/work/NNN-slug/
   git -C .minerva/worktrees/NNN-slug commit -m "chore: initialize NNN-slug work unit"
   ```

7. All subsequent work — reading docs, writing scratchpad, implementation — happens inside `.minerva/worktrees/NNN-slug/`.

## Setup (run at the start of every `minerva:work` invocation)

All paths below are relative to the worktree root (`.minerva/worktrees/NNN-slug/`).

1. Read `.minerva/work/NNN-slug/proposal.md`.
2. Read **all** `.minerva/work/NNN-slug/replan.md` entries chronologically. When the latest replan conflicts with the original proposal, the replan wins.
3. Read `.minerva/work/NNN-slug/scratchpad.md` to figure out where work left off.
4. Glance at `git status` and the last 3 commits (run from inside the worktree) to corroborate.
5. **Summarize the resumption point** to the user in one short paragraph before doing anything else: what the goal is, what's been done, what's next. Confirm before proceeding.

## Implementation protocol — apply throughout the session

### Scratchpad maintenance

As you work, log to `scratchpad.md`. The bar for an entry is: **a future-self might want to see this**. Examples:

- An approach that was tried and dropped (with why)
- A surprising constraint or gotcha
- A decision that might be durable but isn't yet certain
- A breadcrumb pointing at code you'll return to

**Do not** log:
- A transcript of every action
- Tactical implementation details that the diff already shows
- Routine debugging steps

The scratchpad is **ephemeral working memory**. `minerva:promote` will later partition it into "promote / merge into proposal / discard." Keep signal-to-noise high.

### Divergence detection

Continuously check: does the approach I'm taking still match `proposal.md` (as superseded by the latest `replan.md`)?

**Auto-trigger the `minerva:replan` protocol** when reality diverges in a load-bearing way:
- A core assumption from the proposal turns out to be wrong.
- The approach itself is changing (not just an implementation detail within the approach).
- Scope is shifting (in or out of the work unit).

**Do not trigger** for:
- Routine implementation choices (which library, which helper to extract, how to structure a function).
- Small refactors along the way.
- Edge-case handling that wasn't in the proposal but doesn't change the approach.

**On trigger:** pause implementation. Tell the user "this looks like a load-bearing divergence — running the replan protocol." Then invoke the `minerva:replan` skill and follow its protocol. Once the replan entry is written, resume implementation with the new plan in context.

### Completion signal

When you believe implementation is done (the proposal's success criteria are met, any tests pass, the visible scope is delivered), surface `minerva:promote` as the next step. Do not run it automatically — that's the user's call.

## Out of scope

`minerva:work` is a setup-and-protocol skill, not a one-shot operation. After the initial resumption summary it hands control back to normal conversation; the protocols above apply for the rest of the session.
