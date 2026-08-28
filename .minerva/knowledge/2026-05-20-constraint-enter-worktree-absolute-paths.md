# Worktree file ops use prefixed paths, not EnterWorktree

**Date**: 2026-05-20
**Updated**: 2026-06-27 (work unit 044 — `EnterWorktree` removed from every minerva skill)
**Type**: constraint
**Context**: .minerva/work/2026-05-20-worktree-creation-in-propose (see git history if the worktree has been cleaned up)

## Context

When a skill calls `EnterWorktree`, the session's working directory switches to the worktree (e.g. `.minerva/worktrees/010-worktree-creation-in-propose/`). It is natural to assume that subsequent file operations are automatically scoped to the new worktree, but that is only true for **relative** paths. Absolute paths captured before — or constructed during — the worktree session continue to resolve to wherever they pointed on the filesystem.

This bit during the work phase of unit 010: after `EnterWorktree`, ~10 `Edit` calls were issued with absolute paths like `/Users/.../agent-marketplace/plugins/minerva/skills/work/SKILL.md`. Those edits silently landed in the **parent repo** working tree (on the default branch), not in the worktree's branch. The mistake was only caught when a verification grep against the worktree's checkout returned zero matches.

## Finding

`EnterWorktree` changes the session's current working directory but does not rewrite or intercept absolute paths passed to file-handling tools (`Read`, `Edit`, `Write`, `Bash` with absolute args). An absolute path always resolves to the literal filesystem location it names.

Practical consequence: when a skill operates inside a worktree, every file path it constructs must either be relative (so cwd resolution carries it into the worktree) or absolute with the worktree prefix (`/.../.minerva/worktrees/<NNN-slug>/...`). Mixing pre-EnterWorktree absolute paths with post-EnterWorktree file operations is silently wrong — git status on the worktree will look empty while the parent repo accumulates uncommitted changes.

**Standing model (2026-06-27, work unit 044).** minerva no longer calls `EnterWorktree` at all. Its contract only reliably switches the session into worktrees under `.claude/worktrees/`; minerva's worktrees live under `.minerva/worktrees/`, so the call is rejected in the re-entry and pinned-subagent contexts the lifecycle runs in. Every lifecycle skill now keeps its working directory at the **parent repo** and addresses a work unit's worktree explicitly — file paths prefixed with `.minerva/worktrees/<NNN-slug>/`, git commands as `git -C .minerva/worktrees/<NNN-slug> …`. The prefixed-path discipline above is therefore not an edge case to avoid but the **only** operating mode, and there is no cwd switch to forget.

## Implications

- Every minerva lifecycle skill that operates on a worktree (`propose`, `work`, `replan`, `review`, `promote`, `ship`) addresses it by `.minerva/worktrees/<NNN-slug>/`-prefixed file paths and `git -C .minerva/worktrees/<NNN-slug>` commands; none calls `EnterWorktree`. `cleanup` runs from the parent repo and removes worktrees outright.
- When recovering from a misroute (edits landed in the parent repo by accident), the safe sequence is: `cp` the modified files from the parent into the worktree, then `git -C <parent> checkout -- <paths>` to revert the parent's working tree. Do **not** use `git stash` across the worktree boundary unless the branches share the file content exactly.
- Tooling cannot defend against this — it's a discipline of path construction. The risk is a misrouted edit whenever a worktree-bound path is written without the `.minerva/worktrees/<NNN-slug>/` prefix (the session cwd is always the parent repo); git status on the worktree looks empty while the parent repo silently accumulates the change.

## Related
- [[2026-05-19-decision-gitignore-before-worktree]] — see also
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — see also
- [[2026-06-27-decision-worktree-addressing-no-enterworktree]] — see also
- [[2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout]] — see also
