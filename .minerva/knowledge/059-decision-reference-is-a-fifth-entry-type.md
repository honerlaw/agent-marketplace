---
name: reference-is-a-fifth-entry-type
description: Use when a corpus repeatedly contains a value the tooling's closed vocabulary does not admit, or when adding a section to the knowledge index skeleton. `reference` is now a fifth entry type with its own `## References` section — four independent authorings were evidence of a gap, not four mistakes. Carries the append-never-interleave rule for the canonical skeleton, and the line between a `reference` ENTRY and a `.minerva/reference/` DOC.
metadata:
  type: decision
---

# `reference` is a fifth entry type, with its own index section

**Date**: 2026-08-09
**Type**: decision
**Context**: .minerva/work/052-reference-is-a-fifth-entry-type
**Summary**: The entry-type vocabulary was four values — `decision` / `bug` / `pattern` / `constraint` — hardcoded in `SECTION_TO_TYPE`, `SECTION_ORDER` and four skill docs. Authors wrote `reference` entries anyway (four of them in one corpus), and the tooling had nowhere to put them: `plan_index` cannot place a line whose declared type has no section, so they were refused indefinitely. Adding `## References` as a fifth section ratifies what authors already do. Two rules fall out: **append a new section, never interleave it** (appending is the only position that leaves every existing index's line order byte-identical), and an empty section renders as its header alone, so the change is inert for every corpus that does not use it.

## Why not the other reading

`.minerva/reference/` is minerva's documented home for present-tense operational docs, so "those four entries are misfiled" was a real alternative, and the reason this was escalated rather than decided. It was rejected on what the entries actually are: how the blue-green search-index migration is *run*, what the repo-local eslint plugin is and why it has no build step, a curated followups backlog, a known-noise triage map. Each is atomic, numbered, cross-linked and catalogued — an entry's shape, not a maintained page's.

The line that survives: a **`reference` entry** is a standing fact about the system, in the same register as the other four but describing what *is* rather than what was *learned*. A **`.minerva/reference/` doc** is an operational page you maintain. Register, not subject matter, is what separates them.

## Four authorings are a signal, not four mistakes

The general form: when a corpus keeps producing a value a closed vocabulary refuses, count the instances before defending the vocabulary. One is a typo. Four, by different authors, across months, is the vocabulary being wrong — the same shape as the relation-label vocabulary that assumed five terms while every corpus wrote prose. Both were "the convention as designed" losing to "the convention as practiced", and in both cases the tooling had been quietly refusing real content the whole time.

## The mechanics that make it safe

- **Append to `SECTION_ORDER`.** `plan_index` reserializes the whole index from that list, so inserting a section in the middle would renumber every consumer's line order in one diff. Appended, existing lines are untouched.
- **An empty section is just its header** (the canonical-skeleton rule that already existed). A corpus with no `reference` entries gains one inert `## References` line at its next reconciliation and nothing else — pinned by a test, because "inert for everyone who does not use it" is the property that made this safe to ship to every consumer at once.
- **Update every enumeration in the same change.** The vocabulary was written down in six places outside the two scripts (promote's two, debug's two, migrate's, and the init skeleton). A type the tooling accepts but the docs do not name is a worse state than either.

## Related

- [[058-pattern-read-authored-metadata-from-where-it-is]] — the sibling: there the parser could not read a type the entry did state, here the vocabulary had no slot for one four entries did state. Both are the tooling's model of the corpus lagging the corpus
- [[017-decision-knowledge-wiki-navigability-layer]] — the index this adds a section to, and the navigability argument that makes an uncatalogued entry a real loss
