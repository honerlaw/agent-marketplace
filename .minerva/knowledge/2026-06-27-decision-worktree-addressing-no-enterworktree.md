# Worktrees are addressed by prefixed paths; EnterWorktree was dropped

**Date**: 2026-06-27
**Type**: decision
**Context**: .minerva/work/2026-06-27-drop-enterworktree-prefixed-paths

## Context

minerva creates each work unit's worktree under `.minerva/worktrees/<NNN-slug>/` via raw `git worktree add`, then every lifecycle skill called the built-in `EnterWorktree` tool with `path: ".minerva/worktrees/<NNN-slug>"` to switch the session into it. But `EnterWorktree`'s contract only reliably switches the session into worktrees under **`.claude/worktrees/`** — the already-in-a-worktree and pinned-subagent cases *require* that location, and the orchestrators (`propose-ship`, `propose-ship-auto`, `propose-ship-quick`) hit exactly those cases on re-entry and in subagents. So the calls were rejected in practice and only "worked" because the model improvised a fallback.

## Decision

Drop `EnterWorktree`/`ExitWorktree` from minerva entirely. Keep the `.minerva/worktrees/` home; the session's working directory stays the **parent repo**, and skills address a work unit's worktree explicitly — file paths prefixed with `.minerva/worktrees/<NNN-slug>/`, git commands as `git -C .minerva/worktrees/<NNN-slug> …`.

Three options were weighed:

1. **Relocate worktrees to `.claude/worktrees/`** so `EnterWorktree` works natively (preserves cwd-relative ergonomics, especially in the work phase). Rejected: breaks minerva's `.minerva/`-self-contained principle and entangles its worktrees with the harness's own worktree home.
2. **Drop `EnterWorktree`, use prefixed paths + `git -C`** — *chosen*. Works in every context (fresh session, re-entry, pinned subagent) with no dependence on a tool that may reject the path; keeps the `.minerva/` home.
3. **Keep `EnterWorktree` with a documented fallback.** Rejected: doesn't remove the failure mode in the subagent/re-entry contexts that matter.

## Implications

- Accepted tradeoff: no cwd switch means relative paths resolve to the parent repo, so the **work phase must prefix every path it touches** — the silent-misroute footgun documented in [[2026-05-20-constraint-enter-worktree-absolute-paths]] becomes the standing operating model rather than an edge case. Skill prose carries explicit guard language and points at 008.
- This is the concrete instance of [[2026-05-19-constraint-skills-must-call-tools-not-prose]]'s "name the concrete mechanism" rule for the case where *no* reliable context-switching tool exists.
- If a future harness lets `EnterWorktree` enter arbitrary registered worktrees (not just `.claude/worktrees/`), revisiting option 1 or a hybrid would restore cwd-relative ergonomics.

## Related
- [[2026-05-20-constraint-enter-worktree-absolute-paths]] — see also: the prefixed-path discipline this decision makes mandatory
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — see also: the general "name the concrete mechanism" rule this specializes
- [[2026-05-19-decision-gitignore-before-worktree]] — see also: the other half of minerva's `.minerva/worktrees/` operational lore
