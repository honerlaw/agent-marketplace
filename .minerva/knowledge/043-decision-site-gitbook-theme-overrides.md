# Gitbook-theme chrome is customized via `theme.custom_dir → overrides/`, not by editing the installed theme

**Date**: 2026-06-16
**Type**: decision
**Context**: .minerva/work/043-clean-site-footer-nav (see git history if the worktree has been cleaned up)

## Context

After [[038-constraint-site-catalog-source-is-pages-index]] migrated the site to MkDocs, the theme was switched from the built-in `mkdocs` theme to `mkdocs-gitbook` (commit 22a42f1). The gitbook theme ships left-nav promo links ("Published with MkDocs", "Theme by GitBook"), renders both a `site_name` brand link and the page itself as a nav chapter (two identical "minerva" links on a single-page site), and emits a search-results block that renders permanently at the page bottom. Unit 043 removed all of that.

## Finding

Site chrome is customized through MkDocs's supported `theme.custom_dir: overrides` (set in `mkdocs.yml`), **not** by editing the installed `mkdocs_gitbook` package (read-only, and would not survive a reinstall). Files in `overrides/` override the theme's same-named files; absent files fall back to the theme, and `{% include %}` resolves from `overrides/` first. Current overrides:

- **`overrides/nav.html`** — the theme's `nav.html` minus the `{% block site_name %}` brand link (resolving the duplicate "minerva" — the in-page chapter link is kept) and minus the two hardcoded promo `<li>` items.
- **`overrides/css/extra.css`** — wired via `extra_css: [css/extra.css]`; custom_dir static assets are emitted to the site root (`site/css/extra.css`) alongside the theme's own `css/style.min.css` (custom_dir merges file-by-file, it does not shadow the whole `css/` dir).

The gitbook **search-results block is dead**: the bundled `gitbook.min.js` targets none of the `.search-results` / `search-noresults` / `#book-search-results` selectors and no theme CSS hides them, so the "results matching" / "No results matching" placeholders are always visible. `extra.css` hides `#book-search-results .search-results` rather than vendoring the 120-line `base.html` to delete it; the "Type to search" input is left intact.

## Implications

- **To change site nav/footer/chrome, edit `overrides/`** — never the installed theme. Add new template overrides by copying the theme file (`mkdocs_gitbook/<name>.html`) into `overrides/` and editing the copy.
- **`overrides/**` is in the `pages.yml` deploy path filter** — template-only edits redeploy. `pages/**` and `mkdocs.yml` are also filtered.
- **Don't "fix" the search block by re-enabling it** — the JS doesn't drive it; it is hidden deliberately, not broken by this change.
- Verify site changes with `python3 -m mkdocs build` and grep the rendered `site/index.html` (the `mkdocs` CLI may not be on PATH; the module is).

## Related
- [[038-constraint-site-catalog-source-is-pages-index]] — builds on; the catalog source is `pages/index.md` and `site/` is gitignored build output
- [[034-constraint-site-fourth-catalog-surface]] — see also; the catalog markers in `pages/index.md` remain load-bearing and were not touched
