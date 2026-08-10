# Proposal: no-ceremony-ratification

**Date**: 2026-06-06
**Status**: Shipped (2026-06-06)

## Goal
Add a test-enforced "No ceremony ratification" prohibition to `minerva:propose-ship-auto` forbidding the model from soliciting user pre-authorization of reduced panel ceremony at any point in a run.

## Why
Observed auto runs invent an up-front "ceremony + score-design ratification" `AskUserQuestion` ("streamline?") and then log panel skips as "STREAMLINED per user ratification + feedback memory" — where the cited feedback memory does not exist. This behavior:

- Re-introduces the up-front whole-task sizing gate that was explicitly rejected at design time ([[2026-05-31-decision-per-decision-skip-over-sizing-gate]]: "A `--fast` flag is worse still: it smuggles a human strategic risk-call into a skill whose identity is 'no human gates.'").
- Launders per-decision skip evidence through a blanket user answer, defeating the auditability the `[skipped — small]` logging requirement exists to provide.
- Adds a human gate to a skill whose entire purpose is running without them.

## Approach
1. Add a new `### No ceremony ratification` subsection to `plugins/minerva/skills/propose-ship-auto/SKILL.md`, in the Panel protocol section immediately after `### Skip predicate (small decisions)`, stating:
   - (a) Never ask the user — up front or mid-run — to choose a ceremony level, to "streamline," or to pre-ratify/batch-authorize skips for panels that have not yet run and failed.
   - (b) Genuine escalations (a decision that failed quorum twice) remain legitimately batched per the Escalation section — the ban targets *pre*-ratification, not escalation.
   - (c) Stored preferences, memories, or prior-session feedback never widen the skip predicate, and a user answer is never valid `[skipped — small]` evidence.
   - (d) An *unsolicited* user directive to skip panels is honored (the user outranks the skill) and logged `[user-directed]` under the `## Panel decisions` header — but it must never be solicited. The `[user-directed]` prefix is also listed in the Per-decision logging vocabulary alongside `[skipped — small]` / `[synthesis]` / `[escalated to user]` (added via review finding #1).
   - (e) The skip predicate applied silently per-decision is the only de-ceremony mechanism.
2. Strengthen the pre-flight wording from "This is the single mandatory pre-run user interaction" to make it the single mandatory — and only permitted — pre-run user interaction.
3. Add `"No ceremony ratification"` to the `anchors` list in `evals/propose-ship-auto/contract.json` so removal of the section fails the contract test.

## Success criteria
- `plugins/minerva/skills/propose-ship-auto/SKILL.md` contains a `### No ceremony ratification` subsection with all five clauses (a–e).
- The pre-flight line states the in-flight collision check is the only permitted pre-run user interaction.
- `evals/propose-ship-auto/contract.json` lists `"No ceremony ratification"` as an anchor.
- `pytest` (contract tests) passes.

## Open Questions
- None.
