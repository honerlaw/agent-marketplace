---
name: replan
description: Use when the user invokes `minerva:replan`, or when work on a minerva unit has diverged from the proposal in a load-bearing way — a core assumption was wrong, the approach is changing, or scope is shifting. Appends a dated divergence entry to .minerva/work/NNN-slug/replan.md for the current work unit.
---

Append a dated replan entry to the current work unit when reality has diverged from the proposal.

## Usage

- `minerva:replan` — operates on the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous

## Target resolution

1. Check current-session chat history for a mentioned work unit (e.g. a unit name, slug, or path that appeared in conversation). If one is clearly referenced, use it.
2. Fall back to the most-recently-modified `.minerva/work/NNN-*/` by directory mtime.
3. If multiple candidates exist and context is ambiguous, list them and ask the user which to target.
4. If `.minerva/work/` doesn't exist or it's empty, report "no work units found — run `minerva:propose` first" and stop.

## Protocol

Same brainstorming pattern as `minerva:propose`, but framed around divergence:

1. **Read the existing context first.** Read `proposal.md`, any prior `replan.md` entries, and the current `scratchpad.md`. The brainstorm must be grounded in what actually happened.
2. **Frame the replan around three pieces:**
   - **Original plan** — what the proposal (or latest prior replan) said the approach was
   - **What changed** — what was discovered, what broke, what assumption was wrong
   - **New plan** — the revised approach
3. **Ask clarifying questions one at a time** to fill in any of the three pieces that aren't already obvious from the conversation or files.
4. **Propose 2–3 alternative new plans** if the path forward isn't already settled. Iterate.
5. **Present the resulting entry** for approval before writing.
6. **Hard gate:** do not append to the file until the user has approved the entry.

## On approval — file write

1. If `replan.md` doesn't exist yet in the target `.minerva/work/NNN-<slug>/`, create it with this header:

   ```markdown
   # Replan log: <slug>

   ```

2. Append a new entry using this exact template (today's date in `YYYY-MM-DD`):

   ```markdown
   ## YYYY-MM-DD — <short, declarative title>

   **Original plan**: <one or two sentences>
   **What changed**: <what was discovered, what broke, what assumption was wrong>
   **New plan**: <one or two sentences>
   ```

3. Report the path and the title of the appended entry. Suggest resuming `minerva:work` next.

## Out of scope

This skill stops at appending to `replan.md`. It does **not** invoke implementation — return control to `minerva:work` (or its in-progress session) after writing.
