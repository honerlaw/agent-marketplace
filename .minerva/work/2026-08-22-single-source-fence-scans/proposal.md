# Proposal: single-source-fence-scans

**Date**: 2026-08-22
**Status**: Shipped (2026-08-22)
**Closes**: #88

## Goal

Close #88 — `_unfenced_lines` and `_unfenced` duplicated the same fence-toggle loop across
two test modules. Investigation widened it: there were **four** copies, not two, and three
further `FENCE_RE` readers that look identical and must *not* be unified.

## Why

`FENCE_RE` has been single-sourced in `knowledge_spans.py` since the grammar was written.
The six-line loop *around* it never was, and copies accumulated in `knowledge_lint`,
`work_status`, `tests/test_skill_budget.py` and `tests/test_skill_contracts.py`. That is the
two-derivations-one-rule shape
[[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] names — and it sat inside
the very test layer extended to enforce that pattern elsewhere.

## Approach

**The primitive.** `knowledge_spans.unfenced(lines)` yields `(index, line)` for lines outside
fences; `unfenced_lines(body)` is the list convenience. It lives beside `FENCE_RE`, in the
module that already declares itself the single source of truth for this format.

**Four readers converged**: `knowledge_lint._strip_fences` (kept as a name — `knowledge_fix`
imports it and the fence-awareness gate recognises it), `work_status._nonfenced`, and the two
test helpers.

**Three readers deliberately did not**, and the difference is real rather than cosmetic —
exactly what [[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]]
warns to check before unifying:

| reader | why it differs |
|---|---|
| `knowledge_edits._fence_flags` | returns a boolean **per line including delimiters**; the byte-identity guard needs a verdict for every line, not a filtered subset. Its own docstring already said it is "deliberately NOT a `_strip_fences` content filter". |
| `knowledge_rename` | **keeps** fences and fenced content in its output — it rewrites text rather than filtering it, so dropping lines would corrupt the file. |
| `tests/test_skill_dispatch._fence_of` | measures the fence's **run length** for pairing, which the shared regex does not expose. Its docstring calls this "the sanctioned parser-built-on-it form". |

**The refactor is enforced, not just performed.** `test_only_sanctioned_readers_write_their_own_fence_loop`
fails on any new `FENCE_RE.match` loop outside the exemption map, and
`test_every_fence_loop_exemption_still_exists_and_still_loops` fails when an exemption goes
stale — so the map cannot decay into a permission slip nobody re-checks. The checker excludes
itself by identity, not by an exemption entry, so it can never be mistaken for a granted pass.
The fence-awareness gate's `FENCE_AWARE_RE` now recognises `unfenced` as a sanctioned form.

Unused `FENCE_RE` imports left behind in the three converged modules were removed.

## Success criteria

1. `pytest tests/` passes — **645**, up from 641.
2. Exactly four files contain a `FENCE_RE.match` loop, and each is in the exemption map
   with a stated reason.
3. Both new gates verified by mutation: a probe module re-deriving the loop fails the first;
   neutering `knowledge_rename`'s loop fails the second. Both restored, suite green.
4. `knowledge_lint._strip_fences is knowledge_spans.unfenced`, and `work_status._nonfenced`
   returns the same result as `unfenced_lines` on the same input.
