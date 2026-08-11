# Proposal: dot-minerva-init

**Date**: 2026-05-18
**Status**: Shipped (2026-05-18)

## Goal

Reorganize minerva's on-disk artifacts under a hidden `.minerva/` directory at the project root, and add a `/init` command that scaffolds the directory and wires the project's agent file (CLAUDE.md / AGENTS.md / etc.) with a Routing section.

## Why

- **Clutter.** `work/` and `decisions/` at the project root are noisy. `.minerva/` follows the `.git`, `.vscode`, `.github` convention: hidden, committed, tool-owned.
- **Cleaner detection signal.** The existence of `.minerva/` is a single unambiguous signal that the repo uses minerva. The `using-minerva` skill's trigger gets sharper — current logic checks for two separate top-level directories.
- **Routing for new agents.** When an unfamiliar LLM lands in the repo, a Routing section in CLAUDE.md / AGENTS.md tells it where to look for prior context. Minimal pointer, not a full primer.

## Approach

1. **Folder relocation.** All four existing commands (`/propose`, `/replan`, `/work`, `/promote`) and the `using-minerva` skill switch their path references:
   - `work/NNN-<slug>/` → `.minerva/work/NNN-<slug>/`
   - `decisions/NNN-<slug>.md` → `.minerva/decisions/NNN-<slug>.md`
   - The plugin README's file-layout diagram updates to show the new structure.

2. **New `/init` command.**
   - Creates `.minerva/work/` and `.minerva/decisions/`, each with a `.gitkeep` so git tracks the empty directories.
   - Scans `.gitignore` (and any nested gitignores) for patterns that would exclude `.minerva/`. If found, reports the offending file + line and asks the user to fix it manually — doesn't auto-edit, since `.gitignore` is user territory.
   - Detects which agent files already exist (CLAUDE.md, AGENTS.md, GEMINI.md). Adds a Routing section to each that exists.
   - If none exist, prompts the user to pick which to create.
   - Idempotent: re-running on a project that's already initialized leaves things alone and reports a per-piece status (folder ✓, gitignore ✓, agent file(s) ✓).
   - In a non-git repo, skips the gitignore check silently and still creates the folder.

3. **Routing section content** (minimal-pointer style):

   ```markdown
   ## minerva

   This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

   - `.minerva/decisions/` — authoritative architectural decisions. Read when starting work in this repo.
   - `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

   Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill for the full methodology.
   ```

4. **`using-minerva` skill update.** Detection logic switches to a single check — does `.minerva/` exist at the project root. Body references to `work/` and `decisions/` get the `.minerva/` prefix.

5. **Tests.** `tests/test_minerva.py` expectations updated — five existing command/skill tests gained explicit `.minerva/work/` and `.minerva/decisions/` substring assertions (and the using-minerva test gained a `.minerva` frontmatter-detection assertion). One new test, `test_init_command_exists_with_frontmatter`, covers the `/init` command's structural surface. Final count: **12 minerva tests**, not the ~14 initially estimated — tightening existing assertions was preferable to adding parallel `.minerva/`-detection tests for the same coverage.

6. **No migration tooling.** minerva is brand-new and has no existing users. We don't need a converter from `work/` → `.minerva/work/`. If a future user has the old layout, `mv work .minerva/work && mv decisions .minerva/decisions` is fine.

7. **Pre-existing flat layout detection.** If `/init` runs on a repo that already has `work/` or `decisions/` at the root, it reports the situation and tells the user the `mv` command. It does not touch those directories.

## Open Questions

- The exact text of the Routing section may evolve once we see it in real agent files. The template above is the starting point.
- Whether `/init` should also detect non-canonical agent filenames (e.g. `CLAUDE.local.md`, `AGENTS.md.bak`). For now it sticks to the canonical names.
- Whether to surface a `/init --refresh` mode that re-writes the Routing section if it's out of date. Out of scope for v1; revisit if the Routing format changes.
