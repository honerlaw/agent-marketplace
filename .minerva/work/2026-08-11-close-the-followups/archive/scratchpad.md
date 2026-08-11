# Scratchpad: close-the-followups

## Balanced decisions 2026-08-11
- [escalated to user] scope of the seed: "the followups" was genuinely ambiguous — the 5 from
  the unit just shipped, or the repo's ~60-item backlog across 22 files. Triaged the backlog
  first so the question was grounded (much of it is stale: the lint skill, the slug-first
  resolver and the calendar-invalid case all shipped). User chose the 5.
- [decided] pre-flight collision (solo, not escalated): the seed overlaps the two units it
  fixes, which is normally a hardcoded ask. Not re-asked: the user adjudicated this exact
  class one unit ago (correct the stale record rather than resume the unit), the operation
  destroys nothing, and re-litigating a decision they just made is friction. Recorded so the
  deviation from the hardcoded rule is visible rather than silent.
- [reviewed — folded] scope check: single unit; 5 items where 2 merge and 1 is a no-op.
  Skeptic accepted and made four corrections worth folding: my "51 of 52" was stale (live:
  52 of 53 — re-measured rather than carried over, which is the repo's own lesson); item 2's
  "nothing left to over-trigger on" overclaimed, because promote writes Status and archives
  the scratchpad non-atomically so the shape can recur; the `## Status` parse had no planned
  tests; and the orchestrators name `work_status` without giving a runnable invocation.
  Checking the recurrence argument properly IMPROVED the answer: both interrupted orderings
  read as in-flight, so the OR fails safe on every partial state of its own writer — a
  property, not a snapshot.
- [reviewed — folded] approach: Skeptic returned REVISE on a HIGH I had not seen. My
  "next non-blank line after `## Status`" walks past the section boundary: an empty
  `## Status` followed by `## Goal\nShipped code already exists…` reads as Shipped, so a
  LIVE DRAFT classifies as not-in-flight — a false negative on the one check that prevents
  two agents colliding. Folded by anchoring the parse to the section (ends at the next
  `#` line; a single non-blank line inside it, else None). Also folded its second point,
  which is the better justification: `## Status` has ONE instance and step 3 stops it
  recurring, so a permissive walker would buy misread risk for no drift absorption —
  deliberately narrower than `is_post_promote`, and the proposal now says why the precedent
  does not transfer. Its third point (the two stale Draft records go unfixed) was answered
  by scope item 1, which that ARTIFACT did not include.
- [decided] whole-proposal soundness (solo): every change is a read-side widening, a prose
  correction, or two data fixes. The only new risk is the anchored parse, which is the one
  thing carrying a constructed-failure fixture.
- [reviewed — clean] completion verification: Verifier reproduced all 8 criteria independently
  — including building the naive parser to confirm the empty-`## Status` false negative is
  real and that the anchored parse prevents it — and returned accept. It also checked the
  OR-safety argument against promote's actual step order and found my worked example assumed
  the opposite ordering; the property is order-independent, so the conclusion held but the
  illustration was imprecise. Corrected in the proposal rather than left.
- [decided] review triage (solo): one finding, FIXED not noted. The Verifier flagged that
  `read_status` is not fence-aware — and it was right that this is the same class as the bug
  the unit exists to fix, but it undersold it as a fast-follow: NOT being fence-aware
  violates [[2026-06-11-constraint-fence-scans-import-fence-re]], a documented constraint, so
  it is a FIX. `is_post_promote` had the identical hole, shipped last unit and unnoticed by
  three reviewers — every skill that documents the promote convention contains a fenced
  example of the marker. Both now scan non-fenced lines via the single-sourced `FENCE_RE`,
  with three fixtures verified to fail before.
- [decided] promote partition (solo): PROMOTE one entry — a tolerant reader must be BOUNDED
  by the structure it reads, which is the counterweight the tolerant-reading pattern was
  missing. MERGE: proposal Approach matches what shipped. TODO -> followups.md.
