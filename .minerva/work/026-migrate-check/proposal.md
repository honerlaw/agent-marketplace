# Proposal: migrate-check

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> A read-only **migration check** for the LLM-wiki structure: assess an existing
> `.minerva/knowledge/` corpus against the current wiki shape and report what needs
> migrating. The mutating remediation (file renames, cross-ref edge-graph backfill) is
> deferred to follow-up **APPLY** units.

## Goal

Add a read-only `minerva:migrate` skill + `scripts/migration_status.py` that **assess**
an existing `.minerva/knowledge/` corpus against the current LLM-wiki structure and emit a
**migration checklist** — so someone adopting minerva on a legacy / pre-conventions corpus
(or auditing structure) sees exactly what is non-conforming and which existing skill closes
each gap. Detect-and-report only; it mutates nothing.

## Why

Every existing wiki tool — the detector (`knowledge_lint`), the fixer (`knowledge_fix`),
and `synthesis_status` — enumerates the corpus via the `ENTRY_RE` glob **only**
(`^\d{3}-[a-z]+-.+\.md$`). So a legacy corpus of non-conforming files (entries that
predate the `NNN-type-slug` convention) reads as a **false clean** across all of them:
the files are simply invisible. No existing surface inventories what the wiki tooling
cannot see. `minerva:migrate` is the one surface that does — it turns a false-clean legacy
corpus into an actionable conformance checklist. Once files conform, the ongoing skills
(`minerva:lint` / `minerva:synthesize` / `minerva:init`) own the corpus.

## Approach

### `scripts/migration_status.py` — the deterministic shape signal

Importable `migration_status(knowledge_dir) -> dict` returning **plain-primitive**,
JSON-serializable signals only (the same style as `synthesis_status`; **never** lint's
`Finding` namedtuples — that would couple this tool to the frozen detector's internal
schema):

- `non_conforming_files`: sorted list of `*.md` filenames in the knowledge dir that do
  **not** match `ENTRY_RE`, minus a **named, extensible allowlist**
  `RESERVED_NONENTRY = {"index.md", "overview.md"}` (so a future reserved file such as the
  planned Phase-C `log.md` is added there, not flagged). **This is the migration-unique
  signal** — the one thing no other tool can produce, because producing it means globbing
  the *complement* of `ENTRY_RE`.
- `index_present`: bool — is `index.md` present?
- `overview_present`: bool — is `overview.md` (the synthesis layer) present?
- `entries_without_related`: sorted list of conforming entries (ENTRY_RE-matching) whose
  `## Related` block is **absent or empty**, derived via the frozen detector's
  `parse_entry` (`related_out == set()`), which is fence-aware via `_strip_fences`
  ([[023-constraint-wiki-edge-derivation-fence-aware]]). Empty-or-absent both count — the
  parser surfaces no distinction, and both mean "this entry contributes no cross-ref
  edges and needs authoring". This is the **count/inventory** only; authoring is deferred.
- `conforming_entry_count`: int.

Reuses `knowledge_lint`'s `ENTRY_RE` / `parse_entry` / `_strip_fences` per
[[019-constraint-knowledge-span-model-single-sourced]] /
[[021-constraint-skill-wraps-script-via-importable-api]]; it **never re-derives** the
grammar. It is **robust to malformed input** — `parse_entry` returns `declared_type:
None` / `related_out: set()` without raising on a conforming-named entry that lacks
`**Type**` or `## Related` (the exact legacy shape this tool targets).

### `minerva:migrate` — the read-only check skill

A new **read-only** skill (`plugins/minerva/skills/migrate/SKILL.md`):
`allowed-tools: Bash, Read, Grep, Glob` — **no** `Write`/`Edit`; it carries a literal
`read-only` body anchor, exactly like `minerva:lint`. It Bash-invokes the importable API
anchored to `git rev-parse --show-toplevel`
([[021-constraint-skill-wraps-script-via-importable-api]]) and emits a **migration
checklist** that **names** each remediation skill + a one-line effect, **without**
re-rendering that skill's findings or encoding its flags (cite, don't re-emit — avoids
two surfaces drifting):

- `non_conforming_files` present → **rename** them to `NNN-type-slug.md` (manual; **not
  automated** — awaits a future migration-APPLY unit).
- `index_present` false → run `minerva:init` (it backfills `index.md`).
- `overview_present` false → run `minerva:synthesize` (it creates `overview.md`).
- `entries_without_related` non-empty → **author** `## Related` cross-refs (manual; **not
  automated** — awaits a future backfill unit).
