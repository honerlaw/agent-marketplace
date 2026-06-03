# minerva knowledge is a navigable, self-maintaining wiki: an `index.md` catalog with recall-complete corpus-scan discovery (X′ over X)

**Date**: 2026-06-02
**Type**: decision
**Context**: .minerva/work/020-knowledge-wiki-navigability (see git history if the worktree has been cleaned up)

## Context
`.minerva/knowledge/` was an accumulate-only pile of atomic entries with no catalog and no maintained cross-references — the opposite of the "compounding artifact" in Karpathy's LLM-wiki pattern. Work unit 020 (Phase 1 of a planned 3) added the navigability + neighbor-maintenance layer. This entry records the design decisions; the author-facing rules live in [[015-constraint-knowledge-cross-reference-convention]] and the promote-edit invariant in [[016-constraint-promote-narrowed-never-overwrite]].

## Finding
**`.minerva/knowledge/index.md` is a maintained catalog.** It is grouped by Type (`## Decisions` / `## Bugs` / `## Patterns` / `## Constraints`), one line per entry (`- [[NNN-type-slug]] — <≤15-word summary>`), and carries an `<!-- index-watermark: NNN -->` comment recording the highest entry it reflects. The watermark is a **content** freshness signal, chosen over file mtime because mtime is unreliable across git checkouts and worktrees.

**Discovery uses a recall-complete corpus scan (approach X′), not the index (approach X).** When promote ingests a new entry, it scans the corpus directly (titles + Findings of all entries) to find neighbors; the index is consulted only as an *optional pre-filter when its watermark ≥ the max NNN on disk*, and never gates discovery. X′ was chosen over the originally-proposed index-mediated discovery (X) because: (a) the index did not exist before this unit, so an index-gated approach had **zero recall** on first run; and (b) X would couple discovery *correctness* to index *freshness*. With X′ the index is a convenience/accelerator and the browse-time catalog, never a correctness dependency.

**`minerva:init` scaffolds the wiki.** init now creates `index.md` (canonical skeleton, watermark `000`) and the `.minerva/reference/` tier (with `.gitkeep`), mentions both in the Routing template (detection window widened 4→6 lines), and offers — in idempotent mode — to backfill `index.md` from existing entries. This **discharges the two open followups recorded in [[011-decision-minerva-reference-tier]]** ("init does not yet scaffold .minerva/reference/" and "using-minerva needs the reference tier documented").

**`init` and `promote` both create `index.md`** (init scaffolds; promote creates-if-absent) and therefore both emit one **byte-identical canonical skeleton** (differing only in the watermark value) so the two creators cannot diverge.

## Implications
- Treat `.minerva/knowledge/index.md` as the entry point for "what do we know"; it is maintained, not hand-authored — `minerva:promote` updates it (and the watermark) when it ingests.
- Don't make the index a correctness dependency of any future tooling: discovery/lint must tolerate a missing or stale index by recomputing from the corpus. The watermark tells you whether the index can be trusted as a pre-filter.
- If you change the canonical index skeleton, change it in **both** `minerva:init` and `minerva:promote` in the same edit.
- Phases B (`minerva:lint` health-check) and C (synthesis/concept pages + `log.md`) build on this layer and are deliberately deferred — see this unit's `followups.md`.

## Related
- [[015-constraint-knowledge-cross-reference-convention]] — see also
- [[016-constraint-promote-narrowed-never-overwrite]] — see also
- [[011-decision-minerva-reference-tier]] — builds on
