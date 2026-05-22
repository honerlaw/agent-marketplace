# Scratchpad: add-triage-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Follow-up: `minerva:init` should scaffold `.minerva/reference/`

`minerva:triage` is the first skill to depend on `.minerva/reference/`, but `minerva:init` currently only scaffolds `.minerva/work/` and `.minerva/knowledge/`. New minerva projects won't have a `reference/` directory until someone creates it manually. Worth updating `minerva:init` to add `.minerva/reference/` (with a `.gitkeep` and a one-line README explaining the tier) so the directory layout matches the documented persistence hierarchy.

Out of scope for this work unit — separate proposal.

## Follow-up: knowledge vs. reference tier needs a top-level reference

The `using-minerva` skill and `plugins/minerva/README.md` both document the persistence hierarchy with a 2-tier table (always-read / searchable / ephemeral). Neither mentions `.minerva/reference/` yet. After this skill ships, those docs should be updated to include the reference tier. Likely belongs in the same follow-up as the `minerva:init` scaffolding change.

## Review triage 2026-05-22
- [FIXED] #1 low SKILL.md:3, plugins/minerva/README.md — capitalized "OR" → "or" for prose consistency

- Review fix: plugins/minerva/skills/triage/SKILL.md, plugins/minerva/README.md — "OR" → "or" for stylistic consistency with other skill descriptions
