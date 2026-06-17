# Proposal: clean-site-footer-nav

**Date**: 2026-06-16
**Status**: Shipped (2026-06-16)

## Goal
Remove visible chrome cruft from the MkDocs (gitbook theme) site at https://… : the page-bottom Colophon, the always-visible dead search-results placeholder ("results matching"/"No results matching"), the two left-nav footer links ("Published with MkDocs", "Theme by GitBook"), and the duplicate "minerva" nav link (two entries collapse to one).

## Why
The site switched to the `mkdocs-gitbook` theme (commit 22a42f1). That theme ships left-nav promo links and a search-results block that — in this build — is never toggled by the bundled `gitbook.min.js` (it targets none of the `.search-results`/`search-noresults` selectors, and no CSS hides them), so the placeholder text renders permanently at the bottom of every page. The theme also renders both a `site_name` brand link and the single page as a nav chapter, producing two identical "minerva" links. Separately, the Colophon prose is now stale: it claims the site is "Generated with MkDocs using the default theme," but the theme is gitbook. All of this is low-value chrome that distracts from the content.

## Approach
Theme files live in the installed `mkdocs_gitbook` package (read-only); MkDocs's supported `theme.custom_dir` override is the clean mechanism.

1. **`mkdocs.yml`** — add `theme.custom_dir: overrides` and `extra_css: [css/extra.css]`.
2. **`overrides/nav.html`** — copy of the theme's `nav.html`, minus: (a) the `{% block site_name %}` brand link (the redundant `target="_blank"` "minerva" link) — leaving the in-page chapter as the single "minerva" link; (b) the two hardcoded footer `<li>` items ("Published with MkDocs", "Theme by GitBook"). MkDocs resolves `{% include "nav.html" %}` from `custom_dir` first, so `base.html` picks up the override with no `base.html` copy needed.
3. **`overrides/css/extra.css`** — one rule, `#book-search-results .search-results{display:none}`, hiding the dead search placeholder. Copied to `site/css/extra.css` at build (custom_dir static assets are emitted to the site root) and wired via `extra_css`. Avoids vendoring the 120-line `base.html`.
4. **`pages/index.md`** — delete the `## Colophon` section (and its leading `---`). It sits below the `<!-- end skills-catalog -->` marker, so the catalog markers and `tests/test_site_catalog.py` are untouched.
5. **`.github/workflows/pages.yml`** — add `overrides/**` to the deploy job's `paths` filter so future template-only edits redeploy (today's push also touches `mkdocs.yml`/`pages/`, so it would deploy regardless).

Alternatives considered and rejected:
- **Vendor `base.html` into `overrides/`** to delete the search block at source — most "correct," but copies a 120-line template that then silently shadows future theme updates. The one-line CSS hide is far less surface for a dead element.
- **CSS-only (no template override)** — hide the nav links via `:has()`/attribute selectors. Fragile (positional/text-coupled) and leaves the promo links in the DOM; template removal is cleaner for nav structure.

## Success criteria
- `mkdocs build` (local) succeeds; rendered `site/index.html` contains **no** "Published with MkDocs", "Theme by GitBook", or `class="custom-link"` brand link.
- Rendered nav has exactly **one** "minerva" link.
- The dead search-results placeholder is not visible (hidden via `extra.css`, which is present at `site/css/extra.css` and linked from the page `<head>`).
- `pages/index.md` no longer contains a `## Colophon` section; the two catalog markers and `tests/test_site_catalog.py` still pass.
- The site search input ("Type to search") is left intact.
- Full local test suite passes.

## Open Questions
- None.
