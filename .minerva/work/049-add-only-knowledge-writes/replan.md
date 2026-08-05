# Replan: 049-add-only-knowledge-writes

## 2026-08-05 — the scalar reconciliation floor is unsound; replaced

### Original plan

`## Approach` §3 made `index-watermark` a **lagging floor**: `watermark ≤ max NNN`,
with entries *above* the watermark reported as `pending reconciliation` warnings and
entries at or below it still hard errors. The shape was borrowed deliberately from
`synthesis_status`'s watermark, whose docstring says the lag "is the signal."

That discriminator is what let promote go add-only without reddening CI: a work-unit
branch's new entry sits above the floor, so its missing catalog line and its
un-reciprocated forward links are pending, not drift.

The floor was implemented (`0aeb4af`), reviewed, and carried a **3/3 completion-
verification panel accept** before anything questioned it.

### What changed

A fresh-context code review of the finished changeset found the floor broken in
exactly the scenario this unit exists to serve. Reproduced before acting:

> Unit A allocates 050; unit B allocates 051 (correctly — the new allocator sees A's
> branch). **B merges first** and reconciliation advances the watermark to 051. A then
> merges. Entry 050 is now *below* the floor, so the floor calls it drift.

Two consequences, the second worse than the first:

1. Branch A's CI drift gate goes red through no fault of its own — defeating the
   guarantee the floor was introduced to provide.
2. No `pending reconciliation` warning is emitted. That warning is precisely the
   signal `minerva:cleanup` gates reconciliation on, so cleanup reports "nothing
   pending" and **entry 050 is never catalogued at all**. The failure is silent and
   permanent.

The root error is the assumption that entries reconcile in NNN order. They do not —
units merge whenever their PRs land, and enabling exactly that concurrency is the
point of the unit. A scalar threshold cannot express "this set has been reconciled,
that set has not."

A second, compounding defect surfaced with it: `plan_index` set the watermark to the
corpus max even for entries it had *refused* to catalogue, pushing a pending entry
below the floor and converting it into the same silent-permanent-error state.

### New plan

**Delete the floor.** An uncatalogued entry — and an un-reciprocated forward link — is
**always** a `pending reconciliation` warning, with no watermark comparison anywhere.
This is sound because promote no longer writes catalog lines at all, so no
promote-driven path can produce genuine drift; and reconciliation repairs whatever it
finds regardless of ordering.

The watermark survives, with a narrowed job: it records how far the catalog has
actually been brought (`max(actually catalogued)`, never the corpus max), and the only
check remaining on it is that it never *exceeds* max NNN — an index claiming entries
that do not exist is real drift. It also remains the promote-time freshness pre-filter
in `wiki-maintenance.md`, which is a live consumer of an honest value.

**What this costs, stated plainly.** A hand-edit or bad merge that drops an
*already-reconciled* catalog line was a loud error under the floor; it is now a warning
that the next reconciliation silently repairs. That is a deliberate trade, not an
oversight: `index.md` is machine-generated content now, and the failure being traded
away is rarer and self-correcting, while the floor's failure was frequent, silent, and
permanent. `test_corruption_below_the_watermark_is_self_healed_not_errored` pins it so
it is not "restored" without understanding what restoring it costs.

### Success criteria affected

Criterion 2's *intent* is unchanged and better served — a work-unit branch with pending
entries stays green. Its wording ("entries above the watermark") no longer describes
the mechanism; `minerva:promote` rewrites it at promote time. Regression coverage:
`test_out_of_order_merge_stays_green`.
