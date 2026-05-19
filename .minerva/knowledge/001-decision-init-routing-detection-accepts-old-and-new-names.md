# init.md Routing section detection accepts both old and new directory names

**Date**: 2026-05-18
**Type**: decision
**Context**: .minerva/work/003-broaden-promote-knowledge-artifacts

## Context

Work unit `003` renamed `.minerva/decisions/` to `.minerva/knowledge/` throughout the plugin. The `/init` command detects whether a Routing section already exists in the agent file (CLAUDE.md / AGENTS.md / GEMINI.md) before writing one, to stay idempotent. The detection logic previously searched for `.minerva/decisions/` as the signal. After the rename, projects that had already run `/init` would have Routing sections containing the old name — and would fail the detection check, causing `/init` to incorrectly re-write the Routing section.

## Finding

The detection logic in `init.md` was updated to check for either `.minerva/knowledge/` or `.minerva/decisions/` within ~3 lines of the `## minerva` heading. If either substring is present, the section is treated as already in place.

## Implications

- Any future change to the Routing section template (e.g. renaming `.minerva/knowledge/` again) must update both the template content AND the detection logic to include the new string alongside existing ones — otherwise re-runs will overwrite existing Routing sections.
- The detection is intentionally lenient: it checks for presence, not exact match. This means a manually edited Routing section that still references either path won't be rewritten.
