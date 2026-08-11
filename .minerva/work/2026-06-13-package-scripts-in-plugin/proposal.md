# Proposal: package-scripts-in-plugin

**Date**: 2026-06-13
**Status**: Shipped (2026-06-13)

## Goal

Package minerva's 6 Python helper scripts inside `plugins/minerva/scripts/` so they are deployed to the plugin cache and available in any target project when minerva is installed as a plugin — without requiring those scripts to exist in the target project's own `scripts/` directory.

## Why

Four minerva skills (synthesize, lint, lint-fix, migrate) resolve their Python helpers via `git rev-parse --show-toplevel`, pointing to the **target project's** `scripts/` directory. When minerva is deployed as a plugin in a project that doesn't have these scripts (e.g. seekless), the import fails with `ModuleNotFoundError: No module named 'synthesis_status'`. The plugin cache (`~/.claude/plugins/cache/agent-marketplace/minerva/<hash>/`) contains all files from `plugins/minerva/` — so adding scripts there makes them available in any deployment context. This was observed as a real failure in seekless's synthesize Phase 4.5 step.

## Approach

Option B (3/3 approach-selection panel accepted):

**1. Create `plugins/minerva/scripts/` as the source of truth** for the 6 minerva-owned scripts:
   - `knowledge_spans.py` (base — no local imports)
   - `knowledge_lint.py` → imports `knowledge_spans`
   - `knowledge_edits.py` (base — no local imports)
   - `knowledge_fix.py` → imports `knowledge_lint` + `knowledge_edits`
   - `synthesis_status.py` → imports `knowledge_lint`
   - `migration_status.py` → imports `knowledge_lint`

**2. Replace `scripts/<these 6 files>` with relative symlinks** pointing to `../plugins/minerva/scripts/<file>`. Python follows symlinks transparently; git tracks them correctly on macOS. CI tests continue to work via symlinks (they import from `scripts/`, which resolves through the symlinks to the real files).

**3. Update 4 SKILL.md bash commands** to discover scripts via two plugin paths first, falling back to the repo-local `scripts/`:
   ```bash
   PLUGIN_SCRIPTS=$(ls -td "${HOME}/.claude/plugins/cache/agent-marketplace/minerva/"*/scripts \
     "${HOME}/.claude/plugins/minerva/scripts" 2>/dev/null | head -1)
   SCRIPTS="${PLUGIN_SCRIPTS:-$ROOT/scripts}"
   ```
   - synthesize, lint, migrate: `sys.path.insert(0, '$SCRIPTS')` pattern
   - lint-fix: `python3 "${SCRIPTS}/knowledge_fix.py"` (direct invocation — different pattern from the others)

**4. Update knowledge entry [[2026-06-03-constraint-skill-wraps-script-via-importable-api]]** to reflect that scripts are now in the plugin directory as the primary source; repo `scripts/` holds development symlinks.

## Success criteria

1. `plugins/minerva/scripts/` contains all 6 scripts as real files.
2. `scripts/{knowledge_spans,knowledge_lint,knowledge_edits,knowledge_fix,synthesis_status,migration_status}.py` are relative symlinks → `../plugins/minerva/scripts/<file>`.
3. All 276 CI tests pass (Python follows symlinks; no test import paths change).
4. `minerva:synthesize` importable from the plugin cache in a fresh target project (no `scripts/` in target required).
5. 4 SKILL.md files updated with two-path plugin-cache-first discovery.
6. [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] knowledge entry updated.
7. No SKILL.md exceeds 9KB after edits.

## Open Questions

None — approach determined by 3/3 panel; scope is fully specified.
