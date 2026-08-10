# Proposal: knowledge-wiki-navigability-layer

**Date**: 2026-06-02
**Status**: Shipped (2026-06-02)

> **Phase 1 of 3.** Phase B (`minerva:lint` health-check) and Phase C (synthesis /
> concept pages + `log.md`) are deliberately out of scope — see **Out of scope**.

## Goal

Turn `.minerva/knowledge/` from a flat pile of append-only atomic entries into a
navigable, self-maintaining wiki layer — aligning minerva with the "compounding
artifact" model from Karpathy's LLM-wiki pattern — via four coupled pieces around
a maintained index:

1. A maintained `.minerva/knowledge/index.md` catalog.
2. A bidirectional, relationship-labeled cross-reference convention between
   knowledge entries (reusing the existing `[[NNN-type-slug]]` wiki-link form),
   with supersession banners that preserve history.
3. `minerva:promote` maintaining the index and cross-references — including
   updating neighbor entries — gated through its existing confirmation gate(s),
   when it ingests new knowledge.
4. `minerva:init` scaffolding the index and the `.minerva/reference/` directory,
   and offering to backfill the index for projects that already have knowledge
   entries.

**Provenance note.** The `.minerva/reference/` scaffolding in piece 4 is *not*
native to the navigability concern. It discharges a long-pending followup recorded
in knowledge entry [[2026-05-22-decision-minerva-reference-tier]] (unit 014:
"minerva:init does not yet scaffold .minerva/reference/" and "using-minerva …
need[s] updating to include the reference tier") and was absorbed into this unit
by explicit user decision after abandoned unit 015's collision. It rides along
because this unit already rewrites init's scaffold step and the using-minerva
hierarchy. The heavy 015 content-generation skills (`init-ref` / `init-knowledge`)
were deliberately deferred and remain recoverable via tag
`archive/015-init-content-backfill`.

## Why

minerva already implements the spine of an LLM wiki: immutable raw sources (the
codebase + git history + work proposals), an LLM-owned knowledge layer
(`.minerva/knowledge/` + `.minerva/reference/`), and a schema (the `## minerva`
Routing block in the agent file). What it lacks is the *maintenance* behavior that
makes a wiki **compound** rather than merely **accumulate**:

- **No catalog.** Knowledge is `NNN-type-slug.md` files discovered by `ls`/grep;
  there is no index with one-line summaries.
- **No structured cross-references.** A handful of entries use inline `[[NNN]]`
  mentions, but there's no convention and no maintained relation surface — so
  Karpathy's "the cross-references are already there" payoff is absent.
- **Accumulate-only promote.** `minerva:promote` only appends new atoms; it never
  updates related / superseding neighbors ("update relevant pages across the
  wiki").

Phase 1 closes the navigability + neighbor-maintenance gaps. It is the cheapest,
least-speculative layer and a prerequisite for Phase B lint (which validates the
cross-reference graph) and Phase C synthesis.

## Approach

### The canonical `index.md` skeleton (single definition)

Both `minerva:init` (scaffold) and `minerva:promote` (create-if-absent) emit this
exact skeleton, so the two creators cannot diverge:

```markdown
# Knowledge index
<!-- index-watermark: NNN -->

## Decisions

## Bugs

## Patterns

## Constraints
```

- `NNN` in the watermark comment is the highest entry number the index reflects
  (`000` for an empty scaffold). The watermark is a **content** freshness signal,
  used in preference to file mtime (mtime is unreliable across git checkouts and
  worktrees — and this repo uses worktrees).
- Catalog lines are appended under the matching Type section, one per entry:
  `- [[NNN-type-slug]] — <≤15-word summary>` (title from the entry H1, summary
  condensed from its Finding). Sections are plural buckets; links use the singular
  filename stem — consistent with the existing `NNN-decision-…` naming.

### 1. The `index.md` catalog

`.minerva/knowledge/index.md` is a *maintained* (not hand-authored) artifact in the
canonical skeleton above. It is documented as the "what do we know" entry point in
the `using-minerva` persistence hierarchy and the init Routing template.

### 2. Cross-reference convention

- Each knowledge entry MAY carry a trailing, delimited `## Related` block — the
  canonical, promote-maintained relation list.
- Links reuse the existing `[[NNN-type-slug]]` wiki-link convention (already live
  in entries 009/010/012/013), keyed on the **stable NNN** (the slug is cosmetic).
  Each line: `- [[NNN-type-slug]] — <relationship>`.
- Relationship vocabulary (fixed, closed): `builds on` / `supersedes` /
  `superseded by` / `contradicts` / `see also`.
- **Bidirectional:** if A relates to B, B carries the reciprocal line.
- **Supersession preserves history.** A superseded entry gets a banner placed
  between its H1/metadata and the first `## ` section header, carrying a fixed
  machine-delimitable marker:

  ```markdown
  <!-- superseded-by: NNN -->
  > **Superseded by [[NNN-type-slug]]** (YYYY-MM-DD)
  ```

  plus the reciprocal `## Related` line. The superseded entry's body is never
  deleted or rewritten.
- **Coexistence.** Inline `[[…]]` prose mentions in entry bodies remain valid and
  are NOT migrated. The `## Related` block is the structured surface; inline
  mentions are free prose. This coexistence is documented in `using-minerva`.

### 3. `minerva:promote` changes (gated neighbor + index maintenance)

Both **Mode A** (end-of-work full pass) and **Mode B** (single-item mid-work) gain
a neighbor/index maintenance step, folded into promote's **existing** confirmation
gates — no new gate is introduced. The two write paths are anchored by their
structural steps, not line numbers:

- **Mode A**: the new step nests under the existing **hard gate (Mode A step 6)**
  and **write (Mode A step 7)**.
- **Mode B**: the new step nests under the existing **approval gate (Mode B step
  4)** and **write (Mode B step 5)**.

For each promoted entry:

- **a. Neighbor discovery (recall-complete floor).** Scan the knowledge corpus
  directly (read titles + Findings of all entries) to find candidate related
  entries. `index.md` MAY be used as a pre-filter **only** when present AND fresh
  (its watermark ≥ the max NNN on disk); the index NEVER gates discovery. A stale
  or absent index means discovery recomputes from the corpus — it never blocks or
  refuses to run. Dedup candidate hits by target NNN (so an entry referenced both
  inline and in `## Related` collapses to one).
- **b. Propose edits.** For each confirmed relationship: a `## Related` line in the
  new entry; the reciprocal line in the neighbor; a supersession banner where the
  new entry overrides an old one. Reciprocal pairs are presented as a **single
  coupled approval unit** (so a user cannot approve one direction and silently drop
  the reciprocal).
- **c. Propose index line(s).** The new entry's catalog line, the watermark bump,
  and any index-line edits for superseded entries. If `index.md` is absent, promote
  creates it from the canonical skeleton with just the new entry, and points the
  user at `minerva:init`'s backfill for the rest.
- **d. Gate.** All of (b)+(c) surface in promote's existing confirmation gate,
  shown as **concrete diffs against each edited neighbor file and the index**.
  Neighbor files and the index are written **only on approval**.

**Mode B scope.** Mode B gets the *same* machinery as Mode A, scoped to the single
promoted entry: discovery for that entry, its bidirectional links + banner, and its
index line + watermark bump — routed through Mode B's own approval gate (step 4)
before its write (step 5). The cost is accepted; idempotency (below) means a later
Mode A full pass is a no-op over a Mode-B-touched entry.

**Idempotency.** The link writer is *insert-iff-absent*, keyed on the
`[[NNN-type-slug]]` target within the `## Related` block (set semantics). A
supersession banner is added only if no `<!-- superseded-by: NNN -->` marker for
that superseding NNN already exists. An index line is added only if no line for
that NNN exists; the watermark bumps **only** when an index line is actually
added or changed. Re-running promote (either mode) is a byte-level no-op on
already-present links / banners / index lines.

**Never-overwrite invariant, narrowed.** The entry **body** (the H1/metadata block
and the `## Context` / `## Finding` / `## Implications` sections) remains strictly
append-only and is never rewritten by these edits. The delimited `## Related` block
and the supersession-banner span are the *sole* machine-managed mutable surfaces.
promote's "Idempotency summary" prose (the current "knowledge files are never
overwritten" line) is updated to state this narrowed invariant.

### 4. `minerva:init` changes

- **Scaffold (Step 1):** additionally create `.minerva/knowledge/index.md` (the
  canonical skeleton, watermark `000`) and `.minerva/reference/` +
  `.minerva/reference/.gitkeep`. Idempotent — never overwrite existing files.
  Because a non-empty `index.md` makes `.minerva/knowledge/.gitkeep` redundant,
  init writes the knowledge-dir `.gitkeep` only when `index.md` is absent;
  idempotent re-runs neither re-add `.gitkeep` nor overwrite `index.md`.
- **Routing template (Step 3):** mention `.minerva/knowledge/index.md` (the catalog
  entry-point) and `.minerva/reference/` (the orientation tier). **Widen the
  existing-section detection window from 4 to 6 lines** so re-runs on the new,
  longer template are still detected. (The window only loosens detection and still
  requires both the `## minerva` heading and a `.minerva/knowledge/` signal, so
  [[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]] is preserved.)
- **Backfill offer (idempotent mode):** if `.minerva/knowledge/` has entries but
  `index.md` is missing or empty, **offer** to generate `index.md` from the
  existing entries and set the watermark to the max NNN. Cross-reference backfill
  across existing entries is offered as a **separate optional pass** (it is a
  judgment-heavy operation), not forced.
- **Status block (Step 5):** add `.minerva/knowledge/index.md` and
  `.minerva/reference/` lines.

### 5. Docs + contract sync

- **`using-minerva`:** the persistence hierarchy gains `index.md` (the catalog),
  the `## Related` cross-reference convention (incl. the inline-coexistence note),
  and the `.minerva/reference/` tier (the long-pending entry-011 followup).
- **Catalog surfaces ([[2026-05-21-constraint-minerva-skill-catalog-sync]]):** this unit
  MODIFIES init/promote and ADDS no skill, so no new catalog rows are required. If
  init's or promote's `description:` frontmatter changes to reflect the new
  behavior, sync the excerpted text in `plugins/minerva/README.md`'s Skills table
  (the only frontmatter-derived surface).
- **Contracts ([[2026-05-31-constraint-skill-structural-contracts]]):** add load-bearing
  body anchors to `evals/init/contract.json` (index + reference scaffold) and
  `evals/promote/contract.json` (neighbor/index maintenance, `## Related`),
  following the anchor grammar in `evals/README.md`. Anchor on **short stable
  tokens** (e.g. `index-watermark`, `## Related`, `[[`, `.minerva/reference/`), not
  prose sentences. `tests/test_skill_contracts.py` must stay green.
- **Invariant guard test:** because minerva skills are prose executed by an LLM
  (there is no callable `promote()` function to unit-test), this shipped as
  `tests/test_promote_invariant.py` — a **reference implementation** of the two
  allowed mutations (`add_related_link`, `add_supersede_banner`) plus a
  `body_complement` span-extractor, with property tests asserting byte-identity of
  the *complement* of the two machine-managed spans — the **banner span** (between
  the H1 and the first `## ` header, delimited by `<!-- superseded-by: NNN -->`)
  and the **`## Related` span** (`## Related` header → EOF) — across both
  mutations, plus idempotency and a "Mode A over an already-linked pair →
  zero-byte diff" case. `body_complement` asserts `## Related` is the terminal
  section so the guard can't go vacuous. The test is registered in the `evals.yml`
  CI gate. The `SKILL.md` prose is the runtime contract; this test is the
  executable spec-of-record for the span boundaries — making the narrowed
  never-overwrite invariant mechanically enforced, not merely documented.
- **Dogfood:** generate this repo's `.minerva/knowledge/index.md` from its 14
  existing entries (watermark `014`) and commit it, as the unit's own acceptance
  demonstration. Seed the already-inline-cross-referenced
  004 ↔ 010 ↔ 012 cluster with `## Related` blocks to demonstrate the convention
  (the broader cross-reference backfill of all 14 entries stays deferred — see
  Open Questions).

## Success criteria

- Running `minerva:init` on a fresh project scaffolds `.minerva/knowledge/index.md`
  (canonical skeleton, watermark `000`) and `.minerva/reference/` +
  `.minerva/reference/.gitkeep`, alongside `.minerva/work/` and
  `.minerva/knowledge/`.
- The Routing template emitted by init mentions both `.minerva/knowledge/index.md`
  and `.minerva/reference/`; the detection window is widened to 6 lines, and
  re-running init on the new template reports "already present" (no duplicate
  section).
- Running `minerva:init` in idempotent mode on a project with existing knowledge
  entries but no `index.md` offers index backfill and — on approval — writes
  `index.md` from the existing entries with the watermark set to the max NNN.
- The knowledge entry template in `minerva:promote` includes the delimited
  `## Related` block; promote Mode A and Mode B perform recall-complete
  corpus-scan neighbor discovery, propose `[[NNN]]`-keyed bidirectional cross-links
  (reciprocal pairs coupled), supersession banners, and index line(s) + watermark
  bump, show them as diffs in the existing confirmation gate, and write to
  neighbors/index only on approval.
- Re-running promote (either mode) produces a byte-level no-op on already-present
  `## Related` links, supersession banners, and index lines (idempotent, keyed by
  NNN).
- The narrowed never-overwrite invariant is documented in promote AND mechanically
  enforced by the invariant guard test: promote modifies no knowledge-file bytes
  outside the banner span and the `## Related` span, across both write paths.
- `evals/init/contract.json` and `evals/promote/contract.json` gain anchors for the
  new behavior (short stable tokens); `tests/test_skill_contracts.py` and the new
  guard test pass.
- The `using-minerva` persistence hierarchy documents `index.md`, the `## Related`
  cross-reference convention, and the `.minerva/reference/` tier.
- This repo's `.minerva/knowledge/index.md` is generated from the 14 existing
  entries (watermark `014`) and committed, with the 004 ↔ 010 ↔ 012 demo cluster
  cross-linked.

## Open Questions

- Should a later pass seed `## Related` links across **all** existing entries, or
  is the index + the 004 ↔ 010 ↔ 012 demo cluster enough for Phase 1, letting
  cross-refs accrue going forward via promote? **Leaning:** index + demo cluster
  now; full cross-reference backfill deferred (judgment-heavy).
- Should the supersession banner placement (between H1/metadata and the first
  `## ` header) be revisited if it reads awkwardly next to the metadata block?
  **Leaning:** the chosen placement keeps the H1 as the title and gives the guard
  test a clean span boundary; revisit only if real entries look wrong.

## Out of scope

- `minerva:lint` health-check skill (Phase B): contradiction / staleness / orphan /
  index-drift detection across the wiki.
- Synthesis / concept pages + `log.md` (Phase C).
- Cross-references within `.minerva/reference/`.
- The `init-ref` / `init-knowledge` content-backfill skills from abandoned unit 015
  (recoverable via tag `archive/015-init-content-backfill`); candidate future units.
- Automated / CI bidirectional catalog-drift checks.
- A `minerva:init --refresh` mode to rewrite Routing sections in existing projects
  when the template changes.
