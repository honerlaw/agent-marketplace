# Scratchpad: add-propose-ship-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

- Plugin manifest (`plugin.json`) does not enumerate skills — they are auto-discovered from `skills/` subdirectories. No manifest change needed for new skills.
- The review gate is the only handoff that pauses; all others are auto. Deliberate design decision from proposal Q&A.
