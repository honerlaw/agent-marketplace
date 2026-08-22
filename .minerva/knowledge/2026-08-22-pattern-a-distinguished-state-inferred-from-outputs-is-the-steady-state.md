# A distinguished state inferred from a coincidence of outputs is usually the steady state

**Date**: 2026-08-22
**Type**: pattern
**Summary**: gating on "outputs look like X" instead of an explicit flag catches the resting state, not the failure

**Context**: .minerva/work/2026-08-22-close-open-issue-backlog (see git history if the worktree has been cleaned up)

## Context

`knowledge_fix.plan()` called `plan_index` and `plan_reciprocals` independently, so an index
rewrite refused wholesale still returned entry edits and `apply()` wrote them — neighbour
entries gained reciprocal `## Related` links the catalog did not know about. Fixing it
requires telling a **wholesale** refusal from a **per-entry** one, because a per-entry
refusal is routine and must keep both halves.

`plan_index` distinguishes them only by control flow: two sites early-return
`old, old, refusals`; the per-entry path falls through to normal serialization. The obvious
gate reads that off the return values — index unchanged **and** refusals present.

## Finding

That signature is not the failure. It is the **steady state**.

Once a corpus is canonical the index rewrite is a no-op, and a benign per-entry refusal —
one entry of unrecognized type already sitting in a known section — recurs on every
subsequent run. Reproduced against the real module: `new == old` is `True` with a refusal
present and nothing wrong. A caller gating on that signature would have discarded legitimate
reciprocal edits on every run from then on: the same half-reconciled corpus the fix existed
to prevent, arrived at from the other direction.

The fix is an explicit `hard: bool` returned by `plan_index`, set only at the two sites that
genuinely early-return. `plan()` gates on the flag and never inspects text equality. Because
Python tuple-unpacking is arity-strict, the signature change makes every existing caller
fail loudly until updated — the flag cannot be silently ignored.

## Implications

Whenever a caller needs to know that a callee hit a distinguished case, have the callee
**say so**. Do not reconstruct it from the shape of the outputs: the reconstruction is
tested on a fresh fixture, where the distinguished case and the resting state still look
different, and it breaks once the system reaches equilibrium — which is when it is running
unattended and nobody is watching.

Two properties make this trap hard to see. The wrong gate passes every test written against
a newly-built fixture, because "canonical corpus, nothing to do, one standing complaint" is
a state only reached after the code has run successfully for a while. And it fails
**silently**: work is dropped, not errored.

## Related
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — builds on
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — see also
