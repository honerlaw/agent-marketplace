# A defect earns a tracker slot only if it is urgent and too large to absorb

**Date**: 2026-09-23
**Type**: decision
**Summary**: Follow-up issues need failure scenario, critical/high priority, and too-large-to-absorb; small defects fixed in-unit
**Context**: .minerva/work/2026-09-23-follow-ups-must-earn-filing (see git history if the worktree has been cleaned up)

## Context
The 2026-08-27 deferral bar admitted any item with a writable failure scenario. It still
produced two or three follow-up issues per requested unit of work. Review triage made a defect FIX
only "if it belongs to this diff", so small defects in adjacent code were filed. `medium`
priority ("we should eventually do this") was the default when an item gave no signal. Both
open followups at the time (#98, #113) carried it.

## Finding
The bar in `skills/promote/references/deferral-bar.md` now takes three conditions: a defect
(failure scenario), valuable (`critical`/`high`; `medium` retired like `low` before it), and too
large to absorb (needs its own design, changes a public interface or contract, or materially
widens the PR). A defect that can be absorbed is **fixed in the current unit, even outside the
diff** (outlet 0, tried first). Filing is soft-capped at one issue per unit. A second issue
carries a written justification in its body.

## Implications
- Absorption is bounded (local, no new design decision, no interface change, small beside the
  unit's change), so fix-now does not license scope creep. Absorbed fixes are logged
  `- Absorbed fix:` and review's spec-fidelity lens treats them as in scope.
- **Code written after review needs a path back to review.** An absorbable defect found only at
  promote is not fixed inside promote. Promote stops, the fix goes back through review, and then
  promote re-runs. The first draft of this rule said "fix it before ship". An independent
  reviewer caught that this ships unreviewed code under every orchestrator.
- The bar is not retroactive. Existing `priority: medium` issues stay as filed.

## Related
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — why the bar states what qualifies, not what is excluded
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — the review-bypass gap was wiring the author missed
