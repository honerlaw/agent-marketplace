# Scratchpad: migrate-commands-to-skills

> **Ephemeral working memory.**

## 2026-05-19 — implementation notes

- `rm -rf commands/` is blocked by shell permissions in this session. Manual step required: `rm -rf plugins/minerva/commands/`. The five command files remain on disk but are superseded by the new skills; tests and docs no longer reference them.
- The `promote.md` scratchpad marker was updated from `Summarized at /promote on ...` to `Summarized at minerva:promote on ...` in the new skill. Any existing archived scratchpads from prior work units still have the old marker — that's fine, they're already archived.
- `install.sh` listing loop now derives skill name from directory basename under `skills/*/`. No frontmatter parsing needed. Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.
