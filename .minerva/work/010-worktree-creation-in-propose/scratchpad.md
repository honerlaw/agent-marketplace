# Scratchpad: worktree-creation-in-propose

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## 2026-05-20 — EnterWorktree does not redirect absolute paths

Mid-implementation I called `EnterWorktree` to switch into `.minerva/worktrees/010-worktree-creation-in-propose/`, then issued ~10 Edit calls using absolute paths like `/Users/derekhonerlaw/Development/agent-marketplace/plugins/minerva/skills/work/SKILL.md`. All those edits silently landed in the **main repo** working tree, not in the worktree, because absolute paths bypass cwd.

Caught it when verifying success criteria — `grep "^## Worktree entry"` against the worktree returned nothing, but the main repo had all the changes uncommitted. Fix: `cp` each modified file from main into the worktree, then `git checkout --` to revert main.

Gotcha for future work in worktrees: either use relative paths (Edit's cwd is the worktree post-EnterWorktree) or absolute paths that include `.minerva/worktrees/<NNN-slug>/` in the prefix. The Edit/Write/Read tools do not transparently route absolute paths through the active worktree.

Worth a constraint-type knowledge entry: "absolute paths from before EnterWorktree still resolve to the original filesystem location, not into the worktree" — durable, applies to every skill that calls EnterWorktree.
