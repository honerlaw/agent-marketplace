# Plugin skills are auto-discovered from the skills/ directory — no manifest update required

**Date**: 2026-05-19
**Type**: constraint
**Context**: .minerva/work/007-add-propose-ship-skill

## Context
When adding a new skill to the minerva plugin, it was unclear whether `plugin.json` needed to be updated to register the skill.

## Finding
The Claude Code plugin system auto-discovers skills from subdirectories under `skills/`. Each subdirectory containing a `SKILL.md` file is registered as a skill automatically. The `plugin.json` manifest does not enumerate skills and does not need to be modified when adding or removing a skill.

## Implications
Adding a new minerva skill requires only: (1) create `plugins/minerva/skills/<name>/SKILL.md`, (2) populate the frontmatter and body. No other files change. Removing a skill is equally simple — delete the directory.

## Related
- [[010-constraint-minerva-skill-catalog-sync]] — see also
- [[012-constraint-skill-structural-contracts]] — see also
