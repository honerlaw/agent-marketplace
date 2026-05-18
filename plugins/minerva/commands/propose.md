---
description: Brainstorm-style proposal authoring for a new unit of work. Asks clarifying questions one at a time, proposes 2-3 approaches with tradeoffs, presents the design in sections, and writes the approved design to work/NNN-slug/proposal.md.
---

Start a new work unit by brainstorming and writing its proposal.

## Usage

- `/propose add-payments` — brainstorms a new work unit, writes `work/NNN-add-payments/proposal.md`
- `/propose "rate limit overhaul"` — same; slug is normalized

## Slug normalization

Lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

## Pre-flight check

If `work/` already contains an entry matching the normalized slug (any `work/NNN-<slug>/`), do **not** start a new proposal. Tell the user the existing path and suggest `/replan` if they want to course-correct an in-flight work unit.

## Protocol

This command mirrors the `superpowers:brainstorming` flow but writes to `work/NNN-<slug>/proposal.md` instead of a generic spec path.

1. **Explore project context first.** Read `CLAUDE.md` if present, skim `decisions/`, glance at recent `work/NNN-*/proposal.md` files for tone and conventions. This informs the questions you'll ask.
2. **Ask clarifying questions one at a time.** Cover purpose, constraints, and success criteria. Prefer multiple-choice. Don't batch.
3. **Propose 2–3 approaches** with tradeoffs and a recommendation. Lead with the recommendation. Iterate based on user feedback.
4. **Present the design in sections** (Goal, Why, Approach, Open Questions). Get approval per section before moving on.
5. **Hard gate:** do not write any file until the user has explicitly approved the design.

## On approval — file writes

1. Compute the next NNN under `work/`:
   - List entries matching `^[0-9]{3}-` in `work/`.
   - Take `max + 1`, padded to 3 digits.
   - If `work/` doesn't exist, create it and start at `001`.
2. Create `work/NNN-<slug>/`.
3. Write `proposal.md` using the approved content, structured as:

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

4. Write `scratchpad.md` with this header and nothing else:

   ```markdown
   # Scratchpad: <slug>

   > **Ephemeral working memory.** Most of what lands here is noise — small
   > decisions that don't matter, dead ends, momentary confusion. At feature
   > completion, run `/promote`: significant items get promoted to
   > `decisions/`, `proposal.md` gets updated to match reality, and the raw
   > scratchpad is archived.

   ```

5. Report the created path. Suggest `/work` as the next step.

## Out of scope

This command stops at writing the files. It does **not** invoke any implementation skill — `/work` is the next phase.
