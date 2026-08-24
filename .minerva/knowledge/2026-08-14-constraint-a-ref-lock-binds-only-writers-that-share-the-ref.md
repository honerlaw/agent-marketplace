# A ref lock binds only the writers that push that ref

**Date**: 2026-08-14
**Type**: constraint
**Summary**: an atomic-push lock excludes nothing from a second writer that pushes a different branch name
**Context**: .minerva/work/2026-08-14-cleanup-stands-down-for-ci

## Context
`minerva:cleanup`'s reconciliation is serialised by [[2026-08-05-pattern-read-then-act-is-not-a-lock]]:
the open-PR check is an early-out, and the real mutual exclusion is the non-forced push to
the fixed `minerva/reconcile` ref. That reasoning is sound and the entry states its
precondition — *a fixed branch name*.

A consumer repo then installed a CI job that reconciles on merge. It pushes a **unique**
branch per run (`minerva/reconcile-ci/<run_id>`, so that concurrent runs cannot collide
with each other). Both writers now edit `index.md`, and nothing serialises them: there is
no contended ref, so no push is ever rejected and the loser is never told it lost.

The early-out could not catch it either. `gh pr list --head minerva/reconcile` takes an
**exact** branch name, so an open `minerva/reconcile-ci/31727177896` is invisible to it and
the check reports clear while a reconciliation is in flight.

It stayed quiet only because an operator happened to check the CI run by hand before
letting cleanup proceed.

## Finding
**An atomic-push lock is a lock over one ref, not over a resource.** It excludes exactly
the writers that push that ref and is silent about every other writer touching the same
file. The moment a second writer picks a different branch name — for a good reason, here to
avoid a different collision — the exclusion is gone, and its absence produces no error at
all.

Two consequences for any design that leans on a ref as its lock:

- **State the resource the lock protects, not just the ref.** "The push is the lock" reads
  as a property of `index.md`; it is a property of `minerva/reconcile`. A reader adding a
  writer will check whether their change is safe against the stated invariant, and it is —
  their branch never collides with anything.
- **A prefix, not an exact name, is the honest probe.** Any check that asks "is a
  reconciliation already in flight?" must match the family of branches that answer yes.
  Exact-match probes fail closed on the sibling they were never told about.

The fix here was not to make the CI job share the ref — its unique branches exist to solve
a real problem — but to detect the second writer and have the first stand down. Where two
writers cannot be serialised, the answer is that only one of them runs.

## Related
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — builds on: the lock this qualifies, and whose stated precondition is the whole point
- [[2026-08-05-decision-promote-add-only-reconcile-on-default]] — see also: the design whose single-writer assumption a CI reconciler breaks
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — see also
- [[2026-08-24-pattern-a-lock-on-a-derived-name-does-not-cover-the-source]] — see also
