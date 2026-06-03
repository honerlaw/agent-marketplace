# Marketplace plugin registry is NOT auto-discovered — `marketplace.json` and `README.md` must be updated when plugins are added or removed

**Date**: 2026-05-20
**Type**: constraint
**Context**: .minerva/work/012-swap-financials-for-utils-plugin (see git history if the worktree has been cleaned up)

## Context
Knowledge entry 004 established that **skills inside a plugin** are auto-discovered: dropping a `SKILL.md` into `plugins/<plugin>/skills/<name>/` is enough; `plugin.json` doesn't enumerate skills. It's easy to assume the same auto-discovery applies one level up — that adding or removing a directory under `plugins/` is enough at the marketplace level too. It isn't.

## Finding
The marketplace itself maintains an **explicit** plugin registry that is not derived from the filesystem:

1. `.claude-plugin/marketplace.json` enumerates every plugin under a `"plugins"` array (with `name`, `source`, `description` per entry). Adding or removing a `plugins/<plugin>/` directory without editing this file leaves the registry out of sync: the new plugin is not advertised, or the removed one points at a nonexistent path.
2. `README.md` mirrors that registry in two human-facing places: the install example (`./install.sh <plugin>`) and the **Plugins** table at the bottom. Both need to be kept in sync with `marketplace.json`.

The 012 work unit surfaced this constraint when the original proposal Approach enumerated only the `plugins/` directory operations and missed both files; review caught it.

## Implications
- When adding a new plugin: create `plugins/<plugin>/` with `.claude-plugin/plugin.json` AND add an entry to `.claude-plugin/marketplace.json` AND add a row to the README plugin table. Update the install example only if it pointed at a now-removed plugin.
- When removing a plugin: delete `plugins/<plugin>/` AND remove its entry from `.claude-plugin/marketplace.json` AND remove its row from the README plugin table. If the install example used the removed plugin, replace it with another plugin's name.
- When proposing plugin add/remove work, the proposal's `## Approach` should explicitly enumerate the marketplace.json and README updates so they don't slip through as scope misses.
- This constraint complements [[004-constraint-plugin-skills-auto-discovered-from-directory]]: auto-discovery applies **inside** a plugin (skills), not **between** plugins (marketplace registry).

## Related
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — see also
- [[010-constraint-minerva-skill-catalog-sync]] — see also
