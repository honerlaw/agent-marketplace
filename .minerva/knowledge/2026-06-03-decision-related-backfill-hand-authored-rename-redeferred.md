# The initial `## Related` backfill was hand-authored as a one-time unit (the spike for any future skill); rename-APPLY stays deferred at zero live instances

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/2026-06-03-related-backfill (see git history if the worktree has been cleaned up)

## Context

Unit 026's migration check inventoried two deferred APPLY items for the wiki: authoring
the initial `## Related` cross-refs for the 9 early entries that predate the convention,
and automating renames of non-conforming files. This unit discharged the first and
re-deferred the second.

## Decision

**The backfill was done by hand as a one-time work unit — no new skill or script.** The
reusable substrate already existed (`knowledge_edits.add_related_link`,
`knowledge_fix.py`'s reciprocal pass, the detector, `migration_status`); the only new
work was judgment. Doing that judgment by hand once **is the spike** that would inform a
future reusable backfill skill — building the skill first would have been speculative
generality. The methodology, reusable for any future backfill:

- a **per-edge disposition table** recorded *before any write* (entry → target → label →
  one-line justification grounded in **both** entries' bodies, or "legitimately
  standalone" + reason), kept as the completion-verification artifact;
- labels **fenced to `see also` / `builds on`** — a retroactive `supersedes` /
  `contradicts` writes banners / strong claims onto old entries and needs unambiguous
  grounding;
- **forward edges only, written via `knowledge_edits.add_related_link`** (never freehand
  Edit — [[2026-06-02-constraint-promote-narrowed-never-overwrite]]-safety is a property of the
  editor), with `body_complement` asserted on every write;
- **one `knowledge_fix.py` pass owns all reciprocals** (it creates the `## Related` block
  on receive-only entries), and forwards + reciprocals land in a **single atomic commit**
  — a hard CI requirement, since the live-corpus lint test errors on missing reciprocals;
- an **honest residual**: an entry with no genuine neighbor stays standalone (006,
  review-lens ownership, was the only one) — `entries_without_related` going non-zero
  after a backfill is a pass, not a miss.

The strongest edges promoted **latent verbatim prose references** into structured edges
(021's body already said "complements [[007]]"; 003's body already cited 002) — a good
test for whether a proposed edge is real.

**rename-APPLY is re-deferred, not dropped:** the live corpus has **zero** non-conforming
files, so the tooling would have no fixture and no observable behavior to assert (YAGNI).
Revisit when a real pre-conventions corpus provides one.

## Implications

- A future **reusable backfill skill** is a recorded candidate follow-up; its shape should
  follow the methodology above (disposition table → editor-routed forwards → fixer
  reciprocals → atomic commit → honest residual).
- A backfill reshapes `## Related` blocks **in place** — the synthesis watermark
  (new-scope-only floor) cannot see it, so a backfill unit must end with a
  `minerva:synthesize` refresh invoked with that drift rationale explicitly (the bare
  un-synthesized count would wrongly self-skip).
- After this unit, every knowledge entry except 006 carries cross-ref edges; the
  `entries_without_related` signal now inventories genuine standalones, not backlog.

## Related
- [[2026-06-03-decision-migration-check-read-only-entry-re-blindspot]] — builds on
- [[2026-06-02-constraint-knowledge-cross-reference-convention]] — see also
- [[2026-06-02-constraint-promote-narrowed-never-overwrite]] — see also
