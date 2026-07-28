# Skills must invoke tools directly, not describe actions in prose

**Date**: 2026-05-19
**Type**: constraint
**Context**: .minerva/work/008-work-in-git-worktree

## Context

The initial `minerva:work` SKILL.md instructed the model to "switch to the worktree" and "treat it as the working directory for all subsequent steps." This is prose describing an intent, not an instruction to call a tool. In practice, the model used absolute paths instead of actually switching context — the session's working directory never changed.

## Finding

When a skill requires the model to change execution context (working directory, branch, environment), it must instruct the model to call the specific tool that enacts the change — not describe the desired state. Where **no** tool reliably enacts the change, the skill must instead spell out the concrete mechanism that substitutes for it. minerva's worktrees are the live example: the `EnterWorktree` tool only reliably enters worktrees under `.claude/worktrees/`, and minerva's live under `.minerva/worktrees/`, so minerva never switches context into them — it addresses them by worktree-prefixed file paths and `git -C .minerva/worktrees/<NNN-slug>` commands instead (see [[008-constraint-enter-worktree-absolute-paths]]). Either way, prose like "work inside the worktree" is insufficient on its own.

## Implications

- Skill authors must identify the concrete tool call for every context-switching step and name it explicitly in the skill prose.
- Prose like "work inside X" or "treat Y as the working directory" is insufficient on its own — pair it with the tool invocation.
- This applies to any skill step that changes or pins execution context — whether via a context-switching tool, or (as with worktrees) via explicit path / `git -C` addressing when no reliable tool exists.

## Related
- [[008-constraint-enter-worktree-absolute-paths]] — see also
- [[021-constraint-skill-wraps-script-via-importable-api]] — see also
- [[031-decision-phase-handoff-rides-observable-intake]] — see also
- [[044-decision-worktree-addressing-no-enterworktree]] — see also
- [[049-constraint-handoffs-name-skill-tool]] — see also
- [[050-constraint-agent-dispatch-pins-execution-mode]] — see also
