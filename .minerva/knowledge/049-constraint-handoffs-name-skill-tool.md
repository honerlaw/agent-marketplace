# Skill-to-skill handoffs name the Skill tool and the argument

**Date**: 2026-07-21
**Type**: constraint
**Context**: .minerva/work/046-skill-best-practices-audit (see git history if the worktree has been cleaned up)

## Context
Unit 046's handoff diagnosis: the mid-lifecycle handoffs observed to fail in live runs
were exactly those written as bare prose — "run the `minerva:replan` protocol",
"re-enter `minerva:review`", "invoke `minerva:cleanup <NNN-slug> --yes`" — while the
handoffs that worked reliably named their mechanism explicitly (explore→propose:
"invoke the skill via the `Skill` tool, passing the converged direction as the inline
argument").

## Finding
Every skill-to-skill handoff in skill text names the mechanism: **invoke the target
skill via the `Skill` tool**, plus the argument (or "no argument — reads X from
conversation") to pass. Bare-prose handoffs license a literal-reading model to inline
the target's protocol from memory instead of loading it — skipping the target's
gates, templates, and file writes, which is the observed failure mode. Roughly ten
handoff sites were standardized to the explicit form in unit 046.

## Implications
New or edited skills use the explicit form for every handoff. This extends the
tools-not-prose rule and the observable-intake rule down to handoff phrasing; per the
recurrence pattern, a convention documented only in knowledge recurs at runtime — the
phrasing must live in the executing skill text, and an enforcement lint is seeded in
unit 046's followups.md.

## Related
- [[007-constraint-skills-must-call-tools-not-prose]] — builds on
- [[031-decision-phase-handoff-rides-observable-intake]] — builds on
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — see also
