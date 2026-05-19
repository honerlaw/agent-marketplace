---
name: promote
description: Use when the user invokes `minerva:promote`, implementation on a work unit is done and they want to finalize the record, or a significant mid-work decision/bug/pattern should be captured immediately. Promotes durable knowledge to .minerva/knowledge/, rewrites proposal.md to match reality, and archives the scratchpad. Idempotent.
---

Promote durable items from `scratchpad.md` to `.minerva/knowledge/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* Only concrete, past-tense facts qualify — things that happened, were decided, were fixed, or were discovered. If yes, promote. If no, discard. Scratchpads almost always fail; concrete past-tense facts almost always pass; proposals are between.

## Target resolution

Same as `minerva:replan` and `minerva:work`:
1. Check current-session chat history for a mentioned work unit. If one is clearly referenced, use it.
2. Fall back to the most-recently-modified `.minerva/work/NNN-*/` by directory mtime.
3. If multiple candidates and context is ambiguous, list them and ask.
4. `.minerva/work/` missing or empty → report and stop.

## Two modes

### Mode A — no argument (end-of-work full pass)

1. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
2. **Idempotency check:** if `scratchpad.md` is the one-line `Summarized at minerva:promote on YYYY-MM-DD — see archive/.` marker, report "already promoted" and stop.
3. Propose a three-way partition of the scratchpad entries:
   - **PROMOTE** → concrete, past-tense knowledge: architectural/design choices made, bugs fixed (if the fix is non-obvious or the root cause could recur), discovered failure patterns, surprising constraints, gotchas a future reader needs.
   - **MERGE INTO PROPOSAL** → places where the actual approach diverged from the original; the proposal's `## Approach` must end up describing what got built.
   - **DISCARD** → forward-looking TODOs, future investigation notes, "we should do X later" items (regardless of how valuable they sound), dead ends, momentary confusion, debugging digressions, choices that don't matter.
   Skip entries already marked `→ promoted to .minerva/knowledge/...` — they were promoted mid-work.
4. Present the partition as a numbered list with each entry's classification and a one-line justification. Wait for confirmation or edits.
5. **Hard gate:** do not write files until the user confirms.
6. On confirmation:
   - **For each PROMOTE item:** determine its type (`decision`, `bug`, `pattern`, or `constraint`) and write `.minerva/knowledge/NNN-<type>-<slug>.md` using the knowledge entry template below. Auto-increment NNN across the whole `.minerva/knowledge/` directory (3-digit pad). If `.minerva/knowledge/` doesn't exist, create it and start at `001`. Each entry must stand alone.
   - **Rewrite `proposal.md`:** the `## Approach` section (and any other section that's out of date) describes reality, not the original plan. Don't preserve obsolete planning prose just because it was there.
   - **Archive the scratchpad:** create `.minerva/work/<target>/archive/` if needed, move `scratchpad.md` to `archive/scratchpad.md`, then write a new `scratchpad.md` containing exactly:
     ```
     Summarized at minerva:promote on YYYY-MM-DD — see archive/.
     ```
7. Report: items promoted (with paths), whether the proposal was updated and a one-line summary of the change, scratchpad disposition.

### Mode B — with argument (single-item mid-work promote)

`minerva:promote "empty queue causes null pointer in the retry handler"`

1. Read `scratchpad.md`.
2. Locate the block matching the argument (substring or fuzzy match on the entry text). If multiple candidates, list them and ask which.
3. **Idempotency check:** if the matched block already has a `→ promoted to .minerva/knowledge/...` trailing line, report the existing file path and stop.
4. Confirm with the user that you've identified the right block and show the proposed knowledge entry. Wait for approval.
5. On approval:
   - Determine the type (`decision`, `bug`, `pattern`, or `constraint`) and the next NNN under `.minerva/knowledge/` (max+1, 3-digit pad; start at `001` if dir is missing).
   - Write `.minerva/knowledge/NNN-<type>-<slug>.md` using the knowledge entry template.
   - In `scratchpad.md`, append `→ promoted to .minerva/knowledge/NNN-<type>-<slug>.md` to the matched block so the end-of-work pass won't re-promote it.
6. Report the knowledge file path.

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing knowledge file → stops early.
- Knowledge files are never overwritten — auto-incremented NNN guarantees uniqueness.

If a user manually edits the scratchpad to remove markers, re-running `minerva:promote` could duplicate entries. This is a known footgun; not defended against.

## Knowledge entry template

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint
**Context**: .minerva/work/NNN-<slug>

## Context
The situation that led to this entry. Constraints, prior state, or the
problem that was hit. Enough that a reader cold to the project understands
why this matters.

## Finding
What was decided, fixed, learned, or observed — stated as a declarative.
For bugs: what the root cause was and how it was fixed. For patterns: what
the recurring behavior is and when it appears. For decisions: what was
chosen. For constraints: what the limit is and where it comes from.

## Implications
What this means going forward — invariants other code now relies on,
things future work has to honor, gotchas to watch for, tradeoffs accepted.
```
