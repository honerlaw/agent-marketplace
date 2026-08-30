# An anchor on a clause's framing leaves the clause itself deletable

**Date**: 2026-08-30
**Type**: pattern
**Summary**: anchor the sentence that does the work, not the heading or lead-in that introduces it
**Context**: .minerva/work/2026-08-30-cross-session-inform-only (see git history if the worktree has been cleaned up)

## Context
A new protocol file was written, and its load-bearing clauses were pinned with
`evals/<skill>/contract.json` anchors so a later edit could not quietly delete them. The same
mistake was then made **twice in one work unit**, caught by two different mechanisms:

- **Code review** found the boundary anchor was the literal `"adds to their workstream"` — a
  string occurring only in the section's `##` heading. The body underneath it (the carve-out
  explaining that the rule bans delegation, not questions) matched no anchor. Deleting the
  entire body left the suite green.
- **The completion gate's Verifier** found the escalation-forms anchor covered the
  *mid-lifecycle* bullet (`continue / modify / stop`) but not the *intake* bullet beside it.
  Deleting the intake form wholesale left `test_body_anchors[propose]` green — while the
  work unit's own scratchpad recorded that finding as fixed.

Both anchors were written by the same author who wrote the clauses, moments after deciding they
were load-bearing.

## Finding
**An author pins the phrase they just typed, and the phrase they just typed is usually the
label, not the rule.** A heading, a lead-in, or a topic sentence is the most memorable string in
a section and the least load-bearing one — it survives every edit that guts the section beneath
it. The anchor then attests that a requirement is protected while the requirement is deletable.

This is the same family as [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]],
which scopes an assertion to the *region* that does the work, and
[[2026-08-10-pattern-presence-assertions-rot-into-green-lies]], which covers the general case.
The variant here is **within** a region: several clauses sit under one heading, only some carry
the enforcement, and the anchor lands on whichever the author thought of first.

The recurrence is the point. Knowing the pattern did not prevent it — the author of the second
instance had just fixed the first.

## Implications
- Anchor the **clause that does the work**, never its heading. If a section states a rule and
  then explains it, the rule is what needs pinning; the explanation is what keeps a loose check
  green.
- Where a section contains several parallel clauses that are each individually load-bearing —
  two escalation forms, three dispositions — each one needs its own anchor. Anchoring the
  section is anchoring none of them.
- **Delete it and watch.** Per [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]],
  the only reliable way to learn which string an anchor actually protects is to remove the
  clause and observe whether the suite goes red. Reading the anchor list cannot tell you: both
  defects above looked correct in review.
- Reviewing an author's own anchors is low-yield; both instances here were found by a
  fresh-context reader running the deletion, not by re-reading.

## Related
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — sharpens
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — see also
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
