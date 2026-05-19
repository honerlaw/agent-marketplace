---
name: propose
description: Use when the user invokes `minerva:propose`, asks to start a new unit of work, or wants to plan/design a new feature, refactor, or investigation for a minerva-tracked project. Runs a brainstorm-style intake flow, asks clarifying questions one at a time, proposes 2–3 approaches, presents the design in sections, and writes the approved design to .minerva/work/NNN-<slug>/proposal.md.
---

Start a new work unit by brainstorming and writing its proposal.

## Usage

- `minerva:propose` — brainstorms a new work unit; infers intent from current-session context, or asks if context is blank
- `minerva:propose "add rate limiting"` — inline description used as the starting point for Q&A

## Pre-flight check

If `.minerva/` doesn't exist yet at the project root, suggest the user run `minerva:init` first so the directory layout and agent-file Routing section are in place. You can still write the proposal without it, but `minerva:init` is the cleaner entry point.

## Protocol

This skill mirrors the `superpowers:brainstorming` flow but writes to `.minerva/work/NNN-<slug>/proposal.md` instead of a generic spec path.

1. **Context-sensitive intake.** Determine what the user wants to build before asking clarifying questions:
   - If a description was passed inline → treat it as the draft goal; skip the "what do you want to build?" question and confirm/refine it.
   - If no description but current-session chat history is present → read the history and repo structure, state the inferred intent ("Based on our conversation, it sounds like you want to X — is that right?"), and let the user confirm or redirect.
   - If no description and no relevant current-session history → ask "What would you like to build?"

2. **Explore project context.** Read `CLAUDE.md` / `AGENTS.md` if present, skim `.minerva/knowledge/`, glance at recent `.minerva/work/NNN-*/proposal.md` files for tone and conventions. This informs the questions you'll ask.

3. **Ask clarifying questions one at a time.** Cover purpose, constraints, and success criteria. Prefer multiple-choice. Don't batch.

4. **Propose 2–3 approaches** with tradeoffs and a recommendation. Lead with the recommendation. Iterate based on user feedback.

5. **Present the design in sections** (Goal, Why, Approach, Open Questions). Get approval per section before moving on.

6. **Hard gate:** do not write any file until the user has explicitly approved the design.

## On approval — file writes

1. Derive the slug silently from the confirmed goal title: lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

2. Check for a duplicate: if `.minerva/work/` already contains an entry matching the derived slug (any `.minerva/work/NNN-<slug>/`), do **not** write. Tell the user the existing path and suggest `minerva:replan` if they want to course-correct an in-flight work unit.

3. Compute the next NNN under `.minerva/work/`:
   - List entries matching `^[0-9]{3}-` in `.minerva/work/`.
   - Take `max + 1`, padded to 3 digits.
   - If `.minerva/work/` doesn't exist, create it and start at `001`.

4. Create `.minerva/work/NNN-<slug>/`.

5. Write `proposal.md` using the approved content, structured as:

   ```markdown
   # Proposal: <slug>

   **Date**: YYYY-MM-DD
   **Status**: Draft

   ## Goal
   <approved goal>

   ## Why
   <approved motivation>

   ## Approach
   <approved approach — will be rewritten by /promote to describe what shipped>

   ## Open Questions
   - <any remaining items>
   ```

6. Write `scratchpad.md` with this header and nothing else:

   ```markdown
   # Scratchpad: <slug>

   > **Ephemeral working memory.** Most of what lands here is noise — small
   > decisions that don't matter, dead ends, momentary confusion. At feature
   > completion, run `minerva:promote`: significant items get promoted to
   > `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
   > the raw scratchpad is archived.

   ```

7. Report the created path (including the derived slug). Suggest `minerva:work` as the next step.

## Out of scope

This skill stops at writing the files. It does **not** invoke any implementation skill — `minerva:work` is the next phase.
