---
name: propose-ship
description: Use when the user invokes `minerva:propose-ship`, wants to run the full minerva lifecycle end-to-end in one command, or says things like "propose and ship", "full lifecycle", "start to finish", "kick off and ship". Orchestrates propose → work → promote → review → ship by delegating to each skill in sequence with no logic duplication. Always starts fresh from the propose phase.
---

Orchestrate the full minerva lifecycle in one invocation by delegating to each skill in order. This skill contains no logic of its own — it is a thin conductor.

## Phase sequence

```
minerva:propose → minerva:work → minerva:promote → minerva:review → minerva:ship
```

Invoke each phase via the `Skill` tool in this exact order. Let each skill's own instructions handle all interactive parts, completion signals, and internal logic. Do not reproduce or shadow any skill's behavior here.

## Handoff rules

- **Between all phases except review → ship**: hand off automatically once the previous skill reaches its natural completion point. Do not prompt the user to continue.
- **After `minerva:review`**: this is the single gate. If the review surfaces any issues (spec-fidelity gaps, code problems, or anything flagged for triage), **pause and present the findings to the user**. Wait for explicit confirmation before invoking `minerva:ship`. If the review is clean (no issues flagged), hand off to `minerva:ship` automatically.

## Entry point

Always start at `minerva:propose`. Do not attempt to detect or resume mid-lifecycle state. If the user already has a work unit in progress, they should invoke the individual skills directly.

## Execution

1. Invoke `minerva:propose` via the `Skill` tool. Wait for it to complete (proposal files written and approved).
2. Invoke `minerva:work` via the `Skill` tool. Stay engaged through the work phase; `minerva:work` is session-spanning and does not emit a discrete completion signal. Advance to `minerva:promote` only once the user explicitly signals that implementation is complete.
3. Invoke `minerva:promote` via the `Skill` tool. Wait for it to complete.
4. Invoke `minerva:review` via the `Skill` tool. Wait for it to complete, then apply the review gate above.
5. Invoke `minerva:ship` via the `Skill` tool.

## Out of scope

This skill does not define what "done" means for any phase — each skill defines its own completion signal. It does not add checkpoints, summaries, or status messages between phases beyond the review gate.
