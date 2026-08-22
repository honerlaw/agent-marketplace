# Followups: minerva-static-site

- **Link the site from the repo's surfaces** (root README and/or `plugins/minerva/README.md`) so it is reachable without browsing the tree — excluded from unit 034 by its file-touch criterion.
- **Optional: GitHub Pages deploy via an Actions workflow.** The no-Actions `/docs` mode is not a clean option (`docs/` holds internal superpowers plans/specs); `site/` was chosen knowing a future deploy means a workflow.
- **Optional test hardening:** `tests/test_site_catalog.py::_catalog_section` uses `str.index`, so a *duplicated* marker pair would silently scan only the first region. Fail-safe today (entries stranded outside the scanned region fail the presence direction loudly); an assert-single-occurrence check on each marker would close the residual orphan gap in the pathological case.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **Link the site from the repo's surfaces** → #75 (priority: medium)
- **Optional: GitHub Pages deploy via an Actions workflow.** → shipped — `.github/workflows/pages.yml` exists
- **Optional test hardening:** → open (low) — not filed at this pass; `tests/test_site_catalog.py` still uses `str.index` twice
