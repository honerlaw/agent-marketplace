---
description: Capture a divergence from the proposal in the current work unit. Same brainstorm-style flow as /propose, but appends a dated entry to .minerva/work/NNN-slug/replan.md rather than starting a new work unit.
---

Append a dated replan entry to the current work unit when reality has diverged from the proposal.

## Usage

- `/replan` — operates on the most-recently-modified `.minerva/work/NNN-*/`
- `/replan 003-add-payments` — explicit work directory
- `/replan add-payments` — substring match against existing work dirs

## Target resolution

1. If the user passed an exact directory name (e.g. `003-add-payments`), use `.minerva/work/<that>/`.
2. Otherwise substring match against existing `.minerva/work/NNN-*/` entries. If exactly one match, use it; if multiple, list them and ask which.
3. If no argument, use the most-recently-modified `.minerva/work/NNN-*/` by directory mtime.
4. If `.minerva/work/` doesn't exist or it's empty, report "no work units found — run `/propose <slug>` first" and stop.

## Protocol

Same brainstorming pattern as `/propose`, but framed around divergence:

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

3. Report the path and the title of the appended entry. Suggest resuming `/work` next.

## Out of scope

This command stops at appending to `replan.md`. It does **not** invoke implementation — return control to `/work` (or its in-progress session) after writing.
