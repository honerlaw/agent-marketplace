---
name: grill-plan
description: Use when a plan has just been drafted in conversation and needs stress-testing before approval — invoked by `minerva:propose` after approach selection and by `minerva:replan` after the new-plan brainstorm, also usable standalone on any drafted plan. Interviews the user relentlessly about the drafted plan, one question at a time, with the LLM's recommended answer leading each question, until shared understanding is reached.
---

Stress-test a drafted plan by interviewing the user about it until shared understanding is reached. Modeled on mattpocock/skills' `productivity/grill-me`.

## Inputs

A plan is already in conversation context. It may be:

- A `minerva:propose` design draft (Goal / Why / Approach / Success criteria / Open Questions), not yet written to disk.
- A `minerva:replan` entry draft (Original plan / What changed / New plan), not yet appended to `replan.md`.
- An ad-hoc plan the user has shared or pointed at (e.g., an existing `proposal.md` they want re-grilled).

No flag distinguishes these — read the conversation and act on whichever plan is in front of you.

## Protocol

Walk down the decision tree of the drafted plan one question at a time, resolving each branch before moving on.

1. **Ask one question at a time.** Never batch. Wait for the user's answer before asking the next.

2. **Lead with your recommended answer.** For every question, state what you think the answer is based on the draft and project context, then ask the user to confirm or correct. Example: "The Approach says X. I'd expect this means Y because Z — is that right?"

3. **Prefer codebase exploration over asking.** If a question can be resolved by reading code, `.minerva/knowledge/`, prior proposals, or other repo files, do that instead of asking the user. Only ask when the answer genuinely lives in the user's head.

4. **Push on the load-bearing parts.** Probe assumptions the plan is leaning on, ambiguities a reader could resolve two ways, success criteria that aren't objectively checkable, edge cases the Approach doesn't address, scope that might be drifting. Don't run a fixed checklist — let the plan itself tell you what to probe.

5. **Edit the draft as you go.** When an answer shifts the plan, update the affected draft sections in place in conversation memory before continuing. The plan that exits this skill is the plan that gets approved and written, so it must already reflect everything surfaced here.

6. **Stop when shared understanding is reached.** Termination conditions:
   - You judge that no further material gaps remain.
   - The user signals stop: "good enough", "stop grilling", "ship it", "move on", or similar.
   - The user says the draft is ready to proceed (distinct from the formal per-section approval the caller skill will run next — this is just a "done grilling" signal).

   When you stop, summarize what changed in the draft (if anything) and hand control back to the caller skill.

## Out of scope

- File writes — the caller skill (`minerva:propose`, `minerva:replan`) owns persistence.
- Approval gates — the caller skill runs its own approval flow after this skill returns.
- Scope re-decomposition — if grilling reveals the plan should be split into multiple work units, surface that to the user and return; the caller decides how to handle it.
