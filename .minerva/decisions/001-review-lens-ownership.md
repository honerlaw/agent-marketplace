# Each review lens has a clear owner: minerva owns spec/knowledge, code-review owns quality

**Date**: 2026-05-19
**Context**: .minerva/work/006-review-calls-code-review

## Context

`minerva:review` originally had three finding lenses: spec fidelity, knowledge compliance, and general quality. When `code-review:code-review` was integrated into the review flow, there was a question of whether the General quality lens should stay (overlap) or be removed (clean ownership).

## Decision

Remove the General quality lens from the minerva audit. `code-review:code-review` owns general code quality — bugs, missing tests, unhandled edge cases. `minerva:review`'s own lenses are spec fidelity (did you build what was designed?) and knowledge compliance (does the change respect documented patterns and constraints?). No lens is duplicated across the two.

## Consequences

- The minerva audit is narrower and more focused — it can only surface findings the design documents make possible.
- `code-review:code-review` is the authoritative source for code quality findings; future changes to quality heuristics happen there, not in the minerva skill.
- Any future review lens added to `minerva:review` must be minerva-specific (derivable from proposal, replan, or knowledge artifacts) — general quality findings belong in `code-review:code-review`.
