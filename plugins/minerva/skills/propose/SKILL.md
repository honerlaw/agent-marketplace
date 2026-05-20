---
name: propose
description: Use when the user invokes `minerva:propose`, asks to start a new unit of work, or wants to plan/design a new feature, refactor, or investigation for a minerva-tracked project. Runs a brainstorm-style intake flow, asks clarifying questions one at a time, proposes 2–3 approaches, presents the design in sections, writes the approved design to .minerva/work/NNN-<slug>/proposal.md, then runs a self-review and a post-write user gate.
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

2. **Scope check.** Before asking clarifying questions, decide whether the request fits a single work unit. If it spans multiple independent subsystems ("build a platform with chat, billing, analytics", "rewrite the entire data layer"), surface this immediately and help the user decompose into smaller work units. Each sub-unit gets its own `minerva:propose` run. Do not produce a 500-line proposal for work that should be three separate units.

3. **Explore project context.** Read `CLAUDE.md` / `AGENTS.md` if present, skim `.minerva/knowledge/` (and `.minerva/decisions/` if it still exists — legacy directory), glance at recent `.minerva/work/NNN-*/proposal.md` files for tone and conventions. This informs the questions you'll ask.

4. **Ask clarifying questions one at a time.** Cover purpose, constraints, and success criteria. Prefer multiple-choice. Don't batch.

5. **Propose 2–3 approaches** with tradeoffs and a recommendation. Lead with the recommendation. Iterate based on user feedback.

6. **Present the design in sections** (Goal, Why, Approach, Success criteria, Open Questions). Get approval per section before moving on.

7. **Pre-write hard gate:** do not write any file until the user has explicitly approved every section.

## On approval — file writes

1. Derive the slug silently from the confirmed goal title: lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

2. **Duplicate slug check** — look for `.minerva/work/NNN-<slug>/` on disk and also for any branch named `*-<slug>` (`git branch --list "*-<slug>"`, `git branch -r --list "*-<slug>"`). If found, do **not** write. Tell the user the existing path / branch and suggest `minerva:replan` if they want to course-correct an in-flight work unit.

3. **Compute the next NNN** by scanning **all three** sources so parallel work in worktrees and remotes doesn't collide:

   ```
   # local work directory
   ls -1 .minerva/work/ | grep -E '^[0-9]{3}-'

   # local branches (catches in-flight worktrees whose docs left .minerva/work/)
   git branch --list '[0-9][0-9][0-9]-*' --format '%(refname:short)'
   git branch --list 'minerva/[0-9][0-9][0-9]-*' --format '%(refname:short)'

   # remote branches (catches work shipped from elsewhere)
   git ls-remote --heads origin '[0-9][0-9][0-9]-*' 2>/dev/null
   git ls-remote --heads origin 'minerva/[0-9][0-9][0-9]-*' 2>/dev/null
   ```

   Parse the 3-digit prefix from each, take the max across all sources, add 1, pad to 3 digits. If none exist, start at `001`. Skip the git steps cleanly in a non-git repo or when offline (treat the source as empty).

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
   <approved approach — will be rewritten by minerva:promote to describe what shipped>

   ## Success criteria
   - <concrete, checkable item 1>
   - <concrete, checkable item 2>
   <each item must be objectively answerable yes/no when implementation is "done">

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

7. **Self-review the written proposal.** Re-read `proposal.md` with fresh eyes and fix inline:
   - **Placeholders** — any `TBD`, `TODO`, vague phrasing, or incomplete sections.
   - **Internal consistency** — does `## Approach` actually achieve `## Goal`? Do `## Success criteria` cover what `## Goal` promises?
   - **Ambiguity** — could any requirement be read two different ways? Pick one and make it explicit.
   - **Scope** — is this still a single work unit, or did the prose drift into multi-unit territory? If the latter, stop and re-decompose with the user.

   Fix issues inline. No need to re-review — just fix and move on.

8. **Post-write user gate.** Report the created path and ask:

   > "Proposal written to `.minerva/work/NNN-<slug>/proposal.md`. Please review the file directly and let me know if you want to change anything before we start work."

   Wait for the user's response. If they request changes, edit `proposal.md` directly and re-run the self-review. Only once the user approves the written file is the proposal considered final.

9. Suggest `minerva:work` as the next step.

## Out of scope

This skill stops at writing and confirming the files. It does **not** invoke any implementation skill — `minerva:work` is the next phase.
