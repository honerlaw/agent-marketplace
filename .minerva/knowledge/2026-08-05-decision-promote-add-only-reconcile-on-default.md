# `minerva:promote` is add-only; every aggregate is reconciled on the default branch

**Date**: 2026-08-05
**Type**: decision
**Summary**: promote writes only new entry files; index, watermark, reciprocals and overview reconcile on the default branch
**Context**: .minerva/work/2026-08-05-add-only-knowledge-writes (see git history if the worktree has been cleaned up)

## Context
`minerva:promote` used to write a new knowledge entry **and** edit shared aggregates on
the same work-unit branch: the `index.md` catalog line, the `index-watermark` on line 2,
reciprocal `## Related` links in neighbour entries, and supersession banners.

Every one of those is a surface two concurrent work units touch. In a heavy consumer
repo `index.md` appeared in **78% of recent commits**, and its conflicts were guaranteed
rather than probable — the watermark is a same-line edit, so any two promotes collide
there even when their catalog lines land in different Type sections. `overview.md` added
another 33% as a wholesale rewrite, which nothing can merge. Measured cost was roughly
20 minutes per surfaced conflict, so three PRs in flight burned an hour on friction that
produced nothing.

## Finding
**A work-unit branch's `.minerva/` footprint must consist entirely of newly-added
files.** New files merge cleanly no matter how many PRs are open, so the conflicts stop
by construction rather than by careful sequencing.

Promote therefore writes new `.minerva/knowledge/NNN-*.md` entries and nothing else — no
catalog line, no watermark bump, no neighbour edit, no banner. Neighbour discovery still
runs (it is genuine judgment), but emits **forward** `## Related` links only, into the
new entry.

Everything it stopped doing happens in `minerva:cleanup`'s reconciliation on the default
branch, where there is exactly one writer at a time: catalog lines generated from each
entry's `**Summary**` field, the watermark, every reverse link and banner derived by
`knowledge_fix.plan_reciprocals`, and `overview.md`. Reconciliation opens a single
auto-merging PR; work-unit PRs and reconciliation PRs never touch the same files, so the
two classes cannot conflict with each other either.

This is deliberately *not* a CI workflow or a git merge driver. The pain is felt in
consumer repos, so the fix had to be portable skill behaviour with zero per-repo setup —
minerva cannot install a workflow in every repo, and custom merge drivers are per-clone
local config that CI checkouts silently lack.

## Implications
- Never "just add the index line while you're here" during a promote. That single line
  is the file that was in 78% of commits.
- The entry template's `**Summary**` field is load-bearing, not decorative: it is what
  lets reconciliation catalogue an entry mechanically instead of needing an LLM to
  re-condense the Finding. An entry without one is refused, not fabricated.
- A legacy corpus needs no migration. `plan_index` preserves existing catalog lines
  verbatim and only needs a `**Summary**` for entries that have *no* line, so old
  entries keep their hand-written lines forever while new ones generate theirs. The
  mixed state is stable, not transitional (`test_mixed_corpus_needs_no_backfill`).
- Uncatalogued entries and un-reciprocated forward links are **warnings**, so a branch's
  CI drift gate stays green until reconciliation runs. See
  [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]] for why that is not gated on
  the watermark.
- Removing the conflicts removed the only thing incidentally catching duplicate entry
  numbers — which is why [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]]
  had to ship in the same unit, not after it.

## Related
- [[2026-06-02-constraint-promote-narrowed-never-overwrite]] — builds on
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — builds on
- [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]] — see also
- [[2026-08-05-constraint-nnn-keyed-lookups-hide-duplicates]] — see also
- [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]] — see also
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — see also
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — the one gap in this design, and how it was closed
- [[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]] — see also
