---
name: propose-ship
description: Runs the full minerva lifecycle end-to-end in one command with the user in the loop — a human decision gate at each phase transition. Orchestrates propose - work - review - promote - ship - cleanup by delegating to each skill in sequence with no logic duplication, refuses to start if in-flight work exists for the same intent, advances out of the work phase only on explicit user signal, and waits for the PR to actually merge before invoking cleanup. Use when the user wants the whole lifecycle while staying in control — "propose and ship", "I want to approve each step" — or when they invoke `minerva:propose-ship`.
---

Orchestrate the full minerva lifecycle in one invocation by delegating to each skill in order. This skill contains no logic of its own — it is a thin conductor.

## Phase sequence

```
minerva:propose → minerva:work → minerva:review → minerva:promote → minerva:ship → minerva:cleanup
```

`minerva:cleanup` closes the lifecycle by reconciling the knowledge wiki on the default branch — cataloguing the entries promote left pending, writing their reciprocal links, and refreshing `overview.md` when warranted — in a single auto-merging PR. None of that happens on the work-unit branch, which is what keeps concurrent minerva PRs conflict-free.

Invoke each phase via the `Skill` tool in this exact order. Let each skill's own instructions handle all interactive parts, completion signals, and internal logic. Do not reproduce or shadow any skill's behavior here.

The `minerva:propose` phase creates the work unit's branch + worktree at `.minerva/worktrees/<date-slug>/` and enters it; every downstream phase enters that worktree automatically (or stays in it if already there). `minerva:cleanup` is the only phase that runs from outside the worktree — it removes it.

(Note: review runs **before** promote so review-derived scratchpad notes flow through the promote partition. This matches `using-minerva` and `review`. Re-cycle review/promote as needed. Cleanup runs only after the PR actually merges.)


## Protocols

The full step protocols live verbatim in `references/phases.md` — **read it now, before executing**:

- **Pre-flight: detect in-flight work** — the collision check that runs before `minerva:propose`, including the runnable `work_status.unit_state(...)["in_flight"]` invocation. Call the predicate; never restate it as a string comparison.
- **Handoff rules** — what advances each phase, and the work → review signal list.
- **Entry point** — always start at `minerva:propose`; do not resume mid-lifecycle state.
- **Execution** — the eight numbered steps.
- **Phase 7 — cleanup gate** — PR-state polling, the `--cleanup-only` re-entry, and why this wait is a constant where ship's is not.

## Gates

This skill's identity is that **a human decides at every phase transition**. The one explicit gate is promote → ship: summarize what promote did, then wait for `ship it` / `proceed` / `yes`. The work → review handoff advances only on an explicit user signal, never silently.

The autonomous siblings replace those gates with machinery, and the ladder runs by how much independent scrutiny a change earns: `minerva:propose-ship-quick` (main model decides alone), `minerva:propose-ship-balanced` (one advisory reviewer at the high-signal gates), `minerva:propose-ship-auto` (3-agent consensus panels). Reach for one of those when the user wants the lifecycle run unattended; stay here when they want to approve each step.

## Out of scope

This skill does not define what "done" means for any phase — each skill defines its own completion signal. It does not add checkpoints, summaries, or status messages between phases beyond the explicit work → review trigger words, the promote → ship gate, and the cleanup gate.
