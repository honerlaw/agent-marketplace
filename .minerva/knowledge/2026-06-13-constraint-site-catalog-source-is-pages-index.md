# Site catalog surface is pages/index.md (MkDocs source); site/ is gitignored build output

**Date**: 2026-06-13
**Type**: constraint
**Context**: .minerva/work/2026-06-13-mkdocs-site (see git history if the worktree has been cleaned up)

## Context

[[2026-06-10-constraint-site-fourth-catalog-surface]] documented the site as the fourth skill-catalog surface, enforced bidirectionally by `tests/test_site_catalog.py` scanning `site/index.html`. Unit 041 migrated the site from hand-authored HTML+CSS to MkDocs (default theme), moving the source to `pages/index.md` and making `site/` the gitignored build output.

## Finding

The test was updated to scan `pages/index.md` directly (the Markdown source), not the built `site/index.html`. This is an intentional design choice: reading the source avoids requiring a `mkdocs build` step in the evals CI job. The pinned HTML comment markers (the opening skills-catalog comment and `<!-- end skills-catalog -->`) appear verbatim in the Markdown source and pass through to the rendered HTML when MkDocs builds — but the test's authority is the source, not the rendered output.

`site/` is listed in `.gitignore` (`/site/`) and is not committed. It is created at CI build time by `pip install "mkdocs==1.6.1" && mkdocs build` in `.github/workflows/pages.yml`.

## Implications

- **Adding a minerva skill now means updating `pages/index.md`** between the pinned markers (not `site/index.html`, which no longer exists as a committed file).
- **The test requires no build step**: `pytest tests/test_site_catalog.py` reads `pages/index.md` directly; it does not require `mkdocs build` to run first.
- **Do not commit `site/`**: it is gitignored build output. The Pages workflow builds and uploads it in CI.
- **`mkdocs.yml` enables the `def_list` extension**: the skills catalog section uses definition list Markdown syntax (`**term**\n: definition`). Removing this extension would break rendering.
- The pinned marker strings remain load-bearing per [[2026-06-10-constraint-site-fourth-catalog-surface]] — reword them only together with `tests/test_site_catalog.py`.

## Related
- [[2026-06-10-constraint-site-fourth-catalog-surface]] — supplements; the site is still the fourth test-enforced catalog surface
- [[2026-05-21-constraint-minerva-skill-catalog-sync]] — the three other catalog surfaces remain unchanged
- [[2026-06-16-decision-site-gitbook-theme-overrides]] — builds on; the theme is now gitbook, customized via overrides/, with the catalog source unchanged
