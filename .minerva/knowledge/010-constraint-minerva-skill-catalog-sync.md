# Minerva plugin skill catalogs are NOT auto-generated — three docs surfaces must be updated when a minerva skill is added

**Date**: 2026-05-21
**Type**: constraint
**Context**: .minerva/work/013-sync-skill-catalogs (see git history if the worktree has been cleaned up)

## Context
Knowledge entry [[004-constraint-plugin-skills-auto-discovered-from-directory]] established that skills are auto-discovered from `plugins/<plugin>/skills/`. The **runtime** picks them up without any registration. But the **human-readable catalogs** that orient new users (and Claude itself, via `minerva:using-minerva`) are hand-maintained markdown — they drift silently when a skill is added without the matching catalog edits. By the time work unit 013 ran, three different catalogs were stale in three different ways.

## Finding
The minerva plugin has three catalog surfaces that enumerate its skills, and all three must be kept in sync with `plugins/minerva/skills/`:

1. **`plugins/minerva/README.md`** — the `## Skills` table. One row per skill, in lifecycle order (`init → propose → replan → grill-plan → work → promote → review → ship → cleanup → propose-ship → propose-ship-auto → using-minerva`). Each row's description text is excerpted from that skill's `SKILL.md` `description:` frontmatter — verbatim or lightly trimmed (drop leading `"Use when…"` trigger prose, take the next descriptive clause). No paraphrasing or fresh prose.
2. **`plugins/minerva/skills/using-minerva/SKILL.md`** — the `## Skill decision matrix`. One row per user-facing situation, mapping to a skill. Every skill except `using-minerva` itself (self-reference would be circular) gets at least one row. The Situation column is when-to-use phrasing derived from the skill's frontmatter trigger; the Skill column lists `minerva:<name>` with an optional parenthetical for auto-invocation nuance (e.g., `grill-plan` is "auto-invoked by `minerva:propose` and `minerva:replan`; usable standalone on any drafted plan").
3. **`README.md` (repo root)** — the `## Plugins` table's "Skills" cell for the minerva row. Space-separated, backtick-wrapped `minerva:<name>` for every skill (including auto-invoked ones like `grill-plan` and orientation-style ones like `using-minerva`). `<br>` between logical groupings is acceptable if the cell becomes visually unwieldy.

All three surfaces have a single-line HTML comment above them — added by work unit 013 — pointing future authors at `SKILL.md` frontmatter as the source of truth and reminding them to add a row when adding a skill. Treat the comment as a write-time convention nudge, not a CI guarantee.

## Implications
- When **adding a new minerva skill** (`plugins/minerva/skills/<name>/SKILL.md`): add a row to all three catalogs in the same commit. Use the skill's own `description:` frontmatter as the text source. Place the row in lifecycle position for the plugin README; pick a situation phrasing for the using-minerva matrix; append `minerva:<name>` to the top-level README cell.
- When **removing a minerva skill**: remove the row from all three catalogs in the same commit. Update any cross-references in other `SKILL.md` files (workflow narration, e.g., `propose.md` referencing `grill-plan`).
- When **drafting a `minerva:propose` proposal that adds or removes a skill**: enumerate the three catalog updates in `## Approach` so they don't slip through as scope misses.
- This constraint **complements** [[004-constraint-plugin-skills-auto-discovered-from-directory]] and [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — runtime auto-discovery applies at the SKILL.md level only; both marketplace-level (`marketplace.json`, top-level README plugin table) and plugin-level (catalog surfaces in this entry) human-facing registries are manually maintained.
- The HTML-comment convention reminders are a deliberate **mitigation, not a guarantee**. Drift-prevention automation (a CI check or pre-commit hook that diffs `ls plugins/minerva/skills/` against catalog rows) was scoped out of 013 as a follow-up; see `.minerva/work/013-sync-skill-catalogs/followups.md` for the trigger conditions to revisit it. **Partially delivered by [[012-constraint-skill-structural-contracts]]**: each skill's `cross_surface` contract clause now test-enforces its presence in these three surfaces (the dirs→catalog direction, as pytest). The orphaned-catalog-row direction and a true CI/pre-commit hook remain open.

## Related
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — builds on
- [[012-constraint-skill-structural-contracts]] — see also
- [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — see also
- [[034-constraint-site-fourth-catalog-surface]] — see also
- [[038-constraint-site-catalog-source-is-pages-index]] — see also: site surface is now pages/index.md, not site/index.html
- [[048-pattern-catalog-semantic-drift-recurs]] — see also
