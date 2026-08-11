# minerva:migrate is the read-only migration-shape check; its reason to exist is the ENTRY_RE false-clean blind spot every other wiki tool shares

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/2026-06-03-migrate-check (see git history if the worktree has been cleaned up)

## Context

Adopting minerva on a corpus that predates the wiki conventions (entries without the
`NNN-type-slug` filename, without `## Related` blocks, without an index/overview) needs a
"migration check" — assess the corpus against the current wiki structure and report what
to fix. This entry records the design.

## Decision

**The load-bearing insight is a shared blind spot:** the detector
(`scripts/knowledge_lint.py`), the fixer (`scripts/knowledge_fix.py`), and
`scripts/synthesis_status.py` **all enumerate the corpus via the `ENTRY_RE` glob only**
(`^\d{3}-[a-z]+-.+\.md$`). A file that doesn't match — a legacy entry named before the
convention — is **invisible** to every one of them, so a pre-conventions corpus reads as a
**false clean** across the whole toolchain. The migration check's reason to exist is to be
the **one surface that globs the *complement* of `ENTRY_RE`** and inventories those
invisible files. `scripts/migration_status.py` returns plain-primitive signals:
`non_conforming_files` (the migration-unique signal), `index_present` / `overview_present`,
`entries_without_related` (conforming entries with no cross-ref edges, via the frozen
`parse_entry`), and `conforming_entry_count`.

**`minerva:migrate` ships read-only**, following the same seam as
[[2026-06-03-decision-minerva-lint-read-only]]: it reports a migration checklist and **names**
the existing skill that closes each gap (`minerva:init` backfills the index,
`minerva:synthesize` creates the overview, `minerva:lint`/`minerva:lint-fix` handle
mechanical drift) — it does **not** invoke them or mutate anything. `allowed-tools` omits
`Write`/`Edit`; it carries a literal `read-only` anchor.

**It is a SHAPE check, not a HEALTH check.** A clean migration inventory (all files
conforming, index + overview present) can still coexist with `minerva:lint` index-drift
errors, so a passing migration check still requires a green `minerva:lint` +
`minerva:synthesize` pass. The skill states this in-body so its own "clean" can never
become a new false-clean.

## Implications

- The two mutating remediations a legacy corpus needs — **renaming** non-conforming files
  to `NNN-type-slug.md` (link-breaking; must update every `[[…]]` + the catalog) and
  **authoring** the initial `## Related` cross-ref edge graph (O(entries²) LLM-judged
  neighbor discovery) — are **deferred to follow-up migration-APPLY units**. The check
  reports the counts and tells the user this work is manual / not yet automated.
- `migration_status.py` reuses the frozen detector's `ENTRY_RE` / `parse_entry` per
  [[2026-06-02-constraint-knowledge-span-model-single-sourced]] /
  [[2026-06-03-constraint-wiki-edge-derivation-fence-aware]] and returns only plain primitives
  (no lint `Finding` namedtuples) so it is not coupled to the detector's internal schema —
  the same discipline `synthesis_status` follows.
- Reserved non-entry files are exempted via a **named, extensible**
  `RESERVED_NONENTRY = {"index.md", "overview.md"}` set, so a future Phase-C `log.md` is
  added there rather than wrongly flagged.
- The whole toolchain (including this check) globs `*.md` **non-recursively** — entries in
  subdirectories are invisible to all of it.

## Related
- [[2026-06-03-decision-minerva-lint-read-only]] — builds on
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — see also
- [[2026-06-03-decision-related-backfill-hand-authored-rename-redeferred]] — see also
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — see also
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
