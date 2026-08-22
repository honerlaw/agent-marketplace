# Followups: add-triage-skill

## 2026-05-22

- **`minerva:init` should scaffold `.minerva/reference/`.** `minerva:triage` is the first skill to depend on `.minerva/reference/`, but `minerva:init` currently only scaffolds `.minerva/work/` and `.minerva/knowledge/`. New minerva projects won't have a `reference/` directory until someone creates it manually. Update `minerva:init` to add `.minerva/reference/` (with a `.gitkeep` and a one-line README explaining the tier) so the directory layout matches the documented persistence hierarchy.
- **Persistence-hierarchy docs need the reference tier.** `plugins/minerva/skills/using-minerva/SKILL.md` and `plugins/minerva/README.md` both document the persistence hierarchy with a 2-tier table (always-read / searchable / ephemeral). Neither mentions `.minerva/reference/` yet. Update both to include the reference tier alongside `.minerva/knowledge/`. Likely bundled with the `minerva:init` scaffolding change as one future work unit.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **`minerva:init` should scaffold `.minerva/reference/`.** → shipped — `init/references/steps.md` scaffolds `.minerva/reference/` and its `.gitkeep`; this repo's own `.minerva/` predates that change
- **Persistence-hierarchy docs need the reference tier.** → shipped — the reference tier appears in `plugins/minerva/README.md` and `using-minerva/references/guide.md`
