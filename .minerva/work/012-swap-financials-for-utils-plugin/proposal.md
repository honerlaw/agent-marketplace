# Proposal: swap-financials-for-utils-plugin

**Date**: 2026-05-20
**Status**: Shipped (2026-05-20)

## Goal

Restructure the plugin marketplace by removing the existing `plugins/financials/` plugin, creating a new `plugins/utils/` plugin in its place, and seeding the new plugin with the existing user-scope `humanizer` skill (formerly at `~/.claude/skills/humanizer/`). The user-scope copy of `humanizer` is deleted at the end so there is exactly one canonical copy, served from the `utils` plugin.

## Why

Two motivations:

1. **Retire `financials`.** The `financials` plugin is no longer needed in this marketplace repo and was removed cleanly along with its commands and scripts.
2. **Promote `humanizer` from user scope to a marketplace plugin.** The `humanizer` skill is general-purpose enough to be installable by any user of this marketplace, not just the author. Shipping it under a new `utils` plugin gives it a versioned home and creates a container for future small utility skills that don't warrant their own plugin.

## Approach

Six operations, all committed on branch `012-swap-financials-for-utils-plugin`:

1. **Deleted `plugins/financials/`** — entire directory (`.claude-plugin/`, `README.md`, `commands/`, `scripts/`) removed via `git rm -r`.

2. **Created `plugins/utils/`** with the minimal plugin skeleton:
   - `plugins/utils/.claude-plugin/plugin.json` modeled on the existing minerva plugin (same author block, same schema shape):
     ```json
     {
       "name": "utils",
       "description": "Miscellaneous utility skills",
       "author": { "name": "Derek Honerlaw" }
     }
     ```

3. **Copied the humanizer skill** — `~/.claude/skills/humanizer/SKILL.md` → `plugins/utils/skills/humanizer/SKILL.md`, byte-identical (verified via `diff -q` before the source deletion).

4. **Updated `.claude-plugin/marketplace.json`** — replaced the `financials` entry (pointing to the now-deleted directory) with a new `utils` entry. Unlike skills inside a plugin (auto-discovered per knowledge entry 004), top-level plugins are NOT auto-discovered from `plugins/` — the marketplace registry enumerates them explicitly. Knowledge entry 009 captures this constraint.

5. **Updated `README.md`** — replaced the `financials` install example (`./install.sh financials`) with `./install.sh utils`, and replaced the `financials` row in the Plugins table with a `utils` row listing the `humanizer` skill.

6. **Deleted the user-scope humanizer** — `rm -rf ~/.claude/skills/humanizer/` (filesystem operation outside the git repo, after the in-repo changes were committed).

Steps 4 and 5 were not in the original Approach — they were surfaced by `minerva:review` as a scope-miss. The original Approach treated `plugins/<plugin>/` directory operations as sufficient; in fact the marketplace registry and the README plugin table also enumerate plugins explicitly. Knowledge entry 009 codifies this constraint for future plugin add/remove work.

## Success criteria

- `plugins/financials/` directory does not exist in the worktree.
- `plugins/utils/.claude-plugin/plugin.json` exists and is valid JSON containing `name: "utils"`, a description string, and an author block matching the schema of existing plugins.
- `plugins/utils/skills/humanizer/SKILL.md` exists and was byte-identical to the pre-existing `~/.claude/skills/humanizer/SKILL.md` (verified via `diff -q` before the user-scope copy was deleted).
- `~/.claude/skills/humanizer/` does not exist on the filesystem.
- `.claude-plugin/marketplace.json` lists `utils` (not `financials`).
- `README.md` install example references `./install.sh utils` and the Plugins table lists `utils` with the `humanizer` skill (not `financials`).
- All in-repo changes are committed on branch `012-swap-financials-for-utils-plugin`; working tree is clean.

## Open Questions

- None remaining.
