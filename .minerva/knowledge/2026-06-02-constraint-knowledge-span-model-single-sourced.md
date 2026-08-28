# The `.minerva/knowledge/` span model is single-sourced — import it, never re-derive it

**Date**: 2026-06-02
**Type**: constraint
**Context**: .minerva/work/2026-06-02-knowledge-lint-detector (see git history if the worktree has been cleaned up)

## Context

Two components now parse the knowledge-entry span model — the same `## Related`
block and supersession-banner spans: the promote-invariant guard
(`tests/test_promote_invariant.py`) and the knowledge linter
(`scripts/knowledge_lint.py`). Those spans are the machine-managed mutable surfaces
that [[2026-06-02-constraint-promote-narrowed-never-overwrite]] designates as the spec of
record. If each consumer carried its own copy of the span regexes, the two could
drift — and a linter that disagrees with the invariant guard about where a span
begins or ends would silently mis-police promote's safe-edit boundary.

## Finding

The span primitives — the banner marker/quote regexes, the `## Related` header
constant, the `^## ` section regex, and the code-fence regex — are **single-sourced
in `scripts/knowledge_spans.py`**. Both `scripts/knowledge_lint.py` and
`tests/test_promote_invariant.py` import them from there (`conftest.py` puts
`scripts/` on `sys.path`).

The durable rule is **one definition, no drift**: any future tool or test that
parses the knowledge-entry span model must **import from `scripts/knowledge_spans.py`,
not re-derive** the grammar. The module's location is incidental; the invariant is
that the span model has exactly one definition. A second, divergent definition
silently breaks the guarantee in [[2026-06-02-constraint-promote-narrowed-never-overwrite]]
that promote only ever edits within those spans.

## Implications

- Adding a new consumer of the wiki span model (e.g. the deferred Phase B.2
  `minerva:lint` skill's fix logic, or any future migration script): import the
  constants from `scripts/knowledge_spans.py`; do not copy the regexes.
- If the span grammar itself must change, change it in `knowledge_spans.py` once;
  both the invariant guard and the linter pick it up, and their tests will catch a
  break.

## Related
- [[2026-06-02-constraint-promote-narrowed-never-overwrite]] — builds on
- [[2026-06-02-decision-phase-b-deterministic-lint-detector]] — see also
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — see also
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
- [[2026-08-28-pattern-import-the-grammar-not-its-conclusion]] — see also
