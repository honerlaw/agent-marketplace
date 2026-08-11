# Scratchpad: 043-clean-site-footer-nav

## Quick decisions 2026-06-16
- [decided] scope check: single work unit — bounded MkDocs/gitbook chrome cleanup (one md edit + small theme override). Not decompose.
- [decided] approach: `theme.custom_dir` override of `nav.html` + a one-line `extra_css` rule for the dead search placeholder. Rejected vendoring `base.html` (120-line template would silently shadow theme updates) and CSS-only nav hiding (fragile positional/attr selectors, leaves promo links in DOM).
- [decided] duplicate "minerva": keep the in-page chapter link (active-state, normal in-page anchor), remove the `site_name` brand link (redundant, opens in a new `_blank` tab). Dominant choice — chapter is the functional in-page nav.
- [decided] whole-proposal soundness: no public interface/contract; Colophon is below the load-bearing catalog markers so the catalog test is untouched. Add `overrides/**` to `pages.yml` path filter so future template-only edits redeploy.
- [synthesis] no-op (below threshold): watermark 42, corpus max 43, unsynthesized=[043] (one entry), link_rot=[] — re-synthesis would churn for no navigational gain.
