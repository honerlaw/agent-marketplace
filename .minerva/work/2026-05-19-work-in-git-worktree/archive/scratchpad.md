# Scratchpad: work-in-git-worktree

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `.minerva/decisions/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Notes

- Docs were untracked on main when work started, so no "removal" commit needed on main — moving them to the worktree was sufficient.
- `.gitignore` updated on main first so the worktree path is never seen as untracked on main.
- Target resolution updated to scan both `.minerva/work/` and `.minerva/worktrees/NNN-*/` — after first invocation, docs only exist in the worktree.
