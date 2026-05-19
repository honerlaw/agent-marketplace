# Proposal: improve-propose-replan-intake

**Date**: 2026-05-18
**Status**: Shipped (2026-05-18)

## Goal

Update the `minerva:propose` and `minerva:replan` skills so that:

1. Neither command accepts a slug as an argument — slugs are derived silently from the agreed goal.
2. `/propose` accepts an optional description inline (e.g. `/propose "add rate limiting"`), which becomes the starting point for the Q&A.
3. When invoked with no argument and no relevant current-session chat history, `/propose` asks the user what they want to build.
4. When invoked with no argument but relevant current-session chat history exists, `/propose` reads the history and repo context, infers a likely intent, and asks the user to confirm or redirect before proceeding.
5. `/replan` removes its explicit `NNN-slug` / substring-match argument forms and uses current-session context to infer the target work unit, falling back to most-recently-modified.

## Why

- **Slugs are an implementation detail, not a user concern.** Today, users must think up a slug before they've even described what they want to build. Deriving it from the agreed goal removes friction and produces more consistent, meaningful names.
- **Context-aware intake is more natural.** When a user types `/propose` mid-conversation, they've already been thinking about what to build — the skill should meet them there rather than ignoring that context.
- **Inline descriptions reduce ceremony.** If the user already knows the goal, they shouldn't have to sit through an open-ended question before work begins.

## Approach

1. **Update `/propose` usage.** Remove `<slug>` from the documented invocation. New forms: `/propose` and `/propose "description"`.

2. **Add context-sensitive intake step** at the top of the `/propose` Protocol:
   - Description inline → use as draft goal, confirm/refine before proceeding.
   - No description, current-session chat history present → infer likely intent, state it, ask to confirm or redirect.
   - No description, no relevant history → ask "What would you like to build?"

3. **Move slug pre-flight check.** Derive slug silently from the confirmed goal title (normalize: lowercase, spaces/underscores → `-`, strip non-`[a-z0-9-]`). Run the duplicate-check against `.minerva/work/` at that point, just before writing files. Slug is shown implicitly in the `created .minerva/work/NNN-<slug>/` confirmation line — no separate approval step.

4. **Update `/replan` usage.** Remove explicit `NNN-slug` / substring-match argument forms. Target resolution:
   - Check current-session chat history for a mentioned work unit.
   - Fall back to most-recently-modified `.minerva/work/NNN-*/`.
   - If multiple candidates and context is ambiguous, list them and ask the user which.
   - Update the "no work units found" error to reference `/propose` (no slug arg).

5. **No other changes.** Q&A loop, approach proposals, section-by-section approval, and file-write steps in both commands remain unchanged.

