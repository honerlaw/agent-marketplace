---
name: replan
description: Use when the user invokes `minerva:replan`, or when work on a minerva unit has diverged from the proposal in a load-bearing way — a core assumption was wrong, the approach is changing, or scope is shifting. Also use to amend an approved proposal before `minerva:work` starts (pre-work tweaks). Appends a dated divergence entry to .minerva/work/NNN-slug/replan.md for the current work unit.
---

Append a dated replan entry to the current work unit when reality has diverged from the proposal, OR amend an approved proposal pre-work.

## Usage

- `minerva:replan` — operates on the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous
- `minerva:replan 005-add-payments` — operate on the named unit explicitly (slug or path)

## When to use

- **Mid-work divergence** (most common): a core assumption broke, the approach is shifting, scope changed. `minerva:work` auto-triggers this protocol.
- **Pre-work amendment**: the proposal was approved but the user wants to tweak it before implementation starts. Same protocol — the replan entry's `Original plan` is just the freshly written proposal, and `What changed` is "before implementation: user wants to adjust X".

## Target resolution

Same pattern used by `minerva:work`, `minerva:promote`, `minerva:review`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — if the user passed a slug or path, resolve it. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — if a unit slug, path, or branch name has been mentioned in this session, use it.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/`, pick by directory mtime.
4. **Ambiguity** — list candidates, ask the user.
5. **None found** — "no work units found — run `minerva:propose` first" and stop.

## Worktree entry

After resolving the target and before reading or writing any files:

- If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/` and the current session is **not** already in that worktree, call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`.
- If the docs live only on the default branch (a shipped unit being inspected), operate on the parent repo without entering a worktree.
- If the session is already in the matching worktree, do nothing.

This makes the skill robust against being invoked from a stale cwd — all subsequent file paths in this skill are resolved relative to the right working tree.

## Protocol

Same brainstorming pattern as `minerva:propose`, but framed around divergence:

1. **Read the existing context first.** Read `proposal.md`, any prior `replan.md` entries, and the current `scratchpad.md`. The brainstorm must be grounded in what actually happened.
2. **Frame the replan around three pieces:**
   - **Original plan** — what the proposal (or latest prior replan) said the approach was
   - **What changed** — what was discovered, what broke, what assumption was wrong (for pre-work amendments: "user requested adjustment before implementation")
   - **New plan** — the revised approach
3. **Ask clarifying questions one at a time** to fill in any of the three pieces that aren't already obvious from the conversation or files.
4. **Propose 2–3 alternative new plans** if the path forward isn't already settled. Iterate.
5. **Present the resulting entry** for approval before writing.
6. **Hard gate:** do not append to the file until the user has approved the entry.

## On approval — file write

1. If `replan.md` doesn't exist yet in the target work unit, create it with this header:

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

3. **Update Success criteria if the new plan changes them.** If the replan changes what "done" looks like, also edit `proposal.md`'s `## Success criteria` section to reflect the new bar. Otherwise leave it alone — the replan entry will still supersede the proposal on conflict.

4. Report the path and the title of the appended entry. Suggest resuming `minerva:work` next.

## Out of scope

This skill stops at appending to `replan.md` (and optionally editing `proposal.md`'s Success criteria). It does **not** invoke implementation — return control to `minerva:work` (or its in-progress session) after writing.
