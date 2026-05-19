---
description: Extract durable decisions and finalize a work unit. No argument runs the end-of-work full pass (promote significant scratchpad items to .minerva/decisions/, rewrite proposal.md to match reality, archive the raw scratchpad). With an argument, promotes a single mid-work item. Idempotent.
---

Promote durable items from `scratchpad.md` to `.minerva/decisions/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* If yes, promote. If no, discard. Scratchpads almost always fail; decisions almost always pass; proposals are between.

## Target resolution

Same as `/replan` and `/work`:
1. Exact directory match: `.minerva/work/<arg>/`.
2. Substring match against `.minerva/work/NNN-*/`; single match wins.
3. No argument → most-recently-modified `.minerva/work/NNN-*/`.
4. `.minerva/work/` missing or empty → report and stop.

## Two modes

### Mode A — no argument (end-of-work full pass)

1. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
2. **Idempotency check:** if `scratchpad.md` is the one-line `Summarized at /promote on YYYY-MM-DD — see archive/.` marker, report "already promoted" and stop.
3. Propose a three-way partition of the scratchpad entries:
   - **PROMOTE** → durable architectural/design choices, surprising constraints, tradeoffs worth recording, gotchas a future reader needs.
   - **MERGE INTO PROPOSAL** → places where the actual approach diverged from the original; the proposal's `## Approach` must end up describing what got built.
   - **DISCARD** → dead ends, momentary confusion, debugging digressions, choices that don't matter.
   Skip entries already marked `→ promoted to .minerva/decisions/...` — they were promoted mid-work.
4. Present the partition as a numbered list with each entry's classification and a one-line justification. Wait for confirmation or edits.
5. **Hard gate:** do not write files until the user confirms.
6. On confirmation:
   - **For each PROMOTE item:** write `.minerva/decisions/NNN-<slug>.md` using the decision template below. Auto-increment NNN across the whole `.minerva/decisions/` directory (3-digit pad). If `.minerva/decisions/` doesn't exist, create it and start at `001`. Each entry must stand alone.
   - **Rewrite `proposal.md`:** the `## Approach` section (and any other section that's out of date) describes reality, not the original plan. Don't preserve obsolete planning prose just because it was there.
   - **Archive the scratchpad:** create `.minerva/work/<target>/archive/` if needed, move `scratchpad.md` to `archive/scratchpad.md`, then write a new `scratchpad.md` containing exactly:
     ```
     Summarized at /promote on YYYY-MM-DD — see archive/.
     ```
7. Report: items promoted (with paths), whether the proposal was updated and a one-line summary of the change, scratchpad disposition.

### Mode B — with argument (single-item mid-work promote)

`/promote "use postgres listen/notify for cache invalidation"`

1. Read `scratchpad.md`.
2. Locate the block matching the argument (substring or fuzzy match on the entry text). If multiple candidates, list them and ask which.
3. **Idempotency check:** if the matched block already has a `→ promoted to .minerva/decisions/...` trailing line, report the existing decision file path and stop.
4. Confirm with the user that you've identified the right block and show the proposed decision entry. Wait for approval.
5. On approval:
   - Determine the next NNN under `.minerva/decisions/` (max+1, 3-digit pad; start at `001` if dir is missing).
   - Write `.minerva/decisions/NNN-<slug>.md` using the decision template.
   - In `scratchpad.md`, append `→ promoted to .minerva/decisions/NNN-<slug>.md` to the matched block so the end-of-work pass won't re-promote it.
6. Report the decision file path.

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing decision file → stops early.
- Decision files are never overwritten — auto-incremented NNN guarantees uniqueness.

If a user manually edits the scratchpad to remove markers, re-running `/promote` could duplicate entries. This is a known footgun; not defended against.

## Decision entry template

```markdown
# <Short, declarative title — what was decided>

**Date**: YYYY-MM-DD
**Context**: .minerva/work/NNN-<slug>

## Context
The situation that forced this choice. Constraints, prior state, or the
problem we hit. Enough that a reader cold to the project understands why
this was even a question.

## Decision
What we chose. Stated as a declarative.

## Consequences
What this implies going forward — invariants other code now relies on,
things future work has to honor, tradeoffs we accepted.
```
