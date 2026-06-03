# EnterWorktree does not redirect absolute paths

**Date**: 2026-05-20
**Type**: constraint
**Context**: .minerva/work/010-worktree-creation-in-propose (see git history if the worktree has been cleaned up)

## Context

When a skill calls `EnterWorktree`, the session's working directory switches to the worktree (e.g. `.minerva/worktrees/010-worktree-creation-in-propose/`). It is natural to assume that subsequent file operations are automatically scoped to the new worktree, but that is only true for **relative** paths. Absolute paths captured before — or constructed during — the worktree session continue to resolve to wherever they pointed on the filesystem.

This bit during the work phase of unit 010: after `EnterWorktree`, ~10 `Edit` calls were issued with absolute paths like `/Users/.../agent-marketplace/plugins/minerva/skills/work/SKILL.md`. Those edits silently landed in the **parent repo** working tree (on the default branch), not in the worktree's branch. The mistake was only caught when a verification grep against the worktree's checkout returned zero matches.

## Finding

`EnterWorktree` changes the session's current working directory but does not rewrite or intercept absolute paths passed to file-handling tools (`Read`, `Edit`, `Write`, `Bash` with absolute args). An absolute path always resolves to the literal filesystem location it names.

Practical consequence: when a skill operates inside a worktree, every file path it constructs must either be relative (so cwd resolution carries it into the worktree) or absolute with the worktree prefix (`/.../.minerva/worktrees/<NNN-slug>/...`). Mixing pre-EnterWorktree absolute paths with post-EnterWorktree file operations is silently wrong — git status on the worktree will look empty while the parent repo accumulates uncommitted changes.

## Implications

- Every minerva lifecycle skill that calls `EnterWorktree` (`propose`, `work`, `replan`, `review`, `promote`, `ship`) must construct file paths relative to the worktree root after entering, or use absolute paths that explicitly include `.minerva/worktrees/<NNN-slug>/` in the prefix.
- When recovering from a misroute (edits landed in the parent repo by accident), the safe sequence is: `cp` the modified files from the parent into the worktree, then `git -C <parent> checkout -- <paths>` to revert the parent's working tree. Do **not** use `git stash` across the worktree boundary unless the branches share the file content exactly.
- Tooling cannot defend against this — it's a discipline of path construction. The risk is highest immediately after `EnterWorktree` when absolute paths from earlier in the session are still in scope (memory, previous tool calls, system prompts).

## Related
- [[005-decision-gitignore-before-worktree]] — see also
- [[007-constraint-skills-must-call-tools-not-prose]] — see also
