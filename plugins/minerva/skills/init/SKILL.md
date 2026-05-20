---
name: init
description: Use when the user invokes `minerva:init`, wants to start using minerva in a project for the first time, or needs to scaffold the .minerva/ directory layout. Idempotent — re-runs report per-piece status without rewriting anything in place. Warns about legacy `.minerva/decisions/` layouts.
---

One-time scaffolding for a project. Creates the `.minerva/` directory layout, verifies it's not being gitignored, adds a Routing section to the project's agent file, and offers to commit the scaffold.

## Usage

- `minerva:init` — scaffold the current project root. No arguments.

## Pre-flight detection

Before changing anything, inspect the project:

1. **Project root** is the current working directory.
2. **Already initialized?** Look for `.minerva/`. If it exists, you're in idempotent mode — report what's already there (folder ✓, gitignore ✓, agent file(s) ✓, knowledge dir ✓) and apply only the missing pieces.
3. **Pre-existing flat layout?** If `work/` or `decisions/` exist at the **project root** (i.e. someone used a pre-`.minerva/` version of minerva, or set up the directories manually), do **not** touch them. Report:
   ```
   Detected a pre-existing flat layout at <paths>. minerva:init won't migrate it automatically.
   To move to the .minerva/ layout, run:
     mv work .minerva/work && mv decisions .minerva/knowledge
   ```
   Continue with the rest of `minerva:init` (folder creation, gitignore check, agent file). The flat-layout warning is informational.
4. **Legacy nested `decisions/` directory?** If `.minerva/decisions/` exists (the directory was renamed to `.minerva/knowledge/` in an earlier minerva version), do **not** touch it. Report:
   ```
   Detected legacy .minerva/decisions/ — minerva renamed this to .minerva/knowledge/ but the old directory is still here.
   No skill reads .minerva/decisions/ anymore. To migrate:
     mv .minerva/decisions/* .minerva/knowledge/  # then renumber if needed
     rmdir .minerva/decisions
   Review for NNN collisions across the two directories before merging.
   ```
   Continue with the rest of `minerva:init`. This warning is informational.
5. **Git repo?** If `.git/` is absent, skip the gitignore check entirely and silently. Still scaffold the folder and update the agent file.

## Step 1 — scaffold `.minerva/`

If `.minerva/` doesn't exist, create:

- `.minerva/work/`
- `.minerva/work/.gitkeep` (empty file, so git tracks the empty directory)
- `.minerva/knowledge/`
- `.minerva/knowledge/.gitkeep` (empty file)

If `.minerva/` already exists, skip whichever pieces are already in place. Don't overwrite existing `.gitkeep` files.

## Step 2 — gitignore check

(Skip in a non-git repo.)

Read `.gitignore` at the project root and any nested `.gitignore` files that would apply to `.minerva/`. Look for patterns that would exclude `.minerva` or `.minerva/` or `.*` (the common dotfile-catchall). Note: `.minerva/worktrees/` is **expected** to be gitignored (added by `minerva:work` on first run) — only flag patterns that would exclude `.minerva/knowledge/` or `.minerva/work/`.

- If a matching pattern is found, report the offending file path, line number, and the offending pattern. **Do not auto-edit** `.gitignore` — that file is user territory. Suggest the user remove or narrow the pattern, since `.minerva/knowledge/` and `.minerva/work/` are intended to be committed.
- If none found, report `gitignore ✓`.

## Step 3 — agent-file detection + Routing

Check for the canonical agent files at the project root, in this order: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`.

- For **each file that exists**, add a `## minerva` Routing section if one isn't already present. If the section is already present, leave the file alone and report `<file> ✓`.
- If **none of the three exist**, ask the user which to create:
  - `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or **Other** (the user supplies a filename).
  - For **Other**, the user provides a filename; the same Routing section is appended to that file (created empty first). The user can flesh out the rest later.
  - Wait for the answer before creating anything.

### Routing section content

Use this exact template (verbatim, with the appended blank line at the end for readability):

```markdown
## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/` — concrete, past-tense knowledge artifacts: decisions made, bugs fixed, patterns discovered. Read when starting work in this repo.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill (via the `Skill` tool) for the full methodology.
```

Append the Routing section at the end of the file (don't try to find a "right" spot — end is fine and is easy to detect on re-runs).

### Detecting existing Routing section

A re-run is detected by checking the file for a line matching the exact heading `## minerva`, followed within the **next 4 lines** by either the literal substring `.minerva/knowledge/` or `.minerva/decisions/` (the old name, kept for projects initialized before the rename). Both signals are required — the heading alone is too generic.

If the heading appears multiple times in the file, only the first occurrence is checked. (Unlikely in practice; if a user has multiple `## minerva` headings, the file is hand-managed and `init` should not touch it — surface a warning instead of writing.)

## Step 4 — commit offer

(Skip in a non-git repo.)

If any files were newly created in steps 1–3, offer to commit them:

> "Created `.minerva/{work,knowledge}` + Routing section in `<files>`. Stage and commit now?"

If the user agrees:
```
git add .minerva/ <agent files modified>
git commit -m "chore: scaffold minerva and routing section"
```

Use specific paths only — never `-A` or `.`. If the user declines, leave the changes in the working tree.

## Step 5 — report

Print a status block:

```
.minerva/ layout       ✓ created (or: already present)
.gitignore             ✓ ok       (or: skipped — not a git repo; or: ⚠ <pattern at file:line> would exclude .minerva/)
CLAUDE.md              ✓ Routing section added (or: ✓ already present; or: — not present)
AGENTS.md              ✓ Routing section added (or: ✓ already present; or: — not present)
GEMINI.md              ✓ Routing section added (or: ✓ already present; or: — not present)
flat layout            — none detected (or: ⚠ work/ and/or decisions/ at root — see message above)
legacy decisions/      — none detected (or: ⚠ .minerva/decisions/ — see message above)
commit                 ✓ committed (or: declined; or: — nothing to commit)
```

Suggest `minerva:propose` as the next step if no work units exist yet.

## Out of scope

- Migrating a pre-existing flat `work/` + `decisions/` layout. `minerva:init` only reports it; the user runs the `mv` themselves.
- Migrating `.minerva/decisions/` to `.minerva/knowledge/`. Same — report only, user runs the move.
- Authoring or rewriting CLAUDE.md / AGENTS.md content beyond the Routing section.
- Editing `.gitignore` to remove offending patterns.
- A `minerva:init --refresh` mode to rewrite the Routing section when its template changes. Out of scope for v1.
