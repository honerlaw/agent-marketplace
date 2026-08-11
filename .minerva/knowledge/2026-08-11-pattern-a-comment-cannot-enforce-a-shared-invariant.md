# A comment claiming two patterns agree is not a mechanism keeping them agreed

**Date**: 2026-08-11
**Type**: pattern
**Summary**: two derivations plus a comment asserting they match will drift; share one implementation, or the invariant is only a wish
**Context**: .minerva/work/2026-08-11-close-silent-reference-gaps

## Context
`knowledge_lint.RELATED_LINE_RE` carried this comment:

> Single-sourced so `knowledge_fix` cannot recognise a narrower set of edges than this
> linter reports on — a line the linter counts as an edge but the fixer skips is a
> permanent error nothing repairs and nothing refuses.

The comment was precise, correct about the stakes, and false about the code. `knowledge_fix`
did import `RELATED_LINE_RE` — so the regex was shared — but `knowledge_lint.parse_entry`
never used it. It derived its own edges from `CATALOG_LINE_RE`, which is start-anchored
only, where `RELATED_LINE_RE` is anchored at both ends:

| `## Related` line | lint (`CATALOG_LINE_RE`) | fix (`RELATED_LINE_RE`) |
|---|---|---|
| `- [[a]] — supersedes` | edge to `a` | edge to `a` |
| `- [[a]] / [[b]] — both unchanged` | edge to `a` | **nothing** |
| `- [[a]] /` | edge to `a` | **nothing** |

Every line with trailing content that is not `— label` diverged. On a 637-entry corpus,
**18 of 41 findings were neither planned nor refused** — invisible. The convergence loop
runs forever while the fixer prints "corpus clean".

The same shape, independently, in the same subsystem: `WORK_DIR_RE` was a bare
`^(\d{3,})-(.+)$` while every other id pattern used the shared
`ID_RE_SRC = (?:\d{4}-\d{2}-\d{2}|\d{3,})`. Against an already-migrated `2026-08-07-foo`
the outlier captured `2026` as the id and `08-07-foo` as the slug, so the migration
re-dated directories it had already dated — non-idempotent, on all 50-odd units of this
repo, with every `**Context**` path retargeted to the corrupted name.

## Finding
**An invariant between two pieces of code is enforced by a shared implementation or it is
not enforced at all.** Sharing a *constant* is not enough when each side still decides how
to use it; sharing a *grammar* is not enough when one site opts out of it.

The comment made this worse rather than better. It stated the invariant so convincingly
that a reader — including several who touched the file afterwards — had no reason to check
whether the code did what it said. Documentation of an invariant substitutes for
verification of it.

The tell is a comment containing "single-sourced", "must match", "kept in sync with", or
"same as" and naming another symbol. Each one marks a place where a mechanism was needed
and prose was written instead.

The fix is to make the divergence set **empty by construction**, not empty by inspection:
extract the whole operation — not the pattern it uses — into one function both sides call.
Here that was `related_edges(text) -> [(stem, label)]`, owning fence-stripping, block
selection and per-line parsing; `knowledge_fix._forward_related` became a one-line
delegate.

Widening an edge set raises a real question — what happens to edges the consumer cannot
act on? The answer came from the code, not from taste: `plan_reciprocals` already had a
`label is None` branch that appends a **refusal**. So the reported failure (neither
planned nor refused) became a visible refusal with no new machinery. **Check whether the
consumer already has a safe path for the widened case before designing one.**

## Implications
- When two sites must agree, share the *function*, not the regex or the constant. A
  regex both sides import can still be used by only one of them.
- Grep for the one pattern that does not use the shared grammar. Both defects here were
  single outliers in codebases that were otherwise consistent — and a lone outlier is
  invisible precisely because everything around it is right.
- A comment asserting an invariant should be paired with the test that fails when it
  breaks. Here the test is: derive edges both ways over the shapes that used to diverge
  and assert the sets are equal.
- Idempotency is an instance of this: a tool that consumes its own output must parse
  that output with the same grammar it writes it with.
- Related failure: a claim in prose that outlives the thing it describes
  ([[2026-08-10-pattern-presence-assertions-rot-into-green-lies]]). Same root — text and
  code coupled only by a human remembering they are related.

## Related
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on
- [[2026-06-02-constraint-knowledge-span-model-single-sourced]] — builds on
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — see also
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also
