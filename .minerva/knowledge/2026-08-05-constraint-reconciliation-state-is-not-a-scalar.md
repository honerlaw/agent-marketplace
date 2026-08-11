# Reconciliation state cannot be a scalar watermark — records merge out of order

**Date**: 2026-08-05
**Type**: constraint
**Summary**: a threshold assumes NNN-ordered merges; use a per-record marker, not a scalar floor
**Context**: .minerva/work/2026-08-05-add-only-knowledge-writes (see git history if the worktree has been cleaned up)

## Context
When `minerva:promote` became add-only ([[2026-08-05-decision-promote-add-only-reconcile-on-default]]),
something had to distinguish "this entry is not catalogued **yet**" from "this entry is
genuinely drifted." The first design made `index-watermark` a **lagging floor**: entries
with `NNN > watermark` were pending warnings, entries at or below it were hard errors.
The shape was borrowed deliberately from `synthesis_status`, whose watermark docstring
says the lag "is the signal."

That design was implemented, reviewed, passed 413 green tests, and took a **3/3
completion-verification panel accept** before an independent fresh-context review
reproduced it broken.

## Finding
**A scalar threshold cannot express which records have been reconciled, because records
do not arrive in id order.** Concurrent work units merge whenever their PRs land, and
enabling that concurrency was the entire point of the change.

The reproduction:

> Unit A allocates 050; unit B allocates 051 (correctly — the cross-branch allocator
> sees A's branch). **B merges first**, and reconciliation advances the watermark to 051.
> A then merges. Entry 050 now sits *below* the floor, so the floor calls it drift.

Two failures, the second worse:

1. Branch A's CI drift gate goes red through no fault of its own — defeating the exact
   guarantee the floor existed to provide.
2. No `pending reconciliation` warning is emitted. That warning is the signal
   `minerva:cleanup` gates reconciliation on, so cleanup reports "nothing pending" and
   **050 is never catalogued at all.** Silent and permanent.

The fix is to stop deriving state from a threshold and read it per-record: an entry is
pending iff it has no catalog line, full stop. That is sound because promote no longer
writes catalog lines at all, so no promote-driven path produces genuine drift, and
reconciliation repairs whatever it finds regardless of arrival order.

A compounding instance of the same error sat in the fixer: it set the watermark to the
corpus max even for entries it had *refused* to catalogue, pushing a pending entry below
the floor into the same silent-permanent state. The watermark now records only
`max(actually catalogued)`.

## Implications
- Prefer a per-record marker (a catalog line, a wikilink, a row) over a high-water mark
  whenever the records can arrive concurrently. A watermark is only safe when the
  producer is strictly ordered — which a set of independent branches is not.
- **What this trade costs, stated plainly:** a hand-edit or bad merge that drops an
  *already-reconciled* catalog line is no longer reported loudly; it is silently
  self-healed by the next reconciliation. That is deliberate — `index.md` is
  machine-generated content now, and the failure traded away is rarer and
  self-correcting, while the floor's failure was frequent, silent and permanent.
  `test_corruption_below_the_watermark_is_self_healed_not_errored` pins it so it is not
  "restored" without understanding the cost.
- **Neither a green suite nor a consensus panel covers this class of defect.** The tests
  passed because they encoded the same wrong assumption the design did, and the panel
  accepted because it was checking whether the criteria were met, not whether the model
  was right. When a design depends on ordering, concurrency, or arrival sequence, probe
  that assumption explicitly and adversarially — it will not fail on its own.
- `scripts/synthesis_status.py` still carries this exact shape. It is left in place
  deliberately (recorded in the unit's `followups.md`): `minerva:synthesize` rebuilds the
  overview from the whole corpus, so its watermark gates only *whether* to run, never
  what to include — a skipped entry is swept in on the next run. Same shape, materially
  smaller blast radius. Close it anyway when convenient.

## Related
- [[2026-08-05-decision-promote-add-only-reconcile-on-default]] — see also
- [[2026-06-03-decision-synthesis-layer-separate-file-advisory]] — see also
- [[2026-08-10-decision-date-ids-make-identity-the-path]] — see also
