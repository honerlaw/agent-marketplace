# Deriving a view from data that was only displayed makes its latent mislabels live

**Date**: 2026-10-01
**Type**: pattern
**Theme**: knowledge-wiki
**Summary**: data only ever displayed hides mislabels; deriving a view from it turns each into a wrong answer
**Context**: .minerva/work/2026-10-01-derive-knowledge-aggregates

## Context
Switching the knowledge catalog from a stored `index.md` to one derived from each entry's
`## Related` labels, the first derived run marked the live 2026-06-13 constraint as
superseded by the *older* 2026-06-10 entry it actually replaced. The 06-10 entry had
carried `— supersedes: catalog surface is now pages/index.md` for months, a label written
in the wrong direction (it meant "superseded by"). Nothing had ever acted on it: under the
stored design the label was prose a human might read, and the banner reconciliation wrote
came from a different edge. The moment the label became the input to a computed answer,
the mislabel became a false claim that a current rule was retired.

## Finding
**Data that has only ever been displayed has never been checked.** A field a reader skims
can be wrong indefinitely, because a human reading it in context silently corrects it. A
derivation has no context: it executes the field as written. So moving any view from
"stored, hand-maintained" to "derived from fields that already exist" is also the first
real validation those fields have ever had, and it will surface their latent errors as
wrong outputs, not as parse failures.

Two defences, both needed:

- **Diff the derived view against the stored one before deleting the stored one.** Every
  disagreement is either a bug in the derivation or a latent error in the data; both need a
  decision. Here the stored index had no supersession marks, so the comparison would have
  flagged all derived ones for review.
- **Encode the invariants the old human reader applied.** A reader knew an older entry
  cannot retire a newer one; the derivation now ignores such an edge and lint reports it,
  rather than trusting the label.

## Implications
- When a stored aggregate is replaced by a derivation anywhere, expect a burst of data
  fixes in the same change, and budget for reviewing the first derived output line by line.
- Any field that becomes machine-read for the first time deserves a lint rule for the
  sanity checks a human applied implicitly (direction, ordering, existence).

## Related
- [[2026-10-01-decision-knowledge-aggregates-are-derived-on-read]] — the change that turned the label into an input
- [[2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state]] — see also: another case where a check's input was never what the author assumed
