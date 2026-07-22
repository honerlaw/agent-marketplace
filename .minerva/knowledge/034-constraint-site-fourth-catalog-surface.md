# The static site's skills catalog is a fourth, test-enforced catalog surface

**Date**: 2026-06-10
**Type**: constraint
**Context**: .minerva/work/034-minerva-static-site (see git history if the worktree has been cleaned up)

## Context

[[010-constraint-minerva-skill-catalog-sync]] enumerated three hand-maintained catalog surfaces that must list every minerva skill (plugin README table, using-minerva decision matrix, root README cell) and recorded that its HTML-comment nudge is "a mitigation, not a guarantee." Unit 034 added `site/index.html` — a self-contained static site presenting minerva — whose skills-catalog section enumerates every skill. That section is a **fourth** catalog surface, and the most newcomer-exposed one, so it shipped with enforcement rather than repeating the nudge-only experiment.

## Finding

The site's catalog section is delimited by two **pinned HTML markers** (the opening skills-catalog source-of-truth comment and the closing `<!-- end skills-catalog -->`) and enforced by `tests/test_site_catalog.py`, which sits in the CI workflow's explicit pytest list. **For this surface the enforcement is bidirectional**: every SKILL.md-bearing dir under `plugins/minerva/skills/` must have its token-boundary `minerva:<name>` inside the delimited section (presence), and every `minerva:<name>` token inside the section must map to an existing skill dir (orphans). That is stronger than the one-way `cross_surface` floor of [[012-constraint-skill-structural-contracts]] — but the orphan-direction gap [[010-constraint-minerva-skill-catalog-sync]] records for the three original surfaces **remains open there**; this entry closes it for the site only.

The site is **deliberately not** a `SURFACE_FILES` / `cross_surface` surface: adding it to the per-skill contract clauses would have required editing every skill's `contract.json` (19 files at the time), while the bespoke enumerating test self-covers future skills with no per-skill opt-in. Do not "unify" it into `cross_surface` naively — the split is a decision, not an oversight.

## Implications

- **Adding a minerva skill now means four catalog updates** in the same change: the three from [[010-constraint-minerva-skill-catalog-sync]] plus an entry in `site/index.html` between the pinned markers. The site is the only one of the four whose omission fails CI in both directions.
- **Removing a skill**: delete its site entry too, or the orphan direction fails.
- Site descriptions follow 010's excerpt convention (frontmatter, verbatim or lightly trimmed). The test checks token presence only — description prose is point-in-time, and the page's colophon says so.
- The pinned marker strings are load-bearing: the test hardcodes both and fails loudly if either is absent. Reword them only together with `tests/test_site_catalog.py`.
- Token matching reuses `_present` from `tests/test_skill_contracts.py` (hyphen-aware boundaries); never reimplement it.

## Related
- [[010-constraint-minerva-skill-catalog-sync]] — builds on
- [[012-constraint-skill-structural-contracts]] — see also
- [[038-constraint-site-catalog-source-is-pages-index]] — supersedes: catalog surface is now pages/index.md (MkDocs source), not site/index.html
- [[043-decision-site-gitbook-theme-overrides]] — see also; site chrome cleanup that left the catalog markers untouched
- [[048-pattern-catalog-semantic-drift-recurs]] — see also
