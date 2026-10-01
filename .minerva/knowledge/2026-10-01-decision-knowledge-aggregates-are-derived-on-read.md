# Knowledge aggregates are derived on read, so nothing is reconciled after merge

**Date**: 2026-10-01
**Type**: decision
**Theme**: knowledge-wiki
**Summary**: catalog, backlinks and supersession derive from entries' Theme/Summary lines; no post-merge reconciliation
**Context**: .minerva/work/2026-10-01-derive-knowledge-aggregates

## Context
The wiki stored four aggregates beside its entries: the `index.md` catalog and its
watermark, the reverse direction of every `## Related` link plus supersession banners,
and a hand-written `overview.md`. Each was a surface concurrent PRs fought over, so
promote was made add-only and every aggregate moved to a post-merge, single-writer pass
in `minerva:cleanup`. That pass then grew its own failure classes: entries stranded
uncatalogued when a reconcile PR was already open, an unserialised second writer when a
consumer reconciled in CI, stale `minerva/reconcile` branches, and a `chore: reconcile
knowledge index` PR after every feature merge.

`overview.md` had also quietly rotted: an LLM rewrite had pasted a paragraph of its
"Silent success" theme into the intro, mid-sentence, leaving nine entries linked from no
theme section. Nothing noticed, because nothing can check a wholesale prose rewrite.

## Finding
**Store only entries; derive every aggregate when it is read.** Each aggregate was a
cache of data the entries already held:

- a catalog line is `[[stem]] — **Summary**`, and the type section is the stem's type;
- the watermark only tracked reconciliation;
- a back-link is a forward link reversed, and supersession is a `supersedes` edge reversed;
- the overview's load-bearing content was the grouping of entries into themes, which now
  lives on each entry as a single-valued `**Theme**` line.

`knowledge_catalog.py` computes all of it (grouped by theme, `--by-type`, `--themes`,
`--links-to`), and the Routing section carries a portable `awk` one-liner that prints the
same `theme | entry | summary` lines with no plugin path. Entries are write-once, a PR's
knowledge footprint is purely new files, and the knowledge update ships complete in the
unit's own PR. Cleanup only removes worktrees.

The overview's narrative prose is dropped deliberately. `.minerva/` content exists to help
an LLM do work, the recurring cross-cutting lessons are already `pattern` entries, and a
new cross-cutting insight is promoted as a new entry rather than written into a shared
narrative. The catalog costs ~6k tokens on 119 entries against ~17k for the overview.

## Implications
- Never reintroduce a stored aggregate "for convenience" — an index, a generated
  overview, a back-link written into a neighbour. Each one recreates both the conflict
  surface and the post-merge pass that has to maintain it.
- `**Theme**` and `**Summary**` are load-bearing. `knowledge_lint` errors on a missing one
  for any entry dated on/after 2026-10-01, keyed on the entry's own id rather than on
  whether a legacy `index.md` exists, so a 2.x tool recreating that file cannot relax it.
- Theme drift — two units coining near-duplicate themes — is the one remaining
  concurrency cost. It is semantic, not textual: lint warns on a theme only one entry uses,
  and promote lists existing themes first.
- Supersession is the union of `supersedes` edges, legacy `superseded by` edges and legacy
  banners. Old corpora keep their stored back-links and banners; they are still read, never
  rewritten.
- 3.0 is a breaking release: `minerva:synthesize` and `minerva:lint-fix` are gone,
  `knowledge_fix.py` is a tombstone that exits non-zero (a CI reconciler fails loudly, not
  silently), and a consumer migrates with `minerva:migrate-fix` (`knowledge_backfill.py`)
  then a `minerva:init` routing refresh.

## Related
- [[2026-08-05-decision-promote-add-only-reconcile-on-default]] — supersedes: promote stays add-only, but nothing is reconciled on the default branch any more
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — supersedes: the navigable wiki is kept; its maintained index.md is replaced by a derived catalog
- [[2026-06-03-decision-synthesis-layer-separate-file-advisory]] — supersedes: the overview is replaced by Theme-grouped derivation
- [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]] — supersedes: there is no reconciliation state left to represent
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — see also: the stranded-entry failure this removes at the source
- [[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]] — see also: the CI second-writer race this removes at the source
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — see also
