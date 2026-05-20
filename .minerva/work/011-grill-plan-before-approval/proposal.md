# Proposal: grill-plan-before-approval

**Date**: 2026-05-20
**Status**: Shipped (2026-05-20)

## Goal

Add a new minerva sub-skill `minerva:grill-plan` that `minerva:propose` and `minerva:replan` both invoke immediately after the LLM has drafted a plan but before any approval gate. The new skill stress-tests the drafted plan by interviewing the user one question at a time, leading each question with the LLM's recommended answer, preferring codebase exploration over asking when applicable, and editing the in-flight draft in place when answers shift the plan. Modeled on mattpocock/skills' `productivity/grill-me`.

## Why

The current propose flow gathers requirements via clarifying questions during intake (propose step 4), drafts a design, and then gates approval per section. That gates correctness as the user perceives it, but doesn't actively interrogate the drafted plan after it's been put together. Hidden assumptions, unstated edge cases, scope creep, and vague success criteria slip through because both LLM and user can feel "shared understanding" prematurely once the draft reads well. Replan has the same gap: a new plan is proposed and approved without a second pass that pushes back on it. A dedicated grilling step against the freshly drafted plan — relentless, one-at-a-time, recommended-answer-first — surfaces those gaps before they get baked into `proposal.md` or `replan.md`.

## Approach

1. Create `plugins/minerva/skills/grill-plan/SKILL.md`. Frontmatter sets `name: grill-plan` and a description scoped to "stress-test a freshly drafted plan in conversation context before approval; invoked by minerva:propose and minerva:replan, but also usable standalone." Body is intentionally thin and posture-driven (no checklist of categories), mirroring mattpocock's `grill-me`:
   - Operate on whatever plan is currently in conversation context (drafted design from propose, or drafted replan entry from replan).
   - Walk the decision tree of the plan one question at a time. Do not batch.
   - For each question, lead with the LLM's recommended answer based on the draft and project context.
   - If a question can be resolved by reading code, `.minerva/knowledge/`, or other repo files, do that instead of asking the user.
   - When an answer shifts the in-flight draft, edit the affected draft sections in conversation memory and continue grilling.
   - Continue until shared understanding is reached or the user signals "stop" / "good enough" / "ship it".
   - Out of scope: file writes, approval gates, scope re-decomposition. Caller skill owns those.

2. Edit `plugins/minerva/skills/propose/SKILL.md`. Insert a new numbered step between current step 5 (Propose 2–3 approaches) and current step 6 (Present the design in sections). New step: "Stress-test the drafted plan. After approaches are chosen and the design has been internally drafted into Goal / Why / Approach / Success criteria / Open Questions, invoke `minerva:grill-plan` against the draft. Edit affected sections in place as answers surface. Only then proceed to per-section approval." Renumber subsequent steps (current 6 → 7, current 7 → 8) so the pre-write hard gate stays last in the Protocol section.

3. Edit `plugins/minerva/skills/replan/SKILL.md`. Insert a new numbered step between current step 4 (Propose 2–3 alternative new plans if the path forward isn't already settled) and current step 5 (Present the resulting entry for approval before writing). New step: "Stress-test the drafted replan entry. Invoke `minerva:grill-plan` against the drafted Original plan / What changed / New plan triple. Edit affected pieces in place." Renumber subsequent steps so the hard gate stays last.

4. Leave `plugins/minerva/skills/using-minerva/SKILL.md` alone. The grilling step is an internal protocol detail of propose and replan; surfacing it at the top-level user guide would add noise without changing how the user invokes anything.

5. Decisions folded from Open Questions:
   - **Standalone ad-hoc invocation is implicit, not explicit.** Write the description and body so they read naturally when triggered standalone, but don't add a dedicated "Standalone usage" section. If ad-hoc use turns out to be common, a follow-up unit can formalize it.
   - **No hard cap on grill questions.** Rely on LLM judgment plus user short-circuit phrases ("good enough", "stop grilling", "ship it"). Encode that termination condition explicitly in the skill body so the LLM knows when to stop.

## Success criteria

- `plugins/minerva/skills/grill-plan/SKILL.md` exists with valid frontmatter (`name: grill-plan` plus a description that triggers on standalone use and references the propose/replan callers) and a body covering all the directives listed in Approach step 1.
- `plugins/minerva/skills/propose/SKILL.md` contains an explicit step that names `minerva:grill-plan` and is placed after approach selection and before per-section approval; subsequent steps are renumbered consistently with no orphan references.
- `plugins/minerva/skills/replan/SKILL.md` contains an explicit step that names `minerva:grill-plan` and is placed after new-plan brainstorming and before the approval-before-writing step; subsequent steps are renumbered consistently with no orphan references.
- The grill-plan body explicitly mirrors mattpocock/grill-me's three core directives: one question at a time, recommended-answer-per-question, codebase-exploration-preferred over asking.
- The grill-plan body explicitly covers the drift-handling answer from intake: when answers shift the draft, the LLM edits draft sections in place in conversation memory rather than deferring to a post-write fixup.
- `grep -n "minerva:grill-plan" plugins/minerva/skills/propose/SKILL.md plugins/minerva/skills/replan/SKILL.md` returns at least one hit per file.

## Open Questions

(None — Open Questions were resolved into Approach step 5 before implementation began.)
