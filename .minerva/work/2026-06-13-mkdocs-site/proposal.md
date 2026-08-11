# Proposal: mkdocs-site

**Date**: 2026-06-13
**Status**: Shipped (2026-06-13)

## Goal
Replace the hand-authored `site/index.html` + `site/style.css` with an MkDocs-based static site using the default built-in theme (`mkdocs`), with source Markdown in `pages/`, deployed via a build step in the existing GitHub Pages CI workflow.

## Why
The hand-authored HTML site requires manually maintaining raw HTML for every content update. An SSG (static site generator) renders Markdown source to a navigable, consistent-looking site automatically, and the out-of-the-box MkDocs default theme provides clean, minimal styling without any custom CSS or external dependencies.

## Approach
MkDocs (default `mkdocs` theme), source in `pages/`:

1. **`mkdocs.yml`** at repo root — minimal config: `site_name`, `docs_dir: pages`, `site_dir: site`, `theme: {name: mkdocs}`.
2. **`pages/`** directory holds Markdown source. Single-page site (`pages/index.md`) migrated from the existing HTML content, preserving the skills-catalog HTML comment markers (HTML comments pass through MkDocs to the rendered output — the test continues to work).
3. **`site/` becomes build output.** Remove `site/index.html` and `site/style.css` from git; add `/site/` to `.gitignore`. The `site/` directory is created at CI build time by `mkdocs build`.
4. **Update `.github/workflows/pages.yml`** to install MkDocs and run `mkdocs build` before uploading the `site/` artifact.
5. **Update `tests/test_site_catalog.py`** to scan the Markdown source file (`pages/index.md`) instead of the built `site/index.html`. The pinned markers (HTML comment strings) remain identical — only the variable pointing to the file path changes.
6. **No new dependencies in `evals.yml`** — `test_site_catalog.py` now reads a Markdown source file, which needs no MkDocs install to check.

Alternative approaches considered and rejected:
- **Jekyll** — native GitHub Pages support, but adds Ruby as a foreign runtime (project is Python-only).
- **Hugo** — fast Go binary, but introduces a third language runtime with no advantage over MkDocs for this use case.

## Success criteria
- `mkdocs.yml` exists at repo root with `theme.name: mkdocs`.
- `pages/index.md` exists and contains all content from the current `site/index.html`, including the two pinned catalog markers.
- `site/index.html` and `site/style.css` are removed from git (no longer committed).
- `/site/` is listed in `.gitignore`.
- `.github/workflows/pages.yml` installs MkDocs and runs `mkdocs build` before the upload step.
- `tests/test_site_catalog.py` passes against the `pages/index.md` source (not `site/index.html`).
- The full CI evals suite passes locally (including `test_site_catalog.py`).

## Open Questions
- None.
