# Proposal: swap-financials-for-utils-plugin

**Date**: 2026-05-20
**Status**: Draft

## Goal

Restructure the plugin marketplace by removing the existing `plugins/financials/` plugin, creating a new `plugins/utils/` plugin in its place, and seeding the new plugin with the existing user-scope `humanizer` skill (currently at `~/.claude/skills/humanizer/`). The user-scope copy of `humanizer` is deleted at the end so there is exactly one canonical copy, served from the `utils` plugin.

## Why

Two motivations:

1. **Retire `financials`.** The `financials` plugin is no longer needed in this marketplace repo and should be removed cleanly along with its commands and scripts.
2. **Promote `humanizer` from user scope to a marketplace plugin.** The `humanizer` skill is general-purpose enough to be installable by any user of this marketplace, not just the author. Shipping it under a new `utils` plugin gives it a versioned home and creates a container for future small utility skills that don't warrant their own plugin.

## Approach

Four sequential operations, all committed on branch `012-swap-financials-for-utils-plugin`:

1. **Delete `plugins/financials/`** — remove the entire directory (`.claude-plugin/`, `README.md`, `commands/`, `scripts/`). Use `git rm -r` so the deletion is staged.

2. **Create `plugins/utils/`** with the minimal plugin skeleton:
   - `plugins/utils/.claude-plugin/plugin.json` modeled on the two existing plugins (same author block, same schema shape):
     ```json
     {
       "name": "utils",
       "description": "Miscellaneous utility skills",
       "author": { "name": "Derek Honerlaw" }
     }
     ```
   - `plugins/utils/skills/` directory (created implicitly by step 3).

3. **Copy the humanizer skill into the plugin.** Copy `~/.claude/skills/humanizer/SKILL.md` (full file, byte-for-byte) to `plugins/utils/skills/humanizer/SKILL.md`. No edits to skill content — the frontmatter (`name: humanizer`, version, description) ships unchanged.

4. **Delete the user-scope humanizer.** After the copy is committed in the worktree, remove `~/.claude/skills/humanizer/` (the directory and its contents) from the user-scope `~/.claude/skills/` tree. This is a filesystem operation outside the git repo; it is not part of any commit.

The two destructive operations (`git rm` of financials and `rm -rf` of user-scope humanizer) are ordered last within their respective domains: the new plugin layout is fully in place before either is executed, so a mid-flight failure leaves the marketplace in a coherent state.

## Success criteria

- `plugins/financials/` directory does not exist in the worktree (verifiable via `ls plugins/`).
- `plugins/utils/.claude-plugin/plugin.json` exists and is valid JSON containing `name: "utils"`, a description string, and an author block matching the schema of existing plugins.
- `plugins/utils/skills/humanizer/SKILL.md` exists and is byte-identical to the pre-existing `~/.claude/skills/humanizer/SKILL.md` (verifiable via `diff` before the user-scope copy is deleted).
- `~/.claude/skills/humanizer/` does not exist on the filesystem after the work unit completes.
- All in-repo changes are committed on branch `012-swap-financials-for-utils-plugin`; working tree is clean.

## Open Questions

- None. The user's request specified every action; the only inferred detail was the `description` field of the new `utils/plugin.json` (`"Miscellaneous utility skills"`), which the user can correct at the post-write gate or during `minerva:work`.
