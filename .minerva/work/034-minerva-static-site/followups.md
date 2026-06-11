# Followups: minerva-static-site

- **Link the site from the repo's surfaces** (root README and/or `plugins/minerva/README.md`) so it is reachable without browsing the tree — excluded from unit 034 by its file-touch criterion.
- **Optional: GitHub Pages deploy via an Actions workflow.** The no-Actions `/docs` mode is not a clean option (`docs/` holds internal superpowers plans/specs); `site/` was chosen knowing a future deploy means a workflow.
- **Optional test hardening:** `tests/test_site_catalog.py::_catalog_section` uses `str.index`, so a *duplicated* marker pair would silently scan only the first region. Fail-safe today (entries stranded outside the scanned region fail the presence direction loudly); an assert-single-occurrence check on each marker would close the residual orphan gap in the pathological case.