- For mechanical drift on the already-conforming entries → run `minerva:lint` (report) and
  `minerva:lint-fix` (repair).

The body **must state** that `migration_status` is a **SHAPE check, not a HEALTH check**:
a clean inventory (all files conforming, index + overview present) can still coexist with
`minerva:lint` index-drift errors (stale watermark / catalog bijection), so a passing
migration inventory **still requires** a green `minerva:lint` + `minerva:synthesize` pass.
The body enumerates the literal dict keys (`non_conforming_files`,
`entries_without_related`, …) so the contract's code-token anchors resolve.

### Tests, contract, catalog

- `tests/test_migration_status.py` (mirrors `test_synthesis_status.py`: synthetic
  `tmp_path` corpora, no live-repo dependency) covering `non_conforming_files`,
  `index_present` / `overview_present`, `entries_without_related`, the `RESERVED_NONENTRY`
  exemption, and a **malformed conforming-named entry** (no `**Type**` / no `## Related`)
  that is **counted, not crashed on**. Appended to `evals.yml`'s enumerated pytest list.
- `evals/migrate/contract.json` per [[012-constraint-skill-structural-contracts]]:
  `skill: migrate`; frontmatter `name: migrate`, non-empty `description`, `contains:
  allowed-tools`; positive-substring anchors on **stable code tokens**
  (`migration_status`, `non_conforming_files`), the literal `read-only`,
  `git rev-parse --show-toplevel`, and the cited skills (`minerva:lint`,
  `minerva:synthesize`); `cross_surface` all three. **No** mutating anchors.
- Catalog ([[010-constraint-minerva-skill-catalog-sync]]): add `minerva:migrate` to the
  plugin README, the root README, and the `using-minerva` matrix. The matrix **WHEN** row:
  *"A one-time check when adopting minerva on an already-populated, pre-conventions
  `.minerva/knowledge/` corpus — assess what's non-conforming and what to run to migrate
  it (a shape audit, not a recurring health-check)."*

## Success criteria

1. `migration_status(knowledge_dir)` returns the 5 plain-primitive fields;
   `non_conforming_files` excludes the named `RESERVED_NONENTRY` allowlist;
   `entries_without_related` reuses `parse_entry` (fence-aware; empty-or-absent both
   count); **no `Finding` namedtuples** in the returned dict.
2. `migration_status` is **robust to malformed input**: a conforming-named entry lacking
   `**Type**` / `## Related` is **counted** in `entries_without_related` and does not raise
   (explicit test case).
3. `plugins/minerva/skills/migrate/SKILL.md` is **read-only** (no `Write`/`Edit`; literal
   `read-only` anchor present), Bash-invokes the importable API via the
   `git rev-parse --show-toplevel` anchor, emits the checklist citing
   `minerva:init`/`minerva:lint`/`minerva:lint-fix`/`minerva:synthesize` by name, **states
   the shape-check-not-health-check disclaimer**, **states that the renames / cross-ref
   backfill are not yet automated** (manual / future APPLY unit), and contains the literal
   dict-key tokens the contract anchors on.
4. `tests/test_migration_status.py` covers the signals + `RESERVED_NONENTRY` exemption +
   the malformed-entry case on `tmp_path` corpora; appended to `evals.yml`'s enumerated
   list; green.
5. `evals/migrate/contract.json` anchors on code tokens (`migration_status`,
   `non_conforming_files`) + `read-only` + the cited skills; `cross_surface` all three;
   `tests/test_skill_contracts.py` passes with `migrate` enumerated.
6. Catalog on all three surfaces + the `using-minerva` one-time WHEN row.
7. Full enumerated CI suite green; the live corpus stays detector- and fixer-clean;
   `migration_status` on the live (already-migrated) corpus reports
   `non_conforming_files == []`, `index_present` and `overview_present` true.

## Open Questions

- None load-bearing.

## Out of scope (deferred to follow-up APPLY units)

- **Renaming** non-conforming files to `NNN-type-slug.md` (link-breaking mutation across
  the corpus — needs coordinated edits; its own design).
- **Authoring** the initial `## Related` cross-ref edge graph for a legacy corpus
  (O(entries²) LLM-judged neighbor discovery — a separate backfill unit).
- **Orchestrating / driving** the remediation skills (init / lint-fix / synthesize) — this
  unit *cites* them; it does not invoke them. (Keeps the read-only seam,
  [[020-decision-minerva-lint-read-only]].)
- CI-gating migration status (it is a one-time adoption concern, not a standing invariant;
  would false-positive on un-migrated repos).
