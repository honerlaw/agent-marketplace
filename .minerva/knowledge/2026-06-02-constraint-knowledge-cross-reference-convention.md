# Knowledge entries cross-reference each other via a `## Related` block of `[[NNN-type-slug]]` links with a closed relationship vocabulary

**Date**: 2026-06-02
**Type**: constraint
**Context**: .minerva/work/2026-06-02-knowledge-wiki-navigability (see git history if the worktree has been cleaned up)

## Context
Before work unit 020, `.minerva/knowledge/` entries were isolated atoms. A few entries used inline `[[NNN-type-slug]]` mentions in prose (009/010/012/013), but there was no convention for how entries reference each other, so the cross-references Karpathy's LLM-wiki pattern relies on ("the cross-references are already there") were absent. 020 introduced a navigable-wiki layer (see [[2026-06-02-decision-knowledge-wiki-navigability-layer]]); this entry records the cross-reference convention an author/agent must follow.

## Finding
A knowledge entry MAY carry a trailing, delimited `## Related` block — the canonical, machine-managed relation surface — with one line per relationship:

```
## Related
- [[NNN-type-slug]] — <relationship>
```

Rules:
- **Links reuse the existing `[[NNN-type-slug]]` wiki-link form**, keyed on the **stable NNN**. The slug is cosmetic; the NNN is the durable handle (a slug rename does not change the key).
- **Closed relationship vocabulary**: `builds on` / `supersedes` / `superseded by` / `contradicts` / `see also`. No other terms.
- **Bidirectional**: if A links B, B carries the reciprocal line. `supersedes` ↔ `superseded by` is the directional pair; `contradicts` and `see also` are symmetric.
- **`builds on` has no inverse term in the closed vocabulary.** The reciprocal of a `builds on` edge is therefore rendered as `see also` (this is the shipped behavior — e.g. in the dogfooded 004↔010↔012 cluster, where 010/012 `builds on` 004 and 004 reciprocates with `see also`).
- **Supersession preserves history**: a superseded entry gets a banner between its metadata block and the first `## ` header, `<!-- superseded-by: NNN -->` + a `> **Superseded by [[NNN-type-slug]]** (date)` line, plus the reciprocal `## Related` line. The body is never deleted.
- **Inline `[[…]]` prose mentions coexist and are NOT migrated.** The `## Related` block is the structured, promote-maintained surface; inline mentions in entry prose remain valid free-form references.

`minerva:promote` maintains these links (including the reciprocal on neighbor entries) under [[2026-06-02-constraint-promote-narrowed-never-overwrite]].

## Implications
- When authoring or relating a knowledge entry, use `[[NNN-type-slug]]` keyed on NNN and only the five vocabulary terms; render a `builds on` reciprocal as `see also`.
- A future phase may add a richer inverse term for `builds on` — until then the `see also` reciprocal is the convention, not a bug.
- The `## Related` block must remain the **last** section of an entry (the cross-ref span runs to EOF); the supersession banner is the only content allowed above the first `## ` header. These span boundaries are what make promote's edits safe — see [[2026-06-02-constraint-promote-narrowed-never-overwrite]].

## Related
- [[2026-06-02-constraint-promote-narrowed-never-overwrite]] — see also
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — builds on
- [[2026-06-03-constraint-wiki-edge-derivation-fence-aware]] — see also
- [[2026-06-03-decision-related-backfill-hand-authored-rename-redeferred]] — see also
