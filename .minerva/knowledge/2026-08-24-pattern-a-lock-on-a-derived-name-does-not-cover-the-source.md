# A lock on a derived name does not cover the thing the name was derived from

**Date**: 2026-08-24
**Type**: pattern
**Summary**: name the resource an atomic primitive protects, not just the ref — a slug lock does not serialize two sessions working the same goal
**Context**: .minerva/work/2026-08-24-cross-session-preflight

## Context
A pre-flight check for concurrent work needed an honest answer to
[[2026-08-05-pattern-read-then-act-is-not-a-lock]]: if a check-then-act read is not mutual
exclusion, what *is* the atomic primitive here? The obvious answer was
`git worktree add -b <date-slug>` — a ref create, genuinely atomic, so of two sessions
choosing that slug exactly one wins. The draft named it as the backstop and moved on.

## Finding
**That backstop covers the slug, not the goal — and the goal is what collides.**

Two sessions handed the same request will produce *different slugs*, because a slug is a
human-ish summary of intent and two summarizations of one idea rarely match byte-for-byte.
The ref lock binds only writers that share the ref
([[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]]), so for the
case that actually motivated the feature — two sessions independently starting the same
work — **there is no atomic backstop at all**.

The defect is a category error that is easy to miss precisely because the primitive is
real: the lock is on a **derived** name, and the collision is on the **source** the name
was derived from. A derivation that is not injective — many goals to one slug, or one goal
to many slugs — breaks the correspondence in whichever direction it is non-injective. Here
it is one goal → many slugs, so the lock under-covers.

## Implications
- When naming an atomic primitive as a guard, write down **the resource it protects** and
  check that it is the same resource that collides. "Ref create is atomic" is true and
  irrelevant if the contended resource is not the ref.
- The remedy is not always a better lock. Here it was to **state the residual risk in the
  protocol itself**: detection covers the same-goal/different-slug case that no lock
  reaches, and a clean detection result means only *no evidence was found*.
- A guard whose limits are undocumented is worse than one with none, because the next
  reader extends it rather than replacing it — the failure mode
  [[2026-08-05-pattern-read-then-act-is-not-a-lock]] names.
- This was caught by an independent reviewer *that had been handed the constraint entry
  as background*, not by the author who had cited the same entry two paragraphs earlier.
  Citing a constraint is not applying it.

## Related
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — builds on
- [[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]] — builds on
- [[2026-08-24-reference-listagents-returns-the-whole-fleet]] — see also
- [[2026-08-28-constraint-git-branch-merged-is-wrong-in-both-directions]] — see also
