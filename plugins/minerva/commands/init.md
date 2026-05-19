---
description: Scaffold the .minerva/ directory layout for a project and add a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md). Idempotent — re-runs report per-piece status without rewriting anything in place. Run once per project before /propose.
---

One-time scaffolding for a project. Creates the `.minerva/` directory layout, verifies it's not being gitignored, and adds a Routing section to the project's agent file so other LLMs landing in the repo know where to look for prior context.

## Usage

- `/init` — scaffold the current project root. No arguments.

## Pre-flight detection

Before changing anything, inspect the project:

1. **Project root** is the current working directory.
2. **Already initialized?** Look for `.minerva/`. If it exists, you're in idempotent mode — report what's already there (folder ✓, gitignore ✓, agent file(s) ✓) and apply only the missing pieces.
3. **Pre-existing flat layout?** If `work/` or `decisions/` exist at the project root (i.e. someone used a pre-`.minerva/` version of minerva, or set up the directories manually), do **not** touch them. Report:
   ```
   Detected a pre-existing flat layout at <paths>. /init won't migrate it automatically.
   To move to the .minerva/ layout, run:
     mv work .minerva/work && mv decisions .minerva/decisions
   ```
   Continue with the rest of `/init` (folder creation, gitignore check, agent file). The flat-layout warning is informational.
4. **Git repo?** If `.git/` is absent, skip the gitignore check entirely and silently. Still scaffold the folder and update the agent file.

## Step 1 — scaffold `.minerva/`

If `.minerva/` doesn't exist, create:

- `.minerva/work/`
- `.minerva/work/.gitkeep` (empty file, so git tracks the empty directory)
- `.minerva/decisions/`
- `.minerva/decisions/.gitkeep` (empty file)

If `.minerva/` already exists, skip whichever pieces are already in place. Don't overwrite existing `.gitkeep` files.

## Step 2 — gitignore check

(Skip in a non-git repo.)

Read `.gitignore` at the project root and any nested `.gitignore` files that would apply to `.minerva/`. Look for patterns that would exclude `.minerva` or `.minerva/` or `.*` (the common dotfile-catchall).

- If a matching pattern is found, report the offending file path, line number, and the offending pattern. **Do not auto-edit** `.gitignore` — that file is user territory. Suggest the user remove or narrow the pattern, since `.minerva/` is intended to be committed.
- If none found, report `gitignore ✓`.

## Step 3 — agent-file detection + Routing

Check for the canonical agent files at the project root, in this order: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`.

- For **each file that exists**, add a `## minerva` Routing section if one isn't already present. If the section is already present, leave the file alone and report `<file> ✓`.
- If **none of the three exist**, ask the user which to create. Offer the three options plus an "Other" path. Wait for the answer. Create the chosen file containing only the Routing section (the user can flesh out the rest of the agent file later).

### Routing section content

Use this exact template (verbatim, with the appended blank line at the end for readability):

```markdown
## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/decisions/` — authoritative architectural decisions. Read when starting work in this repo.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill for the full methodology.
```

Append the Routing section at the end of the file (don't try to find a "right" spot — end is fine and is easy to detect on re-runs).

### Detecting existing Routing section

A re-run is detected by searching for the literal heading `## minerva` followed within the next ~3 lines by the substring `.minerva/decisions/`. If both are present, treat the section as already in place.

## Step 4 — report

Print a status block:

```
.minerva/ layout       ✓ created (or: already present)
.gitignore             ✓ ok       (or: skipped — not a git repo; or: ⚠ <pattern at file:line> would exclude .minerva/)
CLAUDE.md              ✓ Routing section added (or: ✓ already present; or: — not present)
AGENTS.md              ✓ Routing section added (or: ✓ already present; or: — not present)
GEMINI.md              ✓ Routing section added (or: ✓ already present; or: — not present)
flat layout            — none detected (or: ⚠ work/ and/or decisions/ at root — see message above)
```

Suggest `/propose <slug>` as the next step if no work units exist yet.

## Out of scope

- Migrating a pre-existing flat `work/` + `decisions/` layout. `/init` only reports it; the user runs the `mv` themselves.
- Authoring or rewriting CLAUDE.md / AGENTS.md content beyond the Routing section.
- Editing `.gitignore` to remove offending patterns.
- A `/init --refresh` mode to rewrite the Routing section when its template changes. Out of scope for v1.
