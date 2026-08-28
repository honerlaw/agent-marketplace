# A presence assertion stays green after you delete the thing it pins

**Date**: 2026-08-10
**Type**: pattern
**Summary**: `assert "x" in prose` cannot fail when x is removed from the codebase; invert it, don't delete it
**Context**: .minerva/work/2026-08-09-date-prefixed-identity

## Context
`minerva:promote` allocated entry ids by calling `scripts/knowledge_next_nnn.py`. That
mattered enough to pin with a test:

```python
def test_promote_prose_uses_the_cross_branch_allocator():
    assert "knowledge_next_nnn.py" in _promote_prose()
```

When the allocator was deleted, this test **kept passing**. It only ever asserted that
promote's prose mentions a filename — and promote's prose still did, because nobody had
edited it. The test attested that promote was correctly configured while promote was
instructing a call to a file that no longer existed.

## Finding
**An invariant written as "X is mentioned" degrades into a lie the moment X is removed,
because deleting X does not touch the text that mentions it.** The assertion and the
subject are coupled only through a human remembering they are related.

CI cannot catch this. A grep-shaped test over prose has no reference to the artifact, so
nothing breaks when the artifact goes. It is strictly worse than having no test: the green
check is positive evidence for a false claim.

The fix on removal is to **invert the assertion, not delete it** — pin the absence — and
pair it with one pinning the replacement:

```python
assert "knowledge_next_nnn" not in prose   # the retired thing stays retired
assert "date +%F" in prose                 # ...and the replacement is actually there
```

Absence alone is insufficient: it also passes if the prose stops explaining how to name an
entry at all. The pair brackets the real behaviour.

## Implications
- Deleting a module means grepping the test suite for its **name as a string**, not just
  for imports. An import breaks loudly; a string does not.
- Prefer an assertion that dereferences the subject — import the module, resolve the path,
  call the function — so removal breaks collection rather than passing silently.
- When a contract or eval pins a retired behaviour, re-point it at the replacement.
  Deleting it leaves nothing asserting the new state, which is how a rejected alternative
  gets reinvented ([[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]]).
- The tell is any test whose body is a substring check against documentation.

## Related
- [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] — builds on
- [[2026-08-10-decision-date-ids-make-identity-the-path]] — see also
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
- [[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]] — see also
- [[2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state]] — see also
- [[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]] — see also
- [[2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves]] — see also
- [[2026-08-28-pattern-a-corpus-assertion-must-survive-its-own-first-instance]] — see also
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — see also
- [[2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project]] — see also
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — see also
