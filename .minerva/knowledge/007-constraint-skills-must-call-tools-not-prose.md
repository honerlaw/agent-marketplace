# Skills must invoke tools directly, not describe actions in prose

**Date**: 2026-05-19
**Type**: constraint
**Context**: .minerva/work/008-work-in-git-worktree

## Context

The initial `minerva:work` SKILL.md instructed the model to "switch to the worktree" and "treat it as the working directory for all subsequent steps." This is prose describing an intent, not an instruction to call a tool. In practice, the model used absolute paths instead of actually switching context — the session's working directory never changed.

## Finding

When a skill requires the model to change execution context (working directory, branch, environment), it must instruct the model to call the specific tool that enacts the change — not describe the desired state. For worktree switching, this means explicitly calling `EnterWorktree` with the `path` parameter pointing at the existing worktree directory.

## Implications

- Skill authors must identify the concrete tool call for every context-switching step and name it explicitly in the skill prose.
- Prose like "work inside X" or "treat Y as the working directory" is insufficient on its own — pair it with the tool invocation.
- This applies to any future skills that use `EnterWorktree`, `ExitWorktree`, or analogous context-switching tools.

## Related
- [[008-constraint-enter-worktree-absolute-paths]] — see also
- [[021-constraint-skill-wraps-script-via-importable-api]] — see also
- [[031-decision-phase-handoff-rides-observable-intake]] — see also
