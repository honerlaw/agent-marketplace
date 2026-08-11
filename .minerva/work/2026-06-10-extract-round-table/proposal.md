# Proposal: extract-round-table

**Date**: 2026-06-10
**Status**: Shipped (2026-06-10)

## Goal
Extract the 3-agent Proponent/Skeptic/Arbiter consensus-panel protocol out of `minerva:propose-ship-auto` into a standalone `minerva:round-table` skill, as a pure behavior-preserving extraction, and rewire `propose-ship-auto` to delegate every panel call to it.

## Why
The panel protocol is general-purpose decision machinery — useful for ad-hoc judgment calls in chat, Proponent/Skeptic/Arbiter review of any drafted artifact, and as a building block for other skills — but it was only reachable by running the full auto lifecycle. Extraction makes it independently invocable while leaving auto-run behavior unchanged.

## Approach
What shipped (see [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] for the mechanism-vs-policy boundary decision and rejected alternatives):

1. **New skill `plugins/minerva/skills/round-table/SKILL.md`** holding the panel mechanism, moved from `propose-ship-auto`: Dispatch (parallel Proponent+Skeptic, sequential Arbiter, fresh-context `general-purpose` subagents), the three agent brief templates (byte-identical to the originals), vote semantics with quorum as a caller parameter defaulting to 2/3, the revision round (two votes max), escalation ending at "compose batched `AskUserQuestion`, apply the answer", and the panel log-line format. Intake is the inline argument per [[2026-06-07-decision-phase-handoff-rides-observable-intake]]; a **Caller mode** section defines the load-once / apply-per-decision composition for orchestrators; the standalone logging destination rides an observable signal (in-flight work-unit scratchpad present → log there; none → conversation-only; several unnamed → ask).
2. **Moved-text deltas** (everything else verbatim): quorum parameterized to "caller-specified, default 2/3"; the Skeptic-dissent log destination generalized to "the caller's next phase — or the user"; escalation step 3 (global counter increment) replaced by a caller-owns-run-level-state rule, the counter rule itself surviving in `propose-ship-auto`'s Delegation and Failure-modes sections; plus two behaviorally inert additions — the "resume the flow" sentence relocated to the caller's Delegation bullet, and a multiple-in-flight-units logging disambiguation ("ask which one") new in round-table.
3. **`propose-ship-auto` edits**: the five inlined subsections (Dispatch / Agent briefs / Vote semantics / Revision round / Escalation) replaced by one "Delegation to `minerva:round-table`" subsection (Skill-tool invocation at first panel need with a standing auto-mode instruction; taxonomy quorums override round-table's default; escalation counter and per-decision budget restated as orchestrator-owned). Kept unchanged: skip predicate, No-ceremony-ratification, decision taxonomy, per-decision logging with its `[skipped — small]`/`[user-directed]`/`[synthesis]` prefixes, failure modes, and all seven phases. Frontmatter description names the delegation; the Out-of-scope additivity bullet was reworded to "at run time" and now lists `minerva:round-table` among never-altered skills.
4. **Chores in the same change**: `evals/round-table/contract.json` (anchors on the three roles, the 2/3 default, the two-vote cap, caller mode, always-convenes; `cross_surface` enabled); `propose-ship-auto`'s existing contract anchors verified still passing; all three catalog surfaces updated per [[2026-05-21-constraint-minerva-skill-catalog-sync]] (plugin README row adjacent to `grill-plan`, using-minerva matrix row, root README cell token) with `propose-ship-auto`'s rows re-excerpted to name the delegation.

## Success criteria
- `plugins/minerva/skills/round-table/SKILL.md` exists with the complete protocol: agent briefs, dispatch, parameterized quorum defaulting to 2/3, revision round, escalation, panel log-line format, caller mode, and the standalone logging signal. ✓
- `propose-ship-auto/SKILL.md` contains no agent-brief templates and no vote-counting rules; its decision-taxonomy quorums, skip predicate, escalation counter, and all phase behavior are unchanged. ✓
- A side-by-side read of the old and new text confirms behavior preservation: no quorum, vote threshold, revision budget, or escalation trigger differs; moved text changed only by context renames plus the two behaviorally inert additions itemized in Approach §2. ✓ (verified mechanically: byte-identical briefs, diff-confined changes)
- `tests/test_skill_contracts.py` and the CI-scoped pytest suite (the 8 files named in `.github/workflows/evals.yml`; the files outside that scope fail on main for pre-existing, unrelated reasons) pass, with `evals/round-table/contract.json` present. ✓ (175/175)
- All three catalog surfaces list `minerva:round-table` in the same commit. ✓ (cross_surface-enforced)

## Open Questions
- None.
