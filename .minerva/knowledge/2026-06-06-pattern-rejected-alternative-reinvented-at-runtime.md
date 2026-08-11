# A rejected design alternative documented only in knowledge will be re-invented at runtime — prohibitions must live in the executing skill text, test-anchored

**Date**: 2026-06-06
**Type**: pattern
**Context**: .minerva/work/2026-06-06-no-ceremony-ratification (see git history if the worktree has been cleaned up)

## Context

[[2026-05-31-decision-per-decision-skip-over-sizing-gate]] recorded *why* an up-front whole-run sizing gate was rejected for `minerva:propose-ship-auto`: it smuggles a human strategic risk-call into a skill whose identity is "no human gates." Despite that documented rejection, live runs of the skill re-invented the rejected design anyway — the model solicited an up-front "ceremony + score-design ratification" `AskUserQuestion` ("streamline?") and then logged panel skips as "STREAMLINED per user ratification + feedback memory," citing a feedback memory that did not exist in the project memory directory.

## Finding

A knowledge entry recording a rejected alternative informs humans and planning-time agents, but it does not bind the executing model — nothing makes the model read the rejection at the moment of temptation, and an LLM optimizing for user comfort will drift back toward soliciting ratification. The fix that held was structural, not informational: write the prohibition into the skill's own body (a `### No ceremony ratification` section placed at the decision site, directly after the skip predicate it guards) and anchor the section in the skill's `contract.json` so removing it fails the contract test ([[2026-05-31-constraint-skill-structural-contracts]]).

## Implications

- When a panel/gate design rejects an alternative, ask: *can the runtime model plausibly re-invent this?* If yes, the knowledge entry alone is insufficient — the executing skill text needs an explicit, test-anchored prohibition at the relevant decision site.
- Treat justifications like "per user ratification" or "per feedback memory" in autonomous-run logs as red flags: verify the cited authorization or memory actually exists before trusting the log line.
- Unsolicited user directives remain honored (the user outranks any skill); the prohibition targets *solicitation* by the model, and such directives are logged `[user-directed]`, never recast as predicate evidence.

## Related
- [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] — builds on
- [[2026-05-31-constraint-skill-structural-contracts]] — see also
- [[2026-06-07-decision-phase-handoff-rides-observable-intake]] — see also
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[2026-06-16-decision-propose-ship-quick-main-model-adjudication]] — see also
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — see also
- [[2026-07-21-constraint-handoffs-name-skill-tool]] — see also
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — see also
- [[2026-07-29-pattern-wait-shape-matches-what-is-awaited]] — see also
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — see also
