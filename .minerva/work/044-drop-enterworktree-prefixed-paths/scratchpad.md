# Scratchpad: drop-enterworktree-prefixed-paths

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Quick decisions 2026-06-27
- [escalated to user] mechanism: relocate to `.claude/worktrees/` vs drop-EnterWorktree-use-prefixed-paths vs resilient-EnterWorktree-with-fallback — genuine high-blast-radius cross-cutting fork, no dominant option → user picked **drop EnterWorktree, use `.minerva/worktrees/<NNN-slug>/`-prefixed paths + `git -C`**, keeping the `.minerva/` worktree home.
- [decided] scope check: single work unit — one consistent prose transformation across ~13 skill/record files, no code logic. Broad but shallow; approach locked by the escalation, so fast path holds.
- [decided] keep knowledge 008's filename/slug stable (preserve `[[008-…]]` wikilinks) and rewrite its body, rather than rename or supersede-with-new-file — avoids churn across overview/index/005/007/archives.
- [decided] dogfood: created worktree 044 via `git worktree add` and operate via the `.minerva/worktrees/044-.../` prefix for this run — no EnterWorktree call.
