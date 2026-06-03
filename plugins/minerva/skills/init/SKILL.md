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
- `.minerva/knowledge/index.md` — the knowledge catalog, written with the canonical
  skeleton below (watermark `000`). A non-empty `index.md` already makes the
  directory tracked by git, so **only** create `.minerva/knowledge/.gitkeep` when
  `index.md` is absent (and never both).
- `.minerva/reference/` — the present-tense operational-doc tier (see
  `.minerva/knowledge/011-decision-minerva-reference-tier.md`).
- `.minerva/reference/.gitkeep` (empty file, so git tracks the empty directory)

**Canonical `index.md` skeleton** — `minerva:init` and `minerva:promote` are the two
creators of this file; both emit this **exact** content so they cannot diverge:

```markdown
# Knowledge index
<!-- index-watermark: 000 -->

## Decisions

## Bugs

## Patterns

## Constraints
```

The `index-watermark` is the highest knowledge-entry NNN the catalog reflects
(`000` for a fresh scaffold); it is a content freshness signal preferred over file
mtime (mtime is unreliable across git checkouts and worktrees).

If `.minerva/` already exists, skip whichever pieces are already in place. Don't
overwrite an existing `index.md`, `.gitkeep`, or `.minerva/reference/`.

### Step 1b — index backfill offer (idempotent mode)

If `.minerva/knowledge/` already holds entries (`NNN-<type>-<slug>.md` files) but
`index.md` is missing or empty, **offer** to backfill it:

> "`.minerva/knowledge/` has N entries but no populated `index.md`. Generate the
> catalog from the existing entries now?"

On acceptance, write `index.md` from the canonical skeleton, add one
`- [[NNN-type-slug]] — <≤15-word summary>` line per entry under its Type section
(title from the entry H1, summary condensed from its Finding), and set the watermark
to the max NNN on disk. **Cross-reference backfill** (adding `## Related` blocks
across existing entries) is a separate, judgment-heavy pass — offer it only if the
user asks; it is not part of the index backfill.

## Step 2 — gitignore check

(Skip in a non-git repo.)

Read `.gitignore` at the project root and any nested `.gitignore` files that would apply to `.minerva/`. The check has two parts:

**Part A — flag patterns that would exclude committed dirs.** Look for patterns that would exclude `.minerva` or `.minerva/` or `.*` (the common dotfile-catchall). `.minerva/knowledge/` and `.minerva/work/` are intended to be committed.

- If a matching pattern is found, report the offending file path, line number, and the offending pattern. **Do not auto-edit** `.gitignore` to remove user-authored patterns — that file is user territory. Suggest the user remove or narrow the pattern.
- If none found, report `gitignore ✓ (committed dirs)`.

**Part B — install `.minerva/worktrees/` if missing.** Every worktree created by `minerva:propose` lives under `.minerva/worktrees/` and must be ignored on the default branch (see `.minerva/knowledge/005-decision-gitignore-before-worktree.md`). Init installs this entry up front so propose doesn't have to modify `.gitignore` from inside a worktree later.

- If `.gitignore` does not already contain a line matching `.minerva/worktrees/` (exact match, or a parent pattern like `.minerva/` — both effectively ignore the path), append `.minerva/worktrees/` to the end of the project-root `.gitignore` (create the file if it doesn't exist). Report `gitignore: added .minerva/worktrees/`.
- If already present, report `gitignore ✓ (worktrees ignored)`.

Unlike Part A, this entry is appended automatically — it's part of init's idempotent scaffold, not user territory.

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

- `.minerva/knowledge/` — concrete, past-tense knowledge artifacts: decisions made, bugs fixed, patterns discovered. Start from `.minerva/knowledge/index.md` (the catalog). Read when starting work in this repo.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill (via the `Skill` tool) for the full methodology.
```

Append the Routing section at the end of the file (don't try to find a "right" spot — end is fine and is easy to detect on re-runs).

### Detecting existing Routing section

A re-run is detected by checking the file for a line matching the exact heading `## minerva`, followed within the **next 6 lines** by either the literal substring `.minerva/knowledge/` or `.minerva/decisions/` (the old name, kept for projects initialized before the rename). Both signals are required — the heading alone is too generic. (The window is 6, not 4, to accommodate the `.minerva/reference/` bullet added to the template above without breaking detection on older projects — widening only loosens detection and still requires both signals.)

If the heading appears multiple times in the file, only the first occurrence is checked. (Unlikely in practice; if a user has multiple `## minerva` headings, the file is hand-managed and `init` should not touch it — surface a warning instead of writing.)

## Step 4 — commit offer

(Skip in a non-git repo.)

If any files were newly created in steps 1–3, offer to commit them:

> "Created `.minerva/{work,knowledge,reference}` (incl. `knowledge/index.md`) + Routing section in `<files>`. Stage and commit now?"

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
.minerva/knowledge/index.md  ✓ scaffolded (or: ✓ backfilled from N entries; or: ✓ already present)
.minerva/reference/    ✓ created (or: ✓ already present)
.gitignore             ✓ ok       (or: skipped — not a git repo; or: ⚠ <pattern at file:line> would exclude .minerva/)
.minerva/worktrees/    ✓ added to .gitignore (or: ✓ already ignored; or: — not a git repo)
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
- Editing `.gitignore` to remove offending user-authored patterns. (Init **does** install `.minerva/worktrees/` if missing — that entry is part of the scaffold, not user territory.)
- A `minerva:init --refresh` mode to rewrite the Routing section when its template changes. Out of scope for v1.
