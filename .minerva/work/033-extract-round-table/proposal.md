# Proposal: extract-round-table

**Date**: 2026-06-10
**Status**: Draft

## Goal
Extract the 3-agent Proponent/Skeptic/Arbiter consensus-panel protocol out of `minerva:propose-ship-auto` into a standalone `minerva:round-table` skill, as a pure behavior-preserving extraction, and rewire `propose-ship-auto` to delegate every panel call to it.

## Why
The panel protocol is general-purpose decision machinery — useful for ad-hoc judgment calls in chat, Proponent/Skeptic/Arbiter review of any drafted artifact, and as a building block for other skills — but today it is only reachable by running the full auto lifecycle. Extraction makes it independently invocable while leaving auto-run behavior unchanged.

## Approach
1. **New skill `plugins/minerva/skills/round-table/SKILL.md`** containing, moved verbatim-modulo-context-renames from `propose-ship-auto`: Dispatch (parallel Proponent+Skeptic, sequential Arbiter, fresh-context `general-purpose` subagents), the three agent brief templates, vote semantics with **quorum as a caller parameter defaulting to 2/3**, the revision round (main LLM revises; two votes max per decision), and escalation ending at "compose a focused batched `AskUserQuestion`, apply the answer" — round-table owns no run-level state.
2. **Intake** (per [[031-decision-phase-handoff-rides-observable-intake]]): the inline argument carries the decision/artifact. A **Caller mode** section lets orchestrating skills load the protocol once via the Skill tool and apply it per decision with caller-specified quorum and standing instructions.
3. **Standalone logging signal** (observable, not self-judged): if an in-flight `.minerva/work/NNN-*/scratchpad.md` is present in the working tree (or the work unit is already in session context), append the panel log line under the `## Panel decisions YYYY-MM-DD` header; otherwise the verdict lives in conversation only.
4. **Out of scope declared in the new skill**: skip predicates, decision taxonomies, escalation budgets/counters — those are caller policy; invoking round-table always convenes a panel.
5. **Edit `plugins/minerva/skills/propose-ship-auto/SKILL.md`**: replace the Dispatch / Agent briefs / Vote semantics / Revision round / Escalation subsections with delegation text — invoke `minerva:round-table` via the Skill tool at first panel need, leading with an auto-mode instruction (the same shape Phases 4.5 and 6 use), then apply its protocol at every decision point with the quorum from the decision taxonomy; escalations still increment the global escalation counter exactly as today. Keep: skip predicate, No-ceremony-ratification, decision taxonomy, failure modes/budget caps, all phases, and the `[skipped — small]` / `[user-directed]` / `[synthesis]` log prefixes (skip lines log "under the same header round-table uses"). Update the `description:` frontmatter to name the delegation; adjust the "Out of scope: modifying any existing minerva skill" wording only where it would now be self-contradictory (that line was unit-019-era framing, not a durable ban).
6. **Chores in the same commit**: add `evals/round-table/contract.json` (anchors: the three role names, the 2/3 default quorum, revision round, escalation; `cross_surface` enabled); verify `evals/propose-ship-auto/contract.json` anchors (`Proponent`, `Skeptic`, `Arbiter`, `panel`, `No ceremony ratification`) still match the edited skill — they should, since the roles stay named in its frontmatter and taxonomy; update the three catalog surfaces per [[010-constraint-minerva-skill-catalog-sync]] (plugin README skills table, using-minerva decision matrix, root README plugins cell), listing `minerva:round-table` adjacent to `grill-plan` as a utility skill, and re-excerpt `propose-ship-auto`'s rows if its description changed; run the full pytest suite.

## Success criteria
- `plugins/minerva/skills/round-table/SKILL.md` exists with the complete protocol: agent briefs, dispatch, parameterized quorum defaulting to 2/3, revision round, escalation, panel log-line format, caller mode, and the standalone logging signal.
- `propose-ship-auto/SKILL.md` contains no agent-brief templates and no vote-counting rules; its decision-taxonomy quorums, skip predicate, escalation counter, and all phase behavior are unchanged.
- A side-by-side read of the old and new text confirms behavior preservation: no quorum, vote threshold, revision budget, or escalation trigger differs; moved text changed only by context renames (e.g., "the auto skill" → "the caller").
- `tests/test_skill_contracts.py` and the full pytest suite pass, with `evals/round-table/contract.json` present.
- All three catalog surfaces list `minerva:round-table` in the same commit.

## Open Questions
- None.
