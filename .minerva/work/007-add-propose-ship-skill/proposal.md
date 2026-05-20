# Proposal: add-propose-ship-skill

**Date**: 2026-05-19
**Status**: Draft

## Goal

Add a `minerva:propose-ship` skill that runs the complete minerva lifecycle in one invocation — brainstorm and design, implement, promote knowledge, review, and ship — by delegating to each existing skill in order with no logic duplication.

## Why

Running a full minerva lifecycle today requires manually invoking five skills in sequence. A conductor skill removes that coordination burden — one command kicks off the whole workflow, and the agent carries context forward between phases automatically.

## Approach

The skill is a thin conductor: it instructs Claude to invoke each skill in order via the `Skill` tool, letting each skill's own logic handle its interactive parts and completion signal. The skill's only responsibility is the sequence and the single review gate.

Phase order:
1. `minerva:propose` — brainstorm and get proposal approved; files written to `.minerva/work/NNN-slug/`
2. `minerva:work` — implement in a worktree, maintaining scratchpad
3. `minerva:promote` — extract durable knowledge, rewrite proposal to match reality
4. `minerva:review` — **gate**: if issues are flagged, pause and surface them for user triage; only continue after user confirms
5. `minerva:ship` — commit, PR, CI fix loop, auto-merge

No logic of its own beyond the sequence and the review gate.

## Open Questions

- None.
