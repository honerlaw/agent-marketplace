---
name: init
description: Scaffolds the `.minerva/` directory layout and agent-file Routing section — durable records, knowledge tracking, and project memory for agent work in a project. Idempotent — re-runs report per-piece status without rewriting anything in place, and it warns about legacy `.minerva/decisions/` layouts. Use when adopting minerva or setting up durable record/knowledge discipline for the first time in a project, or when the user invokes `minerva:init`.
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

## Steps

Execute steps 1–5 in order; their full protocols live verbatim in `references/steps.md` — **read it now, before step 1**: **1** scaffold `.minerva/` (directory layout, idempotent per-piece status), **2** gitignore check (`.minerva/worktrees/` entry), **3** agent-file detection + Routing section (template-of-record, stale-marker refresh), **4** commit offer, **5** report.

## Out of scope

- Migrating a pre-existing flat `work/` + `decisions/` layout. `minerva:init` only reports it; the user runs the `mv` themselves.
- Migrating `.minerva/decisions/` to `.minerva/knowledge/`. Same — report only, user runs the move.
- Authoring or rewriting CLAUDE.md / AGENTS.md content beyond the Routing section.
- Editing `.gitignore` to remove offending user-authored patterns. (Init **does** install `.minerva/worktrees/` if missing — that entry is part of the scaffold, not user territory.)
- Auto-refreshing a stale Routing section without the gate. Agent files are user territory — the refresh is always offered, diffed, and confirmable, never silent.
- Splice-preserving refresh (updating canonical bullets while keeping unrecognized custom lines). Future hardening; v1 is a gated whole-section replace.
